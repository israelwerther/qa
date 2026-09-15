#!/usr/bin/env python
"""
Gerador e Respondendor de Cartões Resposta (OMR) para QA (Lize Edu)
Local: .ai_qa_acervo/scripts/generators/answer_omr_sheets.py

Gera documentos PDF reais com as folhas de resposta oficiais da Lize Edu
com as bolinhas pré-preenchidas para simulação de envio de gabarito.

Suporta cenários de teste controlados:
- Respostas 100% preenchidas
- Questão em branco (para gerar pendência no OMR)
- Questão com marcação dupla (para gerar pendência no OMR)
"""

import os
import sys
import argparse
import re
import subprocess
import tempfile

# Setup do ambiente Django
current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir != '/' and not os.path.exists(os.path.join(current_dir, 'manage.py')):
    current_dir = os.path.dirname(current_dir)
BASE_DIR = current_dir
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiscallizeon.settings')

import django
django.setup()

from django.template.loader import render_to_string
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.omr.models import OMRCategory
from fiscallizeon.omr.utils import get_qr_code
from fiscallizeon.exams.models import ExamQuestion, Question


def find_application(identifier=None):
    """Busca aplicação por UUID ou nome do caderno/exame. Se None, pega a última."""
    qs = Application.objects.select_related('exam').order_by('-created_at')
    if not identifier:
        app = qs.first()
        if not app:
            raise ValueError("Nenhuma aplicação encontrada no banco de dados.")
        return app

    # Tenta por UUID
    try:
        return qs.get(id=identifier)
    except Exception:
        pass

    # Tenta por nome do caderno
    app = qs.filter(exam__name__icontains=identifier).first()
    if app:
        return app

    raise ValueError(f"Aplicação não encontrada para o identificador: '{identifier}'")


def mark_student_sheet(html_content, question_answers):
    """
    Substitui no HTML da folha de respostas as bolinhas dos círculos
    para ficarem pretas de acordo com o dicionário de respostas:
    question_answers: { 1: ['A'], 2: ['B'], 3: [], 4: ['A', 'C'] }
    """
    # Regex para localizar cada bloco de questão: <div class="omr-question">...</div>
    # Dentro de cada bloco, procuramos:
    # <td class="index omr-td">N</td> seguido das alternativas: <span class="omr-circle">LETTER</span>

    def replace_question(match):
        block = match.group(0)
        idx_match = re.search(r'<td class="index omr-td">\s*(\d+)\s*</td>', block)
        if not idx_match:
            return block

        q_num = int(idx_match.group(1))
        letters_to_mark = question_answers.get(q_num, [])

        if not letters_to_mark:
            # Não marca nada (questão em branco)
            return block

        # Para cada letra a marcar, adiciona o estilo de preenchimento preto puro
        for letter in letters_to_mark:
            pattern = rf'(<span class="omr-circle">)\s*{letter}\s*(</span>)'
            replacement = (
                rf'<span class="omr-circle" style="background-color: #000 !important; '
                rf'color: #000 !important; -webkit-print-color-adjust: exact !important;">{letter}</span>'
            )
            block = re.sub(pattern, replacement, block)

        return block

    # Aplica a substituição em todos os blocos de questão
    processed_html = re.sub(r'<div class="omr-question">.*?</div>', replace_question, html_content, flags=re.DOTALL)
    return processed_html


def generate_omr_pdf(application, students_count=4, mode='pendings', output_path=None):
    """Gera o documento PDF com os cartões preenchidos."""
    app_students = list(
        application.applicationstudent_set.select_related('student')
        .all()[:students_count]
    )

    if not app_students:
        raise ValueError(f"A aplicação {application.id} não possui alunos vinculados.")

    exam = application.exam
    exam_questions = list(
        ExamQuestion.objects.filter(exam=exam, question__number_is_hidden=False)
        .availables()
        .order_by('exam_teacher_subject__order', 'order')
    )

    if not exam_questions:
        raise ValueError(f"O caderno {exam.name} não possui questões disponíveis.")

    # Gabarito oficial ou alternativas padrão
    letters = ['A', 'B', 'C', 'D', 'E']
    official_answers = {}
    for idx, eq in enumerate(exam_questions, 1):
        correct_alt = eq.question.alternatives.filter(is_correct=True).first()
        if correct_alt and correct_alt.index is not None and correct_alt.index < len(letters):
            official_answers[idx] = letters[correct_alt.index]
        else:
            official_answers[idx] = letters[(idx - 1) % 4]

    total_q = len(exam_questions)
    sequential = OMRCategory.FISCALLIZE

    output_dir = os.path.dirname(output_path) if output_path else os.path.join(BASE_DIR, 'data', 'gabaritos_qa')
    os.makedirs(output_dir, exist_ok=True)

    if not output_path:
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', exam.name[:30])
        output_path = os.path.join(output_dir, f'cartoes_respondidos_{safe_name}.pdf')

    students_scenarios = []

    # Configura os dados dos alunos
    for i, st in enumerate(app_students):
        st.qr_code = get_qr_code(st.pk, sequential, 'S')
        st.school_class = st.get_last_class_student()
        st.is_class_first = False  # Evita página de capa de turma no PDF de scan

        # Define as respostas de acordo com o modo e posição do aluno
        student_answers = {}
        scenario_desc = ""

        if mode == 'all-answered':
            for q_num in range(1, total_q + 1):
                student_answers[q_num] = [official_answers.get(q_num, 'A')]
            scenario_desc = "100% Respondido (Sem pendências)"

        elif mode == 'all-blank':
            for q_num in range(1, total_q + 1):
                student_answers[q_num] = []
            scenario_desc = "100% Em Branco"

        else:  # mode == 'pendings'
            if i == 0:
                # Aluno 1: 100% respondido
                for q_num in range(1, total_q + 1):
                    student_answers[q_num] = [official_answers.get(q_num, 'A')]
                scenario_desc = "100% Respondido (Sem pendências)"
            elif i == 1:
                # Aluno 2: Uma questão em branco (falta de resposta)
                blank_q = min(3, total_q)
                for q_num in range(1, total_q + 1):
                    if q_num == blank_q:
                        student_answers[q_num] = []  # EM BRANCO!
                    else:
                        student_answers[q_num] = [official_answers.get(q_num, 'A')]
                scenario_desc = f"Pendência: Questão {blank_q} EM BRANCO"
            elif i == 2:
                # Aluno 3: Uma questão com dupla marcação
                double_q = min(2, total_q)
                for q_num in range(1, total_q + 1):
                    if q_num == double_q:
                        student_answers[q_num] = ['A', 'B']  # DUPLA MARCAÇÃO!
                    else:
                        student_answers[q_num] = [official_answers.get(q_num, 'C')]
                scenario_desc = f"Pendência: Questão {double_q} com DUPLA MARCAÇÃO (A e B)"
            else:
                # Demais alunos: 100% respondidos
                for q_num in range(1, total_q + 1):
                    student_answers[q_num] = [official_answers.get(q_num, 'B')]
                scenario_desc = "100% Respondido (Sem pendências)"

        st.simulated_answers = student_answers
        students_scenarios.append({
            'name': st.student.name,
            'enrollment': st.student.enrollment_number,
            'class': st.school_class.name if st.school_class else 'Sem turma',
            'scenario': scenario_desc,
        })

    # Renderiza o template oficial da Lize
    context = {
        'object': app_students[0],
        'application_students': app_students,
        'exam_questions': exam_questions,
        'qr_code_text': f'S:{sequential}:{app_students[0].pk}',
    }

    base_html = render_to_string('omr/export_answer_sheets.html', context)

    # Injeta a marcação nas bolinhas para cada aluno
    # Como o template renderiza todos os alunos no mesmo HTML, aplicamos a marcação em bloco
    final_html = base_html
    for st in app_students:
        final_html = mark_student_sheet(final_html, st.simulated_answers)

    # Adiciona estilo para garantir impressão perfeita de fundos pretos no Chrome
    print_style = """
    <style>
        * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        .omr-circle[style*="background-color: #000"] {
            background-color: #000000 !important;
            color: #000000 !important;
        }
    </style>
    """
    final_html = final_html.replace('</head>', f'{print_style}</head>')

    # Salva HTML temporário para compilação via Chrome
    with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
        f.write(final_html)
        temp_html_path = f.name

    try:
        chrome_cmd = [
            'google-chrome',
            '--headless',
            '--disable-gpu',
            '--no-sandbox',
            '--print-to-pdf-no-header',
            f'--print-to-pdf={output_path}',
            temp_html_path,
        ]
        res = subprocess.run(chrome_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise RuntimeError(f"Erro ao compilar PDF via Chrome: {res.stderr.decode()}")
    finally:
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)

    return output_path, students_scenarios


def main():
    parser = argparse.ArgumentParser(description="Gera e responde folhas de resposta (OMR) em PDF para QA.")
    parser.add_argument('-a', '--application', type=str, default=None, help="UUID ou nome da aplicação existente.")
    parser.add_argument('-sc', '--students-count', type=int, default=4, help="Quantidade de alunos a responder (padrão 4).")
    parser.add_argument('-m', '--mode', choices=['pendings', 'all-answered', 'all-blank'], default='pendings', help="Modo de preenchimento (padrão 'pendings').")
    parser.add_argument('-o', '--output', type=str, default=None, help="Caminho do arquivo PDF de saída.")

    args = parser.parse_args()

    try:
        app = find_application(args.application)
        pdf_path, scenarios = generate_omr_pdf(
            application=app,
            students_count=args.students_count,
            mode=args.mode,
            output_path=args.output,
        )

        print("\n" + "=" * 65)
        print("  🎉 CARTÕES RESPOSTA RESPONDIDOS COM SUCESSO! (OMR QA)")
        print("=" * 65)
        print(f"Aplicação:  {app.exam.name} ({app.id})")
        print(f"Alunos:     {len(scenarios)} cartões gerados")
        print(f"Modo:       {args.mode}")
        print(f"Arquivo:    file://{os.path.abspath(pdf_path)}")
        print("-" * 65)
        print("Cenários simulados por aluno:")
        for idx, sc in enumerate(scenarios, 1):
            print(f"  {idx}. {sc['name']} ({sc['class']}) -> {sc['scenario']}")
        print("-" * 65)
        print("Próximo passo:")
        print("  1. Abra o navegador em: http://127.0.0.1:8000/gabaritos/")
        print("  2. Clique em 'Enviar respostas'")
        print(f"  3. Selecione a aplicação: '{app.exam.name}'")
        print(f"  4. Anexe o arquivo PDF: {os.path.abspath(pdf_path)}")
        print("=" * 65 + "\n")

    except Exception as e:
        print(f"\n❌ Erro: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

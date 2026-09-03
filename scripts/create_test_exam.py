#!/usr/bin/env python
"""
Gerador de Cadernos e Questões de Teste para QA (Lize Edu)
Local: .ai_qa_acervo/scripts/create_test_exam.py

Cria sob demanda cadernos de prova (Exam) completos e 100% integrados:
- Objetivas (Múltipla escolha A-E com QuestionOption)
- Discursivas (Question.TEXTUAL, is_essay=False)
- Redações (Question.TEXTUAL, is_essay=True)
- Configurações de embaralhamento (random_questions, random_alternatives)
- Vinculação com Disciplina (Subject), Professor (TeacherSubject) e Série (Grade)
- Criação de ExamTeacherSubject e amarrações em ExamQuestion
- Configuração de diagramação (exam_print_config) herdada do cliente
- Vinculação automática às coordenações do usuário ativo
"""

import os
import sys
import argparse
from datetime import datetime

# Setup do ambiente Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiscallizeon.settings')

import django
django.setup()

from django.utils import timezone
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, SchoolCoordination
from fiscallizeon.classes.models import Grade
from fiscallizeon.subjects.models import Subject
from fiscallizeon.inspectors.models import TeacherSubject
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject
from fiscallizeon.questions.models import Question, QuestionOption


def get_default_user(username=None):
    if username:
        user = User.objects.filter(username=username).first()
        if user:
            return user

    # Prioridades padrão para QA local
    for name in ['fiscallize_geral', 'cloud.coord@lize.local', 'cloud.admin@lize.local']:
        user = User.objects.filter(username=name).first() or User.objects.filter(email=name).first()
        if user:
            return user

    # Fallback para primeiro superusuário ou usuário ativo
    return User.objects.filter(is_superuser=True).first() or User.objects.filter(is_active=True).first()


def create_exam_with_questions(
    name=None,
    objective_count=5,
    discursive_count=0,
    essay_count=0,
    random_questions=False,
    random_alternatives=False,
    username=None,
    subject_name=None,
    client_name=None,
):
    user = get_default_user(username)
    if not user:
        print("❌ Erro: Nenhum usuário válido encontrado no banco de dados.")
        sys.exit(1)

    # Identificar cliente e coordenações
    client = getattr(user, 'client', None)
    if client_name:
        found_client = Client.objects.filter(name__icontains=client_name).first()
        if found_client:
            client = found_client

    if not client:
        clients_cache = user.get_clients_cache()
        if clients_cache:
            client = Client.objects.filter(pk__in=clients_cache).first()
        else:
            client = Client.objects.first()

    coordinations = list(user.get_coordinations_cache())
    if not coordinations and client:
        coordinations = list(SchoolCoordination.objects.filter(unity__client=client).values_list('pk', flat=True))

    # Identificar dados pedagógicos do tenant (Disciplina, Série, Professor)
    subject = None
    if subject_name:
        subject = Subject.objects.filter(client=client, name__icontains=subject_name).first()
        if not subject:
            subject = Subject.objects.filter(name__icontains=subject_name).first()

    if not subject:
        subject = Subject.objects.filter(client=client).first() or Subject.objects.first()
    grade = Grade.objects.filter(schoolclass__coordination__in=coordinations).first() or Grade.objects.first()
    teacher_subject = None
    if subject:
        teacher_subject = (
            TeacherSubject.objects.filter(subject=subject).first()
            or TeacherSubject.objects.filter(subject__client=client).first()
            or TeacherSubject.objects.first()
        )

    timestamp_str = timezone.localtime().strftime('%d/%m %H:%M')
    total_q = objective_count + discursive_count + essay_count

    if not name:
        tags = []
        if objective_count:
            tags.append(f"{objective_count} Obj")
        if discursive_count:
            tags.append(f"{discursive_count} Disc")
        if essay_count:
            tags.append(f"{essay_count} Redação")
        if random_questions or random_alternatives:
            tags.append("Random")

        spec_str = " + ".join(tags) if tags else "Vazia"
        name = f"[QA] Caderno ({spec_str}) - {timestamp_str}"

    print("\n" + "=" * 60)
    print("🚀 CRIANDO CADERNO DE TESTE PARA QA")
    print("=" * 60)
    print(f"• Nome: {name}")
    print(f"• Usuário Criador: {user.username} (Client: {client.name if client else 'Nenhum'})")
    print(f"• Disciplina: {subject.name if subject else 'Nenhuma'}")
    print(f"• Série: {grade.name if grade else 'Nenhuma'}")
    print(f"• Objetivas: {objective_count} | Discursivas: {discursive_count} | Redação: {essay_count}")
    print(f"• Embaralhar Questões: {'Sim' if random_questions else 'Não'}")
    print(f"• Embaralhar Alternativas: {'Sim' if random_alternatives else 'Não'}")

    # Configuração de impressão clonada do cliente
    exam_print_config = None
    if client:
        try:
            base_config = client.get_exam_print_config()
            if base_config:
                base_config.pk = None
                base_config.name = f'Configuração {name}'
                base_config.is_default = False
                base_config.save()
                exam_print_config = base_config
        except Exception as e:
            print(f"⚠️ Aviso ao clonar print_config: {e}")

    # Criação do Exam
    exam = Exam.objects.create(
        name=name,
        created_by=user,
        is_abstract=False,
        not_applicable=False,
        random_questions=random_questions,
        random_alternatives=random_alternatives,
        quantity_alternatives=5,
        exam_print_config=exam_print_config,
    )

    if coordinations:
        exam.coordinations.set(coordinations)

    # Criação do ExamTeacherSubject (essencial para agrupamentos pedagógicos)
    ets = None
    if teacher_subject:
        ets = ExamTeacherSubject.objects.create(
            exam=exam,
            teacher_subject=teacher_subject,
            grade=grade,
            quantity=total_q,
            order=1,
        )

    current_order = 1

    # 1. Questões Objetivas
    for i in range(1, objective_count + 1):
        q = Question.objects.create(
            category=Question.CHOICE,
            subject=subject,
            grade=grade,
            level=Question.MEDIUM,
            is_public=False,
            enunciation=(
                f"<h4>Questão {current_order} — Objetiva (Teste QA)</h4>"
                f"<p>Considere o enunciado da questão objetiva {current_order}. "
                f"Qual das alternativas abaixo é a correta?</p>"
            ),
        )
        if coordinations:
            q.coordinations.set(coordinations)

        # 5 alternativas (A, B, C, D, E) com A correta por padrão
        for idx, letter in enumerate(['A', 'B', 'C', 'D', 'E']):
            QuestionOption.objects.create(
                question=q,
                text=f"<p>Alternativa ({letter}) da questão {current_order}</p>",
                is_correct=(idx == 0),
                index=idx,
            )

        ExamQuestion.objects.create(
            exam=exam,
            question=q,
            order=current_order,
            weight=1.0,
            exam_teacher_subject=ets,
        )
        current_order += 1

    # 2. Questões Discursivas
    for i in range(1, discursive_count + 1):
        q = Question.objects.create(
            category=Question.TEXTUAL,
            is_essay=False,
            quantity_lines=8,
            subject=subject,
            grade=grade,
            level=Question.MEDIUM,
            is_public=False,
            enunciation=(
                f"<h4>Questão {current_order} — Discursiva (Teste QA)</h4>"
                f"<p>Explique detalhadamente a resolução do problema proposto nesta questão discursiva {current_order}. "
                f"Utilize as linhas abaixo para fundamentar sua resposta.</p>"
            ),
        )
        if coordinations:
            q.coordinations.set(coordinations)

        ExamQuestion.objects.create(
            exam=exam,
            question=q,
            order=current_order,
            weight=1.0,
            exam_teacher_subject=ets,
        )
        current_order += 1

    # 3. Propostas de Redação
    for i in range(1, essay_count + 1):
        q = Question.objects.create(
            category=Question.TEXTUAL,
            is_essay=True,
            quantity_lines=30,
            subject=subject,
            grade=grade,
            level=Question.MEDIUM,
            is_public=False,
            enunciation=(
                f"<h4>Proposta de Redação {i} (Teste QA)</h4>"
                f"<p>A partir da leitura dos textos motivadores e com base nos conhecimentos construídos ao longo de sua formação, "
                f"redija um texto dissertativo-argumentativo em modalidade escrita formal da língua portuguesa sobre o tema proposto.</p>"
            ),
        )
        if coordinations:
            q.coordinations.set(coordinations)

        ExamQuestion.objects.create(
            exam=exam,
            question=q,
            order=current_order,
            weight=1.0,
            exam_teacher_subject=ets,
        )
        current_order += 1

    print("-" * 60)
    print("✅ CADERNO CRIADO COM SUCESSO!")
    print(f"• ID do Exam: {exam.pk}")
    print(f"• Nome exato: {exam.name}")
    print(f"• Total de questões vinculadas: {total_q}")
    print(f"• Coordenações vinculadas: {len(coordinations)}")
    print(f"• Disciplina: {subject.name if subject else 'N/A'}")
    print(f"• Diagramação V2: {'Pronta (config vinculada)' if exam.exam_print_config else 'Padrão'}")
    print("=" * 60)
    print("💡 Como usar agora:")
    print("   1. Acesse: http://127.0.0.1:8000/aplicacoes/cadastrar/?category=hibrid")
    print(f"   2. No campo 'Instrumento avaliativo', busque por: {exam.name[:25]}")
    print("   3. Selecione o caderno e continue o agendamento normalmente!")
    print("=" * 60 + "\n")

    return exam


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Gerador de Cadernos e Questões para Testes de QA (Lize Edu)"
    )
    parser.add_argument(
        '-n', '--name',
        type=str,
        default=None,
        help="Nome personalizado do caderno de prova",
    )
    parser.add_argument(
        '-obj', '--objective',
        type=int,
        default=None,
        help="Quantidade de questões objetivas (múltipla escolha A-E)",
    )
    parser.add_argument(
        '-disc', '--discursive',
        type=int,
        default=None,
        help="Quantidade de questões discursivas padrão",
    )
    parser.add_argument(
        '-ess', '--essay',
        type=int,
        default=None,
        help="Quantidade de propostas de redação",
    )
    parser.add_argument(
        '-rq', '--random-questions',
        action='store_true',
        help="Ativar embaralhamento de questões no caderno",
    )
    parser.add_argument(
        '-ra', '--random-alternatives',
        action='store_true',
        help="Ativar embaralhamento de alternativas no caderno",
    )
    parser.add_argument(
        '-u', '--user',
        type=str,
        default=None,
        help="Username do usuário dono/criador (ex: fiscallize_geral)",
    )
    parser.add_argument(
        '-s', '--subject',
        type=str,
        default=None,
        help="Nome ou filtro da disciplina (ex: Matemática, Álgebra)",
    )
    parser.add_argument(
        '-c', '--client',
        type=str,
        default=None,
        help="Nome ou filtro do cliente (ex: Rede Decisão)",
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help="Forçar modo interativo para escolher as quantidades no terminal",
    )
    return parser.parse_args()


def interactive_mode():
    print("\n📝 MODO INTERATIVO — GERADOR DE CADERNOS DE TESTE")
    print("-" * 50)
    try:
        raw_name = input("Nome do caderno (Enter para padrão automático): ").strip()
        name = raw_name if raw_name else None

        raw_obj = input("Quantidade de questões OBJETIVAS [padrão: 5]: ").strip()
        obj = int(raw_obj) if raw_obj.isdigit() else 5

        raw_disc = input("Quantidade de questões DISCURSIVAS [padrão: 0]: ").strip()
        disc = int(raw_disc) if raw_disc.isdigit() else 0

        raw_ess = input("Quantidade de propostas de REDAÇÃO [padrão: 0]: ").strip()
        ess = int(raw_ess) if raw_ess.isdigit() else 0

        raw_rq = input("Embaralhar questões? (s/N): ").strip().lower()
        rq = raw_rq in ['s', 'sim', 'y', 'yes']

        raw_ra = input("Embaralhar alternativas? (s/N): ").strip().lower()
        ra = raw_ra in ['s', 'sim', 'y', 'yes']

        return {
            'name': name,
            'objective_count': obj,
            'discursive_count': disc,
            'essay_count': ess,
            'random_questions': rq,
            'random_alternatives': ra,
        }
    except (KeyboardInterrupt, EOFError):
        print("\nOperação cancelada.")
        sys.exit(0)


if __name__ == '__main__':
    args = parse_arguments()

    has_counts = any(x is not None for x in [args.objective, args.discursive, args.essay])

    if args.interactive or (not has_counts and sys.stdin.isatty()):
        config = interactive_mode()
        create_exam_with_questions(
            name=config['name'],
            objective_count=config['objective_count'],
            discursive_count=config['discursive_count'],
            essay_count=config['essay_count'],
            random_questions=config['random_questions'],
            random_alternatives=config['random_alternatives'],
            username=args.user,
            subject_name=args.subject,
            client_name=args.client,
        )
    else:
        create_exam_with_questions(
            name=args.name,
            objective_count=args.objective if args.objective is not None else 5,
            discursive_count=args.discursive if args.discursive is not None else 0,
            essay_count=args.essay if args.essay is not None else 0,
            random_questions=args.random_questions,
            random_alternatives=args.random_alternatives,
            username=args.user,
            subject_name=args.subject,
            client_name=args.client,
        )

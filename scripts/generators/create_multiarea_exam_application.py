#!/usr/bin/env python
"""
Gerador de Aplicação Multi-Área para QA da Tela de Resultados (Lize Edu)
Local: .ai_qa_acervo/scripts/generators/create_multiarea_exam_application.py

Cria um Simulado Multi-Áreas (Ciências da Natureza + Ciências Humanas)
com questões de Biologia e História, aplica na turma do aluno Enrico (F4MA)
e simula respostas com acertos e erros calibrados para testar:
- Alternador "Disciplinas" vs "Área do conhecimento"
- Navegação restrita por Área ("Visualizar")
- Aba "Questões para revisar" com as questões erradas
- Percentual de acertos da turma e cards com trecho de enunciado (excerpt)
"""

import os
import sys
from datetime import timedelta
import uuid

current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir != '/' and not os.path.exists(os.path.join(current_dir, 'manage.py')):
    current_dir = os.path.dirname(current_dir)
BASE_DIR = current_dir
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiscallizeon.settings')

import django
django.setup()

from django.core.cache import cache
from django.utils import timezone
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, SchoolCoordination
from fiscallizeon.classes.models import SchoolClass, Grade
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import Subject
from fiscallizeon.inspectors.models import Inspector, TeacherSubject
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject, StatusQuestion
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.answers.models import OptionAnswer
from fiscallizeon.applications.models import Application, ApplicationStudent


def create_multiarea_application():
    cache.clear()
    now = timezone.localtime()

    # 1. Recupera Cliente e Aluno Enrico
    enrico_user = User.objects.filter(email='enrico.a53143@aluno.decisaovirtual.com.br').first()
    if not enrico_user:
        raise ValueError("Usuário enrico.a53143@aluno.decisaovirtual.com.br não encontrado no banco.")

    student = Student.objects.filter(user=enrico_user).first()
    client = student.client
    school_class = student.classes.first()
    if not school_class:
        school_class = SchoolClass.objects.filter(coordination__unity__client=client).first()

    coordination = SchoolCoordination.objects.filter(unity__client=client).first()
    grade = school_class.grade if school_class else Grade.objects.filter(teaching_stage__client=client).first()

    print(f"🏫 Cliente: {client.name}")
    print(f"👤 Aluno: {student.name} ({enrico_user.email})")
    print(f"🎓 Turma: {school_class.name}")

    # 2. Seleciona ou cria Disciplinas em 3 Áreas distintas
    sub_bio = Subject.objects.filter(client=client, name__icontains='Biologia').first()
    sub_qui = Subject.objects.filter(client=client, name__icontains='Química').first()
    sub_his = Subject.objects.filter(client=client, name__icontains='História').first()
    sub_mat = Subject.objects.filter(client=client, name__icontains='Aprofundamento de Matemática').first()
    if not sub_mat:
        sub_mat = Subject.objects.filter(client=client, name__icontains='Matemática').first()

    if not sub_bio or not sub_his or not sub_mat:
        raise ValueError("Não foram encontradas disciplinas de Biologia, História e Matemática para o cliente.")

    area_bio = sub_bio.knowledge_area.name if sub_bio.knowledge_area else "Ciências da Natureza"
    area_qui = sub_qui.knowledge_area.name if sub_qui and sub_qui.knowledge_area else area_bio
    area_his = sub_his.knowledge_area.name if sub_his.knowledge_area else "Ciências Humanas"
    area_mat = sub_mat.knowledge_area.name if sub_mat.knowledge_area else "Matemática e suas Tecnologias"

    print(f"🔬 Matéria 1: {sub_bio.name} ➔ Área: {area_bio}")
    if sub_qui:
        print(f"🧪 Matéria 2: {sub_qui.name} ➔ Área: {area_qui}")
    print(f"🏛️ Matéria 3: {sub_his.name} ➔ Área: {area_his}")
    print(f"📐 Matéria 4: {sub_mat.name} ➔ Área: {area_mat}")

    # TeacherSubjects já existentes para as matérias
    ts_bio = TeacherSubject.objects.filter(subject=sub_bio).first()
    ts_qui = TeacherSubject.objects.filter(subject=sub_qui).first() if sub_qui else None
    ts_his = TeacherSubject.objects.filter(subject=sub_his).first()
    ts_mat = TeacherSubject.objects.filter(subject=sub_mat).first()
    teacher_user = (ts_bio.teacher.user if ts_bio and ts_bio.teacher else None) or User.objects.filter(is_superuser=True).first() or enrico_user

    # 3. Criação do Caderno de Prova
    exam_name = "Simulado Multi-Áreas (Natureza, Humanas e Matemática) - QA"
    old_exams = Exam.objects.filter(name__in=[exam_name, "Simulado Multi-Áreas (Natureza e Humanas) - QA"])
    old_apps = Application.objects.all_with_deleted().filter(exam__in=old_exams)
    OptionAnswer.objects.filter(student_application__application__in=old_apps).delete()
    ApplicationStudent.objects.filter(application__in=old_apps).delete()
    old_apps.hard_delete()
    old_exams.delete()

    exam = Exam.objects.create(
        name=exam_name,
        created_by=teacher_user,
        exam_format=Exam.STANDARD,
        is_abstract=False,
        status=Exam.ELABORATING,
        random_questions=False,
        random_alternatives=False,
        show_ranking=True,
    )
    if coordination:
        exam.coordinations.add(coordination)

    # Blocos de Matéria no Caderno
    ets_bio = ExamTeacherSubject.objects.create(exam=exam, teacher_subject=ts_bio, grade=grade, order=1, quantity=3, subject_note=5.0)
    ets_his = ExamTeacherSubject.objects.create(exam=exam, teacher_subject=ts_his, grade=grade, order=2, quantity=3, subject_note=5.0)
    ets_mat = ExamTeacherSubject.objects.create(exam=exam, teacher_subject=ts_mat, grade=grade, order=3, quantity=3, subject_note=5.0)
    ets_qui = ExamTeacherSubject.objects.create(exam=exam, teacher_subject=ts_qui or ts_bio, grade=grade, order=4, quantity=1, subject_note=5.0)

    # ==============================================================================
    # CATÁLOGO DE QUESTÕES DE REFERÊNCIA PARA CASOS EXTREMOS / FORMAS COMPLEXAS
    # Diretriz de QA: É expressamente proibido criar questões mock/sintéticas via
    # código para testes de visualização, cards, drawers e relatórios. Deve-se usar
    # exclusivamente questões reais do banco para evitar viés (evita enviezamentos).
    # ==============================================================================
    REFERENCE_EDGE_CASE_QUESTIONS = {
        "math_formulas_mathml": {
            "id": "0d6f2abc-d76d-4cec-9481-fe757f0ce360",
            "title": "Fórmulas matemáticas com MathML nativo",
            "description": "Enunciado com tags <math> logo no início e alternativas com frações.",
            "notes": "Valida se strip_tags limpa tags <math> gerando excerpt legível e se o Drawer renderiza as fórmulas.",
        },
        "chemistry_base64_image": {
            "id": "3d124dcc-964e-4ed5-9a74-2c44fdd172e5",
            "title": "Imagem inline em Base64 no início do enunciado",
            "description": "Enunciado inicia com <img src='data:image/png;base64,...'>.",
            "notes": "Valida se strip_tags descarta a cadeia Base64 do excerpt e se o Drawer renderiza a imagem inline.",
        },
        "chemistry_cdn_image": {
            "id": "c0fa7391-d699-4ea2-b778-9dff6f30776c",
            "title": "Imagem remota CDN no início do enunciado",
            "description": "Enunciado com imagem hospedada no DigitalOcean Spaces.",
            "notes": "Valida carregamento de asset externo remoto no Drawer e limpeza da tag <img> no card.",
        },
        "math_latex_legacy": {
            "id": "444cfbcd-b2b2-4a5c-afa7-d7ce20fa6708",
            "title": "LaTeX cru sem delimitadores MathJax (caso legado de banco)",
            "description": "Enunciado com macros LaTeX puras sem delimitadores $ ou \\(.",
            "notes": "Exemplo real de questão com LaTeX cru no banco de dados.",
        },
    }

    # 4. Questões (100% REAIS DO BANCO DE DADOS - ZERO DADOS SINTÉTICOS)
    questions_config = [
        # Biologia (Natureza) - 3 Questões Reais do Banco
        {
            "ets": ets_bio,
            "question_id": "5b15fe1e-cd9b-44ef-9343-b41aa56fd9a7", # Cobra-coral
            "enrico_hit": True, # Enrico Acerta (Q1)
        },
        {
            "ets": ets_bio,
            "question_id": "321b93c2-1be2-4989-96cf-81ba18daf937", # Tico-tico
            "enrico_hit": False, # Enrico Erra (Q2) -> Vai para "Questões para revisar"!
        },
        {
            "ets": ets_bio,
            "question_id": "ecc35735-0c1e-4ddf-81ce-5bbfe47da3d6", # Pássaros e nicho ecológico
            "enrico_hit": True, # Enrico Acerta (Q3)
        },
        # História (Humanas) - 3 Questões Reais do Banco
        {
            "ets": ets_his,
            "question_id": "e4122998-509a-4657-9fed-6c2f77595cbe", # República Anos 20
            "enrico_hit": True, # Enrico Acerta (Q4)
        },
        {
            "ets": ets_his,
            "question_id": "75a157b0-8cbb-4bc0-9ad2-f27106b73d6e", # Conceito de revolução
            "enrico_hit": False, # Enrico Erra (Q5) -> Vai para "Questões para revisar"!
        },
        {
            "ets": ets_his,
            "question_id": "7abecd4a-30a3-4f52-9f1c-65dcbbebdd58", # Fato histórico
            "enrico_hit": True, # Enrico Acerta (Q6)
        },
        # Matemática (Matemática) - Questão de Referência com Fórmulas MathML
        {
            "ets": ets_mat,
            "question_id": REFERENCE_EDGE_CASE_QUESTIONS["math_formulas_mathml"]["id"], # 0d6f2abc
            "enrico_hit": False, # Enrico Erra (Q7) -> Vai para "Questões para revisar"!
        },
        {
            "ets": ets_mat,
            "question_id": "00004611-f7e3-4073-ae64-63f9eb0ef0d3", # Equipe de cientistas (Matemática Real)
            "enrico_hit": True, # Enrico Acerta (Q8)
        },
        {
            "ets": ets_mat,
            "question_id": "000062f4-b039-4415-afed-df81ade1d0fd", # Gangorra (Matemática Real)
            "enrico_hit": True, # Enrico Acerta (Q9)
        },
        # Química (Natureza) - Questão 10: Referência com Imagem Base64
        {
            "ets": ets_qui,
            "question_id": REFERENCE_EDGE_CASE_QUESTIONS["chemistry_base64_image"]["id"], # 3d124dcc
            "enrico_hit": False, # Enrico Erra (Q10) -> Vai para "Questões para revisar"!
        },
    ]

    created_questions = []
    ets_order_counter = {}

    for idx, cfg in enumerate(questions_config, 1):
        q = Question.objects.filter(id=cfg["question_id"]).first()
        if not q:
            raise ValueError(f"Questão real {cfg['question_id']} não encontrada no banco de dados!")

        if coordination and not q.coordinations.filter(id=coordination.id).exists():
            q.coordinations.add(coordination)

        correct_opt = q.alternatives.filter(is_correct=True).first()
        wrong_opt = q.alternatives.filter(is_correct=False).first()
        if not correct_opt or not wrong_opt:
            raise ValueError(f"Questão real {q.id} precisa ter pelo menos 1 alternativa correta e 1 incorreta!")

        ets = cfg["ets"]
        ets_order_counter[ets.id] = ets_order_counter.get(ets.id, 0) + 1
        ets_order = ets_order_counter[ets.id]

        eq = ExamQuestion.objects.create(
            exam=exam,
            exam_teacher_subject=ets,
            question=q,
            order=ets_order,
            weight=1.66,
        )
        StatusQuestion.objects.filter(exam_question=eq).update(
            status=StatusQuestion.APPROVED,
            active=True,
        )

        created_questions.append({
            "exam_question": eq,
            "question": q,
            "correct_opt": correct_opt,
            "wrong_opt": wrong_opt,
            "enrico_hit": cfg["enrico_hit"],
        })

    # Fecha o caderno
    exam.status = Exam.CLOSED
    exam.save(update_fields=['status'])

    # 5. Criação da Aplicação
    target_date = now.date()
    start_time = (now - timedelta(hours=2)).time().replace(microsecond=0)
    end_time = (now + timedelta(hours=3)).time().replace(microsecond=0)

    application = Application.objects.create(
        exam=exam,
        date=target_date,
        date_end=target_date,
        start=start_time,
        end=end_time,
        category=Application.MONITORIN_EXAM, # Online
        can_be_done_pc=True,
        can_be_done_cell=True,
        can_be_done_tablet=True,
        subject=exam_name[:150],
        release_result_at_end=True, # LIBERA RESULTADO IMEDIATAMENTE!
        min_time_finish=timedelta(minutes=5),
        max_time_tolerance=timedelta(hours=2),
    )
    application.school_classes.add(school_class)

    # 6. Inscreve alunos da turma
    class_students = list(school_class.students.all()[:6])
    if student not in class_students:
        class_students.insert(0, student)

    application.students.add(*class_students)

    # 7. Simula respostas e finalização de prova
    TARGET_ENRICO_ID = uuid.UUID('b47ce1b3-4883-40b3-bf68-025ca3f2835e')
    for st in class_students:
        is_enrico = (st.id == student.id)
        if is_enrico:
            app_student = ApplicationStudent.objects.create(
                id=TARGET_ENRICO_ID,
                application=application,
                student=st,
            )
        else:
            app_student = ApplicationStudent.objects.create(
                application=application,
                student=st,
            )
        # Finaliza a prova (1 hora atrás)
        app_student.start_time = now - timedelta(minutes=90)
        app_student.end_time = now - timedelta(minutes=30)
        app_student.save(update_fields=['start_time', 'end_time'])

        for item in created_questions:
            eq = item["exam_question"]
            q = item["question"]

            if is_enrico:
                chosen_opt = item["correct_opt"] if item["enrico_hit"] else item["wrong_opt"]
            else:
                # Outros alunos: 60% de chance de acerto para calibrar média da turma
                chosen_opt = item["correct_opt"] if (st.id.int + eq.order) % 3 != 0 else item["wrong_opt"]

            OptionAnswer.objects.create(
                student_application=app_student,
                question_option=chosen_opt,
                status=OptionAnswer.ACTIVE,
                created_by=st.user,
            )

    enrico_app_student = ApplicationStudent.objects.get(id=TARGET_ENRICO_ID)

    print("\n" + "=" * 65)
    print("🎉 APLICAÇÃO MULTI-ÁREA CRIADA E FINALIZADA COM SUCESSO!")
    print("=" * 65)
    print(f"• Caderno: {exam.name}")
    print(f"• Áreas de Conhecimento: '{area_bio}', '{area_his}', '{area_mat}' (3 Áreas distintas!)")
    print(f"• Total de Questões: 10 (3 Biologia + 3 História + 3 Matemática + 1 Química com imagem Base64!)")
    print(f"• Gabarito Enrico: Q1, Q3, Q4, Q6, Q8, Q9 (ACERTO) | Q2, Q5, Q7, Q10 (ERRO)")
    print(f"• ID da Aplicação Student: {enrico_app_student.id}")
    print("-" * 65)
    print("🔗 LINK DIRETO PARA O TESTE NO APP DO ALUNO:")
    print(f"   http://localhost:5173/painel/minhas-provas/{enrico_app_student.id}")
    print(f"   (Ou acesse 'Minhas provas' e abra '{exam.name}')")
    print("=" * 65 + "\n")

    return enrico_app_student


if __name__ == '__main__':
    create_multiarea_application()

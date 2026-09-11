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

    # 2. Seleciona ou cria Disciplinas em 2 Áreas distintas
    sub_bio = Subject.objects.filter(client=client, name__icontains='Biologia').first()
    sub_his = Subject.objects.filter(client=client, name__icontains='História').first()

    if not sub_bio or not sub_his:
        raise ValueError("Não foram encontradas disciplinas de Biologia e História para o cliente.")

    area_bio = sub_bio.knowledge_area.name if sub_bio.knowledge_area else "Ciências da Natureza"
    area_his = sub_his.knowledge_area.name if sub_his.knowledge_area else "Ciências Humanas"

    print(f"🔬 Matéria 1: {sub_bio.name} ➔ Área: {area_bio}")
    print(f"🏛️ Matéria 2: {sub_his.name} ➔ Área: {area_his}")

    # TeacherSubjects já existentes para as matérias
    ts_bio = TeacherSubject.objects.filter(subject=sub_bio).first()
    ts_his = TeacherSubject.objects.filter(subject=sub_his).first()
    teacher_user = (ts_bio.teacher.user if ts_bio and ts_bio.teacher else None) or User.objects.filter(is_superuser=True).first() or enrico_user

    # 3. Criação do Caderno de Prova
    exam_name = "Simulado Multi-Áreas (Natureza e Humanas) - QA"
    Exam.objects.filter(name=exam_name).delete()
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

    # 4. Questões
    # Dados de 6 questões com enunciados limpos e didáticos
    questions_config = [
        # Biologia (Natureza)
        {
            "ets": ets_bio,
            "subject": sub_bio,
            "enunciation": "<p>Em uma população de borboletas da espécie <i>Heliconius</i>, a seleção natural atua na coloração das asas para mimetismo com espécies tóxicas.</p>",
            "options": [
                ("Mimetismo milleriano", True),
                ("Deriva genética aleatória", False),
                ("Efeito fundador populacional", False),
                ("Seleção direcional artificial", False),
            ],
            "enrico_hit": True, # Enrico Acerta (Q1)
        },
        {
            "ets": ets_bio,
            "subject": sub_bio,
            "enunciation": "<p>Durante a fase fotoquímica da fotossíntese nos tilacoides dos cloroplastos, a quebra de moléculas sob ação da luz gera oxigênio gasoso.</p>",
            "options": [
                ("Ciclo de Calvin-Benson", False),
                ("Fotólise da água", True),
                ("Fosforilação oxidativa mitocondrial", False),
                ("Quimiossíntese bacteriana", False),
            ],
            "enrico_hit": False, # Enrico Erra (Q2) -> Vai para "Questões para revisar"!
        },
        {
            "ets": ets_bio,
            "subject": sub_bio,
            "enunciation": "<p>A membrana plasmática possui permeabilidade seletiva, estruturada pelo modelo do mosaico fluido composto de bicamada fosfolipídica.</p>",
            "options": [
                ("Fosfolipídios e proteínas integrais", True),
                ("Parede celulósica impermeável", False),
                ("Monocamada lipídica com quitina", False),
                ("Rede glicídica exclusiva", False),
            ],
            "enrico_hit": True, # Enrico Acerta (Q3)
        },
        # História (Humanas)
        {
            "ets": ets_his,
            "subject": sub_his,
            "enunciation": "<p>A Declaração dos Direitos do Homem e do Cidadão, promulgada em 1789, consagrou princípios fundamentais da Revolução Francesa.</p>",
            "options": [
                ("Liberdade, igualdade e soberania popular", True),
                ("Manutenção dos privilégios do Primeiro Estado", False),
                ("Restauração do absolutismo monárquico", False),
                ("Divisão feudal das propriedades agrárias", False),
            ],
            "enrico_hit": True, # Enrico Acerta (Q4)
        },
        {
            "ets": ets_his,
            "subject": sub_his,
            "enunciation": "<p>Durante a Guerra Fria, a rivalidade geopolítica e ideológica entre EUA e URSS desencadeou alianças militares estratégicas.</p>",
            "options": [
                ("Tratado de Versalhes e Liga das Nações", False),
                ("Pacto de Varsóvia e OTAN", True),
                ("Conferência de Berlim e Santa Aliança", False),
                ("Acordo de Bretton Woods e Mercosul", False),
            ],
            "enrico_hit": False, # Enrico Erra (Q5) -> Vai para "Questões para revisar"!
        },
        {
            "ets": ets_his,
            "subject": sub_his,
            "enunciation": "<p>A crise de 1929 nos Estados Unidos teve como estopim o colapso da Bolsa de Valores de Nova York, impulsionada por superprodução e especulação.</p>",
            "options": [
                ("Quebra da Bolsa de Nova York e New Deal", True),
                ("Início imediato da Guerra da Coreia", False),
                ("Estatização completa dos meios de produção", False),
                ("Fim do padrão-ouro na Europa no século XIX", False),
            ],
            "enrico_hit": True, # Enrico Acerta (Q6)
        },
    ]

    created_questions = []

    for idx, cfg in enumerate(questions_config, 1):
        q = Question.objects.create(
            created_by=teacher_user,
            subject=cfg["subject"],
            grade=grade,
            category=Question.CHOICE,
            enunciation=cfg["enunciation"],
        )
        if coordination:
            q.coordinations.add(coordination)

        correct_opt = None
        wrong_opt = None
        for opt_idx, (text, is_correct) in enumerate(cfg["options"]):
            opt = QuestionOption.objects.create(
                question=q,
                text=text,
                is_correct=is_correct,
                index=opt_idx,
            )
            if is_correct:
                correct_opt = opt
            elif wrong_opt is None:
                wrong_opt = opt

        ets_order = (idx - 1) % 3 + 1
        eq = ExamQuestion.objects.create(
            exam=exam,
            exam_teacher_subject=cfg["ets"],
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
    for st in class_students:
        app_student, _ = ApplicationStudent.objects.get_or_create(
            application=application,
            student=st,
        )
        # Finaliza a prova (1 hora atrás)
        app_student.start_time = now - timedelta(minutes=90)
        app_student.end_time = now - timedelta(minutes=30)
        app_student.save(update_fields=['start_time', 'end_time'])

        is_enrico = (st.id == student.id)

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

    enrico_app_student = ApplicationStudent.objects.filter(application=application, student=student).first()

    print("\n" + "=" * 65)
    print("🎉 APLICAÇÃO MULTI-ÁREA CRIADA E FINALIZADA COM SUCESSO!")
    print("=" * 65)
    print(f"• Caderno: {exam.name}")
    print(f"• Áreas de Conhecimento: '{area_bio}' E '{area_his}' (2 Áreas distintas!)")
    print(f"• Total de Questões: 6 (3 de Biologia + 3 de História)")
    print(f"• Gabarito Enrico: Q1, Q3, Q4, Q6 (ACERTO) | Q2, Q5 (ERRO)")
    print(f"• ID da Aplicação Student: {enrico_app_student.id}")
    print("-" * 65)
    print("🔗 LINK DIRETO PARA O TESTE NO APP DO ALUNO:")
    print(f"   http://localhost:5173/painel/minhas-provas/{enrico_app_student.id}")
    print(f"   (Ou acesse 'Minhas provas' e abra '{exam.name}')")
    print("=" * 65 + "\n")

    return enrico_app_student


if __name__ == '__main__':
    create_multiarea_application()

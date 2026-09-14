#!/usr/bin/env python
"""
Gerador de Aplicação Multi-Área para QA da Tela de Resultados (Lize Edu)
Local: .ai_qa_acervo/scripts/generators/create_multiarea_exam_application.py

Cria um Simulado Multi-Áreas (Ciências da Natureza + Ciências Humanas + Matemática)
com 4 disciplinas (Biologia, Química, História e Matemática) totalizando 30 questões reais,
aplica na turma da aluna Sarah Guimarães Monteiro (ou aluno parametrizado)
e simula respostas com acertos e erros calibrados para testar:
- Alternador "Disciplinas" vs "Área do conhecimento"
- Navegação restrita por Área ("Visualizar" no QuestionReviewSheet)
- Aba "Questões para revisar" (QuestionsToReview) com questões erradas e índices de acerto da turma
- Paginação completa de 30 questões (Página 1: 15 itens | Página 2: 15 itens)
"""

import os
import sys
import argparse
from datetime import timedelta
import uuid
from decimal import Decimal

current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir != '/' and not os.path.exists(os.path.join(current_dir, 'manage.py')):
    current_dir = os.path.dirname(current_dir)
BASE_DIR = current_dir
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiscallizeon.settings')

import django
django.setup()

from django.conf import settings
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

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
from fiscallizeon.answers.models import (
    OptionAnswer,
    TextualAnswer,
    SumAnswer,
    SumAnswerQuestionOption,
    FileAnswer,
)
from fiscallizeon.omr.models import OMRStudents
from fiscallizeon.applications.models import Application, ApplicationStudent


# Questões conhecidas com casos extremos úteis para QA
KNOWN_EDGE_CASES = [
    "0d6f2abc-d76d-4cec-9481-fe757f0ce360", # MathML nativo
    "3d124dcc-964e-4ed5-9a74-2c44fdd172e5", # Imagem Base64 inline
    "c0fa7391-d699-4ea2-b778-9dff6f30776c", # Imagem CDN remota
    "b3300eb0-7b86-4ca8-8ebf-8361784069a0", # Somatório
    "ca93d24c-c95e-42cf-babe-b061a7adaab2", # Arquivo anexado
    "0f52c01f-747c-404e-9c26-1dc55c24b0a3", # Discursiva
]


def pick_real_questions_for_subject(subject, target_count, preferred_ids=None):
    """
    Busca de forma resiliente questões 100% REAIS no banco de dados para a disciplina informada.
    Tenta primeiro os IDs preferidos; caso falte para atingir target_count, busca outras questões reais.
    """
    selected = []
    seen_ids = set()

    # 1. Tenta IDs preferidos que existem no banco
    if preferred_ids:
        for pid in preferred_ids:
            try:
                q = Question.objects.filter(id=pid).first()
                if q and q.id not in seen_ids:
                    # Se for objetiva, garante que tem gabarito correto e incorreto
                    if q.category == Question.CHOICE:
                        if not q.alternatives.filter(is_correct=True).exists() or not q.alternatives.filter(is_correct=False).exists():
                            continue
                    selected.append(q)
                    seen_ids.add(q.id)
                    if len(selected) >= target_count:
                        return selected
            except Exception:
                continue

    # 2. Busca questões diretamente vinculadas à disciplina ou ao nome da disciplina
    candidates = Question.objects.filter(
        subject__name__icontains=subject.name.split()[-1] if subject.name else ''
    ).exclude(id__in=seen_ids)

    # Prioriza questões de múltipla escolha completas
    for q in candidates[:100]:
        if q.category == Question.CHOICE:
            has_correct = q.alternatives.filter(is_correct=True).exists()
            has_wrong = q.alternatives.filter(is_correct=False).exists()
            if has_correct and has_wrong:
                selected.append(q)
                seen_ids.add(q.id)
                if len(selected) >= target_count:
                    return selected

    # 3. Se ainda faltar, busca qualquer questão com alternativas válidas
    if len(selected) < target_count:
        fallback_qs = Question.objects.exclude(id__in=seen_ids)[:100]
        for q in fallback_qs:
            if q.category == Question.CHOICE:
                has_correct = q.alternatives.filter(is_correct=True).exists()
                has_wrong = q.alternatives.filter(is_correct=False).exists()
                if has_correct and has_wrong:
                    selected.append(q)
                    seen_ids.add(q.id)
                    if len(selected) >= target_count:
                        return selected

    return selected


def create_multiarea_application(student_email=None):
    cache.clear()
    now = timezone.localtime()

    # 1. Recupera Aluno Alvo (Sarah Guimarães Monteiro por padrão, ou informado)
    target_email = student_email or 'sarah-guimaraes-monteiro-515-515@email-temp.com.br'
    target_user = User.objects.filter(email=target_email).first()

    if not target_user:
        # Fallback para o Enrico se existir
        target_user = User.objects.filter(email='enrico.a53143@aluno.decisaovirtual.com.br').first()
    if not target_user:
        # Fallback para qualquer aluno com usuário
        student_obj = Student.objects.filter(user__isnull=False).first()
        if student_obj:
            target_user = student_obj.user

    if not target_user:
        raise ValueError("Nenhum usuário de aluno encontrado no banco de dados!")

    student = Student.objects.filter(user=target_user).first()
    client = student.client
    if not client:
        client = Client.objects.filter(name__icontains='Decisão').first() or Client.objects.first()

    # Turma do Aluno
    school_class = student.classes.first()
    if not school_class:
        school_class = SchoolClass.objects.filter(coordination__unity__client=client).first()
        if school_class:
            student.classes.add(school_class)

    coordination = SchoolCoordination.objects.filter(unity__client=client).first()
    grade = school_class.grade if school_class else Grade.objects.filter(teaching_stage__client=client).first()

    print(f"🏫 Cliente: {client.name}")
    print(f"👤 Aluna Alvo: {student.name} ({target_user.email})")
    print(f"🎓 Turma: {school_class.name if school_class else 'Sem Turma'}")

    # 2. Seleciona 4 Disciplinas cobrindo 3 Áreas de Conhecimento
    # Natureza: Biologia e Química | Humanas: História | Matemática: Matemática
    sub_bio = Subject.objects.filter(client=client, name__icontains='Biologia').first()
    sub_qui = Subject.objects.filter(client=client, name__icontains='Química').first()
    sub_his = Subject.objects.filter(client=client, name__icontains='História').first()
    sub_mat = Subject.objects.filter(client=client, name__icontains='Matemática').first()

    # Fallback caso não ache por client específico
    if not sub_bio: sub_bio = Subject.objects.filter(name__icontains='Biologia').first()
    if not sub_qui: sub_qui = Subject.objects.filter(name__icontains='Química').first()
    if not sub_his: sub_his = Subject.objects.filter(name__icontains='História').first()
    if not sub_mat: sub_mat = Subject.objects.filter(name__icontains='Matemática').first()

    area_bio = sub_bio.knowledge_area.name if (sub_bio and sub_bio.knowledge_area) else "Ciências da Natureza e suas Tecnologias - Ensino Médio"
    area_qui = sub_qui.knowledge_area.name if (sub_qui and sub_qui.knowledge_area) else "Ciências da Natureza e suas Tecnologias - Ensino Médio"
    area_his = sub_his.knowledge_area.name if (sub_his and sub_his.knowledge_area) else "Ciências Humanas e Sociais Aplicadas - Ensino Médio"
    area_mat = sub_mat.knowledge_area.name if (sub_mat and sub_mat.knowledge_area) else "Matemática e suas Tecnologias - Ensino Médio"

    print(f"🔬 Matéria 1: {sub_bio.name} ➔ Área: {area_bio}")
    print(f"🧪 Matéria 2: {sub_qui.name} ➔ Área: {area_qui}")
    print(f"🏛️ Matéria 3: {sub_his.name} ➔ Área: {area_his}")
    print(f"📐 Matéria 4: {sub_mat.name} ➔ Área: {area_mat}")

    # TeacherSubjects correspondentes
    ts_bio = TeacherSubject.objects.filter(subject=sub_bio).first()
    ts_qui = TeacherSubject.objects.filter(subject=sub_qui).first()
    ts_his = TeacherSubject.objects.filter(subject=sub_his).first()
    ts_mat = TeacherSubject.objects.filter(subject=sub_mat).first()

    teacher_user = None
    for ts in [ts_bio, ts_qui, ts_his, ts_mat]:
        if ts and ts.teacher and ts.teacher.user:
            teacher_user = ts.teacher.user
            break
    if not teacher_user:
        teacher_user = User.objects.filter(is_superuser=True).first() or target_user

    # 3. Limpeza de cadernos e aplicações anteriores de QA do mesmo nome
    exam_name = "Simulado Multi-Áreas (30 Questões - QA Oficial)"
    old_exams = Exam.objects.filter(name__in=[exam_name, "Simulado Multi-Áreas (Natureza, Humanas e Matemática) - QA"])
    old_apps = Application.objects.all_with_deleted().filter(exam__in=old_exams)
    OMRStudents.objects.filter(application_student__application__in=old_apps).delete()
    SumAnswerQuestionOption.objects.filter(sum_answer__student_application__application__in=old_apps).delete()
    SumAnswer.objects.filter(student_application__application__in=old_apps).delete()
    TextualAnswer.objects.filter(student_application__application__in=old_apps).delete()
    FileAnswer.objects.filter(student_application__application__in=old_apps).delete()
    OptionAnswer.objects.filter(student_application__application__in=old_apps).delete()
    ApplicationStudent.objects.filter(application__in=old_apps).delete()
    old_apps.hard_delete()
    old_exams.delete()

    TARGET_STUDENT_APP_ID = uuid.UUID('c58df2c4-5994-41c4-cf79-136db4e3946f')
    OMRStudents.objects.filter(application_student_id=TARGET_STUDENT_APP_ID).delete()
    SumAnswerQuestionOption.objects.filter(sum_answer__student_application_id=TARGET_STUDENT_APP_ID).delete()
    SumAnswer.objects.filter(student_application_id=TARGET_STUDENT_APP_ID).delete()
    TextualAnswer.objects.filter(student_application_id=TARGET_STUDENT_APP_ID).delete()
    FileAnswer.objects.filter(student_application_id=TARGET_STUDENT_APP_ID).delete()
    OptionAnswer.objects.filter(student_application_id=TARGET_STUDENT_APP_ID).delete()
    ApplicationStudent.objects.filter(id=TARGET_STUDENT_APP_ID).delete()

    # 4. Criação do Caderno de Prova
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

    # Blocos das 4 matérias:
    # 8 questões de Biologia + 7 de Química + 8 de História + 7 de Matemática = 30 Questões no total!
    ets_bio = ExamTeacherSubject.objects.create(exam=exam, teacher_subject=ts_bio, grade=grade, order=1, quantity=8, subject_note=Decimal('10.0'))
    ets_qui = ExamTeacherSubject.objects.create(exam=exam, teacher_subject=ts_qui, grade=grade, order=2, quantity=7, subject_note=Decimal('10.0'))
    ets_his = ExamTeacherSubject.objects.create(exam=exam, teacher_subject=ts_his, grade=grade, order=3, quantity=8, subject_note=Decimal('10.0'))
    ets_mat = ExamTeacherSubject.objects.create(exam=exam, teacher_subject=ts_mat, grade=grade, order=4, quantity=7, subject_note=Decimal('10.0'))

    # 5. Seleção das 30 Questões Reais
    # Preferred IDs conhecidos para cada disciplina
    pref_bio = ["5b15fe1e-cd9b-44ef-9343-b41aa56fd9a7", "321b93c2-1be2-4989-96cf-81ba18daf937", "ecc35735-0c1e-4ddf-81ce-5bbfe47da3d6", "1c739c64-eb95-477b-aac0-b94900413669", "20c4bfca-d00f-4942-927f-488e3a68924c"]
    pref_qui = ["3d124dcc-964e-4ed5-9a74-2c44fdd172e5", "c0fa7391-d699-4ea2-b778-9dff6f30776c", "06e05926-7fd8-4aac-824f-286bbad844b4", "08337f95-5b95-428d-b9a1-af4dd76c0dc2", "325b8815-27f9-4fbf-9a9a-a867d8e8bb65"]
    pref_his = ["e4122998-509a-4657-9fed-6c2f77595cbe", "75a157b0-8cbb-4bc0-9ad2-f27106b73d6e", "7abecd4a-30a3-4f52-9f1c-65dcbbebdd58", "b3300eb0-7b86-4ca8-8ebf-8361784069a0", "ca93d24c-c95e-42cf-babe-b061a7adaab2"]
    pref_mat = ["0d6f2abc-d76d-4cec-9481-fe757f0ce360", "00004611-f7e3-4073-ae64-63f9eb0ef0d3", "000062f4-b039-4415-afed-df81ade1d0fd", "0051e9f5-df84-44fb-8723-540998cfd763", "0f52c01f-747c-404e-9c26-1dc55c24b0a3"]

    qs_bio = pick_real_questions_for_subject(sub_bio, 8, pref_bio)
    qs_qui = pick_real_questions_for_subject(sub_qui, 7, pref_qui)
    qs_his = pick_real_questions_for_subject(sub_his, 8, pref_his)
    qs_mat = pick_real_questions_for_subject(sub_mat, 7, pref_mat)

    # Monta lista de configuração (30 questões)
    # Acertos e Erros calibrados para a Sarah:
    # Sarah erra 2 em cada disciplina para que a aba "Questões para revisar" tenha itens ricos para testar!
    items_plan = []

    # Biologia: 8 questões (Q1 a Q8). Sarah erra Q2 e Q5 (6 acertos, 2 erros)
    for idx, q in enumerate(qs_bio, 1):
        hit = idx not in [2, 5]
        items_plan.append({"ets": ets_bio, "question": q, "student_hit": hit, "subj_name": "Biologia"})

    # Química: 7 questões (Q9 a Q15). Sarah erra Q10 e Q14 (5 acertos, 2 erros)
    for idx, q in enumerate(qs_qui, 1):
        hit = idx not in [2, 6]
        items_plan.append({"ets": ets_qui, "question": q, "student_hit": hit, "subj_name": "Química"})

    # História: 8 questões (Q16 a Q23). Sarah erra Q17 e Q20 (6 acertos, 2 erros)
    for idx, q in enumerate(qs_his, 1):
        hit = idx not in [2, 5]
        items_plan.append({"ets": ets_his, "question": q, "student_hit": hit, "subj_name": "História"})

    # Matemática: 7 questões (Q24 a Q30). Sarah erra Q25 e Q29 (5 acertos, 2 erros)
    for idx, q in enumerate(qs_mat, 1):
        hit = idx not in [2, 6]
        items_plan.append({"ets": ets_mat, "question": q, "student_hit": hit, "subj_name": "Matemática"})

    created_questions = []
    ets_order_counter = {}

    for global_num, item in enumerate(items_plan, 1):
        q = item["question"]
        ets = item["ets"]

        if coordination and not q.coordinations.filter(id=coordination.id).exists():
            q.coordinations.add(coordination)

        correct_opt = None
        wrong_opt = None
        if q.category == Question.CHOICE:
            correct_opt = q.alternatives.filter(is_correct=True).first()
            wrong_opt = q.alternatives.filter(is_correct=False).first()

        ets_order_counter[ets.id] = ets_order_counter.get(ets.id, 0) + 1
        ets_order = ets_order_counter[ets.id]

        eq = ExamQuestion.objects.create(
            exam=exam,
            exam_teacher_subject=ets,
            question=q,
            order=ets_order,
            weight=Decimal('1.0'),
        )
        StatusQuestion.objects.filter(exam_question=eq).update(
            status=StatusQuestion.APPROVED,
            active=True,
        )

        created_questions.append({
            "global_num": global_num,
            "exam_question": eq,
            "question": q,
            "correct_opt": correct_opt,
            "wrong_opt": wrong_opt,
            "student_hit": item["student_hit"],
            "subj_name": item["subj_name"],
        })

    # Fecha o caderno
    exam.status = Exam.CLOSED
    exam.save(update_fields=['status'])

    # 6. Criação da Aplicação
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
        release_result_at_end=True, # Libera resultados imediatamente!
        min_time_finish=timedelta(minutes=5),
        max_time_tolerance=timedelta(hours=2),
    )
    if school_class:
        application.school_classes.add(school_class)

    # 7. Inscreve alunos da turma (Sarah + colegas para calibrar acerto da turma)
    class_students = list(school_class.students.all()[:6]) if school_class else []
    if student not in class_students:
        class_students.insert(0, student)

    application.students.add(*class_students)

    # 8. Simulação de Respostas
    for st in class_students:
        is_target_student = (st.id == student.id)
        if is_target_student:
            app_student = ApplicationStudent.objects.create(
                id=TARGET_STUDENT_APP_ID,
                application=application,
                student=st,
            )
        else:
            app_student = ApplicationStudent.objects.create(
                application=application,
                student=st,
            )

        app_student.start_time = now - timedelta(minutes=90)
        app_student.end_time = now - timedelta(minutes=20)
        app_student.save(update_fields=['start_time', 'end_time'])

        for item in created_questions:
            eq = item["exam_question"]
            q = item["question"]

            if is_target_student:
                hit = item["student_hit"]
            else:
                # Calibra média da turma entre 50% e 75%
                hit = (st.id.int + eq.order) % 3 != 0

            if q.category == Question.CHOICE:
                chosen_opt = item["correct_opt"] if hit else item["wrong_opt"]
                if not chosen_opt:
                    chosen_opt = q.alternatives.first()
                if chosen_opt:
                    OptionAnswer.objects.create(
                        student_application=app_student,
                        question_option=chosen_opt,
                        status=OptionAnswer.ACTIVE,
                        created_by=st.user,
                    )
            elif q.category == Question.TEXTUAL:
                grade_val = Decimal('1.0') if hit else Decimal('0.0')
                TextualAnswer.objects.create(
                    question=q,
                    exam_question=eq,
                    student_application=app_student,
                    content="Resposta formulada pela aluna para validação do cenário de QA.",
                    grade=grade_val,
                    teacher_grade=grade_val,
                    who_corrected=teacher_user,
                    empty=False,
                )
            elif q.category == Question.SUM_QUESTION:
                grade_val = Decimal('1.0') if hit else Decimal('0.0')
                correct_sum = 0
                for idx_opt, opt in enumerate(q.alternatives.all().order_by('index')):
                    if opt.is_correct:
                        correct_sum += (2 ** idx_opt)
                chosen_sum = correct_sum if hit else (correct_sum + 1 if correct_sum > 0 else 2)

                sum_ans = SumAnswer.objects.create(
                    question=q,
                    student_application=app_student,
                    value=chosen_sum,
                    grade=grade_val,
                    created_by=st.user,
                    empty=False,
                )
                for opt in q.alternatives.all():
                    checked = opt.is_correct if hit else not opt.is_correct
                    SumAnswerQuestionOption.objects.create(
                        sum_answer=sum_ans,
                        question_option=opt,
                        checked=checked,
                    )
            elif q.category == Question.FILE:
                grade_val = Decimal('1.0') if hit else Decimal('0.0')
                FileAnswer.objects.create(
                    question=q,
                    exam_question=eq,
                    student_application=app_student,
                    arquivo="answers/file/sample_upload.pdf",
                    grade=grade_val,
                    teacher_grade=grade_val,
                    who_corrected=teacher_user,
                    empty=False,
                )

    target_app_student = ApplicationStudent.objects.get(id=TARGET_STUDENT_APP_ID)

    # 9. Vincula scan OMR se houver
    existing_omr = OMRStudents.objects.exclude(scan_image='').first()
    if existing_omr:
        OMRStudents.objects.create(
            application_student=target_app_student,
            upload=existing_omr.upload,
            scan_image=existing_omr.scan_image.name,
            successful_questions_count=30,
        )

    # Resumo
    errors_list = [f"Q{item['global_num']} ({item['subj_name']})" for item in created_questions if not item['student_hit']]
    hits_count = sum(1 for item in created_questions if item['student_hit'])
    errors_count = len(errors_list)

    print("\n" + "=" * 70)
    print("🎉 APLICAÇÃO MULTI-ÁREA CRIADA E FINALIZADA COM SUCESSO!")
    print("=" * 70)
    print(f"• Caderno: {exam.name}")
    print(f"• Aluna Testada: {student.name} ({target_user.email})")
    print(f"• Turma: {school_class.name if school_class else 'N/A'}")
    print(f"• Total de Questões: 30 questões 100% REAIS do banco")
    print(f"  ↳ Natureza (15 itens): Biologia (8 itens, Q1-Q8) + Química (7 itens, Q9-Q15)")
    print(f"  ↳ Humanas (8 itens): História (8 itens, Q16-Q23)")
    print(f"  ↳ Matemática (7 itens): Matemática (7 itens, Q24-Q30)")
    print(f"• Paginação garantida: Página 1 (Q1-Q15) | Página 2 (Q16-Q30)")
    print(f"• Desempenho Sarah: {hits_count} Acertos | {errors_count} Erros para Revisar")
    print(f"  ↳ Questões para Revisar: {', '.join(errors_list)}")
    print(f"• ID da ApplicationStudent: {target_app_student.id}")
    print("-" * 70)
    print("🔗 LINK DIRETO PARA O TESTE NO APP DO ALUNO:")
    print(f"   http://localhost:5173/painel/minhas-provas/{target_app_student.id}")
    print("=" * 70 + "\n")

    return target_app_student


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Cria aplicação multi-área para testes de QA")
    parser.add_argument("--student-email", "-s", default='sarah-guimaraes-monteiro-515-515@email-temp.com.br', help="E-mail do aluno a ser testado")
    args = parser.parse_args()

    create_multiarea_application(student_email=args.student_email)

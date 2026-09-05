#!/usr/bin/env python
"""
Gerador de Aplicações de Teste para QA (Lize Edu)
Local: .ai_qa_acervo/scripts/generators/create_application.py

Cria sob demanda aplicações (Application) completas e 100% integradas:
- Vinculação com Caderno (Exam) existente ou criação automática encadeada
- Vinculação com Turma (SchoolClass) e Alunos (Student / ApplicationStudent)
- Configuração de data, horário, tipo (Online, Presencial, Lista) e permissões
- Garante alunos ativos e prontos para realização de prova imediata
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

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

from django.conf import settings
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

from django.utils import timezone
from uuid import UUID
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, SchoolCoordination
from fiscallizeon.classes.models import SchoolClass, Grade
from fiscallizeon.students.models import Student
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.answers.models import (
    OptionAnswer,
    TextualAnswer,
    SumAnswer,
    SumAnswerQuestionOption,
)
from fiscallizeon.applications.models import Application, ApplicationStudent

# Importa utilitários do gerador de exames para reuso e encadeamento
from create_exam import (
    get_current_session_user_and_client,
    get_default_user,
    create_exam_with_questions,
)


def simulate_student_answers(application, students=None):
    """
    Simula e persiste respostas completas para os alunos vinculados à aplicação.
    Suporta todos os tipos de questão da plataforma:
    - Objetiva / Múltipla Escolha (CHOICE): com histórico de alteração de alternativas
    - PAS Tipo A: Itens Certo / Errado (com histórico de alteração)
    - PAS Tipo B: Resposta Numérica de 000 a 999
    - PAS Tipo C: Múltipla Escolha de 4 opções
    - PAS Tipo D / Discursivas (TEXTUAL): Fundamentação e cálculos
    - Somatório (SUM_QUESTION): Proposições binárias e valor somado
    - Redação: Texto dissertativo-argumentativo estruturado
    """
    now = timezone.localtime()
    app_students = ApplicationStudent.objects.filter(application=application)
    if students:
        student_ids = [s.id for s in students]
        app_students = app_students.filter(student_id__in=student_ids)

    exam = application.exam
    exam_questions = list(
        ExamQuestion.objects.filter(exam=exam)
        .select_related('question')
        .prefetch_related('question__alternatives')
        .order_by('order')
    )

    total_answers = 0
    total_history_changes = 0

    for st_idx, app_student in enumerate(app_students):
        # 1. Marca ApplicationStudent como finalizado com horários consistentes
        app_student.start_time = now - timedelta(minutes=50)
        app_student.end_time = now - timedelta(minutes=10)
        app_student.save(update_fields=['start_time', 'end_time'])

        student_user = app_student.student.user

        for q_idx, eq in enumerate(exam_questions):
            q = eq.question

            if q.category == Question.CHOICE:
                alternatives = list(q.alternatives.order_by('index'))
                if not alternatives:
                    continue

                # Para o primeiro aluno, nas primeiras 2 questões objetivas, simula troca de alternativa
                # (histórico com marcação anterior inativa + marcação final ativa)
                if st_idx == 0 and q_idx in (0, 1) and len(alternatives) >= 2:
                    # Marcação inicial anterior (35 min atrás)
                    ans_prev = OptionAnswer.objects.create(
                        question_option=alternatives[1],
                        student_application=app_student,
                        status=OptionAnswer.INACTIVE,
                        created_by=student_user,
                    )
                    OptionAnswer.objects.filter(pk=ans_prev.pk).update(created_at=now - timedelta(minutes=35))
                    total_history_changes += 1

                    # Marcação final definitiva (15 min atrás)
                    ans_curr = OptionAnswer.objects.create(
                        question_option=alternatives[0],
                        student_application=app_student,
                        status=OptionAnswer.ACTIVE,
                        created_by=student_user,
                    )
                    OptionAnswer.objects.filter(pk=ans_curr.pk).update(created_at=now - timedelta(minutes=15))
                    total_answers += 2
                else:
                    # Escolhe alternativa
                    chosen_alt = alternatives[0] if (st_idx + q_idx) % 3 != 0 else alternatives[-1]
                    ans = OptionAnswer.objects.create(
                        question_option=chosen_alt,
                        student_application=app_student,
                        status=OptionAnswer.ACTIVE,
                        created_by=student_user,
                    )
                    OptionAnswer.objects.filter(pk=ans.pk).update(created_at=now - timedelta(minutes=25 - (q_idx % 10)))
                    total_answers += 1

            elif q.category == Question.SUM_QUESTION:
                # Questão de Somatório
                alternatives = list(q.alternatives.order_by('index'))
                sum_ans = SumAnswer.objects.create(
                    value=5,  # 01 + 04
                    grade=1.0,
                    question=q,
                    student_application=app_student,
                    created_by=student_user,
                )
                for opt in alternatives:
                    SumAnswerQuestionOption.objects.create(
                        sum_answer=sum_ans,
                        question_option=opt,
                        checked=opt.is_correct,
                    )
                SumAnswer.objects.filter(pk=sum_ans.pk).update(created_at=now - timedelta(minutes=20))
                total_answers += 1

            elif q.category == Question.TEXTUAL:
                if q.b_type_expected_answer is not None:
                    # Questão Tipo B do PAS (Numérica 000-999)
                    expected = q.b_type_expected_answer
                    ans_val = expected if st_idx % 2 == 0 else (expected + 5)
                    ans = TextualAnswer.objects.create(
                        question=q,
                        exam_question=eq,
                        student_application=app_student,
                        content=f"{ans_val:03d}",
                    )
                    TextualAnswer.objects.filter(pk=ans.pk).update(created_at=now - timedelta(minutes=20))
                    total_answers += 1
                elif q.is_essay:
                    # Redação
                    ans = TextualAnswer.objects.create(
                        question=q,
                        exam_question=eq,
                        student_application=app_student,
                        content=(
                            "<p>Texto dissertativo-argumentativo elaborado pelo estudante para a proposta de redação, "
                            "estruturado em introdução, desenvolvimento de argumentos e proposta de intervenção detalhada.</p>"
                        ),
                    )
                    TextualAnswer.objects.filter(pk=ans.pk).update(created_at=now - timedelta(minutes=10))
                    total_answers += 1
                else:
                    # Tipo D do PAS ou Discursiva padrão
                    ans = TextualAnswer.objects.create(
                        question=q,
                        exam_question=eq,
                        student_application=app_student,
                        content=(
                            f"<p>Resposta do estudante para a questão {eq.order}: Apresenta desenvolvimento dos cálculos, "
                            f"justificativa conceitual e conclusão em conformidade com o gabarito.</p>"
                        ),
                    )
                    TextualAnswer.objects.filter(pk=ans.pk).update(created_at=now - timedelta(minutes=15))
                    total_answers += 1

    print(f"📝 Respostas geradas com sucesso: {total_answers} respostas ({total_history_changes} alterações registradas no histórico).")


def find_existing_exam(exam_identifier, client=None):
    """
    Tenta localizar um exame existente por UUID exato ou por busca textual no nome.
    """
    if not exam_identifier:
        return None

    exam_identifier = str(exam_identifier).strip()

    # 1. Tenta UUID exato
    try:
        exam_uuid = UUID(exam_identifier)
        exam = Exam.objects.filter(pk=exam_uuid).first()
        if exam:
            return exam
    except (ValueError, TypeError):
        pass

    # 2. Busca por nome no cliente (se especificado)
    query = Exam.objects.availables()
    if client:
        query = query.filter(coordinations__unity__client=client)

    exact_match = query.filter(name__iexact=exam_identifier).first()
    if exact_match:
        return exact_match

    partial_match = query.filter(name__icontains=exam_identifier).order_by('-created_at').first()
    if partial_match:
        return partial_match

    # Fallback global sem filtro de cliente caso não encontre
    return Exam.objects.availables().filter(name__icontains=exam_identifier).order_by('-created_at').first()


def find_or_select_school_class(client, class_name=None, school_year=None):
    """
    Localiza uma turma existente por nome/UUID ou seleciona automaticamente
    uma turma existente do cliente que possua alunos matriculados.
    """
    target_year = school_year or timezone.localtime().date().year
    classes_qs = SchoolClass.objects.filter(coordination__unity__client=client)

    if class_name:
        class_name_str = str(class_name).strip()
        # 1. Tenta UUID exato
        try:
            class_uuid = UUID(class_name_str)
            found = classes_qs.filter(pk=class_uuid).first()
            if found:
                return found
        except (ValueError, TypeError):
            pass

        # 2. Tenta por nome exato ou parcial
        found = classes_qs.filter(name__iexact=class_name_str).first()
        if not found:
            found = classes_qs.filter(name__icontains=class_name_str).order_by('-school_year', 'name').first()

        if found:
            return found
        else:
            print(f"⚠️ Turma '{class_name}' não encontrada no cliente {client.name}. Selecionando turma ativa automaticamente...")

    # Seleção automática: turma com alunos no ano letivo atual
    class_with_students = classes_qs.filter(school_year=target_year, students__isnull=False).distinct().first()
    if class_with_students:
        return class_with_students

    # Fallback: qualquer ano letivo que possua alunos
    class_with_students_any_year = classes_qs.filter(students__isnull=False).order_by('-school_year').distinct().first()
    if class_with_students_any_year:
        return class_with_students_any_year

    return classes_qs.first()


def get_existing_students_for_class(client, school_class, count=None, reset_passwords=True):
    """
    Obtém alunos já existentes na turma.
    - Se count for informado (> 0), limita aos primeiros `count` alunos.
    - Se count for None ou 0, vincula todos os alunos existentes da turma.
    - Se reset_passwords for True, garante que a senha dos alunos vinculados seja 123456 para testes de QA.
    """
    students_qs = school_class.students.filter(client=client).select_related('user').distinct()
    if not students_qs.exists():
        students_qs = school_class.students.all().select_related('user').distinct()

    if not students_qs.exists():
        print(f"⚠️ A turma '{school_class.name}' não possui alunos matriculados. Buscando alunos existentes do cliente {client.name}...")
        students_qs = Student.objects.filter(client=client, user__isnull=False).select_related('user').order_by('name')

    students = list(students_qs)
    if not students:
        print(f"❌ Nenhum aluno existente encontrado para o cliente {client.name}.")
        sys.exit(1)

    if count and count > 0:
        students = students[:count]

    if reset_passwords:
        for st in students:
            if st.user:
                st.user.set_password('123456')
                st.user.is_active = True
                st.user.save(update_fields=['password', 'is_active'])

    return students


def create_application(
    exam_identifier=None,
    create_exam_flag=False,
    objective_count=5,
    discursive_count=0,
    essay_count=0,
    random_questions=False,
    random_alternatives=False,
    exam_name=None,
    subject_name=None,
    teacher_name=None,
    client_name=None,
    category_str='online',
    class_name=None,
    students_count=None,
    reset_passwords=True,
    is_pas=False,
    sum_count=0,
    answered=False,
    app_date=None,
    start_time=None,
    end_time=None,
    username=None,
):
    """
    Cria uma aplicação completa no banco de dados para testes de QA utilizando alunos existentes.
    """
    session_user, session_client = get_current_session_user_and_client()

    # 1. Identificar Usuário e Cliente
    user = None
    if username:
        user = User.objects.filter(username=username).first() or User.objects.filter(email=username).first()
    if not user:
        user = session_user or get_default_user()

    client = None
    if client_name:
        client = Client.objects.filter(name__icontains=client_name).first()
    if not client:
        client = session_client or getattr(user, 'client', None)
        if not client:
            clients_cache = user.get_clients_cache() if user else []
            if clients_cache:
                client = Client.objects.filter(pk__in=clients_cache).first()
            else:
                client = Client.objects.first()

    if not client:
        print("❌ Erro: Nenhum cliente válido encontrado.")
        sys.exit(1)

    print(f"🏢 Cliente selecionado: {client.name} (ID: {client.id})")

    # 2. Resolver Caderno (Exam): Existente vs. Criação Encadeada
    exam = None
    if exam_identifier and not create_exam_flag:
        exam = find_existing_exam(exam_identifier, client=client)
        if exam:
            print(f" Caderno existente encontrado: '{exam.name}' (ID: {exam.id})")
        else:
            print(f"⚠️ Caderno '{exam_identifier}' não encontrado no cliente {client.name}. Criando novo caderno sob medida...")

    if not exam:
        print("⚙️ Criando caderno de prova encadeado para a aplicação...")
        exam = create_exam_with_questions(
            name=exam_name or (f"[QA] Caderno Modelo PAS {timezone.now().strftime('%d/%m %H:%M')}" if is_pas else f"[QA] Caderno para Aplicação {timezone.now().strftime('%d/%m %H:%M')}"),
            objective_count=objective_count if objective_count is not None else 5,
            discursive_count=discursive_count if discursive_count is not None else 0,
            essay_count=essay_count if essay_count is not None else 0,
            sum_count=sum_count if sum_count is not None else 0,
            random_questions=random_questions,
            random_alternatives=random_alternatives,
            username=user.username if user else None,
            subject_name=subject_name,
            client_name=client.name,
            teacher_name=teacher_name,
            is_pas=is_pas,
        )

    # 3. Identificar Turma Existente (SchoolClass)
    now_local = timezone.localtime()
    target_date = app_date or now_local.date()
    current_year = target_date.year

    school_class = find_or_select_school_class(client, class_name=class_name, school_year=current_year)
    if not school_class:
        print(f"❌ Nenhuma turma existente encontrada para o cliente {client.name}.")
        sys.exit(1)

    print(f"🏫 Turma selecionada: '{school_class.name}' (Ano: {school_class.school_year})")

    # 4. Alunos Existentes da Turma
    students = get_existing_students_for_class(
        client=client,
        school_class=school_class,
        count=students_count,
        reset_passwords=reset_passwords,
    )
    total_class_students = school_class.students.count()
    if students_count and students_count > 0:
        print(f"👥 Alunos vinculados à aplicação: {len(students)} (limite solicitado de {total_class_students} da turma)")
    else:
        print(f"👥 Alunos vinculados à aplicação: {len(students)} (todos da turma '{school_class.name}')")

    # 5. Configurar Categoria
    category_map = {
        'online': Application.MONITORIN_EXAM,
        'presential': Application.PRESENTIAL,
        'presencial': Application.PRESENTIAL,
        'homework': Application.HOMEWORK,
        'lista': Application.HOMEWORK,
    }
    app_category = category_map.get((category_str or 'online').lower(), Application.MONITORIN_EXAM)
    category_display_map = {
        Application.MONITORIN_EXAM: "Online",
        Application.PRESENTIAL: "Presencial",
        Application.HOMEWORK: "Lista de Exercícios",
    }

    # 6. Datas e Horários
    # Por padrão, inicia 30 minutos atrás para já estar ativa e termina daqui a 4 horas
    if not start_time:
        start_time = (now_local - timedelta(minutes=30)).time().replace(microsecond=0)
    if not end_time:
        end_time = (now_local + timedelta(hours=4)).time().replace(microsecond=0)

    # 7. Criar a Aplicação
    application = Application.objects.create(
        exam=exam,
        date=target_date,
        start=start_time,
        end=end_time,
        category=app_category,
        can_be_done_pc=True,
        can_be_done_cell=True,
        can_be_done_tablet=True,
        subject=exam.name[:150],
        min_time_finish=timedelta(minutes=5),
        max_time_tolerance=timedelta(hours=2),
    )

    # Vincula a turma e os alunos
    application.school_classes.add(school_class)
    application.students.add(*students)

    # 8. Simular respostas se solicitado
    if answered:
        print("⚙️ Gerando respostas completas dos alunos na prova (simulação com histórico)...")
        simulate_student_answers(application, students)

    status_str = "🟢 Ativa e RESPONDIDA pelos alunos!" if answered else "🟢 Ativa para realização agora!"

    print("\n" + "=" * 60)
    print("✅ APLICAÇÃO CRIADA COM SUCESSO PARA QA!")
    print("=" * 60)
    print(f"• ID da Aplicação: {application.id}")
    print(f"• Tipo / Modalidade: {category_display_map.get(app_category, 'Online')}")
    print(f"• Data: {application.date.strftime('%d/%m/%Y')} | Horário: {application.start.strftime('%H:%M')} às {application.end.strftime('%H:%M')}")
    print(f"• Status: {status_str}")
    print("-" * 60)
    print(f"• Caderno vinculado: {exam.name} (ID: {exam.id})")
    print(f"• Formato do Caderno: {'Modelo PAS (UnB)' if exam.exam_format == Exam.PAS else 'Padrão'}")
    print(f"• Total de questões no caderno: {exam.questions.count()}")
    print(f"• Turma vinculada: {school_class.name} (Ano: {school_class.school_year})")
    print(f"• Total de alunos inscritos na aplicação: {len(students)}")
    print("-" * 60)
    print(" Alunos existentes disponíveis para login imediato (Senha: 123456):")
    for idx, st in enumerate(students[:8], 1):
        u_email = st.user.email if st.user else 'Sem email'
        print(f"   {idx}. {st.name} | Login: {u_email}")
    if len(students) > 8:
        print(f"   ... e mais {len(students) - 8} alunos vinculados à aplicação.")
    print("=" * 60)
    if answered:
        answered_app_students = (
            ApplicationStudent.objects.filter(application=application, student__in=students)
            .select_related('student')
            .order_by('student__name')[:3]
        )
        for ast in answered_app_students:
            print(f"   • API Histórico ({ast.student.name}): http://localhost:8000/api/v2/application-students/{ast.id}/answer-history/")
    print("=" * 60 + "\n")

    return application


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Gerador de Aplicações de Teste para QA (Lize Edu)"
    )
    parser.add_argument(
        '-e', '--exam',
        type=str,
        default=None,
        help="ID ou Nome do caderno de provas existente a ser vinculado",
    )
    parser.add_argument(
        '--create-exam',
        action='store_true',
        help="Forçar a criação de um novo caderno para esta aplicação",
    )
    parser.add_argument(
        '--pas',
        action='store_true',
        help="Criar caderno encadeado no formato Modelo PAS (UnB)",
    )
    parser.add_argument(
        '--answered',
        action='store_true',
        help="Preencher e responder a prova automaticamente para os alunos da aplicação",
    )
    parser.add_argument(
        '-cat', '--category',
        type=str,
        default='online',
        choices=['online', 'presential', 'presencial', 'homework', 'lista'],
        help="Tipo da aplicação (online, presential, homework)",
    )
    parser.add_argument(
        '-c', '--client',
        type=str,
        default=None,
        help="Nome ou filtro do cliente",
    )
    parser.add_argument(
        '-cl', '--class-name', '--school-class',
        type=str,
        default=None,
        dest='class_name',
        help="Opcional: Nome ou ID da turma existente (ex: 'F9MA', '3ª Série A'). Se omitido, seleciona turma ativa com alunos.",
    )
    parser.add_argument(
        '-sc', '--students-count',
        type=int,
        default=None,
        help="Opcional: Quantidade de alunos existentes a vincular (ex: 3, 5, 10). Se omitido, vincula todos da turma.",
    )
    parser.add_argument(
        '--no-reset-passwords',
        action='store_true',
        help="Opcional: Não resetar senhas dos alunos vinculados para 123456",
    )
    # Parâmetros de criação de caderno quando encadeado
    parser.add_argument(
        '-obj', '--objective',
        type=int,
        default=5,
        help="Quantidade de objetivas se criar caderno padrão",
    )
    parser.add_argument(
        '-disc', '--discursive',
        type=int,
        default=0,
        help="Quantidade de discursivas se criar caderno",
    )
    parser.add_argument(
        '-ess', '--essay',
        type=int,
        default=0,
        help="Quantidade de redações se criar caderno",
    )
    parser.add_argument(
        '-sum', '--sum',
        type=int,
        default=0,
        dest='sum_count',
        help="Quantidade de questões de somatório se criar caderno",
    )
    parser.add_argument(
        '-rq', '--random-questions',
        action='store_true',
        help="Embaralhar questões se criar caderno",
    )
    parser.add_argument(
        '-ra', '--random-alternatives',
        action='store_true',
        help="Embaralhar alternativas se criar caderno",
    )
    parser.add_argument(
        '-en', '--exam-name',
        type=str,
        default=None,
        help="Nome personalizado se criar novo caderno",
    )
    parser.add_argument(
        '-s', '--subject',
        type=str,
        default=None,
        help="Disciplina da prova se criar caderno",
    )
    parser.add_argument(
        '-t', '--teacher',
        type=str,
        default=None,
        help="Professor se criar caderno",
    )
    parser.add_argument(
        '-u', '--user',
        type=str,
        default=None,
        help="Usuário criador (ex: fiscallize_geral)",
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    create_application(
        exam_identifier=args.exam,
        create_exam_flag=args.create_exam or args.pas or (args.sum_count > 0),
        objective_count=args.objective,
        discursive_count=args.discursive,
        essay_count=args.essay,
        sum_count=args.sum_count,
        random_questions=args.random_questions,
        random_alternatives=args.random_alternatives,
        exam_name=args.exam_name,
        subject_name=args.subject,
        teacher_name=args.teacher,
        client_name=args.client,
        category_str=args.category,
        class_name=args.class_name,
        students_count=args.students_count,
        reset_passwords=not args.no_reset_passwords,
        is_pas=args.pas,
        answered=args.answered,
        username=args.user,
    )

#!/usr/bin/env python
"""
Gerador de Dados para Testes de Ensalamento e Malote (Lize Edu)
Local: .ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py
Slash command: /qa-criar-ensalamento-misto

Cria aplicações e ensalamentos sincronizados com alunos reais:
- Caderno 1: Somatório até 15 questões (10Q) -> Cartão somatório padrão
- Caderno 2: Somatório amplo (>15 questões) + objetivas -> Cartão somatório expandido + folha extra
- Caderno 3: Só objetivas (10Q) -> Cartão padrão / modelo do modal
- Caderno 4: Discursiva / redação -> Folha de respostas discursiva
- Caderno 5: Formato PAS -> Caderno com trava de bloqueio para teste negativo

Opções:
  --date, -d             Data (AAAA-MM-DD, 'hoje', 'amanha', '+1') [default: hoje]
  --client, -c           Nome ou UUID do cliente [default: sessão ativa / auto]
  --start, -s            Horário inicial [default: 14:00]
  --end, -e              Horário final [default: 18:00]
  --coordination         Nome ou UUID da coordenação
  --turma, --class-name  Nome da turma
  --students-per-app     Quantidade de alunos por aplicação [default: 2]
  --type, -t             Tipo de geração ('mixed', 'all', 'sum', 'choice') [default: 'mixed']
  --all-types, --suite   Cria todos os 3 tipos de ensalamento + aplicações livres de teste na UI
  --ensalar              Cria o Ensalamento (RoomDistribution) completo e distribui os alunos
  --keep-free-apps       Garante aplicações livres para teste de cadastro na UI mesmo com --ensalar
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir != '/' and not os.path.exists(os.path.join(current_dir, 'manage.py')):
    current_dir = os.path.dirname(current_dir)
BASE_DIR = current_dir
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiscallizeon.settings')

import django
django.setup()

from django.utils import timezone
from django.contrib.sessions.models import Session
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.students.models import Student
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.distribution.models import Room, RoomDistribution
from fiscallizeon.distribution import functions


def get_active_session_client_and_user():
    """Detecta usuário e cliente da sessão ativa no localhost."""
    now = timezone.now()
    sessions = Session.objects.filter(expire_date__gt=now).order_by('-expire_date')
    if not sessions.exists():
        sessions = Session.objects.order_by('-expire_date')

    for session in sessions:
        try:
            data = session.get_decoded()
            uid = data.get('_auth_user_id')
            if uid:
                user = User.objects.filter(pk=uid).first()
                if user:
                    client = getattr(user, 'client', None)
                    if not client:
                        clients = user.get_clients_cache()
                        if clients:
                            client = Client.objects.filter(pk__in=clients).first()
                    if client:
                        return client, user
        except Exception:
            continue
    return None, None


def parse_target_date(date_str):
    """Converte strings flexíveis de data para datetime.date."""
    if not date_str or date_str.lower() in ['hoje', 'today']:
        return timezone.localdate()
    if date_str.lower() in ['amanha', 'amanhã', 'tomorrow']:
        return timezone.localdate() + timedelta(days=1)
    if date_str.startswith('+') and date_str[1:].isdigit():
        return timezone.localdate() + timedelta(days=int(date_str[1:]))

    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Formato de data inválido: {date_str}. Use AAAA-MM-DD ou 'hoje'.")


def resolve_client(client_arg):
    """Resolve o cliente por UUID, nome ou sessão ativa."""
    if client_arg:
        try:
            client = Client.objects.filter(pk=client_arg).first()
            if client:
                return client
        except Exception:
            pass
        client = Client.objects.filter(name__icontains=client_arg).first()
        if client:
            return client

    client, _ = get_active_session_client_and_user()
    if client:
        return client

    client = Client.objects.filter(has_distribution=True).first()
    if not client:
        client = Client.objects.first()
    return client


def create_application_with_students(exam, app_students, target_date, start_time, end_time, school_class):
    """Cria uma aplicação presencial e vincula alunos exclusivos."""
    app = Application.objects.create(
        exam=exam,
        date=target_date,
        start=start_time,
        end=end_time,
        category=Application.PRESENTIAL,
        room_distribution=None,
    )
    app.school_classes.add(school_class)
    app.students.set(app_students)
    return app


def get_or_create_qa_exams(coordination, client):
    """Garante a existência e integridade das questões dos 5 cadernos QA."""
    # Caderno 1: Somatório até 15 questões (10Q)
    exam_sum_10 = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 1 - Somatório 10Q').first()
    if not exam_sum_10:
        exam_sum_10 = mixer.blend(Exam, name='[QA] Caderno 1 - Somatório 10Q', exam_format=Exam.STANDARD)
        exam_sum_10.coordinations.add(coordination)
    if not exam_sum_10.examquestion_set.exists():
        for i in range(1, 11):
            q = mixer.blend(Question, client=client, category=Question.SUM_QUESTION, enunciation=f'Questão Somatório QA {i}')
            mixer.blend(QuestionOption, question=q, text='(01) Proposição 01', is_correct=True)
            mixer.blend(QuestionOption, question=q, text='(02) Proposição 02', is_correct=False)
            mixer.blend(ExamQuestion, exam=exam_sum_10, question=q, order=i)

    # Caderno 2: Somatório amplo (>15 questões) + objetivas
    exam_sum_wide = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 2 - Somatório Amplo 18Q + 5 Obj').first()
    if not exam_sum_wide:
        exam_sum_wide = mixer.blend(Exam, name='[QA] Caderno 2 - Somatório Amplo 18Q + 5 Obj', exam_format=Exam.STANDARD)
        exam_sum_wide.coordinations.add(coordination)
    if not exam_sum_wide.examquestion_set.exists():
        for i in range(1, 19):
            q = mixer.blend(Question, client=client, category=Question.SUM_QUESTION, enunciation=f'Questão Somatório Amplo QA {i}')
            mixer.blend(QuestionOption, question=q, text='(01) Proposição 01', is_correct=True)
            mixer.blend(QuestionOption, question=q, text='(02) Proposição 02', is_correct=False)
            mixer.blend(ExamQuestion, exam=exam_sum_wide, question=q, order=i)
        for i in range(19, 24):
            q = mixer.blend(Question, client=client, category=Question.CHOICE, enunciation=f'Questão Objetiva Extra {i}')
            mixer.blend(QuestionOption, question=q, text='Opção A', is_correct=True)
            mixer.blend(QuestionOption, question=q, text='Opção B', is_correct=False)
            mixer.blend(ExamQuestion, exam=exam_sum_wide, question=q, order=i)

    # Caderno 3: Só Objetivas
    exam_choice = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 3 - Objetivas 10Q').first()
    if not exam_choice:
        exam_choice = mixer.blend(Exam, name='[QA] Caderno 3 - Objetivas 10Q', exam_format=Exam.STANDARD)
        exam_choice.coordinations.add(coordination)
    if not exam_choice.examquestion_set.exists():
        for i in range(1, 11):
            q = mixer.blend(Question, client=client, category=Question.CHOICE, enunciation=f'Questão Objetiva QA {i}')
            mixer.blend(QuestionOption, question=q, text='Opção A', is_correct=True)
            mixer.blend(QuestionOption, question=q, text='Opção B', is_correct=False)
            mixer.blend(ExamQuestion, exam=exam_choice, question=q, order=i)

    # Caderno 4: Redação / Discursiva
    exam_disc = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 4 - Redação e Discursiva').first()
    if not exam_disc:
        exam_disc = mixer.blend(Exam, name='[QA] Caderno 4 - Redação e Discursiva', exam_format=Exam.STANDARD)
        exam_disc.coordinations.add(coordination)
    if not exam_disc.examquestion_set.exists():
        q = mixer.blend(Question, client=client, category=Question.TEXTUAL, enunciation='Tema de Redação / Questão Discursiva QA')
        mixer.blend(ExamQuestion, exam=exam_disc, question=q, order=1)

    # Caderno 5: Formato PAS (para teste negativo de bloqueio)
    exam_pas = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 5 - Formato PAS (Bloqueio)').first()
    if not exam_pas:
        exam_pas = mixer.blend(Exam, name='[QA] Caderno 5 - Formato PAS (Bloqueio)', exam_format=Exam.PAS)
        exam_pas.coordinations.add(coordination)

    return exam_sum_10, exam_sum_wide, exam_choice, exam_disc, exam_pas


def main():
    parser = argparse.ArgumentParser(
        description='Gerador unificado de dados para testes de ensalamento e malote (Task #86ak8wuvc).'
    )
    parser.add_argument('--date', '-d', type=str, default=None,
                        help='Data da aplicação (AAAA-MM-DD, "hoje", "amanha", "+1"). Default: hoje.')
    parser.add_argument('--client', '-c', type=str, default=None,
                        help='Nome ou UUID do cliente. Default: detecta da sessão ativa.')
    parser.add_argument('--client-id', type=str, default=None,
                        help='Alias para UUID do cliente.')
    parser.add_argument('--start', '-s', type=str, default='14:00',
                        help='Horário de início (HH:MM). Default: 14:00.')
    parser.add_argument('--end', '-e', type=str, default='18:00',
                        help='Horário de término (HH:MM). Default: 18:00.')
    parser.add_argument('--coordination', type=str, default=None,
                        help='Nome ou UUID da coordenação escolar.')
    parser.add_argument('--turma', '--class-name', dest='class_name', type=str, default=None,
                        help='Nome da turma para vinculação.')
    parser.add_argument('--students-per-app', type=int, default=2,
                        help='Número de alunos por aplicação. Default: 2.')
    parser.add_argument('--type', '-t', choices=['mixed', 'all', 'sum', 'choice'], default='mixed',
                        help='Tipo de ensalamento a gerar: mixed (padrão), all (suíte completa), sum (só somatório), choice (só objetivas).')
    parser.add_argument('--all-types', '--suite', dest='all_types', action='store_true',
                        help='Atalho para criar todos os 3 tipos de ensalamento + aplicações livres.')
    parser.add_argument('--ensalar', '--create-distribution', dest='create_distribution', action='store_true',
                        help='Cria o objeto RoomDistribution no banco e distribui os alunos nas salas.')
    parser.add_argument('--keep-free-apps', dest='keep_free_apps', action='store_true',
                        help='Garante aplicações livres para teste de cadastro manual na UI mesmo com --ensalar.')

    args = parser.parse_args()

    # 1. Resolver Cliente
    client_param = args.client or args.client_id
    client = resolve_client(client_param)
    if not client:
        print("❌ Nenhum cliente encontrado. Verifique o banco ou especifique --client.")
        sys.exit(1)

    Client.objects.filter(pk=client.pk).update(has_distribution=True, has_sum_question=True)
    client.refresh_from_db(fields=['has_distribution', 'has_sum_question'])

    print("=" * 80)
    print("🚀 SETUP UNIFICADO DE DADOS DE ENSALAMENTO E MALOTE (/qa-criar-ensalamento-misto)")
    print("=" * 80)
    print(f"🏢 Cliente:       {client.name} (UUID: {client.id})")

    # 2. Coordenação e Salas
    coordinations = SchoolCoordination.objects.filter(unity__client=client)
    if args.coordination:
        try:
            coordination = coordinations.filter(pk=args.coordination).first()
        except Exception:
            coordination = None
        if not coordination:
            coordination = coordinations.filter(name__icontains=args.coordination).first()
    else:
        coordination = coordinations.filter(name__icontains='médio').first() or coordinations.first()

    if not coordination:
        unity = mixer.blend(Unity, client=client, name='Unidade QA')
        coordination = mixer.blend(SchoolCoordination, unity=unity, name='Coordenação QA')

    rooms_qs = Room.objects.filter(coordination=coordination)
    if rooms_qs.count() < 2:
        mixer.blend(Room, coordination=coordination, name='Sala QA 101', capacity=40)
        mixer.blend(Room, coordination=coordination, name='Sala QA 102', capacity=40)
        rooms_qs = Room.objects.filter(coordination=coordination)

    print(f"📍 Coordenação:   {coordination.name} | Salas: {[r.name for r in rooms_qs[:3]]}")

    # 3. Turma Ativa e Alunos Reais
    current_year = timezone.now().year
    students_per_app = max(1, args.students_per_app)

    classes_qs = SchoolClass.objects.filter(
        coordination=coordination,
        school_year=current_year,
        temporary_class=False,
    )
    if args.class_name:
        school_class = (
            classes_qs.filter(name__icontains=args.class_name).first()
            or SchoolClass.objects.filter(coordination=coordination, name__icontains=args.class_name).first()
        )
    else:
        school_class = classes_qs.filter(students__user__is_active=True).distinct().first() or classes_qs.first()

    if not school_class:
        school_class = SchoolClass.objects.filter(coordination=coordination).first()

    if school_class and school_class.school_year != current_year:
        school_class.school_year = current_year
        school_class.save(update_fields=['school_year'])

    real_students = list(
        Student.objects.filter(
            client=client,
            user__is_active=True,
            classes=school_class,
        ).exclude(name__startswith='Aluno ').distinct().order_by('name')
    )

    if len(real_students) < 25:
        more_students = list(
            Student.objects.filter(
                client=client,
                user__is_active=True,
                classes__coordination=coordination,
            ).exclude(name__startswith='Aluno ').distinct().order_by('name')
        )
        for s in more_students:
            if s not in real_students:
                real_students.append(s)

    for st in real_students:
        st.classes.add(school_class)
        if st.user:
            st.user.set_password('123456')
            st.user.is_active = True
            st.user.save(update_fields=['password', 'is_active'])

    print(f"👥 Turma:         {school_class.name} ({current_year}) | {len(real_students)} alunos reais ativos")

    # 4. Data e Horário
    target_date = parse_target_date(args.date)
    start_time = args.start
    end_time = args.end
    print(f"📅 Data da Prova: {target_date.strftime('%d/%m/%Y')} | Horário: {start_time} às {end_time}")

    # 5. Cadernos de Prova
    exam_sum_10, exam_sum_wide, exam_choice, exam_disc, exam_pas = get_or_create_qa_exams(coordination, client)
    print("\n📚 Cadernos de Prova Validados:")
    print(f"  ✓ {exam_sum_10.name} (has_sum={exam_sum_10.has_sum_questions})")
    print(f"  ✓ {exam_sum_wide.name} (has_sum={exam_sum_wide.has_sum_questions}, is_sum_only={exam_sum_wide.is_sum_only})")
    print(f"  ✓ {exam_choice.name} (has_sum={exam_choice.has_sum_questions})")
    print(f"  ✓ {exam_disc.name} (has_sum={exam_disc.has_sum_questions})")
    print(f"  ✓ {exam_pas.name} (exam_format=PAS) [Caderno para teste de trava]")

    # 6. Modo de Execução
    is_suite = args.all_types or args.type == 'all'
    student_idx = 0

    if is_suite:
        print("\n🏛️ [MODO SUÍTE COMPLETA] Gerando todos os tipos de ensalamento e aplicações livres:")

        # Tipo 1: Ensalamento Misto
        st_m_1 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
        st_m_2 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
        st_m_3 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
        st_m_4 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app

        app_m_1 = create_application_with_students(exam_sum_10, st_m_1, target_date, start_time, end_time, school_class)
        app_m_2 = create_application_with_students(exam_sum_wide, st_m_2, target_date, start_time, end_time, school_class)
        app_m_3 = create_application_with_students(exam_choice, st_m_3, target_date, start_time, end_time, school_class)
        app_m_4 = create_application_with_students(exam_disc, st_m_4, target_date, start_time, end_time, school_class)

        distrib_misto = RoomDistribution.objects.create(
            category=RoomDistribution.NAME_GRADE,
            status=RoomDistribution.WAITING_EXPORT,
        )
        for a in [app_m_1, app_m_2, app_m_3, app_m_4]:
            a.room_distribution = distrib_misto
            a.save(update_fields=['room_distribution'])

        functions.distribute_students_grade(distrib_misto, rooms_qs)
        print(f"  ✓ [1/3] Ensalamento MISTO criado! ID: {distrib_misto.pk}")
        print(f"        Aplicações: 4 cadernos mistos | Alunos: {len(st_m_1+st_m_2+st_m_3+st_m_4)}")

        # Tipo 2: Ensalamento 100% Somatório
        st_s_1 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
        st_s_2 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app

        app_s_1 = create_application_with_students(exam_sum_10, st_s_1, target_date, start_time, end_time, school_class)
        app_s_2 = create_application_with_students(exam_sum_wide, st_s_2, target_date, start_time, end_time, school_class)

        distrib_sum = RoomDistribution.objects.create(
            category=RoomDistribution.NAME_GRADE,
            status=RoomDistribution.WAITING_EXPORT,
        )
        for a in [app_s_1, app_s_2]:
            a.room_distribution = distrib_sum
            a.save(update_fields=['room_distribution'])

        functions.distribute_students_grade(distrib_sum, rooms_qs)
        print(f"  ✓ [2/3] Ensalamento 100% SOMATÓRIO criado! ID: {distrib_sum.pk}")
        print(f"        Aplicações: 2 cadernos de somatório | Alunos: {len(st_s_1+st_s_2)}")

        # Tipo 3: Ensalamento 100% Objetivas
        st_o_1 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
        st_o_2 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app

        app_o_1 = create_application_with_students(exam_choice, st_o_1, target_date, start_time, end_time, school_class)
        app_o_2 = create_application_with_students(exam_disc, st_o_2, target_date, start_time, end_time, school_class)

        distrib_obj = RoomDistribution.objects.create(
            category=RoomDistribution.NAME_GRADE,
            status=RoomDistribution.WAITING_EXPORT,
        )
        for a in [app_o_1, app_o_2]:
            a.room_distribution = distrib_obj
            a.save(update_fields=['room_distribution'])

        functions.distribute_students_grade(distrib_obj, rooms_qs)
        print(f"  ✓ [3/3] Ensalamento 100% OBJETIVAS criado! ID: {distrib_obj.pk}")
        print(f"        Aplicações: 2 cadernos de objetivas | Alunos: {len(st_o_1+st_o_2)}")

        # Aplicações Livres
        st_f_1 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
        st_f_2 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
        st_f_3 = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app

        app_free_sum = create_application_with_students(exam_sum_10, st_f_1, target_date, start_time, end_time, school_class)
        app_free_obj = create_application_with_students(exam_choice, st_f_2, target_date, start_time, end_time, school_class)
        app_free_pas = create_application_with_students(exam_pas, st_f_3, target_date, start_time, end_time, school_class)

        print(f"  ✓ [LIVRES] 3 Aplicações disponíveis para teste na tela de criação (/ensalamento/criar/):")
        print(f"        1. Somatório 10Q: ID {app_free_sum.id}")
        print(f"        2. Objetivas 10Q: ID {app_free_obj.id}")
        print(f"        3. Formato PAS (Bloqueio): ID {app_free_pas.id}")

    else:
        # Modo Específico (mixed, sum ou choice)
        print(f"\n📝 Gerando aplicações para modo '{args.type}':")
        if args.type == 'sum':
            active_exams = [exam_sum_10, exam_sum_wide]
        elif args.type == 'choice':
            active_exams = [exam_choice, exam_disc]
        else:  # mixed
            active_exams = [exam_sum_10, exam_sum_wide, exam_choice, exam_disc, exam_pas]

        created_apps = []
        for exam in active_exams:
            app_students = real_students[student_idx:student_idx+students_per_app]
            student_idx += students_per_app

            app = create_application_with_students(exam, app_students, target_date, start_time, end_time, school_class)
            created_apps.append((app, exam.name))
            print(f"  ✓ {exam.name}")
            print(f"      ID: {app.id} | Alunos: {', '.join([s.name for s in app_students])}")

        if args.create_distribution:
            print("\n🏛️ Criando Ensalamento no Banco (--ensalar):")
            ensalavel_apps = [app for app, name in created_apps if not name.startswith('[QA] Caderno 5')]

            distrib = RoomDistribution.objects.create(
                category=RoomDistribution.NAME_GRADE,
                status=RoomDistribution.WAITING_EXPORT,
            )
            for app in ensalavel_apps:
                app.room_distribution = distrib
                app.save(update_fields=['room_distribution'])

            try:
                functions.distribute_students_grade(distrib, rooms_qs)
                print(f"  ✓ Ensalamento criado com sucesso!")
                print(f"      ID:         {distrib.pk}")
                print(f"      Status:     Sem malote gerado (WAITING_EXPORT)")
                print(f"      Aplicações: {len(ensalavel_apps)} vinculadas")
            except Exception as err:
                print(f"  ⚠️ Ensalamento criado, mas falhou ao distribuir alunos: {err}")

            if args.keep_free_apps:
                print("\n📝 Criando aplicações livres adicionais para a tela de cadastro:")
                st_free_sum = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
                st_free_obj = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app
                st_free_pas = real_students[student_idx:student_idx+students_per_app]; student_idx += students_per_app

                app_fs = create_application_with_students(exam_sum_10, st_free_sum, target_date, start_time, end_time, school_class)
                app_fo = create_application_with_students(exam_choice, st_free_obj, target_date, start_time, end_time, school_class)
                app_fp = create_application_with_students(exam_pas, st_free_pas, target_date, start_time, end_time, school_class)
                print(f"  ✓ Aplicações livres criadas para teste manual!")

    print("\n" + "=" * 80)
    print("🎯 PRÓXIMOS PASSOS DE QA:")
    print("=" * 80)
    print(f"1️⃣  Teste de Cadastro na UI: http://127.0.0.1:8000/ensalamento/criar/?date={target_date.strftime('%Y-%m-%d')}")
    print(f"2️⃣  Teste do Modal de Malote: http://127.0.0.1:8000/ensalamento/")
    print("=" * 80)


if __name__ == '__main__':
    main()

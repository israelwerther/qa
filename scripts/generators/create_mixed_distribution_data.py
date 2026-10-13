#!/usr/bin/env python
"""
Gerador de Dados para Testes de Ensalamento Misto e Malote (Lize Edu)
Local: .ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py
Slash command: /qa-criar-ensalamento-misto

Cria aplicações e cadernos de tipos variados sincronizados no mesmo dia e horário:
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
  --students-per-app     Quantidade de alunos por aplicação [default: 1]
  --ensalar              Cria o Ensalamento (RoomDistribution) completo e distribui os alunos
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Configura ambiente Django
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
        # Tenta UUID
        client = Client.objects.filter(pk=client_arg).first()
        if client:
            return client
        # Tenta por nome aproximado
        client = Client.objects.filter(name__icontains=client_arg).first()
        if client:
            return client

    # Tenta sessão ativa
    client, _ = get_active_session_client_and_user()
    if client:
        return client

    # Fallback: cliente com ensalamento
    client = Client.objects.filter(has_distribution=True).first()
    if not client:
        client = Client.objects.first()
    return client


def main():
    parser = argparse.ArgumentParser(
        description='Cria cadernos e aplicações sincronizadas para testes de ensalamento misto (Task #86ak8wuvc).'
    )
    parser.add_argument('--date', '-d', type=str, default=None,
                        help='Data da aplicação (AAAA-MM-DD, "hoje", "amanha", "+1"). Default: data atual.')
    parser.add_argument('--client', '-c', type=str, default=None,
                        help='Nome ou UUID do cliente. Default: detecta da sessão ativa.')
    parser.add_argument('--client-id', type=str, default=None,
                        help='Alias legado para UUID do cliente.')
    parser.add_argument('--start', '-s', type=str, default='14:00',
                        help='Horário de início (HH:MM). Default: 14:00.')
    parser.add_argument('--end', '-e', type=str, default='18:00',
                        help='Horário de término (HH:MM). Default: 18:00.')
    parser.add_argument('--coordination', type=str, default=None,
                        help='Nome ou UUID da coordenação escolar.')
    parser.add_argument('--turma', '--class-name', dest='class_name', type=str, default=None,
                        help='Nome da turma para vinculação.')
    parser.add_argument('--students-per-app', type=int, default=3,
                        help='Número de alunos por aplicação. Default: 3.')
    parser.add_argument('--ensalar', '--create-distribution', dest='create_distribution', action='store_true',
                        help='Além de criar aplicações, cria o Ensalamento (RoomDistribution) pronto no banco.')

    args = parser.parse_args()

    # 1. Resolver Cliente
    client_param = args.client or args.client_id
    client = resolve_client(client_param)
    if not client:
        print("❌ Nenhum cliente encontrado. Verifique o banco ou especifique --client.")
        sys.exit(1)

    # Garante módulos ativos no cliente
    if not client.has_distribution or not client.has_sum_question:
        client.has_distribution = True
        client.has_sum_question = True
        client.save(update_fields=['has_distribution', 'has_sum_question'])

    print("=" * 75)
    print("🚀 SETUP DE DADOS PARA ENSALAMENTO MISTO E MALOTE (/qa-criar-ensalamento-misto)")
    print("=" * 75)
    print(f"🏢 Cliente:       {client.name} (UUID: {client.id})")

    # 2. Coordenação e Salas
    coordinations = SchoolCoordination.objects.filter(unity__client=client)
    if args.coordination:
        coordination = coordinations.filter(pk=args.coordination).first() or coordinations.filter(name__icontains=args.coordination).first()
    else:
        coordination = coordinations.first()

    if not coordination:
        unity = mixer.blend(Unity, client=client, name='Unidade QA')
        coordination = mixer.blend(SchoolCoordination, unity=unity, name='Coordenação QA')

    rooms = Room.objects.filter(coordination=coordination)
    if rooms.count() < 2:
        mixer.blend(Room, coordination=coordination, name='Sala QA 101', capacity=40)
        mixer.blend(Room, coordination=coordination, name='Sala QA 102', capacity=40)
        rooms = Room.objects.filter(coordination=coordination)

    print(f"📍 Coordenação:   {coordination.name} | Salas disponíveis: {rooms.count()}")

    # 3. Turma Ativa e Alunos Reais Cadastrados no Ano Corrente
    current_year = timezone.now().year
    students_per_app = max(1, args.students_per_app)
    total_needed_students = 5 * students_per_app

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
        # Prioriza turma que já possua quantidade suficiente de alunos reais ativos no ano atual
        school_class = None
        for sc in classes_qs:
            real_count = sc.students.filter(
                client=client,
                user__is_active=True,
            ).exclude(name__startswith='Aluno ').count()
            if real_count >= total_needed_students:
                school_class = sc
                break

        if not school_class:
            school_class = classes_qs.filter(students__user__is_active=True).distinct().first() or classes_qs.first()

    if not school_class:
        school_class = SchoolClass.objects.filter(coordination=coordination).first()

    if school_class and school_class.school_year != current_year:
        print(f"🔄 Atualizando ano letivo da turma '{school_class.name}' para {current_year}...")
        school_class.school_year = current_year
        school_class.save(update_fields=['school_year'])

    # Busca alunos reais cadastrados, ativos e na turma/coordenação do ano corrente
    students_qs = Student.objects.filter(
        client=client,
        user__is_active=True,
        classes=school_class,
    ).exclude(name__startswith='Aluno ').distinct().order_by('name')

    if students_qs.count() < total_needed_students:
        students_qs = Student.objects.filter(
            client=client,
            user__is_active=True,
            classes__coordination=coordination,
            classes__school_year=current_year,
        ).exclude(name__startswith='Aluno ').distinct().order_by('name')

    if students_qs.count() < total_needed_students:
        students_qs = Student.objects.filter(
            client=client,
            user__is_active=True,
        ).exclude(name__startswith='Aluno ').distinct().order_by('name')

    real_students = list(students_qs)
    if len(real_students) < total_needed_students:
        print(f"❌ Não há alunos reais cadastrados suficientes ({len(real_students)} encontrados, {total_needed_students} necessários).")
        sys.exit(1)

    # Garante senha 123456 e status ativo para os alunos alocados
    selected_students = real_students[:total_needed_students]
    for st in selected_students:
        st.classes.add(school_class)
        if st.user:
            st.user.set_password('123456')
            st.user.is_active = True
            st.user.save(update_fields=['password', 'is_active'])

    print(f"👥 Turma:         {school_class.name} ({current_year}) | {len(selected_students)} alunos reais ativos ({students_per_app} por app)")

    # 4. Data e Horário
    target_date = parse_target_date(args.date)
    start_time = args.start
    end_time = args.end
    print(f"📅 Data da Prova: {target_date.strftime('%d/%m/%Y')} | Horário: {start_time} às {end_time}")

    # 5. Criação/Atualização dos 5 Cadernos de Teste
    print("\n📚 [1/3] Cadernos de Prova:")

    # Caderno 1: Somatório até 15 questões (10Q)
    exam_sum_10 = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 1 - Somatório 10Q').first()
    if not exam_sum_10:
        exam_sum_10 = mixer.blend(Exam, name='[QA] Caderno 1 - Somatório 10Q', exam_format=Exam.STANDARD)
        exam_sum_10.coordinations.add(coordination)
        for i in range(1, 11):
            q = mixer.blend(Question, client=client, category=Question.SUM_QUESTION, enunciation=f'Questão Somatório QA {i}')
            mixer.blend(QuestionOption, question=q, text='(01) Proposição 01', is_correct=True)
            mixer.blend(QuestionOption, question=q, text='(02) Proposição 02', is_correct=False)
            mixer.blend(ExamQuestion, exam=exam_sum_10, question=q, order=i)
    print(f"  ✓ {exam_sum_10.name} (has_sum={exam_sum_10.has_sum_questions}, is_sum_only={exam_sum_10.is_sum_only})")

    # Caderno 2: Somatório amplo (>15 questões) + objetivas
    exam_sum_wide = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 2 - Somatório Amplo 18Q + 5 Obj').first()
    if not exam_sum_wide:
        exam_sum_wide = mixer.blend(Exam, name='[QA] Caderno 2 - Somatório Amplo 18Q + 5 Obj', exam_format=Exam.STANDARD)
        exam_sum_wide.coordinations.add(coordination)
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
    print(f"  ✓ {exam_sum_wide.name} (has_sum={exam_sum_wide.has_sum_questions}, is_sum_only={exam_sum_wide.is_sum_only})")

    # Caderno 3: Só Objetivas
    exam_choice = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 3 - Objetivas 10Q').first()
    if not exam_choice:
        exam_choice = mixer.blend(Exam, name='[QA] Caderno 3 - Objetivas 10Q', exam_format=Exam.STANDARD)
        exam_choice.coordinations.add(coordination)
        for i in range(1, 11):
            q = mixer.blend(Question, client=client, category=Question.CHOICE, enunciation=f'Questão Objetiva QA {i}')
            mixer.blend(QuestionOption, question=q, text='Opção A', is_correct=True)
            mixer.blend(QuestionOption, question=q, text='Opção B', is_correct=False)
            mixer.blend(ExamQuestion, exam=exam_choice, question=q, order=i)
    print(f"  ✓ {exam_choice.name} (has_sum={exam_choice.has_sum_questions})")

    # Caderno 4: Redação / Discursiva
    exam_disc = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 4 - Redação e Discursiva').first()
    if not exam_disc:
        exam_disc = mixer.blend(Exam, name='[QA] Caderno 4 - Redação e Discursiva', exam_format=Exam.STANDARD)
        exam_disc.coordinations.add(coordination)
        q = mixer.blend(Question, client=client, category=Question.TEXTUAL, enunciation='Tema de Redação / Questão Discursiva QA')
        mixer.blend(ExamQuestion, exam=exam_disc, question=q, order=1)
    print(f"  ✓ {exam_disc.name} (has_sum={exam_disc.has_sum_questions})")

    # Caderno 5: Formato PAS (para teste negativo de bloqueio)
    exam_pas = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 5 - Formato PAS (Bloqueio)').first()
    if not exam_pas:
        exam_pas = mixer.blend(Exam, name='[QA] Caderno 5 - Formato PAS (Bloqueio)', exam_format=Exam.PAS)
        exam_pas.coordinations.add(coordination)
    print(f"  ✓ {exam_pas.name} (exam_format=PAS) [Caderno para teste de trava]")

    # 6. Criação das Aplicações Presenciais Sincronizadas
    print("\n📝 [2/3] Aplicações Presenciais Sincronizadas:")
    exam_groups = [
        (exam_sum_10, selected_students[0:students_per_app]),
        (exam_sum_wide, selected_students[students_per_app:2*students_per_app]),
        (exam_choice, selected_students[2*students_per_app:3*students_per_app]),
        (exam_disc, selected_students[3*students_per_app:4*students_per_app]),
        (exam_pas, selected_students[4*students_per_app:5*students_per_app]),
    ]

    created_apps = []
    for exam, app_students in exam_groups:
        app = Application.objects.filter(
            exam=exam,
            date=target_date,
            start=start_time,
            end=end_time,
            category=Application.PRESENTIAL,
        ).first()

        if not app:
            app = Application.objects.create(
                exam=exam,
                date=target_date,
                start=start_time,
                end=end_time,
                category=Application.PRESENTIAL,
            )

        # Garante que a aplicação esteja desvinculada de ensalamentos anteriores para poder ser selecionada na UI
        if app.room_distribution:
            app.room_distribution = None
            app.save(update_fields=['room_distribution'])

        # Garante turma vinculada
        app.school_classes.clear()
        app.school_classes.add(school_class)

        # Substitui a lista de alunos para garantir exatamente o grupo exclusivo sem sobreposição
        ApplicationStudent.objects.filter(application=app).delete()
        app.students.set(app_students)

        created_apps.append((app, exam.name))
        print(f"  ✓ [{len(created_apps)}] {exam.name}")
        st_names = [s.name for s in app_students]
        print(f"      ID: {app.id} | Alunos ({len(st_names)}): {', '.join(st_names)}")

    # 7. Opcional: Criar Ensalamento Diretamente (--ensalar)
    if args.create_distribution:
        print("\n🏛️ [3/3] Criando Ensalamento Completo no Banco (--ensalar):")
        # Ensalamos as 4 aplicações mistas (excluindo PAS que é bloqueado por regra de negócio)
        mixed_apps = [app for app, name in created_apps if not name.startswith('[QA] Caderno 5')]
        selected_rooms = list(rooms[:2])

        distribution = RoomDistribution.objects.create(
            category=RoomDistribution.NAME_GRADE,
            status=RoomDistribution.WAITING_EXPORT,
        )

        for app in mixed_apps:
            app.room_distribution = distribution
            app.save(update_fields=['room_distribution'])

        # Distribui alunos nas salas
        try:
            functions.distribute_students_grade(distribution, selected_rooms)
            print(f"  ✓ Ensalamento criado com sucesso!")
            print(f"      ID:               {distribution.pk}")
            print(f"      Status:           Sem malote gerado (WAITING_EXPORT)")
            print(f"      Aplicações:       4 cadernos mistos vinculados")
            print(f"      Salas alocadas:   {', '.join([r.name for r in selected_rooms])}")
            print(f"  👉 Acesse para testar o Malote: http://127.0.0.1:8000/ensalamento/")
        except Exception as err:
            print(f"  ⚠️ Ensalamento criado, mas falhou ao distribuir alunos: {err}")
    else:
        print("\n🌐 [3/3] Próximos Passos de QA na Interface:")
        create_url = f"http://127.0.0.1:8000/ensalamento/criar/?date={target_date.strftime('%Y-%m-%d')}"
        print(f"  👉 Abra no navegador: {create_url}")
        print("  1. No campo 'Data do Ensalamento', confirme a data selecionada.")
        print("  2. Na lista de 'Aplicações Envolvidas', marque Caderno 1 e Caderno 3 juntos.")
        print("  3. Valide a ausência do alerta de bloqueio e salve o ensalamento!")
        print("  4. Se quiser testar o bloqueio negativo, tente marcar o Caderno 5 (PAS).")

    print("=" * 75)
    print("✅ Concluído com sucesso!")


if __name__ == '__main__':
    main()

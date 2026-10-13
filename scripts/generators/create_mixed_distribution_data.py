#!/usr/bin/env python
"""
Gerador de Aplicações de Teste para Ensalamento Misto (Task ClickUp #86ak8wuvc)
Local: .ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py

Cria o conjunto completo de 5 cadernos e 5 aplicações presenciais sincronizadas:
- Mesmo dia (default: hoje)
- Mesmo horário (14:00 às 18:00)
- Mesma coordenação e turma
- Tipos de cadernos:
  1. Somatório até 15 questões (10Q Somatório)
  2. Somatório Amplo >15 questões (18Q Somatório + 5Q Objetivas)
  3. Só Objetivas (10Q Escolha)
  4. Discursiva / Redação (1Q Redação)
  5. PAS (para validação do bloqueio)
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
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.students.models import Student
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.distribution.models import Room

# Reusa detecção de sessão ativa
try:
    from create_exam import get_current_session_user_and_client
except ImportError:
    def get_current_session_user_and_client():
        return None, None


def main():
    parser = argparse.ArgumentParser(description='Cria dados sincronizados para teste de ensalamento misto.')
    parser.add_argument('--date', type=str, default=None, help='Data da aplicação no formato AAAA-MM-DD (default: data atual)')
    parser.add_argument('--client-id', type=str, default=None, help='UUID do cliente')
    args = parser.parse_args()

    # 1. Identificar Usuário e Cliente
    user, client = get_current_session_user_and_client()
    if args.client_id:
        client = Client.objects.filter(pk=args.client_id).first()

    if not client:
        client = Client.objects.filter(has_distribution=True).first()
        user = User.objects.filter(is_superuser=True).first()

    if not client:
        print("❌ Nenhum cliente com módulo de ensalamento encontrado.")
        sys.exit(1)

    # Garante flags necessárias no cliente
    if not client.has_distribution or not client.has_sum_question:
        client.has_distribution = True
        client.has_sum_question = True
        client.save()

    print(f"🏢 Cliente: {client.name} ({client.id})")

    # 2. Coordenação e Salas
    coordination = SchoolCoordination.objects.filter(unity__client=client).first()
    if not coordination:
        unity = mixer.blend(Unity, client=client, name='Unidade QA')
        coordination = mixer.blend(SchoolCoordination, unity=unity, name='Coordenação QA')

    rooms = Room.objects.filter(coordination=coordination)
    if rooms.count() < 2:
        mixer.blend(Room, coordination=coordination, name='Sala QA 101', capacity=40)
        mixer.blend(Room, coordination=coordination, name='Sala QA 102', capacity=40)
        rooms = Room.objects.filter(coordination=coordination)

    print(f"📍 Coordenação: {coordination.name} | Salas disponíveis: {rooms.count()}")

    # 3. Turma e Alunos
    school_class = SchoolClass.objects.filter(coordination=coordination).first()
    if not school_class:
        school_class = mixer.blend(SchoolClass, coordination=coordination, name='Turma QA Ensalamento')

    students = Student.objects.filter(client=client, classes=school_class)
    if students.count() < 4:
        for idx in range(1, 5):
            st = mixer.blend(Student, client=client, name=f'Aluno QA Ensalamento {idx}')
            st.classes.add(school_class)
        students = Student.objects.filter(client=client, classes=school_class)

    selected_students = list(students[:4])
    print(f"👥 Turma: {school_class.name} | Alunos envolvidos: {len(selected_students)}")

    # 4. Data e Horário
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = timezone.localdate()

    start_time = '14:00'
    end_time = '18:00'
    print(f"📅 Data do Ensalamento: {target_date.strftime('%Y-%m-%d')} | Horário: {start_time} às {end_time}")

    # 5. Criação dos Cadernos de Teste
    print("\n📚 Criando/Atualizando Cadernos de Prova...")

    # Caderno 1: Somatório até 15 questões
    exam_sum_10 = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 1 - Somatório 10Q').first()
    if not exam_sum_10:
        exam_sum_10 = mixer.blend(Exam, name='[QA] Caderno 1 - Somatório 10Q', exam_format=Exam.STANDARD)
        exam_sum_10.coordinations.add(coordination)
        for i in range(1, 11):
            q = mixer.blend(Question, client=client, category=Question.SUM_QUESTION, enunciation=f'Questão Somatório QA {i}')
            mixer.blend(QuestionOption, question=q, text='(01) Proposição 01', is_correct=True)
            mixer.blend(QuestionOption, question=q, text='(02) Proposição 02', is_correct=False)
            mixer.blend(ExamQuestion, exam=exam_sum_10, question=q, order=i)
    print(f"  ✓ {exam_sum_10.name} (has_sum: {exam_sum_10.has_sum_questions}, is_sum_only: {exam_sum_10.is_sum_only})")

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
    print(f"  ✓ {exam_sum_wide.name} (has_sum: {exam_sum_wide.has_sum_questions}, is_sum_only: {exam_sum_wide.is_sum_only})")

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
    print(f"  ✓ {exam_choice.name} (has_sum: {exam_choice.has_sum_questions})")

    # Caderno 4: Redação / Discursiva
    exam_disc = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 4 - Redação e Discursiva').first()
    if not exam_disc:
        exam_disc = mixer.blend(Exam, name='[QA] Caderno 4 - Redação e Discursiva', exam_format=Exam.STANDARD)
        exam_disc.coordinations.add(coordination)
        q = mixer.blend(Question, client=client, category=Question.TEXTUAL, enunciation='Tema de Redação / Questão Discursiva QA')
        mixer.blend(ExamQuestion, exam=exam_disc, question=q, order=1)
    print(f"  ✓ {exam_disc.name} (has_sum: {exam_disc.has_sum_questions})")

    # Caderno 5: Formato PAS (para teste negativo de bloqueio)
    exam_pas = Exam.objects.filter(coordinations=coordination, name='[QA] Caderno 5 - Formato PAS (Bloqueio)').first()
    if not exam_pas:
        exam_pas = mixer.blend(Exam, name='[QA] Caderno 5 - Formato PAS (Bloqueio)', exam_format=Exam.PAS)
        exam_pas.coordinations.add(coordination)
    print(f"  ✓ {exam_pas.name} (exam_format: PAS)")

    # 6. Criação das Aplicações Presenciais
    print("\n📝 Criando/Atualizando Aplicações Presenciais Sincronizadas...")
    exams = [
        (exam_sum_10, selected_students[0]),
        (exam_sum_wide, selected_students[1]),
        (exam_choice, selected_students[2]),
        (exam_disc, selected_students[3]),
        (exam_pas, selected_students[0]),
    ]

    created_apps = []
    for exam, student in exams:
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
            app.school_classes.add(school_class)

        app.students.add(student)
        app_student, _ = ApplicationStudent.objects.get_or_create(
            application=app,
            student=student,
        )
        created_apps.append((app, exam.name))
        print(f"  ✓ Aplicação: {exam.name} | ID: {app.id}")

    print("\n" + "=" * 70)
    print("🎉 DADOS PRONTOS PARA O TESTE DE ENSALAMENTO MISTO!")
    print(f"👉 Data a selecionar no formulário: {target_date.strftime('%Y-%m-%d')}")
    print(f"👉 Horário sincronizado: {start_time} às {end_time}")
    print("=" * 70)
    print("Aplicações prontas para você selecionar na tela:")
    for idx, (app, name) in enumerate(created_apps, start=1):
        print(f"  [{idx}] {name}")
    print("=" * 70)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""
Helper script para QA:
Reseta a questão 25 da aluna Isadora Tomé para o estado pendente (sem nota e sem feedback),
preservando a imagem da folha discursiva e as sugestões da IA intactas.
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir != '/' and not os.path.exists(os.path.join(current_dir, 'manage.py')):
    current_dir = os.path.dirname(current_dir)
BASE_DIR = current_dir
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiscallizeon.settings')
import django
django.setup()

from fiscallizeon.answers.models import FileAnswer
from fiscallizeon.applications.models import ApplicationStudent

fa = FileAnswer.objects.get(pk='1a45b717-7a10-411e-bc5a-5bc00ac43a5e')
fa.teacher_grade = None
fa.grade = None
fa.teacher_feedback = None
fa.ai_suggestion_accepted = False
fa.who_corrected = None
fa.save(update_fields=['teacher_grade', 'grade', 'teacher_feedback', 'ai_suggestion_accepted', 'who_corrected', 'updated_at'])

app_student = ApplicationStudent.objects.get(pk='d5ba1aef-40b7-44c9-99b5-23cabaecf8b3')
if hasattr(app_student, 'calculate_grades'):
    app_student.calculate_grades()

print("✅ Questão 25 da Isadora resetada com sucesso para estado pendente!")
print("   - Imagem do cartão: preservada")
print("   - Sugestões da IA: preservadas")
print("   - Nota do professor: None (vazio)")
print("   - Feedback do professor: None (vazio)")

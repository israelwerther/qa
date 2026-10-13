# Mapeamento de Tela — `distribution_create_update.html`

> Template: `fiscallizeon/distribution/templates/distribution/distribution_create_update.html`

---

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Cadastrar Ensalamento | `/ensalamento/criar/` | `distribution:distribution_create` (`RoomDistributionCreateView`) |
| Editar Ensalamento | `/ensalamento/<uuid:pk>/atualizar/` | `distribution:distribution_update` (`RoomDistributionUpdateView`) |
| API: Listar Aplicações por Data | `GET /aplicacoes/api/list/?date=YYYY-MM-DD` | `applications:api_applications_list` |
| API: Listar Salas por Coordenação e Horário | `GET /ensalamento/api/list/?coordinations=<ids>&date=<date>&start=<start>&end=<end>` | `distribution:rooms_list` |
| API: Alunos por Coordenação das Aplicações | `GET /aplicacoes/api/alunos-coordenacao/?id__in=<ids>` | `applications:api_applications_students_coordination` |

### Navegação para a tela

- **Via menu lateral (Coordenação):** Aplicações ➔ **Ensalamento** (`/ensalamento/`) ➔ botão superior direito **"Cadastrar ensalamento"** (ou ação **"Editar"** na linha de um ensalamento existente).

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from datetime import datetime, timedelta
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.clients.models import (
    Client,
    CoordinationMember,
    Grade,
    SchoolCoordination,
    Unity,
)
from fiscallizeon.distribution.models import Room
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Alternative, Question
from fiscallizeon.students.models import Student

# 1. Usuário Coordenador com permissão de ensalamento
coordinator_user = mixer.blend(User, username='coord_ensalamento_form', is_superuser=True)
client = mixer.blend(
    Client,
    name='Colégio Modelo Ensalamento',
    has_distribution=True,
    has_exam_elaboration=True,
    client_has_sum_questions=True,
    require_2fa=False,
)
unity = mixer.blend(Unity, client=client, name='Unidade Central')
coordination = mixer.blend(SchoolCoordination, unity=unity, name='Coordenação Ensino Médio')
mixer.blend(CoordinationMember, user=coordinator_user, coordination=coordination)

# 2. Séries e Turmas
grade = mixer.blend(Grade, client=client, name='3ª Série EM')
school_class = mixer.blend(SchoolClass, coordination=coordination, grade=grade, name='3º Ano Alpha')

# 3. Alunos
student_sum = mixer.blend(Student, client=client, school_class=school_class, name='Aluno Prova Somatório')
student_choice = mixer.blend(Student, client=client, school_class=school_class, name='Aluno Prova Objetiva')
student_pas = mixer.blend(Student, client=client, school_class=school_class, name='Aluno Prova PAS')

# 4. Caderno Somatório (has_sum_questions = True)
exam_sum = mixer.blend(Exam, client=client, name='Simulado Somatório 2026', exam_format=Exam.STANDARD)
q_sum = mixer.blend(Question, client=client, category=Question.SUM, enunciation='Questão Somatório')
mixer.blend(ExamQuestion, exam=exam_sum, question=q_sum, order=1)
exam_sum.coordinations.add(coordination)

# 5. Caderno Só Objetivas (has_sum_questions = False)
exam_choice = mixer.blend(Exam, client=client, name='Simulado Objetivas 2026', exam_format=Exam.STANDARD)
q_choice = mixer.blend(Question, client=client, category=Question.CHOICE, enunciation='Questão Objetiva')
mixer.blend(Alternative, question=q_choice, text='A', is_correct=True)
mixer.blend(Alternative, question=q_choice, text='B', is_correct=False)
mixer.blend(ExamQuestion, exam=exam_choice, question=q_choice, order=1)
exam_choice.coordinations.add(coordination)

# 6. Caderno PAS (exam_format = Exam.PAS)
exam_pas = mixer.blend(Exam, client=client, name='Simulado PAS 2026', exam_format=Exam.PAS)
exam_pas.coordinations.add(coordination)

# 7. Salas de prova
room_1 = mixer.blend(Room, coordination=coordination, name='Sala 01 - Bloco A', capacity=30)
room_2 = mixer.blend(Room, coordination=coordination, name='Sala 02 - Bloco A', capacity=30)

# 8. Aplicações presenciais no mesmo dia e horário
test_date = datetime.now().date() + timedelta(days=2)
app_sum = mixer.blend(
    Application,
    exam=exam_sum,
    date=test_date,
    start='08:00',
    end='12:00',
    category=Application.PRESENTIAL,
)
app_choice = mixer.blend(
    Application,
    exam=exam_choice,
    date=test_date,
    start='08:00',
    end='12:00',
    category=Application.PRESENTIAL,
)
app_pas = mixer.blend(
    Application,
    exam=exam_pas,
    date=test_date,
    start='08:00',
    end='12:00',
    category=Application.PRESENTIAL,
)

mixer.blend(ApplicationStudent, application=app_sum, student=student_sum)
mixer.blend(ApplicationStudent, application=app_choice, student=student_choice)
mixer.blend(ApplicationStudent, application=app_pas, student=student_pas)
```

---

## 3. Seletores DOM e Ações

### Formulário Principal (`form[method="POST"]`)

#### Dados Básicos do Ensalamento:
- **Campo Data:** `input#id_date` (`type="date"`, aciona busca automática de aplicações via Vue).
- **Tipo de Ensalamento:** `select#id_category` (`name="category"`)
  - `0`: Por nome e série
  - `1`: Por nome e turma
  - `2`: Por série e turma
- **Switch Aleatorizar alunos:** `input#id_shuffle_students` (checkbox switch)
- **Switch Balancear salas (apenas tipo 2):** `input#id_balance_rooms` (checkbox switch)
- **Switch Alocar salas anteriores:** `input#id_assign_previous_rooms` (checkbox switch)

#### Bloco: Aplicações Envolvidas
- **Filtro de Turmas:** `select#id_school_classes` (múltipla escolha)
- **Filtro de Séries:** `select#id_grades` (múltipla escolha)
- **Botão Filtrar Aplicações:** `button:has(i.fa-search)` (no bloco de filtro de aplicações)
- **Lista de Aplicações (`.d-flex.flex-wrap`):**
  - **Checkbox Aplicação Somatório:** `input[type="checkbox"]#application-<id>` (`:id="'application-'+application.id"`)
  - **Checkbox Aplicação Objetivas:** `input[type="checkbox"]#application-<id>`
  - **Checkbox Aplicação PAS:** `input[type="checkbox"]#application-<id>`
  - **Label com nome do caderno:** `label[for="application-<id>"]`
  - *Comportamento Misto (Sucesso):* Marcar aplicação Somatório + aplicação Objetivas é permitido sem disparar SweetAlert.
  - *Comportamento PAS (Bloqueio):* Tentar marcar aplicação PAS + aplicação comum dispara SweetAlert de erro: *"Não é permitido ensalar cadernos do tipo PAS com outros modelos."*

#### Bloco: Salas Envolvidas
- **Filtro de Unidades:** `select#id_unitys`
- **Filtro de Coordenações:** `select#id_school_coordination`
- **Botão Filtrar Salas:** `button:has(i.fa-search)` (no bloco de filtro de salas)
- **Lista de Salas:**
  - **Checkbox da Sala:** `input[type="checkbox"]#room-<id>` (`:id="'room-'+room.id"`)
  - **Capacidade e Vagas:** `.tx-11.text-success` (`Disponíveis: X vagas`)

#### Painel Lateral de Resumo e Submissão
- **Card de Resumo:** `.card-body` sticky lateral
  - Total de Alunos Alocados: `h5:has-text("Total de Alunos")`
  - Vagas Disponíveis nas Salas: `h5:has-text("Vagas Selecionadas")`
- **Botão Submeter / Salvar Ensalamento:**
  - Habilitado (vagas suficientes): `button[type="submit"].btn-primary:has-text("Salvar Ensalamento")`
  - Desabilitado (vagas insuficientes): `button[type="button"].btn-danger[disabled]:has-text("Salvar Ensalamento")`

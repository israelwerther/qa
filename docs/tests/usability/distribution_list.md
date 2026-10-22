# Mapeamento de Tela — `distribution_list.html`

> Template: `fiscallizeon/distribution/templates/distribution/distribution_list.html`

---

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Listar Ensalamentos | `/ensalamento/` | `distribution:distribution_list` (`RoomDistributionList`) |
| Cadastrar Ensalamento | `/ensalamento/criar/` | `distribution:distribution_create` (`RoomDistributionCreateView`) |
| Editar Ensalamento | `/ensalamento/<uuid:pk>/atualizar/` | `distribution:distribution_update` (`RoomDistributionUpdateView`) |
| Visualizar Alunos do Ensalamento | `/ensalamento/<uuid:pk>/distribuicao/detalhe/` | `distribution:distribution_detail` (`RoomDistributionDetailtView`) |
| Deletar Ensalamento | `/ensalamento/<uuid:pk>/deletar/` | `distribution:distribution_delete` (`RoomDistributionDeleteView`) |
| API: Gerar Malote de Ensalamento | `POST /ensalamento/api/exportar/malote/<uuid:distribution_id>/` | `distribution:export_exams_bag` (`ExportDistributionExamsBagAPIView`) |
| Lista de pátio (por sala) | `/ensalamento/<uuid:pk>/lista/patio/` | `distribution:distribution_patio_list` → `patio_list.html` |
| Lista de pátio (por turma) | `/ensalamento/<uuid:pk>/lista/patio/?by_class=true` | idem → `patio_list_by_class.html` (ver `patio_list_by_class.md`) |

### Navegação para a tela

- **Via menu lateral (Coordenação):** Aplicações ➔ **Ensalamento** (`/ensalamento/`).
- **Permissão de Acesso:** Usuário pertencente a `SchoolCoordination` com `client.has_distribution = True`.

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
    SchoolCoordination,
    Unity,
)
from fiscallizeon.distribution.models import Room, RoomDistribution, RoomDistributionStudent
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Alternative, Question
from fiscallizeon.students.models import Student

# 1. Usuário Coordenador com permissões
coordinator_user = mixer.blend(User, username='coord_ensalamento', is_superuser=True)
client = mixer.blend(
    Client,
    name='Colégio Teste Ensalamento',
    has_distribution=True,
    has_exam_elaboration=True,
    client_has_sum_questions=True,
    require_2fa=False,
)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)
mixer.blend(CoordinationMember, user=coordinator_user, coordination=coordination)

# 2. Sala de prova
room = mixer.blend(Room, coordination=coordination, name='Sala 101', capacity=50)

# 3. Turma e Alunos
school_class = mixer.blend(SchoolClass, coordination=coordination, name='3º Ano A')
student_1 = mixer.blend(Student, client=client, school_class=school_class, name='Aluno Somatório')
student_2 = mixer.blend(Student, client=client, school_class=school_class, name='Aluno Objetiva')

# 4. Caderno 1: Somatório (has_sum_questions = True)
exam_sum = mixer.blend(Exam, client=client, name='Prova Somatório', exam_format=Exam.STANDARD)
q_sum = mixer.blend(Question, client=client, category=Question.SUM, enunciation='Questão Somatório')
mixer.blend(ExamQuestion, exam=exam_sum, question=q_sum, order=1)

# 5. Caderno 2: Só Objetivas (has_sum_questions = False)
exam_choice = mixer.blend(Exam, client=client, name='Prova Objetivas', exam_format=Exam.STANDARD)
q_choice = mixer.blend(Question, client=client, category=Question.CHOICE, enunciation='Questão Múltipla Escolha')
mixer.blend(Alternative, question=q_choice, text='Opção A', is_correct=True)
mixer.blend(Alternative, question=q_choice, text='Opção B', is_correct=False)
mixer.blend(ExamQuestion, exam=exam_choice, question=q_choice, order=1)

# 6. Aplicações no mesmo dia e horário
date_app = datetime.now().date() + timedelta(days=1)
app_sum = mixer.blend(
    Application,
    exam=exam_sum,
    date=date_app,
    start='08:00',
    end='12:00',
    category=Application.PRESENTIAL,
)
app_choice = mixer.blend(
    Application,
    exam=exam_choice,
    date=date_app,
    start='08:00',
    end='12:00',
    category=Application.PRESENTIAL,
)

app_student_1 = mixer.blend(ApplicationStudent, application=app_sum, student=student_1)
app_student_2 = mixer.blend(ApplicationStudent, application=app_choice, student=student_2)

# 7. Ensalamento Misto
distribution = mixer.blend(
    RoomDistribution,
    category=RoomDistribution.NAME_GRADE,
    is_printed=False,
)
distribution.applications.add(app_sum, app_choice)
distribution.rooms.add(room)
mixer.blend(RoomDistributionStudent, distribution=distribution, room=room, application_student=app_student_1)
mixer.blend(RoomDistributionStudent, distribution=distribution, room=room, application_student=app_student_2)
```

---

## 3. Seletores DOM e Ações

### Tabela de Ensalamentos
- **Linha da tabela do ensalamento:** `table tbody tr`
- **Coluna de Ações / Dropdown Opções:** `button:has-text("Opções")` (abre o dropdown do Bootstrap).
- **Link Imprimir Malote (Dropdown):** `a:has-text("Imprimir malote")` ou `a:has-text("Imprimir malote novamente")`
  - *Ação:* Abre o modal `#configurePrintModal`.
- **Badge / Link Baixar Malote (quando gerado):** `a span:has-text("Baixar malote")`

### Modal de Configuração de Impressão (`#configurePrintModal`)
- **Container do Modal:** `#configurePrintModal`
- **Título do Modal:** `h5.modal-title:has-text("Configure a impressão do malote nesta exportação")`

#### Radios de Modelo de Cartão (Grupo `.btn-group-toggle`):
- **Folha de respostas Lize:** `label:has(input[value="fiscallize"])` (texto: `"Folha de respostas Lize"`)
- **Bolhas ampliadas:** `label:has(input[value="large_bubbles"])` (texto: `"Bolhas ampliadas"`)
- **Folha de respostas ENEM:** `label:has(input[value="enem"])` (texto: `"Folha de respostas ENEM"`)
- **Modelo Somatório (apenas ensalamento 100% somatório):** `label:has(input[value="sum"])` (texto: `"Modelo somatório"`)
- **Modelo PAS (apenas ensalamento 100% PAS):** `label:has(input[value="pas"])` (texto: `"Modelo PAS"`)
- **Modelos Condicionais (Híbrido / Reduzido / EFAI):**
  - Ocultos obrigatoriamente quando `distributionHasMixedSum == true` (ensalamento misto).

#### Alerta Informativo de Ensalamento Misto:
- **Seletor:** `#configurePrintModal .alert.alert-info`
- **Texto Esperado:** `"Cadernos com somatório saem no cartão de somatório automaticamente (até 15 questões: uma folha; mais de 15: somatório expandido). A escolha acima vale só para cadernos de objetivas."`

#### Opções Adicionais do Modal:
- **Foto oficial:** `#show-official-picture` (visível para `fiscallize` ou `large_bubbles`)
- **Impressão frente e verso:** `#blank-pages`
- **Não imprimir lista de presença:** `#skip-attendance-list`
- **Incluir folhas de respostas discursivas:** `#print-discursives`
- **Incluir cadernos de prova:** `#print-exam`

#### Botão de Ação / Disparo:
- **Botão Imprimir Malote:** `#configurePrintModal button:has-text("Imprimir malote")`
  - *Ação:* Envia requisição `POST` com `{ sheet_model: answer_sheet_model, ... }` e fecha o modal.

### Dropdown — seção IMPRESSÃO (lista de pátio)

- **Abrir modal de pátio:** `button:has-text("Imprimir lista de pátio")` → `@click="showPrintPatioListModal(distribution.id)"` → `$('#patioPrintConfig').modal('show')`
- Visível apenas quando `distribution.rooms.length > 0`.

### Modal de Layout da Lista de Pátio (`#patioPrintConfig`)

- **Container:** `#patioPrintConfig`
- **Título:** `h5.modal-title:has-text("Layout da listagem de alunos")`
- **Pergunta de colunas:** `h6:has-text("Quantas colunas as tabelas de alunos devem utilizar?")`
- **Uma coluna:** `label.btn:has(input[value="one"])` / texto `"Uma coluna"` (`v-model="twoColumnsPatioList"`, default `'one'`)
- **Duas colunas:** `label.btn:has(input[value="two"])` / texto `"Duas colunas"`
- **Switch Separar por turma:** `#patio-by-class` (`v-model="patioListByClass"`, default `false`)
  - Label: `label[for="patio-by-class"]:has-text("Separar lista por turma")`
  - Ajuda: *"Ative esta opção para gerar a listagem com uma turma por página e a sala ao lado de cada aluno."*
- **Gerar:** `#patioPrintConfig button:has-text("Gerar listagem de pátio")` → `printPatiolist()`
  - Monta URL base `distributionPatioList` + query:
    - switch on → `by_class=true`
    - colunas `'two'` → `two_columns=true`
    - params combináveis com `&`
  - Abre em nova aba: `window.open(url, '_blank')`

# Mapeamento de Tela — `application_list_new.html`

> Template: `fiscallizeon/applications/templates/dashboard/applications/application_list_new.html`

---

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Listar todas as aplicações | `/aplicacoes/` | `applications:applications_list` |
| Listar aplicações online | `/aplicacoes/?category=online` | `applications:applications_list` |
| Listar aplicações presenciais | `/aplicacoes/?category=presential` | `applications:applications_list` |
| Listar aplicações híbridas | `/aplicacoes/?category=hibrid` | `applications:applications_list` |
| Botão Agendar Aplicação | `/aplicacoes/cadastrar/?category=<category>` | `applications:applications_create` |
| Botão Agendar Várias | `/aplicacoes/cadastrar-multiplas/?category=<category>` | `applications:applications_create_multiple` |
| API: Imprimir Malote | `POST /aplicacoes/api/aplicacao/<uuid:id>/imprimir-malote/` | `applications:applications_export_exams_bag` |
| API: Status do Malote | `GET /aplicacoes/api/aplicacao/<uuid:id>/status-malote/` | `applications:applications_export_exams_bag_status` |

### Navegação para a tela

- **Via menu lateral (Coordenação):** Aplicações → Híbridas (leva direto para `/aplicacoes/?category=hibrid`).
- **Via menu lateral (Coordenação):** Aplicações → Atividade Online ou Presencial.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from django.contrib.auth.models import Permission
from django.utils import timezone
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
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Alternative, Question
from fiscallizeon.students.models import Student

# Persona Coordenador
coordinator_user = mixer.blend(User, username='coord_hybrid', is_superuser=True)
client = mixer.blend(
    Client,
    name='Escola Teste',
    has_exam_elaboration=True,
    has_distribution=True,
    require_2fa=False,
)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)
mixer.blend(CoordinationMember, user=coordinator_user, coordination=coordination)

# Caderno e questões
exam = mixer.blend(
    Exam,
    client=client,
    name='Simulado Híbrido Teste',
    random_questions=True,
    random_alternatives=True,
    is_abstract=False,
)
exam.coordinations.add(coordination)

question = mixer.blend(
    Question,
    client=client,
    category=Question.CHOICE,
    enunciation='Qual a capital do Brasil?',
)
mixer.blend(Alternative, question=question, text='Brasília', is_correct=True)
mixer.blend(Alternative, question=question, text='Rio de Janeiro', is_correct=False)
mixer.blend(ExamQuestion, exam=exam, question=question, order=1)

# Aplicação Híbrida
school_class = mixer.blend(
    SchoolClass, coordination=coordination, school_year=timezone.now().year
)
student = mixer.blend(
    Student,
    client=client,
    user=mixer.blend(User, username='student_hybrid', is_active=True),
)
school_class.students.add(student)

application = mixer.blend(
    Application,
    exam=exam,
    category=Application.HYBRID,  # 5
    date=timezone.localdate() + timezone.timedelta(days=1),
    start='08:00',
    end='12:00',
    school_class=school_class,
)
mixer.blend(ApplicationStudent, application=application, student=student)
```

**Permissões mínimas exigidas:** Coordenador com permissões `applications.view_application`, `applications.add_application`, `applications.can_print_exams_bag` (ou `is_superuser=True`).

---

## 3. Seletores DOM e Ações

### Barra Superior e Filtros

| Elemento | Seletor / binding | Observação |
|----------|-------------------|------------|
| Botão "Agendar aplicação" | `#createSimpleApplication` | URL contém `?category={{category}}` |
| Botão "Agendar várias aplicações" | `#createMultipleApplication` | Criação em lote |
| Busca por nome/código | `input[name="search"]` | Filtro textual de aplicações |
| Tabela de aplicações | `table` ou container de cards de aplicação | Listagem principal |

### Ações na Linha da Aplicação (Dropdown de Opções)

| Elemento | Seletor / binding | Observação |
|----------|-------------------|------------|
| Gatilho do menu de ações | `button[id^="menu-button-"]` ou ícone de 3 pontos | Abre dropdown de ações da aplicação |
| Cabeçalho "IMPRESSÃO" | `p:has-text("Impressão")` | Renderizado se `application.category === 3 \|\| application.category === 5` |
| Ação "Todos os alunos" (imprimir malote) | `a[@click="showPrintModal(application)"]` | Abre o modal `#configurePrintModal` |
| Ação "Detalhes" | `a[href*="/detalhes/"]` | Relatório e métricas da aplicação |
| Ação "Editar" | `a[href*="/editar/"]` | Abre tela de edição da aplicação |

### Modal de Impressão de Malote (`#configurePrintModal`)

| Elemento | Seletor / binding | Visibilidade em Híbrida (`category == 5`) |
|----------|-------------------|------------------------------------------|
| Modal container | `#configurePrintModal` | Aberto via `$('#configurePrintModal').modal('show')` |
| Modelo da folha de resposta | `.form-group:has(h6:has-text("Modelo da folhas"))` | **Oculto** (`v-if="!isHybridApplication"`) |
| Checkbox "Foto oficial" | `#show-official-picture` | **Oculto** (`v-if="!isHybridApplication"`) |
| Checkbox "Incluir folhas discursivas" | `#print-discursives` | **Oculto** (`v-if="!isHybridApplication"`) |
| Checkbox "Incluir cadernos de prova" | `#print-exam` | **Oculto** (`v-if="!isHybridApplication"` — Caderno é obrigatório) |
| Checkbox "Incluir versões de randomização" | `#randomization-versions` | **Visível** se caderno randomizado (`v-if="showRandomizationVersionsOption && (includeExams \|\| isHybridApplication)"`) |
| Opções de diagramação | Container `show_diagramming_options.html` | **Visível** (`v-if="includeExams \|\| isHybridApplication"`) |
| Checkbox "Páginas em branco" | `#blank-pages` | **Visível** |
| Botão "Imprimir malote" | `button.btn-primary:has-text("Imprimir malote")` | Dispara `generateExamsBag(selectedApplication, 'one_bag')` |

---

## 4. API Interception & Fixtures

- `POST /aplicacoes/api/aplicacao/<uuid:id>/imprimir-malote/`
  - Payload enviado:
    ```json
    {
      "sheet_model": "fiscallize",
      "discursive_params": {},
      "exam_params": {},
      "include_exams": true,
      "include_discursives": false,
      "blank_pages": false,
      "show_official_picture": false,
      "include_randomization_versions": false
    }
    ```
  - Regra de bloqueio no Backend (`ExportApplicationExamsBagAPIView`): Se `application.category == Application.HYBRID` e `timezone.localtime(timezone.now()) >= application.date_time_start_tz`, retorna `HTTP 401 UNAUTHORIZED` com mensagem `"O caderno não pode ser impresso porque a aplicação já iniciou."`.
- Entidades envolvidas: `Application`, `Exam`, `ApplicationStudent`, `ApplicationRandomizationVersion`, `RandomizationVersion`.
- Tasks Celery envolvidas: `fiscallizeon.omr.tasks.export_answer_sheet` e `group_answer_sheet_files`.

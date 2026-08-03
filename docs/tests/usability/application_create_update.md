# Mapeamento de Tela — `application_create_update.html`

> Template: `fiscallizeon/applications/templates/dashboard/applications/application_create_update.html`

---

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Criar nova aplicação | `/aplicacoes/cadastrar/` | `applications:applications_create` |
| Editar aplicação existente | `/aplicacoes/<uuid:pk>/editar` | `applications:applications_update` |
| API: listar ausentes p/ 2ª chamada | `/aplicacoes/api/application-students/missed-at-exam/<uuid:exam_id>/` | `applications:api_application_students_missed_at_exam` |
| API: listar cadernos (modal 2ª chamada) | `/cadernos/api/listar/segunda-chamada/` | `exams:exams_api_second_call_list` |

### Navegação para a tela

- **Via menu lateral:** Aplicações → Criar (botão no header/sidebar).
- **Via header de coordenação:** `/aplicacoes/cadastrar/`.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from django.utils import timezone

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember
from fiscallizeon.exams.models import Exam
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.students.models import Student
from fiscallizeon.classes.models import SchoolClass, Grade
from django.core import management

management.call_command('initial_configs')

# Coordenador com todas as permissões
coordinator = mixer.blend(User, username='coord_test')
coordinator.user_permissions.set(Permission.objects.all())
coordinator.set_password('senha_test')
coordinator.save()

# Tenant
client = mixer.blend(Client, has_public_questions=True, has_exam_elaboration=True)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)
coord_member = mixer.blend(CoordinationMember, user=coordinator, coordination=coordination)

# Caderno da 1ª chamada
exam_1st = mixer.blend(Exam, is_abstract=False, not_applicable=False)
exam_1st.coordinations.add(coordination)

# Application da 1ª chamada (no ano atual, com resultado já liberado)
application_1st = mixer.blend(
    Application,
    exam=exam_1st,
    date=timezone.localdate(),
    student_stats_permission_date=timezone.localdate(),
)

# Aluno ausente na 1ª chamada
grade = Grade.objects.first()
school_class = mixer.blend(SchoolClass, coordination=coordination, school_year=timezone.now().year)
student_absent = mixer.blend(Student, client=client, user__is_active=True)
school_class.students.add(student_absent)

# ApplicationStudent ausente (is_present=False via annotate)
app_student_absent = mixer.blend(
    ApplicationStudent,
    application=application_1st,
    student=student_absent,
    missed=True,   # missed=True é suficiente para o campo; annotate_is_present cobre os demais casos
)
```

**Permissões mínimas exigidas:** `COORDINATION` (ou todas as permissões via `set(Permission.objects.all())`).

---

## 3. Seletores DOM e Ações

### Seção "Informações básicas" (redesign — L90–L256 do template)

| Elemento | Seletor / binding | Observação |
|----------|-------------------|------------|
| Seção Informações Básicas | `[data-tg-title="Informações Básicas"]` | Container da seção redesenhada |
| Campo oculto `is_second_call` | `input[name="is_second_call"]` | Binding `:value="isSecondCall ? 'True' : 'False'"` |

### Toggle "Prova de 2ª chamada" (dentro de "Alunos que realizarão a prova")

| Elemento | Seletor | Binding Vue |
|----------|---------|-------------|
| Checkbox toggle | `#is_second_call_toggle` | `v-model="isSecondCall"`, `@change="onSecondCallToggle"` |
| Label do toggle | `label[for="is_second_call_toggle"].switch` | — |
| Container expandido (visível quando toggle ativo) | `div[v-show="isSecondCall"]` | — |

### Card de prova anterior selecionada

| Elemento | Seletor / binding | Observação |
|----------|-------------------|------------|
| Card exibe caderno escolhido | `template[v-if="previousExamSelection"]` | Mostra nome, categoria e contagem de ausentes |
| Link "Abrir caderno" | `a[href*="/cadernos/"][target="_blank"]` dentro do card | Navega para edição do caderno original |
| Botão "Alterar prova anterior" | `button[@click="openSelectPreviousExamModal"]` (dentro de `template[v-if="previousExamSelection"]`) | Abre o modal novamente |
| Botão CTA inicial (sem seleção) | `button[@click="openSelectPreviousExamModal"]` (dentro de `template[v-else]`) | Texto: "Selecionar prova anterior (1ª chamada)" `[verificar]` |

### Modal `selectPreviousExamModal`

| Elemento | Seletor | Binding |
|----------|---------|---------|
| Modal container | `#selectPreviousExamModal` | Bootstrap `.modal.fade` fullscreen |
| Input de busca de cadernos | `input[v-model="secondCallModal.searchTerm"]` | `@input="onPreviousExamSearchInput"` |
| Lista de cadernos | `div[v-for="exam in secondCallModal.exams"]` | `@click="selectPreviousExam(exam)"` |
| Linha de caderno selecionado | classe `tw-bg-[#FFF4EC]` (aplicada via `:class`) | — |
| Lista de ausentes | `ul > li[v-for="item in secondCallModal.missedStudents"]` | — |
| Checkbox de ausente | `input[type="checkbox"][@change="togglePreviousExamStudent(item.student.id)"]` | `:value="item.student.id"` |
| Filtro por unidade | `button[v-for="unity in missedStudentUnities"]` | `@click="handleUnityAbsenteesClick(unity.id)"` |
| Filtro por turma | `button[v-for="schoolClass in missedStudentClasses"]` | `@click="handleClassAbsenteesClick(schoolClass.id)"` |
| Botão Cancelar | `button[@click="openModal('selectPreviousExamModal')"]` (footer) | Fecha o modal |
| Botão "Adicionar alunos não presentes" | `button[@click="confirmPreviousExamAbsentees"]` | `:disabled="!secondCallModal.selectedExam \|\| secondCallModal.loadingMissed"` |

### Estado Vue principal relevante para 2ª chamada

```javascript
// Estado (data) em application_create_update.html
isSecondCall: Boolean,              // controla toggle e campo hidden
secondCallModal: {
  searchTerm: String,
  exams: Array,
  selectedExam: Object | null,
  missedStudents: Array,
  selectedStudentsIds: Array,
  selectedUnitysIds: Array,
  selectedClassesIds: Array,
  loadingExams: Boolean,
  loadingMoreExams: Boolean,
  loadingMissed: Boolean,
  searchDebounce: Number,
},
previousExamSelection: Object | null, // caderno confirmado (nome, id, missedCount, category_display)
```

---

## 4. API Routes Críticas

| Rota | Método | Uso |
|------|--------|-----|
| `/aplicacoes/api/application-students/missed-at-exam/<exam_id>/` | GET | Retorna `[{id, student: {id, name, enrollment_number, school_class, unity}}]` |
| `/cadernos/api/listar/segunda-chamada/?search=<termo>&limit=<n>&offset=<n>` | GET | Lista cadernos elegíveis com `has_valid_application=True` |
| `/aplicacoes/cadastrar/` (POST form) | POST | Persiste aplicação; campo `is_second_call` via hidden input |
| `/aplicacoes/<pk>/editar` (POST form) | POST | Atualiza aplicação com `is_second_call` |

---

## 5. Automation Snippet (Playwright + mixer)

```python
# Exemplo de teste Playwright para abrir o modal de 2ª chamada
# Inclui setup de dados via mixer

import pytest
from playwright.sync_api import Page
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from django.utils import timezone
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember
from fiscallizeon.exams.models import Exam
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.students.models import Student


@pytest.fixture
def coord_with_second_call_data(db):
    """Setup completo para testar o fluxo de 2ª chamada."""
    from django.core import management
    management.call_command('initial_configs')

    coord = mixer.blend(User)
    coord.user_permissions.set(Permission.objects.all())
    coord.set_password('pass')
    coord.save()

    client = mixer.blend(Client, has_exam_elaboration=True)
    unity = mixer.blend(Unity, client=client)
    coordination = mixer.blend(SchoolCoordination, unity=unity)
    mixer.blend(CoordinationMember, user=coord, coordination=coordination)

    exam = mixer.blend(Exam, is_abstract=False, not_applicable=False)
    exam.coordinations.add(coordination)

    application = mixer.blend(
        Application,
        exam=exam,
        date=timezone.localdate(),
        student_stats_permission_date=timezone.localdate(),
    )

    student = mixer.blend(Student, client=client, user__is_active=True)
    mixer.blend(ApplicationStudent, application=application, student=student, missed=True)

    return {'coord': coord, 'exam': exam}


def test_second_call_modal_opens(page: Page, live_server, coord_with_second_call_data):
    """Verifica que o modal de prova anterior abre corretamente."""
    data = coord_with_second_call_data

    page.goto(f"{live_server.url}/aplicacoes/cadastrar/")
    page.fill('#id_username', data['coord'].username)
    page.fill('#id_password', 'pass')
    page.keyboard.press('Enter')
    page.wait_for_timeout(2000)

    # Ativa toggle de 2ª chamada
    page.locator('#is_second_call_toggle').click()
    page.wait_for_timeout(500)

    # Clica no CTA de seleção de prova anterior
    page.locator('button[class*="openSelectPreviousExamModal"]').click()
    page.wait_for_selector('#selectPreviousExamModal.show')

    # Verifica caderno na lista
    page.wait_for_selector('div[class*="tw-cursor-pointer"]')
    assert data['exam'].name in page.content()
```

---

## 6. Regras de Negócio e Casos de Borda (QA Knowledge Base)

Durante a exploração QA desta interface e das suas integrações (API), mapeamos as seguintes regras críticas de Backend que devem ser levadas em consideração ao construir testes E2E:

1. **Acesso por Professores (Teacher Role):**
   - O Backend (API) permite listar aplicações de 2ª chamada onde o usuário seja um professor (a query cruza `examteachersubject` para retornar apenas cadernos do professor).
   - O botão/toggle na interface (`#is_second_call_toggle`) **deve ser visível para professores**. (Havia um bug histórico no HTML que bloqueava com `{% if not user.user_type == "teacher" %}`).

2. **Ausência Canônica vs `missed=True`:**
   - Para provas Online, a API baseia-se na flag `missed=True`.
   - Para provas Presenciais, um aluno pode ter `missed=False`, mas se ele **não possui submissão de OMR**, a API (`has_missed_at_exam`) considerá-lo-á **Ausente Canônico** e ele DEVE aparecer na lista de alunos do Modal. Testes E2E devem cobrir alunos sem resposta.

3. **Deduplicação de Alunos (Dedupe):**
   - Se o mesmo aluno esteve ausente em **múltiplas** aplicações da 1ª chamada de um caderno, ele deve aparecer **exatamente uma vez** na lista do Modal de seleção. O endpoint realiza deduplicação (`rule 2.6 do service`).

4. **Alunos Inativos:**
   - Alunos com `user__is_active=False` na conta, mesmo que tenham faltado na prova (com `missed=True`), **NÃO devem aparecer** na lista do Modal (query filtra por `student__user__is_active=True`).

5. **Lógica de Filtros no Modal (Unidade/Turma):**
   - A seleção múltipla de chips deve atuar como lógica aditiva (União/OR). Ao selecionar `Unidade A` e `Turma B`, a lista deve renderizar a união de ambos. (Histórico de bug: implementação anterior usava lógica AND).

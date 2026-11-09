# Mapeamento de Tela: exam_teacher_create_update.html / exam_teacher_create_update_v2.html

> Templates:
> - Legado: `fiscallizeon/exams/templates/dashboard/exams/exam_create/exam_teacher_create_update.html`
> - Real (`?v=2`): `fiscallizeon/exams/templates/dashboard/exams/exam_create/exam_teacher_create_update_v2.html`

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Criar lista de exercício (real) | `/provas/prova/professor/?v=2&category=homework` | `exams:exam_teacher_create` (`ExamTeacherCreateUpdateTemplateView`) |
| Editar lista de exercício (real) | `/provas/prova/professor/<uuid:pk>/?v=2` | `exams:exam_teacher_update` (`ExamTeacherCreateUpdateTemplateView`) |
| Criar lista de exercício (legado) | `/provas/prova/professor/` | `exams:exam_teacher_create` |
| Editar lista de exercício (legado) | `/provas/prova/professor/<uuid:pk>/` | `exams:exam_teacher_update` |

- **Menu/lista:** o botão **“Criar Lista de Exercício”** e o item **“Editar”** sempre acrescentam `?v=2`.
- **Permissões:** `required_permissions = [TEACHER]`, `permission_required = 'inspectors.can_add_exercice_list'`; `client_teachers_can_elaborate_exam = True`; o caderno deve ser `Exam.HOMEWORK` e `created_by == user`.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam
from fiscallizeon.inspectors.models import Inspector, TeacherSubject

client_obj = mixer.blend(Client, has_exam_elaboration=True, client_teachers_can_elaborate_exam=True)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
teacher_user = mixer.blend(User, user_type='teacher', two_factor_enabled=False)
mixer.blend(CoordinationMember, user=teacher_user, coordination=coordination)
teacher = mixer.blend(Inspector, user=teacher_user, can_elaborate_questions=True)
teacher_subject = mixer.blend(TeacherSubject, teacher=teacher)
exam = mixer.blend(
    Exam,
    category=Exam.HOMEWORK,
    created_by=teacher_user,
    coordinations=[coordination],
    base_text_location=Exam.SHARED_BELOW,
)
```

## 3. Seletores DOM e Ações

### Versão real (`?v=2`) — `exam_teacher_create_update_v2.html`
- **Título:** `“Nova lista de exercício”`
- **Formulário:** `#form-professor-create-update` (`onsubmit="return false"`, `@submit="saveForm()"`)
- **Handler:** `saveForm()` (`exam_teacher_create_update_v2.html:1429`)
- **Salvar e continuar:** `#form-professor-create-update button:has-text("Salvar e continuar")`
- **Avançar para aplicação:** `button:has-text("Salvar e continuar")` no bloco de aplicação (`controls.expanded = 'application'`)
- **Atenção:** este template **não contém** `base_text_location`, `#id_shared_below` nem a pergunta **“Onde serão mostrados os textos base?”**. A opção 4 não está disponível no fluxo real do professor.

### Versão legada — `exam_teacher_create_update.html`
- **Pergunta:** `label:has-text("Onde serão mostrados os textos base?")`
- **Grupo:** `input[name="base_text_location"]`
- **Por questão:** `#id_per_question` (`value="0"`)
- **Por disciplina:** `#id_exam_top` (`value="1"`)
- **Início do caderno:** `#id_subject_top` (`value="2"`)
- **Final do caderno:** `#id_subject_bottom` (`value="3"`)
- **Texto compartilhado com questões embaixo:** `#id_shared_below` (`value="4"`)
- **Binding:** `@click="exam.base_text_location = 4"`; classe ativa no label via `v-bind:class`.
- **Salvar Parcialmente:** `button:has-text("Salvar Parcialmente")`
- **Salvar e criar aplicação:** `button:has-text("Salvar e criar aplicação")`
- **Salvar parcialmente (rodapé):** `button:has-text("Salvar parcialmente")`
- **Handler:** `saveExam()` (`exam_teacher_create_update.html:977`)

## 4. API Interception & Fixtures (rotas e entidades críticas)

- A tela é `TemplateView`; a persistência é feita pelo front via API de cadernos (`POST/PUT /provas/api/prova/`).
- **Entidades para render:** `Inspector`, `TeacherSubject`, `Grade`, `Subject`, `ExamTeacherSubject`, `Exam`.
- **Campos correlatos:** `category` (`Exam.HOMEWORK = 1`), `created_by`, `base_text_location`, `client_teachers_can_elaborate_exam`.
- **Gap conhecido:** a opção 4 só pode ser validada pela URL legada sem `?v=2`; o fluxo real `?v=2` precisa de follow-up para incluir o controle.

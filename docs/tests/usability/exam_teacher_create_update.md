# Mapeamento de Tela: exam_teacher_create_update.html / exam_teacher_create_update_v2.html

> [!CAUTION]
> **ARMADILHA DE CÓDIGO MORTO (`exam_teacher_create_update.html` DESCONTINUADO):**
> O template legado `fiscallizeon/exams/templates/dashboard/exams/exam_create/exam_teacher_create_update.html` (rota sem `?v=2`) está **oficialmente descontinuado** (confirmado em code review na task `CU-86akta6jf`, comentário `1400580000352050`).
> - **Para Desenvolvedores e IA:** NUNCA edite `exam_teacher_create_update.html` e NUNCA inclua esse arquivo em PRs ou diffs.
> - **Para Planos de QA:** NUNCA gere cenários de teste acessando `/provas/prova/professor/` sem `?v=2`. Apenas a versão `?v=2` (`exam_teacher_create_update_v2.html`) faz parte do fluxo ativo do sistema.

> Templates:
> - **Ativo (`?v=2`):** `fiscallizeon/exams/templates/dashboard/exams/exam_create/exam_teacher_create_update_v2.html`
> - **Descontinuado (NÃO USAR):** `fiscallizeon/exams/templates/dashboard/exams/exam_create/exam_teacher_create_update.html`

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

### Versão legada DESCONTINUADA — `exam_teacher_create_update.html`
- **Status:** **DESCONTINUADO — NÃO EDITAR NEM TESTAR.**
- Mantém apenas as 4 opções originais de `base_text_location` (`0..3`) da `master` por preservação histórica até remoção definitiva do arquivo.

## 4. API Interception & Fixtures (rotas e entidades críticas)

- A tela é `TemplateView`; a persistência é feita pelo front via API de cadernos (`POST/PUT /provas/api/prova/`).
- **Entidades para render:** `Inspector`, `TeacherSubject`, `Grade`, `Subject`, `ExamTeacherSubject`, `Exam`.
- **Campos correlatos:** `category` (`Exam.HOMEWORK = 1`), `created_by`, `base_text_location`, `client_teachers_can_elaborate_exam`.

## 5. Grafo de Dependências e Impacto Cruzado (Upstream & Downstream)

- **⬆️ Tela Canônica de Configuração de Caderno (Coordenação):** 🔗 [exam_request_create_update_new.md](./exam_request_create_update_new.md) (onde configurações avançadas como `base_text_location` são efetivamente gerenciadas).
- **⬇️ Consumidores do Caderno Gerado:** 🔗 [exam_homework_print.md](./exam_homework_print.md) e 🔗 [student_homework.md](./student_homework.md).

## 6. Armadilhas Conhecidas e Cruzamentos Obrigatórios de QA (Histórico de Reviews)

- **[Review CU-86akta6jf — Falso Positivo de `grep` em Templates Legados]:** Ao buscar por campos de `Exam` via `grep` no repositório, `exam_teacher_create_update.html` aparecerá nos resultados por conter inputs homônimos aos de `exam_request_create_update_new.html`. Se o `/qa-criar-plano` detectar alterações em `exam_teacher_create_update.html` no `git diff`, deve imediatamente emitir um alerta de higiene de escopo recomendando `git checkout master -- fiscallizeon/exams/templates/dashboard/exams/exam_create/exam_teacher_create_update.html`.

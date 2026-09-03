# Mapeamento de usabilidade — `question_create_update_redesign.html`

Template da versão nova da tela de criar/editar questão (`?v=redesign`).

## 1. URLs e Navegação

| Modo | URL Django | View name | Query params relevantes |
|------|------------|-----------|-------------------------|
| Criar (página) | `/questoes/cadastrar/?v=redesign` | `questions:questions_create` | — |
| Editar (página) | `/questoes/<uuid>/editar/?v=redesign` | `questions:questions_update` | — |
| Editar (popup) | `/questoes/<uuid>/editar/?v=redesign&is_popup=1&exam_question_id=<uuid>` | `questions:questions_update` | `is_popup=1`, `exam_question_id` |
| Criar com ETS | `/questoes/cadastrar/?v=redesign&exam_teacher=<uuid>` | `questions:questions_create` | `exam_teacher` |
| Dual-acesso (visualização caderno) | Trilho **Editar** → **Editar — versão nova** | — | Abre popup com `v=redesign` |
| Dual-acesso (modal revisão) | **Edição completa — versão nova** | — | `urlQuestionUpdateRedesign()` em `exam_request_create_update_new.html` |

**Navegação típica (coordenação, popup):**

1. `/provas/<exam_pk>/visualizar` (`exams:exams_preview`)
2. Trilho de ações → **Editar** (dropdown) → **Editar — versão nova**
3. Popup renderiza `question_create_update_redesign.html` (sem sidebar/header global)

**Default sem `v=redesign`:** continua servindo `question_create_update.html` (legado).

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

Padrão copiado de `fiscallizeon/questions/tests/test_question_edit_redesign.py` (`_QuestionEditRedesignMixin`):

```python
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.utils import timezone
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import (
    Client, CoordinationMember, SchoolCoordination, Unity,
)
from fiscallizeon.classes.models import Grade
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject
from fiscallizeon.inspectors.models import Inspector, InspectorCoordination, TeacherSubject
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.subjects.models import Subject

permissions = Permission.objects.filter(
    codename__in=['coordination', 'teacher', 'add_question', 'change_question', 'view_question']
)

client_obj = mixer.blend(
    Client,
    has_exam_elaboration=True,
    two_factor_enabled=False,
    has_cloze_question=False,
    has_question_formatter=False,
    use_internal_question_code=False,
)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
grade = mixer.blend(Grade)
subject = mixer.blend(Subject)

coordinator = mixer.blend(User, two_factor_enabled=False, must_change_password=False)
mixer.blend(CoordinationMember, user=coordinator, coordination=coordination)
coordinator.user_permissions.set(permissions)

question = mixer.blend(
    Question, grade=grade, subject=subject, category=Question.CHOICE, created_by=coordinator,
)
question.coordinations.add(coordination)
for i in range(4):
    mixer.blend(QuestionOption, question=question, is_correct=(i == 0))
```

**Permissões da view:** `LoginRequired2FAMixin`, `CheckHasPermission` (`COORDINATION`/`TEACHER`), `questions.add_question` / `change_question`, módulo `client_has_exam_elaboration`.

**Cloud Lab (smoke manual):** `cloud.coord@lize.local` (coordenação) ou `cloud.teacher@lize.local` (professor); senha padrão do lab.

## 3. Seletores DOM e Ações

### Escopo raiz Alpine

| Seletor / atributo | Uso |
|--------------------|-----|
| `[data-question-edit-redesign="1"]` | Container raiz com `x-data="questionEditForm(...)"` |
| `#questionForm` | Form POST principal (`@submit.prevent="handleSubmitFormQuestion"`) |
| `#question-server-field-errors` | JSON de erros server-side (`form.errors` / `obligation_error`) |

**Estado Alpine (referência):** `activeTab` ∈ `questao` \| `pedagogico` \| `competencias` \| `impressao`; `errorCounts.<aba>` alimenta badges das abas.

### Shell (`question_edit_shell`)

| Seletor | Ação / seção |
|---------|--------------|
| `#question-edit-shell-footer` | Footer fixo: Cancelar, Desfazer alterações, Salvar questão |
| `#question-edit-toolbar-sidebar` | Coluna da toolbar TinyMCE (aba Questão, lg+) |
| `#question-edit-richtext-toolbar` | Toolbar rich text compartilhada |
| `#shortcuts-modal-trigger` | Gatilho oculto do modal Atalhos |
| Botão texto **Atalhos do teclado** | Abre `#shortcutsModal` |
| Botão **Utilizações (N)** | `x-show="historicalQuestion.length > 0"`, `@click="openUtilizationsDrawer()"` |
| Botão **Histórico** | `@click="openHistoryDrawer()"` (só se `object.history.all`) |
| Botão **Salvar questão** (header) | `@click="handleSubmitFormQuestion()"` |

### Abas (`components/tabs.trigger`)

| Tab id (`activeTab`) | Label UI | Painel |
|--------------------|----------|--------|
| `questao` | Questão | `question_edit_tab_questao` |
| `pedagogico` | Dados pedagógicos | `question_edit_tab_pedagogico` |
| `competencias` | Competências e habilidades | `question_edit_tab_competencias` |
| `impressao` | Impressão | `question_edit_tab_impressao` |

### Aba Questão

| Seletor | Descrição |
|---------|-----------|
| `[role="radiogroup"] [role="radio"]` | Cards de tipo (`question_edit_type_cards`); `@click="selectQuestionType(category, isEssay)"` |
| `#id_category` | Hidden/select real de `category` (POST) |
| `input[name="is_essay"]` | Hidden `is_essay` |
| `#question-edit-enunciation-anchor` | Âncora do enunciado TinyMCE |
| `#question-edit-richtext-content` | Bloco enunciado + campos rich text |
| `#row-alternatives` | Tabela formset de alternativas (Objetiva/Somatório) |
| `#history-details-modal-trigger` | Gatilho oculto modal **Ver versão** |

### Aba Dados pedagógicos

| Seletor | Descrição |
|---------|-----------|
| `#id_grade` | Ano/Série (POST) |
| `#id_subject` | Disciplina (POST) |
| `#id_level` | Nível de dificuldade (POST) |
| `#question-edit-topics-tree` | Árvore Etapa → Tema → Assunto principal → Assunto |
| `.question-edit-topic-checkbox` | Checkbox de assunto |
| `#question-edit-create-topic-drawer` | Drawer Cadastrar assunto |
| `#question-edit-main-topic-row` | Linha Tópico no drawer |
| `#question-edit-main-topic-field` | Select Tópico |
| `#question-edit-main-topic-button` | Botão + cadastrar tópico |

### Aba Competências e habilidades

| Seletor | Descrição |
|---------|-----------|
| `.question-edit-bncc-lists-wrap` | Wrapper das duas colunas |
| `.question-edit-bncc-checkbox` | Checkbox competência/habilidade |
| `#question-edit-create-ability-drawer` | Drawer Cadastrar habilidade |
| `#question-edit-create-competence-drawer` | Drawer Cadastrar competência |

### Aba Impressão (9 campos — names preservados)

| `name` / `id` | Widget |
|---------------|--------|
| `print_only_enunciation` | switch_toggle |
| `force_choices_with_statement` | switch_toggle |
| `break_enunciation` | switch_toggle |
| `force_one_column` | switch_toggle |
| `number_is_hidden` | switch_toggle (rótulo UI: **Não exibir numeração**) |
| `force_break_page` | switch_toggle |
| `text_question_format` | select |
| `quantity_lines` | number (`id_quantity_lines`) |
| `draft_rows_number` | number |

### Hiddens críticos (POST)

| `name` | Condição |
|--------|----------|
| `is_popup` | `?is_popup=1` |
| `exam_teacher` | query `exam_teacher` |
| `selected_tags`, `status_note` | sempre presentes (fluxo tags não acionado por Edição completa) |
| `base_texts` | dinâmico via `x-for` em `selectedBaseTexts` |
| `topics` | via árvore de assuntos |
| `competences`, `abilities` | via checkboxes BNCC |
| `coordinations` | select oculto múltiplo |

## Critical API Routes

| Endpoint | Uso na tela |
|----------|-------------|
| `classes:grade_list_api` | Cascata Segmento → séries |
| `subjects:knowledge_area_list_api` | Áreas |
| `subjects:subject_list_api` | Disciplinas |
| `subjects:topic_list_api` | Árvore assuntos |
| `subjects:theme_list_api`, `main_topic_list_api` | Drawer assunto |
| `subjects:topic_create_complete` | POST cadastrar assunto |
| `subjects:theme_create_api`, `main_topic_create_api` | + inline tema/tópico |
| `bncc:competence_list_api`, `ability_list_api` | Listas BNCC |
| `bncc:competence_create_api`, `ability_create_api` | Drawers cadastro |
| `questions:base_text_list_create` | Criar texto base |
| `questions:base_text_retrive_update_destroy` | Editar/excluir texto base |
| `questions:question_historical` | GET utilizações (`historicalQuestion`) |
| `questions:formatter` | Formatador IA (só criação) |
| `exams:exams_preview` | Link caderno no drawer Utilizações |

## Entidades complexas

- `Question` + `QuestionOption` formset (até 5 alternativas)
- `ClientTeacherObligationConfiguration` → obrigatoriedade por segmento
- `Question.reason_can_be_updated(user)` → 7 mensagens de bloqueio
- Flags de cliente: `use_internal_question_code`, `has_cloze_question`, `has_question_formatter`, `can_add_support_content_discursive_questions`

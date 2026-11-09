# Mapeamento de Tela: exam_print.html

> Template: `fiscallizeon/exams/templates/dashboard/exams/exam_print.html`
> View: `ExamPrintView` (`fiscallizeon/exams/views/exams.py:3312`)

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Abrir modal e imprimir caderno | `/provas/<uuid:pk>/imprimir` | `exams:exam_print` (`ExamPrintView`) |
| Imprimir versão de aluno (randomizada) | `/provas/<uuid:pk>/imprimir?application_student=<uuid>&version_number=<n>` | idem |
| Diagramar caderno v2 (não alterado) | `/provas/<uuid:pk>/v2/imprimir/` | `exams:exam-print-v2` (`ExamPrintV2View`) |
| Listar cadernos | `/provas/?category=exam` | `exams:exams_list` |

- **Menu:** linha do caderno → **“Opções”** → seção **“Impressão”** → **“Imprimir caderno”**.
- **Disponibilidade:** o item só aparece quando `exam.is_printed == False`.
- **Permissões:** `required_permissions = [COORDINATION, TEACHER, PARTNER]`; usuário precisa de `exams.can_print_exam` e `exams.view_exam`; `Exam.can_print` deve ser verdadeiro (sem malote associado e não marcado como impresso).
- **Modal:** `#configurePrintModal`; formulário `#configure_print_form_id` (`method="get"`, `target="_blank"`); ação definida por `openConfigurePrintModal(url)`.
- **Submit:** botão com texto **“Imprimir prova”**.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam

client_obj = mixer.blend(Client, has_exam_elaboration=True)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
user = mixer.blend(User, user_type='coordination', two_factor_enabled=False)
mixer.blend(CoordinationMember, user=user, coordination=coordination)
user.user_permissions.add(
    Permission.objects.get(content_type__app_label='exams', codename='can_print_exam'),
    Permission.objects.get(content_type__app_label='exams', codename='view_exam'),
)
exam = mixer.blend(
    Exam,
    coordinations=[coordination],
    base_text_location=Exam.SHARED_BELOW,
    is_printed=False,
)
```

- Para o cenário de texto compartilhado, vincular o mesmo `BaseText` a duas questões e criar `ExamQuestion` com `order` correspondente.
- Para o cenário randomizado, criar `RandomizationVersion` e `ApplicationStudent` com `version_number`.

## 3. Seletores DOM e Ações

### Lista de cadernos
- **Linha:** `tr#tr-{{ exam.pk }}`
- **Abrir menu:** `button#dropdownMenuButton-{{ exam.pk }}` (texto **“Opções”**)
- **Abrir modal:** `a:has-text("Imprimir caderno")`
- **Handler:** `openConfigurePrintModal('{% url "exams:exam_print" pk=exam.pk %}')`

### Modal `#configurePrintModal`
- **Container:** `#configurePrintModal`
- **Formulário:** `#configure_print_form_id`
- **Modelo de caderno:** `input[name="separate_subjects"]`
  - `#separate_subjects_default` (`value="0"`) → Caderno Único
  - `#separate_subjects_enem` (`value="1"`) → Caderno por Disciplina
  - `#separate_by_question_type` (`value="2"`) → Caderno por tipo de questão
- **Botão de submit:** `#configure_print_form_id button[type="submit"]:has-text("Imprimir prova")`
- **Ação:** abre o PDF em nova aba com `target="_blank"`.

### Página de impressão (`exam_print.html`)
- **Bloco de texto compartilhado:** `#baseText_<base_text_id>` e `[data-baseText="baseText_<base_text_id>"]`
- **Rodapé de questões:** `.text-base-questions-footer`
- **Questão:** `.question#question-<question_id>`
- **Enunciado:** `.question-enunciation`
- **Aviso residual:** texto **“Esta questão possui”** (`text_relation.html`) — deve estar ausente na opção 4.
- **Título do texto:** `#baseText_<id> .base-text-title` (quando aplicável)
- **Indicação esperada:** `“Texto para a questão X”` ou `“Texto para as questões X e Y”`.

## 4. API Interception & Fixtures (rotas e entidades críticas)

- `GET /provas/<uuid>/imprimir` → renderiza HTML de impressão; parâmetros relevantes:
  - `separate_subjects=0|1|2`
  - `application_student=<uuid>` e `version_number=<n>` (ramo randomizado)
  - `hide_dialog`, `economy_mode`, `two_columns`, `line_textual`, `font_size`, `paper_size`, `margin_*`, `header`, `background_image`.
- **Ramificação de randomização:** `ExamPrintView.get_context_data()` consulta `RandomizationVersion.objects.filter(application_student=application_student, version_number=GET version_number)`. Sem `application_student`, o ramo não é ativado e `context['questions']` é usado.
- **Entidades para render:** `Exam`, `ExamQuestion`, `ExamTeacherSubject`, `Question`, `QuestionOption`, `BaseText`, `RandomizationVersion`, `ApplicationStudent`.
- **Atenção:** o botão **“Diagramar caderno”** usa outro template (`dashboard/exams/v2/exam_print.html`) e não é coberto por este mapeamento.

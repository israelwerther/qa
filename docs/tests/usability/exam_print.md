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

## 5. Grafo de Dependências e Impacto Cruzado (Upstream & Downstream)

- **⬆️ Origem das Configurações (Upstream):**
  - 🔗 [exam_request_create_update_new.md](./exam_request_create_update_new.md) — Cadastro/edição do caderno (`base_text_location`, `random_questions`, `group_discursive_questions_at_end`, `start_number`).
  - 🔗 [modal_print.md](./modal_print.md) / 🔗 [exam_configs_form.md](./exam_configs_form.md) / 🔗 [print_defaults_create_update.md](./print_defaults_create_update.md) — Configurações de diagramação e parâmetros GET (`separate_subjects`, `hide_numbering`, `economy_mode`, `two_columns`).
  - `fiscallizeon/exams/tasks/exams_imports.py` — Cadernos criados via importação de planilha CSV.
- **🧩 Partials e Métodos JS Compartilhados (Atenção ao Impacto Cruzado):**
  - **Layouts internos de `exam_print.html`:**
    - `fiscallizeon/exams/templates/dashboard/exams/includes/exam/not_separate.html` (`separate_subjects=0`)
    - `fiscallizeon/exams/templates/dashboard/exams/includes/exam/separate_subjects.html` (`separate_subjects=1`)
    - `fiscallizeon/exams/templates/dashboard/exams/includes/exam/separate_category.html` (`separate_subjects=2` — divide em 3 blocos: `['Objetiva']`, `['Somatório']` e `['Discursiva', 'Arquivo anexado', 'Preencher lacunas']`).
  - **Partials de Texto-Base:** `per_questions.html`, `shared_below.html`, `subjects_top.html`, `exam_top_bottom.html`, `text_relation.html`.
  - **JS Compartilhado:** `fiscallizeon/exams/templates/dashboard/exams/includes/base_texts/methods/base_texts-functions.js`.
- **⬇️ Telas Irmãs que Compartilham `base_texts-functions.js` e Partials de Texto-Base:**
  - 🔗 [exam_preview.md](./exam_preview.md) (`exam_preview.html`)
  - 🔗 [exam_homework_print.md](./exam_homework_print.md) (`exam_homework_print.html`)
  - 🔗 [student_homework.md](./student_homework.md) (`student-homework.html` e `student-new-exam.html` — realização da atividade/prova pelo aluno)
  - ⚠️ **Diferença Crítica de Contrato Vue:** `this.printConfig` existe em `exam_print.html`, mas **NÃO existe** (`undefined`) em `exam_preview.html`, `exam_homework_print.html`, `student-homework.html` e `student-new-exam.html`. Qualquer método em `base_texts-functions.js` ou expressão em partial compartilhado DEVE acessar `this.printConfig && this.printConfig.hideNumbering` de forma defensiva!

## 6. Armadilhas Conhecidas e Cruzamentos Obrigatórios de QA (Histórico de Reviews)

Sempre que uma tarefa alterar a renderização de questões, cabeçalhos, numeração ou textos-base em `exam_print.html` (ou seus partials), o Plano de QA **DEVE incluir obrigatoriamente** os seguintes cenários combinatórios:

1. **[Review CU-86akta6jf — Cruzamento com `Question.number_is_hidden = True` (Parcial e Total)]:**
   - Questões marcadas com *"Não mostrar numeração"* (`number_is_hidden = True`) recebem `number_print = ""` (e o sistema não gasta número nelas, deslocando a numeração para a próxima questão visível).
   - **Cenário Parcial Obrigatório:** Vincular 3 questões ao mesmo recurso (ex.: texto-base), marcando Q1 e Q3 com `number_is_hidden = True` e deixando apenas Q2 com `number_is_hidden = False` (`number_print = 1`). Validar que o rodapé/referência exibe no **singular** `(Texto para a questão 1)`, sem vírgulas ou conectivos órfãos como `(Texto para as questões , 1 e )`.
   - **Cenário Total Obrigatório:** Marcar **todas** as questões vinculadas ao recurso com `number_is_hidden = True` (ou vincular a apenas 1 questão oculta). Validar que o rodapé/referência numérica é completamente omitido (não exibir `(Texto para a questão )`).
2. **[Review CU-86akta6jf — Cruzamento com `?hide_numbering=1` (Prova Inteira sem Numeração)]:**
   - Acessar `/provas/<uuid>/imprimir?hide_numbering=1` (`printConfig.hideNumbering = true`).
   - Validar que, além de ocultar o cabeçalho `"Questão X"` nos enunciados, nenhuma referência numérica residual (como `(Texto para as questões 1, 2 e 3)`) aparece nos textos-base ou agrupadores.
3. **[Review CU-86akta6jf — Cruzamento de Categorias Mistas com `?separate_subjects=2` (`separate_category.html`)]:**
   - No modo `separate_subjects=2`, o template `separate_category.html` imprime primeiro todas as **Questões Objetivas**, depois **Somatório** e por último **Questões Discursivas**, independentemente da ordem global da questão no caderno.
   - **Cenário Misto Obrigatório:** Configurar um mesmo texto-base/recurso compartilhado entre **Questão 1 = Discursiva** (menor número global) e **Questões 2 e 3 = Objetivas**, e abrir `/provas/<uuid>/imprimir?separate_subjects=2`.
   - Validar que o bloco de **Questões Objetivas** (impresso no início da prova) exibe o texto-base antes da primeira questão objetiva vinculada com rodapé escopado apenas às objetivas `(Texto para as questões 2 e 3)` (sem deixar as objetivas órfãs!), e que o bloco de **Questões Discursivas** (no final) também exibe o texto-base antes da discursiva com rodapé escopado `(Texto para a questão 1)` (sem duplicar números como `1, 1 e 3`).
4. **[Regra Anti-Regressão em `base_texts-functions.js`]:**
   - Nunca sobrescrever o comportamento de `getQuestionsWithTheseBaseTexts` ou `getTheLowestNumber` usados por `per_questions.html` (opção legada `0`). Utilizar sempre os helpers dedicados (`getNumberedQuestionsWithTheseBaseTexts` e `getTheLowestNumberForSection`) para a opção `4`.

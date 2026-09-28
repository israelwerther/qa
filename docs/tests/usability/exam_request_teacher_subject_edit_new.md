# Mapeamento de Tela: Elaboração de Caderno / Importação DOC (exam_request_teacher_subject_edit_new.html)

Mapeamento técnico da tela de Edição de Questões da Disciplina do Caderno e do componente de pré-visualização de importação via DOC (IA).

---

## 1. URLs e Navegação

| Destino | Rótulo real no menu UI | URL Django | View / Action |
|---------|------------------------|------------|---------------|
| Lista de solicitações | **Cadernos** → **"Solicitações de elaboração"** | `/provas/professor/` | `exams:exam-teacher-subject-list` (`ExamTeacherSubjectListView`) |
| Editar questões do caderno | Continuar / Editar questões (card da solicitação) | `/provas/prova/<uuid:pk>/editar/` | `exams:exam_teacher_subject_edit_questions` (`ExamTeacherSubjectEditQuestionsView`) |
| Template renderizado (experiência nova) | — | mesmo URL acima (sem `?v=`) | `exam_request_teacher_subject_edit_new.html` quando `has_new_teacher_experience` |
| Modal/Fullscreen de Importação DOCX | Importar Questões via Arquivo | (Front-end CustomEvent) | Componente `import_preview` |
| Upload API DOCX | — | `/provas/prova/<uuid:pk>/importar-docx/` | `exams:exam_questions_import` (`ExamQuestionsImportView`) |

> **Pré-condição de template:** a view só serve `exam_request_teacher_subject_edit_new.html` se `user.inspector.has_new_teacher_experience` **ou** `user.client_has_new_teacher_experience` **ou** `exam.created_by == user`. Caso contrário cai no template legado.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões Necessárias:
- Usuário autenticado com perfil de Professor (`user.user_type == 'TEACHER'`) associado a uma `Inspector` (ou Coordenador `user.user_type == 'COORDINATION'`).
- `user.inspector.has_new_teacher_experience = True` ou `user.client_has_new_teacher_experience = True` (para renderizar a versão redesenhada `exam_request_teacher_subject_edit_new.html`).
- O caderno (`Exam`) não pode ter aplicação iniciada, gabarito/respostas preenchidas ou malote gerado.

### Setup de Banco de Dados (`mixer`):

```python
from fiscallizeon.exams.models import Exam, ExamTeacherSubject, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.subjects.models import TeacherSubject, Subject
from fiscallizeon.inspectors.models import Inspector
from fiscallizeon.accounts.models import User
from mixer.backend.django import mixer

# 1. Usuário Professor com experiência nova
user = mixer.blend(User, user_type='TEACHER', must_change_password=False)
teacher = mixer.blend(
    Inspector,
    user=user,
    email=user.email,
    inspector_type=Inspector.TEACHER,
    has_new_teacher_experience=True,
    can_elaborate_questions=True,
)

# 2. Disciplina do Professor
subject = mixer.blend(Subject, name='Matemática')
teacher_subject = mixer.blend(TeacherSubject, teacher=teacher, subject=subject, active=True)

# 3. Prova / Caderno em elaboração
exam = mixer.blend(Exam, created_by=user)
exam_teacher_subject = mixer.blend(
    ExamTeacherSubject,
    exam=exam,
    teacher_subject=teacher_subject,
    quantity=5,
)

# 4. (Opcional) Questão discursiva para testar a barra de config
question = mixer.blend(Question, category=0, is_essay=False, quantity_lines=5)
mixer.blend(ExamQuestion, exam_teacher_subject=exam_teacher_subject, question=question, order=0)
```

---

## 3. Seletores DOM e Ações

### Página Principal de Edição (`exam_request_teacher_subject_edit_new.html`)

- **Botão Abrir Importação DOCX:**
  - Seletor: `button:has-text("Importar via DOCX")` ou `[data-testid="import-docx-btn"]`
  - Ação: Clicar para abrir modal de upload de arquivo `.docx`.
- **Input de Upload de Arquivo:**
  - Seletor: `input[type="file"][accept*=".docx"]`
- **Aba Enunciado:**
  - Seletor: texto `"Enunciado"` no menu de abas da questão (`@click="examQuestion.currentMenu = 'enunciation'"`)
- **Cards de tipo de questão** (`.question-type-options`):
  - `"Múltipla escolha"` → `changeQuestionCategory(1)`
  - `"Discursiva"` → `changeQuestionCategory(0)`
  - `"Redação"` → `changeQuestionCategory(0, true)` (dispara `updateQuantityLines()` → `quantityLines = 30`)
  - `"Arquivo anexado"` / `"Somatório"` / `"Preencher lacunas"` (flags de client)
- **Botão Salvar (rodapé do card da questão):**
  - Seletor: `button.lize-btn-primary:has-text("Salvar")` (texto vira `"Salvando..."` enquanto `controls.saving`)
- **Botão Salvar alterações (topo):**
  - Seletor: `button.lize-btn-primary:has-text("Salvar alterações")`

---

### Barra de configuração discursiva/redação (CU-86ajqpbw5)

Barra compacta **logo abaixo** de `.question-type-options` e **acima** do editor TinyMCE. Visível só quando `categoryDisplay == 'Discursiva'` (inclui redação com `isEssay`). Fundo `#F9FBFA`, `tw-flex tw-flex-wrap`, **não** há painel cinza abaixo do editor para esses campos.

| Campo UI (rótulo literal) | Binding Vue | Seletor estável |
|---------------------------|-------------|-----------------|
| **"Quantidade de linhas"** | `examQuestion.question.quantityLines` | `input[name="quantity_lines"]` / `#quantityLines-{examQuestion.id}` |
| Formato de impressão (sem label visível; options) | `examQuestion.question.textQuestionFormat` | `select` irmão do input de linhas — options `"Espaço em branco"` (`0`), `"Imprimir linhas"` (`1`) |
| **"Correção com competências"** (switch) | `examQuestion.question.correctionWithCompetencies` | `#idcorrectionWithCompetencies-{examQuestion.id}` |
| Select de modelo de correção | `examQuestion.question.textCorrection` | `select` ao lado do switch (options de `textCorrections`) |
| **"Valor esperado"** (PAS Tipo B, `exam_format == 1`) | `examQuestion.question.bTypeExpectedAnswer` | `#bTypeExpectedAnswer-{examQuestion.id}` — validação 0–999 via `validateExpectedValue` |

**Condições de ocultação:**
- Campos linhas/competências: ocultos se `isPasExam && isPasType(..., 'B')`
- Valor esperado: só se PAS + Tipo B + não redação

**Altura do editor:** `getQuestionContentHeight()` — penalidade extra (`isReducedHeightCategory`) agora só para `"Preencher lacunas"`; discursiva/redação usam a fórmula padrão (`calc(100vh - 300px)` / `calc(100vh - 260px)`).

**Sugestão de IDs estáveis (débito de automação):**
- Adicionar `id="discursive-config-bar"` no container da barra.
- Manter IDs dinâmicos `:id="'quantityLines-' + examQuestion.id"` (já gold standard).

---

### Componente de Preview (`import_preview`)

#### Shell & Header
- **Layout Fullscreen ID:** `#import-preview` (`fullscreen_layout`)
- **Botão Voltar / Fechar Header:**
  - Seletor: `button:has-text("Selecionar tipo de questão")` ou `button[aria-label="Fechar"]`
  - Ação Alpine: `@click="$store.importPreview.closeShell()"`

#### Sidebar (Navegação & Estatísticas)
- **Barra de Progresso (Válidas):**
  - Componente: `sidebar_progress`
  - Alpine Store: `$store.importPreview.stats.valid`, `$store.importPreview.stats.total`
- **Pills de Navegação por Questão:**
  - Seletor: `nav button.tw-rounded-full`
  - Ação Alpine: `@click="$store.importPreview.goToQuestion(index)"`
- **Botão Confirmar Importação:**
  - Seletor: `button:has-text("Confirmar importação")`
  - Condição Habilitado: `$store.importPreview.canConfirm()` (`invalid === 0 && valid > 0`)
  - Ação Alpine: `@click="$store.importPreview.confirm()"`
- **Botão Cancelar Importação:**
  - Seletor: `button:has-text("Cancelar")`
  - Ação Alpine: `@click="$store.importPreview.closeShell()"`

#### Card da Questão (`import_preview_question_card`)
- **Container do Card:**
  - Seletor: `#import-preview-question-[INDEX]`
- **Botões do Action Rail (Subir, Descer, Remover):**
  - Subir: `button[title="Mover para cima"]` (`$store.importPreview.moveQuestion(question, 'up')`)
  - Descer: `button[title="Mover para baixo"]` (`$store.importPreview.moveQuestion(question, 'down')`)
  - Remover: `button[title="Remover questão"]` (`$store.importPreview.removeQuestion(question)`)
- **Gabarito (Objetivas):**
  - Radio input: `input[type="radio"][name^="correct_choice_"]`
- **Gabarito (Somatório):**
  - Checkbox input: `input[type="checkbox"]` em cada alternativa

---

## 4. API Routes, Eventos e Comportamento de Lifecycle

- **Upload/Parse API (DOCX):** `POST /exams/prova/<uuid:pk>/importar-docx/` — Envia o arquivo `.docx` multipart e retorna JSON das questões extraídas.
- **Inserção de Questões (Backend API):** `POST /ai/import/` (`ai:import-questions-import`) — Submete cada questão para salvamento no caderno.
  - *Bug Conhecido (UX/Z-Index):* Caso a API retorne `HTTP 400 Bad Request` (ex: questão sem resposta correta), o erro é capturado e chama `alertTop`, mas a notificação fica **oculta atrás da camada z-index** do `fullscreen_layout` (`z-[99990]`).
- **Custom Events Frontend (Vue ↔ Alpine):**
  - Envio Vue → Alpine: `window.dispatchEvent(new CustomEvent('import-preview-open', { detail: { data: payload } }))`
  - Retorno Alpine → Vue: `window.addEventListener('import-preview-confirm', (e) => ...)`
  - Remoção de Questão: `window.dispatchEvent(new CustomEvent('import-preview-question-removed', { detail: {} }))` (desencadeia `Alpine.nextTick()` para recalcular scroll e reposicionar foco na questão restante (`#import-preview-question-[TARGET_INDEX]`)).


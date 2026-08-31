# Mapeamento de Tela: exam_essay_correction.html (e componentes associados)

> **Nota de Acervo:** Este arquivo é alimentado de forma incremental e colaborativa. Sempre que uma nova funcionalidade for testada nesta tela, o mapeamento de IDs e seletores estáveis deve ser atualizado aqui. O objetivo é criar um repositório centralizado para facilitar a automação via Playwright, sem depender de classes CSS frágeis.

## 1. URLs e Navegação
- **URL da Tela de Correção:** `/provas/<uuid>/correcao/?application_student=<uuid>&school_class=<uuid>` (ou `/provas/<uuid>/redacoes/correcao/?application_student=<uuid>&school_class=<uuid>`)
- **Navegação:** Na listagem de redações (`/provas/<exam_id>/redacoes/`), ao clicar em um aluno da lista, o usuário é direcionado para esta tela de correção.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
> **Acesso ao Módulo (Permissões):** O professor ou coordenador precisa de privilégios e o cliente precisa ter a flag `has_essay_system=True`. Para o Modo IA e Painel Lize AI aparecerem, a questão de redação precisa utilizar o modelo `Competências ENEM` (`Question.text_correction` contendo "Competências ENEM" e `Question.is_essay=True`).

```python
from mixer.backend.django import mixer
from fiscallizeon.core.models import Client
from fiscallizeon.users.models import User
from fiscallizeon.exams.models import Exam, Question, ExamQuestion, TextCorrection
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.answers.models import FileAnswer, EssayAICorrection, EssayAISuggestion
from fiscallizeon.students.models import Student

# 1. Cliente com sistema de redação habilitado
client = mixer.blend(Client, has_essay_system=True)

# 2. Usuário com papel de professor ou coordenador
teacher = mixer.blend(User, role='teacher', client=client, is_active=True)

# 3. Critério global ENEM
text_correction = mixer.blend(TextCorrection, name="Competências ENEM", client=None)

# 4. Questão de redação vinculada
question = mixer.blend(Question, client=client, is_essay=True, text_correction=text_correction)
exam = mixer.blend(Exam, client=client)
mixer.blend(ExamQuestion, exam=exam, question=question, order=1)

# 5. Aplicação, Turma, Aluno e Resposta
school_class = mixer.blend(SchoolClass, client=client)
student = mixer.blend(Student, client=client)
application = mixer.blend(Application, exam=exam, client=client)
app_student = mixer.blend(ApplicationStudent, application=application, student=student, school_class=school_class)
file_answer = mixer.blend(FileAnswer, student_application=app_student, question=question, arquivo="redacao.png")

# 6. Correção Lize AI populada
correction = mixer.blend(
    EssayAICorrection,
    file_answer=file_answer,
    status=EssayAICorrection.STATUS_READY,
    transcription="Texto da transcrição OCR com quebra de linha\nSegunda linha da redação.",
    total_score=840,
)
suggestion = mixer.blend(
    EssayAISuggestion,
    correction=correction,
    competency="c1",
    kind="deviation",
    status=EssayAISuggestion.STATUS_PENDING,
    payload={"start": 0, "end": 5, "excerpt": "Texto", "label": "Falha de concordância", "match_status": "corrected"}
)
```

## 3. Seletores DOM e Ações

### 3.1. Modo Correção de IA & Controles Centrais
- **Botão Modo Correção de IA (Estrela Flutuante):** `#ia` ou `.ai-mode-toggle` (ao clicar, ativa a classe `.activated`, encolhe a coluna esquerda e aciona o texto digitalizado).
- **Toggle Barra de Texto:** `.digitalized-toggle-bar`
  - **Botão Texto Original:** `.digitalized-toggle button:contains("Texto original")` ou `.digitalized-toggle button:first-child`
  - **Botão Texto Digitalizado:** `.digitalized-toggle button:contains("Texto digitalizado")` ou `.digitalized-toggle button:last-child` (desabilitado se `!lizeAI.correction.transcription`).
- **Toolbar de Zoom (Modo Imagem):** `#toolbarDiv` (`#home`, `#zoom-in`, `#zoom-out`) — oculto durante o modo digitalizado.

### 3.2. Painel Central de Texto Digitalizado (OCR)
- **Container do Texto Digitalizado:** `.digitalized-text-panel`
- **Página OCR:** `.ocr-page`
- **Linha da Folha:** `.ocr-page-line`
- **Número da Linha:** `.ocr-line-num` (1, 2, 3...)
- **Corpo da Linha:** `.ocr-line-body`
- **Marcadores de Desvio / Grifos (Highlights):** `.lize-ai-mark`
  - Atributos úteis para automação: `[data-suggestion-id="<uuid>"]`, `[data-start="<int>"]`, `[data-end="<int>"]`, `[data-match-status="<status>"]`.
  - Estados: `.is-accepted`, `.is-selected`, `.is-corrected`.
- **Popover Tooltip Hover:** `.lize-ai-popover` (exibe `Lize AI — <label>`).

### 3.3. Card de Revisão e Edição no Canvas
- **Card de Revisão Flutuante:** `.lize-ai-canvas-review`
- **Título do Card:** `.lize-ai-canvas-review-title` (interpolado como `Lize AI — <título>`)
- **Ações de Decisão:** `.lize-ai-canvas-review-actions`
  - **Botão Aceitar:** `.lize-ai-canvas-review-actions button.accept`
  - **Botão Recusar:** `.lize-ai-canvas-review-actions button.reject`
  - **Botão Desfazer:** `.lize-ai-canvas-review-actions button:has-text("Desfazer")`
  - **Botão Editar OCR:** `.lize-ai-canvas-review-actions button:has-text("Editar OCR")`
- **Modo de Edição do OCR:**
  - **Textarea de Edição:** `.lize-ai-canvas-review textarea[aria-label="Editar texto do OCR"]`
  - **Botão Salvar Edição:** `.lize-ai-canvas-review-actions button.accept:has-text("Salvar")`
  - **Botão Cancelar Edição:** `.lize-ai-canvas-review-actions button:has-text("Cancelar")`

### 3.4. Sidebar Direita — Painel Lize AI (Aba Corrigir)
- **Accordion Principal Lize AI:** `.lize-ai-panel`
- **Cabeçalho Principal:** `.lize-ai-panel-header` (abre/fecha o painel)
- **Badge Geral de Pendências:** `.lize-ai-panel-header .lize-ai-badge`
- **Ação Aceitar Tudo:** `.lize-ai-batch-action:has-text("Aceitar tudo")`
- **Ação Desfazer Tudo:** `.lize-ai-batch-action:has-text("Desfazer tudo")`
- **Seções por Competência (C1–C5):** `.lize-ai-section-header`
  - **Badge da Competência:** `.lize-ai-section-header .lize-ai-badge`
  - **Linha de Sugestão:** `.lize-ai-suggestion-row` (`[data-suggestion-id="<uuid>"]`)
  - **Chip de Tipo:** `.lize-ai-kind-chip` (ex: "Desvio", "Feedback", "Nota", "Rúbrica")
  - **Ação Aceitar na Linha:** `.lize-ai-action-btn.accept`
  - **Ação Recusar na Linha:** `.lize-ai-action-btn.reject`
  - **Ação Desfazer na Linha:** `.lize-ai-action-btn.undo`

## 4. Rotas Críticas de API e Entidades de Banco
- `POST /respostas/arquivos/<uuid:pk>/enem-ai-correction/` (enfileira ou reutiliza correção)
- `GET /respostas/arquivos/<uuid:pk>/enem-ai-correction/` (obtém status, transcrição com linhas e sugestões agrupadas C1–C5)
- `PATCH /respostas/arquivos/<uuid:pk>/enem-ai-correction/transcription/` (substitui trecho do OCR e realinha offsets)
- `POST /respostas/enem-ai-suggestions/<uuid:pk>/accept/` (aceita sugestão)
- `POST /respostas/enem-ai-suggestions/<uuid:pk>/reject/` (recusa sugestão)
- `POST /respostas/enem-ai-suggestions/<uuid:pk>/undo/` (desfaz decisão)
- `POST /respostas/arquivos/<uuid:pk>/enem-ai-correction/accept-all/` (aceita todas as pendentes)
- `POST /respostas/arquivos/<uuid:pk>/enem-ai-correction/undo-all/` (desfaz todas as decisões)

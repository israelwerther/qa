# Mapeamento de Tela: audio_answer_question.tsx (Componente de Resposta em Áudio - SPA Aluno)

> **Nota de Acervo:** Este arquivo mapeia seletores e comportamentos do componente `src/components/test-execution/question-strategies/audio-answer-question.tsx` e tela de revisão de questão `src/components/exam-result/question-review-sheet.tsx` no repositório `lize-student`.

## 1. URLs e Navegação
- **Ambiente SPA do Aluno:** `http://localhost:5173` (ou porta local de `bun dev`)
- **Tela de Realização de Prova (Online):** `/provas/<application_id>` (rota `src/routes/provas.$id.tsx`)
- **Tela de Resultados (Revisão da Prova):** `/painel/minhas-provas/<application_id>` (rota `src/routes/_app/painel/minhas-provas.$id.tsx`)

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
Para a questão exibir a interface de áudio no app do aluno:
1. Questão deve ser de categoria Arquivo (`Question.FILE` / valor `2`) com `Question.accepts_audio_response = True`.
2. A aplicação deve ser digital/online (`Application.category` online).
3. O aluno deve estar logado no SPA (geralmente autenticado via token de estudante).

```python
# Setup Python Backend (Mixer)
from mixer.backend.django import mixer
from fiscallizeon.questions.models import Question
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.students.models import Student

question = mixer.blend(
    Question,
    category=Question.FILE,
    accepts_audio_response=True,
    enunciation="<p>Grave um áudio de até 5 minutos lendo o texto indicado.</p>"
)
exam = mixer.blend(Exam)
mixer.blend(ExamQuestion, exam=exam, question=question, order=1)
application = mixer.blend(Application, exam=exam, category=Application.ONLINE)
student = mixer.blend(Student)
app_student = mixer.blend(ApplicationStudent, application=application, student=student)
```

## 3. Seletores DOM e Ações

### 3.1. Estado Inicial (Gravação ou Upload)
- **Container da Questão de Áudio:** `.flex.flex-col.items-center.border-dashed`
- **Texto de Instrução:** `p:has-text("Grave sua resposta em áudio (até 5 min) ou anexe um arquivo.")`
- **Botão Iniciar Gravação:** `button:has-text("Gravar")`
- **Botão Anexar Arquivo:** `button:has-text("Anexar áudio")`
- **Input File Oculto (Áudio):** `input[type="file"][accept="audio/*"]`

### 3.2. Estado Gravando
- **Botão Encerrar Gravação:** `button:has-text("Encerrar gravação")` (classe variante `destructive`)
- **Limite Automático:** 5 minutos (`MAX_RECORDING_MS = 300000`)

### 3.3. Estado de Preview (Áudio Gravado ou Selecionado)
- **Player de Preview:** `audio[controls]`
- **Botão Regravar / Descartar:** `button:has-text("Regravar")`
- **Botão Enviar Áudio:** `button:has-text("Enviar áudio")`

### 3.4. Estado de Feedback / Envio
- **Mensagem de Sucesso:** `p:has-text("Áudio enviado com sucesso!")` (texto verde `#16a34a`)
- **Mensagem de Erro de Arquivo/Microfone:** `p.text-xs.text-\[\#dc2626\]`
- **Indicador de Upload:** `p:has-text("Enviando...")` com spinner `.animate-spin`

### 3.5. Visualização no Resultado do Aluno (`question-review-sheet.tsx`)
- **Aba "Sua resposta":** Botão/Tab `[role="tab"]:has-text("Sua resposta")`
- **Player de Áudio da Resposta:** `.flex.items-center.justify-center.rounded-md audio[controls]`

## 4. Rotas Críticas de API
- `POST /api/v3/applications/<id>/create_answer/`
  - Content-Type: `multipart/form-data`
  - Payload: `question_id`, `category=file`, `file=<audio_blob_ou_file>`
  - Validação backend: `validate_student_file_answer` permite formatos `webm`, `mp3`, `mpeg`, `mp4`, `m4a`, `ogg`, `wav`, `aac` até 20MB quando `accepts_audio_response=True`.

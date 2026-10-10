# Mapeamento de Usabilidade — exam_detail_v2.html

## 1. URLs e Navegação

| Destino | URL | Como navegar |
|---------|-----|--------------|
| Listagem de provas | `/exams/` | Menu lateral → Instrumentos Avaliativos |
| Detalhe da prova (template legado) | `/exams/<id>/` | Clicar na prova na listagem |

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões
- Usuário com permissão de correção de professor.
- Cache de tipo de usuário: `USER_TYPE_<user_id>` = `TEACHER`.

### Fixture
```python
from mixer.backend.django import mixer
from decimal import Decimal
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.students.models import Student
from fiscallizeon.clients.models import Client
from fiscallizeon.answers.models import TextualAnswer

exam = mixer.blend(Exam, is_abstract=True)
question = mixer.blend(Question, category=Question.TEXTUAL)
exam_question = mixer.blend(ExamQuestion, question=question, exam=exam, weight=1)
client = mixer.blend(Client)
student = mixer.blend(Student, client=client)
application = mixer.blend(Application, exam=exam)
application_student = mixer.blend(ApplicationStudent, student=student, application=application)

textual_answer = mixer.blend(
    TextualAnswer,
    student_application=application_student,
    question=question,
    exam_question=exam_question,
    ai_grade=Decimal("0.7"),
    ai_explanation="Explicação detalhada.",
    teacher_grade=None,
    teacher_feedback=None,
)
```

## 3. Seletores DOM e Ações

### Card de Sugestão da IA (Template Legado)

| Elemento | Seletor | Ação |
|----------|---------|------|
| Botão "Aceitar apenas o feedback" | `button[title="Aceitar apenas o feedback"]` | Clique |
| Botão "Aceitar nota" | `button[title="Aceitar nota"]` | Clique |
| Botão "Aceitar nota e feedback" | `button[title="Aceitar nota e feedback"]` | Clique |

### Área de Correção

| Elemento | Seletor | Ação |
|----------|---------|------|
| Campo de nota | Input numérico dentro do card de correção | Digitação |
| Textarea de feedback | `textarea` dentro do collapse de comentário | Digitação |
| Botão salvar | Botão de ação na barra inferior | Clique |

### Funções JavaScript (Alpine.js)

| Função | Arquivo | Descrição |
|--------|---------|-----------|
| `setOnlyFeedback(suggestion)` | `exam-detail-functions.js` ou equivalente v2 | Preenche feedback sem atribuir nota |
| `setSuggestion(suggestion, setFeedback)` | `exam-detail-functions.js` ou equivalente v2 | Atribui nota (e feedback se solicitado) |

## 4. API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/questions/get_correction_answers/` | GET | Busca respostas para correção |
| `/api/v1/answers/text_update_feedback/<pk>/` | PUT | Salva feedback e nota de resposta textual |
| `/api/v1/answers/file_update_feedback/<pk>/` | PUT | Salva feedback e nota de resposta de arquivo |

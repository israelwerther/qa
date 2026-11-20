# Mapeamento de Tela: student-homework.html / student-new-exam.html

> Templates:
> - **Lista de Exercícios / Atividade do Aluno:** `fiscallizeon/applications/templates/dashboard/homeworks/student/student-homework.html`
> - **Prova Online Monitorada do Aluno:** `fiscallizeon/applications/templates/dashboard/monitoring/student/student-new-exam.html`
> - **Dados serializados compartilhados:** `fiscallizeon/applications/templates/dashboard/monitoring/student/includes/student-data-exam.js`

## 1. URLs e Navegação

| Ação | URL | View / Template |
|------|-----|-----------------|
| Realizar atividade / lista de exercício (Aluno) | `/aplicacoes/<uuid:pk>/realizar-atividade` | `student-homework.html` (`pk` = `ApplicationStudent.id`) |
| Realizar prova online monitorada (Aluno) | `/aplicacoes/<uuid:pk>/realizar-prova` [verificar rota exata em `applications/urls.py`] | `student-new-exam.html` (`pk` = `ApplicationStudent.id`) |

- **Persona:** Aluno (`user.user_type == 'student'`, `user.is_active == True`, `ApplicationStudent.student.user == request.user`).
- **Pré-condições da Aplicação (`Application`):**
  - Para `/realizar-atividade`: `application.category == Application.HOMEWORK` (`4`), data atual dentro da janela (`date` .. `date_end`, `start` .. `end`), `application_student.application_state != 'finished'`.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from datetime import date, time, timedelta
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import BaseText, Question
from fiscallizeon.students.models import Student

today = date.today()
client_obj = mixer.blend(
    Client,
    has_exam_elaboration=True,
    allow_login_only_google=False,
    two_factor_enabled=False,
)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)

student_user = mixer.blend(
    User,
    user_type='student',
    is_active=True,
    must_change_password=False,
    two_factor_enabled=False,
)
student_user.set_password('123456')
student_user.save()
student = mixer.blend(Student, user=student_user, client=client_obj)

exam = mixer.blend(
    Exam,
    coordinations=[coordination],
    base_text_location=Exam.SHARED_BELOW,
    random_questions=False,
)
base_text = mixer.blend(BaseText, title='Texto Base Teste', text='<p>Corpo do texto base</p>')
q1 = mixer.blend(Question, category=Question.CHOICE, number_is_hidden=False, base_texts=[base_text])
q2 = mixer.blend(Question, category=Question.CHOICE, number_is_hidden=False, base_texts=[base_text])
mixer.blend(ExamQuestion, exam=exam, question=q1, order=0)
mixer.blend(ExamQuestion, exam=exam, question=q2, order=1)

application = mixer.blend(
    Application,
    exam=exam,
    category=Application.HOMEWORK,
    date=today,
    date_end=today + timedelta(days=2),
    start=time(0, 0),
    end=time(23, 59),
)
app_student = mixer.blend(ApplicationStudent, application=application, student=student)
# URL de acesso: f"/aplicacoes/{app_student.id}/realizar-atividade"
```

## 3. Seletores DOM e Ações

### Renderização de Questões e Textos-Base
- **Container da questão:** `.question#question-<question_id>`
- **Bloco de texto-base compartilhado (`base_text_location == 4`):** `#baseText_<base_text_id>`
- **Título do texto-base (usado por `gerateBaseTextNumbers`):** `h6[data-baseText="baseText_<base_text_id>"]`
- **Rodapé de questões vinculadas (`shared_below.html`):** `.text-base-questions-footer` (ex.: `(Texto para as questões 1 e 2)`)
- **Aviso de relação com texto-base (`text_relation.html`):** `"Esta questão possui X texto(s) base"` / `"Leia o texto"` — **DEVE estar ausente** quando `base_text_location == 4` e presente nas opções `0..3`.
- **Número da questão:** `span.question-number` (`${ question.number_print }`)
- **Enunciado:** `question-enunciation.questions-images`

### Painel Lateral da Atividade
- **Acessibilidade (tamanho de fonte / contraste):** botões `A` e ícone de contraste
- **Botão Ver orientações:** `button:has-text("Ver orientações")`
- **Botão Encerrar prova:** `button:has-text("Encerrar prova")`

## 4. API Interception & Fixtures (rotas e entidades críticas)

- `GET /aplicacoes/<uuid:app_student_pk>/realizar-atividade` → renderiza `student-homework.html`.
- `GET /questoes/api/base_texts/<uuid:exam_pk>/` (`questions:base_text_exam`) → chamado no `mounted()` via `this.getBaseTextsExam('{{object.application.exam.pk}}').finally(() => this.gerateBaseTextNumbers())`.
- **Serialização inicial no template (`student-data-exam.js`):**
  - Quando `question.number_is_hidden == True`, `student-data-exam.js` define `number_print: null` (diferente de `exam_print.html`, onde `number_print` é `''`).

## 5. Grafo de Dependências e Impacto Cruzado (Upstream & Downstream)

- **⬆️ Origem das Configurações (Upstream):**
  - 🔗 [exam_request_create_update_new.md](./exam_request_create_update_new.md) (`Exam.base_text_location`, `Exam.random_questions`, `Exam.random_alternatives`).
  - 🔗 [application_create_update.md](./application_create_update.md) (`Application` e `ApplicationStudent`).
- **🧩 Partials e Métodos JS Compartilhados com Impressão (`exams`):**
  - `fiscallizeon/exams/templates/dashboard/exams/includes/base_texts/methods/base_texts-functions.js`
  - `fiscallizeon/exams/templates/dashboard/exams/includes/base_texts/per_questions.html`
  - `fiscallizeon/exams/templates/dashboard/exams/includes/base_texts/shared_below.html`
  - `fiscallizeon/exams/templates/dashboard/exams/includes/base_texts/subjects_top.html`
  - `fiscallizeon/exams/templates/dashboard/exams/includes/base_texts/exam_top_bottom.html`
  - `fiscallizeon/exams/templates/dashboard/exams/includes/base_texts/text_relation.html`
- **⬇️ Fluxo Subsequente (Downstream):**
  - 🔗 [exam_homework_print.md](./exam_homework_print.md) — Impressão da lista pelo aluno após finalizar.

## 6. Armadilhas Conhecidas e Cruzamentos Obrigatórios de QA (Histórico de Reviews)

1. **[Review CU-86akta6jf — Esquecimento das Telas do Aluno ao Alterar `base_text_location`]:**
   - `student-homework.html` e `student-new-exam.html` ficam no app `applications`, mas incluem diretamente os partials de `exams/templates/dashboard/exams/includes/base_texts/` e o script `base_texts-functions.js`.
   - Qualquer nova opção de `base_text_location` ou mudança em `base_texts-functions.js` **DEVE** ser aplicada também em `student-homework.html` e `student-new-exam.html`.
2. **[Review CU-86akta6jf — `Uncaught TypeError` no Console em `gerateBaseTextNumbers()`]:**
   - No `mounted()`, ambos os templates executam `this.gerateBaseTextNumbers()`, que busca `document.querySelector('[data-baseText=baseText_${baseText.id}]')`.
   - O QA **DEVE abrir o Console do DevTools (`F12`)** ao carregar `/realizar-atividade` e validar que há **zero** `Uncaught TypeError: Cannot read properties of null (reading 'innerText')`.
3. **[Armadilha de Login Local de Aluno — Redirect para `localhost:3000`]:**
   - Ao fazer login em `http://localhost:8000/conta/entrar/` com uma conta de aluno (`user_type='student'`), o Django autentica a sessão com sucesso (HTTP 302), mas redireciona o navegador para `http://localhost:3000` (SPA do aluno).
   - Se o SPA na porta 3000 não estiver rodando localmente, basta colar diretamente `http://localhost:8000/aplicacoes/<app_student_pk>/realizar-atividade` na mesma aba após o login que a sessão já estará autenticada.
4. **[Armadilha de Cache de Template (`django.template.loaders.cached.Loader`)]:**
   - O `fiscallizeon/settings.py` utiliza `cached.Loader`. Quando apenas arquivos `.html` ou `.js` incluídos via `{% include %}` são editados, o `runserver` não reinicia sozinho e continua servindo o template antigo em memória RAM.
   - Sempre disparar reload do worker (ex.: `touch fiscallizeon/applications/views.py` ou reiniciar o `runserver`) antes de validar alterações de template no navegador.
5. **[Armadilha Visual com `exam.random_questions = True`]:**
   - Quando o caderno tem `random_questions = True`, `student-data-exam.js` embaralha `subject.list|shuffle:exam.random_questions`. Se apenas algumas questões do caderno possuem texto-base, a 1ª questão vinculada pode não estar no topo da página — rolar até a primeira questão numerada vinculada ao texto-base (ou verificar pelo painel lateral direito).

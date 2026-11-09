# Mapeamento de Tela: exam_homework_print.html

> Template: `fiscallizeon/exams/templates/dashboard/exams/exam_homework_print.html`
> View: `ExamHomeworkPrintView` (`fiscallizeon/exams/views/exams.py:3693`)

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Imprimir lista de exercício do aluno | `/provas/<uuid:pk>/<uuid:application_student>/imprimir/lista-exercicio` | `exams:exam_homework_print` (`ExamHomeworkPrintView`) |

- **Origem:** lista de aplicações do aluno/responsável → botão **“Imprimir Caderno”**.
- **Permissão:** `required_permissions = [STUDENT]`; `ApplicationStudent.student.user` deve ser o usuário logado.
- **Pré-condições:** `Application.category == Application.HOMEWORK`; `today >= application.date_time_start_tz`; `application_student.end_time` preenchido.
- **Mensagens de bloqueio:** “Você não pode imprimir esta lista de exercícios.”, “Você não finalizou esta lista de exercícios.”, “Você não tem permissão para imprimir esta lista de exercícios.”

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from datetime import timedelta

from django.utils import timezone
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam
from fiscallizeon.students.models import Student

client_obj = mixer.blend(Client, has_exam_elaboration=True)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
student_user = mixer.blend(User, user_type='student', two_factor_enabled=False)
student = mixer.blend(Student, user=student_user, client=client_obj)
school_class = mixer.blend(SchoolClass, coordination=coordination)
exam = mixer.blend(
    Exam,
    coordinations=[coordination],
    category=Exam.HOMEWORK,
    base_text_location=Exam.SHARED_BELOW,
)
application = mixer.blend(
    Application,
    exam=exam,
    category=Application.HOMEWORK,
    date=timezone.localdate(),
    start='08:00',
    end='12:00',
)
application_student = mixer.blend(
    ApplicationStudent,
    application=application,
    student=student,
    end_time=timezone.now() - timedelta(minutes=5),
)
```

- Para o cenário de texto compartilhado, vincular o mesmo `BaseText` às questões 4 e 5 e criar `ExamQuestion` com `order` correspondente.

## 3. Seletores DOM e Ações

### Lista de aplicações do aluno
- **Botão de impressão:** `a:has-text("Imprimir Caderno")` / `button:has-text("Imprimir Caderno")` [verificar rótulo exato na tela de origem]
- **Ação:** abre a URL acima em nova aba.

### Página de impressão (`exam_homework_print.html`)
- **Bloco de texto compartilhado:** `#baseText_<base_text_id>` e `[data-baseText="baseText_<base_text_id>"]`
- **Rodapé de questões:** `.text-base-questions-footer`
- **Questão:** `.question#question-<question_id>`
- **Enunciado:** `.question-enunciation`
- **Aviso residual:** texto **“Esta questão possui”** (`text_relation.html`) — deve estar ausente na opção 4.
- **Indicação esperada:** `“Texto para a questão X”` ou `“Texto para as questões X e Y”`.

## 4. API Interception & Fixtures (rotas e entidades críticas)

- `GET /provas/<uuid>/<application_student>/imprimir/lista-exercicio` → HTML de impressão.
- **Entidades para render:** `Exam`, `Application`, `ApplicationStudent`, `Student`, `Question`, `ExamQuestion`, `BaseText`.
- **Condição de template:** o bloco compartilhado aparece quando `object.get_base_text_location_display` ou `object.application.exam.get_base_text_location_display` é `'Texto-base compartilhado com questões embaixo'`.
- **Observação:** esta tela usa `exam_homework_print.html`, não `exam_print.html`; a validação da opção 4 precisa ser feita separadamente do fluxo “Imprimir caderno”.

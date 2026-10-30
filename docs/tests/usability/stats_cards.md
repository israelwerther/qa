# Mapeamento de Usabilidade: StatsCards (Painel do Aluno)

Mapeamento técnico incremental da tela do painel do aluno, com foco nos cards superiores de KPIs de desempenho (`StatsCards`), para suporte à automação de testes com Playwright.

---

## 1. URLs e Navegação

| Origem | Destino | URL SPA Aluno (`lize-student`) | Endpoint Backend (`lizeedu`) |
|---|---|---|---|
| Login do Aluno (`/login`) | Painel do Aluno | `http://localhost:5173/painel/` ou `/painel/` | `GET /api/v3/student/performance_summary/?type=all` |
| Sidebar Aluno ➔ Item "**Visão Geral**" | Painel do Aluno | `/painel/` | `GET /api/v3/student/performance_summary/?type=all` |

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões Necessárias
* O usuário deve ter vínculo de aluno ativo: `user.can_access_app = True` e existir registro de `Student(user=user, client=client)`.
* O `Client` associado deve permitir acesso ao aplicativo: `client.can_access_app = True`.

### Fixture Base via Mixer (Python)

```python
from datetime import timedelta
from django.utils import timezone
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.answers.models import OptionAnswer
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.clients.models import Client
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.students.models import Student

client = mixer.blend(Client, can_access_app=True, type_client=1)
user = mixer.blend(User, can_access_app=True, must_change_password=False)
student = mixer.blend(Student, user=user, client=client)

def criar_avaliacao_finalizada(student, data_aplicacao, peso=10, acertou=True):
    exam = mixer.blend(Exam, is_abstract=True)
    question = mixer.blend(Question, category=Question.CHOICE)
    mixer.blend(ExamQuestion, exam=exam, question=question, weight=peso)
    option = mixer.blend(QuestionOption, question=question, is_correct=acertou)

    app = mixer.blend(
        Application,
        exam=exam,
        category=Application.MONITORIN_EXAM,
        date=data_aplicacao,
        release_result_at_end=True,
        student_stats_permission_date=timezone.now() - timedelta(days=1),
    )
    app_student = mixer.blend(
        ApplicationStudent,
        application=app,
        student=student,
        start_time=timezone.now(),
        end_time=timezone.now(),
    )
    answer = OptionAnswer.objects.create(
        question_option=option,
        student_application=app_student,
        status=OptionAnswer.ACTIVE,
    )
    return app_student
```

---

## 3. Seletores DOM e Ações

Componente React: `src/components/dashboard/stats-cards.tsx`  
Subcomponentes: `src/components/dashboard/kpi-info.tsx`, `src/components/dashboard/kpi-trend.tsx`

### Desktop (`lg:flex`)

| Elemento | Seletor Estável / Recomendado | Tipo | Finalidade / Estado |
|---|---|---|---|
| Card "Questões" | `div.hidden.lg\\:flex > div:has-text("Questões")` | Container | Card de total de questões |
| Card "Desempenho" | `div.hidden.lg\\:flex > div:has-text("Desempenho")` | Container | Card de taxa de acerto (%) |
| Card "Média das notas" | `div.hidden.lg\\:flex > div:has-text("Média das notas")` | Container | Card de média anual de notas |
| Botão Tooltip Questões | `button[aria-label="Como é calculado: Questões"]` | Botão ⓘ | Abre tooltip explicativo |
| Botão Tooltip Desempenho | `button[aria-label="Como é calculado: Desempenho"]` | Botão ⓘ | Abre tooltip explicativo |
| Botão Tooltip Média das notas | `button[aria-label="Como é calculado: Média das notas"]` | Botão ⓘ | Abre tooltip explicativo |
| Conteúdo do Tooltip | `[role="tooltip"]` ou `div[data-radix-popper-content-wrapper]` | Popover | Exibe a descrição do cálculo |
| Indicador de Tendência (Alta) | `span[data-trend="up"]` | Ícone | Seta verde para cima (`text-green-600`) |
| Indicador de Tendência (Queda) | `span[data-trend="down"]` | Ícone | Seta vermelha para baixo (`text-red-600`) |
| Texto Acessível da Seta | `span[data-trend] span.sr-only` | Texto Oculto | `"Em alta em relação às 5 avaliações anteriores"` ou `"Em queda em relação às 5 avaliações anteriores"` |

### Mobile (`lg:hidden`)

| Elemento | Seletor Estável / Recomendado | Tipo | Finalidade / Estado |
|---|---|---|---|
| Grid Mobile | `div.grid.grid-cols-3.lg\\:hidden` | Container | Layout condensado em 3 colunas |
| Coluna Questões | `div.grid.grid-cols-3.lg\\:hidden > div:nth-child(1)` | Coluna | Coluna 1 |
| Coluna Desempenho | `div.grid.grid-cols-3.lg\\:hidden > div:nth-child(2)` | Coluna | Coluna 2 |
| Coluna Média das notas | `div.grid.grid-cols-3.lg\\:hidden > div:nth-child(3)` | Coluna | Coluna 3 |
| Tooltip Trigger Mobile | `div.grid.grid-cols-3 button[aria-label^="Como é calculado:"]` | Botão ⓘ | Abre/fecha ao toque |

---

## 4. Rotas de API e Entidades Complexas

### Endpoints Críticos

* `GET /api/v3/student/performance_summary/?type=all`
  * Retorna array JSON camelCase com estatísticas cacheadas por 20 minutos (`student_{id}_performance_summary_v2_all`).
  * Formato do payload esperado:
    ```json
    [
      {
        "type": "question",
        "total": 42
      },
      {
        "type": "performance",
        "performance": 85.5,
        "trend": {
          "direction": "up",
          "recent": 90.0,
          "previous": 78.5
        }
      },
      {
        "type": "grade",
        "gradeAvg": 8.4,
        "trend": {
          "direction": "down",
          "recent": 7.5,
          "previous": 8.8
        }
      }
    ]
    ```


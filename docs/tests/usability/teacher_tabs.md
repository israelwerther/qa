# Mapeamento de Tela: teacher_tabs.html (Componente de Abas do Professor)

> **Nota de Acervo:** Este arquivo é alimentado de forma incremental e colaborativa. Sempre que uma nova funcionalidade for testada nesta tela/componente, o mapeamento de IDs e seletores estáveis deve ser atualizado aqui. O objetivo é criar um repositório centralizado para facilitar a automação via Playwright, sem depender de classes CSS frágeis.

## 1. URLs e Navegação
- **URL Base:** `/dashboard/` ou `/` (redirecionado via `redirect_dashboard` quando `user.user_type == settings.TEACHER`)
- **View Django:** `fiscallizeon.core.views.DashboardTeacherView`
- **Template da Página:** `dashboard/teacher_v3.html`
- **Template do Componente Alterado:** `core/components/teacher_tabs/teacher_tabs.html`

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
> **Acesso ao Módulo (Permissões):** O usuário deve estar autenticado e ter `user.user_type == TEACHER`.
> - Para exibir a aba **Revisar**: `user.inspector.is_discipline_coordinator = True`
> - Para exibir a aba **Corrigir**: `user.client_has_followup_dashboard = True` (ou `client_has_followup_dashboard = True` na flag do cliente)

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.inspectors.models import Inspector
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination

# Setup base para visualização do Painel do Professor
client = mixer.blend(Client, has_followup_dashboard=True)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)

user = mixer.blend(User, client=client, user_type=User.TEACHER)
teacher = mixer.blend(
    Inspector,
    user=user,
    email=user.email,
    inspector_type=Inspector.TEACHER,
    is_discipline_coordinator=True,
)
teacher.coordinations.add(coordination)
```

## 3. Seletores DOM e Ações

### 3.1. Abas de Navegação (TeacherTabs Component)
- **Container Alpine:** `div[x-data="teacherTabsAlpine()"]` / `div[x-data*="tabs"]`
- **Aba Elaborar (Default):**
  - **Gatilho:** `button#opened` ou `[id="opened"]`
  - **Rótulo:** "Elaborar"
  - **Badge de Contagem:** `span` dentro de `#opened`
- **Aba Revisar:**
  - **Gatilho:** `div[@click="active = 'review'"]` (quando `user.inspector.is_discipline_coordinator`)
  - **Rótulo:** "Revisar"
  - **Badge de Contagem:** `span[x-text="count_exams_to_review"]`
- **Aba Corrigir:**
  - **Gatilho:** `div[@click="active = 'corrections'"]` (quando `user.client_has_followup_dashboard`)
  - **Rótulo:** "Corrigir"
  - **Badge de Contagem:** `span[x-text="count_cards_corrections"]`

### 3.2. Estados Vazios (Empty State Component)
- **Painel Elaborar (Sem solicitações):**
  - `div[x-show="openedExamsLoaded && count_opened_exams <= 0"]` / `{% component "empty_state" %}`
  - Título: `"Não há questões para elaboração"`
  - Descrição: `"Parabéns! Você não possui questões para serem elaboradas."`
- **Painel Corrigir (Sem questões a corrigir):**
  - `div[x-show="cardsCorrectionsLoaded && count_cards_corrections <= 0"]`
  - Título: `"Não há questões para correção"`
  - Descrição: `"Parabéns! Você não possui questões para serem corrigidas."`
- **Painel Revisar (Sem questões a revisar):**
  - `div[x-show="examsToReviewLoaded && count_exams_to_review <= 0"]`
  - Título: `"Não há questões para revisão"`
  - Descrição: `"Parabéns! Você não possui questões para serem revisadas."`

### 3.3. Cards e Ações
- **Cards de Tarefa (Elaborar):** `task_card` component
- **Botão Continuar no Card:** `a button:has-text("Continuar")`
- **Botão Ver Todas as Elaborações:** `button:has-text("Todas as solicitações")` -> redireciona para `/exams/examteachersubject/?v=2`
- **Botão Ver Todas as Correções:** `button:has-text("Todas as correções")` -> redireciona para `/exams/pendences/`
- **Botão Ver Todas as Revisões:** `button:has-text("Todas as revisões")` -> redireciona para `/exams/review/?v=2`

## 4. Rota de APIs e Interceptações
- **Carregar Provas para Revisão:** `/exams/api/exams-to-review/` (`exams:api-exam-get-exams-to-review`)
- **Carregar Dados do Serviço:** `/dashboards/api/service-data/<client_id>/` (`dashboards:get-data-from-service`)

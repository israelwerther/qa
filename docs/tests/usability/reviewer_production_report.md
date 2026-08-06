# Mapeamento de Usabilidade e Elementos DOM — Produção de Revisores

> **Template associado:** `fiscallizeon/dashboards/templates/dashboards/details/reviewer_production_report.html`
> **Componente da Tabela:** `fiscallizeon/dashboards/components/reviewer_production_table/reviewer_production_table.html`

---

## 1. URLs e Navegação

| Tela / Recurso | URL exata | Método | Permissões / Gate |
|---|---|---|---|
| Hub de Relatórios | `/dashboards/relatorios/` | GET | `LoginRequired2FAMixin`, `CheckHasPermission(COORDINATION)`, `client_has_reports=True` |
| Relatório de Produção de Revisores | `/dashboards/relatorios/producao-revisores/` | GET | `LoginRequired2FAMixin`, `CheckHasPermission(COORDINATION)`, `client_has_reports=True` |
| API KPIs | `/dashboards/api/reviewer-production/kpis/` | GET | `SessionAuthentication`, `CheckHasPermissionAPI(COORDINATION)`, `client_has_reports=True` |
| API Listagem de Revisores | `/dashboards/api/reviewer-production/reviewers/` | GET | `SessionAuthentication`, `CheckHasPermissionAPI(COORDINATION)`, `client_has_reports=True` |
| API Drill-Down (Cadernos do Revisor) | `/dashboards/api/reviewer-production/reviewers/<reviewer_id>/exams/` | GET | `SessionAuthentication`, `CheckHasPermissionAPI(COORDINATION)`, `client_has_reports=True` |
| API Drill-Down (Questões do Caderno) | `/dashboards/api/reviewer-production/reviewers/<reviewer_id>/exams/<exam_id>/questions/` | GET | `SessionAuthentication`, `CheckHasPermissionAPI(COORDINATION)`, `client_has_reports=True` |
| API Export CSV Global (Async) | `/dashboards/api/reviewer-production/export/` | POST | `SessionAuthentication`, `CheckHasPermissionAPI(COORDINATION)`, `client_has_reports=True` |
| API Export CSV Revisor (Async) | `/dashboards/api/reviewer-production/reviewers/<reviewer_id>/export/` | POST | `SessionAuthentication`, `CheckHasPermissionAPI(COORDINATION)`, `client_has_reports=True` |
| API Export Status (Polling) | `/dashboards/api/reviewer-production/export-status/<export_id>/` | GET | `SessionAuthentication`, `CheckHasPermissionAPI(COORDINATION)`, `client_has_reports=True` |
| API Export Cancel | `/dashboards/api/reviewer-production/export-cancel/<export_id>/` | POST | `SessionAuthentication`, `CheckHasPermissionAPI(COORDINATION)`, `client_has_reports=True` |

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões Necessárias
- O usuário deve possuir relacionamento `CoordinationMember` vinculado a uma `SchoolCoordination` de uma `Unity` pertencente a um `Client` com `has_reports=True`.
- Autenticação de sessão válida com 2FA validado (`user.two_factor_is_valid_since_last_login() == True`).

### Setup de Dados em Python (Mixer)
```python
from datetime import datetime, timezone
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember
from fiscallizeon.exams.models import Exam, ExamQuestion, StatusQuestion
from fiscallizeon.questions.models import Question

# 1. Instanciar Cliente com relatórios habilitados
client = mixer.blend(Client, has_reports=True)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)

# 2. Usuário da Coordenação (Tester/Bot)
coordination_user = mixer.blend(User, is_staff=True)
mixer.blend(CoordinationMember, user=coordination_user, coordination=coordination)

# 3. Prova e Revisor
exam = mixer.blend(Exam, name="Simulado ENEM 2026 - Caderno 1")
exam.coordinations.add(coordination)
reviewer = mixer.blend(User, name="Carlos Eduardo Silva")

# 4. Questão e Status de Revisão
question = mixer.blend(Question)
exam_question = mixer.blend(ExamQuestion, exam=exam, question=question, order=1)
status_q = mixer.blend(
    StatusQuestion,
    exam_question=exam_question,
    user=reviewer,
    status=StatusQuestion.APPROVED,
    created_at=datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)
)
```

---

## 3. Seletores DOM e Ações

### 3.1 Topbar & Exportação Global
- **Botão Exportar CSV (Global):** `button:has-text("Exportar CSV")` / `@click="$store.reviewerProductionExport.startGlobalExport()"`
- **Spinner de carregamento no botão:** `svg.tw-animate-spin`

### 3.2 Filtros
- **Input Buscar Revisor:** `input#reviewer-search` (atributo `id="reviewer-search"`, binding `x-model="filters.reviewerName"`)
- **Filtro de Período:** Componente `date_filter` integrado ao `Alpine.store('dashboard').startDate` e `endDate`
- **Dropdown Status:** `select[x-model="filters.status"]`
- **Botão Limpar Filtros:** `button:has-text("Limpar filtros")` (desabilitado quando `!hasActiveFilters`)

### 3.3 KPIs e Barra de Distribuição
- **Container KPIs:** `.tw-grid.tw-bg-gray-200`
  - **Questões revisadas:** `[metric="questions_reviewed"]`
  - **Revisores em dia:** `[metric="on_track"]`
  - **Aguardando revisão:** `[metric="pending"]`
- **Barra de Distribuição:** `div[x-data="reviewerDistribution()"]`
  - Segmento Aprovadas: `.tw-bg-green-500`
  - Segmento Reprovadas: `.tw-bg-red-500`
  - Segmento Pendente: `.tw-bg-amber-500`
  - Segmento Outros: `.tw-bg-gray-500`

### 3.4 Tabela de Revisores & Drill-Down
- **Tabela Principal:** `table.tw-min-w-full`
- **Linha do Revisor:** `tbody > tr`
  - **Chevron de Expansão do Revisor:** `button[aria-label^="Expandir cadernos de"]`
  - **Coluna Nome:** `td.tw-font-medium`
  - **Badges de Status:** `span.tw-bg-green-100`, `span.tw-bg-red-100`, `span.tw-bg-amber-100`
  - **Botão Estatísticas (Drawer):** `button[aria-label^="Ver estatísticas de"]`
  - **Botão Exportar CSV do Revisor:** `button[aria-label^="Exportar histórico de"]`
- **Linha Expandida de Cadernos (Drill-Down Nível 1):** `tr.tw-bg-gray-50\/60`
  - **Chevron de Expansão do Caderno:** `button[aria-label="Expandir questões"]` / `button[aria-expanded]`
- **Linha Expandida de Questões (Drill-Down Nível 2):** `div.tw-pl-10`
  - Rótulo da Questão: `span:has-text("Q1")`
  - Badge Status Questão: `span.tw-rounded-full` (verde/vermelho/âmbar)

### 3.5 Drawer Lateral de Estatísticas (Shell)
- **Painel Drawer:** `aside[role="dialog"][aria-modal="true"]`
- **Botão Fechar Drawer:** `button[aria-label="Fechar"]`

---

## 4. API Routes e Intercepts Críticos

- `GET /dashboards/api/reviewer-production/kpis/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&reviewer_name=X&status=Y`
- `GET /dashboards/api/reviewer-production/reviewers/?page=1&page_size=10&reviewer_name=X`
- `GET /dashboards/api/reviewer-production/reviewers/<uuid>/exams/`
- `GET /dashboards/api/reviewer-production/reviewers/<uuid>/exams/<uuid>/questions/`
- `POST /dashboards/api/reviewer-production/export/`
- `POST /dashboards/api/reviewer-production/reviewers/<uuid>/export/`

---

## 5. Exemplo de Snippet de Automação Playwright (Python)

```python
import pytest
from playwright.sync_api import Page, expect
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember
from fiscallizeon.exams.models import Exam, ExamQuestion, StatusQuestion
from fiscallizeon.questions.models import Question

@pytest.mark.django_db
def test_reviewer_production_report_flow(page: Page, live_server):
    # Setup de dados no banco via mixer
    client_obj = mixer.blend(Client, has_reports=True)
    unity = mixer.blend(Unity, client=client_obj)
    coordination = mixer.blend(SchoolCoordination, unity=unity)

    user = mixer.blend('accounts.User', is_staff=True)
    mixer.blend(CoordinationMember, user=user, coordination=coordination)
    user.set_password("pass123")
    user.save()

    reviewer = mixer.blend('accounts.User', name="Mariana Souza")
    exam = mixer.blend(Exam, name="Caderno de Biologia 1º Ano")
    exam.coordinations.add(coordination)

    question = mixer.blend(Question)
    eq = mixer.blend(ExamQuestion, exam=exam, question=question, order=1)
    mixer.blend(StatusQuestion, exam_question=eq, user=reviewer, status=StatusQuestion.APPROVED)

    # Autenticação e navegação
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill('input[name="username"]', user.email)
    page.fill('input[name="password"]', "pass123")
    page.click('button[type="submit"]')

    # Acesso direto à página de relatório
    page.goto(f"{live_server.url}/dashboards/relatorios/producao-revisores/")

    # Validação visual do título
    expect(page.locator("h1")).to_contain_text("Produção de Revisores")

    # Filtro por nome do revisor
    search_input = page.locator("#reviewer-search")
    search_input.fill("Mariana")

    # Expandir drill-down de cadernos
    expand_reviewer_btn = page.locator('button[aria-label^="Expandir cadernos de Mariana Souza"]')
    expand_reviewer_btn.click()

    # Confirmar visibilidade do caderno no drill-down
    expect(page.locator('text="Caderno de Biologia 1º Ano"')).to_be_visible()
```

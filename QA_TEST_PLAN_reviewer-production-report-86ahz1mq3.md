## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-08-06 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Dashboards / Relatórios (Produção de Revisores) |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5 estrelas) |

---

## 1. Summary of Changes (Resumo das Alterações)

Na branch `reviewer-production-report-86ahz1mq3`, foi implementado o novo relatório de **Produção de Revisores** para controle operacional e financeiro da revisão externa de questões:

* **Backend & Serviço de Agregação (`reviewer_production.py`):**
  * Criado o serviço de agregação que filtra registros de `StatusQuestion` escopados pelo cliente do usuário (`request.user.client`) através do relacionamento `exam_question__exam__coordinations__unity__client`.
  * Filtro temporal baseado exclusivamente em `StatusQuestion.created_at` (momento da realização da revisão).
  * Agregações para KPIs (questões revisadas, revisores em dia, questões pendentes, distribuição de status).
  * Agregação e paginação server-side de revisores, drill-down lazy por cadernos e por questões.
  * Gerador de streaming CSV com suporte a BOM UTF-8 para Excel.

* **Endpoints REST API (`dashboards/views.py` e `dashboards/urls.py`):**
  * `/dashboards/api/reviewer-production/kpis/`: Retorna contadores dos 3 KPIs + distribuição de status.
  * `/dashboards/api/reviewer-production/reviewers/`: Listagem paginada de revisores com contagens por status.
  * `/dashboards/api/reviewer-production/reviewers/<uuid>/exams/`: Listagem de cadernos associados ao revisor (drill-down nível 1).
  * `/dashboards/api/reviewer-production/reviewers/<uuid>/exams/<uuid>/questions/`: Listagem de questões do caderno com status (drill-down nível 2).
  * `/dashboards/api/reviewer-production/export/` e `/reviewers/<uuid>/export/`: Disparo assíncrono via Celery task de geração do relatório em CSV (global ou por revisor).
  * `/dashboards/api/reviewer-production/export-status/<export_id>/` e `/export-cancel/<export_id>/`: Status e cancelamento de tarefas de exportação assíncronas.
  * Garantido o gate `client_has_reports=True` e permissão `COORDINATION` em todas as rotas e views.

* **Frontend & Componentes (`django-components` e Alpine.js):**
  * Card **"Produção de Revisores"** adicionado ao grid do Hub de Relatórios (`report_card_grid.py`).
  * Nova página `/dashboards/relatorios/producao-revisores/` estendendo `redesign/base_component.html`.
  * Utilização do componente `report_header` na topbar e `report_kpi` nos 3 KPIs principais.
  * Barra gráfica de distribuição proporcional de status com tooltips ao hover.
  * Filtro de período por intervalo de datas usando `date_filter` sincronizado com `Alpine.store('dashboard')`.
  * Tabela de revisores expansível com chevron (drill-down em 2 níveis), badges de status e controle de paginação.
  * Drawer lateral (shell) para estatísticas do revisor.
  * Integração com exportação assíncrona de CSV com estado reativo no botão de exportar.

* **Suíte de Testes:**
  * Testes unitários do serviço em `fiscallizeon/dashboards/tests/services/test_reviewer_production.py`.
  * Testes de integração de API e visualização em `fiscallizeon/dashboards/tests/test_reviewer_production_api.py`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- **IN SCOPE:**
  - Exibição e comportamento interativo do card "Produção de Revisores" no Hub de Relatórios.
  - Filtro por intervalo de datas baseado na data da revisão (`StatusQuestion.created_at`).
  - Filtros por nome do revisor e status da revisão.
  - KPIs quantitativos de progresso e revisores em dia.
  - Tabela paginada com drill-down lazy de cadernos e questões.
  - Disparo e acompanhamento do download de relatórios CSV via Celery.
  - Isolamento multi-tenant (garantir que um cliente nunca visualize revisões de outro cliente).
  - Controle de acesso (bloqueio para perfil Professor ou contas sem módulo de relatórios ativo).

- **OUT OF SCOPE:**
  - Preenchimento do conteúdo interno do drawer de Estatísticas (o drawer abre como shell/placeholder para futuras métricas).
  - Alterações nos fluxos operacionais de revisão de questões ou na persistência de `StatusQuestion`.
  - Integrações financeiras, notificações por e-mail ou cálculo de valores a pagar.
  - Acesso à funcionalidade por usuários do perfil Professor.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Hub de Relatórios | Relatórios | `/dashboards/relatorios/` | `dashboards:reports` |
| Relatório de Produção de Revisores | Produção de Revisores | `/dashboards/relatorios/producao-revisores/` | `dashboards:reviewer-production-report` |
| Endpoints REST API | N/A (Consumo via AJAX) | `/dashboards/api/reviewer-production/...` | `dashboards:reviewer-production-*-api` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### 4.1 Execução da Suíte de Testes Locais
```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/dashboards/tests/services/test_reviewer_production.py fiscallizeon/dashboards/tests/test_reviewer_production_api.py
```

### 4.2 Definção de Personas para Validação Manual / Automação
- **Persona Coordenador Autorizado:** Usuário pertencente ao grupo `COORDINATION` associado a um `Client` com `has_reports=True`. Ex: `coord_revisao@escola.com.br`.
- **Persona Coordenador Sem Módulo:** Usuário `COORDINATION` cujo `Client` possui `has_reports=False`.
- **Persona Professor:** Usuário do perfil `TEACHER` (acesso restrito / 403 / redirecionamento).

### 4.3 Setup de Dados via Mixer (Python Snippet)
```python
from datetime import datetime, timezone
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember
from fiscallizeon.exams.models import Exam, ExamQuestion, StatusQuestion
from fiscallizeon.questions.models import Question

# 1. Setup da Infraestrutura Tenant
client = mixer.blend(Client, has_reports=True)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)

# 2. Setup do Coordenador (Tester)
user = mixer.blend(User, is_staff=True)
mixer.blend(CoordinationMember, user=user, coordination=coordination)

# 3. Setup de Dados de Revisão
reviewer_1 = mixer.blend(User, name="Ana Clara Rocha")
reviewer_2 = mixer.blend(User, name="Bruno Castro")

exam_1 = mixer.blend(Exam, name="Avaliação Diagnóstica - 9º Ano")
exam_1.coordinations.add(coordination)

# Cadastrar 3 questões com status distintos
q1 = mixer.blend(Question)
eq1 = mixer.blend(ExamQuestion, exam=exam_1, question=q1, order=1)
mixer.blend(StatusQuestion, exam_question=eq1, user=reviewer_1, status=StatusQuestion.APPROVED, created_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc))

q2 = mixer.blend(Question)
eq2 = mixer.blend(ExamQuestion, exam=exam_1, question=q2, order=2)
mixer.blend(StatusQuestion, exam_question=eq2, user=reviewer_1, status=StatusQuestion.REPROVED, created_at=datetime(2026, 8, 2, 11, 0, tzinfo=timezone.utc))

q3 = mixer.blend(Question)
eq3 = mixer.blend(ExamQuestion, exam=exam_1, question=q3, order=3)
mixer.blend(StatusQuestion, exam_question=eq3, user=reviewer_2, status=StatusQuestion.OPENED, created_at=datetime(2026, 8, 3, 14, 0, tzinfo=timezone.utc))
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Acesso e Gate de Permissão [Automatizável ✅]

#### Cenário 1 — Acesso ao card no Hub de Relatórios como Coordenador
- Persona: Coordenador Autorizado (`client_has_reports=True`).
- [ ] Navegar até a URL `/dashboards/relatorios/`.
- [ ] Confirmar que o card "Produção de Revisores" está visível na seção de Gestão.
- [ ] Clicar no card "Produção de Revisores" e verificar o direcionamento para a página `/dashboards/relatorios/producao-revisores/`.

#### Cenário 2 — Restrição de acesso para usuários não autorizados
- Persona: Professor ou Coordenador sem módulo de relatórios (`client_has_reports=False`).
- [ ] Fazer login com usuário do perfil Professor e tentar acessar `/dashboards/relatorios/producao-revisores/`.
- [ ] Confirmar que o sistema redireciona o usuário para o dashboard inicial sem exibir o relatório.
- [ ] Fazer chamada direta à API `/dashboards/api/reviewer-production/kpis/` sem estar logado como coordenação com relatório.
- [ ] Confirmar que a API responde com status HTTP 403 Forbidden.

---

### 5.2 KPIs e Distribuição por Status [Automatizável ✅]

#### Cenário 3 — Validação quantitativa dos KPIs
- Persona: Coordenador Autorizado.
- [ ] Acessar a tela de Produção de Revisores `/dashboards/relatorios/producao-revisores/`.
- [ ] Verificar o KPI "Questões revisadas" e validar a contagem no formato `X/Y` (onde X é o total de aprovadas + reprovadas e Y é o total de questões no escopo).
- [ ] Verificar o KPI "Revisores em dia" e validar se indica a proporção correta de revisores sem pendências.
- [ ] Verificar o KPI "Aguardando revisão" e validar se lista as questões pendentes.

#### Cenário 4 — Visualização da Barra de Distribuição
- Persona: Coordenador Autorizado.
- [ ] Observar a barra empilhada "Distribuição por status" abaixo dos KPIs.
- [ ] Passar o ponteiro do mouse sobre o segmento verde (Aprovadas) e confirmar a exibição do tooltip informando o quantitativo.
- [ ] Passar o mouse sobre o segmento vermelho (Reprovadas) e sobre o segmento âmbar (Pendente) e validar os tooltips.

---

### 5.3 Filtros de Busca e Período [Automatizável ✅]

#### Cenário 5 — Filtragem por nome do revisor
- Persona: Coordenador Autorizado.
- [ ] No campo "Buscar revisor", digitar parte do nome de um revisor cadastrado (ex: "Ana").
- [ ] Aguardar a atualização da tabela e confirmar que apenas o revisor correspondente é exibido.
- [ ] Digitar um nome inexistente e verificar se a tabela exibe a mensagem "Nenhum revisor encontrado para os filtros selecionados."

#### Cenário 6 — Filtragem por período (Data da Revisão)
- Persona: Coordenador Autorizado.
- [ ] Selecionar um intervalo de datas no filtro de Período onde sabidamente ocorreram revisões.
- [ ] Confirmar que a tabela e os KPIs recarregam refletindo apenas as revisões realizadas dentro do intervalo de datas.
- [ ] Alterar o intervalo para um período sem revisões registradas e verificar o esvaziamento das contagens nos KPIs.

#### Cenário 7 — Limpeza de Filtros
- Persona: Coordenador Autorizado.
- [ ] Aplicar um filtro de nome e um filtro de status.
- [ ] Confirmar que o botão "Limpar filtros" fica ativo.
- [ ] Clicar em "Limpar filtros" e verificar se todos os filtros são resetados para o estado padrão ("Todo o período", busca vazia, todos os status) e a tabela é restaurada.

---

### 5.4 Tabela de Revisores e Drill-Down Lazy [Automatizável ✅]

#### Cenário 8 — Expansão de cadernos por revisor (Nível 1)
- Persona: Coordenador Autorizado.
- [ ] Localizar uma linha de revisor na tabela.
- [ ] Clicar exclusivamente no botão chevron posicionado na primeira coluna da linha do revisor.
- [ ] Verificar se uma sub-linha é expandida logo abaixo exibindo a lista de cadernos avaliados por aquele revisor.
- [ ] Clicar novamente no chevron do mesmo revisor e confirmar o recolhimento das sub-linhas.

#### Cenário 9 — Drill-down de questões por caderno (Nível 2)
- Persona: Coordenador Autorizado.
- [ ] Com a lista de cadernos expandida, clicar no chevron ao lado do nome de um caderno.
- [ ] Verificar a exibição das questões associadas àquele caderno, identificadas com o rótulo (ex: Q1, Q2) e badges coloridos indicando a situação de cada questão.

---

### 5.5 Ações por Revisor e Exportação CSV [Automatizável ✅]

#### Cenário 10 — Abertura do Drawer de Estatísticas
- Persona: Coordenador Autorizado.
- [ ] Na coluna "Ações" da linha de um revisor, clicar no ícone de gráfico/estatísticas.
- [ ] Confirmar a abertura do painel lateral (drawer) exibindo o nome do revisor no cabeçalho e a mensagem indicativa de métricas futuras.
- [ ] Clicar no botão de fechar ou pressionar a tecla ESC para encerrar o drawer.

#### Cenário 11 — Exportação CSV Global e Individual
- Persona: Coordenador Autorizado.
- [ ] Clicar no botão "Exportar CSV" localizado no topo da página.
- [ ] Observar a mudança de estado do botão para "Gerando CSV..." com indicador de carregamento animado.
- [ ] Confirmar o download do arquivo CSV consolidado com os dados filtrados.
- [ ] Na tabela, clicar no ícone de download da linha de um revisor específico e confirmar o download do relatório CSV filtrado individualmente para aquele revisor.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **TopBar:** Verificar alinhamento do título "Produção de Revisores" e do botão "Exportar CSV".
- [ ] **Grid de KPIs:** Confirmar se os 3 KPIs estão dispostos horizontalmente com divisor suave e tipografia legível.
- [ ] **Barra Proporcional:** Confirmar arredondamento das bordas e transição suave do tooltip ao passar o mouse.
- [ ] **Tabela & Indentação:** Garantir que o nível 1 do drill-down (cadernos) possua fundo sutilmente destacado (`bg-gray-50/60`) e o nível 2 (questões) apresente recuo à esquerda de 40px (`tw-pl-10`).
- [ ] **Badges de Status:** Validar paleta de cores padrão do sistema (Verde para Aprovadas, Vermelho para Reprovadas, Âmbar para Pendentes).

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Nenhum bug bloqueante ou inconformidade com a especificação OpenSpec foi identificado durante a análise de código e suíte automatizada de testes.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Estatísticas Detalhadas do Revisor (Drawer Shell):** O drawer lateral de estatísticas por revisor foi implementado como uma casca (shell) responsiva, exibindo uma mensagem informativa. O preenchimento com gráficos detalhados de SLA e produtividade temporal está mapeado como dívida técnica aceita/melhoria para ciclos futuros.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.
🔗 **[Ver Mapeamento de Tela](docs/tests/usability/reviewer_production_report.md)**

### Automation Snippet (Python / Playwright)
```python
import pytest
from playwright.sync_api import Page, expect
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember
from fiscallizeon.exams.models import Exam, ExamQuestion, StatusQuestion
from fiscallizeon.questions.models import Question

@pytest.mark.django_db
def test_reviewer_production_report_full_flow(page: Page, live_server):
    # Setup de dados
    client = mixer.blend(Client, has_reports=True)
    unity = mixer.blend(Unity, client=client)
    coordination = mixer.blend(SchoolCoordination, unity=unity)

    user = mixer.blend('accounts.User', is_staff=True)
    mixer.blend(CoordinationMember, user=user, coordination=coordination)
    user.set_password("senha123")
    user.save()

    reviewer = mixer.blend('accounts.User', name="Clara Mendes")
    exam = mixer.blend(Exam, name="Caderno de História")
    exam.coordinations.add(coordination)

    question = mixer.blend(Question)
    eq = mixer.blend(ExamQuestion, exam=exam, question=question, order=1)
    mixer.blend(StatusQuestion, exam_question=eq, user=reviewer, status=StatusQuestion.APPROVED)

    # Login
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill('input[name="username"]', user.email)
    page.fill('input[name="password"]', "senha123")
    page.click('button[type="submit"]')

    # Acessar relatório
    page.goto(f"{live_server.url}/dashboards/relatorios/producao-revisores/")
    expect(page.locator("h1")).to_contain_text("Produção de Revisores")

    # Expandir tabela
    page.click('button[aria-label^="Expandir cadernos de Clara Mendes"]')
    expect(page.locator('text="Caderno de História"')).to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principais gargalos durante os testes:** Dependência de dados populados com `StatusQuestion` vinculados a cadernos do cliente para validação completa dos KPIs e drill-down em múltiplos níveis.
- **Interação com Desenvolvimento:** A especificação OpenSpec apresentou alto nível de detalhamento (`spec.md`, `tasks.md`, `proposal.md`), minimizando ambiguidades sobre o comportamento de filtros temporais (`StatusQuestion.created_at`).
- **Pontos de Melhoria:** A criação de fixtures padronizadas com o `mixer` acelerou significativamente a verificação das regras de negócio do backend e endpoints REST API.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
1. **Verificação Automática de Arquivo de Mapeamento Existente:** Reforçar a checagem no diretório `.ai_qa_acervo/docs/tests/usability/` para que o agente sempre prefira reutilizar/incrementar o arquivo existente ao invés de duplicar seletores.
2. **Standard de Snippet de Automação:** Mandatar que todo Automation Snippet inclua o bloco completo de setup de autenticação de sessão e criação da Persona, facilitando a conversão direta para testes Playwright executáveis pelo pytest.

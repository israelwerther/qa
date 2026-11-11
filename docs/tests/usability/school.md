# Mapeamento de Tela: school.html (Dashboard de Acompanhamento / Followup)

> **Nota de Acervo:** Este arquivo é alimentado de forma incremental e colaborativa. Sempre que uma nova funcionalidade for testada nesta tela, o mapeamento de IDs e seletores estáveis deve ser atualizado aqui. O objetivo é criar um repositório centralizado para facilitar a automação via Playwright, sem depender de classes CSS frágeis.

## 1. URLs e Navegação
- **Dashboard Principal da Escola:** `/` (Home da Coordenação) ou `/dashboards/escola/`
- **Requisição de Dados Analytics (API):** `POST /dashboards/api/get-data-from-service/<client_id>/`
  - Operação Card: `get_card_followup_reviews`
  - Operação Prazos: `get_followup_reviews`
  - Operação Detalhe de Prazo e Unidades: `get_followup_reviews_deadline`
- **Navegação UI:** Login como Coordenador → Página Inicial (Dashboard) → Seção de Cards de Acompanhamento (Followup) → Card "**Revisões**" → Link "**Acompanhe**" para abrir o modal de drill-down.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- **Persona:** Usuário Coordenação (`settings.COORDINATION`) com permissão `accounts.view_dashboards` ativa ou `client.has_dashboards = True`.
- **Backend Analytics:** Serviço ClickHouse operacional ou mock da API `/dashboards/api/get-data-from-service/` retornando as estruturas de dados de `mv_followup_reviews`.
- **Permissões mínimas:**
```python
user.user_permissions.add(
    Permission.objects.get(content_type__app_label='accounts', codename='view_dashboards')
)
```

## 3. Seletores DOM e Ações

### 3.1. Card de Revisões (Visão Resumida no Dashboard)
- **Container do Card:** `div[ref="reviews"]`
- **Título do Card:** `p:has-text("Revisões")`
- **Tooltip Informativo:** `svg[data-tippy-content="Os dados analisados nesse cartão são apenas os que estão dentro no prazo."]`
- **Contador de Pendências:** `p:has-text("Há")` (ex: `Há X revisões aguardando`)
- **Gráfico / Percentual Circular:** `div[data-chart="idReviewsDataChart"] svg text` (ex: `85%`)
- **Gatilho do Drill-Down:** `a:has-text("Acompanhe")` (dispara `followupDetail('reviews')`)

### 3.2. Modal de Acompanhamento Detalhado (Drill-Down)
- **Container do Modal:** `#modal-followup` (ou modal com binding `modalFollowup`)
- **Cabeçalho:** `h3:has-text("Revisões")` e `p:has-text("revisões aguardando")`
- **Listagem de Prazos (Deadlines):**
  - Tabela/Linhas de prazos ordenadas cronologicamente (da data mais antiga para a mais recente)
  - Colunas: Data do Prazo, Cadernos (`exams_count`), Concluídas / Solicitadas (`total / soliciteds`), Desempenho (`performance %`)
  - Clique na linha do prazo para expandir unidades: `tr` ou `div` com evento `@click="selectDeadline(...)"`
- **Listagem de Unidades:**
  - Exibição de cards de Unidade com `awaiting_count`
  - Clique na Unidade para carregar detalhamento de cadernos e professores
- **Detalhamento de Professores e Cadernos na Unidade:**
  - Lista de Professores responsáveis pelas revisões
  - **Bucket Sentinela (Cadernos no Limbo):** Linha ou item com o nome do professor `"Sem professor responsável"` (`UNASSIGNED_TEACHER_ID = "00000000-0000-0000-0000-000000000001"`).
    - Agrupa todas as solicitações (ETS) que possuem disciplina e série lecionadas na escola no ano corrente, mas que não possuem nenhum coordenador elegível ou revisor designado.

## 4. API Interception & Fixtures (Rotas e Operações Críticas)
- `POST /dashboards/api/get-data-from-service/<client_id>/`
  - Payload Card:
    ```json
    {
      "who": "school",
      "who_ids": ["<client_id>"],
      "operation": "get_card_followup_reviews",
      "what": "unities",
      "what_ids": null,
      "filters": {"user_unities": ["<unity_id>"]}
    }
    ```
  - Payload Drill-down por Prazo:
    ```json
    {
      "who": "school",
      "who_ids": ["<client_id>"],
      "operation": "get_followup_reviews_deadline",
      "from_cache": false,
      "what": "unities",
      "what_ids": null,
      "filters": {
        "deadline": "YYYY-MM-DD",
        "user_unities": ["<unity_id>"],
        "followup_unity": "<unity_id>"
      }
    }
    ```


# Mapeamento de Tela — `print_applications_list.html`

> Template: `fiscallizeon/applications/templates/dashboard/applications/print_applications_list.html`

---

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|---|---|---|
| Listar aplicações para impressão | `/aplicacoes/impressao/` | `applications:print_applications_list` |
| API: Status do pedido na gráfica | `GET /aplicacoes/api/<uuid:pk>/grafica/` | `applications:printing_order_status` |

### Navegação para a tela

- **Via URL direta / menu de impressão de coordenação:** `/aplicacoes/impressao/` (`PrintApplicationsListView`).

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

- **Permissões mínimas exigidas:** `required_permissions = ['coordination']` (`PrintApplicationsListView`).
- **Para exibir selo da gráfica (`[data-test="printing-badge"]`):** Cliente vinculado a `PrintingPartnerIntegration(is_active=True)` e `PrintingOrder` existente na aplicação (`application.printingOrder.hasOrder === true`).

---

## 3. Seletores DOM e Ações

| Elemento | Seletor / binding | Observação |
|---|---|---|
| Selo de status na gráfica | `p[data-test="printing-badge"]` | Renderizado quando `application.printingOrder && application.printingOrder.hasOrder`; exibe `Gráfica: ${ ... }`, com `:title="application.printingOrder.lastError || ''"` |

---

## 4. API Interception & Fixtures (rotas e entidades críticas)

- Contexto injetado via `printing_orders.attach_status_json(context['object_list'], self.request.user)` em `PrintApplicationsListView.get_context_data`.
- Entidades: `Application`, `PrintingOrder`, `PrintingPartnerIntegration`.

---

## 5. Grafo de Dependências e Impacto Cruzado (Upstream & Downstream)

- **⬆️ Fontes Irmãs de Entrada:** Ações de envio em [application_list_new.md](./application_list_new.md) e webhooks em `POST /integracoes/api/pageflow/webhook/`.
- **⬇️ Consumidores Diretos:** Tela de conferência de impressão pela equipe/coordenação.
- **🧩 Partials e JS Compartilhados:** Estado Vue local no template (`printingOrder` populado por `{{ application.printing_status_json|default:'null'|safe }}`).
- **🚫 Telas Irmãs Descontinuadas:** Nenhuma mapeada.

---

## 6. Armadilhas Conhecidas e Cruzamentos Obrigatórios de QA (Histórico de Reviews)

- Esta tela **não** possui botão de envio para gráfica — apenas exibe o selo `[data-test="printing-badge"]` quando `hasOrder` é verdadeiro (ao contrário de `application_list_new.html`, que exibe quando `hasOrder || inProduction` e possui a ação `sendToPrinter`).


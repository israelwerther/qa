# Mapeamento de Usabilidade: notification_user_feedback_list.html

> Template: `fiscallizeon/notifications/templates/notifications/notification_user_feedback_list.html`
> Feature: Relatórios de feedbacks CSAT/NPS (task CU-86akhtqav / branch `feat/melhoria-relatorios-nps-csat-CU-86akhtqav`)
> Base da seção 8.1 dos planos de QA. Alimentado incrementalmente sempre que a tela for retestada.

## 1. URLs e Navegação

| URL | Descrição |
|---|---|
| `/notificacoes/` | Listagem de pesquisas NPS/CSAT (`notifications:notifications_list`). Acesso pelo item **Pesquisas NPS/CSAT** da sidebar (grupo Gerenciamento). |
| `/notificacoes/<uuid>/feedbacks/` | Detalhes/feedbacks de uma pesquisa (`notifications:notification_feedback_detail`). |
| `/notificacoes/<uuid>/editar/` | Edição de pesquisa (`notifications:nps_csat_update`). |

**Fluxo de navegação:**
1. Staff logado acessa sidebar → Gerenciamento → **"Pesquisas NPS/CSAT"** → `/notificacoes/`.
2. Na listagem, abre o menu de opções de uma pesquisa e clica no link de detalhes (ou acessa diretamente `/notificacoes/<uuid>/feedbacks/`).
3. Link de volta: **"← Voltar para pesquisas"** no cabeçalho da tela de feedbacks.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Persona
- Usuário **Staff** (`user.is_staff = True`). Todas as views do módulo usam `StaffRequiredMixin`; sem isso, não renderiza.
- 2FA desativado (`two_factor_enabled=False`) para não travar o fluxo local de Playwright.

### Fixture mínima via mixer
```python
from mixer.backend.django import mixer
from fiscallizeon.notifications.models import Notification

staff = mixer.blend(
    User,
    user_type='coordination',
    is_staff=True,
    is_superuser=True,
    two_factor_enabled=False,
    must_change_password=False,
)

notificacao = mixer.blend(
    Notification,
    category='survey',
    survey_type='nps',   # ou 'csat'
    trigger='create',
    model_name='study_material',
)
# page.goto(f"/notificacoes/{notificacao.pk}/feedbacks/")
```

## 3. Seletores DOM e Ações

### 3.1. Cabeçalho e navegação
| Elemento | Seletor | Descrição |
|---|---|---|
| Raiz Vue | `#notification-feedback-app` | `data-notification-id`, `data-list-url`, `data-nps-kpis-url`, `data-csat-kpis-url`, `data-edit-url`, `data-client-list-url`, `data-export-url` |
| Link de volta | `a[href*="notifications_list"]` com texto **"← Voltar para pesquisas"** | Retorna à listagem de pesquisas. |
| Link Editar pesquisa | `a[href*="editar"]` (canto superior direito) | Texto **"Editar pesquisa"**, cor `#FF8904`. |
| Título da página | `h1.tw-text-2xl.tw-font-semibold` | "Feedbacks da pesquisa". |

### 3.2. KPIs (indicadores consideram os filtros aplicados)
| Elemento | Seletor | Descrição |
|---|---|---|
| Loading | `div:v-if="loadingKpis"` | "Carregando indicadores..." |
| Card Enviados | texto "Enviados" + `kpis.totalSent` | Primeiro card do grid. |
| Card Visualizados | texto "Visualizados" + `kpis.totalViewed` | |
| Card Respondidos | texto "Respondidos" + `kpis.totalResponded` | |
| Card NPS Score / Média CSAT | texto dinâmico `notificationType === 'nps' ? 'NPS Score' : 'Média CSAT'` + `scoreLabel` | |
| Promotores (9–10) / Passivos (7–8) / Detratores (0–6) | apenas NPS: `v-if="notificationType === 'nps'"` | Três cards extras ao lado. |

### 3.3. Barra de filtros
| Elemento | Seletor | Descrição |
|---|---|---|
| Botões de Ano | `button[@click="toggleYear(...)"]` dentro de `role="group" aria-label="Filtrar respostas por ano"` | Ano mais recente selecionado por padrão (`tw-border-orange-600 tw-bg-orange-50`). |
| Busca | `#feedback-query` (`type="search"`) | Placeholder "Comentário, nome ou e-mail". |
| De / Até | `#feedback-created-from` / `#feedback-created-to` (`type="date"`) | Labels "De" e "Até". |
| Nota mín./máx. | `#feedback-rating-min` / `#feedback-rating-max` (`type="number"`) | Labels "Nota mín." / "Nota máx." (0–10 NPS, 1–5 CSAT). |
| Exportar CSV | `button[@click="exportCsv"]` | Texto **"Exportar CSV"** (ou "Exportando…" / "Copiado"). Laranja (`tw-bg-orange-600`), `brand-600`. |
| Atalhos NPS | botões **"Detratores 0–6"**, **"Passivos 7–8"**, **"Promotores 9–10"** | Apenas NPS (`v-if="notificationType === 'nps'"`), `@click="setNpsRange(...)"`. |
| Apenas com feedback | checkbox `v-model="withFeedback"` | Label **"Apenas com feedback"**. |

### 3.4. Tabela de respostas
| Elemento | Seletor | Descrição |
|---|---|---|
| Cabeçalhos ordenáveis | botões `Usuário`, `Nota`, `Visualizado`, `Respondido`, `Data` | `@click="toggleOrdering('user_name'\|'rating'\|'viewed'\|'feedback_sent'\|'created_at')"`. Coluna "Feedback" não ordena. |
| Linha da tabela | `tr v-for="item in items" :key="item.id"` | |
| Nome do usuário | `td > div.tw-font-medium.tw-text-gray-900` | |
| E-mail / Cliente | `div.tw-text-gray-500.tw-text-xs` | |
| Nota | `span.tw-font-semibold.tw-text-gray-900` | `—` quando nula. |
| Comentário | `button[@click="showFeedback(...)"]` (texto truncado) | Abre o diálogo com o texto integral. |
| Visualizado / Respondido | `span` verde ("Sim") ou cinza ("Não") | |
| Data | `td.tw-text-gray-600.tw-text-xs` | `formatDate(item.createdAt)` |
| Vazio | `td[colspan="6"]` | "Nenhuma resposta encontrada." |
| Paginação | botões **"Anterior"** / **"Próxima"**, texto `page / totalPages` | |

### 3.5. Diálogo de leitura e cópia do comentário
| Elemento | Seletor | Descrição |
|---|---|---|
| Dialog | `div[v-if="openFeedback"]` | `@click.self="closeFeedback" @keydown.esc.stop.prevent="closeFeedback"` |
| Título | `h2#feedback-dialog-title` | "Comentário de <usuário>" |
| Metadados | `p#feedback-dialog-details` | e-mail · cliente · nota · data |
| Texto integral | `textarea#feedback-full` (`readonly`, `ref="feedbackText"`) | `:value="openFeedback.feedback"` |
| Fechar (topo) | `button[@click="closeFeedback"] aria-label="Fechar comentário"` | Texto **"Fechar"** |
| Fechar (rodape) | `button[@click="closeFeedback"]` | Texto **"Fechar"** |
| Copiar texto | `button[@click="copyFeedback"]` | Texto **"Copiar texto"** / "Copiando…" / "Copiado" |

## 4. API Interception & Fixtures (rotas e entidades críticas)

| Endpoint | Método | Descrição |
|---|---|---|
| `/notificacoes/api/admin/notification_feedback/<uuid>/` | GET | Lista de feedbacks com filtros `q`, `rating_min`, `rating_max`, `created_from`, `created_to`, `with_feedback`, `client_id`, `year`, `ordering`. |
| `/notificacoes/api/admin/notification_feedback/<uuid>/export/` | GET | CSV streaming respeitando os filtros (sem `page`/`page_size`). 200 só com cabeçalho se recorte vazio. |
| `/notificacoes/api/admin/notification_feedback/<uuid>/kpis/nps/` | GET | Indicadores NPS no recorte. |
| `/notificacoes/api/admin/notification_feedback/<uuid>/kpis/csat/` | GET | Indicadores CSAT no recorte. |
| `/notificacoes/api/admin/nps_csat/<uuid>/stats/` | GET | Estatísticas da pesquisa. |

**Entidades complexas:** `Notification` (categoria pesquisa, tipo nps/csat) + `NotificationUser` (respostas com `feedback_sent`, `rating`, `viewed`, `created_at`). Isolamento por `Notification` da URL.

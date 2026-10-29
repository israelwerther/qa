# KI Navegação: Sidebar e Menus Principais

> **Status:** Em construção contínua
> **Objetivo:** Mapear os rótulos REAIS da interface (Sidebar) para os respectivos caminhos/URLs no sistema, eliminando a adivinhação da IA na hora de instruir o QA humano ou criar testes Playwright.

---

## 📚 Menu: Cadernos
*(Mapeado a partir do perfil de Professor/Coordenador)*

Quando o usuário clica no item principal **Cadernos** na barra lateral, o dropdown revela as seguintes opções exatas:

| Rótulo Real na UI (Texto do link) | Ação / Destino Lógico | Observações |
|-----------------------------------|-----------------------|-------------|
| **Todos os cadernos** | Listagem geral de provas/cadernos disponíveis para o perfil. | Acesso primário para visualizar/editar cadernos globais. |
| **Listas de exercícios** | Listagem específica de listas de exercícios (homeworks). | URL geralmente usa `category=homework`. |
| **Solicitações de elaboração** | Fluxo de pedidos de criação de questões/provas. | |
| **Para você revisar** | Cadernos/Questões que aguardam revisão do usuário atual. | |
| **Revisões** | Histórico ou painel geral de revisões. | |

---

## 📝 Menu: Instrumentos Avaliativos
*(Mapeado a partir do perfil de Coordenador)*

| Rótulo Real na UI (Texto do link) | Ação / Destino Lógico | Observações |
|-----------------------------------|-----------------------|-------------|
| **Instrumentos Avaliativos** | Listagem principal de provas da escola (`/provas/?category=exam`). | Rótulo real usado para Coordenadores (o equivalente a "Todos os cadernos"). |

---

## 🏫 Menu: Aplicações
*(Mapeado a partir do perfil de Coordenador — validado no plano QA `feat/lista-ensalamento-por-turma-86ajvb3ka`)*

| Rótulo Real na UI (Texto do link) | Ação / Destino Lógico | Observações |
|-----------------------------------|-----------------------|-------------|
| **Ensalamento** | Listagem de ensalamentos (`/ensalamento/`) | Requer `client_has_distribution`. Dropdown da linha: **"Opções"** ➔ seção **"IMPRESSÃO"** ➔ **"Imprimir lista de pátio"** abre modal `#patioPrintConfig` (switch **"Separar lista por turma"**). |

Detalhe de seletores: `.ai_qa_acervo/docs/tests/usability/distribution_list.md` e `patio_list_by_class.md`.

---

## 📢 Menu: Notificações e Pesquisas NPS/CSAT
*(Mapeado a partir do perfil de Staff — validado na task ClickUp `CU-86akhtqav` / branch `feat/melhoria-relatorios-nps-csat-CU-86akhtqav`)*

| Rótulo Real na UI (Texto do link) | Ação / Destino Lógico | Observações |
|-----------------------------------|-----------------------|-------------|
| **Pesquisas NPS/CSAT** | Listagem de pesquisas de feedback (`/notificacoes/`) | Somente `user.is_staff`. Item do grupo "Gerenciamento" da sidebar (`sidebar-items/coordination.html`). Ativa em `notifications_list`, `nps_csat_create`, `nps_csat_update`, `notification_feedback_detail`. |
| **Nova Pesquisa** | Wizard de criação (`/notificacoes/nova/`) | 6 passos: Identidade → Público → Período → Disparo → Visualização → Revisão. |
| **Editar Pesquisa** | Wizard de edição (`/notificacoes/<uuid>/editar/`) | Restaura dados do wizard ao abrir. |
| **Feedbacks / Detalhes** | Lista de respostas de uma pesquisa (`/notificacoes/<uuid>/feedbacks/`) | Exibe KPIs, busca, filtros por nota/período/cliente, atalhos NPS (detratores/passivos/promotores), leitura e cópia do comentário, exportação CSV em `brand-600`. |

**Rotas da API (staff only):**
- `GET /notificacoes/api/admin/nps_csat/` — listagem de pesquisas (`notifications:api-admin-nps-csat-list`)
- `GET .../options/` — catálogo de opções (`api-admin-nps-csat-options`)
- `GET .../<uuid>/stats/` — estatísticas NPS/CSAT (`api-admin-nps-csat-stats`)
- `GET /notificacoes/api/admin/notification_feedback/<uuid>/` — respostas com filtros `q`, `rating_min`, `rating_max`, `created_from`, `created_to`, `with_feedback`, `client_id`, `year`, `ordering` (`api-notification-feedback-list`)
- `GET .../<uuid>/export/` — CSV streaming (`api-notification-feedback-export`)
- `GET .../<uuid>/kpis/nps/` e `.../kpis/csat/` — indicadores no recorte filtrado (`api-notification-feedback-nps-kpis`, `api-notification-feedback-csat-kpis`)

**Setup via mixer (fixture inicial para renderizar as telas):**
```python
from mixer.backend.django import mixer
from fiscallizeon.notifications.models import Notification

# Permissão obrigatória para ver qualquer tela do módulo: user.is_staff = True
notificacao = mixer.blend(
    Notification,
    category='survey',
    survey_type='nps',   # ou 'csat'
    trigger='create',
    model_name='study_material',
)
```

Detalhe de seletores DOM e ações da tela de feedbacks: `.ai_qa_acervo/docs/tests/usability/notification_user_feedback_list.md`.

*Nota para a IA:* Sempre que encontrar uma divergência entre o nome da View (`exams_list`) e o rótulo da UI, consulte este documento antes de pedir para o usuário clicar em "Provas" ou "Exames".

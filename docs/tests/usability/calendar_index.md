# Mapeamento de Usabilidade e Elementos DOM — Módulo de Calendário Escolar

> **Template associado:** `fiscallizeon/calendar/templates/calendar/calendar_index.html`
> **Componentes associados:**
> - `fiscallizeon/calendar/components/calendar_module_header/calendar_module_header.html`
> - `fiscallizeon/calendar/components/calendar_events_timeline/calendar_events_timeline.html`
> - `fiscallizeon/calendar/components/calendar_dates_grid/calendar_dates_grid.html`
> - `fiscallizeon/calendar/components/calendar_event_drawer/calendar_event_drawer.html`
> - `fiscallizeon/calendar/components/calendar_event_detail_modal/calendar_event_detail_modal.html`
> - `fiscallizeon/calendar/components/calendar_async_state/`

---

## 1. URLs e Navegação

| Tela / Recurso | URL exata | Método | Permissões / Gate |
|---|---|---|---|
| Módulo Calendário (Web) | `/calendario/` | GET | `LoginRequired2FAMixin`, `CheckHasPermission(COORDINATION, TEACHER)`, `client.has_calendar=True`, `calendar.view_calendarevent` |
| Deep Link de Evento | `/calendario/?event=<uuid>` | GET | Mesmas permissões da página web + permissão de leitura do evento |
| Filtro de Visualização | `/calendario/?view=eventos` ou `/calendario/?view=datas` | GET | Mesmas permissões web |
| API Listagem de Eventos | `/api/v2/calendar-events/?year=YYYY&month=MM` | GET | `CsrfExemptSessionAuthentication`, `view_calendarevent`, `client.has_calendar=True` |
| API Criação de Evento | `/api/v2/calendar-events/` | POST | `add_calendarevent` (ou professor com `view_calendarevent` criando evento pessoal) |
| API Detalhes de Evento | `/api/v2/calendar-events/<uuid>/` | GET | `view_calendarevent`, evento do mesmo cliente e com visibilidade permitida |
| API Atualização de Evento | `/api/v2/calendar-events/<uuid>/` | PUT / PATCH | `change_calendarevent`, restrito ao autor (`created_by == request.user`) |
| API Exclusão de Evento | `/api/v2/calendar-events/<uuid>/` | DELETE | `delete_calendarevent`, restrito ao autor (`created_by == request.user`) |

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões Necessárias
1. **Gate Comercial (`Client.has_calendar`):** O `Client` vinculado ao usuário MUST estar com `has_calendar = True`.
2. **Permissões de Modelo Django:**
   - Visualização: `calendar.view_calendarevent`
   - Criação: `calendar.add_calendarevent` (professores com `view_calendarevent` ganham permissão de criar eventos pessoais restritos à sua unidade/público)
   - Edição: `calendar.change_calendarevent` (autor do evento)
   - Exclusão: `calendar.delete_calendarevent` (autor do evento)
3. **Membro de Coordenação ou Professor:**
   - Coordenador: `CoordinationMember` vinculado a `SchoolCoordination` da `Unity` do cliente.
   - Professor: `Inspector` (ou vínculo docente) nas unidades do cliente.

### Setup de Dados em Python (Mixer)
```python
import datetime
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember
from fiscallizeon.calendar.models import CalendarEvent

# 1. Cliente com Módulo Calendário Habilitado
client = mixer.blend(Client, has_calendar=True)
unity = mixer.blend(Unity, client=client, name="Unidade Central")
coordination = mixer.blend(SchoolCoordination, unity=unity)

# 2. Usuário Coordenador com Permissões de Calendário
coordinator = mixer.blend(User, is_staff=True)
mixer.blend(CoordinationMember, user=coordinator, coordination=coordination)
for codename in ('view_calendarevent', 'add_calendarevent', 'change_calendarevent', 'delete_calendarevent'):
    coordinator.user_permissions.add(Permission.objects.get(codename=codename))

# 3. Evento Institucional da Coordenação
today = datetime.date.today()
event_coord = mixer.blend(
    CalendarEvent,
    client=client,
    created_by=coordinator,
    title="Reunião Geral Pedagógica",
    category="pedagogical",
    start_date=today,
    end_date=today,
    start_time=datetime.time(14, 0),
    end_time=datetime.time(16, 0),
    participants=["coordination", "teachers"],
    is_personal=False,
    location="Auditório Principal",
    description="Alinhamento pedagógico sobre o cronograma de avaliações do bimestre."
)
event_coord.unities.add(unity)
```

---

## 3. Seletores DOM e Ações

### 3.1. Navegação e Header do Módulo (`calendar_module_header`)
- **Container Principal:** `#calendar-module-header`
- **Título / Rótulo do Período:** `#calendar-module-header h1` (ex: "Agosto 2024")
- **Botão Período Anterior:** `#calendar-module-header button[aria-label="Período anterior"]`
- **Botão Próximo Período:** `#calendar-module-header button[aria-label="Próximo período"]`
- **Alternador de Visualização (Toggle):**
  - **Aba "Datas":** `#calendar-module-header button:has-text("Datas")`
  - **Aba "Eventos":** `#calendar-module-header button:has-text("Eventos")`
- **Botão Adicionar Evento:** `#calendar-module-header button:has-text("Adicionar")` (visível quando `can_add=True`)

### 3.2. Visualização Linha do Tempo (`calendar_events_timeline`)
- **Container Principal:** `#calendar-events-timeline`
- **Estado Vazio (Empty State):** `#calendar-events-timeline:has-text("Nenhum evento neste período")`
- **Grupo de Data (Cabeçalho do Dia):** `#calendar-events-timeline [data-date-group]`
- **Cards de Evento:** `#calendar-events-timeline .calendar-event-card` (ou elementos com `@click="openDetail(event)"`)
- **Menu de Ações do Card (3 Pontos):**
  - Gatilho: `.calendar-event-actions-trigger`
  - Item "Visualizar": `.calendar-event-actions-item:has-text("Visualizar")`
  - Item "Editar": `.calendar-event-actions-item--edit:has-text("Editar")`
  - Item "Duplicar": `.calendar-event-actions-item:has-text("Duplicar")`
  - Item "Excluir": `.calendar-event-actions-item--delete:has-text("Excluir")`

### 3.3. Visualização Grade Mensal (`calendar_dates_grid`)
- **Container Principal:** `#calendar-dates-grid`
- **Células dos Dias:** `#calendar-dates-grid .tw-grid-cols-7 > div`
- **Chips de Evento:** `button[title]` dentro da célula correspondente ao dia
- **Gatilho de Mais Eventos (Overflow):** `.calendar-dates-overflow-trigger` (ex: `+2 mais`)
- **Popover de Overflow:** `.calendar-dates-overflow-popover`

### 3.4. Drawer Lateral de Criação e Edição (`calendar_event_drawer`)
- **Container Principal:** `#calendar-event-drawer`
- **Painel do Drawer:** `#calendar-event-drawer-panel`
- **Título do Drawer:** `#calendar-event-drawer-title` ("Novo evento" ou "Editar evento")
- **Botão Fechar:** `#calendar-event-drawer button[aria-label="Fechar"]`
- **Campos de Formulário:**
  - **Título:** `input#calendar-event-title`
  - **Checkbox Evento Pessoal:** `input#calendar-event-is-personal` (apenas coordenação)
  - **Select de Unidades:** `select#calendar-event-unities` (visível apenas com múltiplas unidades)
  - **Categoria (Select):** `select#calendar-event-category` (Pedagógico, Administrativo, Avaliação, Feriado)
  - **Data e Hora Inicial:** `input#calendar-event-start-datetime`
  - **Data e Hora Final:** `input#calendar-event-end-datetime`
  - **Público / Participantes (Checkboxes):**
    - Professores: `input.calendar-event-drawer-checkbox-input[value="teachers"]`
    - Coordenação: `input.calendar-event-drawer-checkbox-input[value="coordination"]`
    - Alunos: `input.calendar-event-drawer-checkbox-input[value="students"]`
    - Responsáveis: `input.calendar-event-drawer-checkbox-input[value="guardians"]`
  - **Local:** `input#calendar-event-location`
  - **Descrição:** `textarea#calendar-event-description`
- **Botão de Submissão:** `#calendar-event-drawer button[type="submit"]` ("Adicionar Evento" ou "Salvar evento")

### 3.5. Modal de Detalhes (`calendar_event_detail_modal`)
- **Container Principal:** `#calendar-event-detail-modal`
- **Título do Evento:** `#calendar-event-detail-title`
- **Botão Fechar:** `#calendar-event-detail-modal button[aria-label="Fechar modal de evento"]`
- **Botão Compartilhar:** `#calendar-event-detail-modal button:has-text("Compartilhar")` (muda para "Link copiado!")
- **Botão Editar:** `#calendar-event-detail-modal button:has-text("Editar")` (visível para o autor)

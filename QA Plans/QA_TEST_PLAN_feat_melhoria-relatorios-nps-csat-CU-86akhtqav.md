## 0. Metadata (Metadados de QA)

| Campo                      | Valor                                |
| -------------------------- | ------------------------------------ |
| **Data:**                  | 2026-10-27                           |
| **Natureza da Tarefa:**    | [Business Feature]                   |
| **Área da Feature:**       | Notifications / NPS / CSAT / Reports |
| **Nível de Risco:**        | Médio                                |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐                           |

---

## 1. Summary of Changes (Resumo das Alterações)

Branch `feat/melhoria-relatorios-nps-csat-CU-86akhtqav` (task ClickUp `CU-86akhtqav` — "Melhorias no relatórios de respostas com feedbacks do CSAT e NPS", OpenSpec change `nps-csat-feedback-analise`).

### Backend (lizeedu — app `notifications`)

- `fiscallizeon/notifications/filters.py`: `validate_feedback_query_params` (`rating_min`, `rating_max` 0–10, `created_from`, `created_to` `AAAA-MM-DD`, mensagens em português) e extensão de `NotificationUserFeedbackFilterSet` com `q`, `rating_min`/`rating_max`, `created_from`/`created_to`, `year`, `with_feedback`, `client_id`.
- `fiscallizeon/notifications/api/notification_feedback.py`: `NotificationUserFeedbackListAPIView` (400 se validação falhar), `NotificationNpsKpisAPIView`, `NotificationCsatKpisAPIView` (mesmo recorte dos filtros, ignoram `ordering`/paginação, 400 se tipo trocado), `NotificationUserFeedbackExportAPIView` (CSV streaming, `IsAdminUser`, 404 fora de NPS/CSAT, 200 só cabeçalho se vazio).
- `fiscallizeon/notifications/services/feedback_csv.py`: serviço de CSV (separador `;`, UTF-8 com BOM, colunas Data/Tipo/Pesquisa/Usuário/E-mail/Cliente/Tipo de usuário/Nota/Feedback/Visualizado/Respondido), `select_related` + `iterator`.
- `fiscallizeon/notifications/services/especial_triggers.py`: serviço compartilhado de disparo especial (`CreateEspecialNotificationAPIView`).
- `fiscallizeon/notifications/models.py`: nova choice `AFTER_DOC_IMPORT` / "Após importação DOC" em `ESPECIAL_TRIGGERS_CHOICES`/`ESPECIAL_TRIGGERS_BY_WHERE`, migração de estado das choices (sem coluna nova).
- `fiscallizeon/notifications/views.py`: `NotificationFeedbackDetailView` (template `notification_user_feedback_list.html`, contexto `feedback_years` com até 3 anos mais recentes).
- `fiscallizeon/notifications/urls.py`: rotas de feedback list/export/kpis; nenhuma nova em `/api/v1/` ou `/api/v2/`.
- `fiscallizeon/notifications/js/notification_feedback_list.js`: busca (debounce 400 ms/Enter), datas, nota, atalhos NPS, ano, ordenação estável (`apply_feedback_ordering`), CSV via axios blob, erro 400 na tela.
- `fiscallizeon/notifications/js/notification_feedback_export.js`: exportação CSV.
- `fiscallizeon/notifications/js/notification_feedback_reading.js`: diálogo com texto integral, cópia com confirmação/fallback, fechar por botão/Escape/fundo.
- Migração `0059_add_after_doc_import_trigger.py`.
- Testes API: `fiscallizeon/notifications/tests/api/test_notification_feedback_filters.py`, `test_notification_feedback_export.py`, `test_admin_nps_csat.py`, `test_doc_import_trigger.py` (146 testes no conjunto `fiscallizeon/notifications/tests`).

### Frontend da tela de feedbacks (`notification_user_feedback_list.html`)

- Barra de filtros: busca, De/Até, Nota mín./máx., atalhos NPS (Detratores 0–6 / Passivos 7–8 / Promotores 9–10), botão "Exportar CSV" (`brand-600`), checkbox "Apenas com feedback", botões de ano (mais recente selecionado por padrão).
- KPIs: Enviados, Visualizados, Respondidos, NPS Score / Média CSAT (e Promotores/Passivos/Detratores para NPS), mensagem "Indicadores consideram os filtros aplicados."
- Tabela de respostas: cabeçalhos ordenáveis (Usuário, Nota, Visualizado, Respondido, Data; Feedback não ordena), paginação, diálogo de leitura/cópia do comentário (`textarea#feedback-full`, botão "Copiar texto").

### Gatilho NPS após importação DOC

- Opção "Após importação DOC" exposta no wizard/Admin via choices do model, validação via `Notification.clean()`, serviço compartilhado, disparo apenas após lote confirmado não vazio ser salvo em `confirmImportQuestionsFromPreview`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

**IN SCOPE:**

- Tela de feedbacks de uma pesquisa (`/notificacoes/<uuid>/feedbacks/`): busca textual, ordenação de colunas, filtro por nota (faixa e atalhos NPS), filtro por período livre (De/Até), filtro por ano (3 anos mais recentes), filtro existente "apenas com feedback" e cliente, KPIs no mesmo recorte, exportação CSV respeitando filtros, leitura e cópia do comentário completo.
- Tela de listagem de pesquisas (`/notificacoes/`): visualização de estatísticas básicas (escopo da change `nps-csat-coordinator-module-86aj1yzcv`, relacionada).
- Novo gatilho "Após importação DOC" nas choices de gatilho especial e validação de conclusão de importação DOC.
- Restrição de acesso: apenas `user.is_staff = True` (`StaffRequiredMixin`) e `IsAdminUser` na API.

**OUT OF SCOPE (conforme OpenSpec `nps-csat-feedback-analise`):**

- Análise de sentimento/classificação/resumo por IA dentro da Lize (o CSV alimenta ferramentas externas).
- Exportação cruzada de várias pesquisas numa única planilha, ou exportação a partir da listagem de pesquisas.
- Planilha XLSX, e-mail, link público e autogestão pelo cliente.
- Filtros da listagem de pesquisas (spec adiada `nps-csat-coordinator-list-filters` da change `nps-csat-coordinator-module-86aj1yzcv`).
- Redesenhar o modal in-app de resposta ou alterar regras de vigência/público/repetição; a única ampliação de disparo é o evento "Após importação DOC".
- Disparar NPS em importação PDF, banco de questões, importação direta do Super Professor ou criação manual de questão.
- Trocar `redesign/base.html` por `redesign/base_component.html` nesta tela.
- Abrir a tela ou exportação para quem não é staff.
- Checkbox "Limpar" (removido a pedido do usuário).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

Canonical Navigation Map. Itens com `[verificar]` são inferidos do código e não confirmados 100% no rótulo visual.

| Destino                          | Rótulo real no menu UI                                                 | URL Django                                                             | View name                                                     |
| -------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------- |
| Listagem de pesquisas NPS/CSAT   | **Pesquisas NPS/CSAT** (grupo Gerenciamento da sidebar, só `is_staff`) | `/notificacoes/`                                                       | `notifications:notifications_list`                            |
| Feedbacks / Detalhes da pesquisa | (link no menu de opções da linha da pesquisa)                          | `/notificacoes/<uuid>/feedbacks/`                                      | `notifications:notification_feedback_detail`                  |
| Editar pesquisa                  | **Editar pesquisa** (link no cabeçalho da tela de feedbacks)           | `/notificacoes/<uuid>/editar/`                                         | `notifications:nps_csat_update`                               |
| Nova pesquisa (wizard)           | **Nova Pesquisa** [verificar]                                          | `/notificacoes/nova/`                                                  | `notifications:nps_csat_create`                               |
| API lista feedbacks              | (endpoint)                                                             | `/notificacoes/api/admin/notification_feedback/<uuid>/`                | `notifications:api-notification-feedback-list`                |
| API export CSV                   | (endpoint)                                                             | `/notificacoes/api/admin/notification_feedback/<uuid>/export/`         | `notifications:api-notification-feedback-export`              |
| API KPIs NPS/CSAT                | (endpoint)                                                             | `/notificacoes/api/admin/notification_feedback/<uuid>/kpis/nps\|csat/` | `notifications:api-notification-feedback-nps-kpis\|csat-kpis` |

**Permissão:** todas as views usam `StaffRequiredMixin` → `user.is_staff = True`. API usa `IsAdminUser`.

**Mapeamento de tela:** `.ai_qa_acervo/docs/tests/usability/notification_user_feedback_list.md`

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/notification_user_feedback_list.md)**

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comando para rodar os testes automatizados da equipe

```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/notifications/tests/
```

Ruff:

```bash
./scripts/dev/run-ruff.sh --no-tty
```

### Persona

**Staff / Superusuário** (ex: `cloud.admin@lize.local`). Todas as telas e APIs do módulo exigem `user.is_staff = True` (coordenador/professor recebem redirect 302 ou 403). Não testar com aluno — fora de escopo.

### Setup via mixer (fixture inicial — padrão extraído dos testes da equipe)

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client
from fiscallizeon.notifications.models import Notification, NotificationUser
from django.conf import settings
from django.utils import timezone


def criar_cenario_feedback_nps():
    staff = mixer.blend(
        User,
        is_staff=True,
        is_superuser=True,
        is_active=True,
        two_factor_enabled=False,
        must_change_password=False,
    )
    client_obj = mixer.blend(Client, two_factor_enabled=False)

    notification = mixer.blend(
        Notification,
        title='Pesquisa NPS de teste',
        description='Desc',
        content='<p>x</p>',
        type=Notification.NPS,
        category=Notification.SEARCH,
        start_date=timezone.now() - timezone.timedelta(days=1),
        end_date=timezone.now() + timezone.timedelta(days=30),
        repeat_days=30,
        segments=[settings.COORDINATION],
        elementary_school=True,
        high_school=True,
        trigger=Notification.AFTER_CREATE,
        model='exams.StatusQuestion',
        show_form=True,
        show_rating=True,
    )
    notification.clients.add(client_obj)

    feedback = mixer.blend(
        NotificationUser,
        notification=notification,
        user=mixer.blend(
            User,
            name='Marina Alves',
            username='marina-teste',
            email='marina-teste@example.com',
        ),
        rating=3,
        feedback='O enunciado demora para salvar.',
        feedback_sent=True,
        viewed=True,
        next_nps_date=timezone.localdate(),
    )
    return staff, notification, feedback
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona ativa:** Staff (Superusuário) logado no portal do coordenador (`http://localhost:8000`). Todas as telas exigem `is_staff = True`.

### 5.1 Navegação e Listagem de Pesquisas [Automatizável ✅]

#### Cenário 1 — Acessar a listagem de pesquisas NPS/CSAT pelo menu lateral

**Ação humana:**

- [x] Logar como staff (`cloud.admin@lize.local`, senha `123456`).
- [x] Na barra lateral esquerda, grupo "Gerenciamento", clicar no item **"Pesquisas NPS/CSAT"** (somente visível para staff).
- [x] Confirmar que a página carrega com o título **"Pesquisas NPS/CSAT — Lize"** e exibe a listagem de pesquisas cadastradas.

**Referência técnica (para automação):**

- URL: `/notificacoes/`
- Seletor: item de menu com texto `"Pesquisas NPS/CSAT"` (sidebar, grupo Gerenciamento, condição `user.is_staff`).
- Estado esperado: `sidebar-menu-item-active` quando `request.resolver_match.url_name` for `notifications_list`, `nps_csat_create`, `nps_csat_update` ou `notification_feedback_detail`.
- Fixture: `mixer.blend(User, is_staff=True, is_superuser=True)` + `mixer.blend(Notification, ...)`.

---

### 5.2 Tela de Feedbacks — KPIs e Filtros [Automatizável ✅]

#### Cenário 2 — Abrir os feedbacks de uma pesquisa e conferir KPIs

**Ação humana:**

- [x] Na listagem de pesquisas, abrir o menu de opções de uma pesquisa (botão de opções da linha) e clicar no link de detalhes/feedbacks.
- [x] Confirmar que a tela exibe o título com o nome da pesquisa e o badge do tipo (NPS ou CSAT).
- [x] Conferir os cards de indicadores: **"Enviados"**, **"Visualizados"**, **"Respondidos"** e **"NPS Score"** / **"Média CSAT"**.
- [x] Para NPS, conferir os cards extras: **"Promotores (9–10)"**, **"Passivos (7–8)"**, **"Detratores (0–6)"**.
- [x] Confirmar a legenda **"Indicadores consideram os filtros aplicados."** acima dos filtros.

**Referência técnica (para automação):**

- URL: `/notificacoes/<uuid>/feedbacks/`
- Seletor: `h1` com texto da pesquisa; `div id="notification-feedback-app"`.
- Estado esperado: cards com textos "Enviados", "Visualizados", "Respondidos", "NPS Score" ou "Média CSAT".
- Fixture: `mixer.blend(Notification, type=Notification.NPS)` + `mixer.blend(NotificationUser, ...)`.

#### Cenário 3 — Aplicar filtro de busca por comentário/nome/e-mail

**Ação humana:**

- [x] No campo de busca (rótulo **"Busca"**, placeholder **"Comentário, nome ou e-mail"**), digitar um trecho do comentário de um feedback existente.
- [x] Pressionar Enter ou aguardar a pausa de digitação.
- [x] Confirmar que a tabela exibe apenas os feedbacks que batem com o termo (busca ignora caixa e espaços).

**Referência técnica (para automação):**

- URL: `/notificacoes/api/admin/notification_feedback/<uuid>/?q=<termo>`
- Seletor: `input id="feedback-query"` (type=search, `v-model="searchQuery"`).
- Estado esperado: tabela filtrada; `data-list-url` no root da app.
- Fixture: `mixer.blend(NotificationUser, feedback='...')`.

#### Cenário 4 — Filtrar por nota (faixa e atalhos NPS)

**Ação humana:**

- [x] Nos campos **"Nota mín."** e **"Nota máx."**, preencher uma faixa (ex: 0 a 6) e confirmar que a tabela atualiza.
- [x] Para pesquisa NPS, clicar nos atalhos **"Detratores 0–6"**, **"Passivos 7–8"**, **"Promotores 9–10"** e confirmar o destaque ativo (borda/fundo laranja).
- [x] Confirmar que os KPIs (score, contagem de promotores/passivos/detratores) refletem o recorte filtrado.

**Referência técnica (para automação):**

- URL: `/notificacoes/api/admin/notification_feedback/<uuid>/?rating_min=0&rating_max=6`
- Seletor: `input id="feedback-rating-min"` / `id="feedback-rating-max"`; botões `button:has-text("Detratores 0–6")` / `"Passivos 7–8"` / `"Promotores 9–10"`.
- Estado esperado: `aria-pressed="true"` no atalho ativo; classe `tw-border-orange-600 tw-bg-orange-50`.
- Fixture: `mixer.blend(NotificationUser, rating=...)`.

#### Cenário 5 — Filtrar por período livre (De/Até) e por ano

**Ação humana:**

- [x] Preencher os campos **"De"** e **"Até"** (tipo data) e confirmar que o recorte inclui início e fim do dia no fuso local.
- [x] Clicar em um dos botões de ano (ex: o mais recente selecionado por padrão) e confirmar que a lista e os KPIs restringem a esse ano.
- [x] Desmarcar o ano selecionado e confirmar que todos os anos ficam disponíveis.

**Referência técnica (para automação):**

- URL: `/notificacoes/api/admin/notification_feedback/<uuid>/?created_from=AAAA-MM-DD&created_to=AAAA-MM-DD&year=YYYY`
- Seletor: `input id="feedback-created-from"` / `id="feedback-created-to"` (type=date); botões de ano dentro de `role="group" aria-label="Filtrar respostas por ano"`.
- Estado esperado: ano selecionado com `aria-pressed="true"`; `data-default-year` no root.
- Fixture: `mixer.blend(NotificationUser, created_at=...)`.

#### Cenário 6 — Filtrar "Apenas com feedback" e por cliente

**Ação humana:**

- [x] Marcar o checkbox **"Apenas com feedback"** e confirmar que somem as respostas sem comentário.
- [x] No select **"Ver apenas respostas de um determinado cliente"**, escolher um cliente e confirmar a restrição.

**Referência técnica (para automação):**

- URL: `.../?with_feedback=true&client_id=<uuid>`
- Seletor: `input v-model="withFeedback"`; `select id="feedback-client-filter"`.
- Estado esperado: checkbox marcado; `data-client-list-url` no root.
- Fixture: `mixer.blend(Client)` + `mixer.blend(NotificationUser, with_feedback=True)`.

---

### 5.3 Tela de Feedbacks — Leitura e cópia do comentário [Automatizável ✅]

#### Cenário 7 — Ler o comentário completo no diálogo

**Ação humana:**

- [x] Na linha de um feedback que tenha comentário, clicar no trecho do comentário (botão de leitura).
- [x] Confirmar que abre um diálogo (modal) na mesma tela com: nome, e-mail, cliente, nota, data e o **texto integral do feedback** em área de texto somente leitura.
- [x] Fechar o diálogo pelo botão **"Fechar"**, pela tecla Escape ou clicando no fundo.

**Referência técnica (para automação):**

- URL: mesma `/notificacoes/<uuid>/feedbacks/` (diálogo é Vue no mesmo template).
- Seletor: `button:has-text("<trecho do feedback>")` (linha da tabela); `div[v-if="openFeedback"]`; `h2#feedback-dialog-title`; `textarea#feedback-full` (`readonly`).
- Estado esperado: diálogo com `role="dialog"`, `aria-modal="true"`; texto igual ao `item.feedback`.
- Fixture: `mixer.blend(NotificationUser, feedback='texto longo')`.

#### Cenário 8 — Copiar o texto do feedback

**Ação humana:**

- [x] No diálogo de leitura, clicar no botão **"Copiar texto"**.
- [x] Confirmar a transição do botão para **"Copiando…"** e depois **"Copiado"**.
- [x] (Opcional) Colar em outro local para confirmar que o texto foi copiado para a área de transferência.

**Referência técnica (para automação):**

- Seletor: `button:has-text("Copiar texto")` (`@click="copyFeedback"`, `:aria-disabled="feedbackCopying"`).
- Estado esperado: texto do botão muda para "Copiando…" → "Copiado".
- Fixture: `mixer.blend(NotificationUser, feedback='...')`.

---

### 5.4 Tela de Feedbacks — Exportação CSV [Automatizável ✅]

#### Cenário 9 — Exportar CSV respeitando os filtros aplicados

**Ação humana:**

- [x] Aplicar qualquer combinação de filtros (busca, nota, período, ano, cliente, "apenas com feedback").
- [x] Clicar no botão **"Exportar CSV"** (botão laranja, `brand-600`).
- [x] Confirmar que o download inicia e que o arquivo contém as colunas: Data, Tipo, Pesquisa, Usuário, E-mail, Cliente, Tipo de usuário, Nota, Feedback, Visualizado, Respondido.
- [x] Confirmar que o CSV respeita os filtros (não só a página visível) e que, com recorte vazio, o arquivo vem só com o cabeçalho.

**Referência técnica (para automação):**

- URL: `/notificacoes/api/admin/notification_feedback/<uuid>/export/` (axios blob, separador `;`, UTF-8 com BOM).
- Seletor: `button:has-text("Exportar CSV")` (`@click="exportCsv"`, `:disabled="exportingCsv || !notificationType"`).
- Estado esperado: download de `.csv`; texto do botão "Exportando…" durante a requisição.
- Fixture: `mixer.blend(NotificationUser, ...)` + staff (`is_staff=True`).

---

### 5.5 Gatilho NPS após importação DOC [Apenas Manual 👁]

#### Cenário 10 — Configurar e disparar o gatilho "Após importação DOC"

**Ação humana:**

- [x] No cadastro/edição de uma pesquisa (wizard), confirmar que a opção **"Após importação DOC"** aparece nas choices de gatilho especial.
- [x] Concluir uma importação de DOC com ao menos uma questão salva.
- [x] Confirmar que a pesquisa NPS é disparada para o usuário que importou, conforme público, vigência e repetição configurados.
- [x] Confirmar que upload, conversão, prévia, cancelamento e falha NÃO acionam o gatilho.

**Referência técnica (para automação):**

- URL: `/notificacoes/nova/` (wizard) e fluxo de importação DOC em `exams`.
- Estado esperado: choice `AFTER_DOC_IMPORT` / "Após importação DOC" exposta pelo model; serviço `especial_triggers.py`.
- Fixture: `mixer.blend(Notification, especial_trigger=Notification.AFTER_DOC_IMPORT)`.
- Classificação: **[Apenas Manual 👁]** — depende do fluxo real de importação DOC e do envio da pesquisa ao usuário; validação visual/fluxo ponta a ponta.

---

### 5.6 Permissões e Segurança [Automatizável ✅]

#### Cenário 11 — Coordenador e professor não acessam as telas de NPS/CSAT

**Ação humana:**

- [x] Logar como coordenador (não staff) e tentar acessar `/notificacoes/` → confirmar redirect/negado.
- [x] Logar como professor e tentar acessar a API `/notificacoes/api/admin/nps_csat/` → confirmar 403.
- [x] Logar como aluno e confirmar que não vê a pesquisa nem o menu.

**Referência técnica (para automação):**

- URL: `/notificacoes/` e `/notificacoes/api/admin/nps_csat/`.
- Estado esperado: redirect 302 (coordenador) ou 403 (professor na API); menu "Pesquisas NPS/CSAT" ausente para não-staff.
- Fixture: `mixer.blend(User, is_staff=False)` (coordenador com `CoordinationMember`) e `mixer.blend(Inspector, inspector_type=Inspector.TEACHER)`.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

A tela evolui `notification_user_feedback_list.html` (`extends redesign/base.html`, sem migração para `base_component`). Não é redesign nem tela nova.

- [x] Tirar print da tela de feedbacks com KPIs, barra de filtros e tabela de respostas ![](../evidencias/tela.png)
- [x] Comparar lado a lado com os mockups em `openspec/changes/nps-csat-feedback-analise/references/` (`feedback_list.html`, `feedback_leitura.html`).
- [x] Confirmar que os botões de atalho NPS, o botão "Exportar CSV" (`brand-600` / laranja) e os botões de ano respeitam o design system.
- [x] Confirmar que o diálogo de leitura exibe o texto integral em `<textarea readonly>` e que o tooltip truncado (`:title`) não é mais o único meio de leitura.
- [x] Validar estados:
  - lista vazia ("Nenhuma resposta encontrada.")
  - erro de exportação. ![](../evidencias/estados.png)

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!WARNING]
> **Title:** Nenhum bug crítico bloqueante identificado nesta revisão da branch `feat/melhoria-relatorios-nps-csat-CU-86akhtqav`.
> **Context/Root Cause:** —
> **Expected Behavior:** —
> **Workaround:** —

> [!BUG]
> **1. Title:** [Spec Gap] Filtro de ano não exibido quando não há anos com respostas.
> **2. Context/Root Cause:** A seção de anos só renderiza quando `feedback_years` é preenchido (view `NotificationFeedbackDetailView` consulta `NotificationUser.objects.filter(feedback_sent=True).dates(...)`). Se a pesquisa for nova sem respostas, o filtro de ano some da UI.
> **3. Expected Behavior:** O filtro de ano deveria estar presente (vazio ou com mensagem) mesmo sem respostas, para consistência da tela.
> **4. Workaround:** Enviar pelo menos uma resposta para a pesquisa antes de validar o filtro de ano.

> [!BUG]
> **1. Title:** [UX/UI] Botão "Exportar CSV" desabilitado quando `notificationType` é nulo.
> **2. Context/Root Cause:** O botão tem `:disabled="exportingCsv || !notificationType"`. Enquanto o tipo da pesquisa não é carregado, o botão fica bloqueado.
> **3. Expected Behavior:** O botão deveria ficar habilitado após o carregamento dos dados iniciais da pesquisa.
> **4. Workaround:** Aguardar o carregamento dos KPIs (desaparecer "Carregando indicadores...") antes de exportar.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[Tech Debt] Checkbox "Limpar" removido:** A pedido do usuário, o botão Limpar foi removido da barra de filtros. Não há forma rápida de resetar todos os filtros de uma vez (exceto recarregar a página).

> [!NOTE]
> **[WONTFIX] Exportação XLSX / e-mail / link público:** Fora do escopo desta change (conforme Não-Objetivos do OpenSpec). O CSV no painel é a única exportação prevista neste ciclo.

> [!NOTE]
> **[Scope Gap] Filtros na listagem de pesquisas:** Adiados para a change `nps-csat-coordinator-list-filters` (`nps-csat-coordinator-module-86aj1yzcv`). Não fazem parte desta validação.

> [!NOTE]
> **[WONTFIX] Análise de sentimento por IA:** O CSV alimenta ferramentas externas; não há classificação/resumo dentro da Lize.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/notification_user_feedback_list.md)**

**Automation Snippet (UI + Data Setup):** veja `.ai_qa_acervo/KI_Setup_Mixer.md` (seção 1), que une o setup via `mixer.blend()` com a navegação Playwright até `/notificacoes/<uuid>/feedbacks/` e as asserções sobre os seletores DOM estáveis e rotas de API críticas.

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Qual foi o principal gargalo durante o teste?**
  _(A ser preenchido)_
- **Houve muitas idas e vindas com o desenvolvedor?**
  _(A ser preenchido)_
- **Como o fluxo de dev ou QA para essa task específica poderia ter sido melhorado?**
  _(A ser preenchido)_

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

- Considerar padronizar o preenchimento automático da Seção 0 a partir dos dados da task ClickUp (status, assignees, due_date) para evitar digitação manual.
- Avaliar incluir na Seção 4 um comando único que rode tanto os testes Python quanto os JS da feature (`node --test fiscallizeon/notifications/tests/js/notification_doc_import.test.js`).
- A regra `[Apenas Manual 👁]` para o gatilho DOC depende de ambiente de importação DOC funcional; considerar marcar como `[Automatizável ✅]` apenas a validação da choice no model via API.

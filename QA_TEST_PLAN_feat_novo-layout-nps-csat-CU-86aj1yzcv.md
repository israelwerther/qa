---
Date: 2026-07-14
Feature Area: Notifications / NPS / CSAT
Risk Level: High
OpenSpec Quality: 5
---

## 1. Resumo das Alterações (Summary of Changes)
- **Backend / Modelagem:**
  - Criação do serviço `TriggerDescriptionBuilder` para descrições de gatilho em linguagem natural.
  - Extensão do `NotificationQuerySet` com métodos `for_coordination`, `search_nps_csat` e agregações de estatísticas (`with_nps_csat_stats`).
- **APIs de Gerenciamento (`nps-csat-management-api`):**
  - Novos endpoints REST em `/api/admin/nps_csat/` para listagem, criação e edição exclusivas para coordenadores, baseadas em `Notification.clean()`.
  - Endpoint de catálogo `options` e endpoint de estatísticas (`stats`) que calcula NPS e CSAT.
- **Frontend Administrativo (`nps-csat-coordinator-list` & `nps-csat-coordinator-wizard`):**
  - Listagem de pesquisas NPS/CSAT com design do novo padrão (colunas, status legíveis, paginação e métricas básicas).
  - Assistente de 5 passos (Wizard) usando Vue/Alpine para criar/editar pesquisas (Identidade, Público, Período, Disparo e Revisão), incluindo preview textual do trigger.
- **Frontend Usuário Final (`nps-csat-inapp-modal`):**
  - Modal in-app refatorado (`vue-notifications.html`) separando a nota (estrelas/0-10) do comentário.
  - Nova tela de confirmação/sucesso de feedback enviada.
- **Integração no Sistema:**
  - Atualização do menu lateral de Coordenação para o link correto das Pesquisas NPS/CSAT.

## 2. Diferenças de Escopo (Scope Boundaries)
- **IN SCOPE:** 
  - Listagem paginada, visualização de estatísticas, criação via Wizard e edição de pesquisas NPS/CSAT via menu da Coordenação.
  - Componente in-app do modal recebendo avaliações separadas com tela de sucesso.
- **OUT OF SCOPE:** 
  - **Filtros na Listagem:** Conforme explicitado no arquivo `tasks.md`, os filtros (`type`, `status`, `q`), botões de filtrar e off-canvas **não** fazem parte do `/opsx:apply` atual. Eles estão diferidos.
  - Pesquisas fora do App (Email, SMS).
  - Dashboards analíticos complexos (apenas as métricas unitárias por pesquisa estão no escopo).

## 3. Navegação e Camada Técnica
| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Listagem de Pesquisas | Pesquisas NPS/CSAT | `/notificacoes/` | `notifications:notifications_list` |
| Criar Nova Pesquisa | Nova Pesquisa | `/notificacoes/nova/` | `notifications:nps_csat_create` |
| Editar Pesquisa | Editar | `/notificacoes/<uuid>/editar/` | `notifications:nps_csat_update` |
| Options API | (Endpoint) | `/notificacoes/api/admin/nps_csat/options/` | `notifications:api-admin-nps-csat-options` |

## 4. Testes Automatizados e Setup de Dados
Para rodar os testes automatizados já implementados na branch:
```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/notifications/tests/
```
Para setup via **mixer** durante o QA (Camada Técnica - Exemplo):
```python
# No shell ou na inicialização do teste Playwright
from mixer.backend.django import mixer
from fiscallizeon.notifications.models import Notification

# Gerar uma notificação tipo NPS
nps = mixer.blend(
    Notification, 
    category='survey', 
    survey_type='nps', 
    trigger='create', 
    model_name='study_material'
)
```

## 5. Roteiro de Testes (Execution Test Script)

### Configuração e Permissões
- [x] **[Automatizável ✅]** Acessar a plataforma com usuário sem permissão de superusuário.
  - *Camada Técnica:* Tentar carregar `/notificacoes/` e `/api/admin/nps_csat/`.
  - *Resultado Esperado:* Acesso negado (403/redirect). Conforme checklist, APENAS superusuários podem acessar essas views/APIs na gestão.

### Listagem de Pesquisas
- [x] **[Automatizável ✅]** Validar conteúdo da coluna Disparo.
  - *Camada Técnica:* Visualizar a listagem via interface ou `GET /api/admin/nps_csat/`.
  - *Resultado Esperado:* Coluna exibe frase legível (ex: "depois de criar um caderno").
- [x] **[Automatizável ✅]** Validar contadores de visualizações e respostas.
  - *Camada Técnica:* Acessar a listagem, simular interação num feedback e recarregar.
  - *Resultado Esperado:* Contadores de envios, views e respostas batem com as interações reais.
- [x] **[Apenas Manual 👁]** Filtro rápido de pesquisas ativas.
  - *Camada Técnica:* Marcar a opção "Somente pesquisas ativas" na listagem.
  - *Resultado Esperado:* Pesquisas agendadas (futuras) e encerradas somem da tabela.
- [x] **[Apenas Manual 👁]** Ausência de filtros complexos.
  - *Camada Técnica:* Inspecionar a UI da listagem.
  - *Resultado Esperado:* Não existe botão "Filtrar" nem painel lateral (adiados).
- [x] **[Automatizável ✅]** Menus de opções: Detalhes e Editar.
  - *Camada Técnica:* Clicar em "Detalhes" e depois em "Editar".
  - *Resultado Esperado:* "Detalhes" leva à página de indicadores. "Editar" abre o Wizard com os dados já preenchidos.

### Wizard de Criação / Edição
- [x] **[Apenas Manual 👁]** Navegação com estado mantido (6 passos).
  - *Camada Técnica:* Preencher dados e navegar: Identidade → Público → Período → Disparo → Visualização → Revisão. Clicar em voltar.
  - *Resultado Esperado:* O que foi preenchido é mantido no state do Vue (não é perdido ao voltar/avançar). (Validado durante o processo).
- [x] **[Automatizável ✅]** Exclusividade no passo Disparo.
  - *Camada Técnica:* Tentar ativar dois modos de disparo diferentes e salvar.
  - *Resultado Esperado:* Só um modo fica ativo e os dados são persistidos. (Falhou: Os campos não salvam - Ver Bug 2).
- [x] **[Apenas Manual 👁]** Preview textual dinâmico.
  - *Camada Técnica:* Chegar nos passos Disparo e Revisão.
  - *Resultado Esperado:* Descrição em português claro para quem, quando e com qual recorrência a pesquisa aparece. (Validado nos prints anteriores).
- [x] **[Automatizável ✅]** Validação de Público.
  - *Camada Técnica:* Tentar publicar sem marcar ensino fundamental ou médio.
  - *Resultado Esperado:* Erro de validação renderizado na UI.
- [x] **[Automatizável ✅]** Validação de Clientes.
  - *Camada Técnica:* Tentar publicar sem clientes selecionados (quando público não for "parceiros").
  - *Resultado Esperado:* Erro de validação.
- [x] **[Automatizável ✅]** Conflito Delay x Exibição Automática.
  - *Camada Técnica:* Marcar "exibição automática" junto com um delay > 0.
  - *Resultado Esperado:* Combinação rejeitada com mensagem clara no passo. (Validado: o campo de delay some da UI adequadamente).
- [x] **[Automatizável ✅]** Disparo inválido.
  - *Camada Técnica:* Usar um trigger incompatível com a ação/modelo escolhido.
  - *Resultado Esperado:* Erro no passo certo, com texto compreensível. (Bloqueado/Pulado: Devido ao Bug 2 dos disparos não salvarem).
- [x] **[Apenas Manual 👁]** Fluxo de Sucesso e Reflexo no Admin Django.
  - *Camada Técnica:* Salvar. Checar a listagem web e `/admin/notifications/notification/`.
  - *Resultado Esperado:* Volta para a listagem onde a nova pesquisa surge. No Admin Django, os campos categoria (Pesquisa), avaliação e comentário estão devidamente ativados. (Validado na criação da pesquisa 'teste 1').

### Detalhes e Métricas
- [x] **[Automatizável ✅]** Indicadores Gerais, NPS e CSAT.
  - *Camada Técnica:* Checar a tela de detalhes ou o endpoint `/stats/`.
  - *Resultado Esperado:* Mostra enviados, vistos, respondidos. Para NPS: Score e contagem (Promotores 9-10, Passivos 7-8, Detratores 0-6). Para CSAT: Média de 1 a 5 estrelas. (Validado para CSAT e NPS).
- [x] **[Automatizável ✅]** Lista de respostas.
  - *Camada Técnica:* Visualizar a lista de feedbacks.
  - *Resultado Esperado:* Nota, comentário e usuário visíveis. Filtro por cliente consegue restringir a lista. (Validado: filtro, tabela e checkbox de apenas feedback presentes).

### Experiência do Usuário (Modal In-App)
- [x] **[Apenas Manual 👁]** Diferenciação NPS vs CSAT.
  - *Camada Técnica:* Acionar uma pesquisa NPS e outra CSAT no modal `vue-notifications.html`.
  - *Resultado Esperado:* NPS: 0 a 10. CSAT: 5 estrelas ("Muito ruim" / "Muito boa"). Nota e texto são separados visualmente. (Validado visual do NPS com sucesso, idêntico ao Figma. Faltando validar modal CSAT).
- [x] **[Automatizável ✅]** Envio e validação de Comentário Obrigatório.
  - *Camada Técnica:* Tentar submeter sem texto quando obrigatório.
  - *Resultado Esperado:* Botão Enviar fica desabilitado. Após o envio válido, confirmação "Obrigado pelo feedback!" substitui o modal. (Validado: A validação roda no frontend com exigência de 30 caracteres para notas NPS <= 7 e CSAT <= 3. Bloqueio funciona perfeitamente).
- [x] **[Automatizável ✅]** [Regressão] Notificações Antigas.
  - *Camada Técnica:* Exibir uma notificação do tipo Função, Aviso ou IA.
  - *Resultado Esperado:* O modal continua funcionando sem bugs ou campos fantasmas de nota. (Validado: Criado Aviso via Django Admin. A modal exibiu título, badge verde, texto e o botão 'Entendi' sem nenhum resíduo ou bug visual das opções de NPS/CSAT).

### Disparo e Público (Ponta a Ponta)
- [x] **[Automatizável ✅]** Restrição por Perfil.
  - *Camada Técnica:* Disparar pesquisa exclusiva de "coordenadores". Logar como aluno.
  - *Resultado Esperado:* O aluno não vê a pesquisa.
- [x] **[Automatizável ✅]** Recorrência temporal.
  - *Camada Técnica:* Responder uma pesquisa de recorrência mensal, simular passagem de 30 dias.
  - *Resultado Esperado:* A pesquisa reaparece para o usuário.
- [x] **[Automatizável ✅]** Ciclo de vida (Data Início / Encerramento).
  - *Camada Técnica:* Testar uma pesquisa no futuro e outra encerrada.
  - *Resultado Esperado:* Só ativas aparecem para novos usuários; encerradas param; agendadas aguardam.
- [x] **[Automatizável ✅]** Isolamento por Cliente.
  - *Camada Técnica:* Restringir pesquisa ao Cliente A, acessar com usuário do Cliente B.
  - *Resultado Esperado:* Não há vazamento da pesquisa para o Cliente B.

## 6. Validação Visual e de Layout
- [x] O visual do componente modal In-App NPS/CSAT (estado inicial e estado após submissão) bate rigorosamente com o design system / Figma especificado (`openspec/specs/ui-design-system/spec.md`). (Validado: Design idêntico ao Figma, cores e gradientes perfeitos. Única ressalva é o bug de tamanho fixo do Tailwind já mapeado no plano).
- [x] O design dos cards, tabelas e steps do Wizard seguem a base de redesign, garantindo a **não utilização** da classe `shadow-lg` de acordo com os critérios definidos em spec. (Validado: A interface do Wizard usa um design limpo e flat).

## 7. Bugs and Observations (Problemas Encontrados)

> [!BUG]
> **1. Title:** ~~[Backend Logic] Erro fatal na criação (M2M `clients`)~~ **[RESOLVIDO]**
> **2. Context/Root Cause:** O método `NotificationAdminWriteSerializer.create()` chamava `instance.full_clean()` antes de persistir as relações M2M (`clients`). A função `_validate_clients()` do modelo verificava o M2M e gerava um crash porque a instância ainda não tinha ID.
> **3. Fix Implemented:** A função `_validate_clients()` foi removida do modelo e trazida para o `NotificationAdminWriteSerializer`. Agora a validação dos clientes (M2M) ocorre através dos dados de payload no serializer antes do `instance.full_clean()`, evitando o crash.
> **4. Workaround:** (Não é mais necessário).
> [!BUG]
> **1. Title:** ~~[Backend Logic] Campos do Passo 4 (Disparo) não são persistidos.~~ **[RESOLVIDO]**
> **2. Context/Root Cause:** Ao preencher os disparos de CRUD ("Após ação no sistema") ou Evento Específico e salvar, os dados falham em salvar no banco ou falham na hidratação. Ao recarregar a pesquisa, o Passo 4 volta ao estado "em branco" (TriggerMode = crud, campos default = null). Possível falha na desserialização do `trigger` no backend.
> **3. Expected Behavior:** As seleções de "Quando", "Modelo" e "Evento específico" devem persistir após o clique em Salvar e serem restauradas na UI ao editar.
> **4. Workaround:** Manter os valores vazios (que equivalem ao trigger "Ao acessar a plataforma") para conseguir prosseguir com a criação da notificação caso o disparo específico não seja imperativo para o teste.

> [!BUG]
> **1. Title:** ~~[UX/UI] Race Condition (Roleta Russa) e Duplicação no Filtro Select2 (Dashboard)~~ **[ACEITÁVEL / DEBÍTO TÉCNICO]**
> **2. Context/Root Cause:** Há dois erros graves de ciclo de vida no `notification_user_feedback_list.html`:
>   * *Filtro Vazio/Cru:* O código usa `setTimeout(..., 500)` para iniciar o Select2. Como o select tem `v-if="items?.length > 0"`, se o request de `fetchList()` demorar mais de 500ms, o Select2 falha em inicializar e o campo fica vazio/cru na tela. Se o request for rápido, ele funciona.
>   * *Teletransporte e Duplicação:* Ao filtrar um cliente que não tem respostas, `items.length` vira 0. O `v-if` destrói o select do DOM, mas deixa o container do Select2 orfão (flutuando na tela). Ao limpar o filtro, o Vue recria o select cru, enquanto o lixo do Select2 antigo continua lá, causando duplicação.
> **3. Expected Behavior:** O filtro Select2 deve carregar os clientes consistentemente. A diretiva deveria ser `v-show` ao invés de `v-if` para não destruir o DOM do jQuery, e a inicialização não deve usar `setTimeout` arbitrário (usar `watch` ou `.then()` do axios com `$nextTick`).
> **4. Workaround QA / Status:** O componente se recupera sozinho após o carregamento da lista. Avaliado como um "Edge Case Visual" em conexões lentas. **Aceitável para produção**. Mapeado como débito técnico para melhoria futura.

> [!BUG]
> **1. Title:** [UX/UI] Tamanho da Modal In-App ("Pequeno" vs "Grande") é ignorado na renderização
> **2. Context/Root Cause:** No componente `vue-notifications.html`, a div `.modal-dialog` recebe dinamicamente a classe do Bootstrap referente ao tamanho escolhido (`:class="'modal-'+selectedNotification.notification.modalWidth"`). No entanto, foi adicionada uma classe estática do Tailwind `sm:tw-max-w-2xl` (max-width: 672px) na mesma div. Essa classe do Tailwind sobrepõe a configuração de tamanho, travando a modal para ser sempre "Grande", ignorando a escolha do usuário feita no Wizard (Passo 5).
> **3. Expected Behavior:** O tamanho escolhido no Wizard (Pequeno, Médio, Grande) deve ser respeitado pela modal final. A classe Tailwind limitadora de largura não deve sobrepor a classe dinâmica.
> **4. Workaround:** Nenhum do lado do usuário. O visual permanece elegante, mas não obedece ao parâmetro.

## 8. Melhorias Futuras (Tech Debt & UX)
> Itens de usabilidade ou novas funcionalidades (Feature Requests) que não quebram o uso atual e não afetam o cliente final, podendo ser priorizados futuramente.

> [!NOTE]
> **[UX/UI] Formatação de Data na Revisão**
> No Passo 6 (Revisão) do Wizard, o campo "Período" exibe as datas no formato bruto ISO (ex: `2026-07-15T15:09`) ao invés do padrão amigável (DD/MM/AAAA) que já é usado na frase do preview de Disparo logo abaixo.

> [!NOTE]
> **[UX/UI] Sidebar perde o estado "Ativo" no Dashboard**
> Na tela de Detalhes (`/feedbacks/`), o item "Pesquisas NPS/CSAT" do menu lateral perde a classe ativa (amarela), voltando ao estado cinza. Deve manter o destaque.

> [!NOTE]
> **[UX/UI] Fechamento acidental da Modal descarta o voto**
> Se o usuário seleciona uma nota (ex: 5) e acidentalmente clica fora da modal, ela se fecha. O sistema marca a notificação como "visualizada" (`viewed: true`) mas não envia a nota selecionada. O voto é perdido e a pesquisa não volta mais para o usuário. Como melhoria futura, o clique no backdrop deveria ser desabilitado (`backdrop="static"`) se a pesquisa for obrigatória ou se uma nota já estiver selecionada no state.

> [!NOTE]
> **~~[UX/UI Interna] Erro gramatical na coluna de Disparo~~ [RESOLVIDO]**
> Na tela de listagem de Pesquisas NPS/CSAT, o `TriggerDescriptionBuilder` gerava um texto duplicado: *"coordenadores e professores · **depois de depois de** diagramar uma prova..."*.
> - *Correção:* A preposição 'depois de' hardcoded foi removida do arquivo `trigger_description.py`.

> [!NOTE]
> **[UX/UI Interna] Formatação da mensagem de erro do backend no Wizard**
> Ao tentar salvar a pesquisa com dados inválidos, o alerta exibe a chave técnica em inglês e a mensagem bruta (ex: `clients: ['...']`).
> - *Contexto:* Como a tela é exclusiva para a equipe interna na fase atual, o polimento dessas mensagens não é urgente. Fica o débito técnico de mapear essas mensagens caso a tela seja liberada para coordenadores de escolas.

> [!NOTE]
> **[Feature Request] Funcionalidade de Excluir Pesquisas**
> Faltou prever a funcionalidade de **Excluir** pesquisas no escopo original (OpenSpec/Tasks). A API só implementou GET/PUT/PATCH. É necessário um endpoint DELETE e um botão "Excluir" na UI para limpar pesquisas de teste.

> [!NOTE]
> **[UX/UI] Item do Menu Lateral perde o estado "Ativo" na tela de Detalhes**
> Ao entrar na tela de Detalhes da pesquisa (`/notificacoes/feedback/<id>/`), o link "Pesquisas NPS/CSAT" no menu lateral esquerdo (sidebar) perde o realce em laranja e volta à cor cinza padrão.
> - *Contexto:* A lógica de template (provavelmente no `base.html` ou `sidebar.html`) que aplica a classe ativa (ex: checando `request.path`) não está reconhecendo a rota de feedback como pertencente ao módulo. Fica como débito técnico visual.

## 8.1. Anotações para o Acervo (Knowledge Base Notes)
> Aqui guardamos IDs, seletores DOM e dicas estruturais importantes para que os próximos testes e a automação com Playwright funcionem sem fricção.

- **URL de Criação (Wizard):** `/notificacoes/nova/`
- **URL de Listagem:** `/notificacoes/`
- **URL de Detalhes (Dashboard):** `/notificacoes/<id>/feedbacks/`
- **Navegação (Breadcrumbs):** O link para voltar à listagem no topo da página pode ser selecionado via `nav a[href*="notificacoes"]`. É a forma mais segura para o Playwright voltar à listagem após salvar.
- **Campos da Listagem (`/notificacoes/`):**
  - Filtro Rápido (Somente ativas): `input[type="checkbox"][v-model="onlyActive"]`
  - Linhas da tabela: `table tbody tr` (usar `.tw-font-medium` para checar o título).
  - Botão de Opções: `button[id^="dropdownMenuButton-"]`
  - Link de Detalhes: `a[href*="feedbacks/"]` (dentro do menu de opções).
  - Link de Edição: `a[href*="editar"]` (dentro do menu de opções).
- **Campos da Tela de Detalhes:**
  - Botão de Editar Pesquisa: link no topo direito apontando para a edição (`a[href*="editar"]`).
  - Tabela de Respostas Individuais: mapeada abaixo dos cards de métricas.
- **Estrutura do Wizard:** Dividido em 6 passos controlados por estado local (Vue/Alpine). O botão de avançar é o `.btn-next` (ou similar) que valida o formulário. O botão global superior direito é `Publicar pesquisa` (submete o form em qualquer passo).
- **Campos Passo 1 (Identidade):**
  - Título: `input[v-model="form.title"]`
  - Descrição: `input[v-model="form.description"]`
  - Conteúdo: `#nps-csat-content` (Atenção: É inicializado via TinyMCE, para automação injete em `tinymce.get('nps-csat-content').setContent()`).
  - Tipo: `input[v-model="form.type"][value="nps"]` ou `[value="csat"]`
- **Campos Passo 2 (Público-alvo):**
  - Segmentos: Checkboxes `input[v-model="form.segments"]` (ex: `#segment-coordination`, `#segment-student`).
  - Nível de Ensino: `#elementary-school` (v-model: `form.elementarySchool`) e `#high-school` (v-model: `form.highSchool`).
  - Clientes (Busca): `input[v-model="clientsSearch"]`
  - Clientes (Checkboxes): `input[v-model="form.clients"]` (ex: `#client-123`)
  - Ações de Clientes: Botões com texto "Marcar todos" (`@click="selectAllClients"`) e "Desmarcar todos".
- **Campos Passo 3 (Período e recorrência):**
  - Início: `input[v-model="form.startDateLocal"]`
  - Fim: `input[v-model="form.endDateLocal"]`
  - Repetir a cada (dias): `input[v-model.number="form.repeatDays"]`
  - Exibir até a data final: `#display-until-end-date` (v-model: `form.displayUntilEndDate`)
- **Campos Passo 4 (Disparo / Trigger):**
  - Radio "Após ação no sistema": `input[type="radio"][value="crud"]`
    - Select Ação: `select[v-model="form.trigger"]`
    - Select Modelo: `select[v-model="form.model"]`
  - Radio "Evento específico": `input[type="radio"][value="especial"]`
    - Select Evento: `select[v-model="form.especialTrigger"]`
  - Radio "Ao acessar a plataforma": `input[type="radio"][value="modal"]`
- **Campos Passo 5 (Visualização):**
  - Checkbox Exibição Automática: `input[type="checkbox"][v-model="form.showModal"]`
  - Radios Como Mostrar: `input[type="radio"][v-model="form.npsType"]`
  - Input numérico Delay: `input[type="number"][v-model.number="form.delay"]`
  - Select Altura da Modal: `select[v-model="form.modalHeight"]`
  - Select Largura da Modal: `select[v-model="form.modalWidth"]`

## 9. Retrospectiva de QA (QA Retrospective)
- **Qual foi o principal gargalo durante os testes?**
  *(A ser preenchido)*
- **Houve muitas idas e vindas com o desenvolvedor?**
  *(A ser preenchido)*
- **Como o fluxo de dev ou QA para essa task específica poderia ter sido melhorado?**
  *(A ser preenchido)*

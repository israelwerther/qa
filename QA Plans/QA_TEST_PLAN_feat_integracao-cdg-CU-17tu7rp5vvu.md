## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-11-24 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Integrations / Applications / Distribution / OMR |
| **Nível de Risco:** | Alto |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐☆ (Contrato e especificação anexados na task ClickUp `CU-17tu7rp5vvu`: `contrato-integracao-grafica.pdf`, `integracao-pageflow-especificacao.pdf`, `API-INTEGRACAO-CDG.pdf`; sem artefatos em `openspec/changes/`) |
| **Branch:** | `feat/integracao-cdg-CU-17tu7rp5vvu` |
| **Task ClickUp:** | `CU-17tu7rp5vvu` — Integração Lize <> CDG |

---

## 1. Summary of Changes (Resumo das Alterações)

- **Modelos e Configurações (`integrations`, `clients`, `applications`, `distribution`, `settings`)**:
  - Criados `PrintingPartnerIntegration` (configuração por `Client`: `is_active`, `api_key_encrypted`, `webhook_token_encrypted`, `print_models` com as 8 chaves permitidas), `PrintingOrder` (pedido 1:1 com `Application` ou `RoomDistribution`, `order_number`, `send_status`, `partner_status_id`, `partner_status_name`, `partner_status_at`, `partner_order_id`, `send_count`, `last_payload`, `last_response`, `last_error`, `warnings`) e `PrintingOrderEvent` (auditoria de `send` e `webhook`).
  - Adicionado `Unity.id_printing_partner` (`clients/migrations/0217_unity_id_printing_partner.py`) para mapear o ID opcional da unidade na gráfica.
  - Adicionado `bag_manifest` (`JSONField`, `editable=False`) em `Application` e `RoomDistribution`, gravado automaticamente na geração do malote (`omr/tasks/group_answer_sheet_files.py`, `omr/tasks/elit/group_answer_sheet_files.py`, `distribution/tasks/group_files.py`).
  - Adicionadas variáveis de ambiente em `settings.py` e `envexample.txt`: `PRINTING_PARTNER_API_BASE_URL` (vazia por padrão = desativa envio), `PRINTING_PARTNER_REQUEST_TIMEOUT` (default `30`), `PRINTING_PARTNER_DOWNLOAD_URL_EXPIRES` (default `3600`), e rota Celery `fiscallizeon.integrations.tasks.printing.*` na fila `celery-integration`.
- **Serviços e Tasks Celery (`integrations/services/printing/` e `integrations/tasks/printing.py`)**:
  - `manifest.py`: gera metadados 1:1 de cada arquivo gravado no ZIP e detecta `duplicate_paths`.
  - `payload.py`: valida elegibilidade (`get_send_block_reason`), monta `modelos_impressao` (8 chaves) e `manifesto_zip` nas 4 variações (malote por turma/sala × arquivos separados/juntos), além de normalizar `escopo='sala'` como `'turma'`.
  - `pageflow.py`: cliente HTTP `PageFlowClient.send_order` (`POST {BASE_URL}/pedidos` com `x-api-key` e tratamento de `2xx`, `4xx/5xx`, timeout e erro de rede).
  - `orders.py`: `request_send` (enfileira task após `on_commit`), `order_status` e `attach_status_json` para as telas.
- **APIs de Entrada e Saída (`integrations`, `applications`, `distribution`)**:
  - `POST /aplicacoes/api/<uuid:pk>/grafica/enviar/` e `GET /aplicacoes/api/<uuid:pk>/grafica/`.
  - `POST /ensalamento/api/ensalamentos/<uuid:pk>/grafica/enviar/` e `GET /ensalamento/api/ensalamentos/<uuid:pk>/grafica/`.
  - `GET /integracoes/api/pageflow/aplicacoes/<uuid:pk>/malote/` e `GET /integracoes/api/pageflow/ensalamentos/<uuid:pk>/malote/` (retornam `{ "url", "expires_at" }` para pedidos enviados com integração ativa, ou `404`).
  - `POST /integracoes/api/pageflow/webhook/` (valida corpo/status_id, pedido, `access_token`, ignora evento mais antigo via `data`, atualiza status e grava `PrintingOrderEvent`).
- **Frontend e Django Admin (`applications`, `distribution`, `integrations/admin.py`)**:
  - `application_list_new.html` e `distribution_list.html`: selo `"Gráfica: ..."` (`[data-test="printing-badge"]`), ação `"Enviar para gráfica"` / `"Reenviar para gráfica"` (`[data-test="printing-send"]`) condicionada à permissão `applications.can_print_bag_application`, modal de aviso de caminhos repetidos, polling automático enquanto `queued`/`sending`, e aviso (não bloqueante) ao abrir modal de impressão ou remover malote quando `inProduction` (`status_id >= 3`).
  - `print_applications_list.html`: exibição do selo `"Gráfica: ..."` (`[data-test="printing-badge"]`).
  - Django Admin: `PrintingPartnerIntegrationAdmin` (com campos cifrados `api_key` e `webhook_token`) e `PrintingOrderAdmin` (somente leitura, com inline `PrintingOrderEventInline`).
  - `ApplicationEditForm`: preservado `room_distribution` no formulário para não limpar vínculo ao editar aplicação.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### Parte 1 — Escopo Validável AGORA (Contrato de API, Mock Server & Regras no Lize)
- **Dentro do escopo atual (Parte 1):**
  - Validação integral do **contrato de API** documentado em `contrato-integracao-grafica.pdf` (Proposta v1) e `API-INTEGRACAO-CDG.pdf` (v1.0) usando um **servidor mock HTTP** apontado por `PRINTING_PARTNER_API_BASE_URL` e chamadas diretas aos endpoints do Lize.
  - Estrutura e tipagem do JSON enviado em `POST {BASE_URL}/pedidos` nas **4 variações de malote**: por turma (arquivos separados), por turma (um PDF por unidade / `malote_unidade`), por sala (arquivos separados) e por sala (arquivos juntos).
  - Correspondência 1:1 entre o ZIP real gerado e o `manifesto_zip` (soma de `n_paginas`, `path` exato, homônimos/caminhos repetidos, múltiplos cadernos por aluno no ensalamento, `unidade_id_grafica` string e `null`).
  - Rota de download `GET path_zip` (aplicação e ensalamento): `200` com `{url, expires_at}` quando enviado e `404` antes do envio ou com integração inativa.
  - Endpoint `POST /integracoes/api/pageflow/webhook/`: validação de `200` (`ignored: false` e `ignored: true`), `400`, `401`, `404` e transição de status `1..6`.
  - Comportamento das telas `application_list_new.html`, `distribution_list.html`, `print_applications_list.html` e Django Admin diante dos retornos simulados (`201`, `200`, `400`, `401/403`, `409`, `5xx`, timeout) e bloqueios (`inProduction`, cross-order Aplicação × Ensalamento, malote ELIT, malote desatualizado).
  - Preservação do vínculo `Application.room_distribution` ao editar a aplicação via `ApplicationEditForm`.

### Parte 2 — Escopo Pendente (Aguardando Implementação da Gráfica CDG / PageFlow)
- **Fora do escopo imediato / bloqueado externamente até retorno da CDG:**
  - Envio real para o ambiente de homologação/produção da CDG (`https://backend-pageflow.casadagrafica.com/api/integracao/pedidos` ou equivalente) com `x-api-key` real emitida pela gráfica.
  - Confirmação/aceite pela CDG dos **7 pontos da Seção 9** do `contrato-integracao-grafica.pdf` (especialmente malote por sala com `turno: null`, múltiplos cadernos por aluno, `malote_unidade`, caminhos repetidos e formato de `unidade_id_grafica`).
  - Download efetivo do ZIP pelos servidores do PageFlow usando `path_zip`, renovação de URL após expiração de `expires_at` e extração/impressão física dos PDFs conforme `modelos_impressao`.
  - Disparo real e automático de webhooks pelo PageFlow para o Lize em cada transição de status (`1 → 2 → 3 → 4 → 5 → 6`), incluindo política real de retentativas/backoff do PageFlow e resposta `409` real em reenvio após produção.
- **Explicitamente fora da v1 (conforme contrato):**
  - Malotes no modo `ELIT` (`MSG_ELIT` bloqueia o envio).
  - Campo opcional `modelo_impressao` por documento individual e tipos `discursiva`/`redacao` separados (na v1 ficam reservados em `modelos_impressao`).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Admin — Integração com gráfica | Django Admin ➔ Integrations ➔ Integrações com gráfica [verificar] | `/admin/integrations/printingpartnerintegration/` | `admin:integrations_printingpartnerintegration_changelist` |
| Admin — Pedidos de impressão | Django Admin ➔ Integrations ➔ Pedidos de impressão [verificar] | `/admin/integrations/printingorder/` | `admin:integrations_printingorder_changelist` |
| Admin — Unidade (`id_printing_partner`) | Django Admin ➔ Clients ➔ Unities [verificar] | `/admin/clients/unity/` | `admin:clients_unity_changelist` |
| Lista de aplicações | Aplicações ➔ Presencial / Híbrida / Lista [verificar] | `/aplicacoes/` | `applications:applications_list` |
| Lista de impressão de aplicações | Impressão de provas [verificar] | `/aplicacoes/impressao/` | `applications:print_applications_list` |
| Lista de ensalamentos | Aplicações ➔ Ensalamento | `/ensalamento/` | `distribution:distribution_list` |
| API Lize — Download do malote (Aplicação) | — (API consumida pela gráfica) | `/integracoes/api/pageflow/aplicacoes/<uuid:pk>/malote/` | `integrations:pageflow-application-bag-download` |
| API Lize — Download do malote (Ensalamento) | — (API consumida pela gráfica) | `/integracoes/api/pageflow/ensalamentos/<uuid:pk>/malote/` | `integrations:pageflow-room-distribution-bag-download` |
| API Lize — Webhook PageFlow | — (API consumida pela gráfica) | `/integracoes/api/pageflow/webhook/` | `integrations:pageflow-webhook` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Suíte Automatizada Existente na Branch

Ative a venv e execute toda a suíte da integração e geração de manifesto (com `--reuse-db`):

```bash
source venv/bin/activate && pytest \
  fiscallizeon/integrations/tests/test_printing_models.py \
  fiscallizeon/integrations/tests/test_printing_payload.py \
  fiscallizeon/integrations/tests/test_printing_send.py \
  fiscallizeon/integrations/tests/test_printing_apis.py \
  fiscallizeon/integrations/tests/test_printing_production.py \
  fiscallizeon/integrations/tests/test_printing_views.py \
  fiscallizeon/integrations/tests/test_printing_admin.py \
  fiscallizeon/omr/tests/test_group_answer_sheet_files_manifest.py \
  fiscallizeon/distribution/tests/test_group_files_manifest.py \
  --reuse-db
```

### Personas

1. **Staff / Admin Lize:** usuário `is_staff=True` e `is_superuser=True` (para configurar `PrintingPartnerIntegration` e `Unity.id_printing_partner` no `/admin/` e auditar `PrintingOrder` / `PrintingOrderEvent`).
2. **Coordenador com permissão de malote:** usuário membro de `SchoolCoordination` (`CoordinationMember`) com `applications.can_print_bag_application` (ou `is_superuser=True`) e `client.has_distribution=True` / `client_has_omr=True`.
3. **Coordenador sem permissão `can_print_bag_application`:** para validar ocultação do botão `"Enviar para gráfica"`.
4. **Sistema Parceiro (PageFlow/CDG — Mock na Parte 1 / Real na Parte 2):** consumidor anônimo das rotas `/integracoes/api/pageflow/...` portando o `access_token` no webhook.

### Pré-condições de Tenant, Flags e Ambiente

1. **Variável de ambiente obrigatória (`settings.PRINTING_PARTNER_API_BASE_URL`):**
   - Na **Parte 1 (Contrato/Mock)**, configurar `PRINTING_PARTNER_API_BASE_URL=http://127.0.0.1:9090/api/integracao` (apontando para o servidor mock local; reiniciar Django + worker Celery `celery-integration`).
   - Se `PRINTING_PARTNER_API_BASE_URL` estiver vazia (`''`), o Lize bloqueia qualquer envio com a mensagem `"Integração com a gráfica não configurada no ambiente. Fale com o suporte."`.
2. **Configuração do Tenant no Django Admin:**
   - **Integração:** `/admin/integrations/printingpartnerintegration/` ➔ criar registro vinculando o `Client`, marcar checkbox `"Ativa"` (`is_active`), preencher `"API key (x-api-key)"`, `"Token do webhook (access_token)"` e JSON `"Modelos de impressão"` com as chaves (`prova`, `gabarito`, `lista_presenca`, `randomizacao`, `pagina_customizada`, `discursiva`, `redacao`, `malote_unidade`).
   - *Sintoma visual se não houver integração ativa:* os botões `"Enviar para gráfica"` e os selos `"Gráfica: ..."` não são renderizados nas listas de aplicações e ensalamentos.
   - **ID da Unidade na Gráfica (opcional):** `/admin/clients/unity/` ➔ preencher `"ID na gráfica"` (`id_printing_partner`) em uma unidade e deixar em branco em outra (para testar `string` e `null` no `manifesto_zip`).
   - **Modo de separação do malote no `Client`:** `/admin/clients/client/` ➔ alternar `"Separação de arquivos na exportação do malote"` (`omr_print_file_separation`) entre `Arquivos separados` (`BAG_SEPARATED_FILES`) e `Padrão / Arquivos juntos` (`BAG_DEFAULT`) para cobrir as 4 variações do contrato.
   - **Flag para Ensalamento:** `/admin/clients/client/` ➔ marcar `has_distribution` para acessar `/ensalamento/` e `has_omr` (`client_has_omr`) para exibir a seção de malote no dropdown de Aplicações.

### Setup de Dados com `mixer` (Referência para Automação)

Baseado em `fiscallizeon/integrations/tests/printing_fixtures.py`:

```python
from datetime import date, time
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam
from fiscallizeon.integrations.models import PrintingPartnerIntegration
from fiscallizeon.students.models import Student

client_obj = mixer.blend(
    Client,
    omr_print_file_separation=Client.BAG_SEPARATED_FILES,
    has_distribution=True,
    has_omr=True,
    require_2fa=False,
)
integration = PrintingPartnerIntegration.objects.create(
    client=client_obj,
    is_active=True,
    print_models={
        'prova': 'PROVA_PB_FV',
        'gabarito': 'GABARITO_PB_SF',
        'lista_presenca': 'DOC_PB_SF',
        'randomizacao': 'DOC_PB_SF',
        'pagina_customizada': 'DOC_PB_SF',
        'discursiva': 'PROVA_PB_FV',
        'redacao': 'PROVA_PB_FV',
        'malote_unidade': 'MALOTE_PB_FV',
    },
)
integration.set_api_key('pk_test_123')
integration.set_webhook_token('tok-webhook')
integration.save()

unity_a = mixer.blend(Unity, client=client_obj, name='Unidade Centro', id_printing_partner='1042')
unity_b = mixer.blend(Unity, client=client_obj, name='Unidade Norte', id_printing_partner=None)
coord_a = mixer.blend(SchoolCoordination, unity=unity_a, name='EM')
coord_b = mixer.blend(SchoolCoordination, unity=unity_b, name='EM')

class_a1 = mixer.blend(SchoolClass, coordination=coord_a, name='1000A', turn=SchoolClass.MORNING)
class_b1 = mixer.blend(SchoolClass, coordination=coord_b, name='2001A', turn=SchoolClass.AFTERNOON)

coordinator = mixer.blend(User, is_active=True, is_superuser=True, email='coord@x.test')
CoordinationMember.objects.create(user=coordinator, coordination=coord_a, is_coordinator=True)

exam = mixer.blend(Exam, name='Prova Contrato CDG', random_questions=False)
exam.coordinations.add(coord_a, coord_b)

application = mixer.blend(
    Application,
    exam=exam,
    category=Application.PRESENTIAL,
    date=date(2026, 11, 20),
    start=time(8, 0),
    end=time(12, 0),
)
application.school_classes.add(class_a1, class_b1)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

> **Persona ativa na Parte 1 (exceto onde indicado):** **Coordenador** com permissão `applications.can_print_bag_application` (e **Staff/Admin** para setup e auditoria no `/admin/`).

---

### PARTE 1 — O que podemos testar AGORA (Validação do Contrato de API com Mock Server)

> **Pré-requisito de execução da Parte 1:** Subir um servidor HTTP mock (ex.: script Python/`http.server` ou Mockoon/Postman Mock) na URL configurada em `PRINTING_PARTNER_API_BASE_URL` que registre o header `x-api-key`, o JSON recebido em `POST /pedidos` e devolva respostas controladas (`201`, `200`, `400`, `401`, `409`, `500`).

---

### 5.1 Configuração no Django Admin e Pré-condições de Tenant `[Automatizável ✅]`

#### Cenário 1 — Passo Zero: Cadastro de integração, chaves cifradas, modelos de impressão e ID da unidade no Admin

**Ação humana:**
- [x] **Passo Zero (Admin):** Acessar `/admin/integrations/printingpartnerintegration/` como Staff e clicar em `"Adicionar Integração com gráfica"`.
- [x] Selecionar o `Client` de teste (`Rede Decisão`), manter `"Ativa"` marcado e preencher `"API key (x-api-key)"` (`pk_qa_teste_123`) e `"Token do webhook (access_token)"` (`tok_webhook_qa`).
- [x] No campo `"Modelos de impressão"`, testar salvar uma chave inválida (`{"invalido": "X"}`) e confirmar que o Admin bloqueia com erro listando as 8 chaves aceitas (`Chaves desconhecidas: invalido. Use: prova, gabarito, lista_presenca, randomizacao, pagina_customizada, discursiva, redacao, malote_unidade.`). ![Validação chave inválida no Admin](../evidencias/cdg-cu-17tu7rp5vvu/01-admin-validacao-chaves.png)
- [x] Preencher JSON válido com as chaves do contrato e salvar. Reabrir o registro no Admin e confirmar que os campos de senha não exibem os segredos em texto claro (apenas indicam que estão vazios para manter o valor atual) e que na listagem as colunas `"API key"` e `"Token do webhook"` mostram ícone verde (`True`). ![Listagem Admin com API key e Token ativos](../evidencias/cdg-cu-17tu7rp5vvu/02-admin-integracao-ativa.png)
- [x] Acessar `/admin/clients/unity/`, abrir uma unidade do cliente (`GRU`) e preencher `"ID na gráfica"` (`"1042"`), mantendo as demais unidades do mesmo cliente em branco.
- [ ] Acessar `/aplicacoes/` com um Coordenador **sem** a permissão `applications.can_print_bag_application` e confirmar que a opção `"Enviar para gráfica"` **não** aparece no dropdown `"Opções"` mesmo com malote gerado.

**Referência técnica (para automação):**
- URL: `/admin/integrations/printingpartnerintegration/add/`, `/admin/clients/unity/`
- Seletor: `input[name="is_active"]`, `input[name="api_key"]`, `input[name="webhook_token"]`, `textarea[name="print_models"]`, `input[name="id_printing_partner"]`, `[data-test="printing-send"]`
- Estado esperado: validação de form no Admin para chaves inválidas; `has_api_key == True`; ausência de `[data-test="printing-send"]` no DOM sem permissão `applications.can_print_bag_application`
- Fixture: `PrintingPartnerIntegration`, `Unity(id_printing_partner=...)`, `User` sem `applications.can_print_bag_application`

---

### 5.2 Contrato do Payload `POST /pedidos` e Fidelidade `ZIP × Manifesto` nas 4 Variações `[Automatizável ✅]`

#### Cenário 2 — Variação 5.1: Malote por turma — arquivos separados (com homônimos e unidade com/sem `id_printing_partner`)

**Ação humana:**
- [x] Garantir que o `Client` esteja configurado com separação `"Arquivos separados"` (`BAG_SEPARATED_FILES`) e possua duas unidades (uma com `"ID na gráfica"` preenchido — `CAV` `"2042"` — e outra em branco — `DEC` `null`), uma prova randomizada (`P6_LÍNGUA PORTUGUESA_M3_ANGLO_2026`, `a2629d58-1dd4-4be3-87ee-5aa364cccde6`) com página customizada (`Folha de rosto - Antes da lista de presença`) e dois alunos homônimos na mesma turma (`João Victor Ferreira do Nascimento` em `M2MB`).
- [x] Acessar `/aplicacoes/`, localizar a aplicação presencial/híbrida (`Simulado Geral 2026` e `P6_LÍNGUA PORTUGUESA_M3_ANGLO_2026`), abrir `"Opções"` ➔ `"Todos os alunos"` e gerar o malote (marcando cadernos, randomização e página customizada).
- [x] Após a conclusão do malote (e F5 devido ao bug registrado na Seção 7), abrir `"Opções"` e clicar em `"Enviar para gráfica"`.
- [x] Confirmar que o alerta SweetAlert de confirmação exibe o **aviso de caminhos repetidos** em vermelho listando o `path` duplicado dos alunos homônimos (`caderno_joao-victor-ferreira-do-nascimento.pdf` e `gabarito_joao-victor-ferreira-do-nascimento.pdf`), sem bloquear o envio. ![Aviso de caminhos repetidos no modal de envio](../evidencias/cdg-cu-17tu7rp5vvu/06-aviso-caminhos-repetidos.jpg) Clicar em `"Enviar"`.
- [x] Confirmar envio concluído e selo `"Gráfica: Enviado"` exibido na coluna Malote. ![Selo Gráfica: Enviado na listagem de aplicações](../evidencias/cdg-cu-17tu7rp5vvu/04-lize-selo-grafica-enviado.jpg)
- [x] **Conferência do Contrato no Mock (`Pedido #1848` — `5032175f-...` e `Pedido #1849` — `a2629d58-...`):** Inspecionar as requisições capturadas no mock (`POST /pedidos`): ![Mock validando contrato e ZIP 1:1](../evidencias/cdg-cu-17tu7rp5vvu/05-mock-contrato-zip-ok.jpg)
  - [x] Header `Content-Type: application/json` e `x-api-key` igual à chave cadastrada (`pk_qa_teste_123`).
  - [x] Raiz contém exatamente: `path_zip`, `id_aplicacao` (`5032175f-...` e `a2629d58-...`), `data_aplicacao` (`2026-12-10` / `2026-12-12`), `n_paginas` (`9` / `34`), `modelos_impressao` (todas as 8 chaves) e `manifesto_zip` (array).
  - [x] No `manifesto_zip`: unidade com `"ID na gráfica"` preenchido (`GRU` `"1042"`, `CAV` `"2042"`) envia `unidade_id_grafica` como string; unidade sem ID (`DEC`) envia `null` no mesmo pedido.
  - [x] Cada turma tem `nome` (`F1MA`, `M3MB`, `M2MB`), `turno` (`Manhã`), `modelo: null`, `documentos[]` (`lista_presenca`, `randomizacao`, `pagina_customizada`) e `alunos[]` com `nome`, `matricula` e `documentos[]` (`gabarito` e `prova` com `escopo: "aluno"`).
  - [x] Baixar o ZIP gerado e conferir **1:1**: Pedido `#1848` (`954.325 bytes`, `9` entradas) e Pedido `#1849` (`4.937.339 bytes`, `18` entradas) com `path` idêntico 1:1 ao `manifesto_zip`, `n_paginas` raiz (`9` / `34`) = soma exata dos documentos e contagem real de páginas (`PyPDF2`) batendo como multiconjunto *(obs.: nos dois homônimos `João Victor Ferreira do Nascimento` com provas randomizadas de 3 e 4 páginas, a ordem dentro do ZIP vem por ordem de geração enquanto no JSON os alunos vêm ordenados por matrícula — registrado na Seção 8)*.

**Referência técnica (para automação):**
- URL: `/aplicacoes/`, `POST /aplicacoes/api/<uuid:pk>/grafica/enviar/`
- Seletor: `[data-test="printing-send"]`, `[data-test="printing-badge"]`, `.swal2-confirm:has-text("Enviar")`
- Estado esperado: `POST` no mock com status `201`; JSON aderente às seções 4.1–4.7 e 5.1 do `contrato-integracao-grafica.pdf`
- Fixture: `Client(omr_print_file_separation=Client.BAG_SEPARATED_FILES)`, 2 `Unity`, 2 `Student` homônimos, `Exam(random_questions=True)`

---

#### Cenário 3 — Variação 5.2: Malote por turma — arquivos juntos (`malote_unidade`)

**Ação humana:**
- [ ] Alterar o `Client` para separação padrão (`BAG_DEFAULT` — um PDF por unidade) e gerar novamente o malote da aplicação em `/aplicacoes/`.
- [ ] Clicar em `"Opções"` ➔ `"Enviar para gráfica"` (ou `"Reenviar para gráfica"`).
- [ ] **Conferência do Contrato no Mock:** Inspecionar o JSON capturado em `POST /pedidos`:
  - [ ] Cada item de `manifesto_zip` possui `turmas: []` (array vazio).
  - [ ] Cada item de `manifesto_zip` possui `documentos: [{ "tipo_documento": "malote_unidade", "escopo": "unidade", "path": "...", "n_paginas": <int> }]`.
  - [ ] O `path` corresponde exatamente ao PDF único da unidade dentro do ZIP e `n_paginas` da raiz soma os PDFs das unidades.

**Referência técnica (para automação):**
- URL: `/aplicacoes/`, `POST /aplicacoes/api/<uuid:pk>/grafica/enviar/`
- Seletor: `[data-test="printing-send"]`, `.swal2-confirm`
- Estado esperado: `turmas == []` e `documentos[0].tipo_documento == "malote_unidade"` e `escopo == "unidade"`
- Fixture: `Client(omr_print_file_separation=Client.BAG_DEFAULT)`

---

#### Cenário 4 — Variação 5.3: Malote por sala (Ensalamento) — arquivos separados com múltiplas provas por aluno

**Ação humana:**
- [ ] Configurar `Client` em `"Arquivos separados"` (`BAG_SEPARATED_FILES`) e criar um **Ensalamento** em `/ensalamento/` reunindo **2 aplicações** no mesmo dia com um aluno alocado nas duas provas na mesma sala.
- [ ] Na tela `/ensalamento/`, abrir `"Opções"` ➔ `"Imprimir malote"`, marcar `"Incluir cadernos de prova"` e gerar o malote do ensalamento.
- [ ] Após gerar o malote, abrir `"Opções"` ➔ clicar em `"Enviar para gráfica"` e confirmar no modal.
- [ ] **Conferência do Contrato no Mock:** Inspecionar o JSON capturado em `POST /pedidos`:
  - [ ] `id_aplicacao` é o UUID do `RoomDistribution` e `path_zip` aponta para `/integracoes/api/pageflow/ensalamentos/<uuid>/malote/`.
  - [ ] Em `manifesto_zip[].turmas[]`, cada sala aparece como item com `nome` = nome da sala, `turno: null`, `modelo: null`.
  - [ ] Os documentos da sala (`lista_presenca`, `gabarito`, etc.) vêm com `"escopo": "turma"` (não `"sala"`, conforme contrato seção 4.6).
  - [ ] O aluno que realiza 2 provas aparece **uma única vez** em `alunos[]` com **dois itens** `"tipo_documento": "prova"` em `alunos[].documentos[]` (um por caderno).
  - [ ] Conferência 1:1 com o ZIP do ensalamento e soma de `n_paginas`.

**Referência técnica (para automação):**
- URL: `/ensalamento/`, `POST /ensalamento/api/ensalamentos/<uuid:pk>/grafica/enviar/`
- Seletor: `[data-test="printing-send"]`, `[data-test="printing-badge"]`
- Estado esperado: `escopo == "turma"` nos documentos de sala; `len(aluno['documentos']) == 2` para aluno com 2 provas; `turno is None`
- Fixture: `RoomDistribution` com 2 `Application` na mesma data e aluno presente nas duas

---

#### Cenário 5 — Variação 5.4: Malote por sala (Ensalamento) — arquivos juntos (`malote_unidade`)

**Ação humana:**
- [ ] Com o `Client` em `BAG_DEFAULT`, regerar o malote do ensalamento em `/ensalamento/` e clicar em `"Enviar para gráfica"` / `"Reenviar para gráfica"`.
- [ ] **Conferência do Contrato no Mock:** Confirmar que `manifesto_zip[]` traz `turmas: []` e `documentos` com `tipo_documento: "malote_unidade"` e `escopo: "unidade"`, batendo 1:1 com o ZIP gerado.

**Referência técnica (para automação):**
- URL: `/ensalamento/`
- Seletor: `[data-test="printing-send"]`
- Estado esperado: `manifesto_zip[i].turmas == []` e `documentos[0].tipo_documento == "malote_unidade"`
- Fixture: `RoomDistribution` + `Client(omr_print_file_separation=Client.BAG_DEFAULT)`

---

### 5.3 Contrato da Rota de Download (`GET path_zip`) `[Automatizável ✅]`

#### Cenário 6 — Retorno válido (`200`) e proteção (`404`) nas rotas de download de Aplicação e Ensalamento

**Ação humana:**
- [ ] Executar um `GET` (via curl/Postman/Insomnia, sem header de sessão) na rota `/integracoes/api/pageflow/aplicacoes/<uuid>/malote/` de uma aplicação que **ainda não** foi enviada à gráfica e confirmar retorno `404 Not Found`.
- [x] Após enviar essa aplicação no Cenário 2 (`5032175f-4925-426b-a2c3-fb41851defeb`), executar o mesmo `GET` usando exatamente a URL recebida no campo `path_zip` do mock.
- [x] Confirmar resposta `200 OK` com JSON contendo exatamente `{"url": "<url_assinada>", "expires_at": "2026-11-24T12:26:12Z"}`.
- [x] Fazer download pela `url` retornada e confirmar que o arquivo `.zip` (`954.325 bytes`, `9` entradas) é íntegro e idêntico ao malote da aplicação.
- [ ] Repetir o `GET` para a rota `/integracoes/api/pageflow/ensalamentos/<uuid>/malote/` de um ensalamento enviado (Cenário 4) e confirmar `200 OK` + download íntegro.
- [ ] Desmarcar `"Ativa"` na `PrintingPartnerIntegration` no Admin e repetir o `GET` em `path_zip`: confirmar retorno `404 Not Found`. Reativar em seguida.

**Referência técnica (para automação):**
- URL: `GET /integracoes/api/pageflow/aplicacoes/<uuid:pk>/malote/` e `GET /integracoes/api/pageflow/ensalamentos/<uuid:pk>/malote/`
- Seletor: API HTTP direta (sem DOM)
- Estado esperado: `200` com chaves `url` e `expires_at` em UTC ISO-8601 terminado em `Z` quando enviado e ativo; `404` caso contrário
- Fixture: `PrintingOrder(send_count__gt=0)` vs sem `PrintingOrder`

---

### 5.4 Contrato do Webhook (`POST /integracoes/api/pageflow/webhook/`) e Bloqueios na UI `[Automatizável ✅]`

#### Cenário 7 — Validações de erro do Webhook (`400`, `401`, `404`) e eventos fora de ordem (`ignored: true`)

**Ação humana:**
- [x] Enviar `POST /integracoes/api/pageflow/webhook/` com corpo sem `json.numero_pedido` ou com `status_id: "abc"` ➔ confirmado `400 Bad Request` (`{"ok": false, "detail": "Corpo inválido."}`). ![Webhook HTTP 400 e status 5 no Mock](../evidencias/cdg-cu-17tu7rp5vvu/08-webhook-http-400-e-status-5.jpg)
- [x] Enviar com `numero_pedido` inexistente (UUID aleatório) ➔ confirmado `404 Not Found` (`{"ok": false, "detail": "Pedido não encontrado."}`).
- [x] Enviar com `numero_pedido` válido (igual ao `id_aplicacao` enviado) e `access_token` incorreto ➔ confirmado `401 Unauthorized` (`{"ok": false, "detail": "Token inválido."}`).
- [x] Enviar com `access_token` correto (`tok_webhook_qa`), `status_id: 2` (e `1..5` no Pedido `#1849`), `casa_grafica_id: "1849"` e `data` recente ➔ confirmado `200 OK` com `{"ok": true, "ignored": false}`.
- [x] Enviar novamente um evento com `data` **anterior** à do evento já salvo (`-120 min`, `status_id: 1`) ➔ confirmado `200 OK` com `{"ok": true, "ignored": true}` e verificado na UI que o selo permaneceu verde (`Gráfica: Enviado`), sem regredir. ![Selo verde Gráfica: Enviado sem regressão](../evidencias/cdg-cu-17tu7rp5vvu/09-lize-selo-verde-enviado.jpg)

**Referência técnica (para automação):**
- URL: `POST /integracoes/api/pageflow/webhook/`
- Seletor: API HTTP direta + `[data-test="printing-badge"]`
- Estado esperado: `400`/`401`/`404` conforme tabela da seção 8 do contrato; `{"ok": true, "ignored": true}` para `occurred_at < order.partner_status_at`
- Fixture: `PrintingOrder` enviado com `webhook_token` conhecido

---

#### Cenário 8 — Transição de status (`1 → 2 → 3 → 5`) no Webhook, reflexo nas 3 telas e bloqueio/aviso de produção

**Ação humana:**
- [ ] Com status `2` (`Aguardando Aprovação`): verificar em `/aplicacoes/` (ou `/ensalamento/`) e em `/aplicacoes/impressao/` que o selo exibe `"Gráfica: Aguardando Aprovação"` e que `"Reenviar para gráfica"` permanece habilitado e funcional.
- [x] Disparar webhook com `status_id: 3`, `status: "Em Produção"`, `data` posterior (Pedido `#1848`).
- [ ] Recarregar `/aplicacoes/`, `/aplicacoes/impressao/` e `/ensalamento/`:
  - [x] Confirmado em `/aplicacoes/` que o selo muda para destaque laranja com texto `"Gráfica: Em Produção"` (pendente conferir `/aplicacoes/impressao/` e `/ensalamento/`). ![Selo laranja Gráfica: Em Produção](../evidencias/cdg-cu-17tu7rp5vvu/10-lize-selo-laranja-em-producao.jpg)
  - [x] Em `/aplicacoes/`, abrir `"Opções"` e verificar que `"Reenviar para gráfica"` aparece visualmente esmaecido (`opacity-50`, cursor `not-allowed`) *(falta conferir em `/ensalamento/`)*.
  - [x] Clicar em `"Reenviar para gráfica"` quando bloqueado: reproduzido o bug `bproductionWarning` — o modal `"Não é possível enviar"` abriu **sem texto explicativo** (`11-bug-modal-bloqueio-sem-texto.jpg`, registrado como `[BUG]` na Seção 7).
  - [ ] Tentar enviar `POST` direto para `/aplicacoes/api/<uuid>/grafica/enviar/` e confirmar `400 Bad Request` com mensagem `"A gráfica já está produzindo este pedido (Em Produção). Não é possível reenviar."`.
  - [ ] Clicar em `"Todos os alunos"` (para regerar malote) ou `"Remover malote gerado"`: confirmar que aparece o modal de **aviso** `"A gráfica já está produzindo"` com opções `"Continuar mesmo assim"` e `"Cancelar"`, permitindo prosseguir ao confirmar (sem travar o malote no Lize, conforme contrato seção 8).
  - [ ] Se o malote for regerado após o envio, confirmar que `"Enviar/Reenviar para gráfica"` passa a exigir nova geração (caso `bag_manifest` fique dessincronizado) ou bloqueia reenvio se já em produção.
- [x] Disparar webhook com `status_id: 5`, `status: "Enviado"`, `data` posterior (Pedido `#1849`) e confirmado que o selo muda para estilo verde `"Gráfica: Enviado"` (`09-lize-selo-verde-enviado.jpg`).

**Referência técnica (para automação):**
- URL: `/aplicacoes/`, `/aplicacoes/impressao/`, `/ensalamento/`
- Seletor: `[data-test="printing-badge"]`, `[data-test="printing-send"]`, `.swal2-title:has-text("A gráfica já está produzindo")`
- Estado esperado: `statusId >= 3` aplica classe laranja e `canSend === false`; `statusId >= 5` aplica classe verde; `POST .../grafica/enviar/` retorna HTTP `400`
- Fixture: `PrintingOrder` com `partner_status_id` atualizado via webhook

---

#### Cenário 9 — Bloqueios de negócio: cross-order (Aplicação × Ensalamento), malote ELIT, aplicação online e preservação no `ApplicationEditForm`

**Ação humana:**
- [ ] **Cross-order:** Enviar um **Ensalamento** para a gráfica (Cenário 4) e colocá-lo em `status_id: 3` via webhook. Acessar `/aplicacoes/`, localizar uma aplicação participante desse ensalamento, gerar malote individual dela e confirmar que o selo mostra `"Gráfica: Em Produção (ensalamento)"` e o envio individual é bloqueado (`400` com `"Esta aplicação já foi enviada à gráfica pelo ensalamento de ..."`). Testar também o caminho inverso (aplicação enviada individualmente bloqueando o envio do ensalamento).
- [ ] **Malote ELIT:** Gerar um malote ELIT em `/aplicacoes/` (se aplicável ao cliente) e confirmar que a API `/grafica/enviar/` bloqueia com `400` (`"Malote ELIT não é enviado à gráfica nesta versão."`).
- [ ] **Preservação de `room_distribution` no Edit Form:** Pegar uma aplicação vinculada a um ensalamento, acessar `/aplicacoes/<uuid>/editar`, alterar qualquer campo (ex.: observação/horário) e salvar. Confirmar no banco/ensalamento que a aplicação **não** perdeu o vínculo com `room_distribution`.

**Referência técnica (para automação):**
- URL: `/aplicacoes/`, `/ensalamento/`, `/aplicacoes/<uuid:pk>/editar`
- Seletor: `[data-test="printing-badge"]`, `form button[type="submit"]`
- Estado esperado: `inProductionByOtherOrder === true` na UI; `POST` retorna `400` com `MSG_SENT_BY_ROOM_DISTRIBUTION` / `MSG_SENT_INDIVIDUALLY` / `MSG_ELIT`; `application.room_distribution_id` preservado após POST de edição
- Fixture: `RoomDistribution` + `Application` vinculada

---

### 5.5 Tratamento de Respostas de Erro da Gráfica e Auditoria no Admin `[Automatizável ✅]`

#### Cenário 10 — Respostas `400`, `401/403`, `409`, `500` e Timeout no Mock + Auditoria (`PrintingOrder` / `PrintingOrderEvent`)

**Ação humana:**
- [ ] Configurar o mock para retornar `400` com `{"sucesso": false, "mensagem": "Campo inválido no teste"}` e disparar envio na UI.
- [ ] Confirmar que o selo atualiza para vermelho `"Gráfica: erro no envio"` (se primeiro envio) ou `"Gráfica: erro no reenvio"` (se já tinha status anterior) e o `title`/tooltip exibe a mensagem retornada pela gráfica.
- [ ] Repetir simulando no mock: `401`, `409` (`{"sucesso": false, "mensagem": "Já em produção", "codigo": "PEDIDO_EM_PRODUCAO"}`), `500` e timeout (> `PRINTING_PARTNER_REQUEST_TIMEOUT`).
- [ ] **Auditoria no Admin:** Acessar `/admin/integrations/printingorder/`, abrir o pedido e confirmar:
  - [ ] Todos os campos do pedido estão **somente leitura** (sem botão Salvar/Adicionar).
  - [ ] `Último payload` e `Última resposta` contêm respectivamente o JSON enviado e o retorno do mock.
  - [ ] Na tabela inline `"Eventos de pedidos de impressão"`, existem registros cronológicos de `Envio` (`http_status`, `correlation_id`, `ok`) e `Webhook` (`status_id`, `status_name`, `occurred_at`).

**Referência técnica (para automação):**
- URL: `/admin/integrations/printingorder/<uuid:pk>/change/`
- Seletor: `[data-test="printing-badge"]`, `#printingorder_form`, `.inline-group` (`PrintingOrderEventInline`)
- Estado esperado: `send_status == 'error'` quando mock retorna `>= 400` ou timeout; `PrintingOrderAdmin` sem `has_add_permission` e sem `has_change_permission`; `PrintingOrderEvent` registrado para cada tentativa
- Fixture: Mock HTTP retornando `400`/`401`/`409`/`500` e sleep > timeout

---

### PARTE 2 — O que AINDA NÃO podemos testar (Aguardando Implementação da Gráfica CDG / PageFlow)

> **Condição de desbloqueio:** Executar esta Parte 2 somente após a equipe da CDG/PageFlow confirmar que implementou o contrato `contrato-integracao-grafica.pdf`, fornecer a `BASE_URL` real (homologação/produção), `x-api-key` de teste, `access_token` de webhook e cadastrar a URL do webhook do Lize.

---

### 5.6 Envio Real (`POST {BASE_URL_REAL}/pedidos`) e Validação dos 7 Pontos do Manifesto pela CDG `[Apenas Manual 👁]`

#### Cenário 11 — Aceite real do payload pelo servidor PageFlow/CDG e confirmação dos 7 pontos da Seção 9 do contrato

**Ação humana:**
- [ ] Atualizar `PRINTING_PARTNER_API_BASE_URL` no ambiente de homologação/dev para a URL real informada pela CDG e cadastrar `x-api-key` + `webhook_token` reais no `/admin/integrations/printingpartnerintegration/`.
- [ ] Disparar um pedido real de **Malote por Turma (arquivos separados)** e confirmar resposta `201 Created` real com `pedido_id`, `numero_pedido` e `correlationId` salvos em `/admin/integrations/printingorder/`.
- [ ] Validar junto à equipe da CDG (conforme Seção 9 de `contrato-integracao-grafica.pdf`) que o parser deles processou corretamente:
  - [ ] **Ponto 1:** Estrutura `unidade -> turmas -> alunos -> documentos`, com `documentos` também no nível de turma.
  - [ ] **Ponto 2:** **Malote por sala** enviado com cada sala em `turmas[]` e `turno: null`.
  - [ ] **Ponto 3:** **Vários cadernos por aluno** no malote por sala (aluno único com N documentos `prova`).
  - [ ] **Ponto 4:** **Um PDF por unidade** (`turmas: []` e `documentos` na unidade com `tipo_documento: "malote_unidade"`).
  - [ ] **Ponto 5:** Uso do `path` exato (normalizado pelo Lize) sem tentar reconstruí-lo via `unidade_name` ou `nome`.
  - [ ] **Ponto 6:** Tratamento de **caminhos repetidos** (homônimos) sem falha de ingestão.
  - [ ] **Ponto 7:** Tratamento de `unidade_id_grafica` (string vs `null` quando a unidade ainda não existe na gráfica).
- [ ] Validar que `modelos_impressao` (ex.: `PROVA_PB_FV`, `GABARITO_PB_SF`, `DOC_PB_SF`) bate 100% com os SKUs/produtos reais cadastrados no PageFlow para o cliente piloto.

**Referência técnica (para automação):**
- URL: `{PRINTING_PARTNER_API_BASE_URL}/pedidos`
- Seletor: `/admin/integrations/printingorder/<uuid:pk>/change/` (inspeção de `last_response` e `partner_order_id`)
- Estado esperado: HTTP `201` real no `PrintingOrderEvent`; confirmação da CDG sobre os 7 itens da Seção 9
- Fixture: Cliente piloto real em homologação com `x-api-key` e códigos `print_models` reais da CDG

---

### 5.7 Download Real do ZIP pela CDG via `path_zip` e Conferência Física de Impressão `[Apenas Manual 👁]`

#### Cenário 12 — Fluxo real `path_zip` → URL assinada S3/Storage → extração e impressão na gráfica

**Ação humana:**
- [ ] Confirmar nos logs do Lize e com a equipe da CDG que o PageFlow realizou `GET` na URL `path_zip` enviada no pedido, recebeu `{ "url", "expires_at" }` e concluiu o download do `.zip` sem erro de TLS, CORS, permissão ou URL expirada.
- [ ] Simular/aguardar expiração de `expires_at` (ou solicitar nova chamada pela CDG) e confirmar que uma nova chamada `GET` em `path_zip` devolve nova URL assinada válida.
- [ ] Conferir junto ao operador/equipe CDG os arquivos extraídos por unidade/turma/sala/aluno e o modelo de impressão associado a cada `tipo_documento` (capa/caderno frente-verso, gabarito sem frente-verso, listas/páginas customizadas).

**Referência técnica (para automação):**
- URL: `GET /integracoes/api/pageflow/aplicacoes/<uuid:pk>/malote/` ou `.../ensalamentos/<uuid:pk>/malote/`
- Seletor: Logs de acesso do backend + confirmação operacional CDG
- Estado esperado: HTTP `200` nos logs para requisição originada do IP/serviço PageFlow; download completo do `.zip` no storage
- Fixture: Pedido real criado no Cenário 11

---

### 5.8 Ciclo Real de Webhooks Disparados pelo PageFlow e Reenvio em Produção (`409`) `[Apenas Manual 👁]`

#### Cenário 13 — Transição real no painel da gráfica (`1 → 2 → 3 → 4 → 5 → 6`), reenvio real (`200` vs `409`) e retries

**Ação humana:**
- [ ] Com o pedido recém-criado no PageFlow (status `1 — Pedido Recebido` ou `2 — Aguardando Aprovação`), regerar o malote no Lize e clicar em `"Reenviar para gráfica"`, confirmando que a CDG aceita o update idempotente pelo mesmo `id_aplicacao` e responde `200 OK`.
- [ ] Solicitar que a equipe da CDG avance o pedido no painel do PageFlow para `3 — Em Produção`, `4 — Pronto para Envio`, `5 — Enviado` e `6 — Entregue`, verificando a chegada automática de cada webhook no `/admin/integrations/printingorder/` e a atualização do selo na UI do Lize em até 10s por transição.
- [ ] Confirmar que, quando o pedido está em `Em Produção` no PageFlow, qualquer tentativa de reenvio (se forçada contra a API da gráfica) recebe `409 Conflict` (`PEDIDO_EM_PRODUCAO`) conforme Seção 2 do contrato.
- [ ] *(Opcional em homologação)* Validar comportamento de retry/backoff do PageFlow quando o endpoint do Lize estiver temporariamente indisponível.

**Referência técnica (para automação):**
- URL: `POST /integracoes/api/pageflow/webhook/`, `/admin/integrations/printingorder/`
- Seletor: `[data-test="printing-badge"]`, inline `PrintingOrderEventInline`
- Estado esperado: Eventos `WEBHOOK` criados automaticamente pelo PageFlow com `ok=True` e `http_status` 200 registrado no lado da CDG
- Fixture: Pedido real em homologação com `webhook_url` do Lize cadastrada no PageFlow

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Resolução intermediária (1333×1080) e mobile/tablet:** Verificar em `/aplicacoes/`, `/aplicacoes/impressao/` e `/ensalamento/` que o selo `"Gráfica: ..."` (`[data-test="printing-badge"]`) não quebra a coluna de malote, não vaza sobre botões vizinhos e o tooltip (`title`) fica legível.
- [ ] **Dropdown de ações:** Verificar alinhamento do item `"Enviar para gráfica"` / `"Reenviar para gráfica"` com o ícone de impressora em `/aplicacoes/` e `/ensalamento/`, incluindo estado visual desabilitado (`tw-opacity-50 tw-cursor-not-allowed`) quando `canSend === false`.
- [ ] **Modais SweetAlert:** Validar quebra de linha (`word-break: break-all`) da lista de caminhos repetidos no modal de confirmação quando houver homônimos com caminhos longos, e verificar leitura do modal `"A gráfica já está produzindo"` ao tentar gerar/remover malote com `status_id >= 3`.
- [ ] **Console do navegador (`F12`):** Garantir zero erros `Uncaught TypeError` / `ReferenceError` no console ao carregar e interagir com `/aplicacoes/`, `/aplicacoes/impressao/` e `/ensalamento/` (com e sem integração ativa).

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!BUG]
> **[UX/UI] Botão `"Enviar para gráfica"` fica desabilitado logo após gerar o malote até recarregar a página (F5)**
> - **Title:** `printingOrder.canSend` permanece `false` após conclusão assíncrona da geração do malote em Aplicações e Ensalamento
> - **Context/Root Cause:** Quando o polling da geração do malote termina com `SUCCESS` em `fiscallizeon/applications/templates/dashboard/applications/application_list_new.html` (`fetchStatus`, L.2497–2501) e `fiscallizeon/distribution/templates/distribution/distribution_list.html` (`fetchDistibutionStatus`, L.926–932), o JS atualiza `application.answerSheetUrl` / `distribution.examsBagLink` (fazendo o botão `"Enviar para gráfica"` aparecer no menu), mas **não** consulta `printing_order_status` (`GET .../grafica/`) para atualizar `printingOrder` (`canSend`, `warnings`, `blockReason`). O mesmo ocorre se o malote for regerado enquanto `printingOrder` tinha `blockReason` de manifesto desatualizado.
> - **Expected Behavior:** Assim que a exportação do malote retornar `SUCCESS` (e também ao remover o malote), o frontend deve chamar `axios.get(item.urls.printing_order_status)` para atualizar `item.printingOrder`, habilitando `"Enviar para gráfica"` imediatamente sem exigir F5.
> - **Workaround (Gambiarra temporária):** Recarregar a página (`F5`) após a geração do malote para que o backend re-injete `printing_status_json` atualizado (`canSend: true`).
> - **Evidência:** ![Botão Enviar para gráfica desabilitado logo após geração sem F5](../evidencias/cdg-cu-17tu7rp5vvu/03-bug-enviar-desabilitado-sem-f5.jpg)

> [!BUG]
> **[UX/UI] Modal `"Não é possível enviar"` e tooltip ficam sem texto (`order.bproductionWarning` inexistente nos templates de Aplicações e Ensalamento)**
> - **Title:** Modal e tooltip de bloqueio de envio exibem mensagem vazia (`undefined`) quando `canSend === false`
> - **Context/Root Cause:** No backend (`fiscallizeon/integrations/services/printing/orders.py`, método `order_status`, L.374), a chave retornada no JSON é `'blockReason'`. Porém, nos templates `fiscallizeon/applications/templates/dashboard/applications/application_list_new.html` (L.560 e L.2206) e `fiscallizeon/distribution/templates/distribution/distribution_list.html` (L.319 e L.1054), o Vue referencia `printingOrder.bproductionWarning` (typo provável de substituição de `blockReason` por `productionWarning`).
> - **Expected Behavior:** Ao passar o mouse ou clicar em `"Enviar para gráfica"` / `"Reenviar para gráfica"` quando `canSend === false` (ex.: pedido já em produção, malote desatualizado, cross-order ou URL da API não configurada), o tooltip e o alerta SweetAlert `"Não é possível enviar"` deveriam exibir `order.blockReason` (ex.: `"A gráfica já está produzindo este pedido (Em Produção). Não é possível reenviar."`).
> - **Workaround (Gambiarra temporária):** Validar a mensagem real de bloqueio diretamente na resposta da API `GET /aplicacoes/api/<uuid>/grafica/` (`blockReason`) ou `POST .../grafica/enviar/` (`detail`), e reportar ao dev para corrigir `bproductionWarning` ➔ `blockReason` nos dois templates antes do merge/produção.
> - **Evidência:** ![Modal Não é possível enviar sem texto explicativo](../evidencias/cdg-cu-17tu7rp5vvu/11-bug-modal-bloqueio-sem-texto.jpg)

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[UX / Desambiguação de Homônimos no ZIP]** Na v1, alunos homônimos na mesma turma geram caminhos idênticos dentro do ZIP (ex.: `caderno_joao-victor-ferreira-do-nascimento.pdf`), o que exige que a gráfica leia as entradas do ZIP sem sobrescrever arquivos em disco e exibe apenas um aviso ao coordenador (`06-aviso-caminhos-repetidos.jpg`). Além disso, no Pedido `#1849` observou-se que os dois homônimos possuem versões randomizadas com quantidades de páginas diferentes (3 e 4 páginas): como `alunos[]` no manifesto é ordenado por `(nome, matricula)` enquanto as entradas do ZIP seguem a ordem de geração, não há como a gráfica saber qual das duas entradas repetidas no ZIP pertence a qual matrícula apenas pelo `path`. Como melhoria futura, incluir a matrícula ou sufixo único no nome do arquivo dentro do ZIP para eliminar colisões e ambiguidade. ![Divergência de ordem entre ZIP e manifesto em homônimos](../evidencias/cdg-cu-17tu7rp5vvu/07-mock-homonimos-ordem-zip.jpg) Além disso, no modal de aviso de caminhos repetidos, ajustar `overflow-wrap: anywhere` / formatação da lista para evitar quebra no meio de palavras curtas (ex.: `f-erreira`) e avaliar o comportamento legado de `safe_string` que remove vogais acentuadas (ex.: `Ensino_Mdio`).

> [!NOTE]
> **[UX / Operação — ID da Unidade na Gráfica]** O campo `Unity.id_printing_partner` (`"ID na gráfica"`) está exposto apenas no Django Admin (`/admin/clients/unity/`). Embora atenda à v1 (operação pela equipe Lize conforme `contrato-integracao-grafica.pdf` seção 4.3), como melhoria futura pode ser exposto no cadastro de unidades do dashboard ou sincronizado automaticamente caso o PageFlow forneça endpoint.

> [!NOTE]
> **[Scope Gap / v2 do Contrato]** Suporte a `modelo_impressao` granular por documento individual (previsto inicialmente na descrição do card para `redacao`/`discursiva`, mas explicitamente postergado na seção 4.2 do `contrato-integracao-grafica.pdf` v1) e suporte a malotes `ELIT`.

> [!NOTE]
> **[Melhoria de QA / Ferramental]** Criar um comando/script local reutilizável de mock PageFlow (ou coleção Postman/Bruno) versionado para validar o contrato `contrato-integracao-grafica.pdf` automaticamente sempre que o gerador de malote (`omr`/`distribution`) ou `payload.py` for alterado.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Ver Mapeamento de Tela — application_list_new.html](docs/tests/usability/application_list_new.md)**
- 🔗 **[Ver Mapeamento de Tela — distribution_list.html](docs/tests/usability/distribution_list.md)**
- 🔗 **[Ver Mapeamento de Tela — print_applications_list.html](docs/tests/usability/print_applications_list.md)**

### Snippet de Automação (Setup via Mixer + Playwright — Parte 1 com Mock)

```python
import json
from datetime import date, time
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam
from fiscallizeon.integrations.models import PrintingPartnerIntegration

# 1. Setup do Tenant e Integração Gráfica
client_obj = mixer.blend(
    Client,
    omr_print_file_separation=Client.BAG_SEPARATED_FILES,
    has_distribution=True,
    has_omr=True,
    require_2fa=False,
)
integration = PrintingPartnerIntegration.objects.create(
    client=client_obj,
    is_active=True,
    print_models={'prova': 'PROVA_PB_FV', 'gabarito': 'GABARITO_PB_SF'},
)
integration.set_api_key('pk_test_123')
integration.set_webhook_token('tok-webhook')
integration.save()

unity = mixer.blend(Unity, client=client_obj, name='Unidade Centro', id_printing_partner='1042')
coordination = mixer.blend(SchoolCoordination, unity=unity, name='EM')
school_class = mixer.blend(SchoolClass, coordination=coordination, name='1000A', turn=SchoolClass.MORNING)
coordinator = mixer.blend(User, is_active=True, is_superuser=True, email='coord_cdg@lize.local')
coordinator.set_password('123456')
coordinator.save()
CoordinationMember.objects.create(user=coordinator, coordination=coordination, is_coordinator=True)

# 2. Playwright (Exemplo de validação do botão e selo em /aplicacoes/)
# page.goto(f"{live_server.url}/aplicacoes/")
# page.locator('button[id^="dropdownMenuButton-"]').first.click()
# page.locator('[data-test="printing-send"]').first.click()
# page.locator('.swal2-confirm:has-text("Enviar")').click()
# expect(page.locator('[data-test="printing-badge"]').first).to_contain_text("Gráfica:")
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Qual foi o principal gargalo durante os testes?** *(Preencher após execução — ex.: dependência externa da CDG/PageFlow para a Parte 2)*
- **Houve muito vai-e-vem com o desenvolvedor?** *(Preencher após execução)*
- **Como o fluxo de desenvolvimento ou QA desta task poderia ter sido melhorado?** *(Preencher após execução)*

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- Para features de integração externa com dependência de terceiros ainda não entregue, estruturar nativamente a Seção 5 em **Parte 1 (Contrato / Mock Server)** e **Parte 2 (E2E Externo)** evita bloquear a validação do lado Lize e já deixa o roteiro de homologação pronto para quando o parceiro liberar o ambiente.


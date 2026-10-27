# QA Test Plan: Integração SSO LEX — Logar na Lize (CU-86akbfeqf)

## 0. Metadata (Metadados de QA)

| Campo                      | Valor                                                                                                                                                                                                                                                                                                                                        |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data:**                  | 2026-10-26                                                                                                                                                                                                                                                                                                                                   |
| **Natureza da Tarefa:**    | `[Business Feature]`                                                                                                                                                                                                                                                                                                                         |
| **Área da Feature:**       | Integrations / SSO (LEX — Conexia)                                                                                                                                                                                                                                                                                                           |
| **Nível de Risco:**        | Médio                                                                                                                                                                                                                                                                                                                                        |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5/5) — proposal.md, design.md, spec.md (lex-sso-auth, lex-sso-config, lex-sso-logout) e integration-flow.md presentes em `openspec/changes/lex-sso-integration-86akbfeqf/`. Todos os requisitos, cenários e decisões técnicas estão cobertos, incluindo cenários de falha, configuração ausente e ausência de rota `/complete/`. |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend (lizeedu — app `integrations`)

- **Modelo `IntegrationLex`** (`fiscallizeon/integrations/models.py`): herda `BaseModel`; campos `code` (TextField), `user_integrated` (FK opcional para `User`, `on_delete=SET_NULL`). Não persiste access token, refresh token, `client_secret`, `code_verifier` nem usa sessão. Migration aditiva `0059_integrationlex.py`.
- **Settings** (`fiscallizeon/settings.py` + `envexample.txt`): `LEX_SSO_URL`, `LEX_SSO_CLIENT_ID`, `LEX_SSO_CLIENT_SECRET`, `LEX_SSO_CODE_VERIFIER`, `LEX_SSO_REDIRECT_URI`. Staging usa `https://homolog-api.lex.education/sso`; produção usa `https://api.lex.education/sso`. `scope = 'openid profile offline_access'` constante de `LexIntegrationService.SCOPE`.
- **Service `LexIntegrationService`** (`fiscallizeon/integrations/services/lex_sso.py`): `build_lex_login_url()` monta `{LEX_SSO_URL}/connect/authorize` com PKCE S256 (`code_challenge=BASE64URL(SHA256(LEX_SSO_CODE_VERIFIER))` sem padding, `response_type=code`, `client_id`, `redirect_uri`, `scope`) sem HTTP externo, sem `client_secret` nem `code_verifier` na URL; `exchange_code()` faz `POST {LEX_ISSUER}/connect/token` form-urlencoded com `grant_type=authorization_code`, sem repetir a troca; `get_userinfo()` faz `GET {LEX_ISSUER}/connect/userinfo` com `Authorization: Bearer <access_token>`. Credenciais via `config` do ambiente; não recebe `request`, sessão, cookies ou redirect.
- **View `LexPortalView`** (`fiscallizeon/integrations/views_lex_portal.py`): `TemplateView` pública que renderiza `integrations/lex/loading_auth.html`, repassa `code` opcional e as URLs das APIs ao template via contexto `lex_page`. Não grava `IntegrationLex`, não usa sessão, não chama a LEX.
- **API `IntegrationLexAuthorizationAPIView`** (`apis/lex.py`): `GET /integracoes/api/lex/get-lex-url-login/` público (`AllowAny`), retorna `{ "authorization_url": "..." }`; configuração incompleta retorna HTTP 503 com `{ "message": "..." }`.
- **API `IntegrationLexCreateAPIView`** (`apis/lex.py`): `POST /integracoes/api/lex/` público (`AllowAny`), aceita `code` não vazio via `IntegrationLexCreateSerializer`. Grava `IntegrationLex` com `user_integrated` nulo, troca o código, consulta userinfo, busca `User` ativo único por `email__iexact`, `login()` com `EmailOrUsernameModelBackend`, preenche `user_integrated`, responde `{ "redirect_url": reverse('core:redirect_dashboard') }`; falhas respondem `{ "message": "..." }`. Não existe `/integracoes/api/lex/complete/`.
- **Serializer** (`serializers/lex.py`): `IntegrationLexCreateSerializer` valida `code` não vazio (`allow_blank=False`, `trim_whitespace=True`).
- **URLs** (`integrations/urls.py`): `path('lex', LexPortalView, name='lex_portal')`, `path('api/lex/get-lex-url-login/', IntegrationLexAuthorizationAPIView, name='lex_authorization_url')`, `path('api/lex/', IntegrationLexCreateAPIView, name='lex_integration_create')`.
- **Template** (`templates/integrations/lex/loading_auth.html` + `static/integrations/lex/loading_auth.js`): instância Vue com loading; sem `code` consulta a API de autorização e navega para `authorization_url`; com `code` faz `POST` na create e navega para `redirect_url`; falha exibe `message`. `redirect_uri` cadastrado na LEX é `{LIZE_BASE_URL}/integracoes/lex` (sem barra final).

### Multi-tenant / permissão

- `User` é o ativo encontrado pelo `email` do userinfo (`email__iexact`). Nenhum papel LEX altera `CustomGroup`. Não cria contas automaticamente, não sincroniza turmas/notas.

### Testes automatizados existentes

- `fiscallizeon/integrations/tests/test_lex_sso_auth.py` (402 linhas): página/loading, API de autorização (200/503), create (sucesso, code ausente, token recusado, userinfo inválido, e-mail vazio, usuário inexistente/inativo, e-mail ambíguo, nova linha por POST, logout preserva linha, ausência de rota `/complete/`).
- `fiscallizeon/integrations/tests/test_lex_sso_service.py` (164 linhas): URL de autorização S256/encoded, configuração ausente, troca em homologação/produção, corpo form-urlencoded, sem repetição em falha, userinfo com Bearer.

### Não implementado nesta branch (não-objetivos da spec)

- Botão "Logar com LEX" na tela de login Lize.
- Rota `/integracoes/api/lex/complete/`.
- Registro da tentativa em sessão, `LexClientIntegration`, busca por `sub`/`account_id`/`preferred_username`, app do aluno, 2FA, renovação de token LEX, logout remoto/global.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- **IN SCOPE:**
  - Entrada pública `GET /integracoes/lex` (sem barra final) com `code` opcional; renderiza loading Vue sem gravar nem chamar a LEX.
  - `GET /integracoes/api/lex/get-lex-url-login/` montando a URL de autorização OIDC com PKCE S256 (HTTP 503 se configuração incompleta).
  - Redirecionamento do navegador para `{LEX_SSO_URL}/connect/authorize` quando falta `code` utilizável.
  - `POST /integracoes/api/lex/` criando `IntegrationLex`, trocando o código por token, lendo `email` do userinfo, fazendo `login()` e respondendo `{ "redirect_url": core:redirect_dashboard }`.
  - Exibição de `message` no template em falhas (código ausente, token rejeitado, userinfo inválido, e-mail vazio/inexistente/ambíguo).
  - Logout local `/conta/sair/` preservando a linha de `IntegrationLex`; sem logout remoto da LEX.
  - Configuração por ambiente via `settings.py`/`envexample.txt` (sem segredos versionados).
- **OUT OF SCOPE:**
  - Botão de autorização na tela de login da Lize.
  - Rota `/integracoes/api/lex/complete/`.
  - Registro da tentativa em sessão e `LexClientIntegration`.
  - Criação automática de conta, busca por `sub`/`account_id`, sincronização de usuários/turmas/notas.
  - Renovação contínua de token LEX, logout remoto/back-channel, callback de logout OIDC.
  - App do aluno (`lize-student`, `/api/v3/`).
  - Mudança no shell de login da Lize ou em outros métodos de login (senha, Google, Layers).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino                  | Rótulo real no menu UI             | URL Django                                | View / Rota name                      |
| ------------------------ | ---------------------------------- | ----------------------------------------- | ------------------------------------- |
| Entrada SSO LEX          | (botão no painel LEX, não na Lize) | `/integracoes/lex`                        | `integrations:lex_portal` [verificar] |
| API URL de autorização   | (JSON, sem UI)                     | `/integracoes/api/lex/get-lex-url-login/` | `integrations:lex_authorization_url`  |
| Create de IntegrationLex | (JSON, consumido pelo Vue)         | `/integracoes/api/lex/`                   | `integrations:lex_integration_create` |
| Login local              | `/conta/sair/` (logout)            | `/conta/sair/`                            | `accounts:logout` [verificar]         |
| Destino após sucesso     | Dashboard padrão                   | `core:redirect_dashboard`                 | `core:redirect_dashboard`             |

> **[verificar]** O rótulo do botão no painel LEX ("Ir para a Lize" / "Logar na Lize") é definido pela LEX/Conexia, não consta nos templates da Lize. Confirmar com o parceiro. O rótulo de logout local depende do template de conta da Lize (`/conta/sair/`).

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

- **Comandos para rodar os testes automatizados:**

  ```bash
  source venv/bin/activate
  pytest fiscallizeon/integrations/tests/test_lex_sso_auth.py fiscallizeon/integrations/tests/test_lex_sso_service.py --reuse-db
  ```

  Ou, com Docker: `./scripts/tests/run-tests.sh --no-tty fiscallizeon/integrations/tests/test_lex_sso_auth.py fiscallizeon/integrations/tests/test_lex_sso_service.py`

- **Persona:** Usuário autenticado na LEX (não precisa de sessão Lize prévia). Após o fluxo, o `User` local ativo com o `email` do userinfo fica autenticado via sessão criada no `POST /integracoes/api/lex/` com o backend `EmailOrUsernameModelBackend`. Nenhuma permissão `CustomGroup` específica é exigida (QUALQUER `User` ativo com o e-mail corresponde autentica).

- **Mixer Setup (para QA manual e automação futura):**
  ```python
  from mixer.backend.django import mixer
  from fiscallizeon.accounts.models import User

  # Usuário ativo cuja conta será encontrada pelo e-mail do userinfo LEX
  user = mixer.blend(
      User,
      email='pessoa@escola.com',
      is_active=True,
      two_factor_enabled=False,
      must_change_password=False,
      has_la_place_login=False,
  )

  # Tentativa de integração (linha gravada antes do login)
  mixer.blend(
      'integrations.IntegrationLex',
      code='codigo-lex-teste',
      user_integrated=None,
  )
  ```
  - Para cenários de **falha**, misture usuários inativos (`is_active=False`) ou dois usuários ativos com o mesmo e-mail (ambiguidade).
  - Para a página de loading sem `code`, não é necessário setup de banco; apenas renderiza o template.

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

> **Persona ativa:** Usuário com conta na LEX e `User` ativo correspondente na Lize pelo mesmo e-mail (sem sessão Lize prévia). Executar em ambiente com settings LEX configuradas (homologação: `https://homolog-api.lex.education/sso`).

### 5.1 Entrada pública e loading [Apenas Manual 👁]

#### Cenário 1 — Abertura da página `/integracoes/lex` com código (autenticação)

**Ação humana:**

- [x] Acessar `https://<LIZE_BASE_URL>/integracoes/lex?code=codigo-da-lex` (sem estar logado na Lize).
- [x] Confirmar que a página exibe o título "Autenticação LEX — Lize" e o logo da LEX.
- [x] Confirmar o loading com a animação circular e o texto "**Autenticando sua conta**" (negrito, cinza escuro).
- [x] Confirmar o subtítulo "**Estamos validando seu acesso com a LEX. Aguarde um momento…**" (cinza claro).
- [x] Confirmar o rodapé "**Lize Edu × LEX**" (cinza claro, texto pequeno).
- [x] Confirmar que não há link/botão de login da Lize (ex: "/conta/entrar/") na página.

**Referência técnica (para automação):**

- URL: `/integracoes/lex?code=<codigo>`
- Seletor DOM: `#app`, `h1` com texto `"Autenticando sua conta"`, SVG com classe `tw-animate-spin`
- Estado esperado: `v-cloak` removido após montagem do Vue; `lex_page.code` preenchido no JSON do script `id="lex-sso-config"`
- Fixture: nenhum setup de banco necessário (página pública)

---

### 5.2 Entrada sem código (inicia autorização na LEX) [Apenas Manual 👁]

#### Cenário 2 — Página sem `code` navegando para a LEX

**Ação humana:**

- [x] Acessar `https://<LIZE_BASE_URL>/integracoes/lex` sem query string (ou com `code=` vazio / apenas espaços).
- [x] Confirmar o loading com texto "**Enviando para a LEX**" e subtítulo "**Estamos iniciando seu acesso com a LEX. Aguarde um momento…**".
- [x] Confirmar que o navegador é redirecionado para a URL de autorização da LEX (`{LEX_SSO_URL}/connect/authorize…`) — não para a tela de login da Lize.
- [x] Confirmar que não é criada nenhuma linha de `IntegrationLex` no banco.

**Referência técnica (para automação):**

- URL: `/integracoes/lex` (sem `code`)
- Seletor DOM: `h1` com texto `"Enviando para a LEX"`
- API: `GET /integracoes/api/lex/get-lex-url-login/` → JSON `{ "authorization_url": "..." }`
- Estado esperado: `window.location.href = authorization_url`; `IntegrationLex.objects.count() == 0`
- Fixture: nenhum

---

### 5.3 API de autorização [Automatizável ✅]

#### Cenário 3 — Consulta da URL de autorização com configuração completa

**Ação humana:**

- [x] Abrir `https://<LIZE_BASE_URL>/integracoes/api/lex/get-lex-url-login/` diretamente no navegador.
- [x] Confirmar resposta HTTP 200 com JSON contendo `authorization_url`.
- [x] Confirmar que a URL contém `/connect/authorize` do ambiente (homologação: `https://homolog-api.lex.education/sso/connect/authorize`).
- [x] Confirmar que NÃO expõe `client_secret` nem `code_verifier` na resposta.

**Referência técnica (para automação):**

- URL: `/integracoes/api/lex/get-lex-url-login/`
- Seletor DOM: corpo JSON da resposta (não UI)
- Estado esperado: `authorization_url` com `response_type=code`, `code_challenge_method=S256`, `scope=openid%20profile%20offline_access`, `code_challenge` derivado de `LEX_SSO_CODE_VERIFIER`
- Fixture: settings `LEX_SSO_*` completas

### 5.4 Create de IntegrationLex e autenticação [Automatizável ✅]

#### Cenário 4 — POST com código válido: grava linha, autentica, devolve dashboard

**Ação humana:**

- [x] Garantir que exista exatamente um `User` ativo na Lize com o e-mail que a LEX retornará no userinfo (ex.: `pessoa@escola.com`).
- [x] Com `code` válido na URL (`/integracoes/lex?code=codigo-lex`), o Vue envia o POST da create.
- [x] Confirmar que a página navega para a URL padrão do dashboard (`core:redirect_dashboard`).
- [x] Confirmar que o usuário já está autenticado no dashboard (sessão local criada).
- [x] Confirmar que o `code` NÃO aparece na resposta JSON nem no template de erro.

**Referência técnica (para automação):**

- URL: `POST /integracoes/api/lex/` com corpo `{"code": "<codigo>"}`, header `Content-Type: application/json`, `X-CSRFToken`
- Seletor DOM: resposta JSON `{ "redirect_url": "<url do dashboard>" }`
- Estado esperado: `IntegrationLex` com `code` gravado e `user_integrated` preenchido com o `User` do e-mail; `SESSION_KEY` presente na sessão
- Fixture: `mixer.blend(User, email='pessoa@escola.com', is_active=True)`; mock de `LexIntegrationService.exchange_code` → `{'access_token': 'token-lex'}` e `get_userinfo` → `{'email': 'Pessoa@Escola.com'}`

#### Cenário 5 — POST sem código não grava e devolve message

**Ação humana:**

- [x] Enviar POST com `code` vazio ou apenas espaços (`"   "`).
- [x] Confirmar resposta HTTP 400 com JSON `{ "message": "Código de acesso ausente." }`.
- [x] Confirmar que nenhuma linha de `IntegrationLex` é criada e que não há sessão iniciada.

**Referência técnica (para automação):**

- URL: `POST /integracoes/api/lex/` com `{"code": "   "}`
- Estado esperado: status 400, `message` preenchido, `IntegrationLex.objects.count() == 0`, `SESSION_KEY` ausente

#### Cenário 6 — E-mail vazio / usuário inexistente / e-mail ambíguo

**Ação humana:**

- [x] E-mail vazio no userinfo: confirmar `message` e `user_integrated` nulo.
- [x] Usuário inativo ou inexistente com aquele e-mail: confirmar `message` ("Usuário não cadastrado na Lize.") e sem autenticação. ![](../evidencias/sem-user.png)

**Referência técnica (para automação):**

- URL: `POST /integracoes/api/lex/`
- Estado esperado: status 400, `message` correspondente, `user_integrated__isnull=True`
- Fixture: `User` inativo; dois `User` ativos com mesmo e-mail; userinfo sem `email`

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

A change envolve UI (template de loading da LEX), mas não há Figma/mockup da Lize para este fluxo — a tela de espera segue a referência visual existente (`integrations/layers/loading_auth.html`) e o botão de entrada fica no painel LEX (fora da Lize).

- [x] Capturar print da tela de loading **sem código** (texto "Enviando para a LEX", animação de carregamento ativa). ![](../evidencias/enviando.png)
- [x] Capturar print da tela de loading **com código** (texto "Autenticando sua conta"). ![](../evidencias/autenticando.png)
- [x] Capturar print do **template de erro** (`hasError` com `message` em vermelho). ![](../evidencias/erro.png)
- [x] Confirmar que o `redirect_uri` cadastrado na LEX bate com `{LIZE_BASE_URL}/integracoes/lex` (sem barra final).
- [x] Confirmar que credenciais (`client_secret`, `code_verifier`) não aparecem no HTML, nos logs nem nas respostas JSON.

> **Nota:** Como a Natureza da Tarefa é `[Business Feature]` com UI nova (loading LEX), esta section foca em confirmação visual da tela de loading e de erro, não em comparação estrita com Figma (não há mockup da Lize para esta tela).

---

## 7. Bugs and Observations (Problemas Encontrados)

Reserve esta section para documentar bugs/UX issues durante a execução manual. Use alertas GitHub-style:

> [!BUG] Título do problema  
> **[UX/UI] | [Backend Logic] | [Database] | [Spec Gap]**  
> **Context/Root Cause:** por que ocorre tecnicamente.  
> **Expected Behavior:** o que deveria acontecer (cite a spec exatamente: `spec.md L.XX` ou `integration-flow.md`).  
> **Workaround:** gambiarra temporária para continuar o fluxo, se houver.

_Exemplo de preenchimento (ajustar conforme encontrado na execução):_

> [!BUG] E-mail ambíguo não distingue contas  
> **[Backend Logic] | [Spec Gap]**  
> **Context/Root Cause:** a create filtra `email__iexact` com `[:2]` e retorna `AMBIGUOUS_MESSAGE` quando há mais de um `User` ativo com o mesmo e-mail, conforme spec (`specs/lex-sso-auth/spec.md` L.93-94).  
> **Expected Behavior:** nenhuma conta autenticada; `message` exibida no template.  
> **Workaround:** desativar ou renomear o e-mail de uma das contas duplicadas para permitir o fluxo.

> [!WARNING] Observação de execução  
> Nenhuma ainda — pendente de execução manual do plano.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE] Rótulo do botão no painel LEX definido externamente: o texto "Ir para a Lize" / "Logar na Lize" é controlado pela LEX/Conexia, não pela Lize. Se o parceiro mudar o rótulo, não há impacto no código da Lize.

> [!NOTE] Sem rota `/complete/`: a spec proíbe explicitamente. Se futuramente houver necessidade de concluir o fluxo via GET, será necessário revisar a decision de design (design.md Decision 1).

> [!NOTE] `code` permanece gravado na linha de `IntegrationLex` após a troca (não é apagado nem invalidado). Não há rota de revogação/limpeza desses códigos nesta entrega.

> [!NOTE] O logout local `/conta/sair/` não apaga a linha de `IntegrationLex` nem dispara logout remoto da LEX, conforme spec (`specs/lex-sso-logout/spec.md`).

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- Não existe arquivo de mapeamento prévio para a tela de loading LEX em `.ai_qa_acervo/docs/tests/usability/`.
- Nome do arquivo de mapa (padrão 1:1 com o template HTML Django): `loading_auth.md` (bate com `integrations/lex/loading_auth.html`, não com a view `LexPortalView` nem com a URL).
- Conteúdo sugerido para `.ai_qa_acervo/docs/tests/usability/loading_auth.md`:
  1. **URLs e Navegação:** `GET /integracoes/lex` (com/sem `code`), `GET /integracoes/api/lex/get-lex-url-login/`, `POST /integracoes/api/lex/`, destino `core:redirect_dashboard`.
  2. **Pré-requisitos para Automação:** `User` ativo com `email__iexact` igual ao do userinfo; settings `LEX_SSO_*` completas; `mixer.blend(User, ...)` para o match; mock de `LexIntegrationService.exchange_code`/`get_userinfo` para testes offline.
  3. **Seletores DOM e Ações:** `h1` "Autenticando sua conta" / "Enviando para a LEX"; `div[v-show="hasError"]` com `${ errorMessage }`; JSON script `id="lex-sso-config"` contendo `createUrl`, `authorizationUrl`, `code`, `csrfToken`, `authorizationError`.
- Checkbox de validação de nomeação:
  - [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) (`loading_auth.html`), e não a View (`LexPortalView`).
  - 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/loading_auth.md)**

- Snippet de automação sugerido (UI + setup de dados via mixer):

  ```python
  import json
  import re
  from unittest.mock import patch
  from mixer.backend.django import mixer
  from fiscallizeon.accounts.models import User
  from fiscallizeon.integrations.models import IntegrationLex

  def setup_lex_user():
      user = mixer.blend(User, email='pessoa@escola.com', is_active=True)
      return user

  def test_lex_sso_flow(client):
      user = setup_lex_user()
      with patch(
          'fiscallizeon.integrations.apis.lex.LexIntegrationService.exchange_code',
          return_value={'access_token': 'token-lex'},
      ), patch(
          'fiscallizeon.integrations.apis.lex.LexIntegrationService.get_userinfo',
          return_value={'email': user.email},
      ):
          # POST da create (simula o Vue)
          resp = client.post(
              '/integracoes/api/lex/',
              data={'code': 'codigo-lex'},
              content_type='application/json',
          )
          assert resp.status_code == 200
          assert resp.json()['redirect_url'] == reverse('core:redirect_dashboard')
          integration = IntegrationLex.objects.get()
          assert integration.code == 'codigo-lex'
          assert integration.user_integrated_id == user.pk
          assert client.session[SESSION_KEY] == str(user.pk)
  ```

  **CRITICAL:** o snippet demonstra o setup de backend (`mixer.blend(User, ...)`) necessário para o cenário funcionar, não apenas cliques de UI.

- **Template Permissions Check:** `LexPortalView`, `IntegrationLexAuthorizationAPIView` e `IntegrationLexCreateAPIView` são públicas (`AllowAny` / `TemplateView` sem login required). Não há `user.is_superuser` nem `has_perm` neste fluxo; o match é por `email__iexact` em `User` ativo. Nenhuma elevação de privilégio necessária para o bot de automação.

- **API Interception & Fixtures:** rotas críticas: `/integracoes/lex` (entrada), `/integracoes/api/lex/get-lex-url-login/` (autorização), `/integracoes/api/lex/` (create). Entidades complexas: `IntegrationLex` (code, user_integrated) e `User` ativo pelo e-mail do userinfo.

---

## 9. QA Retrospective (Retrospectiva de QA)

- Qual foi o principal gargalo durante o teste? (pendente de execução manual)
- Houve muitos idas e vindas com o desenvolvedor? (pendente)
- Como o fluxo de desenvolvimento/QA desta tarefa poderia ter sido melhorado? (pendente)

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

- Sugestão: adicionar ao Prompt V2 uma instrução para listar explicitamente as variáveis de ambiente obrigatórias e seus valores de exemplo (homologação vs produção), já que esta change depende inteiramente delas (`LEX_SSO_URL`, `LEX_SSO_CLIENT_ID`, `LEX_SSO_CLIENT_SECRET`, `LEX_SSO_CODE_VERIFIER`, `LEX_SSO_REDIRECT_URI`).
- Sugestão: incluir no template do QA Plan um item obrigatório de "segredos não expostos" (client_secret/code_verifier não devem aparecer em logs, respostas ou HTML), relevante para integrações OAuth/OIDC.

---

## Objetivos da Sessão Atual de Teste (Validação do Prompt V2)

1. **Otimização:** descobrir formas de otimizar ainda mais o Prompt V2 com base neste plano de integração SSO (pouca UI, muito backend/OIDC).
2. **Entendimento de Fluxo:** validar se a estrutura do plano ajuda a compreender o fluxo LEX → Lize (loading → autorização → create → dashboard).
3. **Mapeamento para Automação Futura:** confirmar se os seletores, URLs reais e fixtures (`mixer.blend(User)`, mock do service) permitiriam à IA testar novas funcionalidades desta integração com autonomia.
4. **Sugestões de Melhorias:** registrar ativamente sugestões de ajuste na especificação, no teste ou no prompt durante a interação.

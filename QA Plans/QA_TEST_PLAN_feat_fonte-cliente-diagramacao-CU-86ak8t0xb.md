## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-06 |
| **Branch:** | `feat/fonte-cliente-diagramacao-CU-86ak8t0xb` |
| **ClickUp:** | [Fontes extras por cliente na diagramação (86ak8t0xb)](https://app.clickup.com/t/86ak8t0xb) |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Diagramação / Impressão de Cadernos / Padrões de Impressão / Django Admin / Multi-tenant |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (completa: proposal, design, spec, tasks e referências em `openspec/changes/fonte-cliente-diagramacao-86ak8t0xb/`) |

---

## 1. Summary of Changes (Resumo das Alterações)

- **Backend & Modelos (`fiscallizeon/clients/models.py`):**
  - Criação do modelo `ClientPrintFont(BaseModel)` com FK para `Client`, `label` (nome exibido), `font_file` (armazenado via `PublicMediaStorage`), `css_family` (gerado automaticamente no formato `LizeClientFont-<uuid12>`), `is_active` (booleano) e `sort_order`.
  - Adição da chave estrangeira nullable `client_print_font` em `ExamPrintConfig(BaseModel)`.
  - Validação estrita de extensões permitidas no upload (`.woff`, `.woff2`, `.ttf`, `.otf`) no método `clean()` do modelo.
- **Admin Interno Lize / CS (`fiscallizeon/clients/admin.py`):**
  - Registro de `ClientPrintFontAdmin` (`/admin/clients/clientprintfont/`) com filtros e busca por cliente/rótulo.
  - Registro de `ClientPrintFontInline` dentro de `ClientAdmin` (`/admin/clients/client/<uuid>/change/`), permitindo à equipe de CS cadastrar e ativar fontes tipográficas diretamente na tela do cliente.
  - Inclusão de `client_print_font` no autocomplete do `ExamPrintConfigAdmin`.
- **Serviços & Helpers de Resolução (`fiscallizeon/clients/print_fonts.py`):**
  - `get_print_font_choices(client)`: Retorna dicionário contendo as 5 opções globais (`standard`) e as fontes ativas cadastradas para o cliente (`client`).
  - `standard_print_font_family_css(font_family)`: Mapeamento CSS com inclusão explícita de `Nunito Sans` para o identificador 4.
  - `build_print_font_template_context(...)`: Resolve e gera a diretiva `@font-face` e o valor de `font-family` para o HTML de impressão. Fonte extra prevalece sobre a seleção padrão.
  - `apply_print_font_context(...)`: Injeta as variáveis de tipografia no contexto a partir de parâmetros GET, dicionários de malote ou da instância `ExamPrintConfig`.
- **APIs & Serializers (`fiscallizeon/clients/api/print_configs.py`, `fiscallizeon/exams/apis.py`):**
  - Novo endpoint `GET /api/v2/clients/print-configs/print-font-choices/` expondo choices dinâmicas do cliente autenticado.
  - Validação de isolamento multi-tenant em `ExamPrintConfigUpdateApi` e `ExamPrintConfigViewSet`: tentativa de vincular fonte de outro `Client` rejeitada com HTTP 400.
  - Propagação de `client_print_font_id` nos malotes de aplicações (`applications/api/exams_bag.py`), ensalamento (`distribution/api/exams_bag.py`) e mockup (`omr/mockup_utils.py`).
- **Frontend & Interfaces de Usuário:**
  - **Diagramador de Provas (`diagram_layout_font.html` + `diagram_layout_list.js`):** Substituição do controle por um `<select>` com `<optgroup label="Padrão Lize">` e `<optgroup label="Fontes da instituição">`, com legenda explicativa.
  - **Padrões de Impressão (`print_defaults_create_update.html` e `exam_configs_form.html` via `print_font_family_vue.html`):** Botões para as 5 fontes padrão e grupo dinâmico para as fontes institucionais do cliente.
  - **Modal de Impressão de Provas e Malotes (`modal_print.html`):** Atualização do grupo de botões com as fontes da instituição para cadernos (`exam_list_new.html`), aplicações presenciais (`application_list.html`, `application_list_new.html`) e ensalamento (`distribution_list.html`).
- **Impressão e PDF (`exam_print.html` e variantes v2):**
  - Injeção dinâmica de `@font-face` quando o caderno utiliza fonte extra.
  - Aplicação de `font-family` no corpo do documento e em `.question *:not(.katex *):not(.MathJax *)`.
  - Correção do mapeamento de **Nunito Sans** (`font_family == 4`), que anteriormente caía no fallback de Plex Sans.
- **Testes Automatizados:**
  - `fiscallizeon/clients/tests/test_client_print_font.py`: Testes de isolamento multi-tenant, validação de serializers e geração de contexto `@font-face`.
  - `fiscallizeon/exams/tests/test_exam_print_font_cascade.py`: Testes de cascata CSS na impressão e inclusão de Nunito Sans.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- IN SCOPE: Cadastro e gerenciamento de fontes institucionais exclusivamente via Django Admin (operação CS/Lize).
- IN SCOPE: Exibição das fontes institucionais liberadas nas telas de Diagramar (acordeon Fonte), Padrões de Impressão e Modal de Impressão de cadernos e malotes.
- IN SCOPE: Isolamento estrito entre clientes: Cliente A visualiza suas fontes; Cliente B visualiza apenas as 5 padrão (ou suas próprias fontes).
- IN SCOPE: Persistência de `client_print_font` em `ExamPrintConfig` com retrocompatibilidade total com as 5 fontes padrão (inteiros 0–4).
- IN SCOPE: Aplicação fiel da fonte institucional e de Nunito Sans na pré-visualização e no HTML/PDF de impressão.
- IN SCOPE: Propagação de `client_print_font_id` nos malotes de aplicações e ensalamento.
- IN SCOPE: Permitir múltiplas fontes ativas por cliente (a restrição arbitrária de 3 fontes foi deliberadamente removida no commit `e3e4af064` para atender à flexibilidade exigida pelo produto).
- OUT OF SCOPE: Upload ou gerenciamento de fontes por professores ou coordenadores no portal web (recurso restrito ao staff/CS).
- OUT OF SCOPE: Alteração tipográfica institucional em outras áreas do sistema fora de cadernos e provas impressas (ex: redesign geral da plataforma).
- OUT OF SCOPE: Suporte a fontes variáveis com múltiplos eixos dinâmicos.
- OUT OF SCOPE: Migração retroativa de provas já impressas e arquivadas.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Admin: Fontes de Impressão do Cliente | Django Admin ➔ CLIENTS ➔ **Fontes de impressão do cliente** | `/admin/clients/clientprintfont/` | `admin:clients_clientprintfont_changelist` |
| Admin: Detalhe do Cliente (Inline) | Django Admin ➔ CLIENTS ➔ **Clientes** ➔ Selecionar cliente ➔ seção inline **Fontes de impressão do cliente** | `/admin/clients/client/<uuid>/change/` | `admin:clients_client_change` |
| Diagramador de Provas (Sidebar Fonte) | Menu lateral ➔ **Cadernos** (ou **Instrumentos Avaliativos**) ➔ abrir caderno ➔ botão **"Diagramar"** ➔ acordeon **"Fonte"** | `/provas/<uuid>/v2/imprimir/` | `exams:exam-print-v2` (`ExamPrintV2View`) |
| Padrões de Impressão (Listagem) | Menu lateral ➔ Gerenciamento ➔ Provas ➔ **Padrões de impressão** | `/membros/padrao/configuracao/` | `clients:print-configs-list` |
| Padrões de Impressão (Cadastrar) | Tela de Padrões de Impressão ➔ botão **"Cadastrar um novo padrão de impressão"** | `/membros/padrao/configuracao/cadastrar/` | `clients:print-configs-create` |
| Padrões de Impressão (Editar) | Tela de Padrões de Impressão ➔ ação **"Editar"** no padrão | `/membros/padrao/configuracao/atualizar/<uuid>/` | `clients:print-configs-update` |
| Modal de Impressão de Caderno | Menu lateral ➔ **Cadernos** ➔ botão de impressão na listagem de cadernos | `/provas/` | `exams:exams_list` (`exam_list_new.html`) |
| Modal de Impressão de Malote (Aplicações) | Menu lateral ➔ **Aplicações** ➔ aba **Presencial** ➔ menu **"Opções"** ➔ **"Todos os alunos"** | `/aplicacoes/?category=presential` | `applications:applications_list` |
| Modal de Impressão de Malote (Ensalamento) | Menu lateral ➔ Aplicações ➔ **Ensalamento** ➔ botão de gerar malote | `/ensalamento/` | `distribution:distribution_list` |
| Impressão do Caderno (HTML/PDF) | Diagramador ➔ Ação **"Salvar e visualizar"** / Impressão direta | `/provas/<uuid>/imprimir` ou pré-visualização renderizada | `exams:exam_print` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Personas Executoras:
1. **Staff / Superuser Lize:** Acesso ao Django Admin (`/admin/`) para cadastrar arquivos de fontes vinculados ao `Client`.
2. **Coordenação da Escola A (Cliente com fontes extras):** Usuário vinculado a `SchoolCoordination` da escola dona da fonte, com permissões `can_diagram_exam`, `can_print_exam`, `view_exam` e `view_examprintconfig`.
3. **Coordenação da Escola B (Cliente sem fontes extras):** Usuário vinculado a outro `Client` para validar a barreira multi-tenant (não deve ver nem poder usar fontes da Escola A).

### Execução de Testes Automatizados Locais:

```bash
# Execução na máquina local (com virtualenv ativada):
source venv/bin/activate && pytest fiscallizeon/clients/tests/test_client_print_font.py fiscallizeon/exams/tests/test_exam_print_font_cascade.py --reuse-db

# Execução completa via Docker:
./scripts/tests/run-tests.sh --no-tty fiscallizeon/clients/tests/test_client_print_font.py fiscallizeon/exams/tests/test_exam_print_font_cascade.py
```

### Setup de Dados via Mixer (Python Shell / Script de Teste):

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, ClientPrintFont, ExamPrintConfig
from fiscallizeon.exams.models import Exam

# 1. Utilizando o cliente real existente no banco (Rede Decisão):
client_a = Client.objects.filter(name__icontains="Rede Decisão").first()
# UUID: a2b1158b-367a-40a4-8413-9897057c8aa2
# Usuários de coordenação existentes: chrystyane.mello@rededecisao.com.br, tatiana.pereira@rededecisao.com.br
# (Dica de QA: pode logar diretamente via staff "Aderir ao cliente" ou resetar senha para 123456 via /qa-reset-passwords)

# Fonte extra cadastrada para a Rede Decisão (manual via Admin ou via script):
fonte_institucional = ClientPrintFont(
    client=client_a,
    label="Institucional Decisão Sans",
    is_active=True,
    sort_order=1
)
fonte_institucional.font_file.name = "clients/print-fonts/decisao_sans.woff2"
fonte_institucional.save()

# 2. Cliente B para validação de barreira multi-tenant (ex: Salesiano Dom Bosco ou criado via mixer):
client_b = Client.objects.filter(name__icontains="Salesiano").first()
if not client_b:
    client_b = mixer.blend(Client, name="Colégio Exemplo B")

# 3. Caderno existente para testes na Rede Decisão:
# Já existe no banco: "Caderno para revisão 1" (ID: 1589f071-494c-4a58-964d-820c6717987d)
# Ou crie um novo sob demanda se preferir.
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Django Admin: Cadastro e Gestão de Fontes por Cliente [Automatizável ✅]

Persona: **Staff Lize** logado em `/admin/`.

#### Cenário 1 — Cadastro de fonte institucional ativa vinculada à Rede Decisão

**Ação humana:**
- [x] Acessar `/admin/clients/clientprintfont/add/` (ou abrir o cliente Rede Decisão em `/admin/clients/client/` e descer até o inline `"**Fontes de impressão do cliente**"`)
- [x] Selecionar o cliente `"**Rede Decisão**"` no campo `"**Cliente**"`
- [x] Preencher o campo `"**Nome exibido**"` com `"**Institucional Decisão Sans**"`
- [x] No campo `"**Arquivo da fonte**"`, fazer upload de um arquivo com extensão válida (`.woff2`, `.woff`, `.ttf` ou `.otf`)
- [x] Confirmar que o checkbox `"**Ativa**"` está marcado e a `"**Ordem**"` está como `1`
- [x] Clicar no botão azul `"**Salvar**"` (canto inferior direito)
- [x] Validar a mensagem de sucesso verde: `"A fonte de impressão do cliente "Rede Decisão — Institucional Decisão Sans" foi adicionada com sucesso."`
- [x] Abrir a fonte salva e verificar que o campo `"**Identificador CSS**"` foi gerado automaticamente com o formato `LizeClientFont-<identificador>` em modo somente leitura ![alt text](../evidencias/image-7.png)

**Referência técnica (para automação):**
- URL: `/admin/clients/clientprintfont/add/`
- Seletor: `input[name="label"]`, `input[name="font_file"]`, `input[name="is_active"]`, `input[type="submit"][name="_save"]`
- Estado esperado: Registro salvo no banco com `css_family` não-nulo e `client_id == client_a.pk`
- Fixture: `Client.objects.get(name="Rede Decisão")` + arquivo de fonte válido

#### Cenário 2 — Rejeição de arquivo com formato inválido

**Ação humana:**
- [x] Acessar `/admin/clients/clientprintfont/add/`
- [x] Selecionar um cliente, digitar o nome exibido `"**Fonte Inválida**"` e anexar um arquivo não suportado (ex: `.zip`, `.pdf` ou `.exe`)
- [x] Clicar no botão `"**Salvar**"`
- [x] Confirmar que o formulário não é submetido e exibe o alerta de erro: `"Formato não suportado. Use: .otf, .ttf, .woff, .woff2."` ![alt text](../evidencias/image-8.png)

**Referência técnica (para automação):**
- URL: `/admin/clients/clientprintfont/add/`
- Seletor: `.errorlist li`
- Estado esperado: FormValidationError contendo a mensagem de extensão inválida

#### Cenário 3 — Desativação de fonte no admin

**Ação humana:**
- [x] Acessar a listagem `/admin/clients/clientprintfont/`
- [x] Clicar sobre a fonte cadastrada `"**Institucional Decisão Sans**"`
- [x] Desmarcar o checkbox `"**Ativa**"` (`is_active = False`)
- [x] Clicar no botão `"**Salvar**"`
- [x] Confirmar que o status na coluna `"**Ativa**"` da listagem passa a exibir o ícone vermelho de falso (ícone de X) ![alt text](../evidencias/image-9.png)

**Referência técnica (para automação):**
- URL: `/admin/clients/clientprintfont/<uuid>/change/`
- Seletor: `input[name="is_active"]`
- Estado esperado: `font.is_active == False`

---

### 5.2 Diagramador de Provas: Seleção e Persistência [Automatizável ✅]

Persona: **Coordenação da Rede Decisão** (com fontes liberadas) vs **Coordenação do Cliente B** (ex: Salesiano Dom Bosco, sem fontes liberadas).

#### Cenário 4 — Exibição das fontes da instituição para a Rede Decisão

**Ação humana:**
- [x] Fazer login com a conta de coordenação da **Rede Decisão** (ex: `chrystyane.mello@rededecisao.com.br` ou via botão staff `"Aderir ao cliente"`)
- [x] Acessar o menu lateral `"**Cadernos**"` e abrir a diagramação de um caderno (ex: `"**Caderno para revisão 1**"`, clicando no botão `"**Diagramar**"`)
- [x] Na barra lateral de diagramação, clicar na seção/acordeon `"**Fonte**"`
- [x] Clicar no campo select `"**Tipo de fonte**"`
- [x] Confirmar visualmente a presença do grupo `"**Padrão Lize**"` com as opções: `"Plex Sans"`, `"Verdana"`, `"Times"`, `"Arial"` e `"Nunito Sans"`
- [x] Confirmar visualmente a presença do grupo separado `"**Fontes da instituição**"` exibindo a opção `"**Institucional Decisão Sans**"`![alt text](../evidencias/image-10.png)
- [x] Confirmar que logo abaixo do campo é exibido o texto explicativo em cinza: `"(Fontes da instituição são liberadas pela Lize para este cliente.)"`

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/v2/imprimir/`
- Seletor: `select:has(optgroup[label="Padrão Lize"])`, `optgroup[label="Fontes da instituição"] option`
- Estado esperado: `optgroup[label="Fontes da instituição"]` presente no DOM contendo o `value="custom:<id>"`
- Fixture: `ClientPrintFont(client=rede_decisao, is_active=True)`

#### Cenário 5 — Isolamento Multi-tenant: Cliente B não enxerga as fontes da Rede Decisão

**Ação humana:**
- [x] Deslogar e fazer login com a conta de coordenação do **Cliente B** (ex: Salesiano Dom Bosco ou outro cliente sem fontes extras)
- [x] Acessar um caderno de prova do Cliente B e clicar em `"**Diagramar**"`
- [x] Expandir o acordeon `"**Fonte**"` na barra lateral
- [x] Clicar no campo select `"**Tipo de fonte**"`
- [x] Confirmar que **NÃO** existe o grupo `"**Fontes da instituição**"` e que a opção `"**Institucional Decisão Sans**"` NÃO aparece ![alt text](../evidencias/image-11.png)
- [x] Confirmar que apenas as 5 opções do grupo `"**Padrão Lize**"` estão disponíveis
- [x] Confirmar que o texto explicativo `"(Fontes da instituição são liberadas pela Lize...)"` está oculto

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/v2/imprimir/`
- Seletor: `optgroup[label="Fontes da instituição"]`
- Estado esperado: Elemento não existe no DOM (`count == 0`)
- Fixture: `ClientPrintFont` pertencente exclusivamente à Rede Decisão

#### Cenário 6 — Seleção e salvamento de fonte institucional no caderno

**Ação humana:**
- [x] Estando logado na **Rede Decisão** na tela de diagramação do caderno
- [x] No select `"**Tipo de fonte**"`, escolher a opção `"**Institucional Decisão Sans**"`
- [x] Confirmar que o indicador de status da diagramação é atualizado para indicar alterações pendentes
- [x] Clicar na ação `"**Salvar e visualizar**"` (ou botão de salvar diagramação)
- [x] Aguardar a notificação/toast verde de sucesso
- [x] Recarregar a página (F5) e reabrir o acordeon `"**Fonte**"`
- [x] Confirmar que o select `"**Tipo de fonte**"` permanece com `"**Institucional Decisão Sans**"` selecionada 

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/v2/imprimir/`
- Seletor: `select:has(optgroup[label="Padrão Lize"])` ➔ `value == "custom:<id>"`
- Estado esperado: `ExamPrintConfig.client_print_font_id == fonte_institucional.pk` no banco de dados
- Fixture: `ExamPrintConfigUpdateApi` PATCH com payload `{ clientPrintFont: "<uuid>" }`

#### Cenário 7 — Alternância de volta para fonte padrão Lize

**Ação humana:**
- [x] No mesmo caderno com a fonte institucional selecionada, abrir novamente o acordeon `"**Fonte**"`
- [x] Alterar o select `"**Tipo de fonte**"` para `"**Verdana**"` (do grupo Padrão Lize)
- [x] Clicar em `"**Salvar e visualizar**"`
- [x] Recarregar a página (F5) e confirmar que o select exibe `"**Verdana**"`
- [x] Conferir no banco que o vínculo `client_print_font` foi desfeito (`null`) e `font_family` foi atualizado para `1`

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/v2/imprimir/`
- Seletor: `select:has(optgroup[label="Padrão Lize"])` ➔ `value == "std:1"`
- Estado esperado: `ExamPrintConfig.client_print_font_id is None` e `ExamPrintConfig.font_family == 1`

---

### 5.3 Padrões de Impressão da Escola [Automatizável ✅]

Persona: **Coordenação da Rede Decisão**.

#### Cenário 8 — Criação e edição de Padrão de Impressão com fonte institucional

**Ação humana:**
- [x] Acessar no menu superior/lateral: Gerenciamento ➔ Provas ➔ `"**Padrões de impressão**"` (`/membros/padrao/configuracao/`)
- [x] Clicar no botão `"**Cadastrar um novo padrão de impressão**"`
- [x] Preencher o campo de nome do modelo (ex: `"**Padrão Institucional Decisão 2026**"`)
- [x] Na seção `"**Tipo da fonte**"`, verificar que os botões padrão estão visíveis: `"Plex Sans"`, `"Verdana"`, `"Times"`, `"Arial"` e `"Nunito Sans"`
- [x] Verificar logo abaixo a seção com o subtítulo em cinza `"**Fontes da instituição**"` exibindo o botão `"**Institucional Decisão Sans**"` ![alt text](../evidencias/image-14.png)
- [x] Clicar no botão `"**Institucional Decisão Sans**"` e confirmar que ele fica destacado com fundo azul/laranja (`btn-primary`) enquanto os demais botões ficam com fundo branco
- [x] Preencher os demais campos obrigatórios e clicar no botão `"**Cadastrar padrão de impressão**"`
- [x] Confirmar o redirecionamento com mensagem de sucesso
- [x] Clicar em `"**Editar**"` no padrão recém-criado e validar que o botão `"**Institucional Decisão Sans**"` continua selecionado

**Referência técnica (para automação):**
- URL: `/membros/padrao/configuracao/cadastrar/`
- Seletor: `div.btn-group-toggle label:has-text("Institucional Decisão Sans") input[type="radio"]`
- Estado esperado: `examPrintConfig.clientPrintFont == "<uuid>"` e `examPrintConfig.fontFamily == 0`
- Fixture: `POST /api/v2/clients/print-configs/`

---

### 5.4 Modal de Impressão e Malote (Cadernos, Aplicações e Ensalamento) [Automatizável ✅]

Persona: **Coordenação da Rede Decisão**.

#### Cenário 9 — Modal de impressão rápida de caderno

**Ação humana:**
- [x] Acessar a listagem de cadernos em `"**Cadernos**"` (`/provas/`)
- [x] Localizar um caderno da Rede Decisão (ex: `"**Caderno para revisão 1**"`) e clicar no botão de impressão `(ícone de impressora)` para abrir o modal de configuração
- [x] Localizar a seção `"**Tipo de fonte:**"`
- [x] Confirmar que além dos 5 botões padrão, é exibida a seção `"**Fontes da instituição**"` com o botão `"**Institucional Decisão Sans**"`
- [x] Clicar no botão `"**Institucional Decisão Sans**"` e confirmar que ele ganha a classe ativa de destaque
- [ ] Clicar no botão `"**Imprimir prova**"` e verificar que a requisição de impressão é disparada

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: `#modal-print-exam label:has-text("Institucional Decisão Sans")`
- Estado esperado: `examPrintConfig.clientPrintFont == "<uuid>"` enviado nos parâmetros de impressão

#### Cenário 10 — Modal de impressão de malote em Aplicações Presenciais

**Ação humana:**
- [ ] Acessar o menu `"**Aplicações**"` e abrir a aba `"**Presencial**"`
- [ ] Em uma aplicação da Rede Decisão com a prova vinculada, clicar em `"**Opções**"` ➔ `"**Todos os alunos**"` para abrir o modal de malote
- [ ] Rolar até a seção `"**Tipo da fonte**"`
- [ ] Verificar a presença dos botões padrão e da seção `"**Fontes da instituição**"`
- [ ] Clicar na fonte `"**Institucional Decisão Sans**"`
- [ ] Clicar em `"**Imprimir malote**"`
- [ ] Confirmar que o malote é colocado na fila de exportação sem erros 500

**Referência técnica (para automação):**
- URL: `/aplicacoes/?category=presential`
- Seletor: `label:has-text("Institucional Decisão Sans")` dentro do modal de malote
- Estado esperado: `POST /aplicacoes/api/aplicacao/<uuid>/imprimir-malote/` com `clientPrintFontId: "<uuid>"`

---

### 5.5 Renderização do Caderno e Impressão PDF [Apenas Manual 👁]

Persona: **Coordenação da Rede Decisão**.

#### Cenário 11 — Renderização da fonte institucional com `@font-face` na prova impressa

**Ação humana:**
- [ ] Abrir a pré-visualização da impressão (ou o arquivo PDF gerado) do caderno configurado com a fonte `"**Institucional Decisão Sans**"`
- [ ] Abrir as ferramentas de desenvolvedor (F12) na visualização HTML da prova
- [ ] Inspecionar a tag `<style>` no `<head>` do documento e confirmar a presença da declaração:
  ```css
  @font-face {
      font-family: "LizeClientFont-<hash>";
      src: url(".../clients/print-fonts/decisao_sans.woff2");
      font-display: swap;
  }
  ```
- [ ] Inspecionar a tag `<body>` e confirmar que a regra CSS aplicada é:
  ```css
  font-family: "LizeClientFont-<hash>", "Noto Sans Math", sans-serif !important;
  ```
- [ ] Inspecionar o texto dos enunciados e alternativas das questões e confirmar que a tipografia renderizada visualmente corresponde à fonte institucional enviada no upload

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/imprimir`
- Seletor: `style:has-text("@font-face")`, `body`
- Estado esperado: `print_font_face_css` preenchido e tipografia customizada renderizada

#### Cenário 12 — Correção de regressão histórica: Nunito Sans como fonte padrão

**Ação humana:**
- [ ] Na diagramação de um caderno, selecionar a fonte `"**Nunito Sans**"` (opção 4 das fontes padrão)
- [ ] Salvar e abrir a pré-visualização de impressão
- [ ] Inspecionar a tag `<body>` e o CSS da página
- [ ] Confirmar que o `font-family` é exatamente:
  ```css
  font-family: "Nunito Sans", "Noto Sans Math", sans-serif !important;
  ```
- [ ] Confirmar visualmente que o texto está renderizado com a família **Nunito Sans** (arredondada), e **NÃO** com IBM Plex Sans (que era o bug legado de fallback)

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/imprimir`
- Seletor: `body`
- Estado esperado: `print_font_family` contém `"Nunito Sans"`

#### Cenário 13 — Fallback gracioso ao desativar a fonte no Admin após uso

**Ação humana:**
- [ ] Com o caderno da Rede Decisão previamente configurado com `"**Institucional Decisão Sans**"`, acessar o Admin Lize como staff
- [ ] Desativar a fonte (`is_active = False`) e salvar
- [ ] Retornar à diagramação do caderno como Coordenação da Rede Decisão e recarregar a tela
- [ ] Confirmar que o sistema faz o fallback suave para a fonte padrão (Plex Sans) sem tela branca (erro 500)
- [ ] Abrir a impressão do caderno e verificar que a prova é renderizada normalmente usando a fonte padrão

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/imprimir`
- Seletor: `body`
- Estado esperado: Retorno HTTP 200, fallback para `IBM Plex Sans`

---

### 5.6 Segurança e Validação Multi-tenant na API [Automatizável ✅]

Persona: Desenvolvedor / Automação de Segurança via API.

#### Cenário 14 — Tentativa de vincular fonte de outro cliente retorna HTTP 400

**Ação humana:**
- [ ] Executar uma chamada de API `PATCH /api/v1/exams/<exam_b_id>/print-config/` autenticado como Coordenação do Cliente B, enviando no payload o ID da fonte pertencente à Rede Decisão:
  ```json
  {
    "clientPrintFont": "<id_da_fonte_da_rede_decisao>"
  }
  ```
- [ ] Confirmar que a API responde com status **HTTP 400 Bad Request**
- [ ] Confirmar que a mensagem de erro retornada é: `"A fonte selecionada não pertence ao cliente deste caderno."`
- [ ] Confirmar que a configuração do caderno do Cliente B permanece inalterada

**Referência técnica (para automação):**
- URL: `PATCH /api/v1/exams/<uuid>/print-config/`
- Seletor: Resposta da API
- Estado esperado: Status 400 com payload `{"client_print_font": ["A fonte selecionada não pertence ao cliente deste caderno."]}`

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Comparação de Layout no Diagramador:** Comparar a interface do acordeon `"Fonte"` com o arquivo de referência `openspec/changes/fonte-cliente-diagramacao-86ak8t0xb/references/diagram-tipo-fonte.html`. O `<select>` deve apresentar agrupamento limpo com `optgroup` e texto de rodapé discreto.
- [ ] **Comparação de Layout nos Modais:** Comparar os modais de impressão (`modal_print.html` e `exam_configs_form.html`) com a referência `references/modal-tipo-fonte.html`. Os botões das fontes institucionais devem quebrar linha harmoniosamente com `flex-wrap` e espaçamento uniforme (`gap: 0.5rem`).
- [ ] **Múltiplas Fontes Institucionais (Stress Test Visual):** Cadastrar 4 ou mais fontes ativas para o mesmo cliente e confirmar que a interface:
  - No Diagramador: o select expande verticalmente sem quebrar o acordeon.
  - Nos Modais: os botões quebram linha elegantemente sem vazar as margens do modal.
- [ ] **Fórmulas e Símbolos Matemáticos:** Verificar na prova impressa que expressões matemáticas (KaTeX / MathJax) permanecem renderizadas com sua fonte matemática nativa (`Noto Sans Math`), sem sofrer distorção pela fonte institucional do cliente.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Espaço reservado para documentação de divergências ou comportamentos inesperados durante a execução do roteiro pelo QA.

- **Exemplo de formato para registro de falhas:**
  > [!BUG]
  > **[UX/UI] Quebra visual no modal com nome de fonte muito longo**
  > - **Contexto / Causa Raiz:** Se o CS cadastrar uma fonte com nome de 80 caracteres, o botão no modal de impressão não quebra o texto.
  > - **Comportamento Esperado:** O texto do botão deve truncar com ellipsis (`tw-truncate`) ou permitir quebra de linha.
  > - **Workaround:** Limitar o rótulo da fonte no admin a nomes curtos (ex: até 25 caracteres).

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Débito de Identificador Estável no Diagramador:**
> O elemento `<select>` de Tipo de Fonte em `diagram_layout_font.html` não possui atributo `id`. Recomenda-se adicionar `id="id-diagram-font-family"` para estabilidade absoluta em futuros scripts de teste automatizado Playwright.

> [!NOTE]
> **Limite Flexível de Fontes por Cliente:**
> A remoção da restrição de 3 fontes (commit `e3e4af064`) conferiu flexibilidade total à equipe de CS, porém recomenda-se monitorar se escolas com mais de 8 fontes podem sobrecarregar a altura do modal de impressão.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Mapeamento: diagram_layout_font.html](file:///home/israel/Workspace/lizeedu/.ai_qa_acervo/docs/tests/usability/diagram_layout_font.md)**
- 🔗 **[Mapeamento: modal_print.html](file:///home/israel/Workspace/lizeedu/.ai_qa_acervo/docs/tests/usability/modal_print.md)**
- 🔗 **[Mapeamento: exam_configs_form.html](file:///home/israel/Workspace/lizeedu/.ai_qa_acervo/docs/tests/usability/exam_configs_form.md)**
- 🔗 **[Mapeamento: print_defaults_create_update.html](file:///home/israel/Workspace/lizeedu/.ai_qa_acervo/docs/tests/usability/print_defaults_create_update.md)**

### Automation Snippet (Python + Playwright / Mixer Setup):

```python
import pytest
from playwright.sync_api import Page, expect
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, ClientPrintFont, ExamPrintConfig
from fiscallizeon.exams.models import Exam

def test_select_client_print_font_in_diagrammer(page: Page, live_server):
    # 1. Setup de banco via Mixer
    client = mixer.blend(Client, name="Escola Playwright")
    unity = mixer.blend('clients.Unity', client=client)
    coord = mixer.blend('clients.SchoolCoordination', unity=unity)
    user = mixer.blend(User, email="coord@escola.local", user_type='coordination', two_factor_enabled=False)
    user.set_password("123456")
    user.save()
    mixer.blend('clients.CoordinationMember', user=user, coordination=coord)
    user.user_permissions.add(Permission.objects.get(codename='can_diagram_exam'))
    user.user_permissions.add(Permission.objects.get(codename='view_exam'))
    
    # Elevação de permissões para garantir visibilidade da UI
    user.is_superuser = True
    user.save()

    # Fonte extra do cliente
    font = ClientPrintFont(client=client, label="Fonte Automação", is_active=True, sort_order=1)
    font.font_file.name = "clients/print-fonts/font_auto.woff2"
    font.save()

    config = ExamPrintConfig.objects.create(client=client, name="Cfg Auto", font_family=0)
    exam = mixer.blend(Exam, name="Prova Teste", is_printed=False, exam_print_config=config, coordinations=[coord])

    # 2. Login
    page.goto(f"{live_server.url}/conta/entrar/")
    page.fill('input[name="username"]', "coord@escola.local")
    page.fill('input[name="password"]', "123456")
    page.click('button[type="submit"]')

    # 3. Navegar para Diagramação
    page.goto(f"{live_server.url}/provas/{exam.pk}/v2/imprimir/")
    
    # 4. Abrir Acordeon Fonte
    page.locator('text="Fonte"').first.click()

    # 5. Selecionar Fonte Institucional
    select_font = page.locator('select:has(optgroup[label="Padrão Lize"])')
    expect(select_font).to_be_visible()
    select_font.select_option(value=f"custom:{font.pk}")

    # 6. Salvar e Validar Persistência
    page.locator('button:has-text("Salvar e visualizar")').click()
    page.wait_for_timeout(1000)

    # Validar no banco de dados
    config.refresh_from_db()
    assert config.client_print_font_id == font.pk
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalos identificados:** A criação de arquivos de fontes exige arquivos válidos de tipografia (`.woff2`, `.ttf`); para testes locais, deve-se usar arquivos reais ou fixtures com extensões corretas devido à chamada `self.full_clean()` no `save()`.
- **Alinhamento Produto vs Desenvolvimento:** Excelente resolução do ponto em aberto do ClickUp relativo ao limite de 3 fontes. O desenvolvedor implementou inicialmente com limite e em seguida removeu de forma limpa no commit `e3e4af064`, mantendo a usabilidade com `flex-wrap` e `<optgroup>`.
- **Evolução do Processo:** A cobertura de testes automatizados do desenvolvedor (`test_client_print_font.py` e `test_exam_print_font_cascade.py`) já cobre 100% das regras críticas de backend e multi-tenant.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
<!-- 1. Padronizar verificação automática de seeds de arquivos estáticos (ex: mock de fontes .woff2) em ambientes isolados de teste. -->
<!-- 2. Adicionar lembrete no prompt sobre regras de sanitização de nomes de arquivos para evitar caracteres especiais em caminhos de upload de mídia. -->

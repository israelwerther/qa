## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-08-18 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Malotes (Geração de PDF / OMR) |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5 estrelas) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Contexto (ClickUp CU-86ajqg20v)
- **Problema:** Na geração de malote com a opção **"Arquivos separados"**, os cadernos já saem como pasta `cadernos/` com 1 PDF por aluno. O gabarito, porém, continua sendo um único PDF consolidado por sala/turma (`gabaritos_{sala}.pdf`), forçando a separação manual.
- **Solução:** Novo boolean no `Client` — **"Separar arquivos de gabaritos"** — que, combinado com o modo "Arquivos separados", faz o gabarito virar uma pasta `gabaritos/` com um PDF por aluno (objetivo + discursivo no mesmo arquivo). Mais de 20 clientes usam `separated`, portanto o novo comportamento é **opt-in** (default `False`) para não quebrar o ZIP de quem já usa.

### Implementação (Backend)
- **Modelo:** `Client.omr_print_separate_answer_sheets` (`BooleanField` "Separar arquivos de gabaritos", default `False`) em `fiscallizeon/clients/models.py:312`.
- **Migração:** `fiscallizeon/clients/migrations/0203_client_omr_print_separate_answer_sheets.py` (adiciona o campo em `Client` e `HistoricalClient`).
- **Form:** `ClientForm` passa a expor `omr_print_separate_answer_sheets` além de `omr_print_file_separation` e `print_essay_questions_default` (`fiscallizeon/clients/forms.py:294`).
- **Empacotador de ensalamento:** `fiscallizeon/distribution/tasks/group_files.py` — novo helper `export_answer_generate_path` (path `{unidade}/{sala}/gabaritos/gabarito_{slug}.pdf` **sem PK**) e `merge_student_sheets_path`. No ramo `BAG_SEPARATED_FILES`, quando o boolean é `True`, faz o loop por aluno via `collect_student_paths` → merge → escrita na pasta `gabaritos/`; omite o consolidado `gabaritos_{room}.pdf`.
- **Empacotador de aplicação:** `fiscallizeon/omr/tasks/group_answer_sheet_files.py` — no ramo separado de `process_unity_separated_files`, a mesma regra por turma (`{coordenação} - {turma}/gabaritos/`). No modelo `reduced` (A5), o modo individual NÃO emparelha alunos (`merge_a5_files` fica fora do caminho individual).
- **Regras transversais:** `default` ignora o boolean; `separated` + `False` mantém o consolidado atual; sem path de gabarito para o aluno → não grava arquivo vazio; sem discursiva → PDF só com objetiva, sem página em branco.

### Implementação (Frontend/UI)
- **Template:** `fiscallizeon/clients/templates/dashboard/members/omr_print_separation_update_or_create.html` — o `<select>` de separação agora é controlado por Vue (`v-model="omrPrintFileSeparation"`) e um switch **"Separar arquivos de gabaritos"** (`custom-switch`, padrão de `print_essay_questions_default`) aparece com `v-if="omrPrintFileSeparation === 'separated'"`. Com o modo **Padrão** o switch fica oculto. O switch **não** foi adicionado ao modal de impressão.

### Testes Automatizados
- **NÃO foram criados** testes específicos para a feature (tasks 6.1–6.4 do `tasks.md` estão em aberto). Os testes existentes de base (`test_group_files.py`, `test_group_answer_sheet_files.py`) continuam válidos para regressão.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- **IN SCOPE:**
  - Exibição do switch "Separar arquivos de gabaritos" na tela **Configurações → Malotes** apenas quando o select estiver em "Arquivos separados".
  - Persistência do boolean no `Client` (default `False`) e renderização no `ClientForm`.
  - Geração do malote (ensalamento **e** aplicação) com `separated` + boolean `True`: pasta `gabaritos/` com 1 PDF por aluno, contendo **objetiva + discursiva no mesmo arquivo**, na ordem das folhas customizadas/objetiva/discursiva/rascunho/redação.
  - Filename `gabarito_{slug-do-nome}.pdf` **sem PK** do aluno.
  - Ausência do consolidado `gabaritos_{sala|turma}.pdf` quando o boolean está `True`.
  - Skip silencioso de aluno sem nenhum path de gabarito (sem arquivo vazio).
  - Prova sem gabarito discursivo → PDF individual só com a objetiva, sem erro e sem página em branco.
  - Regressão: cadernos, lista de presença, versões de randomização e páginas customizadas de turma/sala **inalterados** em `separated` (boolean `True` ou `False`).
  - `default` continua gerando PDF único por unidade (boolean é ignorado); `separated` + `False` mantém o gabarito consolidado.

- **OUT OF SCOPE:**
  - Separar gabarito objetivo e discursivo em arquivos distintos por aluno (ambos devem estar no mesmo PDF).
  - Alterar o fluxo de geração dos cadernos individuais (comportamento pré-existente).
  - Reorganização de outras partes do malote além dos gabaritos.
  - Nova option no enum `OMR_PRINT_SEPARATION_CHOICES` (só `default` e `separated`).
  - Exibir o switch no modal de impressão do malote.
  - Alterar o malote ELIT (`omr/tasks/elit/group_answer_sheet_files.py`).
  - Redesign da tela (`base_component`) — ajuste pontual no template legado.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Configurações do cliente | Configurações (entrada do menu) [verificar] | via `core:redirect_dashboard` (redirecionado após salvar) | `core:redirect_dashboard` |
| Configurações → Malotes | Aba **"Malotes"** no header `configurations_header.html` (visível com permissão `clients.change_clientteacherobligationconfiguration`) [verificar] | `/membros/configuracao/malotes/<uuid:pk>/` | `clients:update_client_omr_configuration` (`ConfigOMRConfigurationUpdateView`) |
| Geração de malote (ensalamento) | Lista de ensalamentos / "Gerar malote" (modal de impressão) [verificar] | fluxo `distribution` (modal) | `group_files` (Celery `omr-export`) |
| Geração de malote (aplicação) | Aplicações / "Gerar malote" (modal de impressão) [verificar] | fluxo `omr` (modal) | `group_answer_sheet_files` (Celery `omr-export`) |

> **Nota:** A permissão da view é `clients.change_confignotification`, mas o link **"Malotes"** no header de configurações é renderizado sob `clients.change_clientteacherobligationconfiguration` (`configurations_header.html:11-12`). Verificar na validação se um usuário com uma permissão mas não a outra consegue acessar a tela (possível inconsistência de visibilidade → registrar em Seção 7 se reproduzir).

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### 4.1 Execução da Suíte de Testes Locais (regressão de base)
```bash
# Docker (recomendado)
python scripts/tests/generate-new-test-db.py  # apenas se o test DB ainda não existir
./scripts/tests/run-tests.sh --no-tty fiscallizeon/distribution/tests/test_group_files.py fiscallizeon/omr/tests/test_group_answer_sheet_files.py

# Local (sem Docker)
pytest fiscallizeon/distribution/tests/test_group_files.py fiscallizeon/omr/tests/test_group_answer_sheet_files.py
```

> **GAP:** Não existem testes automatizados cobrindo `omr_print_separate_answer_sheets` (pasta `gabaritos/`, filename sem PK, skip de paths vazios, `default` ignorando o boolean). Recomenda-se criar antes do merge (tasks 6.1–6.4 do OpenSpec) — ver Seção 8.

### 4.2 Definição de Personas
- **Persona Coordenador de Malotes:** Usuário com `user_type` em `settings.COORDINATION`, vinculado ao `Client` alvo (`user.client == client`) e com permissão `clients.change_confignotification` para abrir Configurações → Malotes. Idealmente também `clients.change_clientteacherobligationconfiguration` (para ver o link "Malotes").
- **Persona Coordenador de Aplicação (geração de malote):** Mesmo perfil, realizando a geração do malote a partir da aplicação/ensalamento.

### 4.3 Setup de Dados via Mixer (Python Snippet)
```python
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember

# 1. Cliente no modo "Arquivos separados" + boolean ligado
client = mixer.blend(
    Client,
    has_omr=True,
    omr_print_file_separation=Client.BAG_SEPARATED_FILES,   # 'separated'
    omr_print_separate_answer_sheets=True,                   # opt-in da feature
)

# 2. Persona coordenadora com as permissões da tela
coord = mixer.blend(User, client=client, user_type='coordination', is_superuser=True)
coord.user_permissions.add(
    Permission.objects.get(codename='change_confignotification')
)
coord.user_permissions.add(
    Permission.objects.get(codename='change_clientteacherobligationconfiguration')
)

# 3. Infraestrutura (unidade / coordenação / turma)
unity = mixer.blend(Unity, client=client, name='Unidade Norte')
coordination = mixer.blend(SchoolCoordination, unity=unity, name='Coord Norte')
mixer.blend(CoordinationMember, user=coord, coordination=coordination)
```
Para o cenário de geração de malote com alunos da mesma turma, reutilizar o padrão de `fiscallizeon/omr/tests/test_group_answer_sheet_files.py` (aplicação) e `fiscallizeon/distribution/tests/test_group_files.py` (ensalamento): `Application` + `ApplicationStudent` + alunos na mesma `SchoolClass`/`Room`, com caderno contendo questões objetivas (CHOICE) e discursivas (TEXTUAL, `is_essay=False`), e selecionar **"Incluir folhas de respostas discursivas"** no modal de geração.

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona ativa:** Coordenador de Malotes (perfil COORDINATION vinculado ao Client em teste).

### 5.1 Configuração — Switch "Separar arquivos de gabaritos" [Automatizável ✅]

#### Cenário 1 — Acesso à tela Configurações → Malotes
- [x] Fazer login como Coordenador de Malotes.
- [x] Navegar até Configurações e abrir a aba **"Malotes"**.
- [x] Confirmar o carregamento da tela em `/membros/configuracao/malotes/<uuid>/` com o título "Configurações" e o campo **"Separação de arquivos na geração de malote"**.

#### Cenário 2 — Switch visível apenas no modo "Arquivos separados"
- [x] No select de separação, escolher **"Arquivos separados"**.
- [x] Confirmar que o switch **"Separar arquivos de gabaritos"** aparece, com o texto de apoio explicando que cada aluno terá seu arquivo de gabarito em uma pasta.
- [x] Alternar o select para **"Padrão (Arquivos juntos)"**.
- [x] Confirmar que o switch **desaparece** da tela.
- [x] Voltar para "Arquivos separados" e confirmar que o switch reaparece.

#### Cenário 3 — Persistência e combinação com o modo atual
- [x] Com o select em "Arquivos separados", marcar o switch "Separar arquivos de gabaritos".
- [x] Clicar em **"Salvar configurações"** e confirmar a mensagem de sucesso ("Configuração de malote alterado com sucesso").
- [x] Reabrir a tela e confirmar que o select continua em "Arquivos separados" e o switch continua marcado.
- [x] Desmarcar o switch, salvar, reabrir e confirmar que a configuração voltou ao estado desmarcado (persistência do default `False`).

---

### 5.2 Geração de Malote (Aplicação) — Pasta `gabaritos/` por aluno [Automatizável ✅]

#### Cenário 4 — Malote com alunos da mesma turma gera pasta `gabaritos/`
- [x] Persona: Coordenador de Aplicação. Cliente em `separated` + switch "Separar arquivos de gabaritos" **marcado**.
- [x] Criar uma aplicação com pelo menos **2 alunos da mesma turma** e um caderno contendo questões objetivas e discursivas (com páginas customizadas, se houver).
- [x] Gerar o malote e, no modal, marcar **"Incluir folhas de respostas discursivas"**.
- [x] Baixar/abrir o ZIP gerado.
- [x] Confirmar a estrutura: `{unidade}/{coordenação} - {turma}/gabaritos/` contendo **um arquivo `.pdf` por aluno** (ex.: `gabarito_joao-da-silva.pdf`).
- [x] Confirmar que **NÃO** existe o arquivo consolidado `gabaritos_{turma}.pdf` nesse modo.
- [x] Abrir o PDF de gabarito de um aluno e confirmar que contém **todas as folhas** na ordem: página(s) customizada(s) da objetiva, folha objetiva, página(s) customizada(s) da discursiva, folha discursiva e rascunho/redação (quando o caderno tiver).
- [x] Confirmar que objetiva e discursiva estão **no mesmo arquivo** (não há PDFs separados por modalidade).

#### Cenário 5 — Prova sem gabarito discursivo gera PDF só com a objetiva
- [x] Criar/generar malote para uma aplicação cujo caderno **não** possui questões discursivas (e sem marcar "Incluir folhas de respostas discursivas").
- [x] Gerar o malote e confirmar que **não há erro** e **não há página em branco** no lugar do discursivo.
- [x] Abrir o PDF individual e confirmar que contém apenas as folhas objetivas do aluno.

#### Cenário 6 — Somente discursiva (sem folha objetiva exportável)
- [x] Gerar malote para um caderno que **não exporta folha objetiva** (modelo de folha sem objetiva) com discursivas incluídas.
- [x] Confirmar que o PDF individual contém apenas as folhas discursivas/redação daquele aluno, sem página em branco da objetiva.

#### Cenário 7 — Aluno sem nenhuma folha de gabarito
- [x] Em uma turma com um aluno sem folha objetiva exportável e sem discursiva incluída.
- [x] Gerar o malote e confirmar que **não** existe arquivo vazio/inválido para esse aluno na pasta `gabaritos/` (o aluno simplesmente não aparece).

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] **Tela Configurações → Malotes:** Capturar print com o select em "Arquivos separados" exibindo o switch "Separar arquivos de gabaritos" (estado marcado e desmarcado).
- [x] Capturar print com o select em "Padrão (Arquivos juntos)" confirmando que o switch está oculto.
- [x] Comparar o switch com o padrão visual do switch de "Incluir impressão do cartão resposta discursiva por padrão" (`print_essay_questions_default`) da mesma tela — mesmo estilo de `custom-switch`.
- [x] Comparar o layout com o mockup de referência `openspec/changes/malote-gabaritos-individuais/references/omr-print-separation-select.html` (estrutura do bloco de separação: select + switch + texto de apoio).
- [x] Verificar alinhamento, espaçamento e legibilidade do texto de apoio ("Ao marcar esta opção, cada aluno terá o seu arquivo de gabarito separado em uma pasta.").

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!BUG]
> **BUG PENDENTE — Ausência de testes automatizados da feature:** As tasks 6.1–6.4 do OpenSpec (`fiscallizeon/distribution/tests/test_group_files.py`, `fiscallizeon/omr/tests/test_group_answer_sheet_files.py`, teste de `ClientForm`) ainda não foram implementadas. Sem eles, regressões futuras na pasta `gabaritos/` (filename sem PK, skip de paths vazios, `default` ignorando boolean) podem passar despercebidas. *(inferência de risco — Spec Gap)*
> - **Contexto/Root Cause:** `tasks.md` mantém 6.1–6.4 sem `[x]`; `git log` da branch não traz commits de teste para a feature.
> - **Expected Behavior:** Testes `CustomTransactionTestCase` + `mixer.blend()` cobrindo o contrato da Seção 4.1.
> - **Workaround (Gambiarra temporária):** Validar manualmente o contrato descrito na Seção 4.1 (filename sem PK e ausência de arquivo vazio).

> [!WARNING]
> **Ponto de atenção — Visibilidade do link "Malotes" vs. permissão da view:** O link "Malotes" no header de configurações depende de `clients.change_clientteacherobligationconfiguration`, enquanto a view exige `clients.change_confignotification`. Verificar se existe usuário com a primeira permissão mas sem a segunda → usuário veria o link e cairia em página de erro.
> - **Contexto/Root Cause:** `configurations_header.html:11-12` vs `ConfigOMRConfigurationUpdateView.permission_required = 'clients.change_confignotification'`.
> - **Expected Behavior:** A visibilidade do link deveria refletir a permissão real da view.
> - **Workaround (Gambiarra temporária):** Conceder ambas as permissões ao usuário de teste.

> [!NOTE]
> **Observação de UX — `hasDateError()` desabilitando o botão salvar:** O botão "Salvar configurações" usa `:disabled="hasDateError()"`, que depende de campos de notificação herdados da mesma página (Vue `el: '#app'`). Como o switch de gabaritos está na mesma instância Vue, validar que salvar com datas de notificação válidas não bloqueia a persistência do switch.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Testes automatizados da feature (tasks 6.1–6.4 do OpenSpec):** Criar testes de `CustomTransactionTestCase` cobrindo: `separated` + `True` grava `gabaritos/` por aluno; merge inclui objetiva + discursiva; skip de paths vazios; `separated` + `False` grava `gabaritos_{sala|turma}.pdf`; `default` ignora o boolean; `ClientForm` expõe o campo e mantém `OMR_PRINT_SEPARATION_CHOICES` com apenas `default` e `separated`.

> [!NOTE]
> **Colisão de homônimos na pasta `gabaritos/`:** Como os filenames usam slug sem PK, homônimos na mesma turma/sala colidem no ZIP (última escrita prevalece). Comportamento já existe nos cadernos com páginas customizadas; se virar problema real, adicionar sufixo de PK como no caderno sem custom page (`-{pk[:5]}.pdf`).

> [!NOTE]
> **Volume de merges:** O modo individual executa `merge_urls` por aluno (N merges por sala). Para malotes muito grandes pode aumentar o tempo de geração; monitorar a fila `omr-export` em produção.

> [!NOTE]
> **Alinhamento da permissão do link "Malotes":** Corrigir a divergência entre a permissão do link (`change_clientteacherobligationconfiguration`) e a da view (`change_confignotification`) para evitar link visível sem acesso.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.
🔗 **[Ver Mapeamento de Tela](docs/tests/usability/omr_print_separation_update_or_create.md)**

### Automation Snippet (Python / Playwright — UI de Configuração + Setup de Dados)
```python
import pytest
from playwright.sync_api import Page, expect
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember

@pytest.mark.django_db
def test_malotes_config_switch_separated_only(page: Page, live_server):
    # ---- Setup de dados (backend) ----
    client = mixer.blend(
        Client,
        has_omr=True,
        omr_print_file_separation=Client.BAG_SEPARATED_FILES,
        omr_print_separate_answer_sheets=True,
    )
    coord = mixer.blend("accounts.User", client=client, is_superuser=True)
    coord.user_permissions.add(Permission.objects.get(codename="change_confignotification"))
    coord.user_permissions.add(
        Permission.objects.get(codename="change_clientteacherobligationconfiguration")
    )
    coord.set_password("senha123")
    coord.save()

    # ---- Login da Persona ----
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill('input[name="username"]', coord.email)
    page.fill('input[name="password"]', "senha123")
    page.click('button[type="submit"]')

    # ---- Acessar Configurações → Malotes ----
    page.goto(f"{live_server.url}/membros/configuracao/malotes/{client.id}/")

    # Select de separação (id_ = auto_id do Django)
    select = page.locator('select#id_omr_print_file_separation')
    expect(select).to_be_visible()

    # No modo 'separated', o switch deve estar visível
    expect(page.locator('input#id_omr_print_separate_answer_sheets')).to_be_visible()

    # Alternar para 'default' → o switch some (v-if Vue)
    select.select_option("default")
    expect(page.locator('input#id_omr_print_separate_answer_sheets')).to_be_hidden()
```

> **Nota de automação:** O campo renderiza com `id` Django padrão (`id_omr_print_file_separation`, `id_omr_print_separate_answer_sheets`). O select usa `v-model="omrPrintFileSeparation"` (Vue), portanto a alteração via `select_option` precisa disparar o evento adequado; em Playwright, `select_option` + `expect(...).to_be_hidden()` funcionam porque o Vue escuta `change` nativo do elemento. Para o fluxo de geração de malote, o snippet deve reutilizar o setup de `Application`/`ApplicationStudent` de `fiscallizeon/omr/tests/test_group_answer_sheet_files.py` e interagir com o modal de impressão (marcar "Incluir folhas de respostas discursivas") antes de validar a árvore do ZIP baixado.

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principais gargalos durante os testes:** (a preencher) — Dependência de gerar malotes reais com cadernos contendo objetiva + discursiva + páginas customizadas para validar a ordem das folhas no PDF individual; download e inspeção do ZIP em cada combinação de `separated`/boolean.
- **Interação com Desenvolvimento:** (a preencher) — A OpenSpec detalhou bem o contrato (path, filename sem PK, skip de paths vazios), reduzindo ambiguidades. Faltou a entrega dos testes automatizados junto com o código.
- **Pontos de Melhoria:** (a preencher) — Recomenda-se que o QA rode a suíte de regressão de base (Seção 4.1) e valide os cenários mantidos na Seção 5, dado o risco de quebra para os 20+ clientes em `separated`.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
1. **Validar testes automatizados como critério de prontidão:** O QA_PROMPT_V2 não instrui o agente a verificar se as tasks de teste (`tasks.md` itens `[ ]`) foram entregues antes de declarar o plano "pronto". Sugerir incluir na Seção 1/4 um campo de "gap de testes" quando as tasks de qualidade estiverem em aberto.
2. **Registrar divergências de permissão menu × view:** O mapeamento de navegação deveria sempre confrontar a permissão de renderização do link no template com a `permission_required` da view, gerando alerta automático na Seção 7.
3. **Orientação para estruturas ZIP/PDF no roteiro:** Para features de exportação de arquivos (malotes), adicionar orientação padrão de validação de árvore de ZIP e inspeção visual de PDFs (contagem de páginas, ordem) no Section 5, já que hoje fica a cargo do QA humano improvisar.

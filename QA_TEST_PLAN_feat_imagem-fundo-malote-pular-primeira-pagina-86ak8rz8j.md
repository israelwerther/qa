## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-09-25 |
| **Branch:** | `feat/imagem-fundo-malote-pular-primeira-pagina-86ak8rz8j` |
| **ClickUp:** | Imagem de fundo só em páginas sem cabeçalho (`86ak8rz8j`, status `testing`) |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Diagramação / Impressão de cadernos / Malotes (aplicação e ensalamento) / Padrão de impressão |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (proposal, design, spec, tasks e references completos em `openspec/changes/imagem-fundo-pular-primeira-pagina-86ak8rz8j/`) |

## 1. Summary of Changes (Resumo das Alterações)

- **Backend — persistência (`fiscallizeon/clients/models.py` + migration `0212_examprintconfig_skip_background_first_page.py`):**
  - Novo `ExamPrintConfig.skip_background_first_page` (`BooleanField`, default `False`, sem `HistoricalRecords`).
  - `Exam.get_filters_to_print()` passa a incluir `skip_background_first_page` como inteiro `0`/`1`.
- **Backend — serializers/APIs (v1, sem endpoint novo):**
  - `ExamPrintConfigUpdateApi.BaseSerializer` + `InputSerializer.update` aceitam e persistem o campo (`fiscallizeon/exams/apis.py`).
  - `ExamPrintConfigViewSet` expõe o campo no CRUD de padrão de impressão.
  - `ExamPdfPreviewApi`: quando há `background_image_url`, envia `skip_background_first_page` boolean no JSON de `print_to_file`.
  - Malotes: `applications/api/exams_bag.py` e `distribution/api/exams_bag.py` mapeiam `skipBackgroundFirstPage` → `skip_background_first_page` em `exam_params`.
  - Task `export_exam_application_student` (fila `omr-export`): inclui `skip_background_first_page` no payload de `print_to_spaces` somente se `background_image_url` for enviado.
  - View de diagramação `ExamPrintV2View` inclui `skipBackgroundFirstPage` em `exam_print_config_data`.
- **Frontend — 4 superfícies (ajuste em template existente, sem `redesign/base_component`):**
  - Diagramação nova (Alpine): switch em `diagram_layout_structure.html` + estado em `diagram_layout_list.js` (`sectionFieldsMap.structure`, default `false`, body de `saveLayoutSettings`).
  - Diagramação Vue legada: estado em `v2/exam_print.html` (`skipBackgroundFirstPage`, `handleSubmitExamPrintConfig`).
  - Malote de aplicações + padrão de impressão (Vue compartilhado): `custom-switch` em `exam_configs_form.html`; inicialização em `application_list_new.html` e `print_defaults_create_update.html`.
  - Malote de ensalamento (Vue): controle em `modal_print.html`; sincronização em `distribution_list.html`.
  - Texto do controle em todas as telas: **"Não adicionar imagem à primeira página"**, visível somente quando há imagem de fundo selecionada.
- **Testes automatizados novos:** `test_skip_background_first_page.py`, `test_exams_bag_api.py` (skip), `test_exams_bag_skip_background.py`, `test_export_exam_application_student.py` (`TestExportExamApplicationStudentSkipBackground`).

## 2. Scope Boundaries (Diferenças de Escopo)

- IN SCOPE: exibir o switch somente com imagem de fundo selecionada nas 4 superfícies acima.
- IN SCOPE: persistir `skip_background_first_page` por `ExamPrintConfig` do `Client` (default `False`, retrocompatível).
- IN SCOPE: encaminhar o boolean ao print service junto de `background_image_url` no preview da diagramação e nos malotes de aplicação e ensalamento.
- IN SCOPE: comportamento default desligado = imagem em todas as páginas (regressão).
- IN SCOPE: comportamento ligado = imagem some na **primeira página** do caderno e permanece nas demais.
- OUT OF SCOPE: aplicar skip em gabaritos, listas de presença, páginas customizadas ou folhas discursivas (conforme OpenSpec: não-objetivos).
- OUT OF SCOPE: alterar o serviço de PDF (o parâmetro já existia no serviço; só o encaminhamento foi ligado).
- OUT OF SCOPE: criar endpoint novo em `/api/v3/` ou componente django-components novo.
- OUT OF SCOPE: regenerar PDFs/malotes já exportados — a opção vale nas exportações seguintes.
- OUT OF SCOPE / SPEC GAP CONHECIDO: a descrição do ClickUp fala em ocultar a imagem em **todas** as "páginas que têm cabeçalho" (inclusive início de disciplina e repetição por disciplina); a implementação desta branch pula **só a primeira página** (conforme OpenSpec `spec.md` e `design.md`). Validar só a primeira página; divergência de "cabeçalho repetido por disciplina" deve ir para a Seção 7 como `[Spec Gap]`, não como falha de regressão.

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Diagramação nova (sidebar Estrutura) | "**Imagem de fundo**" + switch "**Não adicionar imagem à primeira página**" | `/provas/<uuid>/v2/imprimir/` | `exams:exam-print-v2` (`ExamPrintV2View`) |
| Diagramação Vue legada [verificar se ainda roteável em prod] | "**Selecione uma imagem de fundo**" + switch "**Não adicionar imagem à primeira página**" | `/provas/<uuid>/v2/imprimir/` (mesma rota, template legado `v2/exam_print.html`) [verificar] | `exams:exam-print-v2` |
| Malote de aplicações (modal) | Aplicações → Presencial [verificar rótulo da aba] → "**Opções**" → "**Todos os alunos**" → modal "**Configure a impressão do malote…**" [verificar título exato] | `/aplicacoes/?category=presential` + `POST /aplicacoes/api/aplicacao/<uuid>/imprimir-malote/` | `applications:applications_list` / `applications:applications_export_exams_bag` |
| Malote de ensalamento (modal) | Aplicações → **Ensalamento** [verificar] | `/ensalamento/` + `POST .../ensalamento/api/ensalamentos/<uuid>/gerar-malote/` | `distribution:distribution_list` / `distribution:export_distribution_exams_bag` |
| Padrão de impressão (criar/editar) | Gerenciamento → Provas → **Padrões de impressão** → "**Cadastrar um novo padrão de impressão**" / "**Editar o padrão de impressão**" | `/membros/padrao/configuracao/cadastrar/` e `/membros/padrao/configuracao/atualizar/<uuid>/` | `clients:print-configs-create` / `clients:print-configs-update` |

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

Persona executora: **coordenação do mesmo `Client`** (`user_type='coordination'`), com `exams.can_diagram_exam`, `exams.can_print_exam`, `exams.view_exam`, `clients.view_examprintconfig` (+ `add`/`change` para padrão). Aluno e fiscal não veem o controle.

Comandos (Cloud Lab, sem container `tests`):

```bash
source .venv/bin/activate && pytest fiscallizeon/exams/tests/test_skip_background_first_page.py fiscallizeon/applications/tests/test_exams_bag_api.py fiscallizeon/distribution/tests/api/test_exams_bag_skip_background.py fiscallizeon/applications/tests/tasks/test_export_exam_application_student.py --reuse-db
```

Com Docker (fluxo de PR):

```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/exams/tests/test_skip_background_first_page.py fiscallizeon/applications/tests/test_exams_bag_api.py fiscallizeon/distribution/tests/api/test_exams_bag_skip_background.py fiscallizeon/applications/tests/tasks/test_export_exam_application_student.py
```

Setup de dados (mixer — espelha `test_skip_background_first_page.py`):

```python
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, ExamPrintConfig
from fiscallizeon.exams.models import Exam, ExamBackgroundImage

client_obj = mixer.blend(Client)
unity = mixer.blend('clients.Unity', client=client_obj)
coordination = mixer.blend('clients.SchoolCoordination', unity=unity)
user = mixer.blend(User, user_type='coordination', two_factor_enabled=False, must_change_password=False)
mixer.blend('clients.CoordinationMember', user=user, coordination=coordination)
user.user_permissions.add(Permission.objects.get(codename='can_diagram_exam'))
user.user_permissions.add(Permission.objects.get(codename='view_exam'))
background = mixer.blend(ExamBackgroundImage, client=client_obj, name='Fundo QA')
config = ExamPrintConfig.objects.create(client=client_obj, name='Padrão QA', background_image=background, skip_background_first_page=True)
exam = mixer.blend(Exam, is_printed=False, exam_print_config=config, coordinations=[coordination])
# Para malote: mixer.blend('applications.Application', exam=exam) + ApplicationStudent com 2+ alunos e caderno de 2+ páginas
```

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

Persona ativa em todos os cenários: **coordenação do `Client` dono do caderno** (login de coordenação; caderno com 2+ páginas e imagem de fundo cadastrada em Gerenciamento → Provas).

### 5.1 Diagramação (Alpine + Vue legado) [Automatizável ✅]

#### Cenário 1 — Switch aparece só com imagem e persiste

**Ação humana:**
- [x] Abrir a diagramação do caderno e expandir a seção "**Estrutura**" (sidebar com "**Cabeçalho**", "**Imagem de fundo**")
- [x] Deixar o seletor "**Imagem de fundo**" em "**Não aplicar imagem de fundo**" e confirmar que o switch "**Não adicionar imagem à primeira página**" não aparece
- [x] Selecionar uma imagem de fundo e confirmar que o switch "**Não adicionar imagem à primeira página**" aparece logo abaixo do seletor (toggle apagado por padrão)
- [x] Ligar o switch, salvar pela ação "**Salvar e visualizar**", recarregar a diagramação e confirmar que o switch continua ligado

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/v2/imprimir/`
- Seletor: select `x-model="examPrintConfig.backgroundImage"` + switch `x-model="examPrintConfig.skipBackgroundFirstPage"`
- Estado esperado: bloco do switch com `x-show="examPrintConfig.backgroundImage"`; trilho laranja quando ligado
- Fixture: `mixer.blend(ExamBackgroundImage)` + `ExamPrintConfig(background_image=background)`

#### Cenário 2 — Preview/PDF respeita o skip na primeira página

**Ação humana:**
- [x] Com o switch desligado, gerar o preview/PDF e confirmar visualmente que a imagem de fundo aparece já na primeira página (capa com cabeçalho)
- [x] Ligar o switch "**Não adicionar imagem à primeira página**", salvar e gerar o preview/PDF de novo
- [x] Confirmar no PDF que a primeira página está sem a imagem de fundo e que a segunda página em diante continua com a imagem
- [x] Repetir com cabeçalho "**Completo**" e com "**Apenas nome do aluno**" (ambos devem pular só a primeira página)

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/v2/imprimir/` (preview via `ExamPdfPreviewApi`)
- Seletor: botão "**Salvar e visualizar**"
- Estado esperado: payload de `print_to_file` com `background_image_url` + `skip_background_first_page: true/false`
- Fixture: caderno com `skip_background_first_page=True/False` + cabeçalho das duas modalidades

### 5.2 Malote de aplicação [Automatizável ✅]

#### Cenário 3 — Malote com e sem skip

**Ação humana:**
- [x] Abrir "**Aplicações**" (lista presencial), abrir o menu "**Opções**" da aplicação e escolher "**Todos os alunos**" (abre o modal de impressão do malote)
- [x] No modal, selecionar uma imagem em "**Selecione uma imagem de fundo**" e confirmar que o switch "**Não adicionar imagem à primeira página**" aparece abaixo do seletor
- [x] Gerar o malote com o switch desligado e confirmar no PDF que a primeira página tem a imagem de fundo
- [x] Gerar o malote com o switch ligado e confirmar no PDF que a primeira página está sem imagem e as demais estão com imagem

**Referência técnica (para automação):**
- URL: `/aplicacoes/?category=presential` + `POST /aplicacoes/api/aplicacao/<uuid>/imprimir-malote/`
- Seletor: `#id-exam-background-image` + `#id-skip-background-first-page`
- Estado esperado: `exam_params` com `skip_background_first_page` correspondente; task `export_exam_application_student` envia boolean só com `background_image_url`
- Fixture: `mixer.blend('applications.Application', exam=exam)` + `ApplicationStudent`

### 5.3 Malote de ensalamento [Automatizável ✅]

#### Cenário 4 — Modal de ensalamento propaga o skip

**Ação humana:**
- [ ] Abrir "**Ensalamento**" (listagem `/ensalamento/`) e abrir o modal de impressão do malote
- [ ] Selecionar uma imagem em "**Imagem de fundo:**" (opção diferente de "**Não há imagem de fundo**") e confirmar que o switch "**Não adicionar imagem à primeira página**" aparece abaixo do seletor
- [ ] Gerar o malote com o switch ligado e confirmar no PDF que a primeira página está sem imagem e as demais estão com imagem
- [ ] Gerar com o switch desligado e confirmar que a imagem volta a todas as páginas

**Referência técnica (para automação):**
- URL: `/ensalamento/` + `POST .../ensalamento/api/ensalamentos/<uuid>/gerar-malote/`
- Seletor: `#id_background_image` + `#id_skip_background_first_page`
- Estado esperado: `exam_params` com `skip_background_first_page`; payload de `print_to_spaces` com boolean
- Fixture: `RoomDistribution` com alunos alocados + imagem de fundo do `Client`

### 5.4 Padrão de impressão da escola [Automatizável ✅]

#### Cenário 5 — Padrão salva e é herdado

**Ação humana:**
- [x] Abrir "**Padrões de impressão**" (Gerenciamento → Provas) e criar um padrão novo com imagem de fundo + switch "**Não adicionar imagem à primeira página**" ligado
- [x] Salvar pela ação "**Cadastrar padrão de impressão**", reabrir em "**Editar o padrão de impressão**" e confirmar que o switch continua ligado
- [x] Aplicar esse padrão num caderno/malote e confirmar no PDF o comportamento de pular a primeira página
- [x] Criar um padrão sem imagem e confirmar que o switch nem aparece (não há o que pular)

**Referência técnica (para automação):**
- URL: `/membros/padrao/configuracao/cadastrar/` e `/membros/padrao/configuracao/atualizar/<uuid>/`
- Seletor: `#id-exam-background-image` + `#id-skip-background-first-page`
- Estado esperado: `GET/PATCH /api/v1/clients/print-configs/` com `skipBackgroundFirstPage` persistido
- Fixture: `ExamPrintConfig.objects.create(client=..., background_image=..., skip_background_first_page=True)`

### 5.5 Regressão e compatibilidade [Apenas Manual 👁]

#### Cenário 6 — Cadernos antigos não mudam sem opt-in

**Ação humana:**
- [x] Abrir um caderno configurado antes desta branch (ou nunca tocado no switch) e confirmar que o switch inicia desligado
- [x] Gerar o PDF sem tocar no switch e confirmar que a imagem continua em todas as páginas, inclusive a primeira
- [x] Limpar a imagem de fundo (voltar para "**Não aplicar imagem de fundo**") com o switch ligado e confirmar que o PDF sai sem imagem em nenhuma página e sem erro

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/v2/imprimir/`
- Seletor: switch "**Não adicionar imagem à primeira página**" (ausente sem imagem)
- Estado esperado: default `False`; sem imagem o payload omite `background_image_url` e `skip_background_first_page`
- Fixture: `ExamPrintConfig` legada sem o campo informado (default `False`)

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Tirar print da sidebar "**Estrutura**" da diagramação com imagem selecionada (switch visível) e sem imagem (switch oculto); comparar com `openspec/changes/imagem-fundo-pular-primeira-pagina-86ak8rz8j/references/diagramacao.html`.
- [ ] Tirar print do modal de malote de aplicação com o switch ligado; comparar com `references/malote-aplicacao-padrao.html`.
- [ ] Tirar print do modal de ensalamento com o switch ligado; comparar com `references/malote-ensalamento.html`.
- [ ] Tirar print do PDF de 2+ páginas nos dois estados (switch ligado/desligado) e anexar como evidência de que só a primeira página muda.
- [ ] Confirmar que o texto é exatamente "**Não adicionar imagem à primeira página**" nas 4 superfícies e que o switch usa o padrão visual da própria tela (Alpine peer laranja na diagramação; `custom-switch` Bootstrap nos modais Vue).

## 7. Bugs and Observations (Problemas Encontrados)

> Instrução: registrar com alerts GitHub (`> [!WARNING]`, `> [!BUG]`) e tags `[UX/UI]`, `[Backend Logic]`, `[Database]`, `[Spec Gap]`. Nunca diga "conforme OpenSpec" de forma genérica — cite `spec.md L.XX` ou marque `(inferência de UX — Spec Gap)`.

> [!NOTE]
> **Template de bug:** Título / Contexto-causa / Comportamento esperado (com citação exata) / Workaround para continuar o roteiro.

Exemplo de lacuna já conhecida nesta task (não preencher como bug sem validar no PDF real):

> [!WARNING]
> **[Spec Gap] Título ClickUp fala em "páginas com cabeçalho", implementação pula só a primeira página.** Contexto: a descrição da task pede ocultar a imagem em qualquer página com cabeçalho (inclusive início de disciplina e repetição por disciplina), mas `spec.md L.54` e `design.md L.49-56` definem skip só na primeira página via `skip_background_first_page`. Esperado desta branch: só a primeira página muda (conforme OpenSpec: spec.md L.58-62). Workaround: validar só a primeira página aqui; abrir follow-up se o cliente exigir skip em todo cabeçalho repetido.

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **WONTFIX nesta branch:** skip em cabeçalho repetido (prova "Por disciplina" / "Por tipo de questão") — o print service só recebe `skip_background_first_page`; pular N páginas exigiria parâmetro novo no serviço.

> [!NOTE]
> **Débito de seletor:** `diagram_layout_structure.html` não tem `id` nos controles (ver `diagram_layout_structure.md`); adicionar `id="id-background-image"` e `id="id-skip-background-first-page"` para automação Playwright estável.

> [!NOTE]
> **Valor órfão:** se o usuário limpar a imagem com skip ligado, o banco mantém `True` (no-op até haver fundo de novo, conforme `design.md L.64`). Avaliar limpar o flag junto ao limpar a imagem por UX.

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/diagram_layout_structure.md)** (novo — sidebar Estrutura da diagramação)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_configs_form.md)** (atualizado — seção imagem de fundo + `#id-skip-background-first-page`)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/modal_print.md)** (atualizado — seção imagem de fundo + `#id_skip_background_first_page`)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/application_list_new.md)** (base do modal de malote de aplicação)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/print_defaults_create_update.md)** (base do padrão de impressão)

Snippet de automação futura (setup + navegação — não só cliques):

```python
# Setup (mixer) — coordenação com permissão de diagramação + caderno com fundo
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, ExamPrintConfig
from fiscallizeon.exams.models import Exam, ExamBackgroundImage

client_obj = mixer.blend(Client)
unity = mixer.blend('clients.Unity', client=client_obj)
coordination = mixer.blend('clients.SchoolCoordination', unity=unity)
user = mixer.blend(User, user_type='coordination', two_factor_enabled=False, must_change_password=False)
mixer.blend('clients.CoordinationMember', user=user, coordination=coordination)
user.user_permissions.add(Permission.objects.get(codename='can_diagram_exam'))
background = mixer.blend(ExamBackgroundImage, client=client_obj)
config = ExamPrintConfig.objects.create(client=client_obj, name='QA skip', background_image=background, skip_background_first_page=True)
exam = mixer.blend(Exam, is_printed=False, exam_print_config=config, coordinations=[coordination])

# Playwright (pseudo): login como coordenação → /provas/<uuid>/v2/imprimir/
# → seção "Estrutura" → select "Imagem de fundo" = background
# → assert switch "Não adicionar imagem à primeira página" visível
# → toggle skip → "Salvar e visualizar" → interceptar preview com skip_background_first_page=true
```

## 9. QA Retrospective (Retrospectiva de QA)

- Qual foi o principal gargalo durante o teste? (preencher após execução)
- Houve muitas idas e vindas com o desenvolvedor? (preencher após execução)
- Como o fluxo de desenvolvimento ou QA desta task poderia ter melhorado? (preencher após execução)

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- (preencher durante a execução: edge case novo, passo faltante ou falha do prompt)

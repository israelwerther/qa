## 0. Metadata (Metadados de QA)

| Campo                      | Valor                                                                                                             |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Data:**                  | 2026-10-21                                                                                                        |
| **Branch:**                | `feat/lista-ensalamento-por-turma-86ajvb3ka`                                                                      |
| **ClickUp:**               | [Lista de ensalamento por turma](https://app.clickup.com/t/86ajvb3ka)                                             |
| **Natureza da Tarefa:**    | `[Business Feature]`                                                                                              |
| **Área da Feature:**       | Ensalamento / Lista de Pátio / Impressão                                                                          |
| **Nível de Risco:**        | Médio                                                                                                             |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (proposal, design, tasks, spec e mockups em `openspec/changes/lista-ensalamento-por-turma-86ajvb3ka/`) |

---

## 1. Summary of Changes (Resumo das Alterações)

**Problema (ClickUp):** no dia da prova, a lista de pátio agrupa alunos **por sala**. O aluno precisa vasculhar sala a sala para achar o nome. Com agrupamento **por turma**, ele vai direto ao bloco da sua turma e lê a sala ao lado do nome.

### Backend

- `DistributionPatioListDetailView` (`fiscallizeon/distribution/views.py`): lê query param `by_class`; expõe `context['by_class']`; `get_template_names()` escolhe `patio_list_by_class.html` ou `patio_list.html`.
- Rota **inalterada**: `/ensalamento/<uuid>/lista/patio/` (`distribution:distribution_patio_list`).
- Params combináveis: `by_class=true`, `two_columns=true`, `hide_dialog=true`.
- Sem migration, sem Celery, sem API nova.

### Frontend / Impressão

- Modal `#patioPrintConfig` em `distribution_list.html`: mantém radios **"Uma coluna"** / **"Duas colunas"** e adiciona switch **"Separar lista por turma"** (`#patio-by-class`).
- `printPatiolist()` monta a query string conforme switch + colunas.
- Template novo `distribution/lists/patio_list_by_class.html`: agrupa por turma (1 turma/página), colunas **Aluno** e **Sala**, ordenação por série (`Grade.order` → `Grade.name` → nome da turma), fallback **"Sem turma"**, split de 2 colunas com `columMin: 25`.

### Testes

- Extensão de `fiscallizeon/distribution/tests/views/test_distribution_views.py` (template, contexto, ordenação, turma vazia, salas distintas, sem turma, two_columns, modal, permissões).

### OpenSpec / Referências

- Mockups: `references/modal-layout-patio.html`, `references/lista-patio-por-turma.html`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- IN SCOPE: Switch **"Separar lista por turma"** no modal de lista de pátio.
- IN SCOPE: Impressão do ensalamento inteiro agrupada por turma, com sala ao lado de cada aluno.
- IN SCOPE: Ordenação turmas por série (`Grade.order`) e, na mesma série, alfabética pelo nome da turma.
- IN SCOPE: Combinação com layout de uma ou duas colunas.
- IN SCOPE: Omitir turmas da escola sem nenhum aluno ensalado.
- IN SCOPE: Grupo **"Sem turma"** no final para aluno sem `SchoolClass` permanente.
- IN SCOPE: Preservar lista de pátio por sala quando o switch estiver desligado.
- OUT OF SCOPE: Incluir a opção por turma no malote (`export_unity_yard_list` / `group_files`) — lista de pátio no malote continua desativada.
- OUT OF SCOPE: Nova rota, endpoint `/api/v3/` ou migration.
- OUT OF SCOPE: Redesign da listagem de ensalamentos / migração para `base_component`.
- OUT OF SCOPE: Alterar a regra de escolha da turma (`prefetched_classes` + `|last`).
- OUT OF SCOPE: Sinalizar no documento alunos da aplicação que **não** foram ensalados (open question do shaping no ClickUp — decisão atual: só entram ensalados).
- OUT OF SCOPE: Alterar lista de presença por sala (código não tocado nesta branch).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino                    | Rótulo real no menu UI                                | URL Django                                                                        | View name                                                  |
| -------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Lista de Ensalamentos      | Menu lateral ➔ **"Aplicações"** ➔ **"Ensalamento"**   | `/ensalamento/`                                                                   | `distribution:distribution_list`                           |
| Abrir ações do ensalamento | Botão **"Opções"** (dropdown na linha)                | —                                                                                 | Vue na listagem                                            |
| Abrir modal de pátio       | Seção **"IMPRESSÃO"** ➔ **"Imprimir lista de pátio"** | abre `#patioPrintConfig`                                                          | `showPrintPatioListModal`                                  |
| Gerar lista por sala       | Modal ➔ switch off + **"Gerar listagem de pátio"**    | `/ensalamento/<uuid>/lista/patio/` (+ `?two_columns=true` opcional)               | `distribution:distribution_patio_list` → `patio_list.html` |
| Gerar lista por turma      | Modal ➔ switch on + **"Gerar listagem de pátio"**     | `/ensalamento/<uuid>/lista/patio/?by_class=true` (+ `&two_columns=true` opcional) | idem → `patio_list_by_class.html`                          |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Persona

- **Coordenação escolar** com cliente que possui módulo de distribuição (`client_has_distribution = True`) e permissão `IsCoordinationExamOwner` sobre os exames do ensalamento.
- Aluno / professor / fiscal **não** acessam esta listagem.

### Comandos de teste

```bash
# Docker (recomendado no repo)
./scripts/tests/run-tests.sh --no-tty fiscallizeon/distribution/tests/views/test_distribution_views.py

# Local (venv)
source venv/bin/activate && pytest fiscallizeon/distribution/tests/views/test_distribution_views.py --reuse-db -q
```

### Pré-requisito de dados para QA manual

Ensalamento **já gerado** com:

- Pelo menos **2 séries** distintas (ex.: 1º e 3º) e **2 turmas na mesma série** (ex.: 1A e 1B).
- Alunos da **mesma turma** em **salas diferentes**.
- Uma turma da escola **sem** nenhum aluno no ensalamento (ex.: 2C) — deve **não** aparecer.
- Opcional: 1 aluno ensalado **sem turma** permanente → grupo **"Sem turma"**.
- Preferencialmente ≥ 25 alunos em uma turma para validar duas colunas (`columMin`).

### Mixer (espelho dos testes da branch)

```python
from django.utils import timezone
from mixer.backend.django import mixer
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.distribution.models import Room, RoomDistribution, RoomDistributionStudent
from fiscallizeon.exams.models import Exam
from fiscallizeon.applications.models import Application

client_obj = mixer.blend(Client, has_distribution=True, require_2fa=False)
unity = mixer.blend(Unity, client=client_obj, name='Unidade Centro')
coordination = mixer.blend(SchoolCoordination, unity=unity)
room = mixer.blend(Room, coordination=coordination, name='Sala 1')
grade_first = mixer.blend(Grade, name='1', order=1)
grade_third = mixer.blend(Grade, name='3', order=10)
room_distribution = mixer.blend(RoomDistribution)
exam = mixer.blend(Exam, client=client_obj)
mixer.blend(Application, room_distribution=room_distribution, exam=exam)

def make_class_student(name, class_name, grade, room=room):
    sc = mixer.blend(
        SchoolClass, name=class_name, grade=grade, coordination=coordination,
        school_year=timezone.now().year, temporary_class=False,
    )
    student = mixer.blend('students.Student', client=client_obj, name=name)
    student.classes.add(sc)
    RoomDistributionStudent.objects.create(
        distribution=room_distribution, student=student, room=room,
    )
    return sc

make_class_student('Zelda Aluna', '3A', grade_third)
make_class_student('Ana Aluna', '1B', grade_first)
make_class_student('Bruno Aluno', '1A', grade_first)
# Turma sem ensalados (não deve sair no PDF):
mixer.blend(
    SchoolClass, name='2C', grade=grade_first, coordination=coordination,
    school_year=timezone.now().year, temporary_class=False,
)
```

URL de smoke direto (substituir UUID):  
`/ensalamento/<pk>/lista/patio/?by_class=true&hide_dialog=true`

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona ativa:** Coordenação com módulo de distribuição e ensalamento com salas alocadas.

### 5.1 Modal — switch e colunas [Automatizável ✅]

#### Cenário 1 — Modal abre com defaults corretos

**Ação humana:**

- [x] Acessar o menu lateral **"Aplicações"** ➔ **"Ensalamento"** (`/ensalamento/`).
- [x] Na linha de um ensalamento com salas, clicar em **"Opções"** (botão branco com borda cinza).
- [x] Na seção cinza **"IMPRESSÃO"**, clicar em **"Imprimir lista de pátio"** (item com ícone de impressora).
- [x] Confirmar que o modal **"Layout da listagem de alunos"** abriu.
- [x] Confirmar que **"Uma coluna"** e **"Duas colunas"** estão visíveis.
- [x] Confirmar que o switch **"Separar lista por turma"** está **desligado** (texto de ajuda: _"Ative esta opção para gerar a listagem com uma turma por página..."_).

**Referência técnica (para automação):**

- URL: `/ensalamento/`
- Seletor: `#patioPrintConfig`, `#patio-by-class`, `label[for="patio-by-class"]`
- Estado esperado: `patioListByClass === false`, `twoColumnsPatioList === 'one'`
- Fixture: ensalamento com `rooms.length > 0`

#### Cenário 2 — Gerar por sala com duas colunas (regressão do fluxo antigo)

**Ação humana:**

- [x] No modal, deixar **"Separar lista por turma"** desligado.
- [x] Selecionar **"Duas colunas"**.
- [x] Clicar em **"Gerar listagem de pátio"**.
- [x] Confirmar que abriu nova aba com URL contendo `two_columns=true` e **sem** `by_class`.
- [x] Confirmar título **"Lista de Pátio"** e agrupamento **por sala** (turma ainda como coluna, comportamento legado).

**Referência técnica (para automação):**

- URL esperada: `/ensalamento/<uuid>/lista/patio/?two_columns=true`
- Seletor: `#patioPrintConfig button:has-text("Gerar listagem de pátio")`
- Estado esperado: template `patio_list.html`, `by_class=False`
- Fixture: mesmo ensalamento do cenário 1

#### Cenário 3 — Gerar por turma com uma coluna

**Ação humana:**

- [x] Reabrir o modal **"Imprimir lista de pátio"**.
- [x] Ligar o switch **"Separar lista por turma"**.
- [x] Manter **"Uma coluna"** selecionado.
- [x] Clicar em **"Gerar listagem de pátio"**.
- [x] Confirmar URL com `by_class=true` e **sem** `two_columns`.
- [x] Confirmar documento com cabeçalho **"Lista de Pátio"**, unidades e blocos **"Turma …"** (não agrupados por sala).

**Referência técnica (para automação):**

- URL esperada: `/ensalamento/<uuid>/lista/patio/?by_class=true`
- Seletor: `#patio-by-class` checked + botão Gerar
- Estado esperado: template `patio_list_by_class.html`, `by_class=True`
- Fixture: alunos em ≥ 2 turmas

### 5.2 Lista impressa por turma — regras de negócio [Automatizável ✅]

> Dica: acrescente `&hide_dialog=true` na URL para inspecionar sem o diálogo de impressão do navegador.

#### Cenário 4 — Ordenação por série e depois alfabética

**Ação humana:**

- [x] Abrir a lista com `by_class=true` em ensalamento com turmas 1A, 1B (série order menor) e 3A (série order maior).
- [x] Confirmar que as páginas/blocos saem na ordem: turmas da série 1 **antes** da série 3.
- [x] Na mesma série, confirmar **"Turma 1A"** antes de **"Turma 1B"** (ordem alfabética).

**Referência técnica (para automação):**

- URL: `/ensalamento/<uuid>/lista/patio/?by_class=true&hide_dialog=true`
- Seletor: `h4 strong` com texto `Turma 1A` / `Turma 1B` / `Turma 3A`
- Estado esperado: ordem DOM das turmas = série ASC + nome ASC
- Fixture: mixer com `Grade.order` 1 e 10 (ver seção 4)

#### Cenário 5 — Sala ao lado do aluno (mesma turma, salas diferentes)

**Ação humana:**

- [x] Localizar o bloco **"Turma …"** de uma turma com alunos em salas distintas.
- [x] Confirmar colunas **"Aluno"** e **"Sala"** (não "Turma").
- [x] Confirmar que cada aluno aparece **uma vez** na mesma tabela da turma, com a sala correspondente na segunda coluna (prefixo "Sala " removido, ex.: nome `"Sala 1"` → `"1"`).

**Referência técnica (para automação):**

- URL: idem `?by_class=true&hide_dialog=true`
- Seletor: `table thead th:has-text("Aluno")`, `th:has-text("Sala")`
- Estado esperado: um único grupo por `schoolClass`; `formatRoomName` no payload
- Fixture: 2 `RoomDistributionStudent` mesma turma, rooms distintos

#### Cenário 6 — Turma sem ensalados não aparece

**Ação humana:**

- [x] Garantir que existe turma na escola (ex.: 2C) **sem** alunos no ensalamento.
- [x] Gerar a lista por turma.
- [x] Confirmar que **não** há cabeçalho **"Turma 2C"** nem página vazia para ela.

**Referência técnica (para automação):**

- URL: `?by_class=true&hide_dialog=true`
- Seletor / assert: ausência de texto `Turma 2C` / `schoolClass: '2C'` no HTML
- Fixture: `SchoolClass` 2C criada sem `RoomDistributionStudent`

#### Cenário 7 — Aluno sem turma

**Ação humana:**

- [ ] ~~Com aluno ensalado sem turma permanente, gerar lista por turma.~~
- [ ] ~~Confirmar grupo **"Sem turma"** **depois** de todas as turmas com série.~~
- [ ] ~~Confirmar que a sala do aluno continua visível na coluna Sala.~~

OBS:

#### ⚠️ Alunos sem turma não aparecem na lista de pátio nem na lista de presença

**Referência técnica (para automação):**

- URL: `?by_class=true&hide_dialog=true`
- Seletor: `h4:has-text("Sem turma")`
- Estado esperado: `schoolClass: ''` no payload → JS mapeia para `"Sem turma"`
- Fixture: `RoomDistributionStudent` sem `student.classes`

#### Cenário 8 — Duas colunas na lista por turma

**Ação humana:**

- [x] No modal, ligar **"Separar lista por turma"** e selecionar **"Duas colunas"**.
- [x] Gerar listagem (URL com `by_class=true&two_columns=true`).
- [x] Em turma com ≥ 25 alunos, confirmar tabela com thead **Aluno | Sala | Aluno | Sala** na mesma página da turma.
- [x] Em turma com poucos alunos (< 25), confirmar layout de uma coluna (sem split).

**Referência técnica (para automação):**

- URL: `/ensalamento/<uuid>/lista/patio/?by_class=true&two_columns=true&hide_dialog=true`
- Seletor: `table thead` com 4 `th` quando `group.split`
- Estado esperado: `twoColumns: true`, `columMin: 25`
- Fixture: turma com ≥ 25 alunos ensalados

### 5.3 Regressão — relatórios existentes [Automatizável ✅]

#### Cenário 9 — Lista de pátio por sala inalterada

**Ação humana:**

- [x] Gerar lista com switch **"Separar lista por turma"** desligado (uma ou duas colunas).
- [x] Confirmar agrupamento **por sala**, com turma na segunda coluna (layout legado de `patio_list.html`).
- [x] Confirmar que o título continua **"Lista de Pátio"**.

**Referência técnica (para automação):**

- URL: `/ensalamento/<uuid>/lista/patio/` ou `?two_columns=true`
- Template esperado: `patio_list.html`
- Estado esperado: `by_class=False`
- Fixture: teste existente `test_lista_patio_inclui_serie_e_turma_ao_lado_do_nome`

#### Cenário 10 — Lista de presença (smoke — fora do diff, critério de aceite ClickUp)

**Ação humana:**

- [x] Acessar a impressão/exportação da **lista de presença por sala** do mesmo ensalamento (fluxo já conhecido da operação — via malote ou detalhe de sala, conforme o cliente usa no dia a dia).
- [x] Confirmar que o documento sai como antes desta entrega (sem agrupamento por turma novo, sem regressão visual óbvia).

**Referência técnica (para automação):**

- URL: `/ensalamento/<uuid_sala>/<uuid_distribution>/lista/presenca/` (`distribution:room_attendance_detail`)
- Nota: nenhum arquivo de presença foi alterado neste PR — smoke de aceite apenas
- Fixture: salas com alunos ensalados

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Tirar prints:
  - (1) modal com switch off, ![](../evidencias/modal_off.png)
  - (2) modal com switch on, ![](../evidencias/modal_on.png)
  - (3) página de uma turma em 1 coluna, ![](../evidencias/1coluna.png)
  - (4) turma em 2 colunas (se massa ≥ 25). ![](../evidencias/2colunas.png)

---

## 7. Bugs and Observations (Problemas Encontrados)

> Instruções ao QA: registrar com `> [!BUG]` ou `> [!WARNING]` e tags `[UX/UI]`, `[Backend Logic]`, `[Database]` ou `[Spec Gap]`.

Formato obrigatório por bug:

1. **Title**
2. **Context/Root Cause**
3. **Expected Behavior** (citar `spec.md` L.XX ou `(inferência de UX — Spec Gap)`)
4. **Workaround**

_(Preencher durante a execução.)_

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Alunos não ensalados:** o shaping do ClickUp deixou em aberto se alunos da aplicação sem sala devem ser sinalizados na lista por turma (hoje ficam de fora, como na lista por sala). Avaliar em change futura se a ausência induz falsa sensação de turma completa.

> [!NOTE]
> **Turma inativa / removida após o ensalamento:** lista por sala exibe turma em branco; na lista por turma o aluno cai em **"Sem turma"**. Documentar para operação se isso for frequente.

> [!NOTE]
> **Malote:** opção por turma propositalmente fora do malote. Se a operação pedir malote com folhas por turma, será outra change.

> [!NOTE]
> **IDs estáveis no HTML impresso:** o template Vue usa interpolação `${…}` sem `data-testid`. Para Playwright robusto, considerar `data-qa` nos cabeçalhos de turma.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django), e não a View.
- 🔗 **[Ver Mapeamento — listagem / modal](../docs/tests/usability/distribution_list.md)** (`distribution_list.html`)
- 🔗 **[Ver Mapeamento — impressão por turma](../docs/tests/usability/patio_list_by_class.md)** (`patio_list_by_class.html`)

### Snippet Playwright + Mixer (rascunho para automação futura)

```python
import re
from django.urls import reverse
from playwright.sync_api import Page, expect

def test_gerar_lista_patio_por_turma(page: Page, live_server, ensalamento_com_turmas):
    """Persona: coordenação autenticada com módulo de distribuição."""
    # Setup: ver fixture em patio_list_by_class.md (mixer + Application + RoomDistributionStudent)
    distribution = ensalamento_com_turmas
    # Elevação de privilégio se a view exigir (espelhar patches dos testes Django):
    # user.is_superuser = True  OU  mock client_has_distribution + IsCoordinationExamOwner

    page.goto(f'{live_server.url}/ensalamento/')
    page.get_by_role('button', name='Opções').first.click()
    page.get_by_role('button', name='Imprimir lista de pátio').click()

    modal = page.locator('#patioPrintConfig')
    expect(modal).to_be_visible()
    expect(page.locator('#patio-by-class')).not_to_be_checked()

    page.locator('#patio-by-class').check()
    with page.expect_popup() as popup_info:
        page.get_by_role('button', name='Gerar listagem de pátio').click()
    report = popup_info.value
    report.wait_for_load_state('domcontentloaded')
    expect(report).to_have_url(re.compile(r'/lista/patio/\?by_class=true'))
    expect(report.get_by_text('Lista de Pátio')).to_be_visible()
    expect(report.locator('h4').filter(has_text='Turma')).to_have_count(
        ensalamento_com_turmas.expected_class_count
    )
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante o teste:** _(preencher)_
- **Ida e volta com o desenvolvedor:** _(preencher)_
- **Como melhorar o fluxo de desenvolvimento/QA desta task:** _(preencher)_

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

- Conflito residual no Prompt V2: Rule 0 pede seletores dentro de **Referência técnica** na seção 5, enquanto Rules 3/4 pedem seletores só em 4/8.1 — o plano desta feature seguiu Rule 0 + padrão do plano de ensalamento misto; vale unificar a regra no prompt.
- ClickUp desta task (seção "Testes") descreve a UI como "checkbox na exportação"; a implementação é **switch** no modal `#patioPrintConfig` — o gerador de plano deve priorizar o DOM/OpenSpec sobre o texto livre do campo Testes do ClickUp.
- Para features de impressão, padronizar no prompt a dica obrigatória de `hide_dialog=true` para inspeção sem `window.print()`.

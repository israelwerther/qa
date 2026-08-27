# QA Test Plan: Customização do Layout de Alternativas (CU-86aj30gzc)

## 0. Metadata (Metadados de QA)

| Campo                      | Valor                                                                                                                                                                                           |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data:**                  | 2026-08-27                                                                                                                                                                                      |
| **Natureza da Tarefa:**    | `[Business Feature]`                                                                                                                                                                            |
| **Área da Feature:**       | Exams / Diagramação / Malote de Provas (PDF impresso)                                                                                                                                           |
| **Nível de Risco:**        | Médio                                                                                                                                                                                           |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5/5) — `proposal.md`, `design.md`, `spec.md` e `tasks.md` cobrem controles granulares, pipeline PDF/malote, defaults e non-goals (sem alterar resolução online nem `reviews.html`). |

**Task ClickUp:** [86aj30gzc — Possibilidade do cliente personalizar padrão de layout de alternativas](https://app.clickup.com/t/86aj30gzc)  
**Branch:** `feat/exam-alternatives-layout-CU-86aj30gzc`  
**Design (referência):** [Setup Global](https://lize-design.vercel.app/pt/dashboard/management/exams?tab=alternatives-layout) · [Diagramação](https://lize-design.vercel.app/pt/dashboard/my-evaluations/cad-001/diagramacao) · [Jam](https://jam.dev/c/da1a39e3-1e72-4836-ae4d-2238f9a44ce4)

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend / Modelos

- Novos campos em `ExamPrintConfig` (`fiscallizeon/clients/models.py`):
  - `alternatives_striped` (default `True`) — zebrado
  - `alternatives_separator_line` (default `True`) — linha horizontal entre alternativas
  - `alternatives_marker` (default `True`) — bolinha vs letra solta
  - `alternatives_marker_color` (0 Preta / 1 Branca, default 0)
  - `alternatives_marker_border` (default `False`)
  - `alternatives_alignment` (0 Centro / 1 Topo, default 0)
- Campo legado `remove_color_alternatives` **depreciado** (mantido no DB até limpeza pós-deploy); UI removida.
- Migrations `0205`–`0209` em `clients`.
- Management command `backfill_alternatives_layout` (`--dry-run`, `--reverse`) para converter configs com `remove_color_alternatives=True` → `alternatives_striped=False` + `alternatives_marker=False`.
- Serializers, `Exam.get_filters_to_print()`, `ExamPrintView`, APIs de malote (`applications/api/exams_bag.py`, `distribution/api/exams_bag.py`) e `omr/mockup_utils.py` passam a propagar os novos parâmetros.

### Frontend

- **Diagramador:** acordeão **Layout de alternativas** (`diagram_layout_alternatives.html`) com toggles Alpine; legado removido de `diagram_layout_print.html`.
- **Modais de malote (Aplicações) + Padrões da escola:** seção **Layout de alternativas** em `exam_configs_form.html` (Vue).
- **Modal de malote (Ensalamento):** controles equivalentes em `modal_print.html`.
- Templates de PDF (`not_separate.html`, `separate_subjects.html`, `separate_category.html`, `exam_print.html`): classes condicionais `table-striped`, borda `#C2C2C2`, `.question-number` / `-white` / `-border`, `align-items-start|center`; `print-color-adjust: exact` para zebrado na impressão.

### Testes

- `fiscallizeon/exams/tests/test_exam_alternatives_layout.py` — modelo, serializers, API, print view, marcador/alinhamento e backfill (~22 cenários).

---

## 2. Scope Boundaries (Diferenças de Escopo)

**IN SCOPE:**

- Configurar layout de alternativas no Diagramador e ver o efeito no preview/PDF.
- Configurar e gerar malote individual e em massa em Aplicações.
- Configurar e gerar malote via Ensalamento.
- Criar/editar **Padrões de impressão** da escola com os novos controles e validar herança em cadernos/modais.
- Combinação estilo ENEM: sem zebrado + sem linha + marcador ativo + alinhamento Topo.
- Ausência do switch legado **"Remover cores das alternativas"** nas UIs listadas.
- Retrocompatibilidade: escola/caderno sem alteração mantém visual clássico (defaults True/Centro/Preta).

**OUT OF SCOPE:**

- Visualização/resolução online de questões pelo aluno (conforme OpenSpec `design.md` Non-Goals).
- Alterações em `reviews.html` / fluxos inertes sem impressão.
- Remoção DDL da coluna `remove_color_alternatives` (deixa para ciclo pós-deploy).
- Redesign geral do diagramador além da seção de alternativas.
- Comparação pixel-perfect com ENEM oficial além dos 4 eixos configuráveis.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino                | Rótulo real no menu UI                                | URL Django                                       | View name                        |
| ---------------------- | ----------------------------------------------------- | ------------------------------------------------ | -------------------------------- |
| Listagem de cadernos   | Cadernos → **Instrumentos avaliativos**               | `/provas/?category=exam`                         | `exams:exams_list`               |
| Diagramador do caderno | Ação do caderno → Diagramar / Imprimir v2 [verificar] | `/provas/<uuid>/v2/imprimir/`                    | `exams:exam-print-v2`            |
| Aplicações presenciais | Aplicações → **Presencial**                           | `/aplicacoes/?category=presential`               | `applications:applications_list` |
| Ensalamento            | Aplicações → **Ensalamento**                          | `/ensalamento/`                                  | `distribution:distribution_list` |
| Padrões de impressão   | Gerenciamento → Provas → **Padrões de impressão**     | `/membros/padrao/configuracao/`                  | `clients:print-configs-list`     |
| Criar padrão           | Botão cadastrar na listagem [verificar]               | `/membros/padrao/configuracao/cadastrar/`        | `clients:print-configs-create`   |
| Editar padrão          | Link da linha na listagem [verificar]                 | `/membros/padrao/configuracao/atualizar/<uuid>/` | `clients:print-configs-update`   |

> **[verificar]** Como o caderno abre o Diagramador a partir da listagem (rótulo exato do menu de opções). Se o texto da UI divergir, tire um print e atualize este mapa + `KI_Navegacao.md`.

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

**Persona (QA manual e automação):** Coordenador da unidade, `user_type='coordination'`, com:

- `exams.view_exam`
- `exams.can_diagram_exam`
- `exams.can_print_exam`
- `clients.view_examprintconfig` (e add/change conforme fluxo de padrões)
- Cliente com `client_has_distribution` se for testar Ensalamento

**Comando (Docker — agents usam `--no-tty`):**

```bash
docker compose --profile test up -d tests
./scripts/tests/run-tests.sh --no-tty fiscallizeon/exams/tests/test_exam_alternatives_layout.py
```

**Mixer setup (padrão do arquivo de teste):**

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, ExamPrintConfig
from fiscallizeon.exams.models import Exam

client_obj = mixer.blend(Client)
unity = mixer.blend('clients.Unity', client=client_obj)
coordination = mixer.blend('clients.SchoolCoordination', unity=unity)
coordinator = mixer.blend(
    User,
    user_type='coordination',
    two_factor_enabled=False,
    must_change_password=False,
)
mixer.blend('clients.CoordinationMember', user=coordinator, coordination=coordination)
for codename in ('view_exam', 'can_diagram_exam', 'can_print_exam'):
    coordinator.user_permissions.add(Permission.objects.get(codename=codename))

config = ExamPrintConfig.objects.create(
    client=client_obj,
    name='ENEM-like',
    alternatives_striped=False,
    alternatives_separator_line=False,
    alternatives_marker=True,
    alternatives_marker_color=0,
    alternatives_marker_border=False,
    alternatives_alignment=1,  # Topo
)
exam = mixer.blend(Exam, exam_print_config=config, is_printed=False, coordinations=[coordination])
```

**Pré-requisito visual:** caderno com pelo menos uma questão objetiva cuja alternativa tenha **texto multilinha** (para validar alinhamento Topo).

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

> **Persona ativa:** Coordenador com permissão de diagramar e gerar malote.

### 5.1 Diagramador — Controles e Persistência [Automatizável ✅ / visual Apenas Manual 👁]

#### Cenário 1 — Seção Layout de alternativas aparece e o legado sumiu

- [x] Abrir um caderno no Diagramador (`/provas/<uuid>/v2/imprimir/`).
- [x] Na sidebar, expandir o acordeão **Layout de alternativas**.
- [x] Confirmar os controles: **Zebrado**, **Linha separadora**, **Marcador das alternativas**, **Cor do marcador**, **Borda no marcador**, **Alinhamento das alternativas**.
- [x] Expandir o acordeão **Impressão** e confirmar que **não** existe o switch **"Remover cores das alternativas"**.

#### Cenário 2 — Zebrado on/off no preview

- [x] Desativar **Zebrado**, clicar em **Salvar e visualizar**.
- [x] No PDF/preview, confirmar fundo uniforme (sem faixas cinza alternadas).
- [x] Reativar **Zebrado**, salvar e visualizar; confirmar retorno do fundo alternado.

#### Cenário 3 — Linha separadora on/off

- [x] Desativar **Linha separadora**, salvar e visualizar; confirmar ausência das linhas horizontais entre alternativas.
- [x] Reativar, salvar e visualizar; confirmar retorno das divisórias.

#### Cenário 4 — Marcador, cor e borda

- [x] Desativar **Marcador das alternativas**; confirmar apenas letra solta (A, B, C…) sem bolinha.
- [x] Reativar marcador; selecionar **Preta (texto branco)** e depois **Branca (texto preto)**; validar cada uma no preview.
- [x] Ativar **Borda no marcador** e validar contorno circular; desativar e validar ausência.

#### Cenário 5 — Alinhamento Topo (estilo ENEM) em alternativa multilinha

- [x] Em questão com alternativa de várias linhas, escolher **Topo (estilo ENEM)**.
- [x] Salvar e visualizar; confirmar que a bolinha/letra alinha à **primeira linha** do texto (não ao centro do bloco).
- [x] Voltar para **Centro (padrão)** e confirmar alinhamento vertical centralizado.

#### Cenário 6 — Layout ENEM completo + persistência (F5)

- [x] Configurar: Zebrado off + Linha off + Marcador on + Alinhamento Topo.
- [x] **Salvar e visualizar** e validar o conjunto no PDF.
- [x] Recarregar a página (F5); confirmar que os controles permanecem com os valores salvos.

### 5.2 Aplicações — Malote Individual e em Massa [Apenas Manual 👁]

#### Cenário 7 — Modal individual de malote

- [x] Ir em **Aplicações → Presencial**.
- [x] Em uma aplicação, abrir a ação de gerar/imprimir malote (modal de configuração).
- [x] Localizar a seção **Layout de alternativas** e confirmar ausência do legado **"Remover cores…"**.
- [x] Alterar combinação (ex.: sem zebrado) e gerar o malote; abrir o PDF e validar o layout.

#### Cenário 8 — Modal em massa (2+ aplicações)

- [x] Selecionar duas ou mais aplicações compatíveis.
- [x] Abrir geração de malote em massa; ajustar layout de alternativas; gerar.
- [x] Validar no(s) PDF(s) que as opções escolhidas foram aplicadas.

### 5.3 Padrões de Impressão da Escola [Automatizável ✅ / herança Apenas Manual 👁]

#### Cenário 9 — Criar/editar padrão com layout de alternativas

- [x] Ir em **Gerenciamento → Provas → Padrões de impressão**.
- [x] Criar ou editar um padrão; configurar Layout de alternativas (ex.: ENEM-like).
- [x] Salvar e reabrir o padrão; confirmar persistência dos valores.
- [x] Associar/usar o padrão em um caderno novo ou no modal de malote e validar herança no PDF. [verificar fluxo exato de associação na UI]

### 5.4 Retrocompatibilidade e Legado [Automatizável ✅ / UI Apenas Manual 👁]

#### Cenário 10 — Defaults clássicos sem configuração

- [x] Abrir caderno/escola sem alteração prévia dos novos campos.
- [x] Gerar preview/PDF; confirmar visual clássico (zebrado on, linha on, marcador preto, alinhamento centro).

#### Cenário 11 — Legado ausente em todas as UIs tocadas

- [x] Conferir Diagramador, modal de Aplicações, modal de Ensalamento e formulário de Padrões: nenhum texto **"Remover cores das alternativas"**.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Tirar prints/PDF das combinações: (a) padrão clássico, (b) ENEM-like, (c) marcador branco + borda, (d) marcador off.
- [ ] Comparar lado a lado com o Design Vercel (Setup Global + Diagramação) e/ou o Jam do cliente.
- [ ] Validar em alternativa **multilinha** o alinhamento Topo vs Centro.
- [ ] Validar que o zebrado aparece na impressão/PDF (não só na tela) graças ao `print-color-adjust`.
- [ ] Anexar evidências na task ClickUp (checklist "O que foi feito" já lista os itens por controle).

Referências:

- Design Setup: https://lize-design.vercel.app/pt/dashboard/management/exams?tab=alternatives-layout
- Design Diagramação: https://lize-design.vercel.app/pt/dashboard/my-evaluations/cad-001/diagramacao
- Spec: `openspec/changes/customizacao-layout-alternativas/specs/customizacao-alternativas/spec.md`

---

## 7. Bugs and Observations (Problemas Encontrados)

> Use alertas GitHub (`> [!BUG]`, `> [!WARNING]`) e tags `[UX/UI]`, `[Backend Logic]`, `[Database]`, `[Spec Gap]`.  
> Em cada bug: **Title**, **Context/Root Cause**, **Expected Behavior** com `(conforme OpenSpec: spec.md L.XX)` ou `(inferência de UX — Spec Gap)`, e **Workaround** se bloquear o fluxo.

_(Reservado para preenchimento durante a execução.)_

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **DDL pós-deploy:** remover coluna `remove_color_alternatives` após estabilizar produção (OpenSpec Fase 5 / design Non-Goals).

> [!NOTE]
> **IDs estáveis no Diagramador:** `diagram_layout_alternatives.html` usa apenas `x-model` sem `id` nos toggles — dificulta Playwright. Preferir IDs espelhando `exam_configs_form.html` (`id-alternatives-striped`, etc.).

> [!NOTE]
> **Escopo futuro:** preferências também na resolução online (explicitamente fora deste ciclo).

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.

🔗 **[Diagramador — Layout de alternativas](../docs/tests/usability/diagram_layout_alternatives.md)**  
🔗 **[Formulário compartilhado de configs (Aplicações + Padrões)](../docs/tests/usability/exam_configs_form.md)**  
🔗 **[Modal de malote Ensalamento](../docs/tests/usability/modal_print.md)**  
🔗 **[Padrões de impressão create/update](../docs/tests/usability/print_defaults_create_update.md)**

### Snippet sugerido (mixer + Playwright)

```python
# setup (pytest + mixer) — ver test_exam_alternatives_layout.py
# UI (Playwright) — Diagramador Alpine:
# page.goto(f"/provas/{exam.id}/v2/imprimir/")
# page.get_by_text("Layout de alternativas").click()
# # Ideal: page.locator("#id-alternatives-striped") após adicionar IDs no HTML
# page.get_by_text("Salvar e visualizar").click()
# # Modal Aplicações (Vue, IDs já estáveis):
# page.locator("#id-alternatives-striped").uncheck()
# page.locator("#id-alignment-top").check()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante o teste:** _[preencher]_
- **Ida e volta com o desenvolvedor:** _[preencher]_
- **Como melhorar o fluxo dev/QA nesta task:** _[preencher]_

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

- O prompt V2 aponta saída em `.qa_acervo/`, mas o acervo versionado usado no repo é `.ai_qa_acervo/` (planos em `QA Plans/`). Alinhar o path no prompt para evitar divergência.
- Para features de PDF/malote, o prompt poderia exigir checklist explícito dos **4 pontos do pipeline** (model → diagram view → bag APIs → mockup_utils → templates), como já documentado no `design.md` desta change.
- Checklist ClickUp "O que foi feito" desta task já espelha bem o roteiro visual — sugerir no prompt cruzar checklists da task com a Seção 5 para não duplicar cenários.

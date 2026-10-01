# QA Test Plan: Correções de UI — Resultados do gabarito (CU-86ajftbkg)

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-01 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Dashboards / Resultados do gabarito (Questões, Alunos, Comparativo) |
| **Nível de Risco:** | Baixo |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5/5) — `proposal.md`, `design.md`, `specs/results-answer-layout/spec.md` e `tasks.md` cobrem hover/radius, full-width, altura de cards, alinhamento sem subtítulo, contraste de cinza, paridade SSR/lazy e non-goals. |

**Task ClickUp:** [Correções de UI - Resultados do gabarito](https://app.clickup.com/t/86ajftbkg)
**Branch:** `feat/correcao-resultado-gabarito-CU-86ajftbkg`
**Status na task:** testing

---

## 1. Summary of Changes (Resumo das Alterações)

Branch puramente visual (sem backend/API/Celery/multi-tenant). Diff `origin/master...HEAD` (~16 arquivos de UI + OpenSpec):

- **Componente global `components/accordion`:**
  - Nova prop opcional `flat_trigger=False` (`accordion.py` + `accordion.html`); quando `true`, trigger vira retangular full-width (`tw-w-full`, `tw-items-center`, sem `rounded-xl`/`rounded-t-xl`).
  - Default `false` preserva consumidores existentes (diagramação, routine, `performance_list` SSR).
- **Aba Alunos (`students_list` SSR + `answer_students` lazy + partial `students_list_expanded_tabs`):**
  - Trigger do aluno sem radius no hover/expandido (`tw-w-full`, `tw-bg-gray-50`/`tw-bg-white`, sem `rounded-xl`/`rounded-t-xl`).
  - Contraste: contagem de alunos, turma, "de acertos", "Carregando alunos…", vazios ("Nenhum resultado disponível…", "Nenhum aluno encontrado…", vazios de Disciplinas/Assuntos/Habilidades/Competências) e spinners de `gray-400`/`gray-300` para `gray-500`.
  - Abas internas do aluno **mantidas compactas** (`rounded-md` + `shrink-0`, sem `flex-1`) — decisão de produto.
- **Aba Questões:**
  - Visão Simples: grade com `tw-items-stretch`, wrapper `[data-question-item]` com `tw-flex tw-h-full tw-flex-col`, `question_card` com `tw-h-full tw-min-h-full tw-flex-1` e corpo `tw-flex-1`; cabeçalho com `tw-min-h-[4.5rem]` + `justify-center` para meta curta.
  - Visão Detalhado: `question_list` passa `flat_trigger=True` ao accordion (trigger retangular full-width).
  - Vazios ("Nenhuma questão encontrada…") de `#9CA3AF` para `gray-500`.
- **Aba Comparativo (`answer_comparative` + `performance_list`):**
  - Tabs principais full-width na fileira (`tw-flex tw-w-full`, botões `tw-flex-1` em `md+`; `max-md` com `gap-1`, scroll horizontal, `flex-none`).
  - Linhas sem subtítulo: coluna `tw-min-h-[2.25rem]` + `tw-justify-center` quando vazio; span do subtítulo oculto (`x-show`/`{% if %}`) para não reservar linha fantasma.
  - Legendas Respostas/Acertos/Erros, subtítulos e "de acertos" para `gray-500`; spinners e vazios/drill para `gray-500`.
- **Histograma + shell (`histogram_distribution`, `results_answer_shared.js`, `results_answer.html`, `results_answer_comparative_section.html`):**
  - Legenda dos eixos, vazios, KPI em erro ("—") e mensagens de erro/empty para `gray-500`.
  - CSS rebuild (`tw.css` / `output.css`): `tw-min-h-[2.25rem]`, `max-md:*`, `tw-accent-primary-600`.
- **Permissões/Serviços:** nenhum impacto (somente classes Tailwind/Alpine markup).

---

## 2. Scope Boundaries (Diferenças de Escopo)

**IN SCOPE:**

- Hover sem radius + fundo full-width no item de aluno (SSR e lazy-load), colapsado/expandido/hover.
- Trigger retangular full-width na visão Detalhado de questões (`flat_trigger=True`).
- Altura uniforme dos `question_card` na grade Simples (`md:grid-cols-2`) + alinhamento do cabeçalho com meta curta.
- Tabs principais do Comparativo full-width (desktop) + scroll horizontal sem sobreposição (mobile).
- Título centralizado verticalmente nas linhas do Comparativo sem subtítulo (sem linha fantasma).
- Contraste `gray-500` em mensagens vazias, loading informativo ("Carregando alunos…"), spinners da página, drill vazio e copy auxiliar (turma, contagem, "de acertos", meta, Respostas/Acertos/Erros, eixos do histograma, traço de KPI em erro).
- Paridade SSR (`students_list`) vs lazy (`answer_students` + partial `students_list_expanded_tabs`).
- Regressão: accordion global com default inalterado; KPIs do topo inalterados em valor/comportamento.

**OUT OF SCOPE:**

- Redesign estrutural da página ou migração de shell (mantém `extends redesign/base_component.html`, conforme OpenSpec proposal).
- Alterar grade/altura dos KPIs do topo (Alunos, Questões, Objetivas, Discursivas) — fora da revisão.
- Alterar comportamento de filtros, lazy-load, ordenação, exportação PDF ou compartilhamento.
- Mudar cores de barras de progresso (verde/amarelo/vermelho) ou semântica de notas.
- Full-width nas abas internas do painel expandido do aluno (Disciplinas/Assuntos/Habilidades/Competências) — explicitamente não-objetivo.
- Trocar `gray-400` em ícones decorativos (lupa, chevron, paginação) e placeholders de input.
- Outras telas de dashboard fora de Resultados do gabarito; backend/API/Celery/multi-tenant.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Resultados do gabarito (shell + KPIs) | "**Resultado do <nome>**" / "**Resultado do gabarito**" [verificar origem do link] | `/dashboards/ver-resultados/?exam_id=<uuid>&application_id=<uuid>` | `dashboards:results-answer` |
| Aba Questões | "**Questões**" (`span[role=tab]`, `setTab('tab1')`) | mesma URL, `tabpanel` `activeTab === 'tab1'` | `dashboards:results-answer` |
| Aba Alunos | "**Alunos**" (`span[role=tab]`, `setTab('tab2')`) | mesma URL, `tabpanel` `activeTab === 'tab2'` | `dashboards:results-answer` |
| Aba Comparativo | "**Comparativo**" (`span[role=tab]`, `setTab('tab3')`) | mesma URL, `tabpanel` `activeTab === 'tab3'` | `dashboards:results-answer` |
| Enunciados (lazy) | — (chamada JS via `page_config`) | `/dashboards/ver-resultados/aba/questoes/enunciados/` | `dashboards:results-answer-questions-enunciations` |
| Impressão (Alunos+Comparativo) | — (botão imprimir [verificar rótulo]) | `/dashboards/ver-resultados/impressao/` | `dashboards:results-answer-print` |

> **[verificar]** De onde o coordenador chega nesta tela no menu real (lista de avaliações / detalhe da aplicação) — o template só define o shell. Se o rótulo de origem divergir, tirar print e atualizar este mapa + KI de navegação.

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

**Persona (QA manual e automação):** Coordenação da unidade (`user_type='coordination'`) — a view também aceita Professor (`settings.TEACHER`). `ResultsAnswerView.required_permissions = [settings.COORDINATION, settings.TEACHER]` + `LoginRequired2FAMixin` (usar `two_factor_enabled=False` no setup).

**Comando (Docker — agents usam `--no-tty`):**

```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/dashboards/tests/components/test_answer_components_context.py fiscallizeon/dashboards/tests/components/test_answer_comparative.py fiscallizeon/dashboards/tests/components/test_performance_question_components.py fiscallizeon/dashboards/tests/test_views_results_answer.py
```

Cloud Lab (sem container `tests`):

```bash
source .venv/bin/activate && pytest fiscallizeon/dashboards/tests/components/test_answer_components_context.py fiscallizeon/dashboards/tests/components/test_answer_comparative.py --reuse-db
```

**Mixer setup (cenário com dados + cenário vazio):**

```python
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client
from fiscallizeon.accounts.models import User

client_obj = mixer.blend(Client)
coord = mixer.blend(
    User,
    user_type='coordination',
    two_factor_enabled=False,
    must_change_password=False,
    is_superuser=True,  # garante visibilidade sem montar CoordinationMember
)
# Com dados: Exam + Application + ApplicationStudent + ExamQuestion/Question
# (ver ResultsAnswerContextBuilder; cobrir: 2+ questões lado a lado,
#  2+ alunos, 1 linha de comparativo SEM subtítulo, 1 filtro sem match)
# Vazio: exam sem students/questions -> "Nenhum resultado disponível para esta avaliação."
# URL manual: /dashboards/ver-resultados/?exam_id=<uuid>&application_id=<uuid>
```

**Pré-requisitos visuais por cenário:** (a) 2+ questões na grade Simples com metas de tamanhos diferentes; (b) 2+ alunos (1 expandido); (c) comparativo com linha sem subtítulo; (d) filtro de alunos sem match; (e) viewport desktop `≥768px` + mobile `<768px` para tabs do comparativo.

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

> **Persona ativa:** Coordenação da unidade (ou Professor) com acesso a uma avaliação com alunos + questões + comparativo, e uma avaliação vazia.

### 5.1 Aba Alunos — Hover sem radius + fundo full-width [Apenas Manual 👁]

#### Cenário 1 — Hover em aluno colapsado ocupa largura total sem cantos arredondados

**Ação humana:**
- [x] Abrir "**Alunos**" (segunda tab em "**Resultado do gabarito**") com 2+ alunos carregados.
- [x] Posicionar o cursor sobre o cabeçalho de um aluno colapsado (linha com nome + turma à esquerda, percentual à direita).
- [x] Confirmar que o fundo de hover (cinza claro) ocupa 100% da largura do item, de borda a borda, sem cantos arredondados.
- [x] Repetir em outro aluno da lista.

**Referência técnica (para automação):**
- URL: `/dashboards/ver-resultados/?exam_id=<uuid>&application_id=<uuid>` (tab `activeTab === 'tab2'`)
- Seletor: `div.tw-w-full.tw-p-6.hover:tw-bg-gray-100` com `:class="expanded ? 'tw-bg-gray-50' : 'tw-bg-white'"`
- Estado esperado: sem `tw-rounded-xl` / `tw-rounded-t-xl` no trigger; hover = `tw-bg-gray-100` full-bleed
- Fixture: avaliação com 2+ `ApplicationStudent`

#### Cenário 2 — Aluno expandido mantém trigger retangular contínuo com o conteúdo

**Ação humana:**
- [x] Clicar no cabeçalho de um aluno (expande o painel com "**Disciplinas**", "**Assuntos**", "**Habilidades**", "**Competências**").
- [x] Confirmar que o cabeçalho ativo (fundo cinza bem claro) continua retangular, sem radius inferior quebrando a continuidade com o conteúdo abaixo.
- [x] Colapsar e expandir novamente; confirmar o mesmo comportamento.

**Referência técnica (para automação):**
- URL: mesma da aba Alunos
- Seletor: mesmo trigger + painel expandido (`tabItems('disciplinas')`, etc.)
- Estado esperado: expandido = `tw-bg-gray-50` sem `tw-rounded-t-xl`
- Fixture: idem cenário 1

#### Cenário 3 — Abas internas do aluno permanecem pills compactas (não full-width)

**Ação humana:**
- [x] Com um aluno expandido, observar a fileira "**Disciplinas**" / "**Assuntos**" / "**Habilidades**" / "**Competências**" (pills cinza-escuro ativo vs cinza claro).
- [x] Confirmar que cada pill envolve só o label (cantos arredondados pequenos) e que as pills **não** esticam para larguras iguais na fileira.
- [x] Trocar entre as 4 abas; confirmar o fundo ativo acompanha só a pill clicada.

**Referência técnica (para automação):**
- URL: mesma da aba Alunos (painel expandido)
- Seletor: `button.tw-px-4.tw-py-2.tw-rounded-md.tw-shrink-0`
- Estado esperado: sem `tw-flex-1` nas pills internas (decisão de produto — mock `student-expanded-tabs.html` não aplicado)
- Fixture: aluno com dados de drill por aba

### 5.2 Aba Questões — Cards Simples com altura uniforme + título alinhado [Apenas Manual 👁]

#### Cenário 4 — Cards lado a lado na visão Simples têm a mesma altura

**Ação humana:**
- [x] Abrir "**Questões**" (primeira tab) na visão "**Simples**" (grade de 2 colunas no desktop).
- [x] Com 2+ questões visíveis lado a lado (uma com enunciado/alternativas mais longos que a outra), confirmar que os cards da mesma linha terminam na mesma altura visual (sem um card visivelmente mais baixo).
- [x] Redimensionar para 1 coluna (mobile) e confirmar que nada quebra.

**Referência técnica (para automação):**
- URL: mesma página (`activeTab === 'tab1'`, `view === 'simples'`)
- Seletor: grade `div.tw-grid.md:tw-grid-cols-2.tw-items-stretch[x-ref="simpleGrid"]`; wrapper `div[data-question-item]` (`tw-flex tw-h-full tw-flex-col`); card `div.tw-h-full.tw-min-h-full.tw-flex-1`
- Estado esperado: `offsetHeight` iguais na mesma linha; corpo `div.tw-flex-1`
- Fixture: 2+ questões com conteúdos de tamanhos diferentes

#### Cenário 5 — Cabeçalho do card não desalinhado quando a meta é curta

**Ação humana:**
- [x] Na mesma grade Simples, localizar cards cuja linha de meta (ex.: "**Matemática • Objetiva • Fácil**") é mais curta que a do vizinho.
- [x] Confirmar que percentual + título + meta ficam harmonizados na altura compartilhada (bloco com altura mínima, conteúdo centralizado), sem o título "subir" em relação ao vizinho.

**Referência técnica (para automação):**
- URL: mesma da visão Simples
- Seletor: `div.tw-min-h-[4.5rem]` + `div.tw-flex-col.tw-justify-center.tw-flex-1`; meta `span.tw-text-xs.tw-text-gray-500`
- Estado esperado: `min-height: 4.5rem` no cabeçalho
- Fixture: idem cenário 4

### 5.3 Aba Questões — Visão Detalhado com trigger retangular [Apenas Manual 👁]

#### Cenário 6 — Lista Detalhado usa accordion flat full-width

**Ação humana:**
- [x] Alternar a aba "**Questões**" para a visão "**Detalhado**" (lista de accordions por questão).
- [x] Passar o cursor sobre um item colapsado e confirmar fundo full-width sem cantos arredondados (igual ao item de aluno).
- [x] Expandir uma questão e confirmar continuidade retangular com o conteúdo.

**Referência técnica (para automação):**
- URL: mesma página (`view === 'detalhado'` [verificar rótulo exato do toggle])
- Seletor: `{% component "accordion" flat_trigger=True %}` → `div.tw-w-full` + `tw-items-center`, sem `rounded-xl`
- Estado esperado: `flat_trigger=True` só em `question_list`; demais accordions mantêm default arredondado
- Fixture: 2+ questões

### 5.4 Aba Comparativo — Tabs full-width + linhas sem subtítulo [Apenas Manual 👁]

#### Cenário 7 — Tabs principais preenchem a fileira no desktop e rolam no mobile

**Ação humana:**
- [x] Abrir "**Comparativo**" (terceira tab) com dados (fileira "**Disciplinas**", "**Assuntos**", "**Habilidades**", "**Competências**", "**Turmas**", "**Unidades**" — conforme disponibilidade).
- [x] No desktop, clicar em cada tab e confirmar que o fundo ativo (quase-preto) preenche o slot da tab na fileira e que as vizinhas compartilham a mesma altura.
- [x] Estreitar para mobile (<768px) e confirmar scroll horizontal suave sem sobreposição de labels (sem texto cortado/empilhado).

**Referência técnica (para automação):**
- URL: mesma página (`activeTab === 'tab3'`)
- Seletor: `div.no-print.tw-flex.tw-w-full` + `button.tw-flex-1.tw-min-w-0` (+ `max-md:tw-flex-none max-md:tw-overflow-x-auto`)
- Estado esperado: ativo = `tw-bg-gray-900 tw-text-white`; inativo = `tw-text-gray-500 hover:tw-bg-gray-100`
- Fixture: comparativo com 2+ tabs com dados

#### Cenário 8 — Linha sem subtítulo centraliza o título (sem linha fantasma)

**Ação humana:**
- [x] No "**Comparativo**", localizar uma linha que exibe só o título (ex.: contagem de questões/alunos vazia, sem segunda linha de subtítulo).
- [x] Confirmar que o título fica verticalmente centralizado na coluna em relação às linhas que têm subtítulo, sem espaço vazio reservado abaixo.
- [x] Comparar lado a lado com uma linha com subtítulo visível.

**Referência técnica (para automação):**
- URL: mesma do Comparativo
- Seletor: `div.tw-min-h-[2.25rem]` + `:class="subtitle ? '' : 'tw-justify-center'"`; subtítulo `span[x-show="subtitle"]` (Alpine) / `{% if subtitle %}` (SSR `performance_list`)
- Estado esperado: sem `<span>` vazio quando `subtitle` falsy
- Fixture: 1 item com subtítulo + 1 sem subtítulo

### 5.5 Contraste de cinza — vazios, loading e copy auxiliar [Apenas Manual 👁]

#### Cenário 9 — Textos legíveis usam cinza escuro; ícones decorativos permanecem claros

**Ação humana:**
- [x] Forçar estados vazios: avaliação sem dados ("**Nenhum resultado disponível para esta avaliação.**"), filtro de alunos sem match ("**Nenhum aluno encontrado para os filtros selecionados.**"), drill vazio ("**Nenhuma disciplina encontrada.**" e equivalentes), histograma vazio, questões vazias ("**Nenhuma questão encontrada.**").
- [x] Confirmar em cada um que o texto é cinza médio legível (não quase-branco) — comparação visual com o print da task (o "muito claro" sumiu).
- [x] Confirmar loading "**Carregando alunos...**" e spinners legíveis durante o carregamento das abas.
- [x] Confirmar copy auxiliar legível: turma do aluno, contagem ("**X alunos**"), legendas "**Respostas**/**Acertos**/**Erros**", "**de acertos**", meta da questão, legenda dos eixos do histograma ("**Eixo Y… · Eixo X…**"), traço "**—**" de KPI em erro.
- [x] Confirmar que chevron de expandir, lupa de busca e paginação continuam no cinza decorativo original (não escurecidos junto).

**Referência técnica (para automação):**
- URL: todas as 3 abas + avaliação vazia
- Seletor: `p.tw-text-gray-500`, `span.tw-text-gray-500`, `div.tw-text-gray-500`, `svg.tw-text-gray-500` (spinners); decorativos `svg.tw-text-gray-400` (chevron) inalterados
- Estado esperado: zero ocorrências de `tw-text-gray-400`/`tw-text-gray-300`/`tw-text-[#9CA3AF]` em texto legível da página (conforme OpenSpec: spec.md L.84-111)
- Fixture: avaliação vazia + avaliação com dados + filtro sem match


---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] Tirar prints de: 
  - (a) hover em aluno colapsado ![ ](../evidencias/aluno_colapsed.png)
  - (b) aluno expandido ![ ](../evidencias/aluno_expand.png)
  - (c) grade Simples com 2 cards lado a lado ![ ](../evidencias/grade_simples.png)
  - (d) linha sem subtítulo vs com subtítulo ![ ](../evidencias/sem_title.png)

---

## 7. Bugs and Observations (Problemas Encontrados)

> Use alertas GitHub (`> [!BUG]`, `> [!WARNING]`) e tags `[UX/UI]`, `[Backend Logic]`, `[Database]`, `[Spec Gap]`.
> Em cada bug: **Title**, **Context/Root Cause**, **Expected Behavior** com `(conforme OpenSpec: spec.md L.XX)` ou `(inferência de UX — Spec Gap)`, e **Workaround** se bloquear o fluxo.

_(Reservado para preenchimento durante a execução.)_

Exemplo de formato:

> [!BUG]
> **Title:** [UX/UI] ...
> **Context/Root Cause:** ...
> **Expected Behavior:** ... (conforme OpenSpec: spec.md L.XX)
> **Workaround:** ...

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Duplicação SSR/lazy:** `students_list` × `answer_students` (+ partial) exigem edição tripla a cada ajuste de item de aluno (conforme OpenSpec proposal Riscos). Avaliar unificar o markup do trigger num include/componente único.

> [!NOTE]
> **IDs estáveis para Playwright:** triggers de aluno/questão/comparativo não têm `id`/`data-testid` (só classes Tailwind + Alpine). Para automação futura, adicionar `data-testid` (ex.: `data-testid="student-trigger"`) sem mudar o visual.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.

🔗 **[Ver Mapeamento de Tela](docs/tests/usability/results_answer.md)**

### Snippet sugerido (mixer + Playwright)

```python
# setup (pytest + mixer) — persona coordenação superuser + avaliação com dados
from mixer.backend.django import mixer
client_obj = mixer.blend(Client)
coord = mixer.blend(User, user_type='coordination', two_factor_enabled=False, is_superuser=True)

# UI (Playwright) — Resultados do gabarito
# page.goto(f"/dashboards/ver-resultados/?exam_id={exam.pk}&application_id={app.pk}")
# page.get_by_text("Alunos").click()
# trigger = page.locator("div.tw-w-full.tw-p-6.hover\\:tw-bg-gray-100").first
# trigger.hover()  # assert: no rounded corners (computed border-radius == 0)
# page.get_by_text("Questões").click()  # grade: comparar offsetHeight dos cards
# page.get_by_text("Comparativo").click()  # tabs flex-1; linha sem subtítulo centralizada
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante o teste:** _[preencher]_
- **Ida e volta com o desenvolvedor:** _[preencher]_
- **Como melhorar o fluxo dev/QA nesta task:** _[preencher]_

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- _[preencher durante a execução: edge cases, passos faltantes, falhas do prompt V2]_

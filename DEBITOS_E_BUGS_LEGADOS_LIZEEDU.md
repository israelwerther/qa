# 📌 Débitos Técnicos e Achados Fora de Escopo — Portal Lize Edu (`lizeedu`)

> **Objetivo deste documento:**  
> Centralizar bugs legados, inconsistências de UX, quebras de layout e débitos técnicos identificados durante sessões de QA no **portal web Lize Edu** (Django — coordenação, professor, OMR, cadernos, aplicações, etc.), quando estiverem **fora do escopo da tarefa em andamento**.  
>
> Use este arquivo como pauta em planejamento de sprint, refinamento técnico ou alinhamento com engenharia/produto, para que os achados não se percam nos planos de QA individuais.
>
> **Escopo deste arquivo:** apenas `lizeedu` (templates Django, Vue/Alpine no portal, APIs internas usadas pelo portal, Celery/OMR no backend).  
> **Não misturar** achados do App do Aluno (`lize-student`) — esses ficam em [`DEBITOS_E_BUGS_LEGADOS_APP_ALUNO.md`](./DEBITOS_E_BUGS_LEGADOS_APP_ALUNO.md).

---

## Como registrar um novo item

1. Adicionar uma linha na **tabela-índice** com o próximo ID (`LIZEEDU #NNN`), linkando para o detalhamento: `| [NNN](#lizeedu-NNN) | ... |`.
2. Criar a seção de detalhamento abaixo com heading só do ID (sem HTML, para âncora estável): `### LIZEEDU NNN` na primeira linha e o título curto na linha seguinte.
3. Citar a branch / plano de QA em que o problema foi encontrado.
4. Classificar severidade: **Alta** | **Média** | **Baixa**.
5. Status sugeridos: `⏳ Aguardando Pauta` | `⏳ Aguardando Alinhamento com PO` | `🔧 Em andamento` | `✅ Resolvido` | `🚫 WONTFIX`.

**Prefixo de ID:** `LIZEEDU` (não reutilizar a numeração `APP-ALUNO`).

**Tags úteis no detalhamento:** `[UX/UI]`, `[Backend Logic]`, `[Database]`, `[Spec Gap]`, `[Automação/QA]`.

---

## 📋 Índice de Ocorrências

| ID | Data | Funcionalidade / Tela | Problema | Severidade | Status |
| :-: | :-: | :--- | :--- | :-: | :-: |
| [001](#lizeedu-001) | 21/09/2026 | Elaboração de questões (professor) — barra discursiva / switch “Correção com competências” | Switch não persiste sozinho — estado amarrado ao select de modelo (`textCorrection`) | Média | ⏳ Aguardando Pauta |

---

## 🔍 Detalhamento das Ocorrências

### LIZEEDU 001 
Switch “Correção com competências” não persiste sozinho — estado amarrado ao select de modelo

* **Data de Identificação:** 21 de setembro de 2026
* **Identificado durante:** QA da branch `feat/campo-elaboracao-questão-CU-86ajqpbw5` / plano `QA Plans/QA_TEST_PLAN_feat_campo-elaboracao-questão-CU-86ajqpbw5.md` (Seção 7, Bug 1 — Cenário 4)
* **Task ClickUp:** [O campo de elaboração das questões ser mais amplo](https://app.clickup.com/t/86ajqpbw5)
* **OpenSpec da feature:** `openspec/changes/reorganizar-campos-elaboracao-questao-discursiva/`
* **Tipo:** Bug Legado | `[Backend Logic]` / `[UX/UI]` (`[Spec Gap]` no caminho inverso — desligar sem limpar modelo)
* **Severidade:** Média
* **Status:** ⏳ Aguardando Pauta
* **Arquivo(s):** `fiscallizeon/exams/templates/dashboard/exams/exam_request/exam_request_teacher_subject_edit_new.html` (barra discursiva: `correctionWithCompetencies` + `textCorrection`; watchers ~L8361–8368)
* **Tela / rota:** Elaboração de questões do professor — aba **“Enunciado”**, questão **Discursiva/Redação** — `/provas/prova/<uuid>/editar/` (`exams:exam_teacher_subject_edit_questions`)

#### 📝 Descrição
Na barra de config da discursiva, o switch **“Correção com competências”** e o select de modelo (`textCorrection`) não persistem de forma independente:
1. **Desligar não cola:** colocar o switch em **“não”** (off) e salvar **não** grava o desligamento se ainda houver um modelo selecionado no select. Após reload, a correção com competências volta ativa.
2. **Ligar sozinho não cola:** ativar o switch **sem** escolher um modelo no select e salvar **também não** persiste. Só persiste quando um modelo é selecionado junto.
3. O caminho feliz (switch on + modelo selecionado + **“Salvar”**) funciona e persiste após reload — o bug está nos caminhos isolados (on/off sem o outro campo).

#### 🛠️ Causa Técnica
Bug legado — **não introduzido** pelo reposicionamento da barra (a feature só moveu layout, sem mudança Python/migration/endpoint). Hipótese confirmada no template: o salvamento parece depender de `textCorrection` (UUID ou `null`) mais do que do boolean `correctionWithCompetencies`. Evidência: os watchers Vue observam `'examQuestion.question.correctWithCompetencies'` (sem “ion”), enquanto o `v-model` do switch é `examQuestion.question.correctionWithCompetencies` (L1928) — dessincronia que impede o clear/sync do select ao alternar só o switch. O watcher de `textCorrection` (L8366–8368) escreve no mesmo nome sem “ion”, então nenhum dos dois watchers reage ao campo real do `v-model`.

#### 💡 Sugestão de Correção
1. Corrigir o nome nos watchers para `examQuestion.question.correctionWithCompetencies` (com “ion”) e validar o fluxo: off → limpa/ignora `textCorrection` no PATCH; on sem modelo → validação explícita na UI (ou permite `true` + `null` se o backend aceitar).
2. **Comportamento esperado:** conforme OpenSpec `specs/exam-elaboration-discursive-config-bar/spec.md` (Scenario *Salvar correção com competências após reposicionamento*), on + modelo + salvar persiste ambos; **(inferência de UX — Spec Gap para o caminho inverso)** desligar o switch e salvar deve persistir `correctionWithCompetencies === false` sem exigir limpar o select na mão.
3. Cobrir com smoke Playwright/pytest: barra por `categoryDisplay`, PATCH com `correctionWithCompetencies`/`textCorrection`, e reload validando os dois caminhos isolados.

#### Workaround temporário (QA)
- Para **ativar** e persistir: ligar o switch **e** selecionar um modelo de correção antes de **“Salvar”**.
- Para **desativar** e persistir: limpar o select (opção vazia `------------------` / nenhum modelo) e então **“Salvar”** — não confiar só no switch em **“não”**.

<!--
### LIZEEDU NNN
Título curto do problema
Tabela-índice: `| [NNN](#lizeedu-NNN) | ... |` (âncora automática do heading, sem HTML)

* **Data de Identificação:** DD de mês de AAAA
* **Identificado durante:** QA da branch `feat/...` / plano `QA_TEST_PLAN_...md`
* **Tipo:** Bug Legado | Débito de UX | Débito de Automação | Spec Gap
* **Severidade:** Alta | Média | Baixa
* **Arquivo(s):** caminho no repositório `lizeedu` (template, view, component, etc.)

#### 📝 Descrição
O que o usuário vê / o que quebra.

#### 🛠️ Causa Técnica
(Se conhecida.)

#### 💡 Sugestão de Correção
(Se houver.)

#### Workaround temporário (QA)
(Se o fluxo de teste ficar bloqueado.)
-->

---

## 📎 Referências do acervo

| Recurso | Caminho |
| :--- | :--- |
| Planos de QA do portal | [`QA Plans/`](./QA%20Plans/) |
| Mapeamentos de usabilidade (templates Django) | [`docs/tests/usability/`](./docs/tests/usability/) |
| Navegação canônica (sidebar) | [`KI_Navegacao.md`](./KI_Navegacao.md) |
| Débitos do App do Aluno | [`DEBITOS_E_BUGS_LEGADOS_APP_ALUNO.md`](./DEBITOS_E_BUGS_LEGADOS_APP_ALUNO.md) |

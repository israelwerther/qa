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
| [002](#lizeedu-002) | 09/10/2026 | Correção por enunciado (professor/coordenação) — modal de competências | `TypeError` em `teacher_grade` e perda de critérios no primeiro envio para alunos sem resposta prévia | Média | ⏳ Aguardando Pauta |

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

---

### LIZEEDU 002
`TypeError` ao selecionar competência e perda de critérios no primeiro envio para alunos sem resposta prévia

* **Data de Identificação:** 09 de outubro de 2026
* **Identificado durante:** QA da branch `refactor/tela-correcao-respostas-CU-86agu3wje` / plano `QA Plans/QA_TEST_PLAN_refactor_tela-correcao-respostas-CU-86agu3wje.md` (Seção 5.4, Cenário 7)
* **Task ClickUp:** [Refactor tela de correção de respostas](https://app.clickup.com/t/86agu3wje)
* **Tipo:** Bug Legado | `[Frontend / JS]` / `[UX/UI]`
* **Severidade:** Média
* **Status:** ⏳ Aguardando Pauta
* **Arquivo(s):** 
  - `fiscallizeon/exams/templates/dashboard/exams/includes/exam-detail-enunciation-functions.js` (funções `selectedCorrection` ~L308 e `sendTeacherFeedback` ~L247–285)
  - `fiscallizeon/exams/templates/dashboard/exams/exam_detail_enunciation_new.html` (função `saveUpdateCorrection` ~L1574)
* **Tela / rota:** Detalhes de enunciados / Correção por enunciado — modal de respostas (`#answers-accordion`) — `/provas/<uuid>/enunciados/detalhes/` (`exams:exams_detail_enunciation_new`)

#### 📝 Descrição
Ao abrir o modal de correção por enunciado de uma questão discursiva com rubrica/competências ativas (ex.: Competências ENEM) para um aluno que **não submeteu resposta textual prévia** (ou seja, `application_student.answers` é uma lista vazia `[]`):
1. **Erro de JavaScript no console:** Ao clicar em qualquer pill de pontuação de critério (ex.: 120, 160, 200), o console dispara repetidamente:
   ```text
   [Vue warn]: Error in v-on handler: "TypeError: Cannot set properties of undefined (setting 'teacher_grade')"
   TypeError: Cannot set properties of undefined (setting 'teacher_grade')
       at Vue.selectedCorrection (detalhes/?turma=all:4534:66)
       at Vue.selectCriterionPoint (detalhes/?turma=all:4905:22)
   ```
2. **Critérios não persistem na primeira tentativa:** Ao preencher a nota ou clicar para salvar/avançar, o modal passa para o próximo aluno, mas **as notas das competências selecionadas não são gravadas no backend**.
3. **Comportamento enganoso de "funcionar só na 2ª vez":** Ao reabrir o mesmo aluno pela segunda vez e preencher as competências novamente, o salvamento finalmente persiste. Isso ocorre porque o primeiro salvamento criou uma instância de `TextualAnswer` com `corrected_but_no_answer = true`, permitindo que na segunda tentativa `answers[0]` exista.

#### 🛠️ Causa Técnica
Bug legado pré-existente (código presente desde o commit `5ac4398aa0` em 13/08/2024):
1. **Acesso inseguro a array vazio:** Em `selectedCorrection` (`exam-detail-enunciation-functions.js`), a linha:
   ```javascript
   this.selectedApplicationStudent.answers.at(0).teacher_grade = this.totalPoints
   ```
   assume que `this.selectedApplicationStudent.answers.at(0)` sempre existe. Para alunos sem resposta prévia (`answers: []`), `answers.at(0)` retorna `undefined`, estourando a exceção não tratada ao tentar setar `.teacher_grade`.
2. **Omissão de chamada a `saveUpdateCorrection` no fluxo de criação:** No método `sendTeacherFeedback`, quando `answer && answer.id` é verdadeiro (`if`), a função invoca `await this.saveUpdateCorrection(...)`. Porém, no bloco `else` (quando o aluno não possuía resposta e é criada uma nova resposta via `POST` em `createUrl`), a chamada a `saveUpdateCorrection` **nunca é executada**. O código apenas faz `this.selectedApplicationStudent.answers[0] = answer` e chama `this.changeStudent()`, avançando para o próximo aluno e descartando o array `this.selectPoint` em memória.

#### 🎯 Como Simular
1. Acessar `/provas/<exam_id>/enunciados/detalhes/?turma=all` em uma prova com discursiva com rubrica ENEM (ex.: Univar `ADM - Fundamentos da Economia Aplicada` — `effa9336-d46f-4617-ac58-44e3e286cf9e`).
2. Abrir o modal de correção da **Questão 11**.
3. Selecionar um aluno que não enviou resposta (ex.: `ISADORA CAMYLLE CERDAM FERNANDES AGUIAR` ou `FABIANA MOREIRA BATISTA`).
4. Abrir o Console do Navegador (F12).
5. Clicar em qualquer nota de critério na tabela (ex.: C1 = 200).
6. **Observar o erro:** O console dispara `TypeError: Cannot set properties of undefined (setting 'teacher_grade')`.
7. Clicar em salvar/atribuir nota. O modal pula para o próximo aluno.
8. Reabrir o aluno anterior: constatar que os critérios não foram salvos e aparecem em branco.

#### 💡 Sugestão de Correção
1. Em `selectedCorrection`: proteger o acesso com checagem segura:
   ```javascript
   if (this.selectedApplicationStudent && this.selectedApplicationStudent.answers && this.selectedApplicationStudent.answers.at(0)) {
       this.selectedApplicationStudent.answers.at(0).teacher_grade = this.totalPoints;
   }
   ```
2. Em `sendTeacherFeedback` (bloco `else`): após criar com sucesso a resposta em branco via `POST`, encadear a chamada a `await this.saveUpdateCorrection(this.selectedApplicationStudent.id)` antes de chamar `this.changeStudent()`.

#### Workaround temporário (QA)
- Ao validar ou corrigir alunos sem submissão prévia, salvar primeiro uma nota geral para criar a resposta no backend, e só então pontuar as competências na segunda abertura.
- Para testes de QA em lote, priorizar alunos que já possuam respostas textuais submetidas.

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

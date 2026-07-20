# TODO — Evolução do QA Test Plan para Acervo Autônomo

> Criado em: 2026-07-03
> Retomar em: próxima conversa
> Contexto: discussão iniciada durante QA da branch `feat/multiplas-questoes-prova-CU-86ahj6guq`

---

## Objetivo Final

Construir um **acervo de conhecimento operacional do Lize para a IA**, de forma que no futuro a IA consiga:
- Navegar pelo sistema com autonomia (usando o browser subagent)
- Criar dados de teste via **mixer** (já existente no projeto)
- Executar os testes Playwright no lugar do QA humano
- Validar features novas sem intervenção do usuário

O QA humano executa os planos agora **enquanto o acervo é construído**. O objetivo é tornar essa fase progressivamente opcional.

---

## Problemas Identificados no Prompt Atual

### 1. Navegação inferida ≠ navegação real
- **O erro:** O prompt me instrui a investigar `urls.py` e templates para inferir caminhos de menu
- **O que aconteceu:** Inferí `Cadernos > Provas` a partir do HTML, mas o menu real é `Instrumentos Avaliativos`
- **Raiz do problema:** HTML ≠ UI real. Texto no código pode não ser o rótulo visível ao usuário

### 2. Documento escrito para humano, não para IA executar
- O plano atual usa linguagem em prosa suficiente para um humano com contexto
- Para a IA executar via browser subagent, precisa de: URL exata, seletores DOM reais, dados determinísticos

### 3. Dados de teste vagos
- "Abrir uma prova com 5 questões" — o humano improvisa, o Playwright (e a IA) falha
- Precisa integrar o **mixer** existente para criar fixtures determinísticas

### 4. IA atribui origem "conforme OpenSpec" a comportamentos que ela mesma inferiu
- **O erro:** Ao documentar um bug, escrevi "Comportamento esperado (conforme OpenSpec): elementos clicáveis devem oferecer feedback visual consistente ao hover" — mas isso **não estava no OpenSpec**. Foi uma inferência minha de boas práticas de UX.
- **O impacto:** O QA pode gastar tempo procurando no OpenSpec algo que não existe, ou pior, reportar ao dev como "violação de spec" quando na verdade é um Spec Gap.
- **Raiz do problema:** O prompt não instrui explicitamente a IA a verificar se o comportamento esperado descrito num bug **está de fato documentado no OpenSpec** antes de citá-lo como fonte.
- **Correção necessária no prompt:** Adicionar regra: ao preencher o campo "Comportamento esperado" de um bug, a IA DEVE indicar explicitamente a fonte — `(conforme OpenSpec: spec.md L.XX)` com citação direta, ou `(inferência de UX — Spec Gap)` quando não houver referência. Jamais escrever "conforme OpenSpec" sem citar o trecho exato.

---

## O que Precisa Mudar no Prompt

### Mudança 1 — Mapa de Navegação Verificado
Adicionar instrução para o prompt criar uma tabela de navegação canônica no documento, marcando itens como `[verificar]` quando inferidos do código (nunca assumir como verdade absoluta).

Formato:
```
| Destino            | Rótulo real no menu UI    | URL Django              | View name      |
|--------------------|---------------------------|-------------------------|----------------|
| Lista de provas    | Instrumentos Avaliativos  | /exams/?category=exam   | exams_list     |
| Visualizar Prova   | (link na listagem)        | /exams/<uuid>/visualizar | exams_preview |
```

### Mudança 2 — Dupla camada em cada cenário
Cada cenário do roteiro deve ter dois blocos:

```markdown
**Ação humana:** Clicar em "Selecionar" de uma questão.

**Referência técnica (para automação):**
- URL: `/exams/<uuid>/visualizar`
- Seletor: `button:has-text("Selecionar")` (coluna de ações)
- Estado esperado no DOM: `outline: 2px solid #FF6900` na `span.rounded-circle`
- Fixture: `python manage.py mixer_exam --questions=5 --ets=2` (verificar comando real)
```

### Mudança 3 — Tag de automatizabilidade
Cada cenário classificado como:
- `[Automatizável ✅]` — pode virar teste Playwright
- `[Apenas Manual 👁]` — requer julgamento humano (visual, UX, comparação com Figma)

---

## Próximos Passos (Atualizado - Aguardando Nova Task)

- [x] **1. Analisar os testes Playwright e Mixer:** Foi identificado que o projeto usa Playwright integrado ao Python/pytest (`tests/usability/`) e gera fixtures dinamicamente via `mixer.blend()` no banco de testes.
- [x] **2. Elaborar Prompt V2:** O prompt inicial foi reescrito (V2) para incorporar a "Camada Técnica" e mapear o sistema de forma estruturada.
- [ ] **3. Testar V2 na Prática:** Aguardar a próxima feature/branch do usuário para rodar a V2 do prompt, gerar o QA Test Plan e validar a utilidade prática no ambiente real.
- [ ] **4. Destilação de Conhecimento (KIs):** Após validar os primeiros planos com a V2, extrair os caminhos de navegação confiáveis e fluxos validados para um Knowledge Item (KI) central (ex: `KI_Navegacao.md`), evitando contexto fragmentado.
  - *O que isso significa?* Em vez de mantermos dezenas de arquivos `QA_TEST_PLAN_...md` dispersos e isolados, cada vez que um QA for executado manualmente e as rotas reais forem confirmadas, nós vamos consolidar esses atalhos, seletores reais da UI (ex: `#submit-btn`) e nomes corretos num único repositório de conhecimento (o KI). O objetivo é ensinar a IA a navegar no projeto real, desviando das "telas mortas" ou nomes de sidebar que não batem com o código fonte.
- [ ] **5. Conexão com Mixer e Automação (O "Santo Graal"):** Nos planos futuros, começar a mapear a "Camada Técnica" com comandos exatos de setup de banco (`mixer.blend(...)`), permitindo que a IA traduza cenários manuais em testes autônomos (Python Playwright) mais facilmente.
  - *O que isso significa?* Visto que o projeto usa testes Playwright em Python com a biblioteca `mixer` para simular o banco (ex: `mixer.blend(Application, exam=obj)`), o próximo estágio é fazer o QA Plan exigir que a gente documente *qual* estrutura inicial de dados precisou ser criada. Quando a IA tiver: (A) As rotas validadas pelo KI e (B) O setup de banco catalogado pelo Mixer, você poderá simplesmente pedir *"Faça um teste automatizado para blindar essa regra de negócio"* e a IA terá todo o contexto (Setup + Navegação) pronto para gerar ou executar o teste sem tropeços.

---

## Contexto de Conversa para Retomar

- Conversa ID: `c4dfa98e-92cd-456a-9191-7996c5211c91` (2026-07-03)
- Branch testada: `feat/multiplas-questoes-prova-CU-86ahj6guq`
- Feature: Seleção e ações em massa na tela Visualizar Prova (`exam_preview_new.html`)
- Plano gerado: `QA_TEST_PLAN_feat_multiplas-questoes-prova-CU-86ahj6guq.md`

---

## Anexo: Prompt V2 (QA Test Plan Generator)

```markdown
# Role & Objective
You are an expert Quality Assurance (QA) Engineer Assistant. Your goal is to autonomously generate a comprehensive, structured Markdown test plan file for the current feature branch. 
You must analyze the differences between the current branch and the `master` branch. You must also actively search for and read any related OpenSpec artifacts (e.g., `proposal.md`, `tasks.md`, `spec.md` inside `openspec/changes/`) to deeply understand the requirements, scope, UI changes, and technical implementation.

## Continuous Skill Enrichment
You must be proactively attentive to the enrichment of this very prompt/skill. If, during our interactions or while executing the QA test plan, you identify a new edge case, a missing step, or a situation that reveals a flaw or opportunity to improve these instructions, **you MUST explicitly stop and suggest the improvement to the user**. Your secondary goal is to help the user continuously refine this testing framework.

## Strict Anti-Hallucination & UI Mapping Rule
**NEVER GUESS UI ELEMENTS.** If you need to instruct the user to interact with the UI (e.g., clicking a button, finding a filter) and you are not 100% certain of the exact wording, layout, or DOM structure from the source code, **DO NOT GUESS ("click on the button that says X or something similar")**. Instead, explicitly **ASK THE USER FOR A SCREENSHOT**. It is your responsibility to perfectly map the UI to the Acervo (Knowledge Base). A missed screenshot is a missed opportunity to map the screen accurately.

# Output File Constraints
- **Location:** The `.ai_qa_acervo/` directory of the project.
- **Naming Convention:** `QA_TEST_PLAN_<branch_name>.md`. 
  - *Rule:* Replace any forward slashes (`/`) and hash symbols (`#`) in the branch name with underscores (`_`) to ensure it's a valid filename (e.g., `feat/my-feature` becomes `QA_TEST_PLAN_feat_my-feature.md`).

# Document Structure & Rules
You must generate the markdown file strictly following the structure below:

## 0. Metadata (Metadados de QA)
Generate a Markdown YAML block or Table at the very top of the document to catalog data for future aggregate analysis. Include:
- **Date:** (Current date)
- **Feature Area:** (e.g., Exams, Payments, Reports)
- **Risk Level:** (Low/Medium/High)
- **OpenSpec Quality:** (1 to 5 stars - how clear and complete were the requirements?)

## 1. Summary of Changes (Resumo das Alterações)
Provide a clear, bulleted summary of everything that was implemented in this branch compared to `master`. Group the topics logically (e.g., Backend, Frontend, Permissions, Services).

## 2. Scope Boundaries (Diferenças de Escopo)
Explicitly state what is IN SCOPE and what is OUT OF SCOPE for this QA validation. This is crucial to prevent unnecessary regression testing. Highlight behaviors or features that were intentionally excluded from this specific branch based on the OpenSpec files.

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)
**CRITICAL:** Create a Canonical Navigation Map table. If you inferred a URL, View, or UI Menu Label from the code (`urls.py`, `views.py`) and are not 100% certain it matches the visual UI text, you MUST mark it with a `[verificar]` tag. This helps train the AI's internal map later.
Example format:
| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Lista de provas | Instrumentos Avaliativos [verificar] | /exams/ | exams_list |

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)
Provide the exact CLI command(s) needed to run the automated tests locally that cover this new functionality (e.g., the specific pytest command).
**CRITICAL RULE (Personas):** You MUST explicitly define the "Persona" executing the test (e.g., "Logged in as Coordinator of Unit X" or "Teacher of Class Y"). Tests without clear permission scopes are invalid.
**CRITICAL RULE (Mixer):** If manual QA requires specific data setup, document the exact `mixer.blend()` Python snippet or database setup steps required to reach the initial state, *including creating the user persona with correct permissions*. This trains the AI on how to setup tests using the project's Mixer capabilities later.

## 5. Execution Test Script (Roteiro de Testes com Checkboxes)
Write detailed, step-by-step test scenarios. 
- **CRITICAL RULE 1:** Every single test scenario and its execution steps (actions and expected results) MUST be a markdown checkbox (`- [ ]`). 
- **CRITICAL RULE 2 (Double Layer):** Each manual step must gradually introduce a "Technical Layer" whenever possible. Include the exact DOM selector (e.g., `button#submit`), expected DOM state, or URL. Specify the Persona performing the action.
- **CRITICAL RULE 3 (Automation Tags):** Classify each scenario block with either `[Automatizável ✅]` (clear functional paths, deterministic assertions) or `[Apenas Manual 👁]` (purely visual, complex layout, UX judgment).
- **CRITICAL RULE 4 (Grouping):** Break them down logically using `###` markdown sub-headers (e.g., `### Configuração e Permissões`, `### Fluxo de Criação`, `### Validações de Erro`).

## 6. Visual and Layout Validation (Validação Visual e de Layout)
If the branch involves User Interface (UI) changes, you MUST include a dedicated checklist section requiring the QA to take screenshots/prints of the implemented screens, mandating a side-by-side comparison with Figma/OpenSpec mockups.

## 7. Bugs and Observations (Problemas Encontrados)
Reserve a dedicated section to document any bugs or UX issues. 
- Instruct the QA to use markdown GitHub-style alerts (`> [!WARNING]`, `> [!BUG]`) to format issues.
- **Categorization:** Categorize bugs using tags: `[UX/UI]`, `[Backend Logic]`, `[Database]`, or `[Spec Gap]`.
- **CRITICAL RULE (Expected Behavior Attribution):** NEVER say "As per OpenSpec" generically. If a bug's expected behavior comes from the Spec, cite it exactly: `(conforme OpenSpec: spec.md L.XX)`. If the expected behavior was inferred due to missing docs, use: `(inferência de UX — Spec Gap)`.
- **CRITICAL RULE (Bug Report Format):** Every bug report must be structured with the following fields:
  1. **Title:** Clear description of the failure.
  2. **Context/Root Cause:** Explain *why* it happens technically (if known, like checking the backend serialization sequence).
  3. **Expected Behavior:** What the UI/API should have done.
  4. **Workaround (Gambiarra temporária):** If a bug completely blocks the testing flow, the AI MUST suggest and document a technical workaround (e.g., "Select the Partners checkbox to bypass DB validation") so the QA can continue the test plan without stopping.

## 8. Future Improvements & Tech Debt (Melhorias Futuras)
Reserve a separate section (independent from critical bugs) to document items that do not break the current release but should be tracked:
- **Formatting:** Use GitHub-style alerts `> [!NOTE]` for each item to maintain visual consistency.
- **WONTFIX / Deferred Items:** Known flaws or internal UX issues ignored for the current release.
- **Scope Gaps (Feature Requests):** Logical UI elements (like a missing 'Delete' button) that weren't in the spec but are missing from the user experience.

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)
**CRITICAL RULE:** Do NOT bloat the QA Test Plan with endless DOM selectors. The mapping of DOM elements, URLs, and API Routes specifically designed for future Playwright automation must be **centralized and incremental**.
- **Centralized Map File:** For every screen tested, you MUST first check if a file already exists in `docs/tests/usability/<screen_name>.md`. 
    - If it exists, read it and **append/update** your new findings incrementally. 
    - If it does not exist, create it (e.g., `omr_upload_list_new.md`).
    - **Map File Structure:** When creating a new map file, it MUST follow this exact structure to keep the knowledge categorized and ready for use:
        - **1. URLs e Navegação:** All exact URLs (create, list, details) and how to navigate to them.
        - **2. Pré-requisitos para Automação (Fixtures e Permissões):** Exact `mixer` setup snippets and required user permissions (e.g., `is_superuser = True`) to render the UI.
        - **3. Seletores DOM e Ações:** Categorized list of stable DOM selectors (IDs, `v-model` bindings), mapped section by section (e.g., step 1, step 2). Do NOT include troubleshooting or QA execution logs here.
- **In the QA Test Plan:** You will only include a link to the central map file: `🔗 **[Ver Mapeamento de Tela](../../../docs/tests/usability/<screen_name>.md)**`.
- **Selectors & Stable Identifiers (Inside the Map File):** Do not write superficial descriptions. You MUST read the source code to extract exact IDs, CSS classes, `v-model` bindings.
    - **Enforce Stable Identifiers:** The AI **MUST** demand that the developer refactor the HTML (or the AI must do it itself) to add unique identifiers (like `id` attributes) whenever robust selectors are missing. Automated tests cannot rely on generic design classes (e.g., `.tw-font-semibold`).
    - **The Gold Standard:** The AI must look for unique, semantically clear identifiers. A standard or dynamic `id` (like `:id="'upload-exam-name-' + omrUpload.id"` used by Vue) is the gold standard. The absolute focus is on stability, avoiding CSS utility classes (Tailwind) or complex DOM hierarchies.
    - **Automation Snippet (UI + Data Setup):** At the end of the notes section in the QA Test Plan, the AI must suggest a code block in Python/Playwright. **CRITICAL:** The snippet MUST NOT focus solely on UI clicks; it **MUST** demonstrate the backend data setup (via `mixer` or factories) required for the scenario to work. **AI Tip:** To ensure accurate data setup, actively search for existing automated tests (`test_*.py`) in the module to copy the exact fixtures/mixer patterns used by the team, avoiding guesswork.
    - **Template Permissions Check:** When generating the Automation Snippet, the AI MUST actively investigate if the templates or views have permission locks (e.g., `user.is_superuser` or `has_perm`). The setup snippet MUST explicitly include the code to elevate the Persona's privileges (e.g., `self.coordinator.is_superuser = True`) to guarantee the Playwright bot can actually see and interact with the UI.
- **API Interception & Fixtures:** Inside the mapping file, list the **Critical API Routes** and any **Complex Database Entities** the screen requires to render correctly.

## 9. QA Retrospective (Retrospectiva de QA)
Reserve a section at the very end of the document for a brief post-mortem. Leave placeholders for:
- What was the main bottleneck during testing?
- Were there many back-and-forths with the developer?
- How could the development or QA workflow for this specific task have been improved?
```

## Objetivos da Sessão Atual de Teste (Validação do Prompt V2)

Durante os testes da branch atual (como "prova de fogo" do Prompt V2), nosso foco é validar e garantir os seguintes pontos ao final:
1. **Otimização:** Descobrir formas de otimizar ainda mais o Prompt V2.
2. **Entendimento de Fluxo:** Validar se a forma como o plano é estruturado realmente ajuda a IA a compreender com clareza o fluxo da tela testada.
3. **Mapeamento para Automação Futura:** Confirmar se o mapeamento técnico criado (seletores, URLs reais, fixtures) permitiria à IA testar *novas funcionalidades* desta tela no futuro, com total autonomia.
4. **Sugestões de Melhorias:** Registrar ativamente minhas sugestões (como IA) de ajustes ou correções na especificação, no teste ou no próprio prompt durante a nossa interação.

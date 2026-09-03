## 0. Metadata (Metadados de QA)

| Campo                      | Valor                                                                                                                                                                                                                                                                                                                                                 |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data:**                  | 2026-09-02                                                                                                                                                                                                                                                                                                                                            |
| **Natureza da Tarefa:**    | `[Business Feature]`                                                                                                                                                                                                                                                                                                                                  |
| **Área da Feature:**       | Questions / Edição completa de questão (Exams — fluxo de revisão)                                                                                                                                                                                                                                                                                     |
| **Nível de Risco:**        | Alto                                                                                                                                                                                                                                                                                                                                                  |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐                                                                                                                                                                                                                                                                                                                                            |
| **ClickUp:**               | [86ahuc1wb](https://app.clickup.com/t/86ahuc1wb) — status **testing**; descrição confirmada via MCP global (`~/.cursor/mcp.json` + OAuth). OpenSpec prevalece sobre o pitch (ex.: aba Questão, Histórico no header). Figma raiz da task: [Lize-Panel 12445-43130](https://www.figma.com/design/rLxKONkzOksH4OZTBN6jOy/Lize-Panel?node-id=12445-43130) |

**Resumo da task (ClickUp / OpenSpec):** Redesign visual da tela **Edição completa da questão** conforme Figma, preservando integralmente funcionalidades, permissões, POST do formulário e contrato de popup. A versão nova convive com a legada via `?v=redesign`; o default continua sendo a tela antiga até cutover futuro.

---

## 1. Summary of Changes (Resumo das Alterações)

### Frontend / UI

- Novo template `question_create_update_redesign.html` estendendo `redesign/base_component.html`, ativado por `?v=redesign` nas views `QuestionCreateView` / `QuestionUpdateView`.
- Shell visual (`question_edit_shell`): header com título e `X` (popup), barra de contexto (breadcrumb, ações), card com 4 abas, footer fixo (Cancelar, Desfazer alterações, Salvar questão).
- Reorganização de **6 abas legadas → 4 abas** (`Questão`, `Dados pedagógicos`, `Competências e habilidades`, `Impressão`) + botões de header (`Histórico`, `Utilizações`).
- Tipo de questão em **cards** (`question_edit_type_cards`) substituindo `<select>`, codificando `category` + `is_essay`.
- Duas famílias visuais na aba Questão: **Redação** (Discursiva, Arquivo anexado, Cloze) e **Objetiva** (Objetiva, Somatório).
- Drawers laterais: textos base, cadastrar assunto, cadastrar habilidade/competência, histórico, utilizações (`question_edit_drawer` compartilhado).
- Modais via `components/modal`: Visualizar questão, Atalhos do teclado, Formatador IA, Ver versão.
- Toolbar TinyMCE compartilhada (`question_edit_rich_text_toolbar`) na coluna lateral.
- Motor de estado **Alpine.js** (`question_edit_form.js` + módulos por aba); sem Vue 2 na versão nova.
- Token laranja `#FF6900` (Figma), distinto de `brand-600` do design system.

### Comportamentos novos

- **Badge de erros por aba** (`errorCounts` + `count_expr` em `components/tabs`).
- **Desfazer alterações** (`undoChanges()`): restaura campos, TinyMCE e seleções Alpine ao estado carregado.

### Integração / Dual-acesso

- Trilho da visualização de caderno (`exam_preview_actions.html`): dropdown **Editar — versão antiga** / **Editar — versão nova**.
- Modal de revisão (`modal_review.html`): **Edição completa — versão antiga** / **versão nova** (`urlQuestionUpdateRedesign`).

### Backend

- Apenas seletor de template em `get_template_names`; **sem migrations**, sem alteração de `QuestionForm`, models ou serializers.
- Template legado `question_create_update.html` **intocado**.

### Testes

- Suíte `fiscallizeon/questions/tests/test_question_edit_redesign.py` (~83 testes na app questions).
- Smoke script `openspec/.../baseline-html/smoke_test_redesign.py`.
- Checklist de paridade 71/71 (seções 1–8) documentado em `parity-checklist.md`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### IN SCOPE (validar neste QA)

- Renderização e paridade funcional da tela `?v=redesign` em **criação** e **edição**, perfis **coordenação** e **professor**, com e sem **popup**.
- Dual-acesso a partir da **visualização do caderno** e do **modal de revisão**.
- 4 abas, drawers, modais, cards de tipo, famílias visuais, estados de bloqueio (`reason_can_be_updated`), obrigatoriedade por cliente (`ClientTeacherObligationConfiguration`).
- Preservação de `name`/`id` de campos no POST (incluindo 9 campos da aba Impressão e hiddens críticos).
- Contrato de popup: `question_popup_response.html`, `window.opener.*.call()`, fechamento, `beforeunload`.
- Comportamentos novos: badge de erros por aba, Desfazer alterações.
- Flags de cliente: código interno, Cloze, formatador IA, conteúdo de apoio discursivo.
- Comparação visual com frames Figma em `openspec/changes/redesign-question-full-edit-screen-86ahuc1wb/references/figma/`.

### OUT OF SCOPE (não bloquear release desta branch por ausência)

- Tornar `?v=redesign` o **default** ou remover a tela legada (cutover futuro).
- Correção da dívida `QuestionHistoryTags` / exibição de `historical_tags`.
- Fluxo `request_tags` acionado pela Edição completa (hiddens existem; fluxo não é disparado — non-goal OpenSpec).
- Campos `break_alternatives` e PAS (`binary_type`, `b_type_expected_answer`) — ausentes também no legado.
- Edição inline do modal de revisão (`PATCH questions:questions-detail`).
- Templates mortos `?v=2` / `?v=new`.
- Regressão completa dos **16 pontos de entrada** que não emitem dual-acesso (permanecem na versão antiga por design).
- **Predeploy / gate de cobertura** (tarefa 12.3 pendente no OpenSpec — responsabilidade de dev, não bloqueia roteiro funcional).

### BLOQUEADO POR INFRA (documentar, não fechar release sem plano)

- **Tarefa 6.3:** comparar malote PDF legado vs redesign após editar aba Impressão — requer print service (`172.17.0.1:8080`) indisponível no ambiente atual (QA-117).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino                                       | Rótulo real no menu UI                                   | URL Django                                                               | View name                    |
| --------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------- |
| Criar questão (nova UI)                       | Banco de questões → Cadastrar [verificar]                | `/questoes/cadastrar/?v=redesign`                                        | `questions:questions_create` |
| Editar questão (nova UI, página)              | Lista/Banco → Editar [verificar]                         | `/questoes/<uuid>/editar/?v=redesign`                                    | `questions:questions_update` |
| Editar questão (popup via caderno)            | Visualizar caderno → Editar → **Editar — versão nova**   | `/questoes/<uuid>/editar/?v=redesign&is_popup=1&exam_question_id=<uuid>` | `questions:questions_update` |
| Editar questão (popup via revisão)            | Modal revisão → **Edição completa — versão nova**        | Mesma URL acima                                                          | `questions:questions_update` |
| Visualização do caderno (entrada dual-acesso) | Instrumentos Avaliativos → Visualizar [verificar]        | `/provas/<uuid>/visualizar`                                              | `exams:exams_preview`        |
| Versão antiga (controle)                      | Editar — versão antiga / Edição completa — versão antiga | `/questoes/<uuid>/editar/?is_popup=1&…` (sem `v=redesign`)               | `questions:questions_update` |
| Lista de questões                             | Questões [verificar]                                     | `/questoes/`                                                             | `questions:questions_list`   |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos CLI

```bash
# Docker (recomendado — agentes: sempre --no-tty)
docker compose --profile test up -d tests
./scripts/tests/run-tests.sh --no-tty fiscallizeon/questions/tests/test_question_edit_redesign.py
./scripts/tests/run-tests.sh --no-tty fiscallizeon/questions/tests/

# Smoke de paridade HTML/POST (requer DB de teste configurado)
python openspec/changes/redesign-question-full-edit-screen-86ahuc1wb/references/baseline-html/smoke_test_redesign.py

# Cloud Lab (sem Docker tests)
source .venv/bin/activate && pytest fiscallizeon/questions/tests/test_question_edit_redesign.py --reuse-db
```

### Setup Mixer (questão objetiva editável — coordenador)

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.classes.models import Grade
from fiscallizeon.subjects.models import Subject
from fiscallizeon.accounts.models import User
from fiscallizeon.questions.models import Question, QuestionOption

client_obj = mixer.blend(Client, has_exam_elaboration=True, two_factor_enabled=False)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
grade = mixer.blend(Grade)
subject = mixer.blend(Subject)

perms = Permission.objects.filter(
    codename__in=['coordination', 'teacher', 'add_question', 'change_question', 'view_question']
)
coordinator = mixer.blend(User, two_factor_enabled=False, must_change_password=False)
mixer.blend(CoordinationMember, user=coordinator, coordination=coordination)
coordinator.user_permissions.set(perms)

question = mixer.blend(
    Question, grade=grade, subject=subject, category=Question.CHOICE, created_by=coordinator,
)
question.coordinations.add(coordination)
for i in range(4):
    mixer.blend(QuestionOption, question=question, is_correct=(i == 0))
```

### Setup popup com caderno (coordenador)

```python
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject

exam = mixer.blend(Exam, coordination=coordination, created_by=coordinator)
ets = mixer.blend(ExamTeacherSubject, exam=exam, teacher_subject__subject=subject)
exam_question = mixer.blend(ExamQuestion, exam=exam, question=question, order=1)
# URL: f"/questoes/{question.pk}/editar/?v=redesign&is_popup=1&exam_question_id={exam_question.pk}"
```

### Referências técnicas (automação Playwright — não usar na Seção 5)

Ver mapeamento completo: [question_create_update_redesign.md](docs/tests/usability/question_create_update_redesign.md)

**Seletores estáveis principais:** `#questionForm`, `[data-question-edit-redesign="1"]`, `#question-edit-shell-footer`, `#question-edit-topics-tree`, `#row-alternatives`, `[role="radiogroup"] [role="radio"]`.

**API críticas:** cascata pedagógica (`classes:grade_list_api`, `subjects:*`), BNCC (`bncc:*`), textos base (`questions:base_text_*`), utilizações (`questions:question_historical`).

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona padrão:** Coordenador com módulo de elaboração de provas, salvo indicação em contrário.

### 5.1 Coexistência e dual-acesso [Automatizável ✅ / Apenas Manual 👁]

#### Cenário 1 — Default continua sendo a tela antiga

- [x] Abrir edição de questão a partir da lista `/questoes/` sem parâmetro `v`.
- [x] Confirmar visual Bootstrap/Vue legado (6 abas com badges F1–F6).
- [x] Repetir a partir do banco de questões do professor (persona Professor) e confirmar mesma versão legada.

#### Cenário 2 — Versão nova via query param

- [x] Abrir `/questoes/<uuid>/editar/?v=redesign` em nova aba.
- [x] Confirmar layout Tailwind com 4 abas e footer fixo.
- [x] Confirmar ausência de sidebar global quando `?is_popup=1`.

#### Cenário 3 — Dual-acesso na visualização do caderno

- [x] Persona Coordenador: abrir `/provas/<uuid>/visualizar`.
- [x] Clicar **Editar** no trilho de ações e verificar opções **Editar — versão antiga** e **Editar — versão nova**.
- [x] Abrir **versão nova** em popup e confirmar mesma questão/caderno (breadcrumb com nome do caderno e número da questão).

#### Cenário 4 — Dual-acesso no modal de revisão

- [x] Na elaboração/revisão do caderno, abrir modal de revisão de uma questão.
- [x] Verificar **Edição completa — versão antiga** e **Edição completa — versão nova**.
- [x] Abrir versão nova e confirmar paridade de dados com a versão antiga na mesma questão.

### 5.2 Shell, popup e salvamento [Automatizável ✅ / Manual 👁]

#### Cenário 5 — Modo popup: fechar e cancelar

- [x] Abrir edição em popup (`is_popup=1`).
- [x] Clicar **X** ou **Cancelar** no footer sem alterações: janela fecha.
- [x] Alterar um campo, tentar fechar: navegador exibe aviso de saída (`beforeunload`).

#### Cenário 6 — Salvar questão em popup

- [x] Editar enunciado em popup aberto a partir do caderno.
- [x] Clicar **Salvar questão** (header ou footer).
- [x] Confirmar que o popup fecha e a tela abridora atualiza a questão (comportamento equivalente ao legado).

#### Cenário 7 — Desfazer alterações

- [x] Carregar questão existente na versão nova.
- [x] Alterar enunciado, trocar aba, marcar um assunto e uma competência.
- [x] Clicar **Desfazer alterações**.
- [x] Confirmar que todos os campos voltam ao estado inicial, incluindo editores rich text e seleções nas abas pedagógicas/BNCC.

### 5.3 Aba Questão — tipos e famílias visuais [Manual 👁]

#### Cenário 8 — Cards de tipo de questão

- [x] Na aba **Questão**, verificar cards: Discursiva, Objetiva, Redação, Arquivo anexado, Somatório (e Cloze se cliente tiver módulo).
- [x] Selecionar **Redação**: confirmar select **Forma de resposta do aluno** e quantidade de linhas = 30 na aba Impressão.
- [x] Trocar para **Discursiva**: confirmar que Redação não permanece selecionada (`is_essay` zerado após salvar).

#### Cenário 9 — Família Objetiva (alternativas e Anular)

- [x] Selecionar **Objetiva** em questão existente.
- [x] Verificar tabela de alternativas com marcação de correta (radio — uma correta).
- [x] Confirmar controle **Anular questão** visível só em edição de objetiva.
- [x] Selecionar **Somatório**: Anular some; coluna Correta permite múltiplas marcadas.

#### Cenário 10 — Família Redação / Discursiva (seção Resposta)

- [x] Selecionar **Discursiva** ou **Redação**.
- [x] Confirmar seção **Resposta** sempre visível (resposta comentada, feedback, vídeo).
- [x] Em **Objetiva**, confirmar que feedback fica no collapse **Adicionar ou alterar resposta comentada e feedback do professor**.

#### Cenário 11 — Drawer de textos base

- [x] Clicar **+ Adicionar texto base** (ou link de quantidade se já houver seleção).
- [x] No drawer: buscar, **Adicionar na questão**, **Cadastrar novo texto**, **Voltar para a lista**, **Salvar texto**.
- [x] Confirmar que texto vinculado aparece na aba Questão e persiste após **Salvar questão**.

### 5.4 Abas pedagógicas e BNCC [Manual 👁]

#### Cenário 12 — Cascata Dados pedagógicos

- [x] Aba **Dados pedagógicos**: grid 3 colunas (Segmento, Ano/Série, Área / Disciplina, Dificuldade).
- [x] Alterar Segmento e confirmar reset de séries, área, disciplina e assuntos dependentes.

#### Cenário 13 — Árvore de assuntos e cadastro inline

- [x] Buscar assunto pelo campo **Buscar por assuntos disponíveis**.
- [x] Marcar assunto na árvore de 4 níveis; salvar questão e reabrir — seleção persistida.
- [ ] Abrir drawer **Cadastrar Assunto** (com cascata preenchida), criar assunto e verificar inclusão na árvore.

#### Cenário 14 — Competências e habilidades

- [x] Aba **Competências e habilidades**: duas colunas, grupos **Recentes** e **Todas**.
- [x] Marcar/desmarcar itens e observar movimentação entre grupos.
- [x] Cadastrar competência via drawers (com dados pedagógicos preenchidos).
- [ ] Cadastrar habilidade via drawers

### 5.5 Aba Impressão e malote PDF [Manual 👁 + Infra]

#### Cenário 15 — Layout e POST da aba Impressão

- [x] Verificar 6 switches + 3 campos inferiores na ordem do Figma.
- [x] Confirmar rótulo **Não exibir numeração** no switch de numeração.
- [x] Alterar switches e quantidades; salvar questão; reabrir e confirmar persistência.


### 5.6 Histórico, Utilizações e header [Manual 👁]

#### Cenário 17 — Drawer Utilizações

- [x] Questão vinculada a ≥1 caderno: botão **Utilizações (N)** visível no header.
- [x] Abrir drawer: badges **Não aplicado** / **Aplicado** / **Em elaboração**, data, professor+disciplina, link abre prévia do caderno em nova aba.
- [x] Questão sem vínculos: botão Utilizações ausente.

#### Cenário 18 — Drawer Histórico e Ver versão

- [x] Questão com histórico: botão **Histórico** abre drawer com colunas Modificado por / Alterações / Data.
- [x] Em alteração de enunciado/alternativa/feedback: ação **Ver versão** abre modal com valor anterior.

#### Cenário 19 — Ações de apoio no header

- [x] **Atalhos do teclado**: modal lista F1–F4 (abas), F5/F6 (drawers), Ctrl+S/I/L.
- [x] **Visualizar questão**: prévia com enunciado, alternativas e dados pedagógicos.

### 5.7 Validação, erros e bloqueios [Automatizável ✅ / Manual 👁]

#### Cenário 20 — Badge de erros por aba

- [x] Submeter formulário com campo obrigatório vazio em aba não visível (ex.: disciplina vazia).
- [x] Confirmar contador vermelho na aba correspondente

#### Cenário 21 — Estados de bloqueio (`reason_can_be_updated`)

- [x] Questão em caderno fechado / com malote / aplicação iniciada: aviso exibido, enunciado e alternativas somente leitura, cards de tipo desabilitados.
- [x] Persona Professor: questão aprovada com bloqueio, criada por outro professor, ou fora do prazo — mensagem correspondente.
- [x] Questão pública: acesso negado com mensagem de operação não permitida.

#### Cenário 22 — Obrigatoriedade por cliente

- [x] Cliente com obrigatoriedade pedagógica ativa: campos marcados com asterisco; erro ao salvar sem preencher.
- [x] Obrigatoriedade de gabarito: objetiva sem alternativa correta exibe erro.

### 5.8 Regressão legado [Manual 👁]

#### Cenário 23 — Tela antiga intacta

- [x] Confirmar que fluxos na versão antiga (sem `v=redesign`) continuam funcionando após merge da branch.
- [x] Popup legado continua comunicando com abridores (salvar fecha janela e atualiza caderno).

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

Capturar prints lado a lado (**versão nova** vs frames Figma em `openspec/.../references/figma/`) para:

- [ ] Shell completo (header, breadcrumb, abas, footer) — popup e página cheia.
- [ ] Aba **Questão** — família Redação (`edicao-questao-frame.png`) e Objetiva (`edicao-questao-objetiva-frame.png`).
- [ ] Aba **Dados pedagógicos** (`edicao-questao-dados-pedagogicos-frame.png`).
- [ ] Aba **Competências e habilidades** (`edicao-questao-competencias-habilidades-frame.png`).
- [ ] Aba **Impressão** (`edicao-questao-impressao-frame.png`).
- [ ] Drawers: Utilizações, Histórico, Textos base (selecionar/cadastrar), Cadastrar assunto/habilidade/competência.
- [ ] Token `#FF6900` em botões primários, links de atalho e bordas ativas (não exigir paridade com `brand-600`).
- [ ] Estados bloqueados (frames pendentes no Figma — validar aviso + readonly conservador).

**Resoluções:** desktop ≥1280px (toolbar lateral visível na aba Questão) e viewport reduzida (drawers responsivos).

---

## 7. Bugs and Observations (Problemas Encontrados)

_Use os placeholders abaixo durante a execução. Formato obrigatório por bug._

> [!BUG] **[Título do bug]**
> **Contexto/Causa raiz:** …
> **Comportamento esperado:** … (conforme OpenSpec: `spec.md` L.XX — quando aplicável)
> **Workaround (Gambiarra temporária):** …

**Itens conhecidos pré-QA (não são bugs do redesign):**

> [!WARNING] **[Spec Gap] Malote PDF não validado**
> **Contexto:** Tarefa OpenSpec 6.3 bloqueada — print service `172.17.0.1:8080` connection refused (QA-117).
> **Comportamento esperado:** PDF gerado após editar aba Impressão reflete mesmas quebras/colunas do legado (conforme OpenSpec: `spec.md` L.459–461).
> **Workaround:** Validar POST/nomes de campo via testes automatizados; adiar comparação visual de PDF até infra disponível.

> [!WARNING] **[Spec Gap] `request_tags` na Edição completa**
> **Contexto:** Fluxo de tags/nota não é acionado por este ponto de entrada (non-goal).
> **Comportamento esperado:** Hiddens presentes; fluxo SweetAlert de tags só em outros entry points com `request_tags=true`.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE] **Cutover para default `?v=redesign`** — Após validação completa incluindo malote PDF, remover dropdown dual-acesso e tornar template novo o default.

> [!NOTE] **Exibir `QuestionHistoryTags` no histórico** — Dívida pré-existente; tags gravadas mas não renderizadas.

> [!NOTE] **Frames Figma de estados bloqueados** — Implementação conservadora até receber frames; revisar copy/layout quando design entregar.

> [!NOTE] **Predeploy pendente (12.3)** — Rodar `./scripts/dev/predeploy.sh --no-tty` antes do merge; resolver gate de cobertura diff vs `origin/master`.

> [!NOTE] **Entrada #10 (diagramação `?v=2` superuser)** — Limitação de ambiente no QA-117; revalidar quando houver caderno de diagramação no lab.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.

🔗 **[Ver Mapeamento de Tela](docs/tests/usability/question_create_update_redesign.md)**

### Snippet Playwright + setup de dados

```python
import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from mixer.backend.django import mixer
from playwright.sync_api import Page, expect

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.classes.models import Grade
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.subjects.models import Subject


@pytest.mark.django_db(databases="__all__")
def test_redesign_question_edit_shell(page: Page, live_server):
    client_obj = mixer.blend(Client, has_exam_elaboration=True, two_factor_enabled=False)
    unity = mixer.blend(Unity, client=client_obj)
    coordination = mixer.blend(SchoolCoordination, unity=unity)
    grade = mixer.blend(Grade)
    subject = mixer.blend(Subject)

    perms = Permission.objects.filter(
        codename__in=["coordination", "add_question", "change_question", "view_question"]
    )
    user = mixer.blend(User, two_factor_enabled=False, must_change_password=False)
    mixer.blend(CoordinationMember, user=user, coordination=coordination)
    user.user_permissions.set(perms)

    question = mixer.blend(
        Question,
        grade=grade,
        subject=subject,
        category=Question.CHOICE,
        created_by=user,
    )
    question.coordinations.add(coordination)
    for i in range(4):
        mixer.blend(QuestionOption, question=question, is_correct=(i == 0))

    page.goto(f"{live_server.url}{reverse('accounts:login')}")
    page.fill('input[name="username"]', user.email)
    page.fill('input[name="password"]', "test-password")  # ajustar conforme fixture
    page.click('button[type="submit"]')

    url = reverse("questions:questions_update", kwargs={"pk": question.pk})
    page.goto(f"{live_server.url}{url}?v=redesign")

    expect(page.locator("#questionForm")).to_be_visible()
    expect(page.get_by_role("tab", name="Questão")).to_be_visible()
    expect(page.get_by_role("tab", name="Dados pedagógicos")).to_be_visible()
    expect(page.locator("#question-edit-shell-footer")).to_contain_text("Desfazer alterações")
    expect(page.locator('[role="radiogroup"] [role="radio"]')).to_have_count(5)
```

---

## 9. QA Retrospective (Retrospectiva de QA)

_Preencher após execução:_

- **Principal gargalo:** …
- **Back-and-forths com dev:** …
- **Melhoria de workflow:** …

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

- Incluir fallback explícito quando ClickUp API falhar: ler `openspec/changes/*-<task_id>/proposal.md` como fonte canônica da descrição.
- Adicionar seção **"Known blockers from OpenSpec tasks.md"** auto-preenchida a partir de checkboxes `[ ]` pendentes (ex.: 6.3, 12.3).
- Para features com `?v=` feature flag, padronizar matriz **Persona × v=legado × v=novo × popup** como subseção obrigatória da Seção 5.

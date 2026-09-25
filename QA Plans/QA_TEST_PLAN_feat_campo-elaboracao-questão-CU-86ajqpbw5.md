## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-09-21 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Exams / Elaboração de questões (professor) |
| **Nível de Risco:** | Baixo |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ |
| **Task ClickUp:** | [O campo de elaboração das questões ser mais amplo](https://app.clickup.com/t/86ajqpbw5) |
| **Branch:** | `feat/campo-elaboracao-questão-CU-86ajqpbw5` |
| **OpenSpec:** | `openspec/changes/reorganizar-campos-elaboracao-questao-discursiva/` |

---

## 1. Summary of Changes (Resumo das Alterações)

Reorganização de layout na tela legada de elaboração do professor (`exam_request_teacher_subject_edit_new.html`). Sem mudança de modelo, API ou validação server-side.

### Frontend / Layout
- **Reposicionados** os campos **"Quantidade de linhas"** (input + select de formato de impressão) e **"Correção com competências"** (switch + select de modelo) para uma **barra compacta** logo abaixo dos cards de **"Tipo de questão"** e **acima** do editor TinyMCE.
- **Removido** o painel cinza inferior (`#F9FBFA`) que ocupava espaço abaixo do editor.
- **Campo PAS "Valor esperado"** (Tipo B) realocado para a mesma barra (ainda acima do enunciado).
- **`getQuestionContentHeight()`** deixou de aplicar penalidade de altura (~160px) para discursiva/redação; a redução extra permanece só para **"Preencher lacunas"**.
- Classes Tailwind auxiliares adicionadas em `tw.css` (`.tw-min-w-[240px]`, `.tw-min-w-[120px]`, `.tw-pr-6`).

### Backend
- Nenhuma alteração Python, migration ou endpoint.

### Bindings preservados
- `quantityLines`, `textQuestionFormat`, `correctionWithCompetencies`, `textCorrection`, `bTypeExpectedAnswer`
- Automação `updateQuantityLines()` → `quantityLines = 30` ao escolher **"Redação"**

---

## 2. Scope Boundaries (Diferenças de Escopo)

**No escopo:**
- Ordem visual na aba **"Enunciado"**: cards de tipo → barra de config → editor
- Visibilidade da barra apenas para discursiva/redação (`categoryDisplay == 'Discursiva'`)
- Ausência do painel inferior duplicado
- Persistência dos valores após **"Salvar"** / **"Salvar alterações"**
- Automação de 30 linhas ao trocar para **"Redação"**
- Layout de objetiva/somatório/lacunas/arquivo anexado **inalterado** (sem barra)
- Responsividade da barra em viewport estreita (~375px) com `flex-wrap`
- PAS Tipo B: campo **"Valor esperado"** acima do editor, validação 0–999
- Comparação visual com mockup OpenSpec `references/barra-config-discursiva.html`

**Fora de escopo:**
- Redesign completo da tela ou migração para `redesign/base_component.html`
- Tela de edição completa (`question_create_update_redesign.html`)
- Alteração de opções/lógica dos campos movidos
- Competências BNCC, aba Feedbacks, configurações de impressão da edição completa
- Novos endpoints, migrations ou mudanças de modelo
- App do aluno (`lize-student`)

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Lista de solicitações | **Cadernos** → **"Solicitações de elaboração"** | `/provas/professor/` | `exams:exam-teacher-subject-list` |
| Elaboração de questões | Card da solicitação → continuar/editar | `/provas/prova/<uuid>/editar/` | `exams:exam_teacher_subject_edit_questions` |
| Template desta feature | — (experiência nova do professor) | mesmo URL sem `?v=` | `exam_request_teacher_subject_edit_new.html` |
| Mockup OpenSpec | — | arquivo local | `openspec/changes/reorganizar-campos-elaboracao-questao-discursiva/references/barra-config-discursiva.html` |

> **Pré-condição:** `has_new_teacher_experience` (inspector ou client) ou `exam.created_by == user`. Sem isso a view serve o template legado e a barra **não** existirá.

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Suite automatizada existente
Não há teste automatizado específico da barra de config discursiva nesta branch. A suíte mais próxima valida apenas acesso HTTP à view:

```bash
# Docker (agente: sempre --no-tty)
./scripts/tests/run-tests.sh --no-tty fiscallizeon/exams/tests/views/test_views.py::TestExamTeacherSubjectEditQuestionsView

# Local sem Docker
pytest fiscallizeon/exams/tests/views/test_views.py::TestExamTeacherSubjectEditQuestionsView --reuse-db
```

### Persona de teste (obrigatória)
- **Papel:** Professor (`User` + `Inspector` tipo teacher) dono do `ExamTeacherSubject`
- **Flags:** `inspector.has_new_teacher_experience = True` **ou** `client` com `client_has_new_teacher_experience`
- **Permissão:** `inspector.can_elaborate_questions` (para ver **"Solicitações de elaboração"** no menu)
- **Caderno:** prazo de elaboração vigente; sem aplicação iniciada que bloqueie edição
- **Variante PAS (cenário 5.4):** `exam.exam_format == 1`

### Mixer — setup mínimo para chegar na tela

```python
from mixer.backend.django import mixer
from django.utils import timezone
import datetime
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination
from fiscallizeon.inspectors.models import Inspector, TeacherSubject
from fiscallizeon.subjects.models import Subject
from fiscallizeon.exams.models import Exam, ExamTeacherSubject, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.classes.models import Grade

client = mixer.blend(Client)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)

user = mixer.blend(User, must_change_password=False)
teacher = mixer.blend(
    Inspector,
    user=user,
    email=user.email,
    inspector_type=Inspector.TEACHER,
    has_new_teacher_experience=True,
    can_elaborate_questions=True,
)
teacher.coordinations.add(coordination)

subject = mixer.blend(Subject)
teacher_subject = mixer.blend(TeacherSubject, teacher=teacher, subject=subject, active=True)
grade = mixer.blend(Grade)

exam = mixer.blend(
    Exam,
    coordinations=[coordination.id],
    elaboration_deadline=timezone.now().date() + datetime.timedelta(days=5),
    created_by=user,
    # exam_format=1  # descomentar para cenários PAS
)
ets = mixer.blend(
    ExamTeacherSubject,
    exam=exam,
    teacher_subject=teacher_subject,
    quantity=5,
    order=1,
    grade=grade,
)

# Questão discursiva já vinculada (opcional — também pode criar pela UI)
question = mixer.blend(Question, category=0, is_essay=False, quantity_lines=5)
exam_question = mixer.blend(ExamQuestion, exam_teacher_subject=ets, question=question, order=0)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona ativa:** Professor com experiência nova, dono da solicitação de elaboração (ver Seção 4).

### 5.1 Layout da barra em discursiva [Automatizável ✅]

#### Cenário 1 — Ordem visual: cards → barra → editor

**Ação humana:**
- [x] Autenticar como a Persona Professor
- [x] No menu lateral, abrir **"Cadernos"** e clicar em **"Solicitações de elaboração"**
- [x] Abrir uma solicitação em elaboração (botão/ação do card para editar questões) e chegar em `/provas/prova/<uuid>/editar/`
- [x] Selecionar uma questão (ou criar uma nova) e garantir que a aba **"Enunciado"** está ativa
- [x] Nos cards **"Tipo de questão"**, clicar em **"Discursiva"** (card com ícone de lápis)
- [x] Confirmar a ordem vertical: (1) cards de tipo → (2) barra cinza clara com borda → (3) editor do enunciado
- [x] Confirmar que **não** existe painel cinza com os mesmos campos **abaixo** do editor
- [x] Na barra, localizar o rótulo **"Quantidade de linhas"** e o switch **"Correção com competências"**

**Referência técnica (para automação):**
- URL: `/provas/prova/{ets_pk}/editar/`
- Seletor barra: `div[style*="#F9FBFA"]` imediatamente após `.question-type-options` (ideal: exigir `id="discursive-config-bar"`)
- Seletor linhas: `input[name="quantity_lines"]` / `#quantityLines-{id}`
- Seletor competências: `#idcorrectionWithCompetencies-{id}` + label `"Correção com competências"`
- Estado esperado: barra visível; painel inferior antigo **ausente** do DOM
- Fixture: `mixer` da Seção 4 + `Question(category=0)`

---

#### Cenário 2 — Editor com área vertical ampliada

**Ação humana:**
- [x] Ainda em questão **"Discursiva"** na aba **"Enunciado"**, com a barra de ferramentas do TinyMCE visível
- [x] Comparar visualmente a altura útil do editor: deve ocupar a região central sem “faixa cinza” de configuração abaixo do card
- [ ] (Opcional) Se houver print/baseline anterior à mudança, confirmar que o editor ficou **igual ou maior** em altura

**Referência técnica (para automação):**
- URL: `/provas/prova/{ets_pk}/editar/`
- Função: `getQuestionContentHeight` — para discursiva com `controls.show`, altura `calc(100vh - 300px)` ou `calc(100vh - 260px)` (não o branch de lacunas)
- Seletor: container com `:style` de height ligado a `getQuestionContentHeight(examQuestion)`
- Estado esperado: `categoryDisplay === 'Discursiva'` **não** entra em `isReducedHeightCategory`
- Fixture: mesma do Cenário 1

---

### 5.2 Persistência dos campos reposicionados [Automatizável ✅]

#### Cenário 3 — Salvar quantidade de linhas e formato de impressão

**Ação humana:**
- [x] Em questão **"Discursiva"**, na barra superior, alterar o input de **"Quantidade de linhas"** para um valor distinto (ex.: `12`)
- [x] No select embutido ao lado, escolher **"Imprimir linhas"** (ou **"Espaço em branco"**, o oposto do valor atual)
- [x] Clicar em **"Salvar"** (botão primário laranja no rodapé do card da questão) ou **"Salvar alterações"** no topo
- [x] Recarregar a página (F5) e reabrir a mesma questão
- [x] Confirmar que quantidade de linhas e formato de impressão permaneceram

**Referência técnica (para automação):**
- URL: `/provas/prova/{ets_pk}/editar/`
- Seletor: `input[name="quantity_lines"]`, `select` com options `value="0"` / `value="1"`
- Estado esperado: após reload, `v-model` refletindo valores salvos via PATCH `question.urls.apiUpdate`
- Fixture: questão discursiva existente; interceptar PATCH e assert body com `quantity_lines` / `text_question_format`

---

#### Cenário 4 — Salvar correção com competências

**Ação humana:**
- [x] Ativar o switch **"Correção com competências"**
- [x] No select abaixo/ao lado, escolher um modelo de correção disponível na lista
- [x] Clicar em **"Salvar"**
- [x] Recarregar e confirmar que o switch permanece ativo e o modelo selecionado persiste
- [ ] **(Falha — ver Bug 1 / Seção 7)** Desativar o switch (**"não"** / off) **sem** limpar o modelo no select, salvar e recarregar — o desligamento **não** persiste
- [ ] **(Falha — ver Bug 1 / Seção 7)** Ativar o switch **sem** escolher modelo no select, salvar e recarregar — a ativação isolada **não** persiste

**Referência técnica (para automação):**
- URL: `/provas/prova/{ets_pk}/editar/`
- Seletor: `#idcorrectionWithCompetencies-{id}`, `select` com `v-model="examQuestion.question.textCorrection"`
- Estado esperado: `correctionWithCompetencies === true` e `textCorrection` = UUID do modelo
- Fixture: cliente com pelo menos um `textCorrection` cadastrado no contexto da tela
- **Status QA:** caminho feliz (switch on + modelo) ok; desligar/ligar o switch de forma isolada falha — documentado na Seção 7

---

#### Cenário 5 — Redação força 30 linhas

**Ação humana:**
- [x] Nos cards **"Tipo de questão"**, clicar em **"Redação"** (card com ícone de assinatura)
- [x] Confirmar que a barra de config continua visível (redação é discursiva com `isEssay`)
- [x] Confirmar que **"Quantidade de linhas"** exibe `30`
- [x] Salvar, recarregar e confirmar persistência de `30` (e tipo Redação ativo)

**Referência técnica (para automação):**
- URL: `/provas/prova/{ets_pk}/editar/`
- Ação: `button.question-type-card:has-text("Redação")` → `changeQuestionCategory(0, true)` → `updateQuantityLines()`
- Estado esperado: `isEssay === true`, `quantityLines === 30`
- Fixture: mesma base; assert PATCH com `isEssay: true`

---

### 5.3 Regressão — tipos não discursivos [Automatizável ✅]

#### Cenário 6 — Objetiva sem barra e layout inalterado

**Ação humana:**
- [x] Clicar no card **"Múltipla escolha"**
- [x] Confirmar que a barra cinza de **"Quantidade de linhas"** / **"Correção com competências"** **não** aparece
- [x] Confirmar que o editor e a área de alternativas seguem o layout habitual (sem painel de linhas)
- [x] (Smoke) Repetir rapidamente para **"Arquivo anexado"** (e **"Somatório"** / **"Preencher lacunas"** se o client tiver as flags)

**Referência técnica (para automação):**
- URL: `/provas/prova/{ets_pk}/editar/`
- Condição: `v-if="examQuestion.question.categoryDisplay == 'Discursiva'"` → barra ausente quando `Objetiva`
- Seletor negativo: `expect(page.locator('label:has-text("Quantidade de linhas")')).toHaveCount(0)`
- Fixture: objetiva `category=1`

---

### 5.4 Compatibilidade PAS [Automatizável ✅]

#### Cenário 7 — Valor esperado em PAS Tipo B

**Ação humana:**
- [x] Usar (ou criar) um caderno com formato PAS (`exam_format == 1`)
- [x] Abrir elaboração e selecionar **"Tipo B: Numérica"**
- [x] Confirmar que o campo **"Valor esperado"** aparece **acima** do editor (na região da barra), com texto de ajuda *"Informe um valor para que o sistema faça a correção automática."*
- [x] Digitar um valor válido (ex.: `42`) e ver o badge **"Discursiva com correção automática"**
- [x] Digitar valor inválido (ex.: `1000`) e ver mensagem de erro de faixa
- [x] Salvar valor válido, recarregar e confirmar persistência

**Referência técnica (para automação):**
- URL: `/provas/prova/{ets_pk}/editar/` com `exam.exam_format == 1`
- Seletor: `#bTypeExpectedAnswer-{id}`
- Estado esperado: validação `0–999`; badge verde quando válido; erro `"Informe um número entre 0 e 999."`
- Fixture: `Exam(exam_format=1)` + Tipo B

> Se o ambiente de QA não tiver caderno PAS, marcar este cenário como bloqueado e registrar em Seção 7 com workaround (criar via mixer/`exam_format=1` no shell).

---

### 5.5 Responsividade da barra [Apenas Manual 👁]

#### Cenário 8 — Viewport estreita (~375px)

**Ação humana:**
- [x] Em DevTools, definir viewport ~375px de largura com questão **"Discursiva"**
- [x] Confirmar que a barra permanece **entre** os cards de tipo e o editor (não desce para baixo do enunciado)
- [x] Confirmar que os campos quebram em até duas linhas (`flex-wrap`) e permanecem usáveis
- [x] Confirmar ausência de scroll horizontal obrigatório para operar os controles da barra

**Referência técnica (para automação):**
- URL: `/provas/prova/{ets_pk}/editar/`
- Classes: `tw-flex tw-flex-wrap tw-gap-x-6 tw-gap-y-3` + `tw-min-w-[200px]` / `tw-min-w-[240px]`
- Estado esperado: campos acima do editor; sem overflow-x forçado
- Fixture: mesma discursiva; viewport Playwright `page.set_viewport_size({"width": 375, "height": 812})`
- Classificação: manual preferencial (julgamento de overflow/UX); snippet Playwright pode smoke-testar posição Y relativa

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

Comparar lado a lado com o mockup OpenSpec e a intenção da task ClickUp:

- [x] Print da aba **"Enunciado"** em **"Discursiva"** (desktop) — barra abaixo dos cards, editor ampliado. ![](./image.png)
- [x] Print em **"Redação"** — mesma barra + `30` linhas ![](./image_1.png)
- [x] Print em **"Múltipla escolha"** — sem barra ![](./image_2.png)
- [x] Print em viewport 375px — barra com wrap ![](./image_3.png)
- [x] Abrir `openspec/changes/reorganizar-campos-elaboracao-questao-discursiva/references/barra-config-discursiva.html` e comparar ordem/estrutura (não pixels do mockup CDN)
- [x] Confirmar rótulos literais da UI: **"Quantidade de linhas"** e **"Correção com competências"** (a task ClickUp diz “Competências da redação”, mas o rótulo real no DOM é **"Correção com competências"**)

---

## 7. Bugs and Observations (Problemas Encontrados)

> Instruções: documentar com `> [!BUG]` ou `> [!WARNING]` e tags `[UX/UI]`, `[Backend Logic]`, `[Database]`, `[Spec Gap]`.

**Formato obrigatório por bug:**
1. **Title**
2. **Context/Root Cause**
3. **Expected Behavior** (citar OpenSpec: `spec.md` L.XX — ou `(inferência de UX — Spec Gap)`)
4. **Workaround**

> [!BUG]
> **Bug 1: Switch "Correção com competências" não persiste sozinho — estado amarrado à seleção do modelo**  
> **Categoria:** `[Backend Logic]` / `[UX/UI]`  
> **Origem:** Cenário 4 (Seção 5.2) — Salvar correção com competências.  
> **Contexto / Root Cause:** Na barra de discursiva, o switch **"Correção com competências"** e o select de modelo (`textCorrection`) não persistem de forma independente:
> 1. **Desativar:** colocar o switch em **"não"** (off) e salvar **não** grava o desligamento se ainda houver um modelo selecionado no select. Após reload, a correção com competências volta ativa.
> 2. **Ativar:** ligar o switch **sem** escolher um modelo no select e salvar **também não** persiste. Só “cola” quando um modelo é selecionado.
> 3. **Vice-versa para desativar:** para desligar de forma persistente, é necessário **não selecionar nenhum modelo** no select (opção vazia / limpar a escolha) e então salvar — o switch sozinho não basta.
>
> Hipótese técnica (legado, não introduzido pelo reposicionamento da barra): o salvamento parece depender de `textCorrection` (UUID ou `null`) mais do que do boolean `correctionWithCompetencies`. No template `exam_request_teacher_subject_edit_new.html`, os watchers Vue usam o nome `correctWithCompetencies` (sem “ion”), enquanto o `v-model` do switch é `correctionWithCompetencies` — possível dessincronia UI ↔ clear do select.
>
> **Comportamento Esperado:** (conforme OpenSpec: `specs/exam-elaboration-discursive-config-bar/spec.md` — Scenario *Salvar correção com competências após reposicionamento*): ao ativar o switch, escolher modelo e salvar, `correctionWithCompetencies` e `textCorrection` persistem; **(inferência de UX — Spec Gap para o caminho inverso)** desligar o switch e salvar deve persistir `correctionWithCompetencies === false` (e limpar/ignorar modelo), sem exigir gambiarra de “desmarcar o select”. Ativar o switch sem modelo pode exigir validação explícita na UI, mas o estado do switch não deve ser ignorado no PATCH.
>
> **Workaround:**
> - Para **ativar** e persistir: ligar o switch **e** selecionar um modelo de correção antes de **"Salvar"**.
> - Para **desativar** e persistir: limpar o select (nenhum modelo selecionado / opção vazia) e então **"Salvar"** — não confiar só no switch em **"não"**.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **IDs estáveis na barra:** o container da barra ainda não tem `id` semântico (`discursive-config-bar`). Os inputs já usam IDs dinâmicos (`quantityLines-{id}`) — gold standard. Adicionar ID no wrapper facilita Playwright.

> [!NOTE]
> **Ausência de teste automatizado da feature:** a branch só cobre acesso HTTP à view. Um teste Playwright/pytest futuros deveria cobrir presença/ausência da barra por `categoryDisplay` e persistência de `quantity_lines`.

> [!NOTE]
> **Áudio/vídeo da task ClickUp:** anexos `File.mp4` e `File (5).ogg` podem revelar pedidos além dos dois campos. Se durante o QA surgir expectativa extra (ex.: tema da redação), registrar como `[Spec Gap]` e não expandir escopo sem produto.

> [!NOTE]
> **Nomenclatura ClickUp vs UI:** task fala em “Competências da redação”; UI e OpenSpec usam **"Correção com competências"**. Manter o rótulo real nos planos e KIs.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.

🔗 **[Ver Mapeamento de Tela](../docs/tests/usability/exam_request_teacher_subject_edit_new.md)**

### Snippet sugerido (Playwright + mixer) — smoke da barra

```python
import pytest
from mixer.backend.django import mixer
# ... setup Persona Professor + ExamTeacherSubject + Question(category=0)
# conforme Seção 4; garantir has_new_teacher_experience=True

def test_discursive_config_bar_above_editor(page, live_server, ets, teacher_user):
    page.goto(f"{live_server.url}/provas/prova/{ets.pk}/editar/")
    # login helper do projeto...
    page.locator("button.question-type-card", has_text="Discursiva").click()
    bar_label = page.locator("label", has_text="Quantidade de linhas")
    assert bar_label.count() == 1
    # Garantir que não há painel duplicado abaixo do editor
    assert page.locator("label", has_text="Quantidade de linhas").count() == 1
    page.locator('input[name="quantity_lines"]').fill("12")
    page.locator("button.lize-btn-primary", has_text="Salvar").click()
    page.reload()
    assert page.locator('input[name="quantity_lines"]').input_value() == "12"
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante o teste:** _(preencher)_
- **Ida e volta com o desenvolvedor:** _(preencher)_
- **Como melhorar o fluxo desta task:** _(preencher)_

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- A task ClickUp e a UI usam rótulos diferentes para o mesmo campo (“Competências da redação” vs “Correção com competências”). O prompt V2 poderia exigir um checklist explícito de **paridade de rótulos ClickUp ↔ DOM** para evitar que o QA procure texto que não existe na tela.
- O mapeamento antigo em `exam_request_teacher_subject_edit_new.md` apontava URL/menu incorretos (`/exams/elaboracao/`). O prompt poderia mandar validar a Seção 1 do usability map contra `sidebar-items/teacher.html` a cada plano.
- Feature 100% layout sem pytest novo: sugerir no plano um “gate mínimo” (smoke Playwright) já na Seção 4 quando `tasks.md` marcar testes manuais como pendentes.

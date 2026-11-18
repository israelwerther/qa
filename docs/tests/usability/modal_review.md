# Mapeamento de Tela: Modal Revisar — aba Ortografia (modal_review.html)

Mapeamento técnico do modal de revisão de caderno, com foco na aba **Ortografia** e no bloqueio do botão **Aprovar** por sugestão pendente.

---

## 1. URLs e Navegação

| Destino | Rótulo real no menu UI | URL Django | View / Action |
|---------|------------------------|------------|---------------|
| Editar caderno | **Cadernos** → **Opções** → **Editar caderno** | `/provas/<uuid:pk>/editar/` | `exams:exams_update` (`ExamUpdateView`) |
| Revisar caderno | **Cadernos** → **Opções** → **Revisar caderno** | `/provas/<uuid:pk>/revisar/` | `exams:exam_review` (`ExamReviewView`) |
| Modal de revisão | Abre ao clicar em **Revisar** (card de professor/solicitação) ou em **Todas as questões** | mesmo documento | Modal `#reviewModal` |
| Aba Ortografia | Aba com ícone **A** e badge âmbar | — | Renderizada por `tabReview` quando `spellingReview.enabled` |

> O template `modal_review.html` é incluído por `exam_request_create_update_new.html` (linha ~3710), portanto é servido tanto por `/editar/` quanto por `/revisar/`.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões necessárias

- Coordenação com `exams.can_review_questions_exam` para ver/decidir as sugestões.
- `exams.change_exam` para abrir a tela de edição.
- O caderno não pode estar com malote/respostas/aplicação iniciada para o escopo de conjunto; para a prova, valem as regras de status do caderno.
- Sigilo do caderno restrito bloqueia o acesso (403), exceto superusuário.

### Setup de banco (`mixer`)

```python
from fiscallizeon.exams.tests.spelling_review_fixtures import (
    SpellingScenarioMixin,
    clear_user_cache,
)

class TesteModalRevisao(SpellingScenarioMixin, CustomTransactionTestCase):
    databases = '__all__'

    def setUp(self):
        self.build_scenario(block_approval=True)
        self.coordinator.add_permission('exams', 'change_exam')
        self.coordinator.add_permission('exams', 'can_review_questions_exam')
        clear_user_cache(self.coordinator)
        self.client.force_login(self.coordinator)
        self.url = f'/provas/{self.exam.pk}/editar/'

    def test_aba_ortografia(self):
        self.suggestion()
        response = self.client.get(self.url)
        self.assertContains(response, 'data-spelling-review-tab')
        self.assertContains(response, 'scope="exam"')
```

A fixture `suggestion()` cria uma `SpellingSuggestion` pendente de `Haviam` → `Havia` na questão `self.question`.

---

## 3. Seletores DOM e Ações

### Modal e navegação

| Elemento | Seletor estável | Ação / Observação |
|----------|-----------------|-------------------|
| Modal | `#reviewModal` | `modal-fullscreen`; o cabeçalho mostra **Revisão** ou o nome do professor. |
| Alternar visão | Textos `Todas as questões` / `Questões solicitadas` e `Notas` | `mainViewReview = 'questions' | 'notes'`. |
| Voltar | `[aria-label="Voltar"]` | Fecha via `openModal('reviewModal')`. |
| Card do professor | `button` com texto `Revisar` | Carrega questões e chama `openModal('reviewModal')`. |
| Todas as questões | Ação que chama `handleViewAllQuestions()` | Busca `/provas/api/<pk>/...?review=true` e abre o modal. |

### Aba Ortografia

| Elemento | Seletor estável | Ação / Observação |
|----------|-----------------|-------------------|
| Aba | `div` com texto `Ortografia` (dentro da barra de abas) | `@click="tabSelected = 'Ortografia'"`; só existe se `spellingReview.enabled`. |
| Badge da aba | `[data-spelling-review-tab-badge]` | Número de sugestões pendentes da questão selecionada (`spellingPendingForReview`). |
| Conteúdo da aba | `[data-spelling-review-tab]` | `v-if="tabSelected == 'Ortografia' && selectedExamQuestionReview"`. |
| Painel embutido | `spelling-review-panel` com `scope="exam"` | Props: `:urls="spellingReview.urls"`, `:scope-id="spellingReview.examId"`, `:exam-question-id="selectedExamQuestionReview.id"`, `embedded`. |
| Aprovar bloqueado | `[data-spelling-approve-blocked]` | Fica na aba **Enunciado**, no lugar do botão Aprovar. `aria-disabled="true"`; `title` com a mensagem de pendência; clique muda para a aba Ortografia. |
| Aprovar normal | `button` com `@click="openDialog(selectedExamQuestionReview, 0)"` | Renderizado quando `!isSpellingBlockedReview`. |

> O botão bloqueado existe apenas na aba **Enunciado**; nas demais abas o fluxo de aprovação segue o comportamento anterior. A condição também exige `canReviewSelectedQuestion`, status diferente de `Aprovada` e aplicação não finalizada.

### Bootstrapping

| Elemento | Seletor | Conteúdo |
|----------|---------|----------|
| URLs da API | `#spelling-review-urls` (`json_script`) | Placeholders de UUID para `summary`, `create`, `suggestions`, `apply_many`, `detail`, `stop`, `retry`, `apply`, `ignore`. |
| Pendências por questão | `#spelling-review-pending` (`json_script`) | Mapa `{ "<exam_question_id>": <n> }`. |
| Estado Vue | `spellingReview` no `data` do app | `enabled`, `examId`, `blockApproval`, `urls`, `pendingByEq`. |

---

## 4. API Routes

As mesmas rotas do painel de prova, com escopo `exam`:

| Operação | Método | Rota |
|----------|--------|------|
| Resumo | GET | `/provas/api/revisao-ortografica/resumo/?exam=<uuid>` |
| Criar revisão | POST | `/provas/api/revisao-ortografica/` (`{"exam": "<uuid>"}`) |
| Detalhe/polling | GET | `/provas/api/revisao-ortografica/<uuid:review>/` |
| Parar | POST | `/provas/api/revisao-ortografica/<uuid:review>/parar/` |
| Tentar de novo | POST | `/provas/api/revisao-ortografica/<uuid:review>/tentar-de-novo/` |
| Listar sugestões da questão | GET | `/provas/api/revisao-ortografica/sugestoes/?exam=<uuid>&exam_question=<uuid>&status=pending` |
| Aplicar | POST | `/provas/api/revisao-ortografica/sugestoes/<uuid:suggestion>/aplicar/` |
| Ignorar | POST | `/provas/api/revisao-ortografica/sugestoes/<uuid:suggestion>/ignorar/` |
| Aplicar todas | POST | `/provas/api/revisao-ortografica/sugestoes/aplicar-todas/` (`{"exam": "<uuid>"}`) |

No modal, a lista é filtrada por `exam_question=<id da questão selecionada>`; o resumo e a criação usam o caderno inteiro.

---

## 5. Complex Database Entities

- `SpellingReview` do caderno (`exam_id` preenchido).
- `SpellingSuggestion` pendente por questão/campo.
- `QuestionSpellingState` (impressão digital dos textos e última checagem). O `spelling_pending_by_eq` vem das `SpellingSuggestion` pendentes por questão.
- `ClientQuestionsConfiguration.block_approval_with_pending_spelling` (regra que ativa o bloqueio).

---

## 6. Observações de Comportamento

- A aba Ortografia aparece mesmo sem revisão iniciada: mostra o resumo e o botão para revisar.
- O badge e o botão bloqueado somem quando não há pendência para a questão selecionada.
- Aplicar/ignorar atualiza o badge e o botão Aprovar sem recarregar a página (o painel emite/atualiza o estado da questão).
- Se a questão não puder ser editada, a sugestão aparece, mas **Aplicar** fica desabilitado com tooltip; **Ignorar** continua disponível.
- O bloqueio é por questão: aprovar outras questões do caderno continua permitido.

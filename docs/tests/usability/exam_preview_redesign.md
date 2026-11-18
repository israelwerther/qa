# Mapeamento de Tela: Visualizar caderno (exam_preview_redesign.html)

Mapeamento técnico da tela de visualização do caderno, incluindo o painel de revisão ortográfica, os indicadores de pendência por questão e o bloqueio do botão Aprovar.

---

## 1. URLs e Navegação

| Destino | Rótulo real no menu UI | URL Django | View / Action |
|---------|------------------------|------------|---------------|
| Lista de cadernos | **Cadernos** | `/provas/` | `exams:exams_list` (`ExamListView`) |
| Visualizar caderno | **Opções** → **Visualizar prova** (abre em nova aba) | `/provas/<uuid:pk>/visualizar` | `exams:exams_preview` (`ExamPreviewView` ou equivalente) |
| Título do documento | — | — | `{% block title %}Lize - Visualizar caderno{% endblock %}` |
| Fechar a aba | Ícone **X** no header (`aria-label="Fechar"`) | — | `closeExamPreviewTab(close_url)` |

> A tela usa `{% extends 'redesign/base_component.html' %}` com sidebar e mensagens suprimidas. O conteúdo principal está em `fiscallizeon/exams/templates/dashboard/exams/exam_preview/includes/exam_preview_redesign_content.html`.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões necessárias

- Usuário autenticado vinculado ao `Client` dono do caderno.
- Permissão de status do caderno (`exams.can_view_exams_<status>`) quando o usuário possui permissões por status; superusuário ignora a checagem.
- Caderno sigiloso restrito retorna 403 para quem não tem acesso (`confidential_exam_is_restricted`).
- Para ver o botão **Aprovar** e o bloqueio: `exams.can_review_questions_exam` (a view expõe `can_approve` no contexto do card).

### Setup de banco (`mixer`)

O cenário pronto está em `fiscallizeon/exams/tests/spelling_review_fixtures.py`:

```python
from fiscallizeon.exams.tests.spelling_review_fixtures import (
    SpellingScenarioMixin,
    clear_user_cache,
)

class TesteVisualizarCaderno(SpellingScenarioMixin, CustomTransactionTestCase):
    databases = '__all__'

    def setUp(self):
        # block_approval=True liga a regra da escola
        self.build_scenario(block_approval=True)
        self.coordinator.add_permission('exams', 'can_review_questions_exam')
        clear_user_cache(self.coordinator)
        self.client.force_login(self.coordinator)

        # Sugestão pendente para a questão criada no cenário
        self.suggestion()

    def test_abre_painel(self):
        response = self.client.get(f'/provas/{self.exam.pk}/visualizar')
        self.assertEqual(response.status_code, 200)
```

`build_scenario()` cria: `Client`, `ClientQuestionsConfiguration`, `Unity`, `SchoolCoordination`, `coordinator`, `teacher_user`, `Inspector`, `TeacherSubject`, `Exam` em elaboração, `Grade`, `ExamTeacherSubject`, uma `Question` com erros de concordância (`ENUNCIATION`) e o respectivo `ExamQuestion`.

### Massa mínima para a tela renderizar

- `Exam.status` em elaboração (ou outro status com permissão do usuário).
- Pelo menos um `ExamQuestion` com `question` preenchida.
- `ClientQuestionsConfiguration.block_approval_with_pending_spelling` define o bloqueio (default `False`).

---

## 3. Seletores DOM e Ações

### Header

| Elemento | Seletor estável | Ação / Observação |
|----------|-----------------|-------------------|
| Botão do painel | `[data-spelling-review-open]` | Alterna `$store.examPreview.openSpellingReview()` / `closeSpellingReview()`; `aria-expanded` reflete o estado. |
| Rótulo do botão | `[data-spelling-review-open] span` (texto `Revisão ortográfica`) | Oculto em telas pequenas (`tw-hidden sm:tw-inline`). |
| Badge de pendências | `[data-spelling-review-open] span[aria-label$="sugestões pendentes"]` | `x-show` quando `$store.examPreview.spellingPendingTotal() > 0`; texto é o total. |
| Fechar aba | `button[aria-label="Fechar"]` | Chama `closeExamPreviewTab(...)`. |

### Navegação lateral de questões

| Elemento | Seletor estável | Ação / Observação |
|----------|-----------------|-------------------|
| Ponto de pendência | `[data-spelling-dot]` | Exibido quando `spellingPendingFor(<eq-id>) > 0`; `aria-hidden="true"`, tooltip no botão da questão. |
| Botão da questão | Botão dentro de `[data-spelling-dot]` pai, texto `01`, `02`, ... | `@click="goToQuestion('<eq-id>')"`; `@dblclick` seleciona. |
| Filtro "com sugestão ortográfica" | `[data-spelling-filter]` | `aria-pressed` reflete `filterOnly`; alterna a exibição das questões sem pendência. |
| Contador do filtro | `[data-spelling-filter] span span` | Número de questões com sugestão (`spellingQuestionsWithPending()`). |

### Menu de ações da questão

Arquivo: `fiscallizeon/exams/components/exam_preview/exam_preview_actions.html`.

| Elemento | Seletor estável | Ação / Observação |
|----------|-----------------|-------------------|
| Aprovar habilitado | `button[x-show="!$store.examPreview.isSpellingApprovalBlocked('<eq-id>')"]` | `@click="applyStatus('<eq-id>', 0)"`. |
| Aprovar bloqueado | `[data-spelling-approve-blocked]` | Visível quando `isSpellingApprovalBlocked(<eq-id>)`; botão interno `aria-disabled="true"` e sem ação. |
| Tooltip do bloqueio | `#spelling-approve-tip-<eq-id>` | Texto: `<n> sugestões ortográficas pendentes. Aplique ou ignore cada uma para aprovar.` |
| Visto | Botão com texto `Visto` | `applyStatus('<eq-id>', 5)`. |
| Sugerir correção | Botão com texto `Sugerir correção` | `applyStatus('<eq-id>', 3)`. |

### Painel lateral (`exam_preview_spelling_review_panel.html`)

O painel é um `<aside>` fixo à direita, sem overlay (`role="complementary"`, `aria-label="Revisão ortográfica"`). Não fecha ao clicar fora; fecha com **ESC** ou no botão **X**.

| Elemento | Seletor / texto | Ação / Observação |
|----------|-----------------|-------------------|
| Container | `aside.exam-preview-spelling-panel` | `x-show="sr.open"`. |
| Fechar | `button[aria-label="Fechar revisão ortográfica"]` | `store.closeSpellingReview()`. |
| Aviso da regra | Texto `Esta escola exige aplicar ou ignorar cada sugestão antes de aprovar a questão.` | `x-show="sr.blockApproval"`. |
| Carregando resumo | Texto `Carregando…` | `sr.loading && !sr.summary`. |
| Total de questões | Texto `N questões na prova` | `sr.summary.total` + `questionsLabel`. |
| Iniciar | Botão `Revisar a prova` | `store.startSpellingReview()`; desabilitado se `summary.total == 0`. |
| Progresso | Texto `X de Y questões verificadas` + barra | Atualiza por polling (~3s). |
| Parar | Botão `Parar` | Visível enquanto `spellingIsRunning()`; `store.stopSpellingReview()`. |
| Revisar de novo | Botão `Revisar de novo` | Visível quando não está rodando. |
| Falhas | Container amarelo com `Tentar de novo` | `store.spellingFailed().count > 0`; lista os números das questões falhas. |
| Aba de filtro | `[role="tablist"][aria-label="Filtrar sugestões"]` → `Pendentes (n)` / `Todas (n)` | `sr.tab = 'pending' | 'all'`. |
| Aplicar todas | Botão `Aplicar todas (n)` | Abre confirmação (`sr.confirmingAll`). |
| Confirmação | `[role="group"][aria-label="Confirmar aplicar todas"]` → `Aplicar todas` / `Cancelar` | Mostra contagem de sugestões, questões e travadas. |
| Estado vazio | Texto `Nenhum erro de ortografia ou concordância encontrado` ou `Todas as sugestões foram resolvidas` | Depende de `sr.lists.all.count`. |
| Grupo por questão | `<section>` com título `Questão N` | `store.spellingGroups(tab)`; inclui `Ir para a questão`. |
| Item de sugestão | `<li>` com del/ins e badge de tipo | Texto riscado (`<del>`) + correção (`<ins>`) e explicação. |
| Aplicar | Botão `Aplicar` | `store.applySpelling(item)`; desabilitado se `item.editable == false`, com tooltip. |
| Ignorar | Botão `Ignorar` | `store.ignoreSpelling(item)`. |
| Estados | Textos `Aplicada`, `Ignorada — não volta nas próximas checagens`, `O texto mudou depois da checagem. Peça de novo para conferir.` | `item.status`. |
| Carregar mais | Botão `Carregar mais` | `store.loadSpellingList(tab)`. |

> **Lacuna de automação:** os controles internos do painel não possuem `data-*`/`id` únicos. Hoje a automação depende de texto ou de `x-show`/`x-text`. Antes de estabilizar Playwright, avaliar adicionar identificadores estáveis (ex.: `data-spelling-start`, `data-spelling-apply`, `data-spelling-ignore`).

### Bootstrapping (JSON no HTML)

| Elemento | Seletor | Conteúdo |
|----------|---------|----------|
| URLs da API | `#exam-preview-spelling-urls` (`json_script`) | `summary`, `create`, `suggestions`, `apply_many`, `detail`, `stop`, `retry`, `apply`, `ignore` com placeholder de UUID. |
| Pendências por questão | `#exam-preview-spelling-pending` (`json_script`) | Mapa `{ "<exam_question_id>": <n> }`. |
| Config do store | `spellingBlockApproval`, `spelling_urls`, `spelling_pending_by_eq` no contexto da view | `blockApproval` e `examId` do store Alpine. |

---

## 4. API Routes

Prefixo: `/provas/api/revisao-ortografica/`.

| Operação | Método | Rota | Nome de reverse |
|----------|--------|------|-----------------|
| Resumo/prévia | GET | `/provas/api/revisao-ortografica/resumo/?exam=<uuid>` | `exams:spelling-review-summary` |
| Criar revisão | POST | `/provas/api/revisao-ortografica/` com `{"exam": "<uuid>"}` | `exams:spelling-review-create` |
| Detalhe / polling | GET | `/provas/api/revisao-ortografica/<uuid:review>/` | `exams:spelling-review-detail` |
| Parar | POST | `/provas/api/revisao-ortografica/<uuid:review>/parar/` | `exams:spelling-review-stop` |
| Tentar de novo | POST | `/provas/api/revisao-ortografica/<uuid:review>/tentar-de-novo/` | `exams:spelling-review-retry` |
| Listar sugestões | GET | `/provas/api/revisao-ortografica/sugestoes/?exam=<uuid>&status=pending&created_after=<iso>` | `exams:spelling-suggestion-list` |
| Aplicar | POST | `/provas/api/revisao-ortografica/sugestoes/<uuid:suggestion>/aplicar/` | `exams:spelling-suggestion-apply` |
| Ignorar | POST | `/provas/api/revisao-ortografica/sugestoes/<uuid:suggestion>/ignorar/` | `exams:spelling-suggestion-ignore` |
| Aplicar todas | POST | `/provas/api/revisao-ortografica/sugestoes/aplicar-todas/` com `{"exam": "<uuid>"}` | `exams:spelling-suggestion-apply-many` |

Respostas usam camelCase (`CamelCaseAPIMixin`): `pendingByExamQuestion`, `blockApproval`, `activeReview`, `latestReview`, `questionUpdate`, etc.

---

## 5. Complex Database Entities

- `SpellingReview` (escopo por `exam` ou `exam_teacher_subject`; status `pending`/`running`/`ready`/...).
- `SpellingReviewItem` (uma linha por questão revisada; estados `checked`/`unchanged`/`failed`).
- `SpellingSuggestion` (sugestão por campo: enunciado, alternativa, texto base, resposta comentada, feedback, conteúdo de apoio, tema, lacunas; status `pending`/`applied`/`ignored`/`outdated`).
- `QuestionSpellingState` (impressão digital dos textos e data da última checagem; usado para decidir o que reenviar à IA). Os indicadores e o bloqueio são calculados a partir das `SpellingSuggestion` pendentes.
- `ClientQuestionsConfiguration.block_approval_with_pending_spelling` (regra da escola; default `False`).

---

## 6. Observações de Comportamento

- O resumo (`GET /resumo/`) **não** cria revisão; só a criação (`POST`) enfileira a task Celery `run_spelling_review`.
- Sugestões aparecem conforme cada questão termina (polling), não só ao final.
- "Ignorar" é definitivo para aquela sugestão e não retorna em checagens futuras, mesmo com contexto diferente.
- "Aplicar" altera o campo da questão e, se o texto base for compartilhado, a correção vale para todas as questões que o usam.
- Se o texto mudou depois da checagem, a sugestão fica `outdated` e não pode ser aplicada.
- Aprovar é bloqueado apenas quando a regra da escola está ligada e há sugestão pendente para **aquela** questão. O caderno em si nunca é bloqueado.
- O painel não consome créditos de IA.

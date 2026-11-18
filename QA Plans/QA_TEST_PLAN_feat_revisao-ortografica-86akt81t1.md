## 0. Metadata (Metadados de QA)

| Campo                      | Valor                                                                             |
| -------------------------- | --------------------------------------------------------------------------------- |
| **Data:**                  | 2026-11-13                                                                        |
| **Task ClickUp:**          | [Revisão ortográfica no conjunto e na prova](https://app.clickup.com/t/86akt81t1) |
| **Branch:**                | `feat/revisao-ortografica-86akt81t1`                                              |
| **Natureza da Tarefa:**    | `[Business Feature]`                                                              |
| **Área da Feature:**       | Provas / Elaboração e Validação de Questões (Revisão Ortográfica com IA)          |
| **Nível de Risco:**        | Alto (IA assíncrona, aprovação de questões, multi-tenant e réplicas)              |
| **Qualidade da OpenSpec:** | ⭐⭐ (2 estrelas)                                                                 |

**Por que 2 estrelas:** a entrega não possui change OpenSpec própria (`proposal`, `design`, `specs`, `tasks`). O único change na branch, `unificar-visualizacao-alternativas-revisao-17tu7rpaqj8`, é de outra tarefa (peso/negrito no modal de revisão) e não descreve a revisão ortográfica. O entendimento veio da descrição da task, do diff e dos testes automatizados.

---

## 1. Summary of Changes (Resumo das Alterações)

A feature adiciona uma checagem de **ortografia e concordância** por IA em dois pontos:

1. **Conjunto (elaboração):** o professor dono da solicitação pede a revisão de todas as suas questões em `/provas/prova/<uuid>/editar/`. As sugestões aparecem em um painel lateral e podem ser aplicadas ou ignoradas.
2. **Prova (validação):** quem valida o caderno pede a revisão em **Visualizar caderno** (`/provas/<pk>/visualizar`) ou pela aba **Ortografia** do modal **Revisar** (`/provas/<pk>/editar/` ou `/provas/<pk>/revisar/`).

### Backend

- Novos modelos em `fiscallizeon/ai/models.py`: `SpellingReview`, `SpellingReviewItem`, `SpellingSuggestion` e `QuestionSpellingState`.
- Serviços em `fiscallizeon/ai/services/spelling_review/`: extração de textos (`extract.py`), criação/reuso de revisão (`review.py`), pendências (`pending.py`), decisões aplicar/ignorar (`decisions.py`) e regra de bloqueio (`approval.py`).
- Task Celery `fiscallizeon.ai.tasks.run_spelling_review`, roteada explicitamente para `celery-priority`, com concorrência configurável (`SPELLING_REVIEW_CONCURRENCY`, default 5).
- API DRF em `fiscallizeon/exams/api/spelling_review.py`, sob `/provas/api/revisao-ortografica/`, com escopos `exam` e `ets`/`examTeacherSubject`.
- Regra da escola `ClientQuestionsConfiguration.block_approval_with_pending_spelling` (default `False`). Quando ligada, `ExamQuestion.can_approve_with_spelling()` bloqueia a aprovação de uma questão com sugestão pendente.
- A revisão ortográfica **não consome créditos de IA** e grava `OpenAIQuery`.

### Frontend

- `core/static/js/spelling_review.js`: helpers puros (`LizeSpellingReview`) compartilhados e testados via Node.
- Painel Alpine na prova (`exam_preview_spelling_review_panel.html` + `exam_preview_spelling_review.js`) com botão no header, badge total, pontos por questão, filtro e bloqueio do Aprovar.
- Componente Vue reutilizável (`vue-spelling-review-panel.html`) na elaboração do professor e na aba Ortografia do modal de revisão.
- Toggle novo na tela **Configurações → Questões**.

### Testes Automatizados

- API: `fiscallizeon/exams/tests/api/test_spelling_review_api.py`
- Bloqueio de aprovação e toggle: `fiscallizeon/exams/tests/api/test_status_question_spelling.py`
- Contextos das telas: `fiscallizeon/exams/tests/views/test_exam_preview_spelling.py`, `test_exam_update_spelling_review.py`, `test_teacher_edit_spelling_review.py`
- Serviço/task: `fiscallizeon/ai/tests/test_spelling_review_task.py`
- Helpers JS: `fiscallizeon/core/tests/test_spelling_review_js.py`
- Componente do preview: `fiscallizeon/exams/tests/components/test_exam_preview.py`

---

## 2. Scope Boundaries (Diferenças de Escopo)

### IN SCOPE

- Pedir, acompanhar (polling), parar e repetir a revisão ortográfica no **conjunto** e na **prova**.
- Exibir sugestões com trecho, correção, tipo (ortografia/concordância), campo e explicação.
- Aplicar e ignorar sugestões individualmente e aplicar todas as pendentes editáveis.
- Atualizar o texto da questão/alternativa/texto base após aplicar.
- Estados `outdated`, `locked`, `failed`, `unchanged`, revisão vazia e revisão interrompida.
- Bloqueio de aprovação por pendência quando a regra da escola está ligada; liberação após aplicar/ignorar.
- Persistência do toggle em Configurações → Questões.
- Permissões: professor dono no conjunto; coordenação na prova; professor vê apenas as próprias questões na prova; isolamento por `Client`; sigilo e permissões por status.
- Não-regressão dos fluxos existentes de revisão/aprovação e do modal de revisão.

### OUT OF SCOPE

- App SPA do aluno (`/api/v3/`, `lize-student`) e qualquer tela do aluno.
- Integrações externas (Perseus, TOTVS), impressão, OMR e correção.
- Consumo/cobrança de créditos de IA.
- Mudança de modelo, prompt ou provedor de IA.
- Alteração no `fiscallizeon/analytics/templates/analytics/grade_map.html` (ajuste de colunas de nomes de provas) presente no diff: **pertence a outro escopo** e não deve ser misturado na validação desta task.
- A change OpenSpec `unificar-visualizacao-alternativas-revisao-17tu7rpaqj8` (peso/negrito de alternativas no modal): não é critério desta task, mas o modal é compartilhado, então entra apenas como smoke de não-regressão.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| #   | Destino                    | Rótulo real no menu UI                                     | URL Django                        | View / template                                                                            |
| --- | -------------------------- | ---------------------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------ |
| 1   | Configurações das questões | **Configurações** → **Questões**                           | `/membros/questoes/configuracoes` | `clients:questions_configurations` / `questions_configutation.html`                        |
| 2   | Solicitações de elaboração | **Cadernos** → **Solicitações de elaboração**              | `/provas/professor/`              | `exams:exam-teacher-subject-list`                                                          |
| 3   | Elaboração do conjunto     | **Continuar** / **Editar questões** no card da solicitação | `/provas/prova/<uuid:pk>/editar/` | `exams:exam_teacher_subject_edit_questions` / `exam_request_teacher_subject_edit_new.html` |
| 4   | Lista de cadernos          | **Cadernos**                                               | `/provas/`                        | `exams:exams_list` / `exam_list_new.html`                                                  |
| 5   | Visualizar caderno         | **Opções** → **Visualizar prova** (nova aba)               | `/provas/<uuid:pk>/visualizar`    | `exams:exams_preview` / `exam_preview_redesign.html`                                       |
| 6   | Editar caderno             | **Opções** → **Editar caderno**                            | `/provas/<uuid:pk>/editar/`       | `exams:exams_update` / `exam_request_create_update_new.html`                               |
| 7   | Revisar caderno            | **Opções** → **Revisar caderno**                           | `/provas/<uuid:pk>/revisar/`      | `exams:exam_review` / `exam_request_create_update_new.html`                                |

**Pré-condição de template da elaboração:** a tela nova só é servida se `user.inspector.has_new_teacher_experience` **ou** `user.client_has_new_teacher_experience` **ou** `exam.created_by == user`. Sem isso, cai no template legado e o botão/painel não existe.

**Rotas da API** (todas sob `/provas/api/revisao-ortografica/`):

| Operação           | Método | Rota                                                         |
| ------------------ | ------ | ------------------------------------------------------------ |
| Resumo             | GET    | `/resumo/?exam=<uuid>` ou `?ets=<uuid>`                      |
| Criar revisão      | POST   | `/` com `{"exam": "<uuid>"}` ou `{"ets": "<uuid>"}`          |
| Detalhe/polling    | GET    | `/<uuid:review>/`                                            |
| Parar              | POST   | `/<uuid:review>/parar/`                                      |
| Tentar de novo     | POST   | `/<uuid:review>/tentar-de-novo/`                             |
| Listar sugestões   | GET    | `/sugestoes/?exam=<uuid>&status=pending&created_after=<iso>` |
| Listar por questão | GET    | `/sugestoes/?exam=<uuid>&exam_question=<uuid>`               |
| Aplicar            | POST   | `/sugestoes/<uuid:suggestion>/aplicar/`                      |
| Ignorar            | POST   | `/sugestoes/<uuid:suggestion>/ignorar/`                      |
| Aplicar todas      | POST   | `/sugestoes/aplicar-todas/`                                  |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### 4.1 Comando para executar os testes automatizados

```bash
source venv/bin/activate
pytest \
  fiscallizeon/ai/tests/test_spelling_review_task.py \
  fiscallizeon/exams/tests/api/test_spelling_review_api.py \
  fiscallizeon/exams/tests/api/test_status_question_spelling.py \
  fiscallizeon/exams/tests/views/test_exam_preview_spelling.py \
  fiscallizeon/exams/tests/views/test_exam_update_spelling_review.py \
  fiscallizeon/exams/tests/views/test_teacher_edit_spelling_review.py \
  fiscallizeon/exams/tests/components/test_exam_preview.py \
  fiscallizeon/core/tests/test_spelling_review_js.py \
  --reuse-db
```

- O teste de JS é pulado se `node` não estiver disponível.
- Para a suíte completa e o gate de cobertura: `./scripts/dev/predeploy.sh --no-tty`.
- Os testes usam `CustomTransactionTestCase` com `databases = '__all__'` e `DATABASE_ROUTER_READ_LIST=['default']` quando tocam réplicas.

### 4.2 Personas dos Testes

| Persona       | Login Cloud Lab            | Uso                                                                                        |
| ------------- | -------------------------- | ------------------------------------------------------------------------------------------ |
| Staff / admin | `cloud.admin@lize.local`   | Acesso irrestrito, útil para inspecionar dados e cadernos sigilosos.                       |
| Coordenação   | `cloud.coord@lize.local`   | Escopo da **prova**: Visualizar caderno, modal Revisar e configurações.                    |
| Professor     | `cloud.teacher@lize.local` | Escopo do **conjunto**: precisa de `has_new_teacher_experience` e ser dono da solicitação. |
| Aluno         | `cloud.student@lize.local` | Deve ser negado em todas as rotas.                                                         |

Senha padrão do Cloud Lab: `lize-cloud-lab` (ou secret `CLOUD_LAB_PASSWORD`).

### 4.3 Fixture/Mixer para Setup Manual

O cenário canônico já existe em `fiscallizeon/exams/tests/spelling_review_fixtures.py` (`SpellingScenarioMixin.build_scenario(block_approval=...)`). Para o Cloud Lab, o caminho mais rápido é criar a sugestão manualmente no shell, sem depender da IA:

```python
# python manage.py shell
from django.utils import timezone
from fiscallizeon.ai.models import SpellingReview, SpellingSuggestion
from fiscallizeon.ai.services.spelling_review.decisions import ignore_key_for
from fiscallizeon.exams.models import Exam, ExamQuestion

exam = Exam.objects.get(pk='<exam_uuid>')
eq = ExamQuestion.objects.filter(exam=exam).first()
question = eq.question

review = SpellingReview.objects.create(
    exam=exam,
    total=1,
    processed=1,
    status=SpellingReview.STATUS_READY,
    finished_at=timezone.now(),
)

SpellingSuggestion.objects.create(
    question=question,
    source_review=review,
    field=SpellingSuggestion.FIELD_ENUNCIATION,
    excerpt='Haviam',
    correction='Havia',
    kind=SpellingSuggestion.KIND_AGREEMENT,
    explanation='Haver no sentido de existir fica no singular.',
    ignore_key=ignore_key_for(
        question.pk, SpellingSuggestion.FIELD_ENUNCIATION, None, 'Haviam', 'Havia'
    ),
)
```

> O trecho **precisa existir** no texto do campo (ex.: enunciado com `Haviam`), senão a sugestão fica `outdated` e não pode ser aplicada.

Para o fluxo real (IA + Celery):

- Garanta a API key do provedor GPT no ambiente e um worker consumindo `celery-priority`.
- Ajuste `SPELLING_REVIEW_CONCURRENCY` se quiser forçar execução serial (útil para observar o polling).
- Para testar falha de IA, use um texto que o provedor rejeite ou derrube o worker; a revisão deve marcar falhas sem perder as sugestões já recebidas.

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Configuração da Funcionalidade [Automatizável ✅]

- [x] A tela **Configurações → Questões** exibe o toggle **"Sugestão ortográfica pendente impede aprovar a questão"**.
- [x] O texto de ajuda contém **"O bloqueio é da questão, nunca do caderno"** e explica que, desligado, a sugestão apenas informa.
- [x] Recém-instalado, o toggle vem **desligado** (`block_approval_with_pending_spelling = False`).
- [x] Ligar o toggle, salvar e recarregar a página mantém o valor ligado.
- [x] Desligar, salvar e recarregar mantém desligado.
- [x] Salvar o toggle não altera os demais campos do formulário.
- [x] A regra vale para o **cliente dono do caderno** (caderno de outro cliente não herda a configuração).

### 5.2 Conjunto — Elaboração do Professor [Automatizável ✅]

Pré-condição: professor dono da solicitação, experiência nova ativa, caderno em elaboração, sem malote/aplicação/respostas.

- [x] A tela `/provas/prova/<uuid>/revisar/` exibe o botão **Ortografia** no header do modal de revisão.
- [x] O painel fecha no **X** e no **ESC**.
- [x] Antes de revisar, o resumo mostra o total de questões e o botão **Revisar a prova**.
- [x] O resumo **não** cria revisão: recarregar a página e reabrir o painel não inicia a IA.
- [x] Clicar em **Revisar a prova** cria a revisão e o progresso **"X de Y questões verificadas"** avança.
- [x] Durante a execução, **Parar** solicita a parada e o botão **Revisar de novo** aparece ao final.
- [x] O cabeçalho de cada grupo mostra **"Questão N"** e a contagem de pendentes.
- [x] **Ir para a questão** posiciona/seleciona a questão correspondente no editor.
- [x] Os pontos âmbar (`data-spelling-dot`) aparecem ao lado do número das questões com pendência.
- [x] O badge do botão do header soma todas as pendências do conjunto.
- [x] **Aplicar** em uma sugestão altera o texto no editor e a sugestão passa para **Aplicada**.
- [x] **Ignorar** remove a pendência e exibe **"Ignorada — não volta nas próximas checagens"**.
- [x] Aplicar/ignorar atualiza badge, pontos e contagens sem recarregar a página.
- [x] **Aplicar todas (n)** pede confirmação com quantidade de sugestões e de questões; **Cancelar** não altera nada.
- [x] **Aplicar todas** aplica apenas as pendentes editáveis; questões travadas permanecem com a sugestão para consulta.
- [x] Aba **Pendentes** mostra só sugestões pendentes; aba **Todas** mantém aplicadas/ignoradas/desatualizadas.
- [x] Sem erros, aparece **"Nenhum erro de ortografia ou concordância encontrado"**.
- [x] Depois de resolver tudo, aparece **"Todas as sugestões foram resolvidas"**.
- [x] Para uma questão que não pode ser editada, **Aplicar** fica desabilitado com tooltip explicativo e **Ignorar** continua disponível.
- [x] Para texto base compartilhado, o aviso informa que a correção vale para todas as questões que usam o texto.
  - OBS.: na listagem de erros o texto base compartilhado por N questões se repete N vezes
- [x] Ao aplicar em texto base compartilhado, todas as questões afetadas refletem a correção.
- [x] Uma sugestão ignorada **não retorna** em uma nova checagem, mesmo que a IA devolva o erro com contexto diferente.

### 5.3 Prova — Visualizar Caderno [Automatizável ✅]

Pré-condição: coordenação com acesso ao caderno e `exams.can_review_questions_exam` para ver o Aprovar.

- [x] O header de `/provas/<pk>/visualizar` exibe o botão **Revisão ortográfica** e o badge total quando há pendências.
- [x] Clicar no botão abre o painel lateral; clicar de novo fecha.
- [x] O painel **não** é modal: não há overlay, o fundo não escurece e o scroll da página não trava.
- [x] **ESC** e o **X** fecham o painel.
- [x] Os números das questões com pendência exibem ponto âmbar (`data-spelling-dot`) e tooltip com a contagem.
- [x] O atalho **"N com sugestão ortográfica"** aparece quando há pendências e filtra as questões ao ser acionado.
- [x] O filtro é alternável (`aria-pressed`) e restaura todas as questões ao desligar.
- [x] **Ir para a questão** rola/seleciona a questão no preview.
- [x] Com a regra da escola desligada, o botão **Aprovar** permanece normal mesmo com pendências.
- [x] Com a regra ligada e pendência na questão, o menu **Aprovar** fica desabilitado (`data-spelling-approve-blocked`) com tooltip **"Aplique ou ignore cada uma para aprovar."**
- [x] Clicar no Aprovar bloqueado não altera o status e leva à revisão ortográfica (painel).
- [x] Aprovar **outra questão** sem pendência continua funcionando (o bloqueio é por questão).
- [x] Aplicar/ignorar uma sugestão remove o ponto, atualiza o badge e libera o Aprovar daquela questão.
- [x] Em questão travada, a sugestão aparece para consulta e **Aplicar** fica desabilitado com tooltip.
- [x] Em texto base compartilhado, o aviso de abrangência aparece e a aplicação vale para todas as questões.

### 5.4 Prova — Modal Revisar, Aba Ortografia [Automatizável ✅]

Pré-condição: `/provas/<pk>/editar/` ou `/provas/<pk>/revisar/`, coordenação com permissão de revisão.

- [x] A barra de abas exibe **Ortografia** com o ícone **A**.
- [x] O badge da aba mostra o número de pendências da questão selecionada.
- [x] A aba lista apenas as sugestões daquela questão.
- [x] Aplicar/ignorar atualiza a lista, o badge e o botão **Aprovar** sem recarregar.
- [x] Com a regra ligada e pendência, a aba **Enunciado** mostra o botão **Aprovar** bloqueado (`data-spelling-approve-blocked`).
- [x] O tooltip do bloqueio informa a quantidade e orienta aplicar/ignorar.
- [x] Clicar no Aprovar bloqueado muda para a aba **Ortografia**.
- [x] Após aplicar/ignorar todas as pendências da questão, o botão **Aprovar** normal volta a aparecer.
- [x] Aprovar outra questão do caderno continua permitido.
- [x] Com a regra desligada, o botão Aprovar nunca é substituído.
- [x] Em questão travada, **Aplicar** fica desabilitado com tooltip e **Ignorar** funciona.

### 5.5 Regras de Sugestão e Estados [Automatizável ✅]

- [x] O resumo não cria `SpellingReview`; a criação só ocorre no `POST`.
- [x] Chamar o resumo sem `exam` nem `ets` retorna 400 com **"Informe a prova ou o conjunto."**
- [x] Sugestão aplicada/ignorada não bloqueia aprovação.
- [x] Aprovar questões nunca revisadas continua permitido.

### 5.6 Permissões e Multi-tenant [Automatizável ✅]

- [x] Professor vê, no escopo da prova, apenas as próprias questões (ou da disciplina quando é coordenador de disciplina / `correction_by_subject`).
- [x] Coordenação vê todas as questões da prova.
- [x] Caderno/revisão/sugestão de outro cliente retorna 404.
- [x] Usuário sem permissão do status atual do caderno recebe 403.

### 5.7 Não-Regressão [Automatizável ✅]

- [x] **Aprimorar questão** na elaboração do professor continua funcionando.
- [x] A **Revisão automática** existente no modal Revisar continua funcionando.
- [x] Aprovar, Visto, Sugerir correção, Falhar e Anular seguem inalterados quando não há pendência ortográfica.
- [x] O modal Revisar continua abrindo e navegando entre questões e abas.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] O painel lateral ocupa a largura correta e não cobre permanentemente o conteúdo; em mobile, ocupa a tela inteira.
- [x] Textos variáveis (nomes de caderno, questão, trecho e correção) usam truncate/quebra adequada e não vazam sob badges.
- [x] Loading e ações em massa exibem feedback imediato (spinner/estado desabilitado); a tela nunca parece inerte.

---

## 7. Bugs and Observations (Problemas Encontrados)

| #   | Severidade | Descrição | Evidência | Status |
| --- | ---------- | --------- | --------- | ------ |
| 1   | —          | —         | —         | —      |

Observações iniciais:

- A branch mistura o ajuste de `analytics/grade_map.html` e a change OpenSpec de alternativas/negrito, que não pertencem à task de revisão ortográfica. Recomenda-se separar antes do merge para não ampliar o escopo de QA.
- Os controles internos do painel não possuem `data-*`/`id` únicos; a automação futura dependerá de texto ou de atributos Alpine. Ver seção 8.1.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

- Adicionar identificadores estáveis (`data-spelling-start`, `data-spelling-apply`, `data-spelling-ignore`, `data-spelling-tab-ortografia`) para Playwright.
- Extrair o painel Alpine e o componente Vue para um único componente compartilhado, reduzindo duplicação de marcação.
- Criar comando de management para gerar sugestões de demonstração no Cloud Lab (sem depender de IA).
- Cobrir o fluxo de polling com teste de integração de browser (hoje a lógica pura é testada em Node).

### 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- Mapeamentos criados nesta task:
  - `docs/tests/usability/exam_preview_redesign.md`
  - `docs/tests/usability/modal_review.md`
  - `docs/tests/usability/exam_request_create_update_new.md`
- Mapeamentos atualizados:
  - `docs/tests/usability/exam_request_teacher_subject_edit_new.md`
  - `docs/tests/usability/questions_configutation.md`

**Snippet de automação (Playwright + setup via backend):**

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.django_db(databases='__all__')
def test_bloqueio_de_aprovacao(page: Page, live_server, scenario):
    # scenario: SpellingScenarioMixin.build_scenario(block_approval=True) + self.suggestion()
    coordinator = scenario.coordinator
    exam = scenario.exam
    eq_id = str(scenario.exam_question.pk)

    page.goto(f'{live_server.url}/provas/{exam.pk}/editar/')
    # login conforme a persona do Cloud Lab (ou force_login no teste)
    page.click('#reviewModal')  # abrir via card do professor no fluxo real
    blocked = page.locator('[data-spelling-approve-blocked]')
    expect(blocked).to_be_visible()
    expect(blocked).to_have_attribute('aria-disabled', 'true')

    page.locator('[data-spelling-review-tab]').wait_for()
    page.get_by_role('button', name='Ignorar').first.click()
    expect(page.locator('[data-spelling-approve-blocked]')).to_have_count(0)
```

> O snippet é um esqueleto: no teste real, use `force_login`/sessão da persona e ajuste o seletor de abertura do modal (`#reviewModal` é o container, não o gatilho).

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante o teste:**
- **Houve idas e voltas com o desenvolvedor?**
- **Como o fluxo de desenvolvimento/QA desta task poderia ter sido melhor?**
- **A ausência de OpenSpec dificultou o entendimento de algum critério?**

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

- A task não tinha OpenSpec; o plano precisou inferir critérios da descrição e dos testes. Vale registrar no prompt a necessidade de marcar explicitamente "sem OpenSpec" e listar as inferências.
- O diff mistura escopos; o prompt pode incluir uma verificação automática de arquivos fora do domínio da task para alertar o QA.

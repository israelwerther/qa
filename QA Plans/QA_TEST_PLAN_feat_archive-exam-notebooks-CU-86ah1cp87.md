# QA Test Plan: Arquivamento de Cadernos de Prova (Archive Exam Notebooks)

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-08-12 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Exams (Cadernos de Prova / Instrumentos Avaliativos) |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐ (4/5) — spec bem detalhada, porém removida do branch no commit `605c41695`; recuperável via `git show 605c41695~1:openspec/changes/archive-exam-notebooks/specs/archive-exam-notebooks/spec.md`. Dois pontos não cobertos pela spec: conformação do aviso de aplicação ativa no arquivamento em massa e a string-truthiness de `confirm`. |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend
- **Modelo `Exam`** (`fiscallizeon/exams/models.py`): novo campo `is_archived = BooleanField(default=False, db_index=True)` + property `has_active_applications` que detecta aplicações vigentes (compara `date`/`date_end`/`end` + 3h com `now`).
- **Migração** `0218_exam_is_archived_historicalexam_is_archived.py`: adiciona `is_archived` em `Exam` e `HistoricalExam`.
- **API** (`fiscallizeon/exams/api/exams.py`): novas actions DRF `archive` e `unarchive` no `ExamCoordinationAndTeacherViewSet` (URLs `POST /provas/api/prova/<pk>/archive/` e `/unarchive/`), restritas a `user_type == 'coordination'`; `archive` exige `confirm` quando há aplicação ativa (retorna `400` com `has_active_applications`).
- **View `ExamListView`** (`fiscallizeon/exams/views/exams.py`): filtro `is_archived` (default `false`) via GET; passa `is_archived` ao contexto.
- **Busca global** (`fiscallizeon/core/apis.py`): o JSON do grupo "Cadernos" agora inclui `"is_archived"` por resultado, e cadernos arquivados **não** são retornados pela busca global (excluídos do grupo "Cadernos").

### Frontend
- **`exam_list_new.html`**: nova aba **"Arquivados"** na barra de tipos; título dinâmico ("Cadernos arquivados"); item "Arquivar caderno"/"Desarquivar caderno" no menu de contexto (somente coordination); dropdown "Remover selecionadas" com opções "Arquivar selecionadas"/"Desarquivar selecionadas" (bulk, coordination); estado vazio diferenciado; novos métodos Vue `archiveAllSelected`/`unarchiveAllSelected` e funções JS `archiveExam`/`executeArchive`/`unarchiveExam` com modais SweetAlert2.
- **Navegação via busca**: cadernos arquivados ficaram **fora** da busca global (não há redirect com `&is_archived=true` — os Cenários 13–15 da seção 5.5 refletem esse comportamento).

### Testes
- **`fiscallizeon/exams/tests/test_exam_archiving.py`** (novo): cobre `is_archived` default, filtragem nativa, archive/unarchive via API, e a exclusão de cadernos arquivados da busca global.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- **IN SCOPE:**
  - Arquivar/desarquivar caderno individual pelo menu de contexto da listagem `/provas/`.
  - Aba/filtro "Arquivados" e manutenção da listagem de ativos (`is_archived=false`).
  - Aviso de confirmação (SweetAlert2) ao arquivar caderno com aplicação em andamento.
  - Ações em massa (seleção) de arquivar/desarquivar.
  - Navegação para caderno arquivado exclusivamente pela aba **"Arquivados"** na listagem `/provas/` (cadernos arquivados ficaram fora da busca global — ver seção 5.5).
  - Preservação do histórico (aplicações, gabaritos, respostas, correções) após arquivamento.
- **OUT OF SCOPE:**
  - Redesign da tela ou migração para `redesign/base_component.html` (mantém `redesign/base.html`).
  - Alterações nos fluxos de elaboração, edição ou correção de provas.
  - Arquivamento automático em lote por rotinas agendadas/cron.
  - Exclusão permanente de cadernos (continua sendo o fluxo "Remover" já existente).
  - Categoria OMR/`gabaritos` — mudanças de busca afetam apenas o grupo "Cadernos".

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View/Rota name |
|---|---|---|---|
| Lista de provas (ativas) | Instrumentos Avaliativos → "Caderno de prova" | `/provas/?category=exam` | `exams:exams_list` |
| Lista de exercícios (ativas) | Instrumentos Avaliativos → "Lista de Exercício" | `/provas/?category=homework` | `exams:exams_list` |
| Cadernos arquivados | Aba **"Arquivados"** na listagem | `/provas/?is_archived=true` | `exams:exams_list` |
| Arquivar caderno (API) | Menu de ações do caderno → "Arquivar caderno" | `POST /provas/api/prova/<uuid>/archive/` | `exams:api-exam-archive` |
| Desarquivar caderno (API) | Menu de ações do caderno → "Desarquivar caderno" | `POST /provas/api/prova/<uuid>/unarchive/` | `exams:api-exam-unarchive` |

> **[verificar]** O item lateral correspondente à listagem de provas (`/provas/?category=exam`) é rotulado **"Instrumentos Avaliativos"** (conforme `KI_Navegacao.md`). Confirme visualmente no perfil de Coordenador.

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

- **Comando (Docker):**
  ```bash
  ./scripts/tests/run-tests.sh --no-tty fiscallizeon/exams/tests/test_exam_archiving.py
  ```
  Se o container `tests` não estiver rodando: `docker compose --profile test up -d tests`.

- **Persona:** **Coordenador de unidade X** com `user_type='coordination'`, vínculo em `SchoolCoordination` via `CoordinationMember`, e permissão `exams.view_exam`. Sem esse perfil (ex.: professor), as ações de arquivar/desarquivar **não** devem aparecer e a API deve retornar `403`.

- **Mixer Setup (para QA manual e automação futura):**
  ```python
  from mixer.backend.django import mixer

  client_obj = mixer.blend(Client, has_exam_elaboration=True)
  unity = mixer.blend(Unity, client=client_obj)
  coordination = mixer.blend(SchoolCoordination, unity=unity)
  user = mixer.blend(
      User,
      two_factor_enabled=False,
      must_change_password=False,
      has_la_place_login=False,
      user_type='coordination',
  )
  mixer.blend(CoordinationMember, user=user, coordination=coordination)
  user.user_permissions.add(
      Permission.objects.get(content_type__app_label='exams', codename='view_exam')
  )
  # login_user(self.client, user)

  ativo = mixer.blend(Exam, is_archived=False, coordinations=[coordination])
  arquivado = mixer.blend(Exam, is_archived=True, coordinations=[coordination])
  ```
  - Para testar o fluxo de **aplicação ativa** (aviso), crie um `Application` cujo `date + end + 3h >= now` (ou `date_end + end + 3h >= now` quando `date_end` especificado).

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

> **Persona ativa:** Coordenador de unidade X (exceto onde indicado).

### 5.1 Filtro Ativos/Arquivados da Listagem [Automatizável ✅]

#### Cenário 1 — A listagem padrão exibe apenas cadernos ativos
- [x] Acessar `/provas/?category=exam` como coordenador.
- [x] Confirmar que o título da página é "Cadernos de prova" e a aba "Caderno de prova" surge destacada.
- [x] Confirmar que nenhum caderno previamente arquivado aparece na listagem.
- [x] Confirmar que não há nenhuma aba destacada simultaneamente (apenas "Caderno de prova" laranja).

#### Cenário 2 — A aba "Arquivados" exibe apenas cadernos arquivados
- [x] Clicar na aba **"Arquivados"** na barra superior da listagem.
- [x] Confirmar que a URL passa a `/provas/?is_archived=true` e o título muda para "Cadernos arquivados".
- [x] Confirmar que apenas cadernos com estado arquivado são exibidos, com suas informações básicas (nome, etapas, status).
- [x] Confirmar que a aba "Arquivados" fica destacada (laranja).

#### Cenário 3 — Alternância entre abas preserva o estado de cada listagem
- [x] Alternar repetidamente entre "Caderno de prova", "Lista de Exercício" e "Arquivados".
- [x] Confirmar que cada aba abre com a visibilidade correta e sem sobreposição de itens de outra aba.

#### Cenário 4 — Estado vazio diferenciado
- [x] Com zero cadernos ativos, confirmar a mensagem "Não há cadernos cadastrados".
- [x] Com zero cadernos arquivados, confirmar a mensagem "Não há cadernos arquivados".

### 5.2 Arquivar/Desarquivar Individual via Menu de Contexto [Automatizável ✅]

#### Cenário 5 — Arquivar caderno ativo sem aplicação em andamento
- [x] No menu de ações (⋮) de um caderno ativo, clicar em **"Arquivar caderno"**.
- [x] Confirmar que **não** aparece o modal de aviso de aplicação em andamento (caderno sem aplicações vigentes).
- [x] Confirmar que o caderno é arquivado e **some imediatamente** da listagem ativa.
- [x] Ir para a aba "Arquivados" e confirmar que o caderno aparece lá.

#### Cenário 6 — Desarquivar caderno arquivado
- [x] Na aba "Arquivados", abrir o menu de ações de um caderno e clicar em **"Desarquivar caderno"**.
- [x] Confirmar o modal SweetAlert2 de confirmação ("Sim, desarquivar").
- [x] Confirmar que o caderno deixa a aba de arquivados e volta à listagem principal de ativos.

#### Cenário 7 — Professor não enxerga ações de arquivamento
- [x] Logar como **professor** (sem permissões de coordenação).
- [x] Confirmar que o menu de contexto **não** exibe "Arquivar caderno"/"Desarquivar caderno" nos cadernos.
- [x] Confirmar que o dropdown em massa **não** exibe "Arquivar selecionadas"/"Desarquivar selecionadas".

### 5.3 Validação de Aplicação Ativa (Aviso de Confirmação) [Apenas Manual 👁]

#### Cenário 8 — Arquivar caderno com aplicação em andamento alerta o coordenador
- [x] Garantir um caderno com pelo menos uma aplicação vigente (prazo aberto e alunos aptos a responder).
- [x] No menu de ações desse caderno, clicar em **"Arquivar caderno"**.
- [x] Confirmar que o modal **"Tem certeza?"** é exibido avisando que há aplicações em andamento (o texto informa que o arquivamento não interrompe as aplicações vigentes).
- [x] Clicar em **Cancelar**: confirmar que o caderno **não** é arquivado e permanece na listagem ativa.
- [x] Repetir clicando em **"Sim, arquivar"**: confirmar que o caderno é arquivado.

#### Cenário 9 — Histórico permanece intacto após arquivamento
- [x] Para um caderno arquivado, acessar diretamente a URL de visualização/preview do caderno.
- [x] Confirmar que aplicações, gabaritos, respostas de alunos, correções e relatórios continuam acessíveis e inalterados.

### 5.4 Ações em Massa (Seleção) [Automatizável ✅]

#### Cenário 10 — Arquivar selecionadas
- [x] Selecionar 2+ cadernos ativos via checkbox das linhas (e via checkbox do header "selecionar tudo").
- [x] Clicar no dropdown **"Remover selecionadas"** e escolher **"Arquivar selecionadas"**.
- [x] Confirmar o SweetAlert2 e o arquivamento em lote: os cadernos somem da listagem ativa e passam a constar em "Arquivados".

#### Cenário 11 — Desarquivar selecionadas
- [x] Na aba "Arquivados", selecionar 2+ cadernos e escolher **"Desarquivar selecionadas"**.
- [x] Confirmar que os cadernos voltam à listagem principal de ativos.

#### Cenário 12 — Ações em massa ficam ocultas sem seleção (seleção vazia)
> **Nota de QA:** O dropdown "Remover selecionadas" (com "Arquivar selecionadas"/"Desarquivar selecionadas") só existe na barra de ações em massa, que é renderizada condicionalmente (`v-if="selectionList.length > 0"` no template). Com **nenhum item selecionado, a ação não aparece** — logo não há fluxo de UI de "arquivar com seleção vazia" para testar. O guard `if (selectionList.length > 0)` + alerta "Não há cadernos selecionados." nos métodos JS é defesa em profundidade, inalcançável pela interface.
- [x] Sem nenhum checkbox marcado, confirmar que a barra de ações em massa (e o dropdown "Remover selecionadas" com suas opções de arquivamento) **não é renderizada**.
- [x] Marcar um item e desmarcar todos (incluindo desmarcar o "selecionar tudo"): confirmar que a barra desaparece imediatamente ao esvaziar a seleção.
- [x] Confirmar que, com a barra oculta, não há como disparar "Arquivar selecionadas"/"Desarquivar selecionadas" com seleção vazia pela UI.

### 5.5 Busca Global e Cadernos Arquivados [Automatizável ✅]

> **Nota de QA:** A busca global **não** retorna mais resultados de cadernos arquivados — o grupo "Cadernos" passou a excluir `is_archived=true`. Logo, não existe fluxo de UI de "abrir caderno arquivado via busca" para testar; os Cenários 13–15 originais deixaram de se aplicar.

#### Cenário 13 — Busca global não exibe cadernos arquivados
- [x] Logado como coordenador, digitar o nome de um caderno arquivado na barra de busca do topo.
- [x] Confirmar que **nenhum** resultado do grupo "Cadernos" retorna o caderno arquivado.
- [x] Confirmar que cadernos **ativos** continuam retornando normalmente na busca.

#### Cenário 14 — Busca de caderno ativo não força a aba arquivada
- [x] Buscar um caderno **ativo** e clicar no resultado.
- [x] Confirmar que a URL **não** contém `is_archived=true` e que a aba ativa correspondente fica destacada.

#### Cenário 15 — Busca em outros ambientes (teacher, analytics, escola, componente Alpine)
- [x] Repetir o Cenário 13 logado como **professor** (dashboard `teacher_v2`) e em páginas com a busca do Analytics, do dashboard de Escola e do componente de busca novo (Alpine).
- [x] Confirmar o mesmo comportamento: cadernos arquivados não aparecem em nenhum ambiente de busca.

### 5.6 Segurança e Permissões [Automatizável ✅]

#### Cenário 16 — API rejeita não-coordenador
- [x] Como professor/outro perfil, disparar `POST /provas/api/prova/<uuid>/archive/` (Insomnia/DevTools).
- [x] Confirmar resposta `403` com mensagem "Apenas coordenadores podem arquivar cadernos." e que o `is_archived` **não** muda.
- [x] Repetir para `unarchive`.

#### Cenário 17 — Usuário sem permissão não acessa a listagem
- [x] Logar como usuário **sem** `exams.view_exam` e acessar `/provas/?category=exam`.
- [x] Confirmar bloqueio/redirecionamento coerente (sem listagem vazia indevida).

### 5.7 Caderno Arquivado no Seletor de Cadernos da Aplicação [Automatizável ✅]

> **Nota de QA:** O seletor/busca de cadernos do fluxo de criação/edição de aplicação (`search-exams-component` → endpoints `exams_api_list` / `exams_template_api_list`) **exclui** cadernos arquivados (`is_archived=False` em `ExamListView`/`ExamTemplateListView`, conforme `AJUSTES_CADERNOS_ARQUIVADOS.md` ETAPA 2). Cadernos arquivados **não** podem ser vinculados a novas aplicações.

#### Cenário 18 — Caderno arquivado NÃO retorna na busca de cadernos para uso na aplicação
- [x] Acessar o fluxo de aplicação (criação/edição) e abrir a busca de cadernos para serem usados na aplicação.
- [x] Buscar por um caderno previamente arquivado.
- [x] Confirmar que o caderno arquivado **não aparece** nos resultados da busca de cadernos disponíveis para uso na aplicação.
- [x] Confirmar que cadernos **ativos** continuam retornando normalmente e podem ser selecionados/vincuados à aplicação.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] A nova aba **"Arquivados"** respeita o padrão visual das demais abas (mesma tipografia/estado laranja quando ativa) e o header de tipos continua legível sem quebrar linha.
- [x] Ícones e itens "Arquivar caderno"/"Desarquivar caderno" no menu de contexto seguem o padrão dos demais itens (ícone + texto, hover corrigo, alinhamento, role `menuitem`).
- [x] O dropdown "Remover selecionadas" agora em cascata (com subitens) renderiza alinhado e não sobrepõe os demais botões da barra de seleção ("Alterar situação", "Alterar prazos").
- [x] Modais SweetAlert2 de arquivar/desarquivar (individual e em massa) exibem título, texto e botões coerentes.
- [x] Estado vazio "Não há cadernos arquivados" segue o mesmo estilo do estado vazio atual.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!BUG]
> **[Backend Logic] Guarda de confirmação de aplicação ativa é "truthy" — `confirm=false` contorna o aviso.**
> **Contexto:** Na action `archive`, `confirm = request.data.get('confirm')` retorna a string `"false"` quando o cliente envia `confirm=false` (form-urlencoded, ex. via `$.post`). Como `not "false"` é `False`, o backend efetiva o arquivamento mesmo havendo aplicação em andamento, sem devolver o `400` de aviso.
> **Comportamento esperado:** `(conforme OpenSpec: spec.md — "Aviso de confirmação ao arquivar caderno com aplicação ativa ... sistema DEVE exibir um aviso de confirmação antes de concluir a ação"). Um `confirm=false` explícito deve ser tratado como NÃO confirmação e o arquivamento deve ser bloqueado/avisado.
> **Workaround (Gambiarra temporária):** Para QA manual, o fluxo de UI passa `confirm` correto (`true` quando confirmado), portanto não bloqueia a execução do plano. Se precisar validar o aviso via API, envie a chamada **sem** o campo `confirm` (não `confirm=false`).

> [!WARNING]
> **[Spec Gap] Arquivo em massa não dispara o aviso específico de aplicação ativa.**
> **Contexto:** `archiveAllSelected` envia `{ confirm: true }` para todos os itens (via `axios.post`), efetivando o arquivamento sem a verificação individual de aplicações vigentes. O único alerta é o SweetAlert2 genérico que menciona genericamente as aplicações ativas.
> **Comportamento esperado:** A spec (item "Aviso de confirmação ao arquivar caderno com aplicação ativa") parece desenhada para a ação individual; no em massa a especificação é silenciosa — decida com o PO se o aviso individual deve ser emitido ou se o texto genérico do bulk é aceitável.

> [!NOTE]
> **[Backend Logic / Perf] `has_active_applications` é property avaliada por caderno na listagem (N+1).**
> **Contexto:** `{{ exam.has_active_applications|yesno:'true,false' }}` executa uma sub-consulta agregada por linha na template. Em listagens grandes há custo perceptível.
> **Comportamento esperado:** `(inferência de UX — Spec Gap)`. Idealmente virar anotação com `Exists(Application...)` no queryset da `ExamListView` (padrão já usado no mesmo queryset para `_has_questions_created_with_ia`).
> **Workaround:** Nenhum bloqueio funcional; apenas performance.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> Remover `TESTE_BUSCA_ARQUIVADOS.md` da raiz do repositório (documento de teste/guia manual desenvolvido durante o desenvolvimento, não é artefato de produção). Se útil, migrar o conteúdo para o Acervo (`docs/tests/usability/exam_list_new.md`).

> [!NOTE]
> Aportar em `has_active_applications` como anotação no queryset (eliminar N+1) antes de escalar a lista.

> [!NOTE]
> Avaliar semântica da aba "Arquivados" sem `category`: hoje `/provas/?is_archived=true` agrega cadernos das duas categorias (prova + lista), enquanto os títulos das abas "Caderno de prova"/"Lista de Exercício" são explícitos por categoria. Confirmar se o comportamento desejado é um agregado único ou um arquivado por categoria.

> [!NOTE]
> Adicionar `id` ou data-attribute estáveis aos novos botões/menus ("Arquivar caderno", "Arquivar selecionadas", aba "Arquivados") para automação Playwright sem depender das classes Tailwind (`tw-*`).

> [!NOTE]
> [Scope Gap] Não há uma coluna/ícone visual na listagem indicando que um caderno está arquivado além do contexto da própria aba — em futuras telas que listam cadernos sem o filtro, pode ser útil um badge "Arquivado".

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.
🔗 **[Ver Mapeamento de Tela](../../docs/tests/usability/exam_list_new.md)**

**Automation Snippet (UI + Data Setup) — arquivar caderno individual:**

```python
# setup: idêntico ao mixer descrito na Seção 4 (coordination + view_exam + Exam ativo)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    # login (sessão do coordenador via cookies/force_login no próprio pytest, se aplicável)
    page.goto("http://127.0.0.1:8000/provas/?category=exam")
    page.click(f'button#dropdownMenuButton-{ativo.pk}')  # abrir menu de contexto da linha
    page.click('a:has-text("Arquivar caderno")')
    # sem aplicação ativa: não deve haver SweetAlert; validar remoção da linha e reload
    page.wait_for_url("**/provas/?category=exam")
    page.wait_for_selector(f'tr#tr-{ativo.pk}', state="detached")

    # aba arquivados agora contém o caderno
    page.click('ul[data-tg-title="Tipos de instrumentos"] a:has-text("Arquivados")')
    page.wait_for_selector(f'tr#tr-{ativo.pk}')

    # desarquivar via menu de contexto na aba arquivados
    page.click(f'button#dropdownMenuButton-{ativo.pk}')
    page.click('a:has-text("Desarquivar caderno")')
    page.locator('.swal2-confirm').click()  # SweetAlert "Sim, desarquivar"
    page.wait_for_selector(f'tr#tr-{ativo.pk}', state="detached")
    browser.close()
```

> **Atenção à permissão:** o shell/Playwright que executar o fluxo precisa do usuário com `user_type='coordination'` e `is_superuser=True` (ou `exams.view_exam`) para que a listagem e os itens do menu sejam renderizados — senão `archiveExam`/`unarchiveExam` nem existem no DOM.

**API Routes críticas:** `POST /provas/api/prova/<uuid>/archive/` (body `{confirm}`), `POST /provas/api/prova/<uuid>/unarchive/`, `GET /api/v1/search/?q=<termo>` (campo `is_archived` no grupo "Cadernos").

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante os testes:**
  - *(placeholder)*
- **Back-and-forths com o desenvolvedor:**
  - *(placeholder)*
- **Melhorias de processo/desenvolvimento:**
  - *(placeholder — ex.: a spec foi removida do branch; sugerir manter `spec.md` até o release, ou versionar no Acervo)*

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
<!--
- Quando a OpenSpec não está mais presente no branch (ex.: commit de "chore: remove ... specification"), o Prompt V2 deveria instruir explicitamente a recuperação via `git show <commit>~1:path`, evitando QA sem fonte.
- Para hardening de endpoints com flag booleana vinda do cliente, incluir no plano um caso de teste "string-truthy" (ex.: `confirm=false`) — a atual guarda no backend falha nesse edge.
- Em modais/validações condicionais (ex.: aviso de aplicação ativa), distinguir claramente "sem aplicação" vs "aplicação vigente" nos cenários manuais para reduzir falso-positivos de QA.
-->

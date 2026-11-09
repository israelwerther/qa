## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-11-05 |
| **Branch:** | `feat/texto-base-compartilhado-questoes-embaixo-CU-86akta6jf` |
| **ClickUp:** | [Texto-base compartilhado com questões embaixo](https://app.clickup.com/t/86akta6jf) (`86akta6jf`) |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Elaboração de cadernos / Impressão e diagramação / Malote / Lista de exercício |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐ (proposal, design, spec e tasks completos; `references/README.md` cita `references/texto_base_compartilhado.html`, mas o arquivo não existe no change) |

## 1. Summary of Changes (Resumo das Alterações)

- **Backend — modelo e choices (`fiscallizeon/exams/models.py` + migration `0221_alter_exam_base_text_location_and_more.py`):**
  - `Exam.PER_QUESTION, SUBJECT_TOP, EXAM_TOP, EXAM_BOTTOM, SHARED_BELOW = range(5)`.
  - Novo choice `SHARED_BELOW = 4` com rótulo `'Texto-base compartilhado com questões embaixo'`.
  - Valores `0`, `1`, `2` e `3` preservados integralmente.
- **Backend — serializers/API:**
  - `ExamCoordinationAndTeacherViewSet` (basename `api-exam`) expõe `base_text_location` via serializer (`fiscallizeon/exams/serializers/exams.py:614`).
  - Exportação de choices em `views/exams.py` usa `Exam.BASE_TEXT_LOCATION_CHOICES`, portanto já inclui a 5ª opção.
- **Frontend — tela de coordenação (`exam_request_create_update_new.html`):**
  - 5º radio em `#collapseAdvanced` (“Configurações adicionais”) com `id_shared_below`, `value="4"`, label **“Texto compartilhado com questões embaixo”**.
  - Reorganização ampla da seção de configurações avançadas nos commits `e3988ddb2` e `2657c7259` (textos base, inputs/seleções, switches e orientações), incluindo correção de alinhamento dos switches Bootstrap.
- **Frontend — tela do professor (`exam_teacher_create_update.html`, versão legada):**
  - 5º botão/radio `id_shared_below`, `value="4"`, no grupo “Onde serão mostrados os textos base?”.
  - **Atenção:** a navegação real do professor usa `?v=2`, que renderiza `exam_teacher_create_update_v2.html`; esse template não contém `base_text_location` nem a 5ª opção. Ver Seção 7.
- **Renderização — novo include (`includes/base_texts/shared_below.html`):**
  - Renderiza o texto-base uma única vez, antes da primeira questão vinculada, usando `question.number == getTheLowestNumber(questions, baseText)`.
  - Corpo do texto antes do rodapé `.text-base-questions-footer` com **“(Texto para as questões X e Y)”** ou **“(Texto para a questão X)”**.
  - IDs `#baseText_<id>` e atributo `data-baseText="baseText_<id>"`.
- **Renderização — integração e supressão do aviso residual:**
  - `not_separate.html`, `separate_subjects.html`, `separate_category.html` (3 seções), `exam_preview.html` e `exam_homework_print.html` incluem `shared_below.html` quando o display do choice é `'Texto-base compartilhado com questões embaixo'`.
  - `text_relation.html` (“Esta questão possui X texto(s) base...”) é suprimido para a opção 4.
- **Impressão/malote:**
  - `exam_print.html` (usado por **Imprimir caderno** e pelo PDF de malote em `print_mockup_exam`) passa a renderizar a nova opção.
  - `exam-print-v2` (“Diagramar caderno”) **não foi alterado** nesta branch.
- **Testes automatizados:**
  - `fiscallizeon/exams/tests/test_exam_shared_base_text_below.py` cobre choice, persistência, retrocompatibilidade 0–3 e asserts de estrutura/condicionais dos templates.
  - Não há teste que renderize o PDF real nem que cubra a versão randomizada.
  - Verificação local em 2026-11-05: `9 passed` no container `web` com `docker compose exec --no-tty web pytest fiscallizeon/exams/tests/test_exam_shared_base_text_below.py --reuse-db -q`. O `.venv` local está sem o pacote `pytest`.

## 2. Scope Boundaries (Diferenças de Escopo)

- **IN SCOPE:** persistir e recuperar `base_text_location=4` em `Exam`.
- **IN SCOPE:** exibir a 5ª opção na tela de criação/edição de caderno da coordenação.
- **IN SCOPE:** exibir a 5ª opção na versão legada da tela do professor (`exam_teacher_create_update.html`, URL sem `?v=2`).
- **IN SCOPE:** imprimir o texto-base uma única vez antes da primeira questão vinculada, com a indicação das questões **abaixo** do corpo do texto.
- **IN SCOPE:** não repetir o corpo do texto nas questões seguintes e não exibir o aviso residual `text_relation.html`.
- **IN SCOPE:** layouts **Caderno Único** (`not_separate.html`), **Caderno por Disciplina** (`separate_subjects.html`) e **Caderno por tipo de questão** (`separate_category.html`).
- **IN SCOPE:** preview fiscal (`exam_preview.html`, rota `/provas/<pk>/visualizar/fiscal`).
- **IN SCOPE:** impressão de lista de exercício do aluno (`exam_homework_print.html`).
- **IN SCOPE:** PDF de malote de ensalamento que inclui cadernos de prova (`print_mockup_exam` → `exam_print.html`).
- **IN SCOPE:** regressão visual/smoke das configurações avançadas reorganizadas na tela de coordenação.
- **OUT OF SCOPE:** “Diagramar caderno” v2 (`/provas/<pk>/v2/imprimir/`, `exam-print-v2`) — a branch não altera esse fluxo.
- **OUT OF SCOPE:** preview simples (`/provas/<pk>/visualizar/simples`, `exam_preview_simple.html`) — não modificado.
- **OUT OF SCOPE:** `/provas/<pk>/visualizar` (conteúdo redesign `exam_preview_redesign_content.html`) — não renderiza textos-base.
- **OUT OF SCOPE:** prova online/SPA do aluno, exportações OMR e leitura de cartões.
- **OUT OF SCOPE:** alterar comportamento visual ou de posicionamento das opções legadas `0`, `1`, `2` e `3`.
- **OUT OF SCOPE:** alterar o serviço externo de geração de PDF.
- **SPEC GAP CONHECIDO:** a tela real do professor (`?v=2`) não expõe `base_text_location`; a branch altera apenas o template legado.
- **SPEC GAP CONHECIDO:** “Diagramar caderno” v2 é uma superfície de diagramação ativa e não foi adaptada.
- **SPEC GAP CONHECIDO:** o comportamento de um texto-base compartilhado entre disciplinas diferentes não está definido na spec.
- **SPEC GAP CONHECIDO:** a versão randomizada não fornece `number` no `exam_data.js`; a condição de renderização única pode falhar. Ver Seção 7.

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Lista de cadernos | Menu lateral → **“Instrumentos Avaliativos”** → **“Caderno de prova”** | `/provas/?category=exam` | `exams:exams_list` (`exams_list`) |
| Criar caderno (coordenação) | Botão **“Solicite questões a professores”** | `/provas/cadastrar/?category=exam` | `exams:exams_create` (`ExamCreateView`) |
| Editar caderno (coordenação) | Linha do caderno → **“Opções”** → **“Editar caderno”** | `/provas/<uuid>/editar/` | `exams:exams_update` (`ExamUpdateView`) |
| Configurações avançadas | Card **“Configurações adicionais”** (accordion) | mesma URL de criar/editar | — |
| Criar lista de exercício (professor, real) | Menu do professor → **“Criar lista de exercício”** / lista → **“Criar Lista de Exercício”** | `/provas/prova/professor/?v=2&category=homework` | `exams:exam_teacher_create` (`ExamTeacherCreateUpdateTemplateView`) |
| Criar lista de exercício (professor, legado) | URL direta sem `?v=2` | `/provas/prova/professor/` | `exams:exam_teacher_create` |
| Editar lista de exercício (professor, real) | Linha da lista → **“Opções”** → **“Editar”** | `/provas/prova/professor/<uuid>/?v=2` | `exams:exam_teacher_update` |
| Editar lista de exercício (professor, legado) | URL direta sem `?v=2` | `/provas/prova/professor/<uuid>/` | `exams:exam_teacher_update` |
| Imprimir caderno | Linha do caderno → **“Opções”** → seção **“Impressão”** → **“Imprimir caderno”** | `/provas/<uuid>/imprimir` | `exams:exam_print` (`ExamPrintView`) |
| Diagramar caderno (v2) | Linha do caderno → **“Opções”** → **“Diagramar caderno”** | `/provas/<uuid>/v2/imprimir/` | `exams:exam-print-v2` (`ExamPrintV2View`) |
| Preview fiscal | Ação de visualização do caderno [verificar rótulo exato] | `/provas/<uuid>/visualizar/fiscal` | `exams:exams_inspector_preview` (`ExamInspectorPreviewView`) |
| Preview simples (não alterado) | — | `/provas/<uuid>/visualizar/simples` | `exams:exams_preview_simple` (`ExamPreviewSimpleView`) |
| Impressão de lista de exercício | Lista de aplicações do aluno/responsável → **“Imprimir Caderno”** | `/provas/<uuid>/<application_student>/imprimir/lista-exercicio` | `exams:exam_homework_print` (`ExamHomeworkPrintView`) |
| Malote de ensalamento | Menu lateral → **“Aplicações”** → **“Ensalamento”** → **“Opções”** → **“Imprimir malote”** / **“Baixar malote”** | `/ensalamento/` + `POST /ensalamento/api/ensalamentos/<uuid>/gerar-malote/` | `distribution:distribution_list` / `distribution:export_distribution_exams_bag` |
| Criar/editar questão e vincular texto-base | **“Editar — versão nova”** / `/questoes/cadastrar/?v=redesign` | `/questoes/cadastrar/?v=redesign`, `/questoes/<uuid>/editar/?v=redesign` | `questions:questions_create` / `questions:questions_update` |

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

**Personas:**
- **Coordenação:** usuário `user_type='coordination'`, membro de `SchoolCoordination` do `Client`, com `exams.add_exam`, `exams.change_exam`, `exams.view_exam` e `exams.can_print_exam`.
- **Professor:** usuário `user_type='teacher'`, `Inspector` com `can_elaborate_questions`, `client_teachers_can_elaborate_exam=True` e permissão `inspectors.can_add_exercice_list`; o caderno deve ser `Exam.HOMEWORK` criado pelo próprio professor.
- **Aluno/responsável:** para a impressão de lista de exercício, `ApplicationStudent` do aluno com `application.category=4` (`HOMEWORK`), `date_time_start_tz` já iniciada e `end_time` preenchido.

**Comandos (Cloud Lab / venv local):**

```bash
source .venv/bin/activate && pytest fiscallizeon/exams/tests/test_exam_shared_base_text_below.py --reuse-db
```

**Com Docker (fluxo de PR):**

```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/exams/tests/test_exam_shared_base_text_below.py
```

**Setup de dados (mixer) — caderno com texto compartilhado entre as questões 4 e 5:**

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.classes.models import Grade
from fiscallizeon.clients.models import (
    Client, CoordinationMember, SchoolCoordination, Unity,
)
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject
from fiscallizeon.inspectors.models import Inspector, TeacherSubject
from fiscallizeon.questions.models import BaseText, Question, QuestionOption

client_obj = mixer.blend(
    Client,
    has_exam_elaboration=True,
    has_distribution=True,
    two_factor_enabled=False,
)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
coordinator = mixer.blend(
    User,
    user_type='coordination',
    two_factor_enabled=False,
    must_change_password=False,
)
mixer.blend(CoordinationMember, user=coordinator, coordination=coordination)
coordinator.user_permissions.add(
    Permission.objects.get(content_type__app_label='exams', codename='add_exam'),
    Permission.objects.get(content_type__app_label='exams', codename='change_exam'),
    Permission.objects.get(content_type__app_label='exams', codename='view_exam'),
    Permission.objects.get(content_type__app_label='exams', codename='can_print_exam'),
)

teacher = mixer.blend(Inspector, coordinations=[coordination])
teacher_subject = mixer.blend(TeacherSubject, teacher=teacher)
grade = mixer.blend(Grade)
exam = mixer.blend(
    Exam,
    coordinations=[coordination],
    base_text_location=Exam.SHARED_BELOW,
    start_number=1,
    is_printed=False,
)
exam_teacher_subject = mixer.blend(
    ExamTeacherSubject,
    exam=exam,
    teacher_subject=teacher_subject,
    grade=grade,
    order=0,
)

base_text = mixer.blend(
    BaseText,
    title='Texto compartilhado QA',
    text='<p>Leia o trecho a seguir para responder às questões 4 e 5.</p>',
    created_by=coordinator,
)

questions = []
for number in range(1, 6):
    question = mixer.blend(
        Question,
        category=Question.CHOICE,
        enunciation=f'<p>Enunciado da questão {number}.</p>',
        created_by=coordinator,
    )
    for index in range(4):
        mixer.blend(
            QuestionOption,
            question=question,
            text=f'Alternativa {index + 1}',
            is_correct=(index == 0),
            index=index,
        )
    mixer.blend(
        ExamQuestion,
        exam=exam,
        exam_teacher_subject=exam_teacher_subject,
        question=question,
        order=number - 1,
    )
    questions.append(question)

questions[3].base_texts.add(base_text)  # Questão 4
questions[4].base_texts.add(base_text)  # Questão 5
```

**Para o malote de ensalamento:** reutilizar o setup de `.ai_qa_acervo/docs/tests/usability/distribution_list.md`, trocando o caderno por `base_text_location=Exam.SHARED_BELOW` e vinculando o mesmo `BaseText` a duas questões. É necessário `Client.has_distribution=True`, `RoomDistribution` com sala/alunos e `Application` presencial.

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona ativa:** coordenação do `Client` dono do caderno, exceto nos cenários 3–4 (professor) e 10 (aluno/responsável).

### 5.1 Cadastro/edição de caderno — coordenação [Automatizável ✅]

#### Cenário 1 — 5ª opção aparece, é selecionável e persiste

**Ação humana:**
- [x] Entrar como coordenação e abrir **“Instrumentos Avaliativos”** → **“Caderno de prova”**.
- [x] Clicar em **“Solicite questões a professores”** (ou abrir **“Opções”** → **“Editar caderno”** em um caderno existente).
- [x] Expandir o card **“Configurações adicionais”**.
- [x] Confirmar que a pergunta **“Onde serão mostrados os textos base?”** exibe **5** opções: **“Por questão”**, **“Por disciplina”**, **“Início do caderno”**, **“Final do caderno”** e **“Texto compartilhado com questões embaixo”**.
- [x] Marcar **“Texto compartilhado com questões embaixo”** e salvar por **“Salvar e continuar”** ou **“Salvar e finalizar”**.
- [x] Reabrir o caderno em **“Editar caderno”**, expandir **“Configurações adicionais”** e confirmar que a 5ª opção continua marcada.
- [x] Inspecionar a resposta da API de detalhe do caderno e confirmar `base_text_location: 4`.

**Referência técnica (para automação):**
- URL: `/provas/cadastrar/?category=exam` ou `/provas/<uuid>/editar/`
- Seletor: `#id_shared_below` (`input[type="radio"][value="4"]`) e labels `label[for="id_per_question"]`, `label[for="id_exam_top"]`, `label[for="id_subject_top"]`, `label[for="id_subject_bottom"]`, `label[for="id_shared_below"]`
- Estado esperado: `v-model="exam.base_text_location"` = `4`; `input#id_shared_below:checked`
- Fixture: `mixer.blend(Exam, base_text_location=Exam.SHARED_BELOW, coordinations=[coordination])`

#### Cenário 2 — Opções legadas 0–3 permanecem intactas

**Ação humana:**
- [x] Na mesma seção, marcar **“Por questão”**, salvar e reabrir; confirmar que continua **“Por questão”**.
- [x] Repetir para **“Por disciplina”**, **“Início do caderno”** e **“Final do caderno”**.
- [x] Em cada opção, conferir que os demais campos de **“Configurações adicionais”** continuam visíveis e operáveis.
- [x] Abrir a impressão de um caderno legado e confirmar que o comportamento visual anterior foi mantido (sem bloco novo de texto compartilhado).

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/editar/`
- Seletor: `input[name="base_text_location"]`
- Estado esperado: valores `0`, `1`, `2`, `3` preservados; labels e displays legados inalterados
- Fixture: `mixer.blend(Exam, base_text_location=<0|1|2|3>)`

### 5.2 Elaboração de lista de exercício — professor [Apenas Manual 👁]

#### Cenário 3 — Tela real do professor (`?v=2`) versus fallback legado

**Ação humana:**
- [x] Entrar como professor e abrir **“Criar lista de exercício”** pelo menu/lista (a URL real inclui `?v=2`).
- [ ] Localizar a seção **“Onde serão mostrados os textos base?”** e verificar se a 5ª opção **“Texto compartilhado com questões embaixo”** está presente.
- [x] Registrar o resultado: na versão `?v=2` atual, essa seção **não existe**; portanto a opção não está disponível no fluxo real do professor.
- [x] Abrir diretamente `/provas/prova/professor/` **sem** `?v=2` e confirmar que a versão legada exibe os 5 botões/rádios.
- [x] Na versão legada, marcar a 5ª opção, salvar por **“Salvar Parcialmente”** ou **“Salvar e criar aplicação”**, reabrir e confirmar a persistência.
- [ ] Abrir a lista criada em **“Opções”** → **“Editar”** e confirmar se o fluxo real (`?v=2`) mantém o valor salvo (mesmo sem exibir o controle).

**Referência técnica (para automação):**
- URL real: `/provas/prova/professor/?v=2&category=homework`
- URL legada: `/provas/prova/professor/`
- Template real: `dashboard/exams/exam_create/exam_teacher_create_update_v2.html` (sem `base_text_location`)
- Template legado: `dashboard/exams/exam_create/exam_teacher_create_update.html` (com `#id_shared_below`, `value="4"`)
- Seletor legado: `#id_shared_below`, labels `label[for="id_shared_below"]`
- Fixture: `Exam(category=Exam.HOMEWORK, created_by=teacher_user)`, `Inspector(can_elaborate_questions=True)`, `client_teachers_can_elaborate_exam=True`

### 5.3 Impressão do caderno — “Imprimir caderno” [Automatizável ✅]

#### Cenário 4 — Texto único antes da questão 4, rodapé abaixo e sem repetição na questão 5

**Ação humana:**
- [x] Entrar como coordenação e abrir **“Instrumentos Avaliativos”** → **“Caderno de prova”**.
- [x] Em um caderno **não impresso** com `base_text_location=4` e o mesmo texto-base vinculado às questões 4 e 5, abrir **“Opções”** → **“Impressão”** → **“Imprimir caderno”**.
- [x] No modal **“Configure a impressão”**, manter **“Caderno Único”** e clicar em **“Imprimir prova”**.
- [x] No PDF, confirmar que o título e o corpo do texto-base aparecem **uma única vez**, imediatamente antes do enunciado da questão 4.
- [x] Confirmar que a indicação **“(Texto para as questões 4 e 5)”** aparece **abaixo** do corpo do texto e **acima** do enunciado da questão 4.
- [x] Confirmar que a questão 5 **não repete** o texto-base.
- [x] Confirmar que nem a questão 4 nem a questão 5 exibem o aviso **“Esta questão possui 1 texto(s) base...”**.

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/imprimir` (GET, `target="_blank"`)
- Modal: `#configurePrintModal`, formulário `#configure_print_form_id`, botão `button[type="submit"]:has-text("Imprimir prova")`
- Seletores no HTML/PDF: `#baseText_<base_text_id>`, `[data-baseText="baseText_<base_text_id>"]`, `.text-base-questions-footer`
- Estado esperado: um único `#baseText_<id>` no documento; rodapé com “Texto para as questões 4 e 5”; ausência de “Esta questão possui”
- Fixture: questões 4 e 5 com `base_texts.add(base_text)`; `Exam.base_text_location=Exam.SHARED_BELOW`

#### Cenário 5 — Variantes de layout: único, por disciplina e por tipo de questão

**Ação humana:**
- [x] Repetir o cenário 4 escolhendo **“Caderno por Disciplina”** no modal.
- [x] Confirmar que o texto-base aparece uma única vez antes da primeira questão vinculada, dentro da disciplina correta, com o rodapé abaixo.
- [x] Repetir escolhendo **“Caderno por tipo de questão”** e confirmar o mesmo comportamento na seção de questões objetivas.
- [x] Confirmar que, nas três variantes, as questões seguintes não repetem o texto e não exibem o aviso residual.

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/imprimir?separate_subjects=0|1|2`
- Seletor: radios `input[name="separate_subjects"]` (`#separate_subjects_default`, `#separate_subjects_enem`, `#separate_by_question_type`)
- Templates: `includes/exam/not_separate.html`, `includes/exam/separate_subjects.html`, `includes/exam/separate_category.html`
- Estado esperado: `shared_below.html` incluído em cada seção; `text_relation.html` suprimido
- Fixture: o mesmo caderno do cenário 4

### 5.4 Malote de ensalamento [Automatizável ✅]

#### Cenário 6 — Malote com “Incluir cadernos de prova” respeita a opção 4

**Ação humana:**
- [x] Entrar como coordenação e abrir **“Aplicações”** → **“Ensalamento”** (`/ensalamento/`).
- [x] Em um ensalamento com aplicação presencial e caderno `base_text_location=4`, abrir **“Opções”** → **“Imprimir malote”** (ou **“Imprimir malote novamente”**).
- [x] No modal **“Configure a impressão do malote nesta exportação”**, confirmar que **“Incluir cadernos de prova”** está marcado.
- [x] Clicar em **“Imprimir malote”** e aguardar a geração do PDF.
- [x] No PDF do malote, localizar o caderno e confirmar o texto-base uma única vez antes da questão 4, com **“(Texto para as questões 4 e 5)”** abaixo do texto.
- [x] Confirmar que a questão 5 não repete o texto e que o aviso **“Esta questão possui...”** não aparece.

**Referência técnica (para automação):**
- URL: `/ensalamento/` + `POST /ensalamento/api/ensalamentos/<uuid>/gerar-malote/`
- Seletor: `#configurePrintModal`, `#print-exam` (`v-model="includeExams"`), botão `#configurePrintModal button:has-text("Imprimir malote")`
- Estado esperado: `include_exams=true`; PDF gerado por `print_mockup_exam` com `template_name='dashboard/exams/exam_print.html'`
- Fixture: `RoomDistribution` + `RoomDistributionStudent` + `Application` presencial + `Exam(base_text_location=4)`

### 5.5 Preview fiscal e lista de exercício [Automatizável ✅ / Apenas Manual 👁]

#### Cenário 7 — Preview fiscal renderiza o texto compartilhado [Automatizável ✅]

**Ação humana:**
- [x] Como coordenação, abrir o caderno com opção 4 e acessar a visualização de fiscal (`/provas/<uuid>/visualizar/fiscal`).
- [x] Confirmar que o texto-base aparece uma única vez antes da questão 4, com o rodapé de indicação abaixo.
- [x] Confirmar que a questão 5 não repete o texto e que o aviso residual não aparece.

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/visualizar/fiscal`
- Seletor: `#baseText_<id>`, `.text-base-questions-footer`
- Estado esperado: mesmo HTML de `exam_preview.html` com `preview_mode="inspector"`
- Fixture: caderno do cenário 4; permissões `COORDINATION`/`TEACHER`/`INSPECTOR`

#### Cenário 8 — Impressão da lista de exercício do aluno [Apenas Manual 👁]

**Ação humana:**
- [x] Criar uma lista de exercício (`Exam.HOMEWORK`) com opção 4 e texto-base compartilhado entre duas questões.
- [x] Criar a aplicação, vincular o aluno e finalizar a lista (ou usar massa de teste com `end_time` preenchido).
- [x] Entrar como aluno/responsável e abrir a lista de aplicações; localizar o botão **“Imprimir Caderno”**.
- [x] Confirmar que o PDF exibe o texto uma única vez antes da primeira questão vinculada, com o rodapé abaixo e sem repetição/aviso residual.

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/<application_student>/imprimir/lista-exercicio`
- Condição: `Application.category == 4` e `today >= application.date_time_start_tz`; `ApplicationStudent.end_time` preenchido
- Template: `exam_homework_print.html`
- Seletor: `#baseText_<id>`, `.text-base-questions-footer`
- Fixture: `ApplicationStudent` do aluno logado + `Application(category=Application.HOMEWORK)`

### 5.6 Regressão, randomização e casos de borda [Apenas Manual 👁]

#### Cenário 9 — Configurações avançadas reorganizadas não quebraram

**Ação humana:**
- [x] Abrir a edição de um caderno e expandir **“Configurações adicionais”**.
- [x] Confirmar que os blocos **“Onde serão mostrados os textos base?”**, campos de seleção/entrada, switches e **“Orientações”** estão legíveis, alinhados e sem sobreposição.
- [x] Verificar visualmente os switches **“Limitar quantidade de alternativas”**, **“Embaralhar alternativas”**, **“Embaralhar questões”**, **“Agrupar questões discursivas ao final”** e **“Relacionar disciplinas”**: trilho e bolinha alinhados ao label.
- [x] Salvar e reabrir o caderno; confirmar que os valores dos switches foram preservados.
- [x] Testar em resolução intermediária (1333×1080) e em tela menor, garantindo que os 5 radios quebram linha sem corte.

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/editar/`
- Seletor: `#collapseAdvanced`, `#id_use_quantity_alternatives`, `#id_random_alternatives`, `#id_random_questions`, `#id_group_discursive_questions_at_end`, `#id_related_subjects`
- Estado esperado: `#collapseAdvanced .custom-switch .custom-control-label::before/after { top: 12px; }` aplicado; sem overflow horizontal
- Fixture: caderno com switches em estados variados

#### Cenário 10 — Versão randomizada (suspeita de repetição) [Apenas Manual 👁]

**Ação humana:**
- [ ] Em um caderno com opção 4 e questões randomizadas, gerar as versões/gabarito ou o malote que cria `RandomizationVersion`.
- [ ] Imprimir a prova de um aluno com versão randomizada (`application_student` + `version_number`).
- [ ] Confirmar se o texto-base aparece **uma única vez** antes da primeira questão vinculada ou se ele se repete antes de **todas** as questões vinculadas.
- [ ] Se repetir, registrar como bug com o contexto técnico abaixo.

**Referência técnica (para automação):**
- URL: `/provas/<uuid>/imprimir?application_student=<uuid>&version_number=<n>`
- Causa provável: no ramo `{% if randomization %}` de `exam_data.js`, cada questão recebe `index` e `number_print`, mas **não recebe `number`**; `getTheLowestNumber()` retorna `undefined` e `question.number == undefined` é verdadeiro para todas as questões
- Seletores: `#baseText_<id>` (contar ocorrências), `.text-base-questions-footer`
- Fixture: `RandomizationVersion` + `ApplicationStudent` com versão


## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Tirar print da seção **“Configurações adicionais”** com os 5 radios, em resolução 1333×1080, e anexar como evidência. ![](../evidencias/configs.png)
- [ ] Tirar print do PDF de 2+ páginas com o texto-base antes da questão, evidenciando o rodapé **“(Texto para as questões X e Y)”** abaixo do corpo. ![](../evidencias/questoes.png)

## 7. Bugs and Observations (Problemas Encontrados)

> Instrução: registrar com alerts GitHub (`> [!WARNING]`, `> [!BUG]`) e tags `[UX/UI]`, `[Backend Logic]`, `[Database]` ou `[Spec Gap]`. Nunca cite “conforme OpenSpec” genericamente; cite a seção/linha ou marque `(inferência de UX — Spec Gap)`.

> [!WARNING]
> **[Spec Gap] A tela real do professor (`?v=2`) não expõe a nova opção.**
> **Contexto:** a navegação do professor usa `?v=2`, que renderiza `exam_teacher_create_update_v2.html`. Esse template não contém `base_text_location` nem a seção “Onde serão mostrados os textos base?”; a branch altera apenas `exam_teacher_create_update.html` (legado). O requisito “Seleção da nova opção nos formulários de caderno” cita `exam_teacher_create_update.html`, mas o fluxo real do produto não passa por ele.
> **Esperado:** a opção 4 deve estar disponível no formulário de criação/edição de lista de exercício do professor, conforme `spec.md` (Requirement “Seleção da nova opção nos formulários de caderno”).
> **Workaround para continuar o roteiro:** validar a persistência e a renderização pela URL legada sem `?v=2`; abrir follow-up para incluir o controle no template `v2`.

> [!WARNING]
> **[Spec Gap] “Diagramar caderno” v2 não renderiza a opção 4.**
> **Contexto:** o item **“Diagramar caderno”** aponta para `/provas/<uuid>/v2/imprimir/` (`exam-print-v2`) e usa `dashboard/exams/v2/exam_print.html`; a branch só alterou `dashboard/exams/exam_print.html` (fluxo **“Imprimir caderno”** e malote). Usuários que diagramam pelo v2 não verão o novo comportamento.
> **Esperado:** alinhar com produto se a opção 4 deve valer também no v2; a spec atual cita `exam_print.html` e os includes, mas não cobre o v2 explicitamente.
> **Workaround:** validar a feature por **“Imprimir caderno”** e pelo malote; registrar a lacuna para decisão de produto.


## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Cobertura de teste:** os testes atuais validam strings dos templates, não o HTML renderizado nem o PDF. Adicionar teste de renderização (Django `render_to_string` ou snapshot de HTML) para as três variantes de layout e para o caso randomizado.

> [!NOTE]
> **Randomização:** incluir `number` no ramo randomizado de `exam_data.js` (ou ajustar `getTheLowestNumber` para usar `number_print`/`index`) e cobrir com teste.

> [!NOTE]
> **Seletores para automação:** adicionar `data-testid` estável nos radios de `base_text_location` e no rodapé do texto; hoje dependemos de `#id_shared_below`, `#baseText_<id>` e `.text-base-questions-footer`.

> [!NOTE]
> **Paridade de telas:** incluir a opção 4 no template `exam_teacher_create_update_v2.html` e avaliar suporte no `exam-print-v2`.

> [!NOTE]
> **Referência visual:** versionar o mockup `references/texto_base_compartilhado.html` citado no README do change.

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [ ] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_list_new.md)** (existente — entrada em “Imprimir caderno” e “Diagramar caderno”)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_request_create_update_new.md)** (novo — radios de texto-base e configurações avançadas)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_teacher_create_update.md)** (novo — radios do professor, versão legada e `?v=2`)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_print.md)** (novo — impressão do caderno e seletores do texto compartilhado)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_homework_print.md)** (novo — impressão de lista de exercício)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_preview.md)** (novo — preview fiscal)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/distribution_list.md)** (existente — malote de ensalamento e `#print-exam`)
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/question_create_update_redesign.md)** (existente — vínculo de textos-base na questão)

**Snippet de automação futura (setup + navegação, não só cliques):**

```python
# Setup: usar o bloco da Seção 4 (Client, CoordinationMember, Exam SHARED_BELOW,
# BaseText vinculado às questões 4 e 5, ExamQuestion orders 3 e 4).

# Playwright (pseudo):
# 1. login como coordenação
# 2. page.goto(f"/provas/{exam.pk}/editar/")
# 3. page.click("#headingAdvanced")
# 4. assert page.is_checked("#id_shared_below")
# 5. page.goto(f"/provas/{exam.pk}/imprimir?separate_subjects=0")
# 6. assert page.locator(f"#baseText_{base_text.pk}").count() == 1
# 7. footer = page.locator(".text-base-questions-footer")
#    assert "Texto para as questões 4 e 5" in footer.inner_text()
# 8. assert "Esta questão possui" not in page.content()
```

## 9. QA Retrospective (Retrospectiva de QA)

- Qual foi o principal gargalo durante o teste? (preencher após execução)
- Houve muitas idas e vindas com o desenvolvedor? (preencher após execução)
- Como o fluxo de desenvolvimento ou QA desta task poderia ter melhorado? (preencher após execução)

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- (preencher durante a execução: edge case novo, passo faltante ou falha do prompt)
- Sugestão inicial: o prompt deve exigir a checagem de **qual template é realmente servido pela navegação** (`?v=2`, feature flags, `has_new_*_experience`) antes de considerar uma tela coberta; neste caso, o template legado do professor foi alterado, mas o fluxo real usa o v2.

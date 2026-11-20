# Mapeamento de Tela: exam_request_create_update_new.html

> Template: `fiscallizeon/exams/templates/dashboard/exams/exam_request/exam_request_create_update_new.html`

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Criar caderno | `/provas/cadastrar/?category=exam` | `exams:exams_create` (`ExamCreateView`) |
| Editar caderno | `/provas/<uuid:pk>/editar/` | `exams:exams_update` (`ExamUpdateView`) |
| Listar cadernos | `/provas/?category=exam` | `exams:exams_list` |

- **Menu lateral:** Instrumentos Avaliativos → **Caderno de prova**.
- **Criar:** botão **“Solicite questões a professores”**.
- **Editar:** linha do caderno → **“Opções”** → **“Editar caderno”**.
- **Permissões:** criar → `exams.add_exam` + `required_permissions = [COORDINATION]`; editar → `exams.change_exam` + `required_permissions = [COORDINATION, TEACHER]`; cliente com `client_has_exam_elaboration = True`.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam

client_obj = mixer.blend(Client, has_exam_elaboration=True, two_factor_enabled=False)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
user = mixer.blend(
    User,
    user_type='coordination',
    two_factor_enabled=False,
    must_change_password=False,
)
mixer.blend(CoordinationMember, user=user, coordination=coordination)
user.user_permissions.add(
    Permission.objects.get(content_type__app_label='exams', codename='add_exam'),
    Permission.objects.get(content_type__app_label='exams', codename='change_exam'),
    Permission.objects.get(content_type__app_label='exams', codename='view_exam'),
)
exam = mixer.blend(Exam, coordinations=[coordination], base_text_location=Exam.SHARED_BELOW)
```

## 3. Seletores DOM e Ações

### Formulário principal
- **Formulário:** `#form-exam-create-update` (`method="POST"`, `onsubmit="return false"`)
- **Nome do caderno:** `#id_name` (`v-model="exam.name"`)
- **Nota geral:** `#id_total_grade`
- **Salvar e continuar (topo):** `button:has-text("Salvar e continuar")`
- **Salvar e finalizar (rodapé):** `button:has-text("Salvar e finalizar")`
- **Handler:** `saveExam()` (`exam_request_create_update_new.html:10618`); `controls.isSavingAndContinue` controla o botão do rodapé.
- **API de persistência:** `POST /provas/api/prova/` (criar) e `PUT/PATCH /provas/api/prova/<uuid>/` (editar), `ExamCoordinationAndTeacherViewSet` (`api-exam`).

### Card “Configurações adicionais”
- **Header:** `#headingAdvanced` (`data-toggle="collapse"`, `data-target="#collapseAdvanced"`)
- **Container:** `#collapseAdvanced` (`aria-labelledby="headingAdvanced"`)
- **Título visível:** `“Configurações adicionais”`

### Radios “Onde serão mostrados os textos base?”
- **Grupo:** `input[name="base_text_location"]`
- **Por questão:** `#id_per_question` (`value="0"`)
- **Por disciplina:** `#id_exam_top` (`value="1"`)
- **Início do caderno:** `#id_subject_top` (`value="2"`)
- **Final do caderno:** `#id_subject_bottom` (`value="3"`)
- **Texto compartilhado com questões embaixo:** `#id_shared_below` (`value="4"`)
- **Binding:** `v-model="exam.base_text_location"`
- **Label da 5ª opção:** `label[for="id_shared_below"]` → `“Texto compartilhado com questões embaixo”`
- **Container do grupo de rádios:** `div.tw-col-span-full` (linha inteira do grid de 6 colunas para não colidir com `"Qual número irá iniciar o caderno?"`; atenção: `sm:tw-col-span-6` **não existe** compilada em `fiscallizeon/core/static/tw/tw.css`, usar sempre `tw-col-span-full`).
- **Atenção:** os IDs `id_exam_top`/`id_subject_top` não correspondem semanticamente aos labels; usar sempre `value` para automação.

### Outros controles de “Configurações adicionais”
- **Limitar quantidade de alternativas:** `#id_use_quantity_alternatives`
- **Embaralhar alternativas:** `#id_random_alternatives`
- **Embaralhar questões:** `#id_random_questions`
- **Agrupar questões discursivas ao final:** `#id_group_discursive_questions_at_end` (`:disabled="!canEditDiscursiveGrouping"`)
- **Relacionar disciplinas:** `#id_related_subjects`

### API e estado
- **Serializer:** `base_text_location` em `ExamCoordinationAndTeacherViewSet` (`fiscallizeon/exams/serializers/exams.py:614`).
- **Choices:** `Exam.BASE_TEXT_LOCATION_CHOICES` exportado em `fiscallizeon/exams/views/exams.py:5608`.
- **Valores esperados:** `0`, `1`, `2`, `3`, `4`; o detalhe do caderno deve devolver `base_text_location` numérico.
- **Inicialização Vue:** `base_text_location: {% if object %}{{ object.base_text_location|default:0 }}{% else %}0{% endif %}` no objeto `exam` do Vue.

## 4. API Interception & Fixtures (rotas e entidades críticas)

- `GET /provas/api/prova/<uuid>/` → detalhe com `base_text_location`.
- `POST /provas/api/prova/` → cria caderno; body inclui `base_text_location: 4`.
- `PUT/PATCH /provas/api/prova/<uuid>/` → atualiza `base_text_location`.
- **Entidades para render:** `Exam`, `SchoolCoordination`, `Unity`, `Grade`, `Subject`, `TeacherSubject`, `ExamHeader`.
- **Campos correlatos:** `category` (`0=Exam`, `1=Homework`), `base_text_location`, `random_questions`, `random_alternatives`, `group_discursive_questions_at_end`, `related_subjects`.

## 5. Grafo de Dependências e Impacto Cruzado (Upstream & Downstream)

Qualquer alteração em campos de configuração do caderno (`Exam`) nesta tela exige verificação e inclusão de cenários nos seguintes fluxos conectados:

- **⬆️ Fontes Irmãs de Entrada (Upstream / Batch):**
  - **Importação de Cadernos via Planilha CSV:** `fiscallizeon/exams/tasks/exams_imports.py` (mapeia strings da coluna `"Onde serão mostrados os textos base"` e demais colunas para os choices de `Exam`). **Regra:** todo novo choice ou campo em `Exam` DEVE ser mapeado em `exams_imports.py` e testado via importação CSV.
  - **Documento Auxiliar de Importação:** `fiscallizeon/exams/views/exams.py` (exporta `Exam.BASE_TEXT_LOCATION_CHOICES` dinamicamente).
- **⬇️ Consumidores Diretos (Downstream Screens — Incluir no Plano de QA):**
  - 🔗 [exam_print.md](./exam_print.md) — Impressão de caderno e malote (`/provas/<uuid>/imprimir`, layouts `not_separate.html`, `separate_subjects.html` e `separate_category.html`).
  - 🔗 [exam_preview.md](./exam_preview.md) — Preview fiscal (`/provas/<uuid>/visualizar/fiscal`).
  - 🔗 [exam_homework_print.md](./exam_homework_print.md) — Impressão de lista de exercício do aluno (`/provas/<uuid>/<application_student>/imprimir/lista-exercicio`).
  - 🔗 [student_homework.md](./student_homework.md) — Realização de lista de exercício (`/aplicacoes/<app_student_pk>/realizar-atividade` via `student-homework.html`) e prova online monitorada (`student-new-exam.html`) pelo aluno.
- **🚫 Telas Irmãs Descontinuadas (Dead Screens — PROIBIDO Editar ou Testar):**
  - 🔗 [exam_teacher_create_update.md](./exam_teacher_create_update.md) — O template legado `exam_teacher_create_update.html` (sem `?v=2`) está **oficialmente descontinuado**. Nunca replicar alterações nele nem incluí-lo em diffs ou roteiros de QA.

## 6. Armadilhas Conhecidas e Cruzamentos Obrigatórios de QA (Histórico de Reviews)

- **[Review CU-86akta6jf — Escopo Mínimo no `#collapseAdvanced`]:** Este arquivo possui mais de 11.700 linhas. É terminantemente proibido aproveitar uma task pontual para reorganizar a ordem dos campos, alterar grids de outros inputs ou adicionar CSS customizado para `.custom-switch` no `#collapseAdvanced`. Alterar apenas as linhas estritamente relacionadas ao campo da tarefa.
- **[Review CU-86akta6jf — Purga do Tailwind (`tw.css`)]:** Nem todas as classes utilitárias do Tailwind existem no bundle estático `fiscallizeon/core/static/tw/tw.css` (ex.: `sm:tw-col-span-6`, `sm:tw-flex-wrap` e `sm:tw-space-x-6` **não existem** no `tw.css` e fazem o grid cair para 1 coluna, misturando inputs vizinhos). Verificar sempre em `tw.css` e usar `tw-col-span-full`, `tw-flex-wrap` e `tw-gap-y-3`.
- **[Review CU-86akta6jf — Propagação Ponta a Ponta de Choices]:** Sempre que um novo choice for adicionado em `Exam` (ex.: `base_text_location`), o Plano de QA DEVE testar: (1) Persistência neste formulário, (2) Importação via CSV (`exams_imports.py`), (3) Impressão em todas as variantes (`exam_print.md`), e (4) Realização da atividade/prova com a visão do aluno (`student_homework.md` com Console `F12` aberto).

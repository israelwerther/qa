# Mapeamento de Tela: exam_preview.html

> Template: `fiscallizeon/exams/templates/dashboard/exams/exam_preview/exam_preview.html`
> View: `ExamInspectorPreviewView` (`fiscallizeon/exams/views/exams.py:3284`)

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Preview fiscal | `/provas/<uuid:pk>/visualizar/fiscal` | `exams:exams_inspector_preview` (`ExamInspectorPreviewView`) |
| Preview simples (não alterado) | `/provas/<uuid:pk>/visualizar/simples` | `exams:exams_preview_simple` (`ExamPreviewSimpleView`) |
| Preview redesign (não renderiza textos-base) | `/provas/<uuid:pk>/visualizar` | `exams:exams_preview` |

- **Acesso:** a partir das ações de visualização do caderno [verificar rótulo exato do botão].
- **Permissões:** `required_permissions = [COORDINATION, TEACHER, INSPECTOR]`.
- **Template alvo da feature:** `exam_preview.html` com `preview_mode="inspector"`.
- **Atenção:** `exam_preview_simple.html` e `exam_preview_redesign_content.html` não são cobertos por este mapeamento.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam

client_obj = mixer.blend(Client, has_exam_elaboration=True)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
user = mixer.blend(User, user_type='coordination', two_factor_enabled=False)
mixer.blend(CoordinationMember, user=user, coordination=coordination)
user.user_permissions.add(
    Permission.objects.get(content_type__app_label='exams', codename='view_exam'),
)
exam = mixer.blend(
    Exam,
    coordinations=[coordination],
    base_text_location=Exam.SHARED_BELOW,
)
```

- Para o cenário de texto compartilhado, vincular o mesmo `BaseText` às questões 4 e 5 e criar `ExamQuestion` com `order` correspondente.

## 3. Seletores DOM e Ações

### Página de preview fiscal
- **Bloco de texto compartilhado:** `#baseText_<base_text_id>` e `[data-baseText="baseText_<base_text_id>"]`
- **Rodapé de questões:** `.text-base-questions-footer`
- **Questão:** `.question#question-<question_id>`
- **Enunciado:** `.question-enunciation`
- **Aviso residual:** texto **“Esta questão possui”** (`text_relation.html`) — deve estar ausente na opção 4.
- **Indicação esperada:** `“Texto para a questão X”` ou `“Texto para as questões X e Y”`.
- **Contexto:** `preview_mode = "inspector"`, `questions = self.object.questions.availables(self.object)`.

## 4. API Interception & Fixtures (rotas e entidades críticas)

- `GET /provas/<uuid>/visualizar/fiscal` → renderiza `exam_preview.html` com `preview_mode="inspector"`.
- **Entidades para render:** `Exam`, `ExamQuestion`, `ExamTeacherSubject`, `Question`, `QuestionOption`, `BaseText`.
- **Condição de template:** `shared_below.html` é incluído quando `object.get_base_text_location_display` é `'Texto-base compartilhado com questões embaixo'`; `text_relation.html` é omitido no mesmo caso.
- **Observação:** o preview simples (`/visualizar/simples`) e o preview redesign (`/visualizar`) não usam este template e não devem ser usados para validar a opção 4.

## 5. Grafo de Dependências e Impacto Cruzado (Upstream & Downstream)

- **⬆️ Origem das Configurações (Upstream):** 🔗 [exam_request_create_update_new.md](./exam_request_create_update_new.md) (`Exam.base_text_location`).
- **🧩 Partials e JS Compartilhados:** `per_questions.html`, `shared_below.html`, `subjects_top.html`, `exam_top_bottom.html`, `text_relation.html` e `base_texts-functions.js`.
- **↔️ Telas Irmãs que Compartilham os Mesmos Partials:** 🔗 [exam_print.md](./exam_print.md), 🔗 [exam_homework_print.md](./exam_homework_print.md) e 🔗 [student_homework.md](./student_homework.md).

## 6. Armadilhas Conhecidas e Cruzamentos Obrigatórios de QA (Histórico de Reviews)

- **[Ausência de `printConfig` no Vue]:** Diferente de `exam_print.html`, a instância Vue de `exam_preview.html` **não define `printConfig`** em `data`. Qualquer função em `base_texts-functions.js` ou partial compartilhado deve checar `this.printConfig && this.printConfig.hideNumbering` de forma defensiva para não lançar `TypeError` nesta tela.
- **[Cruzamento com `number_is_hidden = True`]:** Validar que questões com `number_is_hidden = True` não geram vírgulas órfãs no rodapé `.text-base-questions-footer` também no preview fiscal.

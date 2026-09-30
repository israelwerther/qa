# Mapeamento de usabilidade — `question_create_update.html`

Template legado da tela de criar/editar questão (tela clássica de edição).

> Nota: em `QuestionCreateView` / `QuestionUpdateView` (`fiscallizeon/questions/views/questions.py`,
> `get_template_names`) o default atual é `question_create_update_redesign.html`; este template
> legado (`question_create_update.html`) segue sendo mantido e foi alvo do fix de permissão da
> branch `feat/bloqueio-gabarito-revisor-CU-86ajjhfa9`. Confirmar em QA se ainda há rota que o
> renderiza ou se permanece apenas como fallback [verificar].

## 1. URLs e Navegação

| Modo | URL Django | View name | Query params relevantes |
|------|------------|-----------|-------------------------|
| Editar (clássica) | `/questoes/<uuid>/editar/` | `questions:questions_update` | — |
| Editar variante `v=2` | `/questoes/<uuid>/editar/?v=2` | `questions:questions_update` | `v=2` → renderiza `question_create_update_new.html` |
| Editar variante `v=new` | `/questoes/<uuid>/editar/?v=new` | `questions:questions_update` | `v=new` → renderiza `question_create_update_v2.html` [verificar] |
| Editar (redesign, default) | `/questoes/<uuid>/editar/` (sem `v`) | `questions:questions_update` | default → `question_create_update_redesign.html` |
| Sucesso pós-save | `reverse('questions:questions_list')` | `questions:questions_list` | URL exata da listagem [verificar] |

**Navegação típica (revisor sem permissão):**

1. Lista de questões (`questions:questions_list`) [verificar URL exata]
2. Abrir questão de outro professor → `/questoes/<uuid>/editar/`
3. Aba/formulário de alternativas com switches de gabarito desabilitados

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

Padrão copiado de `fiscallizeon/questions/tests/test_bloqueio_edicao_gabarito.py`
(`TestBloqueioEdicaoGabaritoView.setUp`):

```python
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.conf import settings
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import (
    Client, ClientQuestionsConfiguration, CoordinationMember,
    SchoolCoordination, Unity,
)
from fiscallizeon.inspectors.models import Inspector
from fiscallizeon.questions.models import Question, QuestionOption

cache.clear()
permissions = Permission.objects.filter(
    codename__in=[settings.COORDINATION, settings.TEACHER]
)

client_obj = mixer.blend(Client, has_sum_question=True)
mixer.blend(
    ClientQuestionsConfiguration,
    client=client_obj,
    teachers_coordinations_can_edit_questions=True,
)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)

# Autor da questão
author = mixer.blend(User)
author.user_permissions.set(permissions)
mixer.blend(CoordinationMember, user=author, coordination=coordination)
author_insp = mixer.blend(
    Inspector, user=author, email=author.email,
    inspector_type=Inspector.TEACHER, is_discipline_coordinator=False,
)
author_insp.coordinations.add(coordination)

# Revisor (não-autor, não-coordenador) — persona sem permissão
reviewer = mixer.blend(User)
reviewer.user_permissions.set(permissions)
mixer.blend(CoordinationMember, user=reviewer, coordination=coordination)
rev_insp = mixer.blend(
    Inspector, user=reviewer, email=reviewer.email,
    inspector_type=Inspector.TEACHER, is_discipline_coordinator=False,
)
rev_insp.coordinations.add(coordination)

question = mixer.blend(
    Question, category=Question.CHOICE, created_by=author,
)
mixer.blend(QuestionOption, question=question, is_correct=True)
mixer.blend(QuestionOption, question=question, is_correct=False)
```

**Permissões da view:** `LoginRequired2FAMixin`, `CheckHasPermission`
(`COORDINATION`/`TEACHER`), `questions.change_question`, módulo
`client_has_exam_elaboration`. Questão pública (`is_public`) redireciona para o dashboard.

**Atenção cache:** `reason_can_be_updated` usa cache de 30s
(`QUESTION_CAN_BE_UPDATED_{pk}_user_{user_pk}`) — chamar `cache.clear()` entre cenários.

## 3. Seletores DOM e Ações

### Gabarito — Múltipla Escolha / Somatório (tela clássica)

| Seletor | Descrição |
|---------|-----------|
| `input:checkbox.check-is-correct` | Switch/checkbox de alternativa correta (classe `custom-control-input check-is-correct`) |
| `label.custom-control-label[for="<auto_id do is_correct>"]` | Rótulo clicável do switch de gabarito |
| `b:contains("Alternativa X")` [verificar] | Cabeçalho de cada alternativa no loop do formset (`Alternativa {{ forloop.counter\|num_to_char }}`) |

### Comportamento JS verificado no fonte (`question_create_update.html`)

| Trecho | Comportamento |
|--------|---------------|
| Render do `is_correct` com `disabled="disabled"` quando `not can_be_updated.can_be_updated` | Switch nasce desabilitado para revisor |
| `$(window).on('load')` + `not form.instance\|check_can_be_updated:user` → `$('input:checkbox.check-is-correct').prop('disabled', true)` | Trava via JS no load quando sem permissão |
| `$('form').submit(...)` com permissão → remove `disabled` de todos os checkboxes | Fluxo do autor (inalterado) |
| `$('form').submit(...)` sem permissão → remove `disabled` de todos **exceto** `.check-is-correct` (`.not('.check-is-correct')`) | Gabarito bloqueado nem chega ao POST |
| TinyMCE `setMode('readonly')` + `check-is-correct` disabled no bloco de questão não-editável | Enunciado + gabarito travados juntos |

## Critical API Routes

| Endpoint | Uso na tela |
|----------|-------------|
| `PATCH /api/v1/alternatives/<pk>/?examquestion_id=<id>` (`questions:alternatives-detail`) | Alternância de gabarito / edição de opção (modelo PAS e API direta) — agora retorna `403` sem `can_be_updated` |
| `DELETE /api/v1/alternatives/<pk>/` (`questions:alternatives-detail`) | Remoção de alternativa — agora retorna `403` sem `can_be_updated` |

## Entidades complexas

- `Question` + `QuestionOption` formset (`question_option_formset`)
- `Question.can_be_updated(user)` / `reason_can_be_updated(user)` (7+ motivos de bloqueio, cache 30s)
- `ClientQuestionsConfiguration.teachers_coordinations_can_edit_questions`
- `Question.category`: `CHOICE`, `SUM_QUESTION` (via `supports_alternatives()`); campos diretos de gabarito: `binary_type`, `b_type_expected_answer`, `cloze_content`, `incorrect_cloze_alternatives`

# Mapeamento de Tela — `patio_list_by_class.html`

> Template: `fiscallizeon/distribution/templates/distribution/lists/patio_list_by_class.html`  
> Shell: `dashboard/clean_base_without_header.html`  
> View: `DistributionPatioListDetailView` (`distribution:distribution_patio_list`)  
> Feature: [Lista de ensalamento por turma](https://app.clickup.com/t/86ajvb3ka) / OpenSpec `lista-ensalamento-por-turma-86ajvb3ka`

---

## 1. URLs e Navegação

| Ação | URL | View name |
|------|-----|-----------|
| Lista de pátio por turma (1 coluna) | `/ensalamento/<uuid:pk>/lista/patio/?by_class=true` | `distribution:distribution_patio_list` |
| Lista de pátio por turma (2 colunas) | `/ensalamento/<uuid:pk>/lista/patio/?by_class=true&two_columns=true` | idem |
| Lista de pátio por sala (legado, sem by_class) | `/ensalamento/<uuid:pk>/lista/patio/` | idem → `patio_list.html` |
| Lista de pátio por sala (2 colunas) | `/ensalamento/<uuid:pk>/lista/patio/?two_columns=true` | idem → `patio_list.html` |

### Como chegar pela UI

1. Menu lateral: **"Aplicações"** → **"Ensalamento"** (`/ensalamento/`).
2. Na linha do ensalamento (com salas), botão **"Opções"** → seção **"IMPRESSÃO"** → **"Imprimir lista de pátio"**.
3. Modal `#patioPrintConfig` → ligar switch **"Separar lista por turma"** → **"Gerar listagem de pátio"** (`window.open` em nova aba).

### Comportamento de impressão

- No `mounted` do Vue, se `hide_dialog` for falso, dispara `window.print()` automaticamente.
- Para inspecionar o HTML sem o diálogo de impressão: acrescentar `&hide_dialog=true` na URL.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from django.utils import timezone
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.distribution.models import Room, RoomDistribution, RoomDistributionStudent
from fiscallizeon.exams.models import Exam

# Persona: coordenação com módulo de distribuição + permissão nos exames
user = mixer.blend(User, is_superuser=True)  # em UI real: CoordinationMember + IsCoordinationExamOwner
client_obj = mixer.blend(Client, has_distribution=True, require_2fa=False)
unity = mixer.blend(Unity, client=client_obj, name='Unidade Centro')
coordination = mixer.blend(SchoolCoordination, unity=unity)
room_1 = mixer.blend(Room, coordination=coordination, name='Sala 1')
room_2 = mixer.blend(Room, coordination=coordination, name='Sala 2')

grade_1 = mixer.blend(Grade, name='1', order=1)
grade_3 = mixer.blend(Grade, name='3', order=10)
class_1a = mixer.blend(
    SchoolClass, name='1A', grade=grade_1, coordination=coordination,
    school_year=timezone.now().year, temporary_class=False,
)
class_1b = mixer.blend(
    SchoolClass, name='1B', grade=grade_1, coordination=coordination,
    school_year=timezone.now().year, temporary_class=False,
)
class_3a = mixer.blend(
    SchoolClass, name='3A', grade=grade_3, coordination=coordination,
    school_year=timezone.now().year, temporary_class=False,
)
# Turma vazia (não deve aparecer):
mixer.blend(
    SchoolClass, name='2C', grade=grade_1, coordination=coordination,
    school_year=timezone.now().year, temporary_class=False,
)

exam = mixer.blend(Exam, client=client_obj, name='Prova QA Pátio')
room_distribution = mixer.blend(RoomDistribution)
mixer.blend(Application, room_distribution=room_distribution, exam=exam)

def _place(name, school_class, room):
    student = mixer.blend('students.Student', client=client_obj, name=name)
    if school_class:
        student.classes.add(school_class)
    RoomDistributionStudent.objects.create(
        distribution=room_distribution, student=student, room=room,
    )

_place('Ana Aluna', class_1b, room_1)
_place('Bruno Aluno', class_1a, room_1)
_place('Zelda Aluna', class_3a, room_2)
_place('Aluno Sem Turma', None, room_1)  # fallback "Sem turma"
```

**Permissões na view (dispatch):**

- `user.client_has_distribution` deve ser `True` (senão redirect: *"Cliente não possui este módulo"*).
- `IsCoordinationExamOwner` em todos os exames do ensalamento (senão: *"Você não tem permissão para acessar esta página"*).

---

## 3. Seletores DOM e Ações

### Cabeçalho por página/turma

- Título: `h3:has-text("Lista de Pátio")`
- Nome da prova: `h2` (vindo de `object.get_applications`)
- Unidade: texto `"Unidade: "` + `${unity.name}`
- Data: texto `"Data:"` + data da aplicação
- Cabeçalho da turma: `h4 strong` com `${classHeader(group)}` → `"Turma 1A"` ou `"Sem turma"`

### Tabela (uma coluna)

- Thead: `th:has-text("Aluno")`, `th:has-text("Sala")`
- Células: `${item.student}` e `${formatRoomName(item.room)}` (remove prefixo `"Sala "` do nome)

### Tabela (duas colunas — `group.split === true`)

- Só quando `twoColumns` e `students.length >= columMin` (25).
- Thead: **Aluno | Sala | Aluno | Sala** (quatro `th`).

### Quebra de página

- Container: `.pagebreak` (`page-break-before: always`) — **uma turma por página**.

### Payload Vue (dados embutidos)

Cada aluno no array `unities[].distributions[]`:

```js
{ student, schoolClass, gradeOrder, gradeName, room }
```

Ordenação JS (`groupsByClass`): `gradeOrder` ASC → `gradeName` → nome da turma; `"Sem turma"` por último (`Number.MAX_SAFE_INTEGER`).

### Sinal de carga (Playwright)

- Após `DOMContentLoaded`, o template injeta `#loaded` no `body`.

---

## 4. Rotas / APIs críticas

- Sem API nova. Apenas GET síncrono na view de detalhe.
- Query params independentes: `by_class`, `two_columns`, `hide_dialog`.
- Malote **não** inclui opção por turma (fora de escopo / lista de pátio no malote desativada).

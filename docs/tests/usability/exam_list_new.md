# Mapeamento de Tela: exam_list_new.html

> **Nota de Acervo:** Este arquivo é alimentado de forma incremental e colaborativa. Sempre que uma nova funcionalidade for testada nesta tela, o mapeamento de IDs e seletores estáveis deve ser atualizado aqui. O objetivo é criar um repositório centralizado para facilitar a automação via Playwright, sem depender de classes CSS frágeis.

## 1. URLs e Navegação
- **Listagem de cadernos (default / ativos):** `/provas/?category=exam`
- **Lista de exercícios (ativos):** `/provas/?category=homework`
- **Cadernos arquivados:** `/provas/?is_archived=true`
- **Abertura direta de caderno arquivado via busca:** `/provas/?q_pk=<uuid>&is_archived=true`
- **Navegação:** Menu lateral → "Instrumentos Avaliativos" → "Caderno de prova"/"Lista de Exercício"; a aba "Arquivados" fica na barra superior da própria listagem (`<nav>` com `data-tg-title="Tipos de instrumentos"`).
- **Arquivar/Desarquivar (API):** `POST /provas/api/prova/<uuid>/archive/` e `POST /provas/api/prova/<uuid>/unarchive/` (DRF action do `ExamCoordinationAndTeacherViewSet`, basename `api-exam`).
- **Busca global:** `GET /api/v1/search/?q=<termo>` retorna o grupo `"Cadernos"` com `"is_archived": true|false` em cada resultado.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- **Persona:** usuário com `user_type='coordination'` (somente coordenadores veem as ações de arquivar/desarquivar no menu de contexto e no bulk).
- **Permissão mínima para renderizar a listagem:** `exams.view_exam` (o filtro de status usa `ExamEnums.get_allowed_statuses_from_view_permissions`).
- **Setup via mixer (padrão usado em `test_exam_archiving.py`):**
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
login_user(self.client, user)

ativo = mixer.blend(Exam, is_archived=False, coordinations=[coordination])
arquivado = mixer.blend(Exam, is_archived=True, coordinations=[coordination])
```

## 3. Seletores DOM e Ações

### 3.1. Barra de abas (tabs Ativos/Arquivados)
- Container: `ul[data-tg-title="Tipos de instrumentos"]`
- Aba **Caderno de prova**: `ul[data-tg-title="Tipos de instrumentos"] li a:has-text("Caderno de prova")` → `/provas/?category=exam`
- Aba **Lista de Exercício**: `ul[data-tg-title="Tipos de instrumentos"] li a:has-text("Lista de Exercício")` → `/provas/?category=homework`
- Aba **Arquivados**: `ul[data-tg-title="Tipos de instrumentos"] li a:has-text("Arquivados")` → `/provas/?is_archived=true`

### 3.2. Barra de ações em massa (após seleção)
- Barra: `div[v-if="selectionList.length > 0"]` (posicionada sobre o topo da tabela)
- Botão **Alterar situação**: `button:has-text("Alterar situação")`
- Dropdown **Remover selecionadas**: `button#dropdownRemoverButton`; itens `.dropdown-menu a:has-text("Remover selecionadas")`, `.dropdown-menu a:has-text("Arquivar selecionadas")`, `.dropdown-menu a:has-text("Desarquivar selecionadas")`
- Checkbox de linha: `tr#tr-{{ exam.pk }} input[type="checkbox"][value="{{ exam.pk }}"]` (usa `v-model="selectionList"`)
- Checkbox do header (selecionar tudo): `input[type="checkbox"]` com binding `:checked="isIndeterminate || selectionList.length === exams.length"`

### 3.3. Menu de contexto por caderno (dropdown de ações)
- Gatilho: `button#dropdownMenuButton-{{ exam.pk }}` (texto "Opções", `data-toggle="dropdown"`) na linha `tr#tr-{{ exam.pk }}`
- **Arquivar caderno** (apenas ativos + `user_type == 'coordination'`): link com `onclick="archiveExam('{{ exam.pk }}', {{ exam.has_active_applications|yesno:'true,false' }})"` e texto "Arquivar caderno"
- **Desarquivar caderno** (apenas arquivados + coordination): link com `onclick="unarchiveExam('{{ exam.pk }}')"` e texto "Desarquivar caderno"

### 3.4. Modais (SweetAlert2)
- Confirmação de arquivamento com aplicação ativa: chamado por `archiveExam(examId, hasActiveApplications=true)` → `Swal.fire(...)`
- Confirmação de desarquivamento: `unarchiveExam(examId)` → `Swal.fire(...)`

### 3.5. Estado vazio
- Lista ativa vazia: `tbody td p:has-text("Não há cadernos cadastrados")`
- Lista arquivada vazia: `tbody td p:has-text("Não há cadernos arquivados")`

## 4. API Interception & Fixtures (rotas e entidades críticas)
- `POST /provas/api/prova/<uuid>/archive/`
  - Body (JSON): `{"confirm": true}` para contornar o aviso de aplicação ativa; `{"confirm": false}` retorna `400` com `"has_active_applications": true` quando há aplicação vigente.
  - Response 200: `{"message": "Caderno arquivado com sucesso", "is_archived": true}`
  - Non-coordination → `403` `"Apenas coordenadores podem arquivar cadernos."`
- `POST /provas/api/prova/<uuid>/unarchive/` → 200 `{"is_archived": false}`
- `GET /api/v1/search/?q=<termo>` → grupo `"Cadernos"` com `is_archived` por item.
- **Entidades complexas para render:** `Exam` (com `coordinations` relacionadas), `Application` (via `application_set`) — a property `has_active_applications` consulta `date`/`date_end`/`end` para detectar aplicações vigentes.
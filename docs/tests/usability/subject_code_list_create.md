# Mapeamento de Usabilidade — `subject_code_list_create.html`

Mapeamento do template `fiscallizeon/integrations/templates/integrations/subjects/subject_code_list_create.html` (Gestão de Códigos de Disciplinas / ERP).

## 1. URLs e Navegação

| Ação | Método | URL / Rota | View / Handler |
|---|---|---|---|
| Listagem e Gestão (Coordenação) | GET | `/integracoes/codigos/disciplinas/` | `fiscallizeon.integrations.views.SubjectCodeTemplateView` |
| API Sessão Web - Listar/Criar | GET / POST | `/integracoes/api/disciplinas/` | `fiscallizeon.integrations.apis.subjects.subject_code.api_subject_code_list_create` |
| API Sessão Web - Detalhe/Atualizar/Excluir | GET / PUT / DELETE | `/integracoes/api/disciplinas/<uuid:pk>/` | `fiscallizeon.integrations.apis.subjects.subject_code.api_subject_code_retrieve_update_destroy` |
| API Pública v2 - Listar/Criar Códigos | GET / POST | `/api/v2/subject-codes/` | `fiscallizeon.integrations.api2.subject_code.SubjectCodeIntegrationViewSet` |
| API Pública v2 - Detalhe/Editar/Excluir Códigos | GET / PUT / PATCH / DELETE | `/api/v2/subject-codes/<uuid:pk>/` | `fiscallizeon.integrations.api2.subject_code.SubjectCodeIntegrationViewSet` |
| API Pública v2 - Listar/Criar Etapas | GET / POST | `/api/v2/teaching-stages/` | `fiscallizeon.clients.api2.teaching_stage.TeachingStageIntegrationViewSet` |
| API Pública v2 - Detalhe/Editar/Excluir Etapas | GET / PUT / PATCH / DELETE | `/api/v2/teaching-stages/<uuid:pk>/` | `fiscallizeon.clients.api2.teaching_stage.TeachingStageIntegrationViewSet` |
| API Pública v2 - Resultados Alunos | GET | `/api/v2/application-students-results/` | `fiscallizeon.applications.api2.application_student.ApplicationStudentResultListAPIView` |

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

Para visualização da tela de gestão:
- Usuário logado com vínculo em coordenação (`CoordinationMember`) pertencente ao `Client`.
- Permissão `subjects.view_topic` (ou papel de Coordenação com permissões padrão).
- Grupo de Coordenação (`settings.COORDINATION`).

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember, TeachingStage
from fiscallizeon.subjects.models import Subject
from fiscallizeon.integrations.models import SubjectCode

client = mixer.blend(Client, require_2fa=False, use_only_own_subjects=True)
user = mixer.blend(User, is_active=True, client=client, must_change_password=False)
unity_a = mixer.blend(Unity, client=client, name="Unidade Centro")
unity_b = mixer.blend(Unity, client=client, name="Unidade Sul")
coordination = mixer.blend(SchoolCoordination, unity=unity_a)
mixer.blend(CoordinationMember, user=user, coordination=coordination)
subject_mat = mixer.blend(Subject, client=client, name="Matemática", parent_subject=None)
subject_port = mixer.blend(Subject, client=client, name="Português", parent_subject=None)
```

## 3. Seletores DOM e Ações

### 3.1 Cabeçalho e Painel de Filtros (Off-canvas)

- **Botão "Filtrar listagem":**
  - Seletor: `button.tw-off-canvas-menu[data-toggle-off-canvas="#right-off-canvas"]`
  - Badge de filtros aplicados: `span.tw-bg-red-100.tw-text-red-700`
- **Painel lateral (Off-canvas):**
  - Seletor contêiner: `#right-off-canvas`
  - Botão fechar: `#right-off-canvas .tw-off-canvas-close`
  - Formulário: `#subjectCodeFilterForm`
  - Input Nome da Disciplina: `#filterSubjectName` (`name="q_name"`)
  - Checkbox "Apenas disciplinas com código": `#filterWithCode` (`name="with_code"`, `value="1"`)
  - Botão Aplicar Filtro: `button[type="submit"][form="subjectCodeFilterForm"]`
  - Botão Limpar Filtro: `#right-off-canvas a:has-text("Limpar filtro")`

### 3.2 Tabela de Listagem de Códigos

- Contêiner de Dados Vue: `#app`
- Tabela: `table` (dentro de `#app`)
- Cabeçalhos:
  - Disciplina: `table thead th:nth-child(1)`
  - Código: `table thead th:nth-child(2)`
  - Unidade: `table thead th:nth-child(3)` (Texto: "Unidade")
  - Ações: `table thead th:nth-child(4)`
- Linhas: `tbody tr`
- Coluna Disciplina: `tbody tr td:first-child`
- Coluna Código: `tbody tr td:nth-child(2)`
- Coluna Unidade: `tbody tr td:nth-child(3)` (Exibe nome da unidade ou "Todas as unidades" / "—")
- Botões de Ação na Linha:
  - **Disciplina sem código:**
    - Botão "Cadastrar": `button:has-text("Cadastrar")`
  - **Disciplina com código cadastrado:**
    - Botão "Visualizar": `button:has-text("Visualizar")`
    - Botão "Cadastrar outro código": `button:has-text("Cadastrar outro código")`
    - Botão "Remover": `button:has-text("Remover")`

### 3.3 Modal de Cadastro / Edição de Código (`#modalSubjectCodeEdit`)

- Modal contêiner: `#modalSubjectCodeEdit`
- Título do Modal: `#modalSubjectCodeEditLabel`
- Campo Código da disciplina: `#subjectCodeValue` (ligado a `v-model="subjectCode.code"`)
- Select Unidade: `#subjectCodeUnity` (ligado a `v-model="subjectCode.unity"`)
  - Opção padrão: `<option value="">Todas</option>`
  - Opções dinâmicas: `<option :value="unity.id">${unity.name}</option>`
- Alerta de Erro de validação: `div.tw-rounded-md.tw-bg-red-50 span` (exibe `formError`)
- Botão "Fechar": `#modalSubjectCodeEdit button[data-dismiss="modal"]`
- Botão "Cadastrar código" / "Confirmar alterações": `#modalSubjectCodeEdit button:has-text("Cadastrar código")` ou `button:has-text("Confirmar alterações")`

## 4. Rotas de API Críticas

1. `GET /integracoes/api/disciplinas/`: Retorna a lista de `SubjectCode` existentes do cliente em formato JSON.
2. `POST /integracoes/api/disciplinas/`: Cria código. Em duplicidade, retorna HTTP 404 com `{"detail": "Já existe código para esta disciplina no contexto informado."}`.
3. `PUT /integracoes/api/disciplinas/<pk>/`: Atualiza código existente.
4. `DELETE /integracoes/api/disciplinas/<pk>/`: Exclui código.
5. `GET /api/v2/subject-codes/`: Endpoint público v2 do Swagger com suporte a GET, POST, PUT, PATCH e DELETE.
6. `GET /api/v2/teaching-stages/`: Endpoint público v2 do Swagger com suporte a GET, POST, PUT, PATCH e DELETE.
7. `GET /api/v2/application-students-results/?teaching_stage=<nome>&subject=<nome>`: API pública consultada pelo SEB para obter notas e `subject_id_erp`.

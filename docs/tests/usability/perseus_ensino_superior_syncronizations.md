# Mapeamento de Tela — `perseus_ensino_superior_syncronizations.html`

> Template: `fiscallizeon/integrations/templates/integrations/perseus_ensino_superior_syncronizations.html`
> View: `fiscallizeon/integrations/views.py::IntegrationsSynconizationsTemplateView`
> Branch de referência: `feat/perseus-status-alunos` (etapa 5 — Situação dos alunos)

---

## 1. URLs e Navegação

| Ação | URL | View name (Django) |
|------|-----|--------------------|
| Abrir a sincronização | `/integracoes/sincronizacoes/` | `integrations:integration_synconizations` |
| Abrir com token explícito (integrations baseadas em token) | `/integracoes/sincronizacoes/<int:token>/` | `integrations:integration_synconizations_token` |
| Prévia dos alunos que mudam (API) | `/integracoes/api/perseus/alunos/situacao/previa/` | `integrations:perseus-student-status-preview` |
| Salvar mapping + aplicar situação (API) | `/integracoes/api/perseus/alunos/situacao/aplicar/` | `integrations:perseus-student-status-apply` |
| Consultar o que já existe na Lize (API, etapa Alunos) | `/integracoes/api/perseus/alunos/sync-status/` | `integrations:perseus-students-sync-status` |
| Sincronizar turmas (API) | `/integracoes/api/sincronizar/turmas` | `integrations:sync_classes` |
| Sincronizar enturmações (API) | `/integracoes/api/sincronizar/enturmacoes` | `integrations:sync_interships` |

### Navegação para a tela

- **Menu/breadcrumb:** `Chaves` → `Sincronizar Perseus`.
- A página só abre para cliente com integração configurada e token/credenciais válidos.
- As etapas do wizard são botões no topo (`.perseus-wizard-step`); a etapa 5 é `Situação dos alunos`, entre `Ofertas` e `Alunos`.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões e persona

- Persona: **Coordenação** (`user_type = settings.COORDINATION`) vinculada ao cliente por `CoordinationMember`.
- A view exige `permission_required = 'integrations.view_integration'`.
- As APIs exigem `CheckHasPermissionAPI` (user_type coordenação) + `HasPerseusCollegeIntegration` (integração `erp = Integration.PERSEUS_COLLEGE`).
- O cliente precisa de `has_exam_elaboration`/módulo de integração ativo e de `client.integration` com token (ou usuário/senha válidos).

### Fixture Mixer (base copiada de `fiscallizeon/integrations/tests/test_perseus_sync.py::SetupMixin`)

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.clients.models import (
    Client,
    CoordinationMember,
    SchoolCoordination,
    Unity,
)
from fiscallizeon.integrations.models import Integration
from fiscallizeon.students.models import Student


def setup_perseus_status_ui():
    client = mixer.blend(
        Client, has_public_questions=True, has_exam_elaboration=True
    )
    # user_type é derivado de CoordinationMember (property), não é campo do User.
    coordinator = mixer.blend(User)
    integration = mixer.blend(
        Integration,
        client=client,
        erp=Integration.PERSEUS_COLLEGE,
        username='usuario_perseus',
        password='senha_criptografada',
        base_url='https://perseus-teste.example/PerseusPublicApi',
    )
    unity = mixer.blend(Unity, client=client)
    coordination = mixer.blend(SchoolCoordination, unity=unity)
    mixer.blend(
        CoordinationMember, user=coordinator, coordination=coordination
    )
    coordinator.user_permissions.set(
        Permission.objects.filter(
            codename__in=[
                'view_integration',
                'add_integration',
                'change_integration',
                'delete_integration',
            ]
        )
    )

    # Turma sincronizada (a tela considera turmas com id_erp no ano corrente)
    school_class = mixer.blend(
        SchoolClass,
        coordination=coordination,
        id_erp='TURMA-1',
        name='Turma Perseus 2026-2',
    )
    student = mixer.blend(
        Student,
        client=client,
        id_erp='PESSOA-1',
        enrollment_number='2026001',
        user__is_active=True,
    )
    school_class.students.add(student)

    # Situação salva de exemplo (vazio = primeira configuração)
    integration.perseus_student_status_mapping = {}
    integration.save(update_fields=['perseus_student_status_mapping'])

    return {
        'client': client,
        'coordinator': coordinator,
        'integration': integration,
        'school_class': school_class,
        'student': student,
    }
```

> Para simular "configuração já salva", preencha `perseus_student_status_mapping` com um dict `{"MAT": True, "CAN": False, ...}`.

### Observação sobre dados do Perseus

O catálogo de situações (`/v1/statusmatricula`), as matrículas por curso (`/v1/pessoas/alunos/matriculas?codigoCurso=...`) e o fallback por código (`/v1/pessoas/alunos/matriculas/obter-por-codigo`) são chamados **pelo navegador**, direto na API do Perseus (não passam pelo backend da Lize). Para automação offline, interceptar essas chamadas com `page.route(...)` e devolver fixtures JSON determinísticas.

---

## 3. Seletores DOM e Ações

### 3.1 Wizard de etapas (topo)

| Elemento | Seletor estável | Ação/observação |
|---|---|---|
| Container das etapas | `.perseus-wizard` | `role="navigation"`, `aria-label="Etapas da sincronização"` |
| Etapa por rótulo | `.perseus-wizard-step:has-text("5. Situação dos alunos")` | Clique bloqueado usa `:disabled` + classe `.perseus-wizard-step--locked` |
| Etapa ativa | `.perseus-wizard-step.perseus-wizard-step--active` | Cor de borda azul |
| Etapa concluída | `.perseus-wizard-step.perseus-wizard-step--done` | Borda verde |
| Meta da etapa 5 | `.perseus-wizard-step:has-text("Situação dos alunos") .step-meta` | `Defina as situações` ou `N ativas · M inativas` |

### 3.2 Aba Ofertas (`#classes`)

| Elemento | Seletor estável | Ação/observação |
|---|---|---|
| Período letivo | `#classes select` | `v-model="selectedPeriod"` |
| Buscar turmas | `#classes button:has-text("Buscar Turmas")` | Desabilitado sem período/unidade |
| Sincronizar turmas | `#classes button:has-text("Sincronizar Turmas")` | |
| Avançar para etapa 5 | `#classes button:has-text("Avançar para Situação dos alunos")` | Chama `goToStudentStatus()` |

### 3.3 Aba Situação dos alunos (`#student-status`)

| Elemento | Seletor estável | Ação/observação |
|---|---|---|
| Painel | `#student-status` | `role="tabpanel"`, `aria-label="Situação dos alunos"` |
| Bloco explicativo | `#student-status details.status-legend` | `<details open>` quando não há mapping salvo; `.status-legend-chevron` gira 180° |
| Título do bloco | `#student-status details.status-legend summary h6` | Texto `Quais alunos continuam ativos na Lize?` |
| Loading | `#student-status .text-center.text-muted` | Mensagens trocadas por `statusLoadingMessage` |
| Card resumo | `#student-status .card:has-text("Situações do Perseus")` | Contém `.progress` verde/vermelho e legenda |
| Botão de carga manual | `#student-status button:has-text("Buscar situações no Perseus")` | Aparece antes da primeira carga |
| Busca de situações | `#student-status input[type="search"][placeholder="Buscar situação ou código"]` | Normaliza acentos (`normalizeText`) |
| Filtro Todas/Ativo/Inativo | `#student-status .btn-group button:has-text("Todas")`, `...("Ativo")`, `...("Inativo")` | Botões com contagem no rótulo |
| Mostrar sem matrículas | `#student-status #statusShowEmpty` | `v-model="showEmpty"` |
| Atualizar do Perseus | `#student-status button:has-text("Atualizar do Perseus")` | Emite `reload` |
| Restaurar sugestão | `#student-status button:has-text("Restaurar sugestão")` | `:disabled` quando `isSuggestion` |
| Grupo | `#student-status .card:has-text("<Nome do grupo>")` | Ex.: Cursando, Contrato e pagamento, Pré-matrícula, Resultado do período, Movimentação interna, Curso encerrado, Saída da instituição, Outras situações |
| Marcar grupo ativo/inativo | dentro do grupo: `button:has-text("ativo")` / `button:has-text("inativo")` | No header `Marcar todas como ativo · inativo` |
| Linha por código | `#student-status tr:has-text("<CODIGO>")` | Linha inativa recebe `.status-row--inactive` (fundo `#fdf6f6`) |
| Escolha da linha | `tr:has-text("<CODIGO>") .status-choice button:has-text("Ativo")` / `...("Inativo")` | `aria-pressed` reflete o estado |
| Etiquetas | `tr:has-text("<CODIGO>") .badge-warning` (`nova`) / `.badge-light` (`alterado`) | |
| Card de mudanças | `#student-status .card:has-text("Mudanças na Lize ao aplicar")` | Contadores `inativados`/`reativados` |
| Ver quem muda | `#student-status a:has-text("Ver quem muda")` | Faz scroll até `#student-status-preview` |
| Salvar e aplicar | `#student-status button:has-text("Salvar e aplicar")` | `:disabled="saving"` |
| Avançar para Alunos | `#student-status button:has-text("Avançar para Alunos")` | Emite `advance` → `goToInterships()` |

### 3.4 Prévia "O que muda ao aplicar" (`#student-status-preview`)

| Elemento | Seletor estável | Ação/observação |
|---|---|---|
| Seção | `#student-status-preview` | |
| Aba inativados | `#student-status-preview button:has-text("Serão inativados")` | Classe ativa `btn-danger` |
| Aba reativados | `#student-status-preview button:has-text("Serão reativados")` | Classe ativa `btn-success` |
| Aba sem mudança | `#student-status-preview button:has-text("Sem mudança")` | Classe ativa `btn-secondary` |
| Busca de aluno | `#student-status-preview input[type="search"][placeholder="Buscar aluno por nome ou matrícula"]` | Só renderiza com >10 linhas ou busca ativa |
| Linhas | `#student-status-preview tbody tr` | Máximo de 100 (`previewVisibleRows`) |
| Rodapé de limite | `#student-status-preview .card-footer` | `Mostrando X de Y. Use a busca...` |

### 3.5 Aba Alunos (`#interships`)

| Elemento | Seletor estável | Ação/observação |
|---|---|---|
| Painel | `#interships` | `aria-label="Alunos e enturmações"` |
| Buscar alunos do Perseus | `#interships button:has-text("Buscar Alunos do Perseus")` | Desabilitado sem turmas |
| Sincronizar Enturmações | `#interships button:has-text("Sincronizar Enturmações")` | Texto muda para `Sincronizando X / Y...` |
| Remover turmas anteriores | `#interships #removeStudentClassesID` | |
| Coluna de situação | `#interships th:has-text("Situação no Perseus")` | Badge `badge-success` / `badge-danger` + `Fica ativo na Lize` / `Fica inativo na Lize` |
| Accordion de alunos | `#intershipsAccordion` | |

### 3.6 Diálogos SweetAlert2

| Diálogo | Seletor | Texto esperado |
|---|---|---|
| Etapa bloqueada | `.swal2-popup` | Título `Etapa bloqueada`; corpo com a mensagem da etapa |
| Atualizar sem turma | `.swal2-popup` | Título `Atenção`; `Sincronize ao menos uma turma antes de definir a situação dos alunos.` |
| Alterações não salvas | `.swal2-popup` | Título `Salve as situações`; `Salve e aplique as situações dos alunos antes de seguir para a etapa de Alunos.` |
| Confirmação | `.swal2-popup` | Título `Aplicar situações?`; botões `Salvar e aplicar` / `Cancelar` |
| Sucesso | `.swal2-popup` | Título `Situações salvas` |
| Sincronização | `.swal2-popup` | Título `Concluído!`; `${synced} de ${total} alunos sincronizados.` + resumo de inativações/reativações |

---

## 4. Rotas Críticas de API

| Rota | Método | Payload | Retorno |
|------|--------|---------|---------|
| `/integracoes/api/perseus/alunos/situacao/previa/` | POST | `{"student_ids": ["PESSOA-1", ...]}` | `{"students": [{"id_erp", "name", "enrollment_number", "is_active"}]}` |
| `/integracoes/api/perseus/alunos/situacao/aplicar/` | POST | `{"mapping": {"MAT": true, "CAN": false}, "persons": {"PESSOA-1": ["MAT", "CAN"]}}` | `{"deactivated": N, "reactivated": M}` |
| `/integracoes/api/perseus/alunos/sync-status/` | POST | `{"student_ids": [...]}` | `[{"id_erp", "atipico"}]` |

### Entidades de banco relevantes

- `integrations.Integration.perseus_student_status_mapping` (JSONField; migração `integrations/0059`).
- `students.Student.id_erp` (código da pessoa no Perseus) e `Student.enrollment_number`.
- `accounts.User.is_active` (é o campo alterado pela aplicação; histórico via `simple_history`).

---

## 5. Automation Snippet (Playwright + mixer)

```python
import pytest
from playwright.sync_api import Page
from django.urls import reverse

from .setup import setup_perseus_status_ui  # fixture acima


PERSEUS_STATUS_CATALOG = [
    {"codigo": "MAT", "nome": "Matriculado"},
    {"codigo": "CAN", "nome": "Cancelado"},
]
PERSEUS_ENROLLMENTS = [
    {
        "codigo": "MATRICULA-1",
        "status": {"codigo": "MAT", "nome": "Matriculado"},
    },
]


def test_situacao_dos_alunos_renderiza_sugestao(page: Page, live_server):
    data = setup_perseus_status_ui()

    # Intercepta a API externa do Perseus chamada pelo navegador
    page.route("**/v1/statusmatricula*", lambda route: route.fulfill(json=PERSEUS_STATUS_CATALOG))
    page.route("**/v1/pessoas/alunos/matriculas*", lambda route: route.fulfill(json=PERSEUS_ENROLLMENTS))
    page.route("**/v1/autenticacao/obter-token", lambda route: route.fulfill(
        json={"success": True, "data": {"access_token": "fake"}}
    ))

    page.goto(f"{live_server.url}{reverse('integrations:integration_synconizations')}")

    # A etapa 5 só destrava após Ofertas; para o teste, injete o estado via evaluate
    page.evaluate("window.__perseusTest = true")
    page.locator('.perseus-wizard-step:has-text("5. Situação dos alunos")').click()
    page.wait_for_selector("#student-status")
    assert page.locator("text=Situações do Perseus").is_visible()
```

> Dica: para isolar a etapa 5 sem repetir Unidades → Cursos → Disciplinas → Ofertas, interceptar as APIs e/ou acionar o método Vue `goToStudentStatus()` via `page.evaluate` depois de popular `syncedClasses`.

---

## 6. Gotchas e Regras de Negócio (QA Knowledge Base)

1. **Situação usada é a da matrícula** (`status.codigo` da matrícula no Perseus), não a situação da disciplina.
2. **Recorte:** só entram alunos das turmas sincronizadas do período. `rosterEnrollments` deduplica por `codigoMatricula`.
3. **Aluno com múltiplas matrículas:** fica ativo se **qualquer** matrícula estiver em situação marcada como ativa (`person_should_be_active` = `any`).
4. **Situação desconhecida no mapping salvo:** o backend assume `True` (mantém ativo) e a UI mostra badge `nova` + alerta. Só deixa de ser "nova" após salvar.
5. **Aplicação em massa:** `apply_students_status` altera `User.is_active` via `bulk_update_with_history` (motivo `Situação de matrícula no Perseus`).
6. **Mapping é por cliente** (campo único na `Integration`), não por período/turma.
7. **Performance:** ~3 mil matrículas levam 30–60 s porque a API do Perseus pagina em blocos de 50 e devolve o histórico inteiro do curso.
8. **Ordem de sincronização:** a regra é aplicada ao final de `Sincronizar Enturmações`, reutilizando `personStatuses` já carregado na etapa 5.

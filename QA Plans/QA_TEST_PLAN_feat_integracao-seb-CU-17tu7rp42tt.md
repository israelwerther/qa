## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-11-12 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Integrações / ERP (SEB) / Resultados / Disciplinas |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5 estrelas — proposal, design, specs e tasks completos) |
| **Branch Backend (lizeedu):** | `feat/integracao-seb-CU-17tu7rp42tt` |
| **Task ClickUp:** | [17tu7rp42tt](https://app.clickup.com/t/3120759/17tu7rp42tt) |

---

## 1. Summary of Changes (Resumo das Alterações)

A branch implementa a infraestrutura para a integração do **SEB (Sistema Educacional Brasileiro)**, permitindo mapeamento de códigos de disciplina por unidade escolar, disponibilização de CRUD de etapas e códigos na API pública v2, e a consulta otimizada de notas por disciplina via `GET /api/v2/application-students-results/`.

- **Modelo `SubjectCode` (`fiscallizeon/integrations/models.py`):**
  - Adicionado campo opcional `unity` (ForeignKey para `Unity`, `on_delete=models.PROTECT`, `null=True, blank=True`).
  - Campo com ordenação explícita por `created_at`.
- **Regras de Duplicidade (`reject_duplicate_subject_code`):**
  - `POST` em `/integracoes/api/disciplinas/` e `/api/v2/subject-codes/` rejeita duplicidade retornando **HTTP 404** com mensagem explicativa:
    - Se informado `unity`: rejeita se já existir código para o mesmo cliente + disciplina + unidade.
    - Se `unity` for omitido ou `null`: rejeita se já existir **qualquer** código para o cliente + disciplina (global ou com unidade).
    - Permite cadastrar código por unidade específica se já houver um código global anterior (mas bloqueia o inverso).
- **Resolução de `subject_id_erp` (`get_subject_id_erp` / `get_subject_ids_erp`):**
  - Se houver 0 códigos cadastrados: retorna `None` (`null`).
  - Se houver 1 código (mesmo com unidade): retorna esse código sem consultar turma.
  - Se houver múltiplos códigos sem unidade: retorna o último cadastrado (`created_at`) sem consultar turma.
  - Se houver múltiplos códigos e ao menos um tiver unidade: busca a turma do aluno via `get_last_class_student()`. Se o aluno não tiver turma, retorna `None`. Se tiver turma, busca o código correspondente à unidade da coordenação daquela turma (ou o mais recente se houver duplicidade histórica). Se não houver código para aquela unidade, retorna `None` (código global não mascara ausência de código específico).
- **Otimização de Desempenho em Lote (`result_page.py`):**
  - Prepara turmas e códigos em lote via subqueries e dicionários indexados, eliminando gargalo N+1 na rota de resultados.
- **API Pública v2:**
  - `GET /api/v2/teaching-stages/`: CRUD de etapas com isolamento por cliente e suporte a campos de notas separadas (objetiva/discursiva).
  - `GET /api/v2/subject-codes/`: CRUD de códigos de disciplina com filtros `unity` (UUID) e `unity_name` (busca textual sem case sensitive).
  - `GET /api/v2/application-students-results/`: Novos filtros `teaching_stage` (nome exato da etapa, case-insensitive) e `subject` (nome exato da disciplina, case-insensitive).
- **Interface Web da Coordenação (`subject_code_list_create.html`):**
  - Refatoração completa da tela `/integracoes/codigos/disciplinas/` para o design system atual (mesmo padrão de `/disciplinas/disciplinas/`), substituindo dropdown genérico por botões de ação direto na linha.
  - Modal para cadastrar/editar código com seleção de unidade opcional ("Todas as unidades" ou unidade específica).
  - Filtro off-canvas com busca por nome e toggle "Apenas disciplinas com código" restrito ao cliente ativo.
- **Bugfix Colateral de Layout (`subject_list.html`):**
  - Restaurado o padding `ard cer dcv` na listagem de disciplinas extras (`/disciplinas/disciplinas/`), corrigindo layout que encostava na borda da tela.

---

## 2. Scope Boundaries (Diferenças de Escopo)

**Dentro do Escopo:**
- Gestão de códigos de disciplina com unidade opcional via UI da Coordenação e via API v2.
- Validação e mensagens de recusa (HTTP 404) para duplicidade de códigos no mesmo contexto.
- Resolução do campo `subject_id_erp` nas notas de alunos conforme a unidade da turma do aluno.
- CRUD da API v2 para `teaching-stages` e `subject-codes`.
- Filtros `teaching_stage` e `subject` na listagem de resultados `application-students-results`.
- Proteção contra exclusão (`ProtectedError`) de Unidades que possuam códigos de disciplinas atrelados.
- Filtro "Apenas disciplinas com código" na UI da Coordenação.
- Correção de padding na tela de disciplinas extras (`/disciplinas/disciplinas/`).

**Fora do Escopo:**
- Integração ativa/síncrona (push de notas) com o sistema Sponte ou ERP do SEB pela Lize (a integração é passiva via consumo de API pelo SEB).
- Alteração no cálculo numérico de notas dos alunos.
- Associação de etapas diretamente ao modelo `SubjectCode` (etapa é gerenciada separadamente e vinculada ao caderno/avaliação).
- Migração automática ou backfill preenchendo unidade em códigos pré-existentes.
- Restrição de unicidade global rígida no PostgreSQL (`unique_together` de banco), preservando registros históricos já existentes.

---

## 3. Navegação e Camada Técnica

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Códigos de Disciplina (ERP) | Gerenciamento ➔ Disciplinas ➔ Código de Disciplina (ERP) [verificar] | `/integracoes/codigos/disciplinas/` | `integrations:integration_subject_code_list_create` |
| Disciplinas extras (bugfix de layout) | Gerenciamento ➔ Disciplinas ➔ Disciplinas extras [verificar] | `/disciplinas/disciplinas/` | `subjects:subjects_list` |
| API Pública - Códigos | N/A (Integração) | `/api/v2/subject-codes/` | `api2:subject-code-list` |
| API Pública - Etapas | N/A (Integração) | `/api/v2/teaching-stages/` | `api2:teaching-stage-list` |
| API Pública - Resultados | N/A (Integração) | `/api/v2/application-students-results/` | `api2:application-students-results` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### 4.1 Comandos de Execução Local

```bash
# Ativar o ambiente virtual
source venv/bin/activate

# 1. Testes de entrega SEB (APIs, isolamento de tenant, duplicidade, proteção de deleção)
pytest fiscallizeon/integrations/tests/test_seb_delivery.py --reuse-db -v

# 2. Testes de resolução de subject_id_erp por quantidade de códigos e unidade da turma
pytest fiscallizeon/applications/tests/serializers/test_application_student_result_subject_code.py --reuse-db -v

# 3. Testes da API v2 de códigos de disciplinas
pytest fiscallizeon/integrations/tests/test_subject_code_api.py --reuse-db -v

# 4. Testes do serviço de códigos de disciplinas
pytest fiscallizeon/integrations/tests/services/test_subject_code_service.py --reuse-db -v

# 5. Teste de performance e volumetria em lote de resultados
pytest fiscallizeon/applications/tests/test_result_performance.py --reuse-db -v

# 6. Testes de recursos de integração gerais (Etapas, etc.)
pytest fiscallizeon/api2/tests/test_integration_resources.py --reuse-db -v
```

### 4.2 Fixture Mixer para Testes Manuais

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember, TeachingStage
from fiscallizeon.subjects.models import Subject
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.students.models import Student
from fiscallizeon.exams.models import Exam
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.integrations.models import SubjectCode

# 1. Tenant e Usuário Coordenação
client = mixer.blend(Client, name="Colégio SEB Teste", require_2fa=False, use_only_own_subjects=True)
user_coord = mixer.blend(User, email="coord.seb@lize.local", is_active=True, client=client, must_change_password=False)
user_coord.set_password("123456")
user_coord.save()

# Unidades
unity_centro = mixer.blend(Unity, client=client, name="Unidade Centro")
unity_sul = mixer.blend(Unity, client=client, name="Unidade Sul")

coord_centro = mixer.blend(SchoolCoordination, client=client, unity=unity_centro, name="Coordenação Centro")
mixer.blend(CoordinationMember, user=user_coord, coordination=coord_centro)

# 2. Disciplinas
sub_mat = mixer.blend(Subject, client=client, name="Matemática SEB", parent_subject=None)
sub_port = mixer.blend(Subject, client=client, name="Português SEB", parent_subject=None)

# 3. Etapa e Avaliação Multidisciplinar
stage = mixer.blend(TeachingStage, client=client, name="1º Ano EM", code_export="EM-01")
exam = mixer.blend(Exam, client=client, name="Simulado Geral SEB", teaching_stage=stage, is_abstract=True)

# 4. Turmas
class_centro = mixer.blend(SchoolClass, client=client, coordination=coord_centro, name="Turma 101 Centro", school_year=2026, is_itinerary=False, temporary_class=False)
coord_sul = mixer.blend(SchoolCoordination, client=client, unity=unity_sul, name="Coordenação Sul")
class_sul = mixer.blend(SchoolClass, client=client, coordination=coord_sul, name="Turma 201 Sul", school_year=2026, is_itinerary=False, temporary_class=False)

# 5. Aplicação
app = mixer.blend(Application, client=client, exam=exam)
app.school_classes.add(class_centro, class_sul)

# 6. Alunos
student_a = mixer.blend(Student, client=client, name="Aluno Centro", enrollment_number="SEB001")
student_a.classes.add(class_centro)
app_student_a = mixer.blend(ApplicationStudent, application=app, student=student_a, missed=False)

student_b = mixer.blend(Student, client=client, name="Aluno Sul", enrollment_number="SEB002")
student_b.classes.add(class_sul)
app_student_b = mixer.blend(ApplicationStudent, application=app, student=student_b, missed=False)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona Ativa:** Coordenação Geral (`coord.seb@lize.local` / senha `123456`) e Agente de Integração via Token Bearer OAuth2.

### 5.1 Gestão de Códigos de Disciplina na Interface Web [Automatizável ✅]

#### Cenário 1 — Acesso à listagem e visualização do novo layout

**Ação humana:**
- [x] Fazer login com a Persona de **"Coordenação"**.
- [x] Acessar no menu lateral: `"**Gerenciamento**"` ➔ `"**Disciplinas**"` ➔ `"**Código de Disciplina (ERP)**"` (URL `/integracoes/codigos/disciplinas/`).
- [x] Verificar que o topo exibe o título `"**Códigos de disciplina**"` com visual limpo e o botão `"**Filtrar listagem**"`.
- [x] Confirmar que a tabela lista as disciplinas cadastradas no cliente com suas respectivas colunas de nome e código.

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/`
- Seletor: `h1:has-text("Códigos de disciplina")`
- Estado esperado: Tabela visível sem erros no console JS, elementos Tailwind carregados
- Fixture: `mixer.blend(Subject, client=client, name="Matemática")`

---

#### Cenário 2 — Cadastro de código sem unidade (válido para todas as unidades)

**Ação humana:**
- [x] Na linha de uma disciplina que ainda não possui código (ex.: `"**Álgebra**"` ou `"**Matemática SEB**"`), clicar no botão `"**Cadastrar**"` (ou `"**Cadastrar código**"` na coluna de ações).
- [x] No modal `"**Cadastrar código**"`, preencher o campo `"**Código ERP**"` com `"MAT-GLOBAL"`.
- [x] Deixar a seleção do campo `"**Unidade**"` na opção `"**Em branco**"` (conforme a dica abaixo do campo: *"Caso o código não mude entre unidades, deixe em branco"*).
- [x] Clicar no botão `"**Salvar código**"`.
- [x] Verificar a mensagem de feedback `"**Código cadastrado com sucesso!**"`.
- [x] Confirmar que a linha foi atualizada na tabela exibindo o código `"MAT-GLOBAL"`.

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/`
- Seletor: `#modalSubjectCodeEdit input#subjectCodeValue`, `#subjectCodeUnity`
- Estado esperado: Modal fecha via SweetAlert2, linha na tabela exibe texto `"MAT-GLOBAL"`
- Fixture: Subject sem SubjectCode vinculado

---

#### Cenário 3 — Bloqueio de duplicidade (mesma disciplina e mesmo contexto/unidade)

**Ação humana:**
- [x] Notar que na interface web, após cadastrar o código no Cenário 2, a linha da disciplina agora exibe os botões `"**Visualizar**"` e `"**Remover**"`, impedindo por design o cadastro acidental de múltiplos códigos no mesmo card.
- [x] Clicar no botão `"**Visualizar**"` para abrir o modal da disciplina recém-cadastrada.
- [x] Confirmar que os dados do código cadastrado (`al-global`) e da unidade (`Em branco`) são carregados corretamente nos campos do formulário.
- [x] *(Via API / Backend)*: Caso uma requisição POST tente criar um segundo código global (sem unidade) para esta mesma disciplina, verificar que a API rejeita a operação com erro de validação e mensagem clara: `"Já existe código cadastrado para esta disciplina no contexto informado."`.

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/`
- Seletor: `#modalSubjectCodeEdit div.tw-bg-red-50 span`
- Estado esperado: HTTP 404 retornado por `/integracoes/api/disciplinas/`, exibição de erro na UI
- Fixture: Subject já com um SubjectCode cadastrado

---

#### Cenário 4 — Cadastro de múltiplos códigos específicos por unidade

**Ação humana:**
- [x] Escolher uma disciplina ainda sem código na lista (por exemplo, `"**BIOLOGIA A**"` ou `"**Análises historiográficas**"`).
- [x] Clicar no botão `"**Cadastrar**"` dessa disciplina.
- [x] Cadastrar um código selecionando uma primeira unidade real (ex.: `"**GRU**"` ou qualquer unidade da escola) com o valor `"BIO-GRU"`.
- [x] Clicar em `"**Cadastrar código**"`.
- [x] Confirmar que o código `"BIO-GRU"` é exibido na coluna Código e, ao clicar em `"**Visualizar**"`, a unidade `"**GRU**"` permanece vinculada corretamente (validado também no banco de dados).

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/`
- Seletor: `#subjectCodeUnity select option[value="<unity_uuid>"]`
- Estado esperado: Duas linhas renderizadas no `#app` para a mesma disciplina

---

#### Cenário 5 — Filtro lateral por nome e disciplinas com código

**Ação humana:**
- [x] Clicar no botão `"**Filtrar listagem**"`.
- [x] No painel lateral off-canvas, marcar a caixa de seleção `"**Apenas disciplinas com código**"`.
- [x] Clicar em `"**Aplicar filtro**"`.
- [x] Verificar que apenas as disciplinas com códigos cadastrados para o cliente ativo continuam visíveis.
- [x] Confirmar que surge o badge/chip de filtro `"**Disciplinas com código**"` com botão `X` para remoção rápida.
- [x] Confirmar que códigos de **outros clientes** não fazem disciplinas aparecerem.

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/?with_code=1`
- Seletor: `#filterWithCode`, `span:has-text("Disciplinas com código")`
- Estado esperado: `tbody tr` filtrado de acordo com as disciplinas que possuem código

---

### 5.2 Resolução de Códigos no Endpoint de Resultados (`/api/v2/application-students-results/`) [Automatizável ✅]

#### Cenário 6 — Avaliação com alunos de unidades diferentes e códigos por unidade

**Ação humana:**
- [ ] Disparar requisição `GET` para `/api/v2/application-students-results/` passando os filtros da avaliação e disciplina `"Português SEB"`.
- [ ] Para o Aluno Centro (`SEB001`), verificar no payload JSON que o campo `"subject_id_erp"` é retornado como `"PORT-CENTRO"`.
- [ ] Para o Aluno Sul (`SEB002`), verificar no payload JSON que o campo `"subject_id_erp"` é retornado como `"PORT-SUL"`.
- [ ] Confirmar que o código de uma unidade nunca vaza para o aluno da outra unidade.

**Referência técnica (para automação):**
- URL: `/api/v2/application-students-results/?subject=Português%20SEB`
- Resposta esperada: `results[0].subject_id_erp == "PORT-CENTRO"`, `results[1].subject_id_erp == "PORT-SUL"`
- Fixture: Aluno A vinculado a turma da Unidade Centro, Aluno B vinculado a turma da Unidade Sul

---

#### Cenário 7 — Aluno de unidade sem código específico cadastrado

**Ação humana:**
- [ ] Simular um terceiro aluno vinculado a uma terceira unidade (ex.: `"Unidade Norte"`) na mesma avaliação.
- [ ] Consultar `/api/v2/application-students-results/`.
- [ ] Verificar que o campo `"subject_id_erp"` retorna **`null`** (o sistema não deve assumir códigos de outras unidades nem código global quando há variação contextual).

**Referência técnica (para automação):**
- URL: `/api/v2/application-students-results/`
- Resposta esperada: `"subject_id_erp": null` para aluno sem código na sua respectiva unidade

---

#### Cenário 8 — Filtro por `teaching_stage` e `subject` na API v2

**Ação humana:**
- [ ] Consultar `/api/v2/application-students-results/?teaching_stage=1º%20ano%20em` (usando minúsculas).
- [ ] Confirmar que o filtro ignora maiúsculas e minúsculas (case-insensitive) e retorna os resultados da etapa.

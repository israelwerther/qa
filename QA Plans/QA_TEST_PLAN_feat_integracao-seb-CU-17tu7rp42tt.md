## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-11-12 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Integrações / ERP (SEB) / Resultados / Disciplinas / Swagger API v2 |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5 estrelas — proposal, design, specs e tasks completos) |
| **Branch Backend (lizeedu):** | `feat/integracao-seb-CU-17tu7rp42tt` |
| **Task ClickUp:** | [17tu7rp42tt](https://app.clickup.com/t/3120759/17tu7rp42tt) |

---

## 1. Summary of Changes (Resumo das Alterações)

A branch implementa e consolida a infraestrutura completa para a integração do **SEB (Sistema Educacional Brasileiro)**, permitindo mapeamento de códigos de disciplina com unidade opcional, disponibilização de endpoints RESTful completos (CRUD) na API pública v2 documentados no Swagger, isolamento multi-tenant rigoroso por cliente e a consulta otimizada de notas por disciplina via `GET /api/v2/application-students-results/`.

### 1.1 Backend & Modelos
- **Modelo `SubjectCode` (`fiscallizeon/integrations/models.py`):**
  - Adicionado campo opcional `unity` (ForeignKey para `Unity`, `on_delete=models.PROTECT`, `null=True, blank=True`).
  - Campo com ordenação explícita por `created_at`.
- **Regras de Duplicidade (`reject_duplicate_subject_code`):**
  - Rejeita duplicações no mesmo contexto retornando **HTTP 404** com mensagem explicativa:
    - Com `unity`: rejeita se já existir código para o mesmo cliente + disciplina + unidade.
    - Sem `unity` (global): rejeita se já existir **qualquer** código para o cliente + disciplina.
    - Permite cadastrar código por unidade específica se já houver um código global anterior.
- **Resolução de `subject_id_erp` (`get_subject_id_erp` / `get_subject_ids_erp`):**
  - 0 códigos cadastrados: retorna `None` (`null`).
  - 1 código (mesmo com unidade): retorna esse código sem consultar turma.
  - Múltiplos códigos sem unidade: retorna o último cadastrado (`created_at`).
  - Múltiplos códigos com ao menos um com unidade: busca a turma do aluno via `get_last_class_student()`. Se tiver turma, busca o código correspondente à unidade da coordenação daquela turma (ou o mais recente em duplicidades legadas). Se não houver código para aquela unidade, retorna `None` (código global não mascara ausência de código específico).
- **Otimização de Desempenho em Lote (`result_page.py`):**
  - Prepara turmas e códigos em lote via subqueries e dicionários indexados, eliminando gargalos N+1 na rota de resultados.

### 1.2 Endpoints RESTful Públicos (API v2 Swagger)
- **Gestão de Etapas de Ensino (`/api/v2/teaching-stages/`):**
  - `GET /api/v2/teaching-stages/`: Listagem paginada com filtro por nome e isolamento estrito por `client`.
  - `POST /api/v2/teaching-stages/`: Criação de etapa vinculada automaticamente ao cliente autenticado.
  - `GET /api/v2/teaching-stages/{id}/`: Detalhe da etapa.
  - `PUT /api/v2/teaching-stages/{id}/`: Atualização completa da etapa.
  - `PATCH /api/v2/teaching-stages/{id}/`: Atualização parcial de campos (ex.: `name`, `code_export`).
  - `DELETE /api/v2/teaching-stages/{id}/`: Exclusão de etapa (protegida por tenant).
- **Gestão de Códigos de Disciplina (`/api/v2/subject-codes/`):**
  - `GET /api/v2/subject-codes/`: Listagem paginada com filtros `unity` (UUID) e `unity_name` (case-insensitive).
  - `POST /api/v2/subject-codes/`: Criação de código com validação de duplicidade e vínculo ao cliente.
  - `GET /api/v2/subject-codes/{id}/`: Detalhe do código.
  - `PUT /api/v2/subject-codes/{id}/`: Atualização completa.
  - `PATCH /api/v2/subject-codes/{id}/`: Atualização parcial.
  - `DELETE /api/v2/subject-codes/{id}/`: Exclusão de código.
- **Endpoint Web Interno (`/integracoes/api/disciplinas/`):**
  - Suporte às ações da interface Vue da coordenação (`POST`, `PUT`, `DELETE`).
- **Consulta de Resultados dos Alunos (`/api/v2/application-students-results/`):**
  - Novos filtros `teaching_stage` e `subject` (busca case-insensitive).

### 1.3 Interface Web da Coordenação (`subject_code_list_create.html`)
- **Correções recentes:**
  - **Coluna "Unidade":** Adicionada a coluna "Unidade" na tabela principal de disciplinas, exibindo o nome da unidade ou "Todas as unidades" / "—".
  - **Ação "Cadastrar outro código":** Permite adicionar múltiplos códigos contextuais (por unidade) para a mesma disciplina diretamente na UI.
  - **Label "Todas":** A opção em branco no modal foi ajustada para `"Todas"` (comportamento global para todas as unidades).
  - **Isolamento de catálogo:** A consulta de disciplinas restringe a exibição a disciplinas do próprio cliente ou do catálogo geral (sem cliente), eliminando disciplinas raiz de outros clientes.
  - **Filtro off-canvas:** Suporte ao filtro por nome e toggle "Apenas disciplinas com código" restrito ao cliente ativo.

---

## 2. Scope Boundaries (Diferenças de Escopo)

**Dentro do Escopo:**
- Gestão de códigos de disciplina com unidade opcional via UI da Coordenação e via API v2.
- Nova coluna "Unidade" e ação "Cadastrar outro código" na interface web.
- Cobertura completa de testes para todos os métodos HTTP das rotas `/api/v2/teaching-stages/` e `/api/v2/subject-codes/` (GET, POST, PUT, PATCH, DELETE).
- Validação e mensagens de recusa (HTTP 404) para duplicidade de códigos no mesmo contexto.
- Resolução do campo `subject_id_erp` nas notas de alunos conforme a unidade da turma do aluno.
- Filtros `teaching_stage` e `subject` na listagem de resultados `application-students-results`.
- Proteção contra exclusão (`ProtectedError`) de Unidades que possuam códigos de disciplinas atrelados.
- Correção de padding na tela de disciplinas extras (`/disciplinas/disciplinas/`).

**Fora do Escopo:**
- Integração síncrona ativa (push automático) para o ERP do SEB pela Lize (integração é passiva via consumo de API).
- Alteração nas fórmulas matemáticas de cálculo de notas dos alunos.
- Associação de etapas diretamente ao modelo `SubjectCode` (etapas são vinculadas ao exame/avaliação).
- Backfill compulsório ou migração automática preenchendo unidade em códigos legados.
- Restrição de unicidade rígida no PostgreSQL (`unique_together` de banco), preservando compatibilidade com dados legados.

---

## 3. Navegação e Camada Técnica

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Códigos de Disciplina (ERP) | Gerenciamento ➔ Disciplinas ➔ Código de Disciplina (ERP) [verificar] | `/integracoes/codigos/disciplinas/` | `integrations:integration_subject_code_list_create` |
| Disciplinas extras (bugfix de layout) | Gerenciamento ➔ Disciplinas ➔ Disciplinas extras [verificar] | `/disciplinas/disciplinas/` | `subjects:subjects_list` |
| API Pública - Códigos (CRUD) | Documentação Swagger | `/api/v2/subject-codes/` | `api2:subject-code-list` |
| API Pública - Etapas (CRUD) | Documentação Swagger | `/api/v2/teaching-stages/` | `api2:teaching-stage-list` |
| API Pública - Resultados | Documentação Swagger | `/api/v2/application-students-results/` | `api2:application-students-results` |
| API Sessão Web - Códigos | N/A (Consumo AJAX da tela) | `/integracoes/api/disciplinas/` | `integrations:api_subject_code_list_create` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### 4.1 Comandos de Execução Local

```bash
# Ativar o ambiente virtual
source venv/bin/activate

# 1. Testes de CRUD completo da API v2 (Etapas e Códigos de Disciplina)
pytest fiscallizeon/api2/tests/test_integration_resources.py --reuse-db -v

# 2. Testes de entrega SEB (isolamento de tenant, duplicidade, proteção de deleção de unidade)
pytest fiscallizeon/integrations/tests/test_seb_delivery.py --reuse-db -v

# 3. Testes de resolução de subject_id_erp por quantidade de códigos e unidade da turma
pytest fiscallizeon/applications/tests/serializers/test_application_student_result_subject_code.py --reuse-db -v

# 4. Teste de performance e volumetria em lote de resultados
pytest fiscallizeon/applications/tests/test_result_performance.py --reuse-db -v
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

#### Cenário 1 — Acesso à listagem, nova coluna "Unidade" e isolamento de catálogo

**Ação humana:**
- [x] Fazer login com a Persona de **"Coordenação"**.
- [x] Acessar no menu lateral: `"**Gerenciamento**"` ➔ `"**Disciplinas**"` ➔ `"**Código de Disciplina (ERP)**"` (URL `/integracoes/codigos/disciplinas/`).
- [x] Verificar que a tabela exibe as colunas: `"**Disciplina**"`, `"**Código**"`, `"**Unidade**"` e `"**Ações**"`.
- [x] Confirmar que a listagem não exibe disciplinas raiz pertencentes a outros clientes escolares.

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/`
- Seletor: `table thead th:has-text("Unidade")`, `h1:has-text("Códigos de disciplina")`
- Estado esperado: Tabela com 4 cabeçalhos de coluna, incluindo Unidade
- Fixture: `mixer.blend(Subject, client=client, name="Matemática")`

---

#### Cenário 2 — Cadastro de código global com opção "Todas"

**Ação humana:**
- [x] Na linha de uma disciplina que ainda não possui código, clicar no botão `"**Cadastrar**"`.
- [x] No modal de cadastro, preencher o campo `"**Código da disciplina**"` (ex.: `"MAT-GLOBAL"`).
- [x] Verificar que o campo `"**Unidade**"` possui a opção padrão com o rótulo `"**Todas**"`.
- [x] Clicar no botão `"**Cadastrar código**"`.
- [x] Verificar o feedback de sucesso e confirmar que na tabela a coluna `"**Unidade**"` exibe `"**Todas as unidades**"`.

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/`
- Seletor: `#modalSubjectCodeEdit select#subjectCodeUnity option[value=""]` (texto "Todas")
- Estado esperado: Modal fecha com sucesso; tabela exibe "Todas as unidades" na coluna Unidade
- Fixture: Subject sem SubjectCode vinculado

---

#### Cenário 3 — Bloqueio de duplicidade (mesma disciplina e mesmo contexto)

**Ação humana:**
- [x] Notar que após o cadastro, a disciplina exibe os botões `"**Visualizar**"`, `"**Cadastrar outro código**"` e `"**Remover**"`.
- [x] Clicar em `"**Visualizar**"` e validar que os dados salvos reabrem preenchidos.
- [x] Validar que caso uma requisição envie um segundo código global para a mesma disciplina, a API rejeita com status 404 e mensagem: `"Já existe código para esta disciplina no contexto informado."`.

**Referência técnica (para automação):**
- URL: `/integracoes/api/disciplinas/`
- Seletor: `#modalSubjectCodeEdit div.tw-bg-red-50 span`
- Estado esperado: Resposta HTTP 404 com `{ "detail": "Já existe código para esta disciplina no contexto informado." }`
- Fixture: Subject com SubjectCode já existente

---

#### Cenário 4 — Cadastro de múltiplos códigos com "Cadastrar outro código"

**Ação humana:**
- [x] Em uma disciplina que já possui código cadastrado, clicar no novo botão `"**Cadastrar outro código**"` (botão branco com texto laranja).
- [x] Verificar que o modal abre com os campos limpos para a mesma disciplina selecionada.
- [x] Preencher um novo código (ex.: `"BIO-GRU"`) e selecionar uma unidade específica no campo `"**Unidade**"` (ex.: `"GRU"`).
- [x] Clicar em `"**Cadastrar código**"`.
- [x] Confirmar que a tabela passa a listar ambas as variações de código para a mesma disciplina, cada uma com sua respectiva unidade.

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/`
- Seletor: `button:has-text("Cadastrar outro código")`
- Estado esperado: Duas linhas renderizadas na tabela para a mesma disciplina, com códigos e unidades distintos
- Fixture: Subject com um SubjectCode e ao menos uma Unity disponível

---

#### Cenário 5 — Filtro lateral por nome e disciplinas com código

**Ação humana:**
- [x] Clicar no botão `"**Filtrar listagem**"`.
- [x] No painel lateral off-canvas, marcar a caixa de seleção `"**Apenas disciplinas com código**"`.
- [x] Clicar em `"**Aplicar filtro**"`.
- [x] Verificar que apenas as disciplinas que possuem código cadastrado para o cliente ativo continuam visíveis.
- [x] Confirmar que o badge `"**Disciplinas com código**"` surge com o botão `X` para remoção rápida.

**Referência técnica (para automação):**
- URL: `/integracoes/codigos/disciplinas/?with_code=1`
- Seletor: `#filterWithCode`, `span:has-text("Disciplinas com código")`
- Estado esperado: Linhas da tabela filtradas de acordo com o parâmetro

---

### 5.2 Validação Completa dos Endpoints RESTful de Etapas (`/api/v2/teaching-stages/`) [Automatizável ✅]

#### Cenário 6 — CRUD completo de Etapas de Ensino via API v2

**Ação humana / Automatizada:**
- [x] **GET `/api/v2/teaching-stages/`**: Disparar requisição de listagem autenticada com token do cliente; verificar retorno HTTP 200 e paginação (`results`).
- [x] **POST `/api/v2/teaching-stages/`**: Criar uma nova etapa com payload `{"name": "1º Ano Ensino Médio", "code_export": "EM01"}`; verificar retorno HTTP 201 e que o campo `client` é associado automaticamente ao cliente do usuário.
- [x] **GET `/api/v2/teaching-stages/{id}/`**: Consultar a etapa criada pelo seu UUID; verificar retorno HTTP 200 com os dados corretos.
- [x] **PUT `/api/v2/teaching-stages/{id}/`**: Atualizar todos os campos da etapa; verificar retorno HTTP 200.
- [x] **PATCH `/api/v2/teaching-stages/{id}/`**: Atualizar parcialmente um campo (ex.: `code_export: "EM01-NOVO"`); verificar retorno HTTP 200 e persistência do valor.
- [x] **DELETE `/api/v2/teaching-stages/{id}/`**: Excluir a etapa pelo UUID; verificar retorno HTTP 204 No Content.
- [x] **Isolamento Multi-tenant**: Tentar acessar ou alterar via GET/PATCH/DELETE uma etapa pertencente a outro cliente; verificar retorno estrito **HTTP 404 Not Found**.

**Referência técnica (para automação):**
- URL: `/api/v2/teaching-stages/` e `/api/v2/teaching-stages/<uuid:pk>/`
- Suíte automatizada: `pytest fiscallizeon/api2/tests/test_integration_resources.py` (método `test_crud_com_token_e_isolamento_por_cliente`)
- Estado esperado: Operações 200/201/204 e 404 em registros de outros clientes

---

### 5.3 Validação Completa dos Endpoints RESTful de Códigos (`/api/v2/subject-codes/`) [Automatizável ✅]

#### Cenário 7 — CRUD completo de Códigos de Disciplina via API v2

**Ação humana / Automatizada:**
- [x] **GET `/api/v2/subject-codes/`**: Disparar listagem autenticada; verificar retorno HTTP 200.
- [x] **POST `/api/v2/subject-codes/`**: Criar código com `{"subject": "<uuid>", "code": "MAT-01", "unity": "<uuid_unidade>"}`; verificar retorno HTTP 201.
- [x] **Filtros de listagem**: Testar busca por `unity=<uuid>` e busca case-insensitive por `unity_name=centro`; verificar que apenas os códigos daquela unidade são listados.
- [x] **GET `/api/v2/subject-codes/{id}/`**: Consultar código pelo UUID; verificar retorno HTTP 200.
- [x] **PUT `/api/v2/subject-codes/{id}/`**: Atualizar código completo; verificar retorno HTTP 200.
- [x] **PATCH `/api/v2/subject-codes/{id}/`**: Atualizar parcialmente (ex.: alterar `code` para `"MAT-02"` ou `unity` para `null`); verificar retorno HTTP 200.
- [x] **DELETE `/api/v2/subject-codes/{id}/`**: Excluir o código pelo UUID; verificar retorno HTTP 204.
- [x] **Isolamento e Segurança**: Tentar vincular `unity` ou `subject` pertencentes a outro cliente; verificar retorno **HTTP 400 Bad Request**. Tentar acessar código de outro cliente; verificar retorno **HTTP 404 Not Found**.

**Referência técnica (para automação):**
- URL: `/api/v2/subject-codes/` e `/api/v2/subject-codes/<uuid:pk>/`
- Suíte automatizada: `pytest fiscallizeon/api2/tests/test_integration_resources.py` e `pytest fiscallizeon/integrations/tests/test_seb_delivery.py`
- Estado esperado: CRUD com sucesso, validação de permissões de escopo OAuth e bloqueio de dados de outro tenant

---

### 5.4 Resolução de Códigos no Endpoint de Resultados (`/api/v2/application-students-results/`) [Automatizável ✅]

#### Cenário 8 — Resolução contextual de `subject_id_erp` por unidade da turma do aluno

**Ação humana / Automatizada:**
- [x] Validado via suíte de testes de integração (`test_application_student_result_subject_code.py`).
- [x] Teste `test_codigo_da_turma_da_aplicacao_e_escolhido`: aluno da turma vinculada à Unidade A recebe o código da Unidade A, e nunca o da Unidade B.
- [x] Confirmado que o código de uma unidade nunca vaza para o aluno da outra unidade (9/9 testes passando com 100% de sucesso).

**Referência técnica (para automação):**
- URL: `/api/v2/application-students-results/?subject=Português%20SEB`
- Resposta esperada: `results[0].subject_id_erp == "PORT-CENTRO"`, `results[1].subject_id_erp == "PORT-SUL"`
- Fixture: Aluno A vinculado a turma da Unidade Centro, Aluno B vinculado a turma da Unidade Sul

---

#### Cenário 9 — Aluno de unidade sem código específico cadastrado

**Ação humana / Automatizada:**
- [x] Validado via suíte de testes de integração (`test_application_student_result_subject_code.py`).
- [x] Teste `test_sem_codigo_da_unidade_nao_retorna_codigo_global`: quando a disciplina tem código contextual por unidade, um aluno cuja unidade não tem código cadastrado recebe `subject_id_erp: null` (não assume código global indevidamente).

**Referência técnica (para automação):**
- URL: `/api/v2/application-students-results/`
- Resposta esperada: `"subject_id_erp": null` para aluno sem código na sua respectiva unidade

---

#### Cenário 10 — Filtros por `teaching_stage` e `subject` na API v2

**Ação humana / Automatizada:**
- [x] Consultar `/api/v2/application-students-results/?teaching_stage=1º%20ano%20em&subject=matemática` (letras minúsculas).
- [x] Confirmar que a busca ignora caixa alta/baixa (case-insensitive) e filtra os resultados exatamente pelos parâmetros informados.

**Referência técnica (para automação):**
- URL: `/api/v2/application-students-results/?teaching_stage=1º%20ano%20em&subject=matemática`
- Resposta esperada: HTTP 200 com array `results` contendo apenas notas da etapa e disciplina informadas

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] **Coluna Unidade na Tabela**: A coluna "Unidade" foi incorporada à tabela com alinhamento e truncamento Tailwind adequados (`tw-truncate`).
- [x] **Botão "Cadastrar outro código"**: Botão secundário na cor branca com texto laranja e borda cinza posicionado entre "Visualizar" e "Remover".
- [x] **Opção "Todas" no Modal**: O select de unidade exibe o label `"Todas"` como primeira opção limpa.
- [x] **Regressão de layout em `/disciplinas/disciplinas/`**: Listagem de disciplinas extras preserva padding lateral (`ard cer dcv`), não colando nas bordas da janela.
- [x] **Documentação Swagger OpenAPI**: Os blocos `"Etapas"` (`/api/v2/teaching-stages/`) e `"Códigos de disciplinas"` (`/api/v2/subject-codes/`) aparecem categorizados no Swagger UI com todas as operações (GET, POST, PUT, PATCH, DELETE).

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE] Diagnóstico de Schema Drift Resolvido
> Durante a execução dos testes na branch local, foi identificado um erro de banco `IntegrityError: null value in column "has_new_application_experience" of relation "accounts_historicaluser" violates not-null constraint`.
> **Diagnóstico:** A coluna era resíduo de migração de outra branch paralela (Schema Drift) e não pertence a esta branch.
> **Ação executada:** Foi utilizado o workflow seguro `/qa-limpar-coluna-residual` (`drop_residual_column.py --execute`), limpando a coluna das tabelas locais sem perda de dados da tarefa atual.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE] Padrão de Status Code para Duplicidade
> Atualmente a rejeição de duplicidade em códigos de disciplina retorna HTTP 404 com mensagem descritiva (conforme especificação e implementação original). Em evoluções futuras da API pública, pode ser avaliado padronizar retornos de duplicidade como HTTP 409 Conflict ou HTTP 400 Bad Request.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
🔗 **[Ver Mapeamento de Tela (subject_code_list_create.md)](docs/tests/usability/subject_code_list_create.md)**

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo:** Inicialmente a tela web exibia disciplinas raiz de outros clientes no catálogo e não permitia cadastrar múltiplos códigos por unidade diretamente pela UI. Essas melhorias foram implementadas nos commits mais recentes (`007df608de` e `6daea70cb6`) e validadas com sucesso.
- **Eficiência da automação:** A cobertura por testes unitários e de integração (com 15 testes passando em `test_integration_resources.py` e `test_seb_delivery.py` e 9 testes em `test_application_student_result_subject_code.py`) permitiu validar todos os verbos HTTP da API pública v2 sem necessidade de chamadas manuais repetitivas via Postman/cURL.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- Para endpoints RESTful documentados via OpenAPI/Swagger, a execução direcionada da suíte de testes de integração (`test_integration_resources.py`) garante 100% de cobertura nos métodos GET, POST, PUT, PATCH, DELETE e no isolamento multi-tenant de forma muito mais rápida e confiável do que cliques manuais na UI do Swagger.

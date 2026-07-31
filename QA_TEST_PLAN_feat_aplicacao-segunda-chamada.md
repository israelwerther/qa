# QA Test Plan — feat/aplicacao-segunda-chamada

---

## 0. Metadados de QA

| Campo | Valor |
|-------|-------|
| **Data** | 2026-07-31 |
| **Branch** | `feat/aplicacao-segunda-chamada` |
| **Task Nature** | `[Business Feature]` |
| **Feature Area** | Applications / Exams |
| **Risk Level** | **Medium** — novo campo no model, nova API, modal com integração Vue; sem alteração de fluxo de alunos existente |
| **OpenSpec Quality** | ⭐⭐⭐⭐⭐ (5/5) — Proposta, design, spec e tasks exaustivos, com decisões fechadas explícitas e referências de implementação |

---

## 1. Resumo das Alterações

### Backend

- **Model `Application`:** novo `BooleanField is_second_call` (default `False`). **Sem FK** para `Application` ou `Exam`.
- **Migration:** `0117_application_is_second_call.py`.
- **Service:** `has_missed_at_exam(exam)` em `application_student_service.py` — critério canônico de ausência (via `annotate_is_present_with_subquery`), alunos ativos, ano atual, dedupe por student.
- **Nova API:** `ApplicationStudentMissedAtExamListAPIView` em `/aplicacoes/api/application-students/missed-at-exam/<exam_id>/` — somente leitura; multi-tenant na view.
- **Novo serializer:** `ApplicationStudentMissedAtExamSerializer` — retorna `id` e `student` (id, name, enrollment_number, school_class, unity).
- **Nova ListAPIView de cadernos:** `ExamSecondCallListView` — endpoint `/cadernos/api/listar/segunda-chamada/`; filtra cadernos com `date__year` atual, `student_stats_permission_date` liberado e ≥1 ausente.
- **Filtro removido/movido:** `ExamListFilter.has_valid_application` de `exams/filters.py` foi substituído por view dedicada.

> [!NOTE]
> `exams/filters.py` foi **deletado** nesta branch. A listagem de cadernos para o modal não usa `ExamListFilter` via query param, mas sim a nova `ExamSecondCallListView` (`exams_api_second_call_list`). Isso diverge levemente da proposta inicial, que mencionava `ExamListFilter.has_valid_application`.

### Frontend

- **Redesign** da seção "Informações básicas" em `application_create_update.html` (~L90–L256) — cards de categoria, campos de data/hora.
- **Toggle "Prova de 2ª chamada"** na seção de alunos: `#is_second_call_toggle` + campo hidden `is_second_call`.
- **Card de prova anterior selecionada** com contagem de ausentes e link "Abrir caderno".
- **Modal fullscreen** `select_previous_exam.html` (id `selectPreviousExamModal`): busca de cadernos (coluna esquerda) + listagem de ausentes com filtros por unidade/turma e checkboxes (coluna direita).
- **Estado Vue** completo no host (`secondCallModal.*`, `previousExamSelection`, `isSecondCall`).

---

## 2. Escopo — In / Out

### ✅ In Scope

- Toggle `is_second_call` na criação e edição de aplicação.
- Modal `selectPreviousExamModal`: abrir, buscar cadernos, carregar ausentes, filtrar por unidade/turma, selecionar/desselecionar, confirmar.
- Preenchimento automático da seção "Alunos que realizarão a prova" após confirmação.
- API `/missed-at-exam/<exam_id>/`: autenticação, multi-tenant, dedupe, retorno correto.
- API `/cadernos/api/listar/segunda-chamada/`: filtro `has_valid_application` (ausentes + ano atual + `student_stats_permission_date`).
- Persistência de `is_second_call=True` no `Application` após save.
- Redesign visual da seção "Informações básicas".

### ❌ Out of Scope

- FK de "prova anterior" em `Application` ou `Exam` — não existe por design.
- Alterações em categoria, datas, turmas ao ativar o toggle.
- Endpoint de inserção em massa de ausentes — não existe por design.
- Redesign das demais seções do formulário (Alunos, Configurações Avançadas etc.).
- Cascata de 2ª → 3ª chamada.
- Relatórios autônomos de ausentes.

---

## 3. Navegação e Camada Técnica

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Criar aplicação | "Criar" (menu Aplicações) | `/aplicacoes/cadastrar/` | `applications:applications_create` |
| Editar aplicação | — (botão na lista de aplicações) | `/aplicacoes/<pk>/editar` | `applications:applications_update` |
| API ausentes (prévia) | — (fetch Vue interno) | `/aplicacoes/api/application-students/missed-at-exam/<exam_id>/` | `applications:api_application_students_missed_at_exam` |
| API cadernos 2ª chamada | — (fetch Vue interno) | `/cadernos/api/listar/segunda-chamada/` | `exams:exams_api_second_call_list` |
| Seção Alunos do form | "Alunos que realizarão a prova" `[verificar]` | — (mesma página) | — |

---

## 4. Testes Automatizados e Setup de Dados

### Comando para rodar testes automatizados

```bash
# Roda testes do módulo applications
./scripts/tests/run-tests.sh --no-tty fiscallizeon/applications/

# Testes específicos de service e API (quando criados — tasks 5.1–5.4)
./scripts/tests/run-tests.sh --no-tty fiscallizeon/applications/tests/ fiscallizeon/exams/
```

> [!IMPORTANT]
> As tasks 5.1–5.4 do `tasks.md` (testes automatizados) ainda estão como `[ ]` — **não foram implementadas**. Este plano cobre o QA manual e documenta os fixtures para quando forem criadas.

### Persona para os testes manuais

> **Coordenadora da Unidade A** — usuária com `CoordinationMember` associada a uma `SchoolCoordination` que possui cadernos com aplicações no ano corrente e alunos ausentes.

### Fixture mínima — setup via `mixer.blend()`

```python
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from django.utils import timezone
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination, CoordinationMember
from fiscallizeon.exams.models import Exam
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.students.models import Student
from fiscallizeon.classes.models import SchoolClass, Grade
from django.core import management

management.call_command('initial_configs')

# Persona: Coordenadora
coord = mixer.blend(User)
coord.user_permissions.set(Permission.objects.all())
coord.set_password('senha')
coord.save()

# Tenant
client = mixer.blend(Client, has_exam_elaboration=True)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)
mixer.blend(CoordinationMember, user=coord, coordination=coordination)

# Caderno da 1ª chamada
exam_1st = mixer.blend(Exam, is_abstract=False, not_applicable=False)
exam_1st.coordinations.add(coordination)

# Application já encerrada no ano atual com resultado liberado
application_1st = mixer.blend(
    Application,
    exam=exam_1st,
    date=timezone.localdate(),
    student_stats_permission_date=timezone.localdate(),  # liberado hoje
)

# Aluno ausente (missed=True faz is_present=False via annotate)
student_absent = mixer.blend(Student, client=client, user__is_active=True)
mixer.blend(ApplicationStudent, application=application_1st, student=student_absent, missed=True)

# Aluno presente (para confirmar exclusão da listagem)
student_present = mixer.blend(Student, client=client, user__is_active=True)
mixer.blend(ApplicationStudent, application=application_1st, student=student_present, missed=False)
```

---

## 5. Roteiro de Testes com Checkboxes

### 5.1 Configuração — Toggle "Prova de 2ª chamada" [Automatizável ✅]

**Persona:** Coordenadora da Unidade A, logada no sistema.

#### Cenário 1 — Toggle desligado por padrão

- [x] Acessar `/aplicacoes/cadastrar/` e confirmar que o toggle `#is_second_call_toggle` está **desmarcado** por padrão.
- [x] Confirmar que o campo oculto `input[name="is_second_call"]` tem valor `False`.
- [x] Confirmar que o container `div[v-show="isSecondCall"]` **não é exibido** (estilo `display: none`).

#### Cenário 2 — Toggle ativado exibe CTA de seleção [Automatizável ✅]

- [ ] Clicar no toggle `#is_second_call_toggle`.
- [ ] Confirmar que o container `div[v-show="isSecondCall"]` **fica visível**.
- [ ] Confirmar que o campo oculto `input[name="is_second_call"]` tem valor `True`.
- [ ] Confirmar que o texto "Prova de 2ª chamada" aparece no rótulo `label[for="is_second_call_toggle"]`.
- [ ] Confirmar que o CTA de seleção de prova anterior aparece (sem caderno selecionado ainda).

> **⚠️ Screenshot solicitado:** Como o CTA de seleção de prova anterior é exibido quando o toggle está ativo e nenhum caderno foi selecionado ainda?

#### Cenário 3 — Toggle desativado esconde elementos [Automatizável ✅]

- [ ] Com toggle ativo, clicar novamente para desativar.
- [ ] Confirmar que o container `div[v-show="isSecondCall"]` some.
- [ ] Confirmar que o campo oculto retorna ao valor `False`.

---

### 5.2 Modal "Selecionar prova anterior" — Abertura e busca [Automatizável ✅]

**Persona:** Coordenadora com cadernos elegíveis no banco (fixture acima).

#### Cenário 4 — Modal abre via CTA [Automatizável ✅]

- [ ] Com toggle ativo, clicar no CTA de seleção de prova anterior.
- [ ] Confirmar que o modal `#selectPreviousExamModal` fica visível (classe `.show` ou `display: block`).
- [ ] Confirmar que o header exibe botões de Voltar e Fechar (X).
- [ ] Confirmar que a coluna esquerda exibe "Cadernos" e o input de busca.
- [ ] Confirmar que a coluna direita exibe "Ausentes" sem caderno selecionado.
- [ ] Confirmar que o fetch inicial de cadernos acontece com a URL `exams:exams_api_second_call_list`.

#### Cenário 5 — Lista de cadernos carrega [Automatizável ✅]

- [ ] Aguardar o carregamento e confirmar que cadernos com ausentes elegíveis aparecem na lista.
- [ ] Confirmar que o estado de loading (`secondCallModal.loadingExams`) desaparece após o fetch.

#### Cenário 6 — Busca por nome de caderno [Automatizável ✅]

- [ ] Digitar parte do nome de um caderno existente no input `input[v-model="secondCallModal.searchTerm"]`.
- [ ] Confirmar que o fetch é disparado com debounce (não instantâneo).
- [ ] Confirmar que os resultados filtrados aparecem na lista.
- [ ] Limpar o campo e confirmar que a lista retorna ao estado default.

#### Cenário 7 — Nenhum caderno disponível [Apenas Manual 👁]

- [ ] Com banco sem cadernos elegíveis (sem `student_stats_permission_date` liberado ou sem ausentes no ano atual), abrir o modal.
- [ ] Confirmar mensagem: **"Nenhum caderno com ausentes elegíveis no ano atual."**

---

### 5.3 Seleção de caderno e exibição de ausentes [Automatizável ✅]

**Persona:** Coordenadora com fixture completa.

#### Cenário 8 — Selecionar caderno carrega ausentes

- [ ] Clicar em um caderno da lista.
- [ ] Confirmar que o caderno clicado recebe destaque visual (classe `tw-bg-[#FFF4EC]`).
- [ ] Confirmar que `"Caderno selecionado: <nome>"` aparece na coluna direita.
- [ ] Confirmar que o estado de loading de ausentes aparece (`"Carregando ausentes…"`).
- [ ] Aguardar o fetch para `/aplicacoes/api/application-students/missed-at-exam/<exam_id>/`.
- [ ] Confirmar que a lista de ausentes é preenchida com nome, matrícula e, quando disponível, turma/unidade.
- [ ] **Confirmar que o aluno PRESENTE da fixture NÃO aparece na lista.**

#### Cenário 9 — Filtro por unidade/turma [Automatizável ✅]

- [ ] Com ausentes carregados, confirmar que os chips de unidade aparecem (se houver alunos com unidade).
- [ ] Clicar em um chip de unidade.
- [ ] Confirmar que apenas alunos daquela unidade ficam visíveis na lista `ul > li`.
- [ ] Clicar novamente no chip (deselecionar) e confirmar que a lista retorna à exibição completa.
- [ ] Repetir para filtro por turma.

#### Cenário 10 — Caderno sem ausentes elegíveis [Automatizável ✅]

- [ ] Selecionar um caderno onde todos os alunos estão presentes.
- [ ] Confirmar mensagem: **"Nenhum aluno ausente elegível neste caderno."**
- [ ] Confirmar que o botão "Adicionar alunos não presentes" fica desabilitado (`:disabled`).

---

### 5.4 Confirmação e preenchimento do formulário [Automatizável ✅]

**Persona:** Coordenadora com ausentes carregados no modal.

#### Cenário 11 — Confirmar ausentes preenche seção de alunos

- [ ] Com ausentes carregados e pelo menos um selecionado (checkbox marcado), clicar em **"Adicionar alunos não presentes"**.
- [ ] Confirmar que o modal fecha.
- [ ] Confirmar que o card de prova anterior (`template[v-if="previousExamSelection"]`) aparece com o nome do caderno selecionado.
- [ ] Confirmar que a contagem de ausentes (`X alunos ausentes`) bate com os checkboxes selecionados.
- [ ] Confirmar que os alunos aparecem na seção "Alunos que realizarão a prova" (hiddens `input[name="students"]`).

#### Cenário 12 — Desselecionar aluno antes de confirmar [Automatizável ✅]

- [ ] No modal com ausentes carregados, desmarcar o checkbox de um aluno.
- [ ] Confirmar que `secondCallModal.selectedStudentsIds` não contém mais o `student.id` deselecionado.
- [ ] Confirmar que ao confirmar, esse aluno **não** aparece na seção de alunos do formulário.

#### Cenário 13 — Botão "Cancelar" fecha modal sem alterar estado [Automatizável ✅]

- [ ] Abrir o modal, selecionar um caderno, não confirmar, clicar em **"Cancelar"**.
- [ ] Confirmar que o modal fecha.
- [ ] Confirmar que `previousExamSelection` permanece `null` (nenhum caderno foi salvo no card).
- [ ] Confirmar que os alunos do formulário não foram alterados.

#### Cenário 14 — Alterar prova anterior [Apenas Manual 👁]

- [ ] Com um caderno já confirmado (card visível), clicar no botão "Alterar…".
- [ ] Confirmar que o modal abre **com estado limpo** (busca vazia, sem caderno selecionado, sem ausentes).
- [ ] Selecionar um caderno diferente e confirmar.
- [ ] Confirmar que o card atualiza com o novo caderno e a nova contagem de ausentes.

---

### 5.5 Persistência no save do formulário [Automatizável ✅]

**Persona:** Coordenadora, formulário preenchido com `is_second_call=True` e alunos ausentes selecionados.

#### Cenário 15 — Salvar aplicação com toggle ativo persiste `is_second_call=True`

- [ ] Preencher todos os campos obrigatórios do formulário.
- [ ] Ativar toggle de 2ª chamada.
- [ ] Submeter o formulário.
- [ ] Confirmar via Django Admin ou `Application.objects.get(pk=...).is_second_call` que o campo é `True`.
- [ ] Confirmar que os `ApplicationStudent` foram criados via fluxo normal do form (sem endpoint dedicado).

#### Cenário 16 — Salvar sem toggle ativo persiste `is_second_call=False`

- [ ] Criar aplicação sem ativar o toggle.
- [ ] Confirmar que `Application.is_second_call = False`.

#### Cenário 17 — Editar aplicação existente com toggle ativo

- [ ] Editar uma aplicação já existente (com `is_second_call=False`).
- [ ] Ativar o toggle e salvar.
- [ ] Confirmar que `is_second_call` foi atualizado para `True`.

---

### 5.6 API — Segurança e Multi-tenant [Automatizável ✅]

**Persona A:** Coordenadora do Client A. **Persona B:** Coordenadora do Client B.

#### Cenário 18 — API retorna apenas ausentes do escopo da coordenação

- [ ] Como Coordenadora A, chamar `GET /aplicacoes/api/application-students/missed-at-exam/<exam_do_client_A>/`.
- [ ] Confirmar resposta HTTP 200 com lista de ausentes somente do client A.
- [ ] Confirmar que alunos de outras coordenações fora do escopo não aparecem.

#### Cenário 19 — Exam fora do client retorna lista vazia (sem leak cross-tenant)

- [ ] Como Coordenadora A, chamar a API com `exam_id` pertencente ao Client B.
- [ ] Confirmar resposta HTTP 200 com lista **vazia** (ou 403/404 — verificar o comportamento real).

> **⚠️ Screenshot/Resposta API solicitada:** Qual o HTTP status quando o exam não pertence ao client do usuário — 200 vazio, 403 ou 404?

#### Cenário 20 — Endpoint não aceita chamadas não autenticadas

- [ ] Sem sessão de login, chamar `GET /aplicacoes/api/application-students/missed-at-exam/<qualquer_id>/`.
- [ ] Confirmar redirecionamento para login (302) ou HTTP 403.

#### Cenário 21 — API de cadernos 2ª chamada filtra corretamente

- [ ] Chamar `GET /cadernos/api/listar/segunda-chamada/` como coordenadora autenticada.
- [ ] Confirmar que apenas cadernos com `application.date__year = ano_atual`, `student_stats_permission_date <= hoje` e ≥1 ausente aparecem.
- [ ] Confirmar que cadernos sem aplicações ou sem ausentes **não aparecem**.
- [ ] Chamar com `?search=<nome>` e confirmar busca textual.

---

### 5.7 Paginação Infinita no modal [Apenas Manual 👁]

#### Cenário 22 — Scroll carrega mais cadernos

- [ ] Abrir o modal com muitos cadernos disponíveis.
- [ ] Rolar a lista de cadernos até o final.
- [ ] Confirmar que "Carregando mais…" aparece e novos cadernos são adicionados.

---

### 5.8 Critérios de elegibilidade dos cadernos na listagem [Automatizável ✅]

> Valida as regras de filtro de `ExamSecondCallListView.get_queryset()`. Cada cenário cria uma situação que **deve excluir** o caderno da lista.

**Persona:** Coordenadora logada (para cenários 23–27) e Professor logado (cenário 28).

#### Cenário 23 — Caderno `not_applicable=True` não aparece [Automatizável ✅]

```python
exam_not_applicable = mixer.blend(Exam, not_applicable=True, is_abstract=False)
exam_not_applicable.coordinations.add(coordination)
mixer.blend(Application, exam=exam_not_applicable, date=timezone.localdate(), student_stats_permission_date=timezone.localdate())
```

- [ ] Chamar `GET /cadernos/api/listar/segunda-chamada/`.
- [ ] Confirmar que o caderno com `not_applicable=True` **não** aparece na lista.

#### Cenário 24 — Caderno abstrato (`is_abstract=True`) não aparece [Automatizável ✅]

```python
exam_abstract = mixer.blend(Exam, not_applicable=False, is_abstract=True)
exam_abstract.coordinations.add(coordination)
```

- [ ] Confirmar que o caderno abstrato **não** aparece na lista.

#### Cenário 25 — Caderno sem `student_stats_permission_date` liberado não aparece [Automatizável ✅]

> **Este é o critério mais provável de falso negativo em produção**: coordenação consulta o modal logo após a prova, mas o resultado ainda não foi liberado.

```python
from datetime import timedelta
exam_future = mixer.blend(Exam, is_abstract=False, not_applicable=False)
exam_future.coordinations.add(coordination)
mixer.blend(
    Application,
    exam=exam_future,
    date=timezone.localdate(),
    student_stats_permission_date=timezone.localdate() + timedelta(days=1),  # amanhã — não liberado
)
```

- [ ] Abrir o modal como coordenadora.
- [ ] Confirmar que o caderno com resultado **não liberado** (`student_stats_permission_date` no futuro) **não aparece** na lista.
- [ ] Confirmar que o caderno aparece **após** a data de liberação ser ajustada para hoje ou passado.

#### Cenário 26 — Caderno com aplicação fora do ano atual não aparece [Automatizável ✅]

```python
from datetime import date
exam_old = mixer.blend(Exam, is_abstract=False, not_applicable=False)
exam_old.coordinations.add(coordination)
mixer.blend(
    Application,
    exam=exam_old,
    date=date(2024, 6, 1),  # ano passado
    student_stats_permission_date=date(2024, 6, 2),
)
```

- [ ] Confirmar que o caderno com aplicação de ano anterior **não aparece** na lista.

#### Cenário 27 — Caderno somente com alunos presentes não aparece [Automatizável ✅]

```python
exam_only_present = mixer.blend(Exam, is_abstract=False, not_applicable=False)
exam_only_present.coordinations.add(coordination)
app_only_present = mixer.blend(Application, exam=exam_only_present, date=timezone.localdate(), student_stats_permission_date=timezone.localdate())
student_p = mixer.blend(Student, client=client, user__is_active=True)
mixer.blend(ApplicationStudent, application=app_only_present, student=student_p, missed=False)
```

- [ ] Confirmar que o caderno onde **todos** os alunos estão presentes **não aparece** na lista.

#### Cenário 28 — Usuário Professor só vê cadernos com vínculo a ele [Automatizável ✅]

> **Regra de produto:** se `user.user_type == settings.TEACHER`, o queryset aplica `.filter(examteachersubject__teacher_subject__teacher__user=user)`. Professor não vê cadernos de outros professores.

```python
from fiscallizeon.inspectors.models import Inspector, TeacherSubject
from fiscallizeon.exams.models import ExamTeacherSubject

teacher_user = mixer.blend(User)
teacher_user.user_type = settings.TEACHER
teacher_user.save()

exam_with_teacher = mixer.blend(Exam, is_abstract=False, not_applicable=False)
exam_with_teacher.coordinations.add(coordination)
mixer.blend(Application, exam=exam_with_teacher, date=timezone.localdate(), student_stats_permission_date=timezone.localdate())
# Criar ExamTeacherSubject vinculando o professor ao caderno
teacher = mixer.blend(Inspector, user=teacher_user)  # Inspector ou TeacherSubject — [verificar]
# mixer.blend(ExamTeacherSubject, exam=exam_with_teacher, teacher_subject__teacher=teacher)

exam_without_teacher = mixer.blend(Exam, is_abstract=False, not_applicable=False)
exam_without_teacher.coordinations.add(coordination)
mixer.blend(Application, exam=exam_without_teacher, date=timezone.localdate(), student_stats_permission_date=timezone.localdate())
```

- [ ] Autenticar como professor (`teacher_user`).
- [ ] Chamar `GET /cadernos/api/listar/segunda-chamada/`.
- [ ] Confirmar que `exam_with_teacher` **aparece** na lista.
- [ ] Confirmar que `exam_without_teacher` (sem vínculo com o professor) **não aparece**.

> **⚠️ Verificar:** O model exato de vínculo professor–caderno (`ExamTeacherSubject`, `TeacherSubject`, `Inspector`) precisa ser confirmado no código para montar o fixture corretamente. O fixture acima está **marcado como [verificar]**.

---

### 5.9 Critério de ausência por modalidade — Risco 🔴 do Pitch [Automatizável ✅]

> O pitch original elencou como risco crítico: *"o critério de ausência varia por modalidade — para provas online `missed=True`; para presenciais `is_omr=False`"*. A implementação usa `annotate_is_present_with_subquery + is_present=False`, que deve cobrir ambos os casos. **Estes cenários validam explicitamente esse critério.**

**Persona:** Coordenadora com fixture específica por modalidade.

#### Cenário 29 — Ausente em aplicação online (`missed=True`) aparece corretamente [Automatizável ✅]

```python
# Simula aluno que não compareceu em prova online — campo missed=True
exam_online = mixer.blend(Exam, is_abstract=False, not_applicable=False)
exam_online.coordinations.add(coordination)
app_online = mixer.blend(Application, exam=exam_online, category=Application.ONLINE, date=timezone.localdate(), student_stats_permission_date=timezone.localdate())
student_online_absent = mixer.blend(Student, client=client, user__is_active=True)
mixer.blend(ApplicationStudent, application=app_online, student=student_online_absent, missed=True)
```

- [ ] Chamar `GET /aplicacoes/api/application-students/missed-at-exam/<exam_online_id>/`.
- [ ] Confirmar que `student_online_absent` **aparece** na lista de ausentes.

#### Cenário 30 — Ausente em aplicação presencial (OMR não processado) aparece corretamente [Apenas Manual 👁]

> Para provas presenciais, um aluno sem OMR processado pode ser marcado como ausente canonicamente mesmo que `missed=False`. O `annotate_is_present_with_subquery` avalia presença via respostas/OMR — não apenas pelo campo `missed`.

- [ ] Criar aplicação presencial com aluno sem respostas submetidas (sem OMR, sem resposta corrigida).
- [ ] Chamar a API de ausentes para o caderno.
- [ ] Confirmar que o aluno sem resposta **aparece** na lista (ausente canônico, não apenas `missed=True`).
- [ ] Confirmar que um aluno com respostas submetidas **não aparece** na lista.

> **⚠️ Atenção:** Se o Cenário 30 **falhar** (aluno sem OMR não aparece como ausente), indica bug no critério de ausência — a lógica de `annotate_is_present_with_subquery` precisa ser auditada. Documentar com `[Backend Logic]`.

#### Cenário 31 — Aluno inativo não aparece como ausente [Automatizável ✅]

```python
student_inactive = mixer.blend(Student, client=client, user__is_active=False)
mixer.blend(ApplicationStudent, application=application_1st, student=student_inactive, missed=True)
```

- [ ] Confirmar que `student_inactive` (com `user__is_active=False`) **não aparece** na API de ausentes, mesmo com `missed=True`.

#### Cenário 32 — Aluno ausente em múltiplas aplicações do mesmo caderno aparece uma única vez [Automatizável ✅]

> Valida a regra de dedupe por `student` (regra 2.6 do service).

```python
# Duas applications do mesmo caderno, aluno ausente em ambas
app_a = mixer.blend(Application, exam=exam_1st, date=timezone.localdate(), student_stats_permission_date=timezone.localdate())
app_b = mixer.blend(Application, exam=exam_1st, date=timezone.localdate(), student_stats_permission_date=timezone.localdate())
student_dup = mixer.blend(Student, client=client, user__is_active=True)
mixer.blend(ApplicationStudent, application=app_a, student=student_dup, missed=True)
mixer.blend(ApplicationStudent, application=app_b, student=student_dup, missed=True)
```

- [ ] Chamar `GET /aplicacoes/api/application-students/missed-at-exam/<exam_1st_id>/`.
- [ ] Confirmar que `student_dup` aparece **exatamente uma vez** na lista (dedupe funcionando).

---

## 6. Validação Visual e de Layout [Apenas Manual 👁]

> Comparar com [Figma node 13884:94433](https://www.figma.com/design/rLxKONkzOksH4OZTBN6jOy/Lory-Panel?node-id=13884-94433) (redesign da seção Informações Básicas) e [13884:92113](https://www.figma.com/design/rLxKONkzOksH4OZTBN6jOy/Lory-Panel?node-id=13884-92113) (fluxo completo 2ª chamada).

- [ ] Tirar screenshot da seção "Informações básicas" no estado padrão e comparar com Figma `13884:94433`.
- [ ] Tirar screenshot da seção com toggle ativo + caderno selecionado e comparar com Figma `13884:92113`.
- [ ] Tirar screenshot do modal aberto (coluna esquerda com cadernos) e comparar com Figma.
- [ ] Tirar screenshot do modal com ausentes carregados (coluna direita) e comparar com Figma.
- [ ] Verificar responsividade no modal: em tela pequena, colunas empilham (`lg:tw-flex-row → tw-flex-col`).
- [ ] Confirmar que o modal ocupa tela cheia (`modal-fullscreen`).
- [ ] Confirmar que header e footer do modal são sticky ao rolar o body.
- [ ] Confirmar que o card de prova anterior exibe nome, categoria e contagem corretamente após confirmar.
- [ ] Confirmar que seções fora de "Informações básicas" (ex.: Configurações avançadas, seção de questões) **não foram redesenhadas**.

---

## 7. Bugs e Observações

> Use os alertas abaixo para documentar bugs encontrados durante a execução.

> [!WARNING]
> **Formato obrigatório para bugs:**
> 1. **Título** — descrição clara.
> 2. **Contexto/Root Cause** — por que acontece tecnicamente (se conhecido).
> 3. **Comportamento Esperado** — o que deveria ocorrer.
> 4. **Workaround (Gambiarra temporária)** — alternativa para continuar o teste.
> Categorize com tags: `[UX/UI]`, `[Backend Logic]`, `[Database]`, `[Spec Gap]`.

_Reserve este espaço durante a execução do plano._

> [!WARNING]
> **Bug 1: Filtro de data de liberação falha no mesmo dia devido a comparação de `Date` com `DateTime`**
> - **Contexto/Root Cause:** O campo `student_stats_permission_date` é um `DateTimeField`. Em `ExamSecondCallListView` (linha 229), a query usa `today = timezone.localdate()` (`Date`). Quando o Django compara o `DateTimeField` `<= today`, ele assume `today` às `00:00:00`. Logo, qualquer aplicação cuja liberação ocorra no próprio dia atual após meia-noite (ex: 13:20) não aparece na listagem, pois 13:20 não é `<= 00:00:00`.
> - **Comportamento Esperado:** A query deveria comparar com `now = timezone.now()` para que exames liberados no dia de hoje já fiquem disponíveis na mesma hora, ou usar `.date()` na anotação, garantindo que o exame liberado hoje apareça.
> - **Workaround:** Para testar a listagem, defina a data de liberação do resultado no Admin para *ontem*.
> - **Tags:** `[Backend Logic]`

> [!WARNING]
> **Bug 2: Inconsistência visual no Toggle de "Prova de 2ª chamada"**
> - **Contexto:** O switch implementado usa uma estrutura customizada (`toggle-switch` com `span.slider`), que difere visualmente do padrão predominante no sistema (como o toggle "É avaliação do tipo PAS?").
> - **Comportamento Esperado:** Utilizar a classe padrão do projeto (`custom-control custom-switch`) para manter a uniformidade visual da interface.
> - **Tags:** `[UX/UI]` 

---

## 8. Melhorias Futuras e Tech Debt

> [!NOTE]
> **[Spec Gap]** O comportamento de multi-tenant quando `exam_id` não pertence ao client retorna lista vazia (200) ao invés de 403/404. Considerar resposta mais explícita para auxiliar no diagnóstico de integrações futuras.

> [!NOTE]
> **[Spec Gap]** A prop `search_fields` do `ExamSecondCallListView` está configurada para `('name',)` (busca por nome). A spec menciona "Busca textual no modal além do filtro default — mantém `has_valid_application=true` ao pesquisar?" como questão em aberto. Confirmar com produto se a busca textual deve continuar filtrando somente cadernos com ausentes.

> [!NOTE]
> **[Tech Debt]** Testes automatizados (tasks 5.1–5.5 do `tasks.md`) ainda não foram implementados. Criar:
> - `test_has_missed_at_exam_service.py` — regras 2.1–2.7 da spec + cenários 29–32 (modalidade online/presencial, aluno inativo, dedupe)
> - `test_application_second_call_api.py` — multi-tenant, exam fora do escopo
> - `test_exam_second_call_list_view.py` — critérios de elegibilidade: `not_applicable`, `is_abstract`, `student_stats_permission_date`, ano atual, só-presentes, filtro por professor (cenários 23–28)

> [!NOTE]
> **[UX/UI]** O toggle "Prova de 2ª chamada" aparece na seção "Alunos que realizarão a prova" (L360), enquanto o redesign do Figma `13884:94433` o coloca na seção "Informações básicas". Verificar se houve decisão de produto para essa diferença de posicionamento ou se é divergência de implementação.

> [!CAUTION]
> **[Backend Logic — Risco 🔴 do Pitch]** O critério de ausência canônico (`annotate_is_present_with_subquery + is_present=False`) precisa ser validado **explicitamente** para provas online (`missed=True`) e presenciais (sem OMR/resposta). Se o Cenário 30 falhar, há risco de alunos incorretos na listagem de 2ª chamada. Ver cenários 29–32.

> [!NOTE]
> **[Spec Gap / Produto]** O vínculo entre a aplicação de 2ª chamada e o caderno original **não é persistido** (decisão de produto). Isso significa que, ao editar uma aplicação de 2ª chamada já salva, o card "Caderno anterior" não é exibido — a coordenação perde o contexto de qual caderno foi usado. Avaliar se exibir `is_second_call=True` com algum indicador visual na edição seria útil.

---

## 8.1 Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [ ] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.

🔗 **[Ver Mapeamento de Tela](../docs/tests/usability/application_create_update.md)**

---

## 9. Retrospectiva de QA

> _Preencher ao final da sessão de QA._

- **Principal gargalo durante os testes:** _a preencher_
- **Houve muitas idas e vindas com o dev?** _a preencher_
- **Como o fluxo de dev/QA poderia ter sido melhor?** _a preencher_

---

> **Gerado por:** Antigravity QA Test Plan Generator (Prompt V2)
> **Conversa ID:** `899a3764-9564-4f50-acfc-d0f2c1a4f941`

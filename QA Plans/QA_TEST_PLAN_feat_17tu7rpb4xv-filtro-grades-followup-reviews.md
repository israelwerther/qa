# QA Test Plan - Recorte por Série no Card e Fila de Revisão de Cadernos (Followup & Django)

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-11-11 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Provas & Acompanhamento de Desempenho (Fila de Revisão / Followup Reviews) |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5/5 estrelas — proposal, design, spec e tasks alinhadas entre repositórios) |
| **Branch Backend (lizeedu):** | `feat/17tu7rpb4xv-filtro-grades-followup-reviews` |
| **Branch Analytics (lize-analytics):** | `feat/17tu7rpb4xv-filtro-grades-followup-reviews` |
| **Card ClickUp:** | [17tu7rpb4xv — Ajustar dados do card de revisão no followup](https://app.clickup.com/t/3120759/17tu7rpb4xv) |
| **PRs Relacionados:** | [LizeEdu #2315](https://github.com/LizeEdu/lizeedu/pull/2315) / [Lize Analytics #17](https://github.com/LizeEdu/lize-analytics/pull/17) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend (`lizeedu`)
- **Recorte por Série em `Inspector.get_exams_to_review`:** Adicionado predicado `grade_eligible` cruzando `classes__grade_id = OuterRef('grade_id')` com turmas ativas do ano corrente vinculadas a `TeacherSubject` ativo da disciplina. O professor coordenador de disciplina agora só herda cadernos cujas solicitações pertençam às séries que ele leciona neste ano.
- **Grão por Solicitação (ETS):** O filtro opera no grão de `ExamTeacherSubject`. Em um mesmo exame com múltiplas solicitações da mesma disciplina em séries distintas, o professor vê apenas as solicitações de suas séries.
- **Soberania de `reviewed_by`:** Se o revisor constar no relacionamento M2M `ExamTeacherSubject.reviewed_by`, o caderno entra na fila do professor independentemente de lecionar a série ou não (designação explícita prevalece).
- **Fallbacks Preservados:** Mantido o matching tradicional só por disciplina quando:
  1. A solicitação não possui série definida (`ETS.grade IS NULL`);
  2. O professor possui a disciplina ativa no ano corrente, mas não leciona para nenhuma turma (`get_grades()` vazio).
- **Sem Mudança de Contrato na View:** A rota `/provas/professor/revisar/` (`ExamTeacherSubjectToReviewListView`) consome o mesmo método e herda o comportamento automaticamente sem alterações de template ou contrato de API.
- **Cobertura de Testes:** Adicionados 7 novos testes unitários em `fiscallizeon/inspectors/tests/test_models.py` validando happy path, exclusão de séries alheias, divisão por ETS no mesmo exame, fallbacks de série nula e turmas vazias, e soberania de `reviewed_by`.

### Analytics & ClickHouse (`lize-analytics`)
- **ClickHouse Materialized Views:**
  - `mv_followup_review_ets`: Inclusão do campo `grade_id`.
  - `mv_followup_review_teacher_subjects`: Agregação de turmas do ano corrente por série (`grade_id`).
  - `mv_followup_review_named` (Nova MV): Materializa o matching de coordenadores por `unity_id + subject_id + grade_id` (com tratamento de fallbacks).
  - `mv_followup_reviews_unassigned` (Nova MV): Materializa solicitações em limbo (disciplina e série lecionadas na escola no ano corrente, mas sem nenhum revisor designado ou coordenador elegível).
  - `mv_followup_reviews`: Unifica as solicitações nomeadas e as solicitações em limbo.
- **Operação de Followup (`dashboards/operations/followup/reviews.py`):**
  - **Bucket Sentinela:** Introduzida a constante `UNASSIGNED_TEACHER_ID = "00000000-0000-0000-0000-000000000001"` e `UNASSIGNED_TEACHER_NAME = "Sem professor responsável"`.
  - **Visão Escola (`who=school`):** O card e o drill-down somam cadernos em limbo e os exibem no detalhe de professores sob o agrupamento `"Sem professor responsável"`.
  - **Visão Professor (`who=teacher`):** O sentinela é filtrado e não aparece para os professores.
  - **Ordenação Cronológica:** Adicionada ordenação obrigatória por prazo (`order_by("deadline")`) no detalhamento por prazos (`get_followup_reviews`).

---

## 2. Scope Boundaries (Diferenças de Escopo)

### Em Escopo (IN SCOPE)
- Recorte por série na fila pessoal de revisão do professor coordenador no Django (`/provas/professor/revisar/`).
- Exclusão de cadernos de séries que o coordenador de disciplina não leciona no ano corrente.
- Soberania absoluta de `reviewed_by` sobre a regra de série.
- Fallback para matching só por disciplina em caso de `ETS.grade` nulo ou ausência de turmas no ano corrente para o professor.
- Ocultação de cadernos sem turmas vinculadas na escola ou em limbo na fila pessoal de qualquer professor.
- Agrupamento de cadernos em limbo sob o rótulo `"Sem professor responsável"` no drill-down do card de Revisões na visão da escola (`who=school`) no Analytics.
- Ordenação cronológica estrita de prazos no detalhamento de revisões do Analytics.
- Isolamento por `Client` e coordenações do usuário em ambos os sistemas.

### Fora de Escopo (OUT OF SCOPE)
- Alterações no menu "Revisões" da coordenação geral (`/provas/revisoes/`) ou nas telas de diagramação e visualização de provas.
- Exibição do grupo `"Sem professor responsável"` na fila pessoal Django do professor (o sentinela existe apenas no Analytics para a escola).
- Modificações de interface, novos componentes ou redesign visual nas páginas (o layout das telas permanece inalterado).
- Alinhamento da janela de 120 dias do Analytics no Django (a fila Django continua exibindo pendências com `review_deadline >= today`).
- Migrations de banco de dados no Django (o modelo utiliza campos e relacionamentos já existentes).
- Alteração na regra de impedimento de autor (quem elaborou o caderno continua impedido de revisar as próprias questões).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django / Endpoint | View name |
|---|---|---|---|
| Painel do Professor (Home) | Aba "**Revisar**" (ao lado de "Elaborar" e "Corrigir") | `/painel/professor/` | `core:dashboard-teacher` (`DashboardTeacherView` / `teacher_tabs.html`) |
| Fila Completa de Revisão | Botão "**Todas as revisões**" / Menu | `/provas/professor/revisar/` | `exams:exam-teacher-subject-to-review-list` (`ExamTeacherSubjectToReviewListView`) |
| Revisão de Questões do Caderno | Botão "**Continuar**" (no card) ou "**Revisar questões**" | `/provas/<exam_id>/revisar/?exam_teacher_subject=<ets_id>` | `exams:exam_review` (`exam_review`) |
| Dashboard Principal da Coordenação | Menu lateral → "**Dashboard**" / Home | `/` (ou `/dashboards/escola/`) | `core:dashboard-coordination` (`DashboardCoordinationView`) |
| Modal de Acompanhamento (Followup) | Link "**Acompanhe**" no card "**Revisões**" | Disparado via JS (`followupDetail('reviews')`) | Modal `#modal-followup` (`school.html`) |
| API Analytics — Card de Revisões | N/A (chamada assíncrona) | `POST /dashboards/api/get-data-from-service/<client_id>/` | Operação `get_card_followup_reviews` |
| API Analytics — Prazos de Revisão | N/A (chamada assíncrona) | `POST /dashboards/api/get-data-from-service/<client_id>/` | Operação `get_followup_reviews` |
| API Analytics — Detalhe da Unidade | N/A (chamada assíncrona) | `POST /dashboards/api/get-data-from-service/<client_id>/` | Operação `get_followup_reviews_deadline` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### 4.1. Comandos de Execução Local
Para rodar a suíte de testes de modelos e métodos de revisão no Django (`lizeedu`):
```bash
source venv/bin/activate && pytest fiscallizeon/inspectors/tests/test_models.py --reuse-db -k test_get_exams_to_review
```

### 4.2. Personas Envolvidas
- **Persona Principal / Revisor de Álgebra: Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`)**
  - Professora com `is_discipline_coordinator = True` na disciplina de **Álgebra - Matemática**.
  - Leciona turmas do **1º Ano** no ano letivo corrente (2026).
  - É a coordenadora de disciplina responsável por revisar itens de Álgebra do 1º Ano.
- **Persona Elaborador Neutro: Cláudia Pereira (`claudia.pereira@rededecisao.com.br`)**
  - Professora da mesma disciplina (**Álgebra - Matemática**).
  - Elabora questões sob demanda para as provas criadas pela coordenação.
- **Persona Administrador / Coordenação: Administrador QA (`admin123@admin.com`)**
  - Usuário com papel de Coordenação/Admin na instituição (Rede Decisão / Colégio QA).
  - Cria cadernos, solicita elaborações e visualiza os cards de acompanhamento (Followup no Dashboard `/`).

### 4.3. Cadernos Cadastrados para Validação no Ambiente (Staging)
> [!IMPORTANT]
> **Pré-requisito obrigatório de revisão:** Para que qualquer caderno entre na fila de revisão (`get_exams_to_review`), ele **precisa ter pelo menos 1 questão inserida** na solicitação (questão com status em aberto/aguardando revisão). Cadernos com `0 questões` permanecem apenas na fila de elaboração.

1. **`Caderno Cláudia Teste 1`** (Teste Positivo de Filtro):
   - **Disciplina:** Álgebra - Matemática.
   - **Série:** **1º Ano** (série que Rayssa leciona).
   - **Elaborador Solicitado:** Cláudia Pereira (com ao menos 1 questão inserida).
   - **Expectativa:** **DEVE APARECER** na fila de revisão da Rayssa (`/painel/professor/` aba *"Revisar"* e menu lateral *"Para você revisar"*).
2. **`Caderno Cláudia Teste 2`** (Teste Negativo de Filtro):
   - **Disciplina:** Álgebra - Matemática.
   - **Série:** **2º Ano** (série que Rayssa NÃO leciona).
   - **Elaborador Solicitado:** Cláudia Pereira (com ao menos 1 questão inserida).
   - **Expectativa:** **NÃO DEVE APARECER** na fila de revisão da Rayssa.
3. **`Caderno Rayssa Teste`** (Auto-revisão bloqueada / Solicitação direta):
   - **Disciplina:** Álgebra - Matemática.
   - **Série:** 1º Ano.
   - **Elaborador Solicitado:** Rayssa Rodrigues da Silva.
   - **Expectativa:** Aparece na aba **"Elaborar"** da Rayssa. Não entra em sua própria fila de revisão.

### 4.4. Fixture Base via Mixer (Setup Completo)
Snippet em Python para recriar os dados de teste no shell do Django (`python manage.py shell`):

```python
from django.utils import timezone
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject, Question
from fiscallizeon.inspectors.models import Inspector, TeacherSubject
from fiscallizeon.subjects.models import Subject

# 1. Tenant e Unidade
client = mixer.blend(Client, name="Colégio QA Ciclo 4")
unity = mixer.blend(Unity, client=client, name="Unidade Sede")
coordination = mixer.blend(SchoolCoordination, unity=unity, name="Ensino Médio")

# 2. Séries e Disciplina
grade_1em = mixer.blend(Grade, name="1ª Série EM", level=Grade.HIGHT_SCHOOL)
grade_2em = mixer.blend(Grade, name="2ª Série EM", level=Grade.HIGHT_SCHOOL)
grade_3em = mixer.blend(Grade, name="3ª Série EM", level=Grade.HIGHT_SCHOOL)
subject_fisica = mixer.blend(Subject, name="Física Geral", client=client)

# 3. Revisor 1ª Série
u_rev1 = mixer.blend(User, email="coord.1em@lize.local", user_type="teacher", two_factor_enabled=False, must_change_password=False)
rev_1em = mixer.blend(Inspector, user=u_rev1, client=client, coordinations=[coordination], is_discipline_coordinator=True)
ts_rev1 = mixer.blend(TeacherSubject, teacher=rev_1em, subject=subject_fisica, active=True, school_year=timezone.now().year)
c1 = mixer.blend(SchoolClass, coordination=coordination, grade=grade_1em, school_year=timezone.now().year, name="1ª A")
ts_rev1.classes.add(c1)

# 4. Revisor 2ª Série
u_rev2 = mixer.blend(User, email="coord.2em@lize.local", user_type="teacher", two_factor_enabled=False, must_change_password=False)
rev_2em = mixer.blend(Inspector, user=u_rev2, client=client, coordinations=[coordination], is_discipline_coordinator=True)
ts_rev2 = mixer.blend(TeacherSubject, teacher=rev_2em, subject=subject_fisica, active=True, school_year=timezone.now().year)
c2 = mixer.blend(SchoolClass, coordination=coordination, grade=grade_2em, school_year=timezone.now().year, name="2ª A")
ts_rev2.classes.add(c2)

# 5. Elaborador Neutro
u_elab = mixer.blend(User, email="prof.autor@lize.local", user_type="teacher")
elab = mixer.blend(Inspector, user=u_elab, client=client, coordinations=[coordination])
ts_elab = mixer.blend(TeacherSubject, teacher=elab, subject=subject_fisica, active=True, school_year=timezone.now().year)

# 6. Exame 1: 1ª Série
exam_1em = mixer.blend(Exam, name="Prova 1 EM - Física", status=Exam.ELABORATING, review_start=timezone.now().date(), review_deadline=timezone.now().date(), coordinations=[coordination])
ets_1em = mixer.blend(ExamTeacherSubject, exam=exam_1em, teacher_subject=ts_elab, grade=grade_1em, quantity=1)
q1 = mixer.blend(Question, client=client, grade=grade_1em)
mixer.blend(ExamQuestion, exam=exam_1em, exam_teacher_subject=ets_1em, question=q1)

# 7. Exame 2: 2ª Série
exam_2em = mixer.blend(Exam, name="Prova 2 EM - Física", status=Exam.ELABORATING, review_start=timezone.now().date(), review_deadline=timezone.now().date(), coordinations=[coordination])
ets_2em = mixer.blend(ExamTeacherSubject, exam=exam_2em, teacher_subject=ts_elab, grade=grade_2em, quantity=1)
q2 = mixer.blend(Question, client=client, grade=grade_2em)
mixer.blend(ExamQuestion, exam=exam_2em, exam_teacher_subject=ets_2em, question=q2)

# 8. Exame 3: 3ª Série (Limbo - Ninguém leciona 3ª série neste ano)
exam_limbo = mixer.blend(Exam, name="Prova 3 EM - Física (Limbo)", status=Exam.ELABORATING, review_start=timezone.now().date(), review_deadline=timezone.now().date(), coordinations=[coordination])
ets_limbo = mixer.blend(ExamTeacherSubject, exam=exam_limbo, teacher_subject=ts_elab, grade=grade_3em, quantity=1)
q3 = mixer.blend(Question, client=client, grade=grade_3em)
mixer.blend(ExamQuestion, exam=exam_limbo, exam_teacher_subject=ets_limbo, question=q3)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Fila Pessoal de Revisão (LizeEdu - Django) [Automatizável ✅]

#### Cenário 1 — Coordenador leciona a série da solicitação (Caderno Visível - Teste Positivo)
**Persona:** Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`) — Coordenadora de Álgebra lecionando 1º Ano
**Caderno Alvo:** `Caderno Cláudia Teste 1` (Álgebra - 1º Ano, elaborado por Cláudia)

**Ação humana:**
- [x] Fazer login ou impersonar a professora `"Rayssa Rodrigues da Silva"` (`rayssa.silva@rededecisao.com.br`).
- [x] Acessar a fila de revisão por um dos dois caminhos canônicos da UI:
  - **Opção A (Menu Lateral):** No menu lateral, expandir `"Cadernos"` e clicar no item submenu `"Para você revisar"` (redireciona para `/provas/professor/revisar/`).
  - **Opção B (Painel Principal):** Na tela inicial da professora (`/painel/professor/`), clicar na aba central `"Revisar"`.
- [x] Validar que o contador exibe 1 solicitação/revisão pendente.
- [x] Localizar o card correspondente ao caderno `"Caderno Cláudia Teste 1"`.
- [x] Verificar que no corpo do card consta a disciplina `"Álgebra"` e a série `"1º Ano"`.
- [x] Clicar no botão para revisar o caderno (`"Revisar questões"` na listagem completa ou `"Continuar"` na aba do painel).
- [x] Garantir que a tela de revisão de questões do exame abre sem erros 403 ou 500.

**Referência técnica (para automação):**
- URL: `/provas/professor/revisar/` ou `/painel/professor/`
- Seletor: `.card.card-body:has-text("Caderno Cláudia Teste 1")` ou `div:has(h2:has-text("Caderno Cláudia Teste 1"))`
- Estado esperado: Série `"1º Ano"` visível; link para `/provas/<exam_id>/revisar/?exam_teacher_subject=<ets_id>`
- Fixture: `ets` com `grade = 1º Ano` e revisor com turmas do `1º Ano`

---

#### Cenário 2 — Coordenador NÃO leciona a série da solicitação (Caderno Oculto - Teste Negativo)
**Persona:** Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`) — NÃO leciona no 2º Ano
**Caderno Alvo:** `Caderno Cláudia Teste 2` (Álgebra - 2º Ano, elaborado por Cláudia)

**Ação humana:**
- [x] Estando logado/impersonado como `"Rayssa Rodrigues da Silva"`.
- [x] Acessar a fila de revisão (via menu `Cadernos ➔ Para você revisar` ou no `/painel/professor/` ➔ aba `"Revisar"`).
- [x] Verificar na listagem de cadernos que o caderno `"Caderno Cláudia Teste 2"` **NÃO** está visível.
- [x] Na tela completa (`/provas/professor/revisar/`), digitar `"Caderno Cláudia Teste 2"` no campo de busca e submeter.
![alt text](../evidencias/image-42.png)
- [x] Confirmar que o caderno do 2º Ano **não é retornado** para a Rayssa.
- [x] Confirmar que apenas o `"Caderno Cláudia Teste 1"` (1º Ano) consta na fila de revisão dela.

**Referência técnica (para automação):**
- URL: `/provas/professor/revisar/?q_name=Caderno+Cláudia+Teste+2`
- Seletor: `:has-text("Caderno Cláudia Teste 2")`
- Estado esperado: Elemento não presente no DOM (`count == 0`)
- Fixture: `revisor` sem turmas no `2º Ano` tentando listar caderno da série `2º Ano`

---

#### Cenário 3 — Mesmo exame com solicitações em séries distintas (Corte Cirúrgico por ETS)
**Persona:** Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`) — Leciona apenas no 1º Ano de Álgebra
**Caderno Alvo:** `Caderno Multi-Série Álgebra` (Caderno com 2 solicitações: uma para o 1º Ano e outra para o 2º Ano)

**Ação humana:**
- [x] Logado como **Coordenador (`admin123@admin.com`)**, criar um caderno de Álgebra contendo 2 solicitações de elaboração para a **Cláudia** dentro do mesmo caderno: uma para o `1º Ano` e outra para o `2º Ano` (e inserir ao menos 1 questão em cada solicitação).
- [x] Estando logado/impersonado como `"Rayssa Rodrigues da Silva"`, atualizar a listagem de revisão (`Cadernos ➔ Para você revisar` ou aba `"Revisar"`).
- [x] Verificar que o caderno é exibido na lista com o card/solicitação da série do `"1º Ano"`.
![alt text](../evidencias/image-43.png)
- [x] Garantir que **NÃO** existe um segundo card ou item para a solicitação do `"2º Ano"`.
- [x] Se houver um coordenador que leciona no `2º Ano`, confirmar que este vê apenas a solicitação do `2º Ano`.

**Referência técnica (para automação):**
- URL: `/provas/professor/revisar/`
- Seletor: `.card.card-body:has-text("1º Ano")` presente e `:has-text("2º Ano")` ausente para a Rayssa
- Estado esperado: `Inspector.get_exams_to_review(return_exam_teacher_subjects=True)` retorna apenas o ETS da série lecionada
- Fixture: `test_get_exams_to_review_same_exam_two_grades_is_cut_per_ets`

---

#### Cenário 4 — Revisor designado no M2M `reviewed_by` (Soberania de Designação)
**Persona:** Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`)
**Caderno Alvo:** `Caderno Cláudia Teste 2` (Álgebra - 2º Ano, série que Rayssa NÃO leciona)

**Ação humana:**
- [x] Logado como Admin (`admin123@admin.com`), editar a solicitação de elaboração do `"Caderno Cláudia Teste 2"` (ou via Django Admin em `ExamTeacherSubject.reviewed_by`) e adicionar `"Rayssa Rodrigues da Silva"` como revisora explicitamente designada.
- [x] Acessar novamente a plataforma como `"Rayssa Rodrigues da Silva"` e atualizar a página `"Para você revisar"`.
- [x] Verificar que agora o card do `"Caderno Cláudia Teste 2"` **passa a aparecer** na fila de revisão da Rayssa, mesmo sendo do 2º Ano.
- [x] Confirmar que o card exibe a série `"2º Ano"` e permite clicar em `"Continuar"` / `"Revisar questões"`.

**Referência técnica (para automação):**
- URL: `/provas/professor/revisar/`
- Seletor: `.card.card-body:has-text("Caderno Cláudia Teste 2")`
- Estado esperado: Presente no DOM apesar de `grade != 1º Ano`
- Fixture: `ets_2em.reviewed_by.add(rayssa)`

---

#### Cenário 5 — Fallback para solicitação sem série cadastrada (`grade IS NULL` - Caso Legado / Admin)
**Persona:** Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`)
**Caderno Alvo:** `Caderno Cláudia Teste 2` (ou qualquer solicitação editada via Django Admin para ficar com `grade = None`)

> [!NOTE]
> **Limitação da UI:** Na interface do sistema (`Solicitar ao professor`), o campo **Série** é obrigatório (`required`) e serve de gatilho para carregar a lista de disciplinas. Portanto, não é possível criar uma solicitação sem série pela tela normal — esse cenário existe para proteger cadernos legados no banco de dados e só pode ser simulado no ambiente removendo a série via **Django Admin** (`/admin/exams/examteachersubject/`) ou validado via teste automatizado (`pytest`).

**Ação humana (Opcional via Django Admin):**
- [x] No Django Admin (`/admin/exams/examteachersubject/`), localizar uma solicitação de Álgebra da Cláudia, deixar o campo **Série (Grade)** em branco (`---------`) e salvar.
- [x] Estando logado como `"Rayssa Rodrigues da Silva"`, atualizar a página `"Para você revisar"`.
- [x] Verificar que o caderno sem série **é exibido normalmente** na fila de revisão dela (mantendo o fallback tradicional por disciplina).
- [x] Garantir que o sistema não gerou erro de tela ou quebra de layout por ausência de série.
![alt text](../evidencias/image-44.png)

**Referência técnica (para automação):**
- URL: `/provas/professor/revisar/`
- Seletor: `:has-text("Caderno Álgebra Sem Série")`
- Estado esperado: Card renderizado com campo de série vazio ou `None` sem quebrar
- Fixture: `test_get_exams_to_review_null_grade_keeps_subject_match`

---

#### Cenário 6 — Fallback para Coordenador com disciplina ativa mas sem turmas no ano corrente
**Persona:** Professor Coordenador de Disciplina sem turmas vinculadas em 2026

**Ação humana:**
- [ ] Cadastrar ou alterar um professor para ser coordenador de disciplina em Álgebra, mas sem nenhuma turma associada no ano letivo de 2026.
- [ ] Acessar a tela `"Para você revisar"` com esse professor.
- [ ] Verificar que o professor visualiza **todos** os cadernos da disciplina de Álgebra da sua coordenação, independentemente da série (`1º Ano`, `2º Ano`).
- [ ] Validar que o fallback tradicional por disciplina foi ativado integralmente para quem não possui turmas.

**Referência técnica (para automação):**
- URL: `/provas/professor/revisar/`
- Seletor: `:has-text("Álgebra")`
- Estado esperado: Todos os cadernos de Álgebra da coordenação visíveis
- Fixture: `test_get_exams_to_review_empty_grades_keeps_subject_match`

---

#### Cenário 7 — Caderno em série sem turma no colégio / Limbo (Não visível para nenhum professor)
**Persona:** Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`)
**Caderno Alvo:** `Caderno Álgebra - 3º Ano` (Série onde nenhum professor do colégio leciona no ano de 2026)

**Ação humana:**
- [ ] Observar ou criar um caderno de Álgebra cuja série (ex: `3º Ano`) não é lecionada por nenhum professor do colégio.
- [ ] Estando logado como `"Rayssa Rodrigues da Silva"`, verificar que o caderno **NÃO** aparece na fila dela.
- [ ] Logar com outros professores de Álgebra e confirmar que o caderno também **NÃO** aparece na fila de nenhum deles.
- [ ] Confirmar que o caderno em limbo não polui a fila de nenhum professor, ficando reservado para o agrupamento da Coordenação Geral no Analytics.

**Referência técnica (para automação):**
- URL: `/provas/professor/revisar/`
- Seletor: `:has-text("Caderno Álgebra - 3º Ano")`
- Estado esperado: Ausente do DOM para todos os revisores não vinculados ao M2M `reviewed_by`
- Fixture: ETS com série `3º Ano` sem turmas no ano

---

#### Cenário 8 — Turmas vinculadas a `TeacherSubject` ativo de ano anterior
**Persona:** Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`)

**Ação humana:**
- [ ] No banco de testes/staging, caso haja vínculo da turma do `1º Ano` a um `TeacherSubject` ativo com ano letivo anterior `(now.year - 1)`.
- [ ] Atualizar a página `"Para você revisar"` logado como `"Rayssa Rodrigues da Silva"`.
- [ ] Verificar que o `"Caderno Cláudia Teste 1"` continua sendo exibido na fila da professora.
- [ ] Confirmar que o sistema considerou o ano da turma (`SchoolClass.school_year = now.year`) e não o ano do cadastro do `TeacherSubject`.

**Referência técnica (para automação):**
- URL: `/provas/professor/revisar/`
- Seletor: `:has-text("Caderno Cláudia Teste 1")`
- Estado esperado: Presente no DOM
- Fixture: `test_get_exams_to_review_grades_from_older_teacher_subject`

---

### 5.2 Card de Revisão no Dashboard de Acompanhamento (Lize Analytics) [Automatizável ✅]

#### Cenário 9 — Exibição e contadores do Card de Revisões da Escola (`who=school`)
**Persona:** Administrador QA (`admin123@admin.com`) — Coordenação Geral da Escola

**Ação humana:**
- [ ] Fazer login ou voltar para a sessão do usuário `"admin123@admin.com"`.
- [ ] Acessar a página inicial do Dashboard `/` `(visão da escola/coordenação)`.
- [ ] Rolar até a seção de cards de acompanhamento e localizar o card com o título `"Revisões"`.
- [ ] Verificar o texto do contador: `"Há X revisões aguardando"` `(onde X inclui os cadernos da Cláudia dentro do prazo de 120 dias)`.
- [ ] Verificar o gráfico circular SVG à direita com o percentual de conclusão das revisões `(ex: "0%" ou percentual correspondente)`.
- [ ] Passar o mouse sobre o ícone de interrogação `(i)` ao lado do título e validar o tooltip: `"Os dados analisados nesse cartão são apenas os que estão dentro no prazo."`.
- [ ] Garantir que o link inferior `"Acompanhe"` está visível.

**Referência técnica (para automação):**
- URL: `/`
- Seletor: `div[ref="reviews"] p.tw-truncate:has-text("Revisões")`
- Estado esperado: `p:has-text("Há")` presente; `div[data-chart="idReviewsDataChart"] svg text` contém percentual
- Fixture: Chamada API `POST /dashboards/api/get-data-from-service/<client_id>/` com `operation: "get_card_followup_reviews"`, `who: "school"`

---

#### Cenário 10 — Ordenação cronológica dos prazos no modal de Acompanhamento
**Persona:** Administrador QA (`admin123@admin.com`)

**Ação humana:**
- [ ] No card `"Revisões"`, clicar no link inferior `"Acompanhe"`.
- [ ] Observar a abertura do modal de Acompanhamento de Revisões.
- [ ] Conferir o cabeçalho do modal exibindo o título `"Revisões"` e o total de pendências.
- [ ] Na tabela de prazos de revisão, inspecionar a coluna de datas/prazos (ex: prazo definido para `12 de Dezembro de 2026`).
- [ ] Validar que as datas estão ordenadas em ordem cronológica ascendente `(da data mais antiga/próxima para a mais distante)`.
- [ ] Garantir que prazos com 100% de conclusão **não** aparecem na listagem de pendências.

**Referência técnica (para automação):**
- URL: `/` (Modal Followup)
- Seletor: `#modal-followup table tr td:first-child` (ou lista de prazos)
- Estado esperado: Datas ordenadas crescentemente (`order_by("deadline")` no Ibis/Analytics)
- Fixture: Operação `get_followup_reviews` retornando lista ordenada por `deadline`

---

#### Cenário 11 — Detalhamento por unidade e agrupamento "Sem professor responsável" (`who=school`)
**Persona:** Administrador QA (`admin123@admin.com`) — Coordenação Geral

**Ação humana:**
- [ ] Dentro do modal de acompanhamento de Revisões, clicar sobre a linha de um prazo que contenha cadernos em limbo (ex: cadernos cujos coordenadores não lecionam aquela série específica).
- [ ] Localizar o card da unidade escolar correspondente.
- [ ] Clicar sobre a unidade para abrir a lista detalhada de cadernos e professores.
- [ ] Na aba de professores da unidade, localizar o agrupamento com o nome `"Sem professor responsável"`.
- [ ] Verificar que os cadernos em limbo estão agrupados sob esta identificação sentinela.
- [ ] Conferir a quantidade de questões solicitadas e pendentes listadas nesse grupo.

**Referência técnica (para automação):**
- URL: `/` (Modal Followup - Drill-Down de Unidade)
- Seletor: `div:has-text("Sem professor responsável")`
- Estado esperado: Elemento renderizado associado a `UNASSIGNED_TEACHER_ID = "00000000-0000-0000-0000-000000000001"`
- Fixture: Operação `get_followup_reviews_deadline` com `followup_unity` setada retornando `_map_unassigned`

---

#### Cenário 12 — Isolamento de pendências na visão da Professora Rayssa (`who=teacher`)
**Persona:** Rayssa Rodrigues da Silva (`rayssa.silva@rededecisao.com.br`) — Acessando acompanhamento

**Ação humana:**
- [ ] Acessar a visão de acompanhamento sob a perspectiva da professora Rayssa `(who=teacher)`.
- [ ] Verificar os dados do card e do detalhamento de revisões.
- [ ] Garantir que a Rayssa visualiza **apenas** as revisões sob sua responsabilidade direta (no caso, cadernos do 1º Ano como `Caderno Cláudia Teste 1`).
- [ ] Validar que o grupo `"Sem professor responsável"` **NÃO** é exibido para a professora em hipótese alguma.

**Referência técnica (para automação):**
- URL: Endpoint de operações analíticas com `who: "teacher"`, `who_ids: ["<teacher_id>"]`
- Seletor: N/A (validação de resposta de payload ou UI do professor)
- Estado esperado: `teacher_id` nulo descartado pelo filtro `who=teacher`
- Fixture: `table = self.apply_who_filter(..., "teacher", teacher_id)`

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Badges de Situação:**
  - Garantir que solicitações com zero questões revisadas exibam badge com fundo azul claro e texto azul escuro `"Aguarda revisão"` (`bg-primary-soft text-primary`).
  - Garantir que solicitações com pelo menos 1 questão revisada (mas não todas) exibam badge com fundo verde claro e texto verde `"Revisando"` (`bg-success-soft text-success`).
- [ ] **Truncamento de Texto (Anti-Rework):**
  - Cadernos com nomes longos (ex: *"Avaliação Trimestral Unificada de Física e Ciências da Natureza - 1ª Série EM - Manhã e Tarde"*) devem conter a classe `.text-truncate` e não vazar ou quebrar a altura dos cards adjacentes no grid de 4 colunas.
- [ ] **Responsividade do Grid:**
  - Testar a tela em resolução `1333x1080` e `1024x768`.
  - Os cards de revisão devem se reorganizar de 4 colunas (`col-lg-3`) para 2 colunas (`col-sm-6`) sem sobreposição de textos.
- [ ] **Gráfico de Percentual do Followup:**
  - O gráfico circular SVG deve apresentar cores dinâmicas de acordo com a performance:
    - Menor que 50%: Borda de destaque vermelha (`#D92D20`) e fundo suave (`#FBEAE9`).
    - Entre 50% e 69%: Borda de destaque laranja/amarela (`#F3B364`) e fundo suave (`#FEF7EF`).
    - 70% ou superior: Borda de destaque verde (`#41C588`) e fundo suave (`#ECF9F3`).

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Espaço reservado para documentação de eventuais anomalias identificadas durante a execução dos testes pelo QA.

- **Status:** Nenhum bug impeditivo identificado nos testes unitários e de integração até o momento.
- **Diretriz de Schema Drift (Banco Local vs Staging):** Conforme apontado pelo desenvolvedor (Jan Justi), o ambiente de staging terá o ClickHouse sincronizado com o banco de produção para refletir fielmente as novas views (`mv_followup_review_named` e `mv_followup_reviews_unassigned`). Caso ocorra erro de coluna inexistente no banco local durante os testes, deve-se checar se a tabela do PostgreSQL está sincronizada antes de classificar como bug da feature.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Alinhamento de Janela de Prazos (Django vs Analytics):**
> Atualmente a fila Django filtra por `review_deadline >= today` (cadernos vencidos saem da fila do professor a menos que a data seja prorrogada), enquanto o card de Analytics monitora uma janela histórica de `today - 120 days` (incluindo cadernos em atraso). Avaliar com o time de Produto se no futuro a fila Django também deve exibir cadernos atrasados com destaque de alerta visual.

> [!NOTE]
> **Performance do Exists no Django:**
> As subqueries `Exists` cruzando `TeacherSubject` e `SchoolClass` executam com alta eficiência em réplicas de leitura, mas caso clientes de grande porte (com centenas de turmas e disciplinas) relatem lentidão na listagem `/provas/professor/revisar/`, pode-se avaliar a criação de um índice composto cobrindo `(teacher_id, active, subject_id)` em `TeacherSubject` e `(school_year, grade_id)` em `SchoolClass`.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
🔗 **[Ver Mapeamento de Tela (Painel do Professor - Tabs)](docs/tests/usability/teacher_tabs.md)**
🔗 **[Ver Mapeamento de Tela (Fila de Revisão Completa)](docs/tests/usability/teacher_exam_to_review_list.md)**
🔗 **[Ver Mapeamento de Tela (Dashboard Followup)](docs/tests/usability/school.md)**

### Automation Snippet (Python / Playwright + Mixer Data Setup)
Abaixo está o snippet canônico para converter os cenários manuais em testes automatizados ponta a ponta com Playwright no Lize Edu:

```python
import pytest
from django.utils import timezone
from mixer.backend.django import mixer
from playwright.sync_api import Page, expect

from fiscallizeon.accounts.models import User
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject, Question
from fiscallizeon.inspectors.models import Inspector, TeacherSubject
from fiscallizeon.subjects.models import Subject


@pytest.mark.django_db
def test_teacher_exam_to_review_grade_filter(page: Page, live_server):
    # 1. Setup de Dados via Mixer
    client = mixer.blend(Client, name="Escola Playwright")
    unity = mixer.blend(Unity, client=client)
    coord = mixer.blend(SchoolCoordination, unity=unity)

    grade_1 = mixer.blend(Grade, name="1ª Série", level=Grade.HIGHT_SCHOOL)
    grade_2 = mixer.blend(Grade, name="2ª Série", level=Grade.HIGHT_SCHOOL)
    sub = mixer.blend(Subject, name="História", client=client)

    # Revisor que leciona apenas a 1ª série
    user_rev = mixer.blend(
        User,
        email="revisor.historia@teste.com",
        user_type="teacher",
        two_factor_enabled=False,
        must_change_password=False,
    )
    user_rev.set_password("123456")
    user_rev.save()

    rev = mixer.blend(
        Inspector,
        user=user_rev,
        client=client,
        coordinations=[coord],
        is_discipline_coordinator=True,
    )
    ts_rev = mixer.blend(TeacherSubject, teacher=rev, subject=sub, active=True, school_year=timezone.now().year)
    s_class = mixer.blend(SchoolClass, coordination=coord, grade=grade_1, school_year=timezone.now().year)
    ts_rev.classes.add(s_class)

    # Elaborador
    user_elab = mixer.blend(User, email="autor.historia@teste.com", user_type="teacher")
    elab = mixer.blend(Inspector, user=user_elab, client=client, coordinations=[coord])
    ts_elab = mixer.blend(TeacherSubject, teacher=elab, subject=sub, active=True, school_year=timezone.now().year)

    # Exame 1: 1ª Série (DEVE APARECER)
    exam_ok = mixer.blend(
        Exam,
        name="Avaliação História 1ª Série",
        status=Exam.ELABORATING,
        review_start=timezone.now().date(),
        review_deadline=timezone.now().date(),
        coordinations=[coord],
    )
    ets_ok = mixer.blend(ExamTeacherSubject, exam=exam_ok, teacher_subject=ts_elab, grade=grade_1, quantity=1)
    q1 = mixer.blend(Question, client=client, grade=grade_1)
    mixer.blend(ExamQuestion, exam=exam_ok, exam_teacher_subject=ets_ok, question=q1)

    # Exame 2: 2ª Série (NÃO DEVE APARECER)
    exam_hidden = mixer.blend(
        Exam,
        name="Avaliação História 2ª Série",
        status=Exam.ELABORATING,
        review_start=timezone.now().date(),
        review_deadline=timezone.now().date(),
        coordinations=[coord],
    )
    ets_hidden = mixer.blend(ExamTeacherSubject, exam=exam_hidden, teacher_subject=ts_elab, grade=grade_2, quantity=1)
    q2 = mixer.blend(Question, client=client, grade=grade_2)
    mixer.blend(ExamQuestion, exam=exam_hidden, exam_teacher_subject=ets_hidden, question=q2)

    # 2. Execução Playwright
    page.goto(f"{live_server.url}/conta/login/")
    page.fill('input[name="login"]', "revisor.historia@teste.com")
    page.fill('input[name="password"]', "123456")
    page.click('button[type="submit"]')

    # Navegação para a fila de revisão
    page.goto(f"{live_server.url}/provas/professor/revisar/")

    # 3. Asserções
    expect(page.locator('.card.card-body:has-text("Avaliação História 1ª Série")')).to_be_visible()
    expect(page.locator('.card.card-body:has-text("Avaliação História 2ª Série")')).not_to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalo Principal:** Necessidade de sincronizar as regras de negócio em dois ecossistemas distintos (Django ORM no `lizeedu` e ClickHouse Views / Ibis no `lize-analytics`), exigindo atenção redobrada aos casos de borda (limbo, fallback sem turma, `reviewed_by` soberano).
- **Alinhamento Dev/QA:** A existência prévia de OpenSpec estruturada em ambos os repositórios (`filtro-serie-fila-revisao` no Django e as especificações de views no Analytics) reduziu drasticamente o atrito e permitiu criar o plano de testes com 100% de precisão nos seletores e rotas.
- **Oportunidade de Melhoria:** Criar um comando unificado para smoke test de views no ClickHouse em conjunto com as fixtures do Django, facilitando a validação de features de analytics em ambientes locais.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
<!-- 
1. Considerar formalizar no prompt V2 uma seção para 'Multi-Repository Backend + Analytics', padronizando a documentação conjunta de Views Django com Materialized Views de BI/ClickHouse.
2. Adicionar recomendação explícita para sempre checar o arquivo de migrações e o repositório analítico quando a task envolver palavras-chave como 'card', 'followup', 'dashboard' ou 'indicadores'.
-->


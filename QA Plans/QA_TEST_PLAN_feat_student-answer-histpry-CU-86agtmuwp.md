# QA Test Plan: Histórico de Respostas de Alteração do Aluno

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-08-31 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Exams (Correção / Acompanhamento de Aplicações) |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐ (4/5) — proposal, spec e design bem estruturados; tasks completas; referência visual (mockup HTML) disponível. Pequena lacuna: spec não detalha comportamento de loading/erro no frontend. |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend
- **Serviço `StudentAnswerHistoryService`** (`fiscallizeon/answers/services/answer_history.py`): novo serviço que consolida o histórico de marcações de respostas de múltipla escolha por questão, incluindo trilha sequencial (`trail`), contagem de alterações (`changes_count`, `has_changes`), horários de primeira/última marcação e resolução de randomização via `shuffle_code`/`RandomizationVersion`.
- **Endpoint REST** (`fiscallizeon/applications/api2/application_student.py`): nova view `ApplicationStudentAnswerHistoryView` expondo `GET /api/v2/application-students/<uuid:pk>/answer-history/`, com permissões para Coordenação, Professor, Staff e Superuser, e isolamento multi-tenant por `Client`.
- **Serializers** (`fiscallizeon/applications/serializers2/application_student.py`): novos serializers `StudentAnswerHistorySerializer`, `QuestionAnswerHistorySerializer`, `TrailItemSerializer`, `StudentInfoSerializer`, `ExamInfoSerializer`, `HistorySummarySerializer`.
- **URL** (`fiscallizeon/api2/urls.py`): rota registrada como `application-student-answer-history`.

### Frontend
- **Componente `student_answer_history_modal`** (`fiscallizeon/applications/components/student_answer_history_modal/`): componente django-components com template HTML, JS (Alpine.js) e classe Python para registro.
- **Integração na tela de detalhe da prova** (`fiscallizeon/exams/templates/dashboard/exams/exam_detail_new.html`): nova aba "Histórico de Marcações" no modal de correção do aluno, com cards por questão, trilha visual de círculos e badges de alteração.
- **Funções JS** (`fiscallizeon/exams/templates/dashboard/exams/includes/exam-detail-functions.js`): método `fetchAnswerHistory()` para busca assíncrona do histórico via API.

### Testes
- **Testes unitários do serviço** (`fiscallizeon/answers/tests/services/test_answer_history.py`): cobre cenários de questões sem respostas, sem trocas, com múltiplas trocas, limpeza de HTML do snippet e randomização.
- **Testes de integração da API** (`fiscallizeon/applications/tests/test_answer_history_api.py`): cobre status 200, 403 (permissão negada) e 404 (isolamento de cliente).

---

## 2. Scope Boundaries (Diferenças de Escopo)

**IN SCOPE:**
- Exibição do histórico de alterações de respostas de múltipla escolha para o coordenador/professor.
- Aba "Histórico de Marcações" no modal de correção do aluno na tela de detalhe da prova.
- Cards por questão com trilha visual de alternativas, badges de contagem e horários.
- Endpoint REST com isolamento multi-tenant e controle de permissão.
- Respeito à randomização de questões e alternativas (letras e ordem do caderno do aluno).

**OUT OF SCOPE:**
- Auditoria de digitação tecla a tecla em redações/questões discursivas.
- Edição ou alteração manual do histórico pela coordenação (somente leitura).
- Exposição do histórico para o portal público do aluno neste ciclo.
- Alterações nos fluxos de correção de discursiva/redação.
- Criação de novas tabelas ou migrações de dados (usa `OptionAnswer` existente).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Detalhe da prova (correção) | Instrumentos Avaliativos → detalhe da prova → modal do aluno | `/provas/<uuid>/` | `exams:exams_detail_new` |
| Aba "Histórico de Marcações" | Aba "Histórico de Marcações" no modal de correção | (interno ao modal) | — |
| API de histórico | — | `/api/v2/application-students/<uuid>/answer-history/` | `application-student-answer-history` |

> **[verificar]** O rótulo "Histórico de Marcações" está definido no template `exam_detail_new.html` (linha da aba). Confirme visualmente no perfil de Coordenador.

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos de Teste

**Testes unitários do serviço:**
```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/answers/tests/services/test_answer_history.py
```

**Testes de integração da API:**
```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/applications/tests/test_answer_history_api.py
```

**Todos os testes afetados:**
```bash
./scripts/tests/run-tests.sh --no-tty fiscallizeon/answers/tests/services/test_answer_history.py fiscallizeon/applications/tests/test_answer_history_api.py
```

### Persona

**Coordenador de unidade X** com `user_type='coordination'`, vínculo em `SchoolCoordination` via `CoordinationMember`, e acesso ao mesmo `Client` do aluno. O endpoint também aceita Professor (`settings.TEACHER`), Staff e Superuser.

### Mixer Setup (para QA manual e automação futura)

```python
from datetime import datetime, timedelta
from django.utils import timezone
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.answers.models import OptionAnswer
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject
from fiscallizeon.inspectors.models import TeacherSubject
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import Subject

# --- Cliente e Coordenador ---
client_obj = mixer.blend(Client, max_students_quantity=None)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
coord_user = mixer.blend(
    User,
    two_factor_enabled=False,
    is_staff=False,
    is_superuser=False,
    user_type='coordination',
)
mixer.blend(CoordinationMember, user=coord_user, coordination=coordination)

# --- Aluno ---
student = mixer.blend(
    Student,
    client=client_obj,
    name="Aluno Teste",
    enrollment_number="2403441",
)

# --- Prova e Aplicação ---
exam = mixer.blend(
    Exam,
    client=client_obj,
    name="Simulado Teste",
    start_number=1,
    random_questions=False,
    random_alternatives=False,
)
app = mixer.blend(
    Application,
    exam=exam,
    date=timezone.now().date(),
    start=datetime.strptime("13:00:00", "%H:%M:%S").time(),
    end=datetime.strptime("18:00:00", "%H:%M:%S").time(),
)
app_student = mixer.blend(
    ApplicationStudent,
    application=app,
    student=student,
    start_time=timezone.now() - timedelta(hours=2),
    end_time=timezone.now(),
)

# --- Questões e Opções ---
subject = mixer.blend(Subject, name="Biologia")
ts = mixer.blend(TeacherSubject, subject=subject, client=client_obj)
ets = mixer.blend(ExamTeacherSubject, exam=exam, teacher_subject=ts, order=1)

q1 = mixer.blend(
    Question,
    category=Question.CHOICE,
    enunciation="<p>Questão de teste com <strong>genótipo</strong> Aa Bb.</p>",
    subject=subject,
)
eq1 = mixer.blend(ExamQuestion, exam=exam, question=q1, exam_teacher_subject=ets, order=1)
opt_a = mixer.blend(QuestionOption, question=q1, text="Opção A", index=1)
opt_b = mixer.blend(QuestionOption, question=q1, text="Opção B", index=2)
opt_c = mixer.blend(QuestionOption, question=q1, text="Opção C", index=3)

# --- Cenário: Aluno trocou A → C → B (2 alterações) ---
t0 = app_student.start_time
ans1 = mixer.blend(
    OptionAnswer,
    student_application=app_student,
    question_option=opt_a,
    status=OptionAnswer.INACTIVE,
)
OptionAnswer.objects.filter(pk=ans1.pk).update(created_at=t0 + timedelta(minutes=10))

ans2 = mixer.blend(
    OptionAnswer,
    student_application=app_student,
    question_option=opt_c,
    status=OptionAnswer.INACTIVE,
)
OptionAnswer.objects.filter(pk=ans2.pk).update(created_at=t0 + timedelta(minutes=30))

ans3 = mixer.blend(
    OptionAnswer,
    student_application=app_student,
    question_option=opt_b,
    status=OptionAnswer.ACTIVE,
)
OptionAnswer.objects.filter(pk=ans3.pk).update(created_at=t0 + timedelta(minutes=70))
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona ativa:** Coordenador de unidade X (logado na plataforma com perfil de coordenação).

### 5.1 Acesso à Aba de Histórico [Automatizável ✅]

#### Cenário 1 — Acesso à aba "Histórico de Marcações" no modal de correção

- [ ] Acesse a tela de detalhe de uma aplicação/prova (`/provas/<uuid>/`).
- [ ] Clique em um aluno na listagem para abrir o modal de correção.
- [ ] Verifique que existem duas abas: "Respostas" e "Histórico de Marcações".
- [ ] Clique na aba "Histórico de Marcações".
- [ ] Verifique que o indicador de carregamento (spinner) aparece enquanto a API retorna os dados.
- [ ] Verifique que o conteúdo da aba é exibido corretamente após o carregamento.

### 5.2 Aluno com Trocas de Alternativa [Automatizável ✅]

#### Cenário 2 — Visualização de histórico com múltiplas trocas

- [ ] Acesse o histórico de um aluno que realizou trocas de alternativa em uma questão.
- [ ] Verifique que o card da questão exibe o badge com a contagem de alterações (ex.: "2 alterações").
- [ ] Verifique que a trilha de alternativas está na ordem cronológica (ex.: A → C → B).
- [ ] Verifique que a resposta final ativa está destacada em verde (círculo preenchido).
- [ ] Verifique que as alternativas anteriores estão em cinza (círculo com borda).
- [ ] Verifique que o rodapé do card exibe o horário da primeira e da última marcação (formato "HH:MM → HH:MM").
- [ ] Verifique que o texto "marcação em verde é a resposta final" aparece no rodapé.

### 5.3 Aluno sem Trocas [Automatizável ✅]

#### Cenário 3 — Histórico de aluno que respondeu sem alterar

- [ ] Acesse o histórico de um aluno que respondeu cada questão apenas uma vez.
- [ ] Verifique que o badge de cada questão exibe "Sem alterações".
- [ ] Verifique que apenas um único círculo verde é exibido na trilha de cada questão.
- [ ] Verifique que o rodapé exibe o horário da marcação (primeiro e último são iguais).

### 5.4 Questão Não Respondida [Automatizável ✅]

#### Cenário 4 — Questão deixada em branco pelo aluno

- [ ] Acesse o histórico de um aluno que deixou uma questão em branco.
- [ ] Verifique que o card da questão exibe o aviso em itálico: "Não respondida pelo aluno".
- [ ] Verifique que não há trilha de alternativas ou badges de alteração para essa questão.

### 5.5 Randomização de Questões/Alternativas [Apenas Manual 👁]

#### Cenário 5 — Prova com randomização

- [ ] Acesse o histórico de um aluno que realizou uma prova com randomização de questões e/ou alternativas.
- [ ] Verifique que as letras das alternativas na trilha correspondem à versão que o aluno viu na tela de realização.
- [ ] Verifique que a ordem das questões no histórico respeita a numeração do caderno do aluno (não a ordem canônica do gabarito).

### 5.6 Validação de Permissões [Automatizável ✅]

#### Cenário 6 — Acesso permitido (Coordenador)

- [ ] Logue como Coordenador de uma unidade.
- [ ] Acesse o histórico de um aluno da mesma instituição.
- [ ] Verifique que o histórico é exibido corretamente (status 200).

#### Cenário 7 — Acesso negado (Usuário sem permissão)

- [ ] Logue como um usuário que NÃO possui perfil de Coordenação, Professor, Staff nem Superuser.
- [ ] Tente acessar o endpoint de histórico via API.
- [ ] Verifique que o sistema retorna status HTTP 403 (Forbidden).

#### Cenário 8 — Isolamento multi-tenant

- [ ] Logue como Coordenador do Cliente A.
- [ ] Tente acessar o histórico de um aluno do Cliente B (via API, manipulando o UUID).
- [ ] Verifique que o sistema retorna status HTTP 404 (Not Found).

### 5.7 Comportamento da API [Automatizável ✅]

#### Cenário 9 — Estrutura do payload da API

- [ ] Requisite o endpoint `GET /api/v2/application-students/<uuid>/answer-history/` com um coordenador autorizado.
- [ ] Verifique que o JSON retornado contém os campos: `student` (id, name, enrollment_number), `exam` (id, name, is_randomized), `summary` (total_changes, questions_changed_count, total_questions_answered), `questions` (array).
- [ ] Verifique que cada item de `questions` contém: `question_id`, `question_number`, `subject_name`, `question_snippet`, `changes_count`, `has_changes`, `first_marked_at`, `last_marked_at`, `trail` (array com letter, is_final, marked_at).

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Captura de tela da aba "Histórico de Marcações" com aluno que tem trocas — comparar com o mockup de referência.
- [ ] Captura de tela da aba "Histórico de Marcações" com aluno sem trocas.
- [ ] Captura de tela da aba "Histórico de Marcações" com questão não respondida.
- [ ] Verificar responsividade do modal em telas menores (scroll horizontal não deve ser necessário).
- [ ] Conferir que o spinner de loading segue o padrão visual da plataforma (borda laranja `#f54a00`).
- [ ] Conferir que os cards de questão seguem o design system (bordas arredondadas, sombra suave, espaçamento consistente).

---

## 7. Bugs and Observations (Problemas Encontrados)

> **[!NOTE]**  
> Esta seção deve ser preenchida durante a execução dos testes. Use o formato abaixo para registrar bugs:

**Exemplo de formato:**

> **[!BUG]**  
> **Title:** [Descrição clara da falha]  
> **Context/Root Cause:** [Por que acontece tecnicamente, se conhecido]  
> **Expected Behavior:** [O que a UI/API deveria ter feito]  
> **Workaround:** [Se aplicável, uma solução temporária]

Categorias: `[UX/UI]`, `[Backend Logic]`, `[Database]`, `[Spec Gap]`

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> **[!NOTE]**  
> Itens que não quebram a release atual, mas devem ser rastreados:

- **Melhoria de UX:** Adicionar tooltip ou popover ao passar o mouse sobre cada círculo da trilha, exibindo o horário exato da marcação (atualmente o horário só aparece no rodapé do card).
- **Performance:** O endpoint carrega todas as `OptionAnswer` do aluno; para provas com muitas questões, considerar paginação ou cache.
- **Acessibilidade:** Os círculos da trilha não possuem atributos `aria-label` para leitores de tela.
- **Escopo futuro:** Exposição do histórico para o portal do aluno (conforme discutido na proposta, mas fora deste ciclo).

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.
  🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_detail_new.md)**

### 1. URLs e Navegação

| URL | Descrição |
|---|---|
| `/provas/<uuid>/` | Detalhe da prova (tela `exam_detail_new.html`) |
| `/api/v2/application-students/<uuid>/answer-history/` | Endpoint REST do histórico |

### 2. Pré-requisitos para Automação (Fixtures e Permissões)

- **Persona:** Coordenador com `user_type='coordination'`, vínculo em `SchoolCoordination` via `CoordinationMember`, mesmo `Client` do aluno.
- **Permissão:** A view verifica `user.is_superuser`, `user.is_staff`, ou `user.user_type in (settings.COORDINATION, settings.TEACHER)`.
- **Dados necessários:** `ApplicationStudent` com `OptionAnswer` (pelo menos uma com `status=ACTIVE` e opcionalmente INATIVAS para trocas).

### 3. Seletores DOM e Ações

| Elemento | Seletor / Identificador | Descrição |
|---|---|---|
| Aba "Respostas" | Botão com texto "Respostas" na barra de abas do modal | Aba padrão |
| Aba "Histórico de Marcações" | Botão com texto "Histórico de Marcações" na barra de abas | Aba de histórico |
| Spinner de loading | `div.tw-animate-spin` dentro do template `v-if="loadingAnswerHistory"` | Indicador de carregamento |
| Card de questão | `div` com `v-for="q in answerHistoryData.questions"` | Card individual de cada questão |
| Badge de alterações | `span` com `v-if="q.has_changes"` exibindo "X alterações" ou "Sem alterações" | Indicador de trocas |
| Círculo da alternativa | `div` com `:class` dinâmico (verde se `is_final`, cinza caso contrário) | Elemento da trilha |
| Chevron separador | `svg` entre os círculos | Separador visual |
| Rodapé com horários | `p` com `x-text` formatando `first_marked_at → last_marked_at` | Informação temporal |
| Mensagem "Não respondida" | `p` com texto "Não respondida pelo aluno" | Questão em branco |

### 4. Rotas de API Críticas

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/v2/application-students/<uuid>/answer-history/` | Retorna o histórico consolidado |

### 5. Snippet de Automação (Playwright + Mixer)

```python
"""
Exemplo de setup para teste automatizado do histórico de respostas.
Persona: Coordenador logado.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.answers.models import OptionAnswer
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject
from fiscallizeon.inspectors.models import TeacherSubject
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import Subject

# Setup de dados
client_obj = mixer.blend(Client, max_students_quantity=None)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
coord_user = mixer.blend(
    User,
    two_factor_enabled=False,
    is_staff=False,
    is_superuser=False,
    user_type='coordination',
)
mixer.blend(CoordinationMember, user=coord_user, coordination=coordination)

student = mixer.blend(Student, client=client_obj, name="Aluno Teste", enrollment_number="2403441")
exam = mixer.blend(Exam, client=client_obj, name="Simulado Teste", start_number=1)
app = mixer.blend(
    Application,
    exam=exam,
    date=timezone.now().date(),
    start=datetime.strptime("13:00:00", "%H:%M:%S").time(),
    end=datetime.strptime("18:00:00", "%H:%M:%S").time(),
)
app_student = mixer.blend(
    ApplicationStudent,
    application=app,
    student=student,
    start_time=timezone.now() - timedelta(hours=2),
    end_time=timezone.now(),
)

subject = mixer.blend(Subject, name="Biologia")
ts = mixer.blend(TeacherSubject, subject=subject, client=client_obj)
ets = mixer.blend(ExamTeacherSubject, exam=exam, teacher_subject=ts, order=1)
q1 = mixer.blend(Question, category=Question.CHOICE, enunciation="Questão de teste", subject=subject)
eq1 = mixer.blend(ExamQuestion, exam=exam, question=q1, exam_teacher_subject=ets, order=1)
opt_a = mixer.blend(QuestionOption, question=q1, text="A", index=1)
opt_b = mixer.blend(QuestionOption, question=q1, text="B", index=2)
opt_c = mixer.blend(QuestionOption, question=q1, text="C", index=3)

# Cenário: troca A → C → B
t0 = app_student.start_time
ans1 = mixer.blend(OptionAnswer, student_application=app_student, question_option=opt_a, status=OptionAnswer.INACTIVE)
OptionAnswer.objects.filter(pk=ans1.pk).update(created_at=t0 + timedelta(minutes=10))
ans2 = mixer.blend(OptionAnswer, student_application=app_student, question_option=opt_c, status=OptionAnswer.INACTIVE)
OptionAnswer.objects.filter(pk=ans2.pk).update(created_at=t0 + timedelta(minutes=30))
ans3 = mixer.blend(OptionAnswer, student_application=app_student, question_option=opt_b, status=OptionAnswer.ACTIVE)
OptionAnswer.objects.filter(pk=ans3.pk).update(created_at=t0 + timedelta(minutes=70))

# Elevação de privilégios (se necessário para Playwright)
coord_user.is_superuser = True
coord_user.save()

# Login via Playwright: navegar até /provas/<exam.pk>/ e clicar no aluno
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante os testes:** _(a ser preenchido após execução)_
- **Houve muitos vai-e-volta com o desenvolvedor?** _(a ser preenchido após execução)_
- **Como o fluxo de desenvolvimento/QA poderia ter sido melhorado?** _(a ser preenchido após execução)_

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

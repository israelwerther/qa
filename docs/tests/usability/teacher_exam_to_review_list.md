# Mapeamento de Tela: teacher_exam_to_review_list.html

> **Nota de Acervo:** Este arquivo é alimentado de forma incremental e colaborativa. Sempre que uma nova funcionalidade for testada nesta tela, o mapeamento de IDs e seletores estáveis deve ser atualizado aqui. O objetivo é criar um repositório centralizado para facilitar a automação via Playwright, sem depender de classes CSS frágeis.

## 1. URLs e Navegação
- **Fila Pessoal de Revisão (default):** `/provas/professor/revisar/`
- **Filtro de Cadernos Aguardando Revisão:** `/provas/professor/revisar/?q_status=await_review`
- **Filtro de Cadernos em Revisão:** `/provas/professor/revisar/?q_status=in_review`
- **Busca por Nome de Caderno:** `/provas/professor/revisar/?q_name=<termo>`
- **Exportação em PDF da Fila:** `/provas/professor/revisar-pdf/`
- **Revisão de Questões do Caderno:** `/provas/<exam_id>/revisar/?exam_teacher_subject=<ets_id>`
- **Navegação UI:** 
  - **Menu Lateral:** Expandir `"Cadernos"` ➔ Clicar no item submenu `"Para você revisar"`.
  - **Painel do Professor (`/painel/professor/`):** Clicar na aba central `"Revisar"` e, caso queira ver a listagem completa, clicar em `"Todas as revisões"` no rodapé.
  - **Versões legadas:** Botão/Aba `"Para você revisar"` ao lado de `"Elaboradas por você"` dentro de `"Elaboração de provas"`.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- **Persona:** Usuário autenticado com perfil Professor (`settings.TEACHER`) e coordenador de disciplina (`user.inspector.is_discipline_coordinator = True`).
- **Permissão de Acesso:** Usuários sem `inspector` ou com `is_discipline_coordinator = False` são redirecionados com mensagem de alerta: *"Você não tem permissão para acessar esta página."*.
- **Multi-tenant:** Isolamento garantido via coordenações vinculadas ao cliente (`user.get_coordinations_cache()`).
- **Setup via Mixer (Padrão canônico do módulo `inspectors/tests/test_models.py`):**

```python
from django.utils import timezone
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject, Question
from fiscallizeon.inspectors.models import Inspector, TeacherSubject
from fiscallizeon.subjects.models import Subject

# 1. Tenant e Coordenação
client = mixer.blend(Client, name="Colégio Teste QA")
unity = mixer.blend(Unity, client=client, name="Unidade Central")
coordination = mixer.blend(SchoolCoordination, unity=unity, name="Coordenação EM")

# 2. Séries e Disciplina
grade_1em = mixer.blend(Grade, name="1ª Série EM", level=Grade.HIGHT_SCHOOL)
grade_2em = mixer.blend(Grade, name="2ª Série EM", level=Grade.HIGHT_SCHOOL)
subject = mixer.blend(Subject, name="Física", client=client)

# 3. Professor Revisor (Coordenador de Disciplina)
user_revisor = mixer.blend(
    User,
    email="revisor.fisica@lize.local",
    user_type="teacher",
    two_factor_enabled=False,
    must_change_password=False,
)
revisor = mixer.blend(
    Inspector,
    user=user_revisor,
    client=client,
    coordinations=[coordination],
    is_discipline_coordinator=True,
)
ts_revisor = mixer.blend(
    TeacherSubject,
    teacher=revisor,
    subject=subject,
    active=True,
    school_year=timezone.now().year,
)

# 4. Turma da 1ª Série vinculada ao Revisor
school_class_1em = mixer.blend(
    SchoolClass,
    coordination=coordination,
    grade=grade_1em,
    school_year=timezone.now().year,
    name="101-A",
)
ts_revisor.classes.add(school_class_1em)

# 5. Outro professor elaborador
user_autor = mixer.blend(User, email="autor.fisica@lize.local", user_type="teacher")
autor = mixer.blend(Inspector, user=user_autor, client=client, coordinations=[coordination])
ts_autor = mixer.blend(TeacherSubject, teacher=autor, subject=subject, active=True, school_year=timezone.now().year)

# 6. Exame e Solicitação (ETS) da 1ª Série (Revisor leciona -> DEVE APARECER)
exam_1 = mixer.blend(
    Exam,
    name="Simulado Física 1ª Série",
    status=Exam.ELABORATING,
    review_start=timezone.now().date(),
    review_deadline=timezone.now().date(),
    coordinations=[coordination],
)
ets_1 = mixer.blend(
    ExamTeacherSubject,
    exam=exam_1,
    teacher_subject=ts_autor,
    grade=grade_1em,
    quantity=1,
)
q1 = mixer.blend(Question, client=client, grade=grade_1em)
mixer.blend(ExamQuestion, exam=exam_1, exam_teacher_subject=ets_1, question=q1)
```

## 3. Seletores DOM e Ações

### 3.1. Cabeçalho e Abas de Navegação
- **Título da Página:** `h4:has-text("Elaboração de provas")`
- **Aba "Elaboradas por você":** `a.btn.btn-outline-primary:has-text("Elaboradas por você")` (link para `{% url 'exams:exam-teacher-subject-list' %}`)
- **Aba "Para você revisar" (ativa):** `a.btn.btn-primary:has-text("Para você revisar")` (link para `{% url 'exams:exam-teacher-subject-to-review-list' %}`)

### 3.2. Filtros e Busca
- **Totalizador de Solicitações:** `h4:has-text("Exibindo")` (exibe `Exibindo X solicitações`)
- **Select de Status:** `select[name="q_status"]`
  - Opção *"Todos os cadernos"*: `select[name="q_status"] option[value=""]`
  - Opção *"Revisando"*: `select[name="q_status"] option[value="in_review"]`
  - Opção *"Aguardando revisão"*: `select[name="q_status"] option[value="await_review"]`
- **Campo de Busca:** `input[name="q_name"][type="search"]` (placeholder: *"Buscar por nome do caderno"*)
- **Botão de Submissão de Busca:** `button[type="submit"]:has(i[data-feather="search"])`

### 3.3. Cards de Cadernos para Revisão
- **Container do Card:** `.card.card-body` dentro de `.col-sm-6.col-lg-3`
- **Badge de Status:**
  - *Aguarda revisão:* `span.badge.bg-primary-soft.text-primary:has-text("Aguarda revisão")`
  - *Revisando:* `span.badge.bg-success-soft.text-success:has-text("Revisando")`
- **Informações do Card:**
  - Disciplina: `p.mb-0:has-text("{{ subject.name }}")`
  - Nome do Professor Elaborador: `p.mb-3:has-text("{{ teacher.name }}")`
  - Série do Caderno: `p:has-text("{{ grade.name }}")`
  - Nome do Caderno: `p.text-truncate:has-text("{{ exam.name }}")`
  - Categoria do Caderno: `span:has-text("Caderno de Prova")` ou `span:has-text("Caderno de atividade")`
  - Contador de Questões: `span:has-text("X de Y questões revisadas")`
- **Botão de Ação:** `a.btn.btn-success.btn-block:has-text("Revisar questões")` (link com atributo `href` contendo `/provas/<exam_id>/revisar/?exam_teacher_subject=<ets_id>`)

### 3.4. Estado Vazio (Sem cadernos para revisar)
- Quando a lista está vazia, o elemento de paginação exibe `Exibindo 0 solicitações` e nenhuma linha de cards é renderizada no container `.row.row-xs`.

## 4. API Interception & Fixtures (Rotas e Entidades Críticas)
- `GET /provas/professor/revisar/` — Rota principal server-rendered via Django ListView.
- `GET /provas/<exam_id>/revisar/?exam_teacher_subject=<ets_id>` — Rota de revisão detalhada das questões da solicitação.
- **Entidades Críticas:** `Inspector`, `TeacherSubject`, `SchoolClass`, `Grade`, `Exam`, `ExamTeacherSubject`, `ExamQuestion`, `StatusQuestion`.


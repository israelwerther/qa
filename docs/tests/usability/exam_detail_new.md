# Mapeamento de Usabilidade: exam_detail_new.html

> Template: `fiscallizeon/exams/templates/dashboard/exams/exam_detail_new.html`
> Feature: Histórico de Respostas de Alteração do Aluno (CU-86agtmuwp)

## 1. URLs e Navegação

| URL | Descrição |
|---|---|
| `/provas/<uuid>/` | Detalhe da prova — tela principal onde o modal de correção é exibido |
| `/api/v2/application-students/<uuid>/answer-history/` | Endpoint REST do histórico ( chamado via AJAX pelo modal) |

**Fluxo de navegação:**
1. Coordenador acessa `/provas/` (lista de instrumentos avaliativos).
2. Clica em uma prova para ver o detalhe (`/provas/<uuid>/`).
3. Na listagem de alunos, clica em um aluno para abrir o modal de correção (`#detailModal`).
4. Dentro do modal, clica na aba "Histórico de Marcações".
5. O JS chama `fetchAnswerHistory()` que busca `/api/v2/application-students/<uuid>/answer-history/`.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Persona
- **Coordenador** com `user_type='coordination'`, vínculo em `SchoolCoordination` via `CoordinationMember`, mesmo `Client` do aluno.
- A view também aceita: Professor (`settings.TEACHER`), Staff (`is_staff=True`), Superuser (`is_superuser=True`).

### Permissões da View
A `ApplicationStudentAnswerHistoryView` verifica:
```python
if not (
    user.is_superuser
    or user.is_staff
    or getattr(user, 'user_type', None) in (settings.COORDINATION, settings.TEACHER)
):
    return Response(..., status=status.HTTP_403_FORBIDDEN)
```

### Fixture Mínima
```python
from datetime import datetime, timedelta
from django.utils import timezone
from mixer.backend.django import mixer

client_obj = mixer.blend(Client, max_students_quantity=None)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
coord_user = mixer.blend(User, two_factor_enabled=False, is_staff=False, is_superuser=False, user_type='coordination')
mixer.blend(CoordinationMember, user=coord_user, coordination=coordination)

student = mixer.blend(Student, client=client_obj, name="Aluno Teste", enrollment_number="2403441")
exam = mixer.blend(Exam, client=client_obj, name="Simulado Teste", start_number=1, random_questions=False, random_alternatives=False)
app = mixer.blend(Application, exam=exam, date=timezone.now().date(), start=datetime.strptime("13:00:00", "%H:%M:%S").time(), end=datetime.strptime("18:00:00", "%H:%M:%S").time())
app_student = mixer.blend(ApplicationStudent, application=app, student=student, start_time=timezone.now() - timedelta(hours=2), end_time=timezone.now())

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
```

## 3. Seletores DOM e Ações

### Modal de Correção
| Elemento | Seletor | Descrição |
|---|---|---|
| Modal container | `#detailModal` | Modal principal de correção (Bootstrap modal) |
| Aba "Respostas" | Botão com `@click="studentModalTab = 'answers'"` | Aba padrão |
| Aba "Histórico de Marcações" | Botão com `@click="studentModalTab = 'history'; fetchAnswerHistory()"` | Aba de histórico |

### Conteúdo da Aba "Histórico de Marcações"
| Elemento | Seletor / Template | Descrição |
|---|---|---|
| Container da aba | `<template v-if="studentModalTab === 'history'">` | Wrapper condicional |
| Spinner de loading | `div.tw-animate-spin` dentro de `v-if="loadingAnswerHistory"` | Indicador visual |
| Mensagem de erro | `div` com `v-else-if="answerHistoryError"` | Mensagem de erro em vermelho |
| Lista de questões | `div` com `v-else-if="answerHistoryData && answerHistoryData.questions"` | Container da listagem |
| Card de questão | `div` com `v-for="q in answerHistoryData.questions"` | Card individual |
| Título "Questão X" | `h3` com `x-text="'Questão ' + q.question_number"` | Laranja (`tw-text-orange-400`) |
| Badge "X alterações" | `span` com `v-if="q.has_changes"` + `x-text="q.changes_count + ..."` | Fundo cinza |
| Badge "Sem alterações" | `span` com `v-else` estático | Fundo cinza, texto "Sem alterações" |
| Snippet do enunciado | `p` com `x-text="q.question_snippet"` | Texto cinza claro |
| Círculo da alternativa | `div` com `:class` dinâmico (verde se `is_final`, cinza caso contrário) | `tw-w-7 tw-h-7 tw-rounded-full` |
| Chevron separador | `svg` entre os círculos | `tw-w-3.5 tw-h-3.5 tw-text-slate-300` |
| Rodapé com horários | `p` com `x-text="q.first_marked_at + ' → ' + q.last_marked_at"` | Texto pequeno cinza |
| Texto "Não respondida" | `p` com `x-text` ou conteúdo estático "Não respondida pelo aluno" | Itálico |

### Alpine.js Data Store
| Propriedade | Tipo | Descrição |
|---|---|---|
| `studentModalTab` | `String` | Aba ativa: `'answers'` ou `'history'` |
| `loadingAnswerHistory` | `Boolean` | Flag de carregamento |
| `answerHistoryError` | `String` | Mensagem de erro |
| `answerHistoryData` | `Object` | Dados retornados pela API |
| `currentStudentId` | `String` | UUID do `ApplicationStudent` |

### Métodos JS
| Método | Descrição |
|---|---|
| `fetchAnswerHistory(applicationStudentId)` | Busca o histórico via `GET /api/v2/application-students/<id>/answer-history/` |
| `openStudentModal(student)` | Abre o modal e reseta estado do histórico |

## 4. Rotas de API Críticas

| Método | Rota | Headers | Descrição |
|---|---|---|---|
| `GET` | `/api/v2/application-students/<uuid>/answer-history/` | `Accept: application/json`, `X-Requested-With: XMLHttpRequest` | Retorna histórico consolidado |

### Resposta da API (200 OK)
```json
{
  "student": { "id": "uuid", "name": "...", "enrollment_number": "..." },
  "exam": { "id": "uuid", "name": "...", "is_randomized": false },
  "summary": { "total_changes": 2, "questions_changed_count": 1, "total_questions_answered": 5 },
  "questions": [
    {
      "question_id": "uuid",
      "question_number": 1,
      "subject_name": "Biologia",
      "question_snippet": "Trecho do enunciado...",
      "changes_count": 2,
      "has_changes": true,
      "first_marked_at": "13:10",
      "last_marked_at": "13:40",
      "trail": [
        { "letter": "A", "is_final": false, "marked_at": "2026-08-31T13:10:00Z" },
        { "letter": "C", "is_final": false, "marked_at": "2026-08-31T13:25:00Z" },
        { "letter": "B", "is_final": true, "marked_at": "2026-08-31T13:40:00Z" }
      ]
    }
  ]
}
```

### Erros da API
| Status | Significado |
|---|---|
| `403` | Usuário sem permissão (não é Coord/Teacher/Staff/Superuser) |
| `404` | `ApplicationStudent` não encontrado ou pertence a outro `Client` |

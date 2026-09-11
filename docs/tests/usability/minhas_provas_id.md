# Mapeamento de Usabilidade: App do Aluno (Tela de Resultados e Revisão de Questões)

> **Caminho no Código (`lize-student`):**
> - `src/routes/_app/painel/minhas-provas.$id.tsx`
> - `src/components/exam-result/disciplines-breakdown.tsx`
> - `src/components/exam-result/questions-overview.tsx`
> - `src/components/exam-result/questions-to-review.tsx`
> - `src/components/exam-result/question-review-sheet.tsx`
> - `src/types/application-result.ts`
> - `src/types/question-detail.ts`
> 
> **Caminho no Código (`lizeedu`):**
> - `fiscallizeon/app/students/views.py` (`ApplicationStudentViewSet.result`, `question_detail_with_answer`)
> - `fiscallizeon/app/students/serializers.py` (`ExamQuestionResultSerializer`)
> - `fiscallizeon/questions/services/questions.py` (`build_question_excerpt`, `get_questions_performances`)

---

## 1. URLs e Navegação

| Destino | Rota / URL | Método / Contexto |
|---|---|---|
| **App do Aluno: Minhas Provas** | `http://localhost:5173/painel/minhas-provas` | Listagem de avaliações do estudante |
| **App do Aluno: Tela de Resultado** | `http://localhost:5173/painel/minhas-provas/{application_student_id}` | Visualização detalhada do resultado |
| **API Backend: Resultado Completo** | `GET /api/v3/applications/{pk}/result/` | Payload com `questionsData` e `subjects` |
| **API Backend: Detalhes da Questão** | `GET /api/v3/applications/{pk}/question_detail_with_answer/?question_id={id}` | Detalhes, resposta do aluno e feedback |
| **API Backend: Desempenho na Matéria** | `GET /api/v3/applications/{pk}/subjects/{subject_id}/` | Estatísticas detalhadas por assunto/habilidade |

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Backend (`lizeedu`):
- O teste exige uma aplicação finalizada (`end_time` preenchido ou `release_result_at_end=True`), com respostas enviadas e corrigidas.
- Para validar o **Alternador de Área do Conhecimento**, o caderno de prova deve conter **pelo menos 2 Áreas do Conhecimento** distintas (ex.: *Linguagens e Códigos* + *Ciências da Natureza*). Se houver apenas 1 área, o front renderiza o título fixo "Disciplinas".
- As questões da prova devem conter acertos (`is_correct=True`), acertos parciais (`is_partial=True`) e erros (`is_incorrect=True`) para popular a aba "Questões para revisar".

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.students.models import Student
from fiscallizeon.clients.models import Client
from fiscallizeon.subjects.models import KnowledgeArea, Subject
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.applications.models import Application, ApplicationStudent

# 1. Criação do Cliente e Aluno
client = mixer.blend(Client, can_access_app=True)
user = mixer.blend(User, can_access_app=True, must_change_password=False)
user.set_password("123456")
user.save()
student = mixer.blend(Student, user=user, client=client)

# 2. Áreas do Conhecimento e Disciplinas
area_nat = mixer.blend(KnowledgeArea, name="Ciências da Natureza e suas Tecnologias")
area_hum = mixer.blend(KnowledgeArea, name="Ciências Humanas e suas Tecnologias")

sub_bio = mixer.blend(Subject, name="Biologia", knowledge_area=area_nat)
sub_his = mixer.blend(Subject, name="História", knowledge_area=area_hum)

# 3. Prova Multidisciplinar
exam = mixer.blend(Exam, is_abstract=True, name="Simulado Geral Multi-Áreas")
q1 = mixer.blend(Question, subject=sub_bio, enunciation="<p>Enunciado sobre citologia celular...</p>")
q2 = mixer.blend(Question, subject=sub_his, enunciation="<p>Enunciado sobre a Revolução Francesa...</p>")

mixer.blend(ExamQuestion, exam=exam, question=q1, weight=1.0)
mixer.blend(ExamQuestion, exam=exam, question=q2, weight=1.0)

# 4. Aplicação Liberada para o Aluno
app = mixer.blend(Application, exam=exam, release_result_at_end=True)
app_student = mixer.blend(ApplicationStudent, application=app, student=student)
```

---

## 3. Seletores DOM e Ações

### Abas de Primeiro Nível da Página de Resultados:
- **Aba "Informações Gerais":** `button[role="tab"]:has-text("Informações Gerais")`
- **Aba "Questões para revisar":** `button[role="tab"]:has-text("Questões para revisar")`

### Listagem em Cards de Questões (`QuestionsOverview`):
- **Container da Listagem:** `div.space-y-6` ou seção superior de questões
- **Filtros por Categoria:**
  - Todas: `button:has-text("Todas")`
  - Objetivas: `button:has-text("Objetivas")`
  - Discursivas: `button:has-text("Discursivas")`
  - Somatório: `button:has-text("Somatório")`
  - Arquivo anexado: `button:has-text("Arquivo anexado")`
- **Seletor de Ordenação:** `button[role="combobox"]`
  - Opções: `"Número (crescente)"`, `"Número (decrescente)"`, `"Acerto da turma (menor → maior)"`, `"Acerto da turma (maior → menor)"`
- **Cards de Questão (Itens):** `div[role="button"]:has(span:has-text("Q"))`
  - Número da Questão: `span.font-bold` (ex.: "Q1")
  - Badge de Status: `.bg-emerald-100` ("Acertou"), `.bg-rose-100` ("Errou"), `.bg-amber-100` ("Parcial"), `.bg-slate-200` ("Aguardando correção")
  - Trecho do Enunciado (`excerpt`): `p.line-clamp-2`
  - Acerto da Turma: `span:has-text("% de acertos")`
- **Paginação:**
  - Botão Página Anterior: `button:has(svg.lucide-chevron-left)`
  - Botão Próxima Página: `button:has(svg.lucide-chevron-right)`

### Tabela de Desempenho e Alternador de Áreas (`DisciplinesBreakdown`):
- **Alternador de Visão (Multi-Área):**
  - Aba "Disciplinas": `button[role="tab"]:has-text("Disciplinas")`
  - Aba "Área do conhecimento": `button[role="tab"]:has-text("Área do conhecimento")`
- **Tabela de Disciplinas / Áreas:** `table`
  - Linhas de Disciplina (Clicáveis): `tr[role="button"][aria-label^="Ver desempenho em"]`
  - Linhas de Área do Conhecimento: `tr` com coluna `"Área do conhecimento"`
  - Botão "Visualizar" por Área: `button:has-text("Visualizar")` (ou `button[aria-label^="Ver questões de"]`)

### Painel / Gaveta Lateral de Revisão (`QuestionReviewSheet`):
- **Container do Sheet:** `div[role="dialog"][data-state="open"]`
- **Título da Questão:** `h2:has-text("Revisar questão")` ou `span.text-3xl:has-text("Q")`
- **Setas de Navegação:**
  - Anterior: `button[aria-label="Questão anterior"]`
  - Próxima: `button[aria-label="Próxima questão"]`
- **Subtítulo (Disciplina e Área):** `span.text-sm.text-slate-500` (ex.: `"Biologia · Ciências da Natureza e suas Tecnologias"`)
- **Abas Internas da Revisão:**
  - `button:has-text("Questão")`
  - `button:has-text("Sua resposta")`
  - `button:has-text("Resposta comentada")`
  - `button:has-text("Assuntos abordados")`
  - `button:has-text("Competências")`
  - `button:has-text("Habilidades")`

### Aba "Questões para revisar" (`QuestionsToReview`):
- **Cabeçalho da Disciplina:** `h2.text-2xl.font-bold` (Nome da Disciplina) e `p.text-sm` (Área do Conhecimento)
- **Métricas da Matéria:**
  - Percentual na Prova: `p.text-5xl.font-bold`
  - Contadores: `li:has-text("questões")`, `li:has-text("acertos")`, `li:has-text("erros")`
  - Barra de Progresso e Emoji: `div.bg-primary` e `span:has-text("🚀")`
- **Seletor de Grau de Domínio (`SubjectMastery`):**
  - Select: `button[role="combobox"]` ("Assuntos", "Habilidades", "Competências")
  - Barras de Nível: `div:has(span:has-text("Grau de domínio"))`
- **Tabela de Questões a Revisar:**
  - Número da Questão: `span.rounded-full` (ex.: "1")
  - Trecho do Enunciado: `p.line-clamp-2`
  - Selo de Acerto da Turma: `span:has-text("% da turma acertou essa questão")`
  - Botão "Revisar": `button:has-text("Revisar")` (ou `button[aria-label^="Revisar questão"]`)

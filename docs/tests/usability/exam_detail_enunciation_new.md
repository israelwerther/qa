# Mapeamento de Usabilidade: exam_detail_enunciation_new

Mapeamento técnico da tela de **Correção por Enunciado** do LizeEdu para uso no acervo de QA e automação com Playwright/Mixer.

- **Template Django:** `fiscallizeon/exams/templates/dashboard/exams/exam_detail_enunciation_new.html`
- **View:** `fiscallizeon.exams.views.exams.ExamDetailEnunciationNewView`
- **URL Django:** `exams:exams_detail_enunciation_new` (`/provas/<uuid:pk>/enunciados/detalhes/`)
- **API v2 de Carregamento:** `exams:exam_question_answers_detail_v2` (`/provas/api/exam-question/<uuid:pk>/answers/v2/`)

---

## 1. URLs e Navegação

| Destino | Rótulo no menu UI | URL Django | Parâmetros GET suportados |
|---|---|---|---|
| Lista de Provas | Menu lateral ➔ Instrumentos Avaliativos (ou Cadernos) | `/provas/` | `?page=...` |
| Detalhe da Prova | Clicar na prova na listagem | `/provas/<exam_id>/detalhes/` | `?turma=<uuid>` |
| Correção por Enunciado | Botão "**Correção por enunciado**" no detalhe da prova ou no menu de ações (3 pontos) da listagem de provas | `/provas/<exam_id>/enunciados/detalhes/` | `?turma=<class_id>` e/ou `?year=YYYY` |

### Fluxo de Acesso pela UI:
1. Acesse o portal logado como **Coordenação** ou **Professor** com acesso à prova.
2. Navegue até a listagem de cadernos em `/provas/`.
3. Abra o caderno desejado ou clique no menu de opções (ícone de reticências / ações) da linha do caderno.
4. Clique no item ou botão `"**Correção por enunciado**"`.
5. Na tela aberta, selecione uma turma no dropdown `select[name="turma"]` caso não tenha sido passada por parâmetro GET.
6. A tela exibirá os cards das questões. Clique no botão `"**Corrigir**"` da questão desejada para abrir o modal de correção em tela cheia (`#detailModal`).

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Permissões Necessárias:
- O usuário deve ser do tipo `COORDINATION` (`user_type = 2`) ou `TEACHER` (`user_type = 3`) ou ter `is_superuser = True`.
- Em caso de professor, o professor deve estar vinculado à disciplina da questão ou o caderno deve permitir correção cruzada (`can_correct_questions_other_teachers = True`).

### Script Mixer para Setup de Dados de Teste:

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, TeachingInstitution
from fiscallizeon.schools.models import School
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.students.models import Student
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.corrections.models import TextCorrection, CorrectionCriterion
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.answers.models import TextualAnswer

# 1. Base Multi-tenant e Usuário
client = mixer.blend(Client, name="Escola Teste QA")
user = mixer.blend(User, client=client, user_type=2, is_superuser=True)

# 2. Caderno e Aplicação
exam = mixer.blend(Exam, created_by=user, name="Prova Diagnóstica Discursiva")
school_class = mixer.blend(SchoolClass, name="3º Ano EM A")
application = mixer.blend(Application, exam=exam, deadline_for_correction_of_responses=None)
application.school_classes.add(school_class)

# 3. Rubrica/Template de Correção (Critérios)
text_correction = mixer.blend(TextCorrection, client=client, name="Rubrica Padrão ENEM")
c1 = mixer.blend(CorrectionCriterion, text_correction=text_correction, name="Domínio da norma culta", order=1, maximum_score=2.0)
c2 = mixer.blend(CorrectionCriterion, text_correction=text_correction, name="Proposta de intervenção", order=2, maximum_score=2.0)

# 4. Questão Discursiva com Rubrica
question = mixer.blend(Question, category=Question.TEXTUAL, text_correction=text_correction, enunciation="Escreva uma proposta de intervenção.")
exam_question = mixer.blend(ExamQuestion, exam=exam, question=question, weight=10.0)

# 5. Aluno com Resposta
student = mixer.blend(Student, client=client, name="Ana Silva")
school_class.students.add(student)
app_student = mixer.blend(ApplicationStudent, application=application, student=student)
answer = mixer.blend(TextualAnswer, question=question, student_application=app_student, content="Minha resposta dissertativa para avaliação.")
```

---

## 3. Seletores DOM e Ações

### 3.1. Tela Principal (Filtros e Cards)

| Elemento | Seletor Estável / Ação | Descrição / Contexto Visual |
|---|---|---|
| Dropdown de Turmas | `select[name="turma"]` | Dropdown no topo para filtrar a turma exibida |
| Filtro "Todas" | `button:has-text("Todas")` | Pill de filtro para exibir todas as questões |
| Filtro "Dissertativas" | `button:has-text("Dissertativas")` | Pill de filtro para exibir Discursivas e Arquivo anexado |
| Filtro "Objetivas" | `button:has-text("Objetivas")` | Pill de filtro para exibir questões objetivas |
| Filtro "Somatórias" | `button:has-text("Somatórias")` | Pill de filtro para exibir somatórias |
| Grid de Questões | `div[role="list"]` | Container com os cards de cada questão |
| Card de Questão | `div[role="list"] > div:has(h3:has-text("Questão <N>"))` | Card individual contendo métricas e enunciado |
| Botão Corrigir da Questão | `div:has(h3:has-text("Questão <N>")) button:has-text("Corrigir")` | Botão branco com borda cinza que abre o modal |

### 3.2. Modal de Correção em Tela Cheia (`#detailModal`)

| Elemento | Seletor Estável / Ação | Descrição / Contexto Visual |
|---|---|---|
| Container do Modal | `#detailModal` | Modal full-screen de correção |
| Botão "Anterior" | `#detailModal button:has-text("Anterior")` | Navega para a questão anterior |
| Botão "Próximo" | `#detailModal button:has-text("Próximo")` | Navega para a próxima questão |
| Botão Fechar Modal | `#detailModal button[data-dismiss="modal"]` | Ícone de fechar (X) no canto superior direito |
| Título da Questão | `#detailModal p.tw-text-orange-400` | Exibe `Questão X` |
| Valor da Questão | `#detailModal span:has-text("Valor da questão:")` | Badge com o peso/nota máxima da questão |
| Expansor do Enunciado | `#detailModal button[aria-controls="collapseEnunciation"]` | Botão `"Detalhes da questão"` com chevron giratório |
| Container Acordeon Alunos | `#answers-accordion` | Lista colapsável de respostas por aluno |
| Cabeçalho do Aluno | `#answers-accordion h6:has-text("<Nome do Aluno>")` | Clicar seleciona o aluno e hidrata as notas |
| Tabela de Critérios | `#answers-accordion table:has(th:has-text("Competências"))` | Tabela com critérios e notas discursivas |
| Botão Opção do Critério | `label[for^="line-competence-enem-"]` | Botão pill com o valor do critério (ex.: 0,00, 1,00, 2,00) |
| Opção Selecionada | `label.tw-bg-blue-50.tw-text-blue-700` | Pill do critério quando ativo/selecionado |
| Input de Nota Final | `input#grade` | Campo da nota final (disabled com rubrica) |
| Input de Nota Livre | `input[id^="inputSetGrade-"]` | Campo de nota para questões sem rubrica |
| Atalhos Rápidos de Nota | `button:has-text("25%")`, `50%`, `75%`, `100%`, `button[title="Atribuir nota zero"]` | Botões coloridos de nota rápida (0% a 100%) |
| Textarea de Feedback | `textarea#feedback-textarea` | Campo para comentário personalizado do professor |
| Botão Salvar | `#answers-accordion button:has-text("Salvar")` | Botão roxo/primário que persiste as notas no backend |
| Indicador de Status | `#answers-accordion span:has-text("Correção salva!")` | Texto informativo de confirmação de gravação |
| Indicador de Erro | `#answers-accordion span:has-text("Erro no envio, tente novamente")` | Alerta em vermelho quando a gravação falha |

---

## 4. Rotas de API Críticas e Interceptações

| Endpoint | Método | Descrição |
|---|---|---|
| `/provas/api/exam-question/<id>/answers/v2/?class=<id>&year=<year>` | GET | Carga em lote O(1) de alunos, respostas e `criterion_scores` |
| `/correcoes/api/textuais/` | POST | Criação inicial de registro de nota por critério (Textual) |
| `/correcoes/api/textuais/<id>/` | PUT | Atualização (regravação) do registro de critério existente |
| `/correcoes/api/arquivos/` | POST | Criação inicial de nota por critério (Arquivo anexado) |
| `/correcoes/api/arquivos/<id>/` | PUT | Atualização de critério para questão de arquivo anexado |
| `/respostas/api/textuais/<id>/feedback/` | PUT | Atualização da nota total (`teacher_grade`) e comentário |

# Mapeamento de Usabilidade: student_individual_tracking.html

Mapeamento técnico da tela de **Acompanhamento Individual do Aluno** (`student_individual_tracking.html`), incluindo o modal de seleção (`student_tracking_modal.html`), cabeçalho com KPIs, abas de Linha do Tempo e Desempenho, expansão por aplicação com tabela por disciplina e modal de exportação de histórico.

---

## 1. URLs e Navegação

### Rotas de Interface (Páginas Web)
- **Entrada Principal (Hub de Relatórios):**
  - URL: `/dashboards/reports/` (View `ReportsTemplateView`, namespace `dashboards:report`)
  - Elemento de Disparo: Card `"**Acompanhamento Individual de Alunos**"` na categoria `"Pessoas"`.
  - Disparo do Modal: Clique no card abre o componente `student_tracking_modal` via evento Alpine `$dispatch('student-tracking-open', { reset: true })`.
- **Ficha do Aluno (URL Canônica):**
  - Rota Django: `reverse('students:students_individual_tracking', kwargs={'pk': student_pk})`
  - URL: `/alunos/<uuid:student_pk>/acompanhamento/`
  - Query Params de Contexto (Pager e Ano Letivo):
    `/alunos/<uuid:student_pk>/acompanhamento/?class_id=<uuid:class_id>&grade_id=<uuid:grade_id>&school_year=<ano_letivo>`
- **Navegação de Retorno:**
  - Breadcrumb / Botão Voltar: link para `/dashboards/reports/` (`reports_url`).

### APIs Internas Consumidas pela Tela
| Rota / Endpoint | Método | Função / Payload |
|---|---|---|
| `GET /alunos/api/acompanhamento/turmas/` | GET | Lista turmas autorizadas por nível e ano letivo (`IndividualTrackingClassListAPIView`) |
| `GET /alunos/api/acompanhamento/turmas/<uuid:class_id>/alunos/` | GET | Lista alunos da turma selecionada (`IndividualTrackingClassStudentsAPIView`) |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/timeline/` | GET | Eventos paginados da linha do tempo (`StudentTimelineAPIView`) com filtros de presença, disciplina, período e categoria |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/media/` | GET | Média geral do aluno e comparativo da turma (`StudentAverageAPIView`) |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/etapas/` | GET | Evolução por etapa letiva (`StudentStagePerformanceAPIView`) |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/avaliacoes/resumo/` | GET | Lista de disciplinas presentes nas avaliações (`StudentChallengeOverviewAPIView`) |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/avaliacoes/` | GET | Desempenho avaliação a avaliação (`StudentChallengePerformanceAPIView`) |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/disciplinas/` | GET | Desempenho geral por disciplina (`StudentSubjectPerformanceAPIView`) |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/aplicacoes/` | GET | Lista paginada de aplicações com status e nota (`StudentApplicationListAPIView`) |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/aplicacoes/<uuid:application_student_pk>/disciplinas/` | GET | Detalhamento de questões, acertos, erros, parciais, desempenho e nota por disciplina (`StudentApplicationSubjectsAPIView`) |
| `GET /alunos/api/acompanhamento/<uuid:student_pk>/historico/filtros/` | GET | Opções de unidades, turmas e disciplinas para o modal de exportação (`StudentHistoryExportFiltersAPIView`) |
| `POST /alunos/api/acompanhamento/<uuid:student_pk>/historico/` | POST | Enfileira a task Celery de exportação individual (`StudentHistoryExportAPIView`) |
| `GET /exportar/provas/status/<uuid:export_id>/` | GET | Polling do status da task assíncrona Celery (`ExamsExportResultsTaskStatusView`) |

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Perfis de Acesso Autorizados
- **Coordenação:** Membro de `CoordinationMember` com cliente ativo possuindo `has_reports=True`. Coordenação precisa estar vinculada à unidade e turmas do aluno.
- **Professor:** Requer `has_reports=True`, `Inspector` vinculado e vínculo ativo em `TeacherSubject` para turmas e disciplinas onde o aluno está matriculado.
- **Aluno / Responsável:** Acesso restrito ou negado (não acessam a visão de coordenação da ficha).

### Snippet Mixer para Setup de Dados
```python
from datetime import date
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamTeacherSubject
from fiscallizeon.inspectors.models import Inspector, TeacherSubject
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import KnowledgeArea, Subject

# 1. Setup Tenant & Instituição
client = mixer.blend(
    Client,
    type_client=1,
    two_factor_enabled=False,
    has_reports=True,
)
unity = mixer.blend(Unity, client=client, name="Unidade Central")
coordination = mixer.blend(SchoolCoordination, unity=unity)

# 2. Usuário Coordenação
user_coord = mixer.blend(
    User,
    client=client,
    is_staff=False,
    two_factor_enabled=False,
    is_freemium=False,
)
mixer.blend(CoordinationMember, user=user_coord, coordination=coordination)

# 3. Nível e Turma
grade = mixer.blend(Grade, level=Grade.HIGHT_SCHOOL, name="1ª Série")
school_class = mixer.blend(
    SchoolClass,
    coordination=coordination,
    grade=grade,
    school_year=2026,
    name="1º Ano A",
)

# 4. Aluno
user_student = mixer.blend(User, client=client, first_name="Ana", last_name="Silva")
student = mixer.blend(
    Student,
    user=user_student,
    client=client,
    enrollment_number="2026001",
)
school_class.students.add(student)

# 5. Disciplina e Prova com Múltiplas Disciplinas
ka = mixer.blend(KnowledgeArea, client=client, name="Ciências Humanas")
subject_hist = mixer.blend(Subject, client=client, name="História", knowledge_area=ka)
subject_geo = mixer.blend(Subject, client=client, name="Geografia", knowledge_area=ka)

exam = mixer.blend(Exam, client=client, name="Simulado Geral 1")
mixer.blend(ExamTeacherSubject, exam=exam, subject=subject_hist)
mixer.blend(ExamTeacherSubject, exam=exam, subject=subject_geo)

app = mixer.blend(Application, exam=exam, date=date.today(), status=Application.APPLIED)
app_student = mixer.blend(
    ApplicationStudent,
    application=app,
    student=student,
    start_time=date.today(),
)
```

---

## 3. Seletores DOM e Ações

### 3.1. Modal de Seleção (`student-tracking-modal`)
| Elemento | Seletor Estável | Tipo | Finalidade |
|---|---|---|---|
| Card de Disparo | `[data-component="report_card_grid"] button:has-text("Acompanhamento Individual de Alunos")` | Click | Abre o modal no Hub de Relatórios |
| Título do Modal | `h2:has-text("Acompanhamento Individual")` | Texto | Validação de abertura do modal |
| Subtítulo do Modal | `p:has-text("Qual aluno você quer acompanhar?")` | Texto | Orientação de preenchimento do modal |
| Passo 1: Nível | `button:has-text("Ensino Médio")` (ou outro nível) | Click | Seleciona o nível de ensino |
| Passo 2: Busca Turma | `input#student-tracking-search-class` | Digitação | Filtra lista de turmas por nome |
| Passo 2: Botão Turma | `div[x-show="step === 2"] button:has-text("1º Ano A")` | Click | Seleciona a turma desejada |
| Passo 3: Busca Aluno | `input#student-tracking-search-student` | Digitação | Filtra lista de alunos por nome/matrícula |
| Passo 3: Selecionar Aluno | `div[x-show="step === 3"] button:has-text("Ana Silva")` | Click | Marca o aluno (ganha badge "Selecionado") |
| Botão Confirmar | `button:has-text("Confirmar")` | Click | Executa navegação para a ficha individual |
| Botão Cancelar | `button:has-text("Cancelar")` | Click | Fecha o modal sem navegar |

### 3.2. Cabeçalho e Pager (`individual_tracking_header`)
| Elemento | Seletor Estável | Tipo | Finalidade |
|---|---|---|---|
| Nome do Aluno | `h1#ficha-aluno-nome` | Texto | Nome completo do estudante |
| Pager - Posição | `nav[aria-label="Outros alunos da turma"] span:has-text("de")` | Texto | Ex.: "1 de 28 · 1º Ano A" |
| Pager - Anterior | `a[aria-label="Aluno anterior"]` / `button[aria-label="Sem aluno anterior"]` | Link/Botão | Navega para o aluno anterior ou fica desabilitado |
| Pager - Próximo | `a[aria-label="Próximo aluno"]` / `button[aria-label="Sem próximo aluno"]` | Link/Botão | Navega para o próximo aluno ou fica desabilitado |
| Botão Exportar | `button[data-export-history-trigger]` ou `button:has-text("Exportar histórico")` | Click | Abre o modal de exportação de histórico |
| Cards de KPI (Geral) | `dl.tw-grid dt:has-text("Média geral")`, `dt:has-text("Taxa de presença")`, `dt:has-text("Posição na turma")` | Contêiner | Cards de indicadores agregados no topo |

### 3.3. Abas Principais
| Elemento | Seletor Estável | Tipo | Finalidade |
|---|---|---|---|
| Gatilho Linha do Tempo | `button[role="tab"]:has-text("Linha do tempo")` | Click | Alterna para o painel de linha do tempo |
| Gatilho Desempenho | `button[role="tab"]:has-text("Desempenho")` | Click | Alterna para o painel de gráficos e aplicações |

### 3.4. Aba Linha do Tempo (`individual_tracking_timeline_panel`)
| Elemento | Seletor Estável | Tipo | Finalidade |
|---|---|---|---|
| Segmento Presença | `div[role="radiogroup"][aria-label="Presença"] button:has-text("Todas")` / `"Presentes"` / `"Ausentes"` | Click | Filtra presença/ausência na timeline |
| Botão Menu Filtros | `button:has-text("Filtros")` | Click | Abre dropdown com filtros de categorias e disciplinas |
| Select Disciplina | `select#timeline-subject` | Change | Filtra por disciplina específica |
| Select Período | `select#timeline-period` | Change | Filtra por Ano letivo, Últimos 30 dias ou Etapa |
| Badges de Filtro Ativo | `div[x-show="timelineFilterBadges.length"] button` | Click | Remove filtro ativo |
| Lista de Eventos | `div[data-application-student]` | Contêiner | Itens agrupados por mês cronológico |

### 3.5. Aba Desempenho (`individual_tracking_performance_panel` e Gráficos)
| Elemento | Seletor Estável | Tipo | Finalidade |
|---|---|---|---|
| Select Etapa Letiva | `select[x-model="stageId"]` | Change | Recorta gráficos e médias por etapa |
| Gráfico Evolução | `section[aria-labelledby="individual-tracking-stages-title"]` | Seção | Contém canvas ECharts de etapas |
| Gráfico Avaliação a Avaliação | `section[aria-labelledby="individual-tracking-challenges-title"]` | Seção | Contém canvas ECharts de provas |
| Pílulas Disciplina (Gráfico) | `div[role="radiogroup"][aria-label="Disciplina do gráfico"] button` | Click | Filtra a prova por disciplina |
| Seção Por Aplicação | `section[aria-labelledby="individual-tracking-applications-title"]` | Seção | Listagem de aplicações do aluno |
| Pílulas Tipo Aplicação | `div[role="radiogroup"][aria-label="Tipo de aplicação"] button` | Click | Filtra por Todas, Simulado, etc. |
| Linha da Aplicação (Accordion) | `li[data-tracking-application] button[aria-controls^="aplicacao-"]` | Click | Expande a aplicação para ver disciplinas |
| Tabela de Disciplinas | `div[data-application-subjects] table` | Tabela | Exibe colunas Disciplina, Questões, Acertos, Parciais, Erros, Desempenho, Nota |
| Link Correção Q×Q | `a:has-text("Correção questão a questão")` | Link | Redireciona para o espelho de correção da prova |
| Link Linha do Tempo da Prova | `a:has-text("Linha do tempo da prova")` | Click | Alterna para a aba Linha do Tempo e foca o evento |

### 3.6. Modal de Exportação (`individual-tracking-history-export`)
| Elemento | Seletor Estável | Tipo | Finalidade |
|---|---|---|---|
| Período (Ano / Personalizado) | `button[data-export-history-period="year"]` / `"custom"` | Click | Alterna entre Ano Letivo e Datas Personalizadas |
| Data Início | `input#export-history-start-date` | Digitação | Data de início do período customizado |
| Data Fim | `input#export-history-end-date` | Digitação | Data de fim do período customizado |
| Filtro Aplicações | `button[data-export-history-presence="all"]` / `"present"` / `"absent"` | Click | Todas / Só presentes / Só ausentes |
| Select Unidade | `select#export-history-unity` | Change | Filtra unidade |
| Select Turma | `select#export-history-school-class` | Change | Filtra turma |
| Select Disciplina | `select#export-history-subject` | Change | Filtra disciplina específica |
| Checkbox Unidade e Turma | `input[data-export-history-extra-columns]` | Check | Adiciona colunas Unidade e Turma |
| Checkbox Separar por Disciplina | `input[data-export-history-separate]` | Check | Divide linhas por disciplina |
| Formato XLSX / CSV | `button[data-export-history-format="xlsx"]` / `"csv"` | Click | Escolhe formato do arquivo |
| Preview Nome do Arquivo | `[data-export-history-filename]` | Texto | Exibe nome gerado para o arquivo |
| Botão Exportar (Submit) | `button[data-export-history-submit]` | Click | Dispara geração e download assíncrono via Celery |
| Botão Cancelar | `button:has-text("Cancelar")` | Click | Fecha modal de exportação |


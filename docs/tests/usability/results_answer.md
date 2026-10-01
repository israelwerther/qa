# Mapeamento de Usabilidade: results_answer.html

> Template: `fiscallizeon/dashboards/templates/dashboards/details/results_answer.html`
> Feature: Correções de UI — Resultados do gabarito (CU-86ajftbkg)
> Componentes: `answer_questions`, `answer_students`, `answer_comparative`, `question_card`, `question_list`, `students_list`, `performance_list`, `histogram_distribution`, `results_answer_shared`, `results_answer_report`

## 1. URLs e Navegação

| URL | Descrição |
|---|---|
| `/dashboards/ver-resultados/?exam_id=<uuid>&application_id=<uuid>` | Página Resultados do gabarito — shell com KPIs + tabs Questões / Alunos / Comparativo |
| `/dashboards/ver-resultados/aba/questoes/enunciados/?<query>` | Endpoint JSON de enunciados (lazy, via `page_config.questionsEnunciationsUrl`) |
| `/dashboards/ver-resultados/impressao/?<query>&sections=students,comparative` | HTML de impressão sob demanda (abas Alunos + Comparativo) |
| `/dashboards/get-data/<client_pk>/` | API genérica de dados (`page_config.apiUrl`, ECharts/histograma) |

**Fluxo de navegação:**
1. Coordenador/Professor logado acessa `/dashboards/ver-resultados/?exam_id=<uuid>&application_id=<uuid>` (link vem do dashboard de avaliações ou direto com query).
2. Shell `redesign/base_component.html` renderiza header (`answer_header` com "Resultado do <exam_name>") + KPIs (Alunos, Questões, Objetivas, Discursivas).
3. Tabs de primeiro nível (Alpine `activeTab`): `tab1` "**Questões**", `tab2` "**Alunos**", `tab3` "**Comparativo**" (`li[role=presentation] > span[role=tab]`).
4. Aba Questões: toggle de visão Simples/Detalhado dentro de `answer_questions`; grade Simples (`x-ref="simpleGrid"`) vs lista `question_list` (accordion `flat_trigger=True`).
5. Aba Alunos: `answer_students` em modo `lazy_load=True`; cada aluno é um accordion próprio (`students_list` SSR ou bloco `x-for` Alpine) com abas internas Disciplinas/Assuntos/Habilidades/Competências.
6. Aba Comparativo: `answer_comparative` com fileira de tabs principais + linhas `performanceListItem` expansíveis com drill.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Persona
- **Coordenação** (`user_type='coordination'`) ou **Professor** (`user_type='teacher'`) do mesmo `Client` da prova/aplicação.
- View `ResultsAnswerView` exige `required_permissions = [settings.COORDINATION, settings.TEACHER]` + `LoginRequired2FAMixin` (2FA desabilitado no setup: `two_factor_enabled=False`).
- Para Playwright local, elevar para `is_superuser=True` se faltar vínculo de coordenação (padrão do acervo).

### Fixture Mínima
```python
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client
from fiscallizeon.accounts.models import User

client_obj = mixer.blend(Client)
coord_user = mixer.blend(
    User,
    user_type='coordination',
    two_factor_enabled=False,
    must_change_password=False,
    is_superuser=True,  # garante visibilidade sem montar CoordinationMember
)
# Avaliação com dados: Exam + Application + ApplicationStudent + questões
# (usar builders de ResultsAnswerContextBuilder; para vazio, basta exam sem students/questions)
# page.goto(f"/dashboards/ver-resultados/?exam_id={exam.pk}&application_id={app.pk}")
```

### Permissões da View
```python
class ResultsAnswerView(LoginRequired2FAMixin, CheckHasPermission, TemplateView):
    required_permissions = [settings.COORDINATION, settings.TEACHER]
    template_name = 'dashboards/details/results_answer.html'
```

## 3. Seletores DOM e Ações

### Shell + Tabs de primeiro nível
| Elemento | Seletor | Descrição |
|---|---|---|
| Root Alpine | `#results-answer-report-root[x-data="resultsAnswerReport()"]` | Escopo de `activeTab`, `kpis`, `tabs.tab2/tab3`, `questions` |
| Page config | `#results-answer-page-config` | `json_script` com `examId`, `applicationId`, `apiUrl`, `printUrl` |
| Tab Questões | `li[role="presentation"]:has(span:text("Questões"))` | `setTab('tab1')` |
| Tab Alunos | `li[role="presentation"]:has(span:text("Alunos"))` | `setTab('tab2')` |
| Tab Comparativo | `li[role="presentation"]:has(span:text("Comparativo"))` | `setTab('tab3')` |
| KPIs erro | `span.tw-text-gray-500:text("—")` | Traço em erro (antes `gray-400`) |

### Aba Alunos — item accordion (SSR `students_list` + lazy `answer_students`)
| Elemento | Seletor / Classe real | Descrição |
|---|---|---|
| Trigger do aluno | `div.tw-w-full.tw-p-6.hover:tw-bg-gray-100` + `:class="expanded ? 'tw-bg-gray-50' : 'tw-bg-white'"` | Full-width, **sem** `tw-rounded-xl` / `tw-rounded-t-xl` (requisito) |
| Nome + turma | `span.tw-text-sm.tw-font-semibold` + `span[data-student-class-label].tw-text-xs.tw-text-gray-500` | Copy auxiliar em `gray-500` |
| Percentual | `span.tw-text-sm.tw-font-semibold` + `span.tw-text-[10px].tw-text-gray-500:text("de acertos")` | Legenda em `gray-500` |
| Chevron | `svg.tw-text-gray-400` com `:class="expanded ? 'tw-rotate-180' : ''"` | Decorativo, permanece `gray-400` (não alterar) |
| Contador | `[data-students-count]` | `tw-text-xs tw-text-gray-500` |
| Loading / vazio | `div:text("Carregando alunos...")`, `div:text("Nenhum resultado disponível para esta avaliação.")` | `tw-text-sm tw-text-gray-500` |
| Filtro sem resultado | `p:text("Nenhum aluno encontrado para os filtros selecionados.")` | `tw-text-sm tw-text-gray-500` |
| Abas internas (pills compactas) | `button.tw-px-4.tw-py-2.tw-rounded-md.tw-shrink-0` | Disciplinas/Assuntos/Habilidades/Competências — **não** `flex-1` |
| Vazios internos | `p:text("Nenhuma disciplina encontrada.")` (e assuntos/habilidades/competências) | `tw-text-gray-500` |

### Aba Questões — Simples (`answer_questions` + `question_card`)
| Elemento | Seletor / Classe real | Descrição |
|---|---|---|
| Grade Simples | `div.tw-grid.tw-grid-cols-1.md:tw-grid-cols-2.tw-gap-5.tw-items-stretch[x-ref="simpleGrid"]` | Stretch da linha |
| Wrapper do item | `div[data-question-item][data-question-id]` com `tw-flex tw-h-full tw-min-h-0 tw-flex-col` | Altura total |
| Card raiz | `div.tw-relative.tw-h-full.tw-min-h-full.tw-flex-1.tw-bg-white...tw-rounded-xl.tw-p-7` | `h-full` + `flex-col` |
| Cabeçalho | `div.tw-flex.tw-items-start.tw-justify-between.tw-min-h-[4.5rem]` + `div.tw-flex-col.tw-justify-center.tw-flex-1` | Alinhamento com meta curta |
| Meta | `span.tw-text-xs.tw-text-gray-500` | `subject • type • difficulty` |
| Corpo alternativas | `div.tw-flex.tw-flex-col.tw-gap-2.tw-flex-1` | Stretch interno |
| Vazios | `p:text("Nenhuma questão encontrada.")` | `tw-text-sm tw-text-gray-500` |

### Aba Questões — Detalhado (`question_list` + `accordion flat_trigger`)
| Elemento | Seletor | Descrição |
|---|---|---|
| Accordion questão | `{% component "accordion" show_border=True flat_trigger=True %}` | Trigger retangular full-width |
| Trigger flat | `div.tw-w-full.tw-p-6.hover:tw-bg-gray-100` + `:class="expanded ? 'tw-bg-gray-50' : 'tw-bg-white'"` + `tw-items-center` | Sem `rounded-xl` (vs default `rounded-xl`/`rounded-t-xl` + `items-start`) |
| Subtítulo questão | `span.tw-text-xs.tw-text-gray-500` | Meta da questão |

### Aba Comparativo (`answer_comparative` + `performance_list`)
| Elemento | Seletor / Classe real | Descrição |
|---|---|---|
| Fileira tabs principais | `div.no-print.tw-flex.tw-w-full.tw-items-center.tw-bg-gray-50.tw-rounded-lg.tw-p-1` + `max-md:tw-gap-1 max-md:tw-overflow-x-auto` | Scroll horizontal em mobile |
| Botão tab principal | `button.tw-flex-1.tw-min-w-0...tw-rounded-md` + `max-md:tw-flex-none` | `flex-1` em `md+` |
| Linha desempenho trigger | `div.tw-p-6.hover:tw-bg-gray-100...tw-items-center` + `:class="expanded ? 'tw-bg-gray-50' : 'tw-bg-white'"` | Item clicável |
| Coluna título | `div.tw-flex.tw-flex-col.tw-min-w-0.tw-flex-1.tw-min-h-[2.25rem]` + `:class="subtitle ? '' : 'tw-justify-center'"` | Centraliza quando sem subtítulo |
| Título / subtítulo | `span.tw-text-sm.tw-font-semibold.tw-truncate` + `span[x-show="subtitle"].tw-text-xs.tw-text-gray-500` | Subtítulo oculto (`x-show`) se vazio — sem linha fantasma |
| SSR (`performance_list`) | `div.tw-min-h-[2.25rem]{% if not subtitle %} tw-justify-center{% endif %}` + `{% if subtitle %}<span class="tw-text-xs tw-text-gray-500">` | Mesma regra server-side |
| Legendas | `span.tw-text-[10px].tw-text-gray-500` ("Respostas"/"Acertos"/"Erros"/"de acertos") | Antes `gray-400` |
| Spinner | `svg.tw-animate-spin.tw-h-6.tw-w-6.tw-text-gray-500` | Antes `gray-400` |
| Vazios | `div.tw-py-16.tw-text-sm.tw-text-gray-500:text("Nenhum resultado disponível...")`, `p.tw-text-xs.tw-text-gray-500[x-text="emptyMessage()"]` | Antes `gray-400`/`gray-300` |

### Histograma
| Elemento | Seletor | Descrição |
|---|---|---|
| Legenda eixos | `p.tw-mt-2.tw-text-center.tw-text-[10px].tw-text-gray-500` ("Eixo Y... · Eixo X...") | Também gerado via JS em `results_answer_shared.js` |
| Vazio | `div.tw-py-16.tw-text-sm.tw-text-gray-500:text("Nenhum resultado disponível para exibir o histograma.")` | `histogram_distribution.html` |

### Alpine.js Stores / Componentes
| Propriedade | Contexto |
|---|---|
| `activeTab` (`tab1`/`tab2`/`tab3`) | `resultsAnswerReport()` em `#results-answer-report-root` |
| `view` (`individual`/`histograma`, `simples`/`detalhado`) | `answer_students`, `answer_questions` |
| `expanded`, `toggle()`, `tab`, `setTab()` | Item de aluno, `performanceListItem(item, tabId)`, comparativo |
| `flat_trigger` (bool, default `false`) | `components/accordion/accordion.py` — só `question_list` passa `true` |
| `visibleItems(tabId)`, `tabItems(tab)`, `isTabLoading()`, `sortOrder()` | `answer_comparative` / `performance_list` / `students_list` |

## 4. Rotas de API Críticas

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/dashboards/ver-resultados/?exam_id=<uuid>&application_id=<uuid>` | HTML principal (SSR + lazy via Alpine) |
| `GET` | `/dashboards/ver-resultados/aba/questoes/enunciados/?<query>` | Enunciados das questões (lazy) |
| `GET` | `/dashboards/get-data/<client_pk>/?...` | Dados de serviço (students/comparative/charts) |
| `GET` | `/dashboards/ver-resultados/impressao/?...&sections=students,comparative` | Fragmentos de impressão |

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-11-18 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Students / Reports / Analytics / Exports |
| **Nível de Risco:** | Alto (módulo novo de acompanhamento individual, gráficos ECharts integrados ao Analytics, agregação de disciplinas, exportação assíncrona ERP no Celery e isolamento multi-tenant) |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5 estrelas — proposta, design com decisões D1 a D11, spec com cenários normativos, tasks e spike 5.1 documentados) |
| **Task ClickUp:** | [86ak8t6rp](https://app.clickup.com/t/3120759/86ak8t6rp) — *Detalhes do aluno: desempenho por disciplina + exportação* |
| **Branch:** | `feat/detalhes-aluno-CU-86ak8t6rp` |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend & APIs
- **Nova View da Ficha Individual:** Criada `StudentIndividualTrackingView` (`/alunos/<uuid:pk>/acompanhamento/`) em paralelo à view legada `StudentDetailView`, preservando o código antigo sem regressão.
- **Mixins de Permissão e Escopo:** Implementados `StudentIndividualTrackingViewMixin`, `StudentTrackingAPIGateMixin` e funções de escopo em `fiscallizeon/students/individual_tracking/` (`permissions.py`, `scope.py`, `pager.py`, `school_year.py`), restringindo acesso por `Client`, coordenações ativas do usuário e vínculos docentes em `TeacherSubject`.
- **Extração de Service de Disciplinas:** Criado `application_student_subjects.py` em `fiscallizeon/applications/services/`, desacoplando a lógica de cálculo por disciplina de `TeacherSubjectListFromApplication` e eliminando o consumo direto do endpoint legado da coordenação.
- **Endpoints de Desempenho e Seções:**
  - `GET /alunos/api/acompanhamento/<uuid:student_pk>/media/` (`StudentAverageAPIView`): média do aluno e comparativo da turma.
  - `GET /alunos/api/acompanhamento/<uuid:student_pk>/etapas/` (`StudentStagePerformanceAPIView`): séries de evolução por etapa letiva.
  - `GET /alunos/api/acompanhamento/<uuid:student_pk>/avaliacoes/resumo/` e `/avaliacoes/` (`StudentChallengePerformanceAPIView`): avaliações individuais filtráveis por disciplina.
  - `GET /alunos/api/acompanhamento/<uuid:student_pk>/disciplinas/` (`StudentSubjectPerformanceAPIView`): médias por disciplina.
  - `GET /alunos/api/acompanhamento/<uuid:student_pk>/aplicacoes/` (`StudentApplicationListAPIView`): listagem paginada de aplicações com status e nota.
  - `GET /alunos/api/acompanhamento/<uuid:student_pk>/aplicacoes/<uuid:app_student_pk>/disciplinas/` (`StudentApplicationSubjectsAPIView`): detalhamento de questões, acertos, parciais, erros, desempenho e nota por disciplina.
  - `GET /alunos/api/acompanhamento/<uuid:student_pk>/timeline/` (`StudentTimelineAPIView`): agregação cronológica de eventos reais de `ApplicationStudent`, `Event`, `Annotation` e `TextMessage`.
- **Exportação Individual Assíncrona:**
  - `StudentHistoryExportAPIView` e `StudentHistoryExportFiltersAPIView` enfileiram a task Celery `export_exams_erp` com parâmetro `student_pk`.
  - Revalidação defensiva no worker (`restrict_application_students_to_student_scope`) garantindo que apenas dados daquele aluno e do tenant autorizado sejam gerados.
  - Suporte a formatos `.xlsx` e `.csv`, filtros de presença (Todas, Presentes, Ausentes), período (ano letivo ou datas customizadas) e opção de separar por disciplina.

### Frontend & UI
- **Modal de Seleção de Aluno (`student_tracking_modal`):**
  - Card integrado ao Hub de Relatórios (`/dashboards/reports/`) na categoria `"Pessoas"`.
  - Fluxo assistido em 3 passos: 1. Nível de ensino ➔ 2. Turma (com busca dinâmica e paginação) ➔ 3. Aluno (com busca, avatar e seleção).
  - Confirmação navega diretamente para a ficha individual preservando query params de contexto (`class_id`, `grade_id`, `school_year`).
- **Cabeçalho da Ficha (`individual_tracking_header`):**
  - Identificação completa do aluno (avatar com iniciais, nome, série/turma, matrícula e responsável).
  - Pager contextual ("n de total") com links anterior/próximo navegando estritamente dentro da turma autorizada.
  - Botão de atalho para `"Exportar histórico"`.
  - 3 Cards de KPI: Média geral (com comparativo de turma), Taxa de presença e Posição na turma — exibidos apenas quando houver dados reais, com estados de fallback e sem fórmulas artificiais.
- **Abas Principais (Tabs Redesign):**
  - Alternância rápida via Alpine.js entre `"Linha do tempo"` e `"Desempenho"`.
- **Aba Linha do Tempo (`individual_tracking_timeline_panel`):**
  - Segmentação rápida por presença (Todas, Presentes, Ausentes).
  - Dropdown de filtros com categorias (Avaliações e ausências, etc.), filtro por disciplina e período (ano letivo, últimos 30 dias ou etapa letiva).
  - Pílulas/badges de filtros ativos com remoção em um clique.
  - Agrupamento visual por mês em ordem cronológica decrescente.
- **Aba Desempenho (`individual_tracking_performance_panel`):**
  - Média geral com seletor de etapa letiva ("Todas as etapas" ou etapa específica).
  - Gráfico ECharts de "Evolução por etapa letiva" com barras comparativas aluno vs. turma.
  - Gráfico ECharts de "Avaliação a avaliação" com seletor de disciplinas em pílulas.
  - Seção "Por disciplina" com barras de progresso e expansão de aplicações vinculadas.
  - Seção "Por aplicação" com acordeão de expansão revelando a tabela de disciplinas (questões, acertos, parciais, erros, desempenho e nota).
  - Links contextuais de profundidade para `"Correção questão a questão"` e `"Linha do tempo da prova"`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### Em Escopo (IN SCOPE)
- Ponto de entrada pelo card de `"Acompanhamento Individual de Alunos"` no Hub de Relatórios (`/dashboards/reports/`).
- Modal em 3 passos (Nível ➔ Turma ➔ Aluno) com validação de coordenação e tenant.
- Ficha do aluno em template redesign (`student_individual_tracking.html`) com cabeçalho, pager na turma e 3 KPIs (Média geral, Taxa de presença, Posição na turma).
- Abas de navegação interna: `"Linha do tempo"` e `"Desempenho"`.
- Linha do tempo com eventos reais de banco (`ApplicationStudent`, `Event`, `Annotation`, `TextMessage`), filtros de presença, categoria, disciplina e período.
- Aba Desempenho com média geral, gráficos ECharts (etapa letiva e avaliação a avaliação com pílulas de disciplina) e seção por disciplina.
- Expansão de aplicações listadas exibindo tabela detalhada por disciplina com colunas: Disciplina, Questões, Acertos, Parciais, Erros, Desempenho, Nota.
- Links na expansão da aplicação para correção questão a questão e redirecionamento para o evento na linha do tempo.
- Modal e fluxo de exportação de histórico do aluno via Celery (`export_exams_erp`), com filtros de período, presença, turma/disciplina e opção de separar por disciplina em formatos XLSX e CSV.
- Validação estrita de autorização (Coordenação com relatório ativo, Professor limitado aos seus `TeacherSubject`, 403 para usuários de outro `Client`).

### Fora de Escopo (OUT OF SCOPE)
- Dashboard intermediário da referência externa Vercel (`/individual-monitoring` com índice de risco e recomendações agregadas).
- Aba `"Engajamento"` da referência externa (heatmap de acessos, métricas de tempo em tela, estatísticas de login).
- Funcionalidades de Inteligência Artificial ("Resumo da Lize", "Perguntar à Lize", "Sugestões pedagógicas automáticas").
- Funcionalidades de criação de novos registros pedagógicos institucionais na timeline ("Novo registro").
- Histórico persistido em banco de arquivos exportados anteriormente na tela do usuário.
- Alteração ou remoção da tela legada de detalhes do aluno (`student_detail.html` / `StudentDetailView`).
- Exportação em lote de múltiplos alunos a partir desta tela (a exportação é estritamente individual).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

### Mapa de Navegação Canônica

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Hub de Relatórios | "Relatórios" [verificar menu lateral] | `/dashboards/reports/` | `dashboards:report` (`ReportsTemplateView`) |
| Modal de Seleção | "Acompanhamento Individual de Alunos" (Card em Relatórios) | `/dashboards/reports/` (modal inline) | `student_tracking_modal` (component) |
| Ficha do Aluno | "Ficha do aluno" (Breadcrumb da página) | `/alunos/<uuid:pk>/acompanhamento/` | `students:students_individual_tracking` (`StudentIndividualTrackingView`) |
| Linha do Tempo (Aba) | "Linha do tempo" | `/alunos/<uuid:pk>/acompanhamento/#timeline` | `tabs.trigger id="timeline"` |
| Desempenho (Aba) | "Desempenho" | `/alunos/<uuid:pk>/acompanhamento/#performance` | `tabs.trigger id="performance"` |
| Modal Exportar Histórico | "Exportar histórico" (Botão no cabeçalho) | `/alunos/<uuid:pk>/acompanhamento/` (modal inline) | `individual_tracking_history_export` (component) |
| Correção Questão a Questão | "Correção questão a questão" (Link na aplicação) | `/dashboards/results/answer/?exam=<exam_id>&application=<app_id>` | `dashboards:results-answer` |
| Tela Legada de Detalhe | "Alunos" ➔ Detalhe do aluno | `/alunos/<uuid:pk>` | `students:students_detail` (`StudentDetailView`) |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos de Teste Automatizado (CLI)
Ativar a venv e rodar a suíte completa de testes do módulo de acompanhamento individual:
```bash
source venv/bin/activate
DEBUG=True pytest fiscallizeon/students/tests/test_individual_tracking_*.py dashboards/tests/components/test_student_tracking_modal.py fiscallizeon/applications/tests/api/test_school_class_v2_contract.py --reuse-db -v
```

Para rodar com medição de cobertura:
```bash
source venv/bin/activate
DEBUG=True pytest --cov=fiscallizeon/students/individual_tracking --cov=fiscallizeon/students/api/individual_tracking_* --cov-report=term-missing fiscallizeon/students/tests/test_individual_tracking_*.py --reuse-db
```

### Personas de Teste
1. **Persona Coordenação Autorizada (`coord_user`):**
   - Usuário associado a `CoordinationMember` em `SchoolCoordination` da unidade onde o aluno possui turmas.
   - `Client.has_reports = True`.
   - Permissão esperada: Acesso total ao modal, à ficha, às APIs de desempenho e à exportação do histórico.
2. **Persona Coordenação Sem Relatórios (`coord_no_reports`):**
   - Usuário de coordenação, porém com `Client.has_reports = False`.
   - Permissão esperada: Redirecionamento ou HTTP 403 / bloqueio de acesso ao módulo.
3. **Persona Professor Vinculado (`teacher_user`):**
   - Usuário professor com registro em `Inspector` e vínculo ativo em `TeacherSubject` para turmas e disciplinas onde o aluno está matriculado.
   - Permissão esperada: Visualiza a ficha apenas para a turma do vínculo ativo; dados de outras turmas/disciplinas permanecem restritos.
4. **Persona Coordenação de Outro Tenant (`foreign_coord`):**
   - Coordenador de uma instituição diferente (`client_b`).
   - Permissão esperada: HTTP 403 / 404 estrito ao tentar acessar qualquer URL ou API com o UUID do aluno de `client_a` (Anti-IDOR).

### Pré-condições de Tenant & Módulos no Admin
- **Módulo necessário:** `has_reports` (Acesso à aba de relatórios).
- **Onde ativar no Admin:** Acesse `/admin/clients/client/` ➔ Abra a instituição do usuário ➔ Marque o checkbox `"Tem acesso à aba de relatórios"` e salve.
- **Sintoma se inativo:** O menu `"Relatórios"` fica completamente oculto na barra lateral esquerda e o acesso direto a `/dashboards/reports/` é bloqueado pelo backend.

### Setup de Dados via Mixer (Python Shell)
```python
from datetime import date, timedelta
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamTeacherSubject
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import KnowledgeArea, Subject

# 1. Tenant e Coordenação
client = mixer.blend(Client, type_client=1, two_factor_enabled=False, has_reports=True)
unity = mixer.blend(Unity, client=client, name="Unidade Central")
coordination = mixer.blend(SchoolCoordination, unity=unity)

# 2. Usuário de Coordenação
user_coord = mixer.blend(User, client=client, is_staff=False, two_factor_enabled=False, is_freemium=False)
mixer.blend(CoordinationMember, user=user_coord, coordination=coordination)

# 3. Série, Turma e Alunos para Pager
grade = mixer.blend(Grade, level=Grade.HIGHT_SCHOOL, name="3ª Série")
school_class = mixer.blend(SchoolClass, coordination=coordination, grade=grade, school_year=2026, name="3º Ano Terceirão")

user_ana = mixer.blend(User, client=client, first_name="Ana", last_name="Silva")
student_ana = mixer.blend(Student, user=user_ana, client=client, enrollment_number="2026010")
school_class.students.add(student_ana)

user_bruno = mixer.blend(User, client=client, first_name="Bruno", last_name="Menezes")
student_bruno = mixer.blend(Student, user=user_bruno, client=client, enrollment_number="2026011")
school_class.students.add(student_bruno)

# 4. Prova Multi-disciplinar e Aplicação
ka = mixer.blend(KnowledgeArea, client=client, name="Linguagens")
subj_port = mixer.blend(Subject, client=client, name="Português", knowledge_area=ka)
subj_ing = mixer.blend(Subject, client=client, name="Inglês", knowledge_area=ka)

exam = mixer.blend(Exam, client=client, name="Simulado Diagnóstico 1")
mixer.blend(ExamTeacherSubject, exam=exam, subject=subj_port)
mixer.blend(ExamTeacherSubject, exam=exam, subject=subj_ing)

app = mixer.blend(Application, exam=exam, date=date.today(), status=Application.APPLIED)
mixer.blend(ApplicationStudent, application=app, student=student_ana, start_time=date.today() - timedelta(hours=2))
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Seleção de Aluno via Modal no Hub de Relatórios [Automatizável ✅]

#### Cenário 1 — Abertura do modal a partir do Hub de Relatórios
**Ação humana:**
- [x] **Passo 0 (Pré-condição no Admin):** No Django Admin (`/admin/clients/client/`), certificar-se de que a instituição do usuário está com o checkbox `"**Tem acesso à aba de relatórios**"` marcado. *(Caso esteja desmarcado, o menu "Relatórios" não é renderizado na barra lateral).*
- [x] Logar como Coordenador (`coord_user`) no sistema Lize.
- [x] Localizar no menu lateral esquerdo o item 📄 `"**Relatórios**"` *(ícone de documento com gráfico de barras/linhas)* e clicar para acessar `/dashboards/reports/`.
- [x] Rolar a página até a seção de Cards de Atalho e localizar o card `"**Acompanhamento Individual de Alunos**"` *(card com ícone de usuário em círculo laranja e descrição "Visão detalhada da evolução de cada estudante")*.
- [x] Clicar no card `"**Acompanhamento Individual de Alunos**"`.
- [x] Verificar se o modal se abre centralizado na tela exibindo o título `"**Acompanhamento Individual**"` *(com ícone laranja de usuário)* e o subtítulo `"**Qual aluno você quer acompanhar? Selecione o nível de ensino, a turma e depois o aluno para visualizar o relatório completo.**"`.
![alt text](../evidencias/image-46.png)
- [x] Verificar se o primeiro passo exibido é `"**NÍVEL DE ENSINO**"`, listando os níveis disponíveis (ex.: `"**Ensino Médio**"`).

**Referência técnica (para automação):**
- URL: `/dashboards/reports/`
- Seletor: `button:has-text("Acompanhamento Individual de Alunos")` ➔ `div#student-tracking-modal` (título: `h2:has-text("Acompanhamento Individual")`)
- Estado esperado: Modal visível com classe `tw-flex` e atributo `aria-modal="true"`.
- Fixture: `mixer.blend(Client, has_reports=True)` + `CoordinationMember`.

#### Cenário 2 — Fluxo completo de seleção Nível ➔ Turma ➔ Aluno e navegação
**Ação humana:**
- [ ] No modal aberto no passo 1, clicar sobre o nível de ensino `"**Ensino Médio**"`.
- [ ] Verificar se o modal avança para o passo 2 exibindo a trilha de navegação `"**Níveis**"` ➔ `"**Ensino Médio**"` e o campo `"**Buscar turma...**"`.
- [ ] Digitar no campo de busca o nome da turma `"**3º Ano Terceirão**"`.
- [ ] Clicar sobre a turma `"**3º Ano Terceirão**"` na listagem.
- [ ] Verificar se o modal avança para o passo 3 exibindo o campo `"**Buscar aluno...**"` e a lista de alunos matriculados naquela turma.
- [ ] Clicar sobre o aluno `"**Ana Silva**"`.
- [ ] Verificar se o aluno fica marcado com fundo sutilmente destacado e surge a indicação `"**Selecionado**"` em texto laranja.
- [ ] Verificar se o botão `"**Confirmar**"` no rodapé do modal se torna habilitado (deixa de estar desabilitado/opaco).
- [ ] Clicar no botão `"**Confirmar**"` *(botão laranja com texto branco)*.
- [ ] Verificar se o modal exibe o estado `"**Abrindo…**"` e a página é redirecionada para a URL da ficha do aluno (`/alunos/<student_uuid>/acompanhamento/?class_id=...&grade_id=...&school_year=...`).

**Referência técnica (para automação):**
- URL: `/dashboards/reports/` ➔ `/alunos/<student_uuid>/acompanhamento/`
- Seletor: `button:has-text("Ensino Médio")` ➔ `button:has-text("3º Ano Terceirão")` ➔ `button:has-text("Ana Silva")` ➔ `button:has-text("Confirmar")`
- Estado esperado: URL final contém `/alunos/<uuid>/acompanhamento/` com parâmetros `class_id`, `grade_id` e `school_year`.
- Fixture: Setup com `Grade`, `SchoolClass` e `Student` vinculado à classe.

#### Cenário 3 — Turma sem alunos visíveis
**Ação humana:**
- [ ] Abrir o modal de seleção e selecionar um nível de ensino.
- [ ] Selecionar uma turma que não possua nenhum aluno cadastrado.
- [ ] Verificar se o passo 3 exibe a mensagem amigável `"**Esta turma não possui alunos visíveis.**"`.
- [ ] Verificar se o botão `"**Confirmar**"` permanece desabilitado, impedindo que o usuário avance sem selecionar um estudante.

**Referência técnica (para automação):**
- URL: `/dashboards/reports/` (modal passo 3)
- Seletor: `p:has-text("Esta turma não possui alunos visíveis.")` e `button:has-text("Confirmar")[disabled]`
- Estado esperado: Elemento de empty state visível e botão com atributo `disabled`.
- Fixture: `mixer.blend(SchoolClass, coordination=coordination)` sem adicionar alunos ao ManyToMany `students`.

---

### 5.2 Cabeçalho da Ficha, Pager e Indicadores de KPI [Automatizável ✅]

#### Cenário 4 — Exibição dos dados do aluno e navegação via Pager
**Ação humana:**
- [ ] Acessar a ficha do aluno com contexto de turma na URL (`/alunos/<ana_uuid>/acompanhamento/?class_id=<class_uuid>`).
- [ ] Verificar no topo da página o botão de retorno `"**Voltar aos relatórios**"` com ícone de seta para a esquerda e o breadcrumb `"**Relatórios** / **Ficha do aluno**"`.
- [ ] Verificar se o nome `"**Ana Silva**"` é exibido em destaque no cabeçalho com suas iniciais `"**AS**"` dentro do avatar circular.
- [ ] Verificar as informações contextuais abaixo do nome: série e turma (ex.: `"**3ª Série 3º Ano Terceirão**"`), matrícula e idade/responsável se informados.
- [ ] Localizar o componente de Pager no topo direito do cabeçalho.
- [ ] Verificar se o texto exibe a posição correta, ex.: `"**1 de 2 · 3º Ano Terceirão**"`.
- [ ] Verificar se o botão `"**Aluno anterior**"` está desabilitado *(ícone cinza sem cursor de clique)*, pois Ana é o primeiro registro.
- [ ] Clicar no botão `"**Próximo aluno**"` *(ícone de seta chevron para a direita)*.
- [ ] Verificar se a página navega com sucesso para a ficha do próximo aluno (`Bruno Menezes`), mantendo os parâmetros de turma na URL e atualizando o contador para `"**2 de 2 · 3º Ano Terceirão**"`.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/?class_id=<uuid>`
- Seletor: `h1#ficha-aluno-nome` e `nav[aria-label="Outros alunos da turma"] a[aria-label="Próximo aluno"]`
- Estado esperado: Navegação para a URL do próximo estudante mantendo a turma informada.
- Fixture: Duas instâncias de `Student` vinculadas à mesma `SchoolClass`.

#### Cenário 5 — Validação rigorosa dos Cards de KPI
**Ação humana:**
- [ ] No cabeçalho da ficha, inspecionar os 3 cards de métricas principais posicionados abaixo do nome do aluno:
  - Card 1: `"**Média geral**"`
  - Card 2: `"**Taxa de presença**"`
  - Card 3: `"**Posição na turma**"`
- [ ] Se o aluno não tiver dados ou o serviço retornar vazio, verificar se os cards exibem o estado informativo `"**Ainda não há dados para este indicador.**"` *(sem inventar notas fictícias ou 0.0 falso)*.
- [ ] Se houver dados reais calculados:
  - Verificar se a `"**Média geral**"` exibe o valor percentual (ex.: `"**68%**"`) e ao lado o comparativo com a turma (ex.: `"**Turma: 62%**"`).
  - Verificar se a `"**Taxa de presença**"` exibe a porcentagem real calculada sobre as aplicações encerradas.
  - Verificar se a `"**Posição na turma**"` exibe a classificação (ex.: `"**3º de 28**"`).

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: `dl.tw-grid dt:has-text("Média geral") + dd span`
- Estado esperado: Formato de percentual válido ou texto descritivo de ausência de dados; nunca vazio ou NaN.
- Fixture: `build_header_kpis` com retornos reais de Analytics ou vazio.

---

### 5.3 Abas e Linha do Tempo [Automatizável ✅]

#### Cenário 6 — Alternância entre abas Linha do Tempo e Desempenho
**Ação humana:**
- [ ] Na ficha do aluno, localizar a barra de abas logo abaixo do cabeçalho.
- [ ] Verificar se a aba `"**Linha do tempo**"` está ativa por padrão com sublinhado laranja (`#e74a00`).
- [ ] Clicar na aba `"**Desempenho**"`.
- [ ] Verificar se o painel da linha do tempo é ocultado e o conteúdo de desempenho (gráficos e tabela) é exibido imediatamente sem recarregamento completo da página (comportamento de SPA Alpine).
- [ ] Clicar novamente na aba `"**Linha do tempo**"` e verificar o retorno imediato da listagem de eventos.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: `button[role="tab"]:has-text("Desempenho")` e `button[role="tab"]:has-text("Linha do tempo")`
- Estado esperado: Painel `div[data-individual-tracking-tabs] div[tabs.panel id="performance"]` torna-se visível.
- Fixture: `student` criado e visualizado na ficha.

#### Cenário 7 — Filtros e agrupamento mensal na Linha do Tempo
**Ação humana:**
- [ ] Na aba `"**Linha do tempo**"`, verificar o agrupador de presença no topo: botões `"**Todas**"`, `"**Presentes**"` e `"**Ausentes**"`.
- [ ] Clicar no botão `"**Ausentes**"`.
- [ ] Verificar se a listagem exibe apenas as aplicações em que o aluno esteve ausente, identificadas com ícone e badge amarelo/laranja `"**Ausente**"`.
- [ ] Clicar no botão `"**Filtros**"` *(botão branco com borda cinza e ícone de funil/linhas)*.
- [ ] No menu dropdown aberto:
  - Selecionar uma disciplina no campo seletor `"**Todas as disciplinas**"`.
  - Selecionar o período `"**Últimos 30 dias**"` ou uma etapa letiva.
- [ ] Verificar se pílulas de filtro ativo surgem acima da linha do tempo com ícone `"**x**"` para remoção rápida.
- [ ] Verificar se os eventos aparecem agrupados por cabeçalhos de mês (ex.: `"**Novembro de 2026**"`).

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: `button[role="radio"]:has-text("Ausentes")` ➔ `select#timeline-subject` ➔ `h3.tw-sticky`
- Estado esperado: Dropdown aplica filtros, requisição para `/api/acompanhamento/<uuid>/timeline/` é disparada com parâmetros.
- Fixture: Eventos de `ApplicationStudent` presentes e ausentes criados via mixer.

---

### 5.4 Aba Desempenho e Tabela por Disciplina [Automatizável ✅]

#### Cenário 8 — Filtro por Etapa Letiva e Gráficos de Desempenho
**Ação humana:**
- [ ] Clicar na aba `"**Desempenho**"`.
- [ ] Localizar o seletor de etapa letiva à direita da `"**Média geral**"`.
- [ ] Abrir o select e escolher uma etapa específica (ex.: `"**1º SIMULADO**"` ou `"**1º Bimestre**"`).
- [ ] Verificar se a Média Geral da aba e os gráficos se atualizam para refletir exclusivamente a etapa escolhida.
- [ ] Verificar se o gráfico `"**Evolução por etapa letiva**"` exibe os rótulos reais de etapas recebidos da API (sem forçar o termo "Bimestre").
- [ ] Na seção `"**Avaliação a avaliação**"`, clicar na pílula de uma disciplina específica (ex.: `"**Português**"`).
- [ ] Verificar se o gráfico de barras filtra os dados e apresenta apenas o desempenho naquela matéria.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: `select[x-model="stageId"]` e `div[role="radiogroup"][aria-label="Disciplina do gráfico"] button:has-text("Português")`
- Estado esperado: ECharts canvas redesenhado e API `/api/acompanhamento/<uuid>/avaliacoes/?subject_id=...` requisitada.
- Fixture: `ApplicationStudent` com respostas e dados agregados em disciplinas distintas.

#### Cenário 9 — Expansão da Aplicação e Tabela Detalhada por Disciplina
**Ação humana:**
- [ ] Na aba `"**Desempenho**"`, rolar até a seção `"**Por aplicação**"`.
- [ ] Localizar uma aplicação multi-disciplinar (ex.: `"**Simulado Geral 1**"`).
- [ ] Clicar sobre a linha da aplicação para expandir o acordeão *(linha com data, nome do exame, percentual e seta chevron)*.
- [ ] Verificar se o acordeão expande revelando a tabela de disciplinas com as seguintes colunas:
  - `"**Disciplina**"`
  - `"**Questões**"`
  - `"**Acertos**"`
  - `"**Parciais**"`
  - `"**Erros**"`
  - `"**Desempenho**"`
  - `"**Nota**"`
- [ ] Verificar se cada disciplina vinculada à prova (ex.: `"**Português**"` e `"**Inglês**"`) possui sua respectiva linha preenchida com valores numéricos corretos.
- [ ] Verificar se abaixo da tabela constam os links de ação:
  - Link `"**Correção questão a questão**"` *(com ícone de seta externa)*.
  - Link `"**Linha do tempo da prova**"`.
- [ ] Clicar no link `"**Linha do tempo da prova**"` e verificar se o sistema comuta automaticamente para a aba `"**Linha do tempo**"` posicionando a tela sobre o evento daquela aplicação.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: `li[data-tracking-application] button[aria-controls^="aplicacao-"]` ➔ `table th:has-text("Disciplina")`
- Estado esperado: Tabela visível com cabeçalhos e linhas preenchidas a partir de `StudentApplicationSubjectsAPIView`.
- Fixture: `Application` com `ExamTeacherSubject` múltiplos e `ApplicationStudent` associado.

#### Cenário 10 — Aplicação de Disciplina Única
**Ação humana:**
- [ ] Localizar na lista de aplicações uma prova que contenha apenas uma disciplina (ex.: `"**Avaliação Mensal de Matemática**"`).
- [ ] Expandir a aplicação clicando sobre a linha.
- [ ] Verificar se a tabela exibe exatamente uma única linha para `"**Matemática**"`.
- [ ] Conferir se os números de questões, acertos, erros e nota dessa linha única coincidem exatamente com o total da prova.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: `li[data-tracking-application]:has-text("Matemática") tr`
- Estado esperado: Exatamente 1 linha no `tbody` da tabela de disciplinas.
- Fixture: `Exam` com 1 único `ExamTeacherSubject`.

---

### 5.5 Exportação do Histórico Individual do Aluno [Automatizável ✅]

#### Cenário 11 — Abertura e configuração do modal de exportação
**Ação humana:**
- [ ] No cabeçalho da ficha do aluno, clicar no botão `"**Exportar histórico**"` *(botão branco com ícone de download)*.
- [ ] Verificar se o modal se abre exibindo o título `"**Exportar histórico do aluno**"`.
- [ ] No grupo `"**Período**"`, verificar que `"**Ano letivo 2026**"` vem selecionado por padrão.
- [ ] Clicar no botão `"**Personalizado**"` e verificar a exibição dos campos de data `"**Início**"` e `"**Fim**"`.
- [ ] Retornar para `"**Ano letivo 2026**"`.
- [ ] No grupo `"**Aplicações**"`, alternar entre `"**Todas**"`, `"**Só presentes**"` e `"**Só ausentes**"`.
- [ ] Marcar o checkbox `"**Adicionar unidade e turma**"`.
- [ ] Marcar o checkbox `"**Separar por disciplina**"`.
- [ ] No formato, selecionar `"**XLSX**"` ou `"**CSV**"`.
- [ ] Verificar se na prévia inferior é exibido o nome gerado do arquivo (ex.: `historico_aluno_ana_silva_2026.xlsx`) e a quantidade estimada de aplicações.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: `button[data-export-history-trigger]` ➔ `div#individual-tracking-history-export`
- Estado esperado: Modal de exportação visível e controles interativos funcionais.
- Fixture: Aluno com histórico de aplicações presente no banco.

#### Cenário 12 — Submissão e processamento da exportação via Celery
**Ação humana:**
- [ ] Com os filtros configurados no modal de exportação, clicar no botão `"**Exportar**"` *(botão laranja com ícone de download)*.
- [ ] Verificar se o botão entra em estado de carregamento exibindo o texto `"**Exportando…**"` e fica desabilitado para prevenir cliques duplos.
- [ ] Aguardar a conclusão do processamento assíncrono via Celery.
- [ ] Verificar se o modal se fecha automaticamente ou apresenta a mensagem de conclusão e o download do arquivo é disparado no navegador.
- [ ] Abrir o arquivo baixado (`.xlsx` ou `.csv`) e auditar:
  - O arquivo contém **apenas** dados do aluno selecionado (`Ana Silva`), sem conter linhas de qualquer outro estudante da turma ou da instituição.
  - Se a opção `"**Separar por disciplina**"` foi marcada, verificar que cada aplicação possui linhas discriminadas por disciplina com as respectivas notas e contagens de acertos/erros.
  - Se a opção `"**Adicionar unidade e turma**"` foi marcada, verificar a presença das colunas `"Unidade"` e `"Turma"`.

**Referência técnica (para automação):**
- URL: `POST /alunos/api/acompanhamento/<uuid>/historico/` ➔ Polling `GET /exportar/provas/status/<export_id>/`
- Seletor: `button[data-export-history-submit]`
- Estado esperado: Requisição responde com `export_id`, Celery executa a task `export_exams_erp` com `student_pk` e status finaliza em `SUCCESS`.
- Fixture: Worker Celery ativo e `export_exams_erp` executado com `student_pk`.

---

### 5.6 Segurança, Permissões e Multi-Tenant [Automatizável ✅]

#### Cenário 13 — Acesso negado para usuário de outra Instituição (Anti-IDOR)
**Ação humana:**
- [ ] Efetuar login com usuário Coordenador da Instituição B (`foreign_coord`).
- [ ] Tentar acessar diretamente via barra de endereço do navegador a URL da ficha do aluno pertencente à Instituição A:
  `/alunos/<student_a_uuid>/acompanhamento/`
- [ ] Verificar se o sistema bloqueia o acesso, respondendo com página de erro de permissão (HTTP 403) ou Não Encontrado (HTTP 404).
- [ ] Tentar disparar requisição manual via API para buscar disciplinas da aplicação daquele aluno:
  `GET /alunos/api/acompanhamento/<student_a_uuid>/aplicacoes/<app_student_a_uuid>/disciplinas/`
- [ ] Verificar se a API responde estritamente com status HTTP 403 ou 404 sem vazar nenhum dado do estudante ou da instituição externa.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid_tenant_a>/acompanhamento/`
- Seletor: Resposta HTTP 403 / 404
- Estado esperado: Acesso categoricamente negado pelo mixin `StudentIndividualTrackingViewMixin`.
- Fixture: Aluno de `client_a` e usuário logado de `client_b`.

#### Cenário 14 — Restrição de escopo para perfil Professor
**Ação humana:**
- [ ] Logar como Professor (`teacher_user`) que leciona apenas para a Turma A.
- [ ] Acessar a ficha de um aluno matriculado na Turma A e também em atividades da Turma B.
- [ ] Verificar se o professor consegue visualizar a ficha do aluno para o contexto da Turma A.
- [ ] Tentar alterar o parâmetro de URL para a Turma B (`?class_id=<turma_b_uuid>`).
- [ ] Verificar se o sistema não autoriza o acesso ao contexto da turma não lecionada pelo docente, mantendo o escopo restrito exclusivamente às suas turmas e disciplinas autorizadas.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/?class_id=<unauthorized_class_id>`
- Seletor: Resposta HTTP 403 ou redirecionamento defensivo
- Estado esperado: `authorized_class_id` recusa turmas fora do vínculo do docente.
- Fixture: `TeacherSubject` ativo apenas para uma turma específica.

---

### 5.7 Validação Visual, Layout e Responsividade [Apenas Manual 👁]

#### Cenário 15 — Responsividade e Visual em Resolução Intermediária (1333×1080)
**Ação humana:**
- [ ] Ajustar a viewport do navegador para a resolução de teste padrão corporativo (1333×1080 px).
- [ ] Acessar a ficha do aluno (`/alunos/<uuid>/acompanhamento/`).
- [ ] Verificar o cabeçalho: o nome do aluno, dados cadastrais, botões de ação e cards de KPI não devem sobrepor elementos nem quebrar o alinhamento.
- [ ] Verificar se textos longos (nomes compostos de alunos, nomes de turmas extensas) recebem truncamento elegante com reticências (`...`) sem estourar os contêineres.
- [ ] Verificar a renderização dos gráficos ECharts na aba Desempenho: os gráficos devem redimensionar dinamicamente respeitando as margens e a legibilidade dos eixos.
- [ ] Verificar a tabela de disciplinas na aplicação expandida: deve exibir scroll horizontal (`tw-overflow-x-auto`) suave caso o espaço seja restrito, sem deformar as colunas de notas e contagens.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: Inspeção visual de layout em `div.ai-mesh` e contêineres `content-fixed`.
- Estado esperado: Ausência de quebra de layout, overflow indesejado ou sobreposição de texto.
- Fixture: Aluno com nome extenso e turma com nomenclatura longa.

#### Cenário 16 — Validação em Tela Mobile (390×844 px)
**Ação humana:**
- [ ] Emular dispositivo móvel no DevTools (largura 390 px).
- [ ] Abrir o modal de seleção de alunos: verificar se os passos se adaptam verticalmente e se a rolagem de turmas/alunos é confortável via touch.
- [ ] Abrir a ficha do aluno: verificar se os 3 cards de KPI se empilham verticalmente em 1 coluna (`sm:tw-grid-cols-3`).
- [ ] Abrir o modal de exportação de histórico: verificar se o diálogo se ajusta à largura total da tela (`width: min(32rem, calc(100vw - 2rem))`) mantendo botões de Cancelar e Exportar acessíveis no rodapé.

**Referência técnica (para automação):**
- URL: `/alunos/<uuid>/acompanhamento/`
- Seletor: Viewport mobile 390px
- Estado esperado: Layout fluido e utilizável em telas pequenas conforme spec de design.
- Fixture: Dispositivo móvel ou modo responsivo do navegador.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

O QA humano deve registrar capturas de tela (prints) nos seguintes momentos da homologação para anexar ao relatório do ClickUp:
1. **Modal de Seleção de Aluno:** Print dos três passos (1. Níveis, 2. Turmas com busca, 3. Aluno selecionado).
2. **Cabeçalho da Ficha:** Print com o nome do aluno, pager ativo ("1 de X · Turma"), cards de KPI (Média, Presença, Posição) e botão Exportar histórico.
3. **Aba Linha do Tempo:** Print da linha do tempo com filtros aplicados e agrupamento mensal.
4. **Aba Desempenho (Visão Completa):** Print dos gráficos ECharts (Evolução por etapa letiva e Avaliação a avaliação filtrado por disciplina).
5. **Aplicação Expandida:** Print da tabela detalhada por disciplina com todas as colunas visíveis (Questões, Acertos, Parciais, Erros, Desempenho, Nota) e links inferiores.
6. **Modal de Exportação:** Print do formulário com opções de período, presença e separação por disciplina.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!WARNING]
> ### ⚠️ ALERTA DE SCHEMA DRIFT NO BANCO DE DADOS LOCAL
> **Contexto:** Durante a execução dos testes automatizados locais com pytest, foi detectado o seguinte erro de integridade:
> `psycopg2.errors.NotNullViolation: null value in column "has_new_application_experience" of relation "clients_client" violates not-null constraint`
> **Diagnóstico:** O campo `has_new_application_experience` **NÃO existe** no modelo Django da branch atual (`fiscallizeon/clients/models.py`). Trata-se de uma contaminação de banco local por migração de outra branch (`feat/instrumentos-avaliativos-CU-86ak8r20g`).
> **Ação Recomendada ao Desenvolvedor:** Executar a limpeza da coluna residual no banco de testes local:
> ```sql
> ALTER TABLE clients_client DROP COLUMN IF EXISTS has_new_application_experience;
> ```

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[UX/UI] Padronização Visual das Opções de Nível de Ensino (Passo 1 do Modal):**
> Durante os testes no Passo 1 do modal de seleção, observou-se uma despadronização no padrão de capitalização das opções listadas:
> - `"Anos iniciais"` (inicial maiúscula apenas na primeira palavra: "A" maiúsculo e "i" minúsculo)
> - `"Anos finais"` (inicial maiúscula apenas na primeira palavra: "A" maiúsculo e "f" minúsculo)
> - `"Ensino Médio"` (ambas as palavras com inicial maiúscula: "E" e "M" maiúsculos)
> 
> **Visão de Usuário:** Do ponto de vista de consistência e harmonia visual para quem está operando o sistema, seria mais agradável padronizar a exibição para que todas as opções apareçam em maiúsculas (ex.: `"ANOS INICIAIS"`, `"ANOS FINAIS"`, `"ENSINO MÉDIO"`) de maneira uniforme, mantendo um padrão coeso. Deixamos a cargo da equipe de desenvolvimento a decisão de onde e como aplicar essa padronização da melhor forma.
> 
> ![alt text](../evidencias/image-48.png)

> [!NOTE]
> **[UX/UI] Padronização Visual dos Nomes dos Alunos na Listagem (Passo 3 do Modal):**
> Durante os testes no Passo 3 do modal de seleção de alunos, observou-se uma variação visual na listagem: alguns estudantes aparecem com o nome completamente em maiúsculas (ex.: `BENJAMIM SOARES BASTOS LIMA`), enquanto outros aparecem em caixa mista / inicial maiúscula (ex.: `Davi Komatsu Rodrigues`).
> 
> **Visão de Usuário:** Do ponto de vista de consistência visual para quem está operando o sistema, seria mais agradável padronizar a exibição para que todos os nomes apareçam em maiúsculas de maneira uniforme, mantendo um padrão coeso em toda a lista. Deixamos a cargo da equipe de desenvolvimento a decisão de onde e como aplicar essa padronização da melhor forma.
> 
> ![alt text](../evidencias/image-47.png)
> [!NOTE]
> **Definição de Produto para Professor na Exportação:** Atualmente a exportação está vinculada aos mesmos critérios de coordenação e turmas ativas de `TeacherSubject`. Uma permissão independente no `CustomGroup` para exportação pode ser avaliada em ciclos futuros caso o produto deseje desvincular a exportação da visualização da ficha.

> [!NOTE]
> **Categorias Avançadas de Timeline:** As categorias da referência externa Vercel relativas a LMS (Entregas e prazos, Alertas automatizados de engajamento) permanecem desabilitadas por ausência de modelos no Lize, sendo ativadas sob demanda conforme novas fontes forem mapeadas pelo produto.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.

🔗 **[Ver Mapeamento de Tela](docs/tests/usability/student_individual_tracking.md)**

### Snippet de Automação Playwright (Python)
Exemplo de teste autônomo combinando setup de banco de dados via `mixer` e automação de navegação:

```python
import pytest
from datetime import date
from mixer.backend.django import mixer
from playwright.sync_api import Page, expect
from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.exams.models import Exam, ExamTeacherSubject
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import KnowledgeArea, Subject

def test_coordenacao_expande_disciplinas_da_aplicacao(page: Page, live_server):
    # 1. Setup Backend via Mixer
    client = mixer.blend(Client, type_client=1, two_factor_enabled=False, has_reports=True)
    unity = mixer.blend(Unity, client=client, name="Unidade QA")
    coord = mixer.blend(SchoolCoordination, unity=unity)

    user = mixer.blend(User, client=client, is_staff=True, two_factor_enabled=False)
    user.set_password("123456")
    user.save()
    mixer.blend(CoordinationMember, user=user, coordination=coord)

    grade = mixer.blend(Grade, level=Grade.HIGHT_SCHOOL, name="2ª Série")
    school_class = mixer.blend(SchoolClass, coordination=coord, grade=grade, school_year=2026, name="2º Ano B")

    student_user = mixer.blend(User, client=client, first_name="Lucas", last_name="Ferreira")
    student = mixer.blend(Student, user=student_user, client=client, enrollment_number="2026099")
    school_class.students.add(student)

    ka = mixer.blend(KnowledgeArea, client=client, name="Exatas")
    mat = mixer.blend(Subject, client=client, name="Matemática", knowledge_area=ka)
    fis = mixer.blend(Subject, client=client, name="Física", knowledge_area=ka)

    exam = mixer.blend(Exam, client=client, name="Simulado Exatas 1")
    mixer.blend(ExamTeacherSubject, exam=exam, subject=mat)
    mixer.blend(ExamTeacherSubject, exam=exam, subject=fis)

    app = mixer.blend(Application, exam=exam, date=date.today(), status=Application.APPLIED)
    app_student = mixer.blend(ApplicationStudent, application=app, student=student, start_time=date.today())

    # 2. Login
    page.goto(f"{live_server.url}/conta/login/")
    page.fill("input[name='username']", user.email)
    page.fill("input[name='password']", "123456")
    page.click("button[type='submit']")

    # 3. Navegação para Ficha Individual
    url_ficha = f"{live_server.url}/alunos/{student.pk}/acompanhamento/?class_id={school_class.pk}&school_year=2026"
    page.goto(url_ficha)

    # 4. Validar Cabeçalho
    expect(page.locator("h1#ficha-aluno-nome")).to_contain_text("Lucas Ferreira")

    # 5. Comutar para Aba Desempenho
    page.click("button[role='tab']:has-text('Desempenho')")

    # 6. Expandir Aplicação
    app_row = page.locator(f"li[data-application-student='{app_student.pk}']")
    app_row.locator("button[aria-controls^='aplicacao-']").click()

    # 7. Validar Tabela de Disciplinas
    tabela = app_row.locator("table")
    expect(tabela).to_be_visible()
    expect(tabela).to_contain_text("Matemática")
    expect(tabela).to_contain_text("Física")
    expect(app_row.locator("a:has-text('Correção questão a questão')")).to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante os testes:**
  - Identificação de contaminação de banco local (schema drift da coluna residual `has_new_application_experience`), que necessitou de diagnóstico para não ser confundido com regressão do módulo.
  - Menu "Relatórios" e entrada da tela ocultados na interface devido à flag `Client.has_reports = False` na instituição de teste, gerando fricção de navegação resolvida após documentação explícita de pré-requisitos de tenant.
- **Interações com o desenvolvedor / decisões técnicas:**
  - Alinhamento quanto ao isolamento da view nova (`StudentIndividualTrackingView`) sem quebrar ou alterar a view legada (`StudentDetailView`).
  - Confirmação de que a exportação utiliza o fluxo assíncrono padrão ERP com a segurança da revalidação de `student_pk` no worker Celery.
- **Melhorias de processo para o próximo ciclo:**
  - Incluir sempre como "Passo Zero" no Roteiro Humano os pré-requisitos de Feature Flags / Módulos do Cliente com comando CLI rápido.
  - Manter scripts de checagem prévia de schema drift antes da rodada inicial de testes.
  - Assegurar que os cards de KPI tenham casos de borda com retorno nulo e retorno com dados reais cobertos por testes unitários e de componente.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- [x] **Adicionado à Skill:** Diretriz obrigatória `CRITICAL RULE 6 (Passo Zero — Pré-condições de Tenant & Feature Flags no Checklist Humano)` para exigir que todo plano indique com clareza quais flags do modelo `Client` precisam estar ativas e o comando rápido para ligá-las localmente.
- Adicionar no checklist do prompt uma verificação explícita sobre links contextuais bidirecionais (ex.: o link "Linha do tempo da prova" dentro da aba Desempenho que automaticamente comuta a aba ativa e rola até o evento correto na Linha do Tempo).
- Reforçar a exigência de checagem de sanitização de filtros em queries do tipo Pager ("Aluno anterior / próximo") para garantir que o contexto de paginação seja invalidado se o usuário manipular parâmetros de URL.


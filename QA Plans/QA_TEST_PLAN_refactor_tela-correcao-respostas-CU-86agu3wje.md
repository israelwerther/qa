## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-09 |
| **Branch:** | `refactor/tela-correcao-respostas-CU-86agu3wje` |
| **ClickUp:** | [Refatoração da tela de correção de respostas (86agu3wje)](https://app.clickup.com/t/3120759/86agu3wje) |
| **Natureza da Tarefa:** | `[Refactoring]` |
| **Área da Feature:** | Correção de Provas / Correção por Enunciado / Desempenho Backend & Frontend / Rubricas de Discursivas |
| **Nível de Risco:** | Médio (tela de alta criticidade operacional usada por coordenação e professores para atribuição de notas) |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (completa: proposal, design detalhado com medição real de queries, specs com cenários Gherkin e tasks em `openspec/changes/refactor-correction-screen-86agu3wje/`) |

---

## 1. Summary of Changes (Resumo das Alterações)

Esta tarefa refatora o fluxo de carregamento e salvamento da tela de **Correção por Enunciado** (`/provas/<exam_id>/enunciados/detalhes/`), eliminando o crescimento de consultas SQL proporcional ao número de alunos ($O(N) \to O(1)$) e corrigindo a duplicação indevida de notas por critério ao regravar avaliações discursivas.

- **Backend & Camada de Serviços (`fiscallizeon/exams/services/correction_screen.py`):**
  - Criação do serviço `CorrectionScreenLoader`: centraliza a carga em lote dos alunos da turma, respostas da questão (`OptionAnswer`, `SumAnswer`, `FileAnswer`, `TextualAnswer`), notas por critério associadas à resposta (`CorrectionTextualAnswer`, `CorrectionFileAnswer`), scans OMR (`OMRStudents`, `OMRDiscursiveScan`), prazo limite de correção (`ApplicationDeadlineCorrectionResponseException`) e respostas similares com `similarity`.
  - Redução drástica no volume de queries: de um comportamento que escalava até mais de 1.100 queries em turmas grandes para uma faixa constante de **6 a 8 queries**, independente da quantidade de alunos.
- **Serialização de Respostas e Alunos (`fiscallizeon/exams/serializers/exam_questions.py` e `fiscallizeon/applications/serializers/application_student.py`):**
  - Reescrita de `ExamQuestionAnswersV2Serializer`: agora delega a carga ao `CorrectionScreenLoader`, elimina a chamada duplicada de `get_applications_student` em `to_representation` e resolve o ano via parâmetro GET `?year=` (com fallback para `exam.created_at.year`).
  - Atualização de `ApplicationStudentWithAnswerSerializer`: consome os mapas pré-carregados no `context['loaded_correction_screen']` quando presentes, adiciona o novo campo `criterion_scores` por aluno, e mantém a execução original quando chamado por outros fluxos legados da plataforma.
- **Frontend Vue & Resolução de Duplicação (`fiscallizeon/exams/templates/dashboard/exams/exam_detail_enunciation_new.html`):**
  - Correção do mapeamento de categoria: anteriormente `selectApplicationStudent` verificava apenas `'Texto'` e `'Arquivo anexado'`, ignorando o valor real retornado pelo serializer (`'Discursiva'`). Agora inclui explicitamente `'Discursiva'`, disparando `hydrateCorrectionScores`.
  - Hidratação imediata de rubricas: as notas por critério são lidas diretamente do payload inicial (`applicationStudent.criterion_scores`), eliminando requisições AJAX adicionais a `questions:get_correction_answers`.
  - Regravação via `PUT`: a função `saveUpdateCorrection` foi convertida de um loop assíncrono descoordenado (`forEach(async)`) para um laço sequencial aguardado (`for ... await`). Se o critério já possui ID retornado no payload, dispara requisição `PUT` em `corrections:correction_textual_answer_update` (ou arquivo), evitando criar registros redundantes via `POST`.
  - Indicador de falha: se algum critério falhar na persistência, o aluno é marcado com status de erro na interface (`handleApplicationStudentStatus('error')`).
- **Encaminhamento de Filtros (`fiscallizeon/exams/templates/dashboard/exams/includes/exam-detail-enunciation-functions.js`):**
  - Função `fetchAnswers`: passa a encaminhar o parâmetro `year` presente na URL da página para a chamada do endpoint `exams:exam_question_answers_detail_v2`.
  - Função `sendTeacherFeedback`: passa a aguardar a conclusão de `saveUpdateCorrection` com `await`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- IN SCOPE: Carga em lote $O(1)$ de alunos, respostas e notas por critério no endpoint `exams:exam_question_answers_detail_v2`.
- IN SCOPE: Hidratação automática das notas de rubrica (`criterion_scores`) na tela ao alternar entre alunos em questões Discursivas e de Arquivo anexado.
- IN SCOPE: Reutilização do ID do registro existente e envio de `PUT` na regravação de critérios pela tela de correção por enunciado.
- IN SCOPE: Encaminhamento do parâmetro `year` da query string da página para o endpoint v2 da API.
- IN SCOPE: Preservação estrita do layout e dos comportamentos visuais existentes no template `exam_detail_enunciation_new.html`.
- IN SCOPE: Garantia de equivalência nos campos preexistentes do payload (`student_name`, `answers`, `files_urls`, `similar_answers`, `can_be_corrected`).
- OUT OF SCOPE: Criação de constraints `unique_together` ou validações de pontuação máxima no nível do banco de dados (model `CorrectionTextualAnswer` / `CorrectionFileAnswer`).
- OUT OF SCOPE: Limpeza ou expurgo de duplicados legados que já foram persistidos em produção antes desta entrega.
- OUT OF SCOPE: Refatoração ou alteração do modal alternativo de correção por aluno (`exam-detail-functions.js`).
- OUT OF SCOPE: Redesign visual da tela, substituição de bibliotecas ou alteração do `extends redesign/base.html`.
- OUT OF SCOPE: Alterações no pipeline de importação OMR.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Listagem de Provas | Menu lateral ➔ **Instrumentos Avaliativos** (ou **Cadernos**) | `/provas/` | `exams:exams_list` (`exam_list_new.html`) |
| Detalhe da Prova | Clicar no título da prova na listagem de cadernos | `/provas/<exam_id>/detalhes/` | `exams:exams_detail` (`exam_detail_new.html`) |
| Correção por Enunciado (via Detalhe) | Botão roxo **"Correção por enunciado"** no topo da página de detalhes da prova | `/provas/<exam_id>/enunciados/detalhes/` | `exams:exams_detail_enunciation_new` (`ExamDetailEnunciationNewView`) |
| Correção por Enunciado (via Ações na Lista) | Menu de opções (3 pontos) do caderno ➔ item **"Correção por enunciado"** | `/provas/<exam_id>/enunciados/detalhes/` | `exams:exams_detail_enunciation_new` (`ExamDetailEnunciationNewView`) |
| Correção com Filtro de Ano | Parâmetro `?year=YYYY` na barra de endereços | `/provas/<exam_id>/enunciados/detalhes/?year=YYYY` | `exams:exams_detail_enunciation_new` |
| Endpoint API v2 (Carregamento da Questão) | Chamada interna ao abrir modal clicando em **"Corrigir"** | `/provas/api/exam-question/<eq_id>/answers/v2/` | `exams:exam_question_answers_detail_v2` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Personas Executoras:
1. **Coordenação da Instituição:** Usuário do tipo `COORDINATION` com acesso às provas e turmas da escola.
2. **Professor da Disciplina:** Usuário do tipo `TEACHER` associado à matéria da questão (ou com permissão `can_correct_questions_other_teachers = True`).
3. **Staff / Superuser:** Acesso administrativo irrestrito para validação exploratória rápida.

> [!IMPORTANT]
> **Alerta de Pendência da Task (Conforme Comentários no ClickUp):**
> O desenvolvedor Richard registrou formalmente nos comentários da task ClickUp: *"Pendências da task: Testes automatizados"*. O arquivo de testes `fiscallizeon/exams/tests/test_correction_screen_loading.py` (previsto na Seção 4 do OpenSpec) ainda não foi commitado nesta branch. Os comandos abaixo são a referência oficial para execução assim que os testes forem integrados.

### Execução de Testes Automatizados Locais:

```bash
# Com a virtualenv ativada:
source venv/bin/activate && pytest fiscallizeon/exams/tests/test_correction_screen_loading.py --reuse-db

# Ou via Docker:
./scripts/tests/run-tests.sh --no-tty fiscallizeon/exams/tests/test_correction_screen_loading.py
```

### Provas Reais Já Disponíveis no Banco Local para Teste Imediato:

Conforme levantamento do baseline no `design.md`, os dois cadernos abaixo estão **preservados e funcionais no banco local**:

1. **Caso 1 (Discursiva + Template de 5 Critérios):**
   - **Nome:** ODT - Saúde Bucal na Atenção Básica
   - **Exam UUID:** `12d0d423-a8f3-4934-8abf-0580ddf48285`
   - **Questão Discursiva:** `d3b115d8-5e6e-450a-b5c5-80e148bc6a85`
   - **Turma:** ODT01A-M (`7a24afea-b8c9-4b71-82ac-148ded9dca48`) — 28 alunos, 27 respostas, 25 já corrigidos.
   - **URL Direta:** `http://localhost:8000/provas/12d0d423-a8f3-4934-8abf-0580ddf48285/enunciados/detalhes/?turma=7a24afea-b8c9-4b71-82ac-148ded9dca48`

2. **Caso 2 (Arquivo Anexado / OMR + Template de 5 Critérios):**
   - **Nome:** P3 - BLOCO 02 - PV2
   - **Exam UUID:** `93faa67a-e3a2-4388-931c-273b3177c1a0`
   - **Questão Arquivo Anexado:** `24d5880e-1aba-4c03-a2cc-4aaacd6dc7c5`
   - **Turmas:** `8839f1ab-94c9-49d8-90e4-45aa09960576` (14 alunos), `e07740e2-d44f-4001-8868-3d8d5b5c0eba` (22 alunos), `207e41e1-de41-448d-af17-e7e8127647f8` (47 alunos).
   - **URL Direta:** `http://localhost:8000/provas/93faa67a-e3a2-4388-931c-273b3177c1a0/enunciados/detalhes/?turma=8839f1ab-94c9-49d8-90e4-45aa09960576`

### Setup Sintético via Mixer (Python Shell):

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.students.models import Student
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.corrections.models import TextCorrection, CorrectionCriterion
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.answers.models import TextualAnswer

# 1. Tenant e Usuário
client = mixer.blend(Client, name="Escola Teste QA")
user = mixer.blend(User, client=client, user_type=2, is_superuser=True)

# 2. Caderno e Turma
exam = mixer.blend(Exam, created_by=user, name="Prova Refactor Correção")
school_class = mixer.blend(SchoolClass, name="Turma A")
app = mixer.blend(Application, exam=exam, deadline_for_correction_of_responses=None)
app.school_classes.add(school_class)

# 3. Rubrica de Critérios
rubrica = mixer.blend(TextCorrection, client=client, name="Rubrica Redação")
crit1 = mixer.blend(CorrectionCriterion, text_correction=rubrica, name="Gramática", order=1, maximum_score=2.0)
crit2 = mixer.blend(CorrectionCriterion, text_correction=rubrica, name="Argumentação", order=2, maximum_score=2.0)

# 4. Questão Discursiva
q = mixer.blend(Question, category=Question.TEXTUAL, text_correction=rubrica, enunciation="Discorra sobre tecnologia na educação.")
eq = mixer.blend(ExamQuestion, exam=exam, question=q, weight=10.0)

# 5. Aluno e Resposta
student = mixer.blend(Student, client=client, name="Carlos Eduardo")
school_class.students.add(student)
app_student = mixer.blend(ApplicationStudent, application=app, student=student)
ans = mixer.blend(TextualAnswer, question=q, student_application=app_student, content="O avanço da tecnologia permite...")
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Carregamento em Lote O(1) e Filtro de Ano [Automatizável ✅]

#### Cenário 1 — Carga O(1) e hidratação de notas no payload inicial

**Ação humana:**
- [x] Acessar o caderno do Caso 1 (`/provas/12d0d423-a8f3-4934-8abf-0580ddf48285/enunciados/detalhes/?turma=7a24afea-b8c9-4b71-82ac-148ded9dca48`) logado como coordenação ou staff.
- [x] Localizar a questão discursiva com rubrica de 5 critérios e clicar no botão `"**Corrigir**"` (botão branco com borda cinza `tw-border-neutral-300`).
- [x] Conferir se o modal de correção abre em tela cheia exibindo a lista de alunos no acordeon lateral esquerdo.
- [x] Inspecionar a aba Rede (Network) do navegador e confirmar que a chamada para `/provas/api/exam-question/.../answers/v2/?class=...` retorna status `200 OK` (conforme validado na sua aba Network).
- [x] Clicar na requisição `v2/?class=...` na aba Rede ➔ aba **Response** (ou **Preview**) e conferir que dentro de `applications_student`, alunos já avaliados (ex.: `OLENDINA MOREIRA DE SOUZA FILHA`) trazem a chave `criterion_scores` populada com as notas e IDs dos critérios. 
- [x] No acordeon à esquerda da tela, clicar no aluno corrigido (**`OLENDINA MOREIRA DE SOUZA FILHA`** ou `WENER CARVALHO SANTOS`) e confirmar que as opções de competências aparecem marcadas em azul instantaneamente, sem gerar novas requisições HTTP na aba Rede.![alt text](../evidencias/image-12.png)
- [x] *(Nota de ambiente local)*: A coluna da direita com o texto *"Carregando, aguarde..."* tenta carregar o scan OMR do S3/CDN; como o arquivo físico não existe no ambiente local, esse loading na imagem é normal e não interfere na correção.

**Referência técnica (para automação):**
- URL: `/provas/12d0d423-a8f3-4934-8abf-0580ddf48285/enunciados/detalhes/?turma=7a24afea-b8c9-4b71-82ac-148ded9dca48`
- Seletor: `div[role="list"] > div:has(h3:has-text("Questão")) button:has-text("Corrigir")`
- Estado esperado no DOM: Modal `#detailModal` visível com classe `.modal.show`; acordeon `#answers-accordion` com lista de alunos e hidratação de notas via `criterion_scores`.
- Fixture: `CorrectionScreenLoader(exam_question, school_class=sc, year=2026, user=coord).load()` com `len(criterion_scores) > 0`.

#### Cenário 2 — Respeito ao parâmetro de ano (`?year=`) na query string

**Ação humana:**
- [ ] Abrir a tela de correção forçando um parâmetro de ano anterior na barra de endereço (ex.: `?year=2025`).
- [ ] Clicar no botão `"**Corrigir**"` de uma questão.
- [ ] Verificar na aba Rede que a requisição para o endpoint v2 recebe o parâmetro `&year=2025` na URL.
- [ ] Confirmar que o sistema não utiliza arbitrariamente o ano corrente (`2026`) quando o parâmetro `year` é fornecido na URL.

**Referência técnica (para automação):**
- URL: `/provas/<exam_id>/enunciados/detalhes/?year=2025&turma=<turma_id>`
- Seletor: `#answers-accordion`
- Estado esperado no DOM: Requisição de API disparada para `exams:exam_question_answers_detail_v2` com query param `year=2025`.
- Fixture: Aplicação com `application.date.year = 2025` filtrada adequadamente.

---

### 5.2 Correção de Discursiva e Prevenção de Duplicação [Automatizável ✅]

#### Cenário 3 — Seleção de aluno com notas prévias sem chamada de API redundante

**Ação humana:**
- [ ] No modal de correção da questão discursiva, clicar no nome de um aluno que já possua notas corrigidas (ex.: aluno com ícone verde de conferência).
- [ ] Observar que a tabela de `"**Competências**"` e `"**Pontos**"` exibe imediatamente os botões azuis selecionados com as notas salvas do aluno.
- [ ] Inspecionar a aba Rede e confirmar que **NÃO foi disparada nenhuma requisição** para `questions/api/correction-answers/`.
- [ ] Alternar para outro aluno corrigido e confirmar que as notas mudam instantaneamente conforme os dados de `criterion_scores` em memória.

**Referência técnica (para automação):**
- URL: `/provas/<exam_id>/enunciados/detalhes/`
- Seletor: `#answers-accordion h6:has-text("Aluno Corrigido")`
- Estado esperado no DOM: `label.tw-bg-blue-50.tw-text-blue-700` visível na tabela sem chamadas à rota `questions:get_correction_answers`.
- Fixture: `student.criterion_scores` contendo IDs populados no payload inicial.

#### Cenário 4 — Regravação de notas executando PUT em vez de duplicar via POST

**Ação humana:**
- [ ] Selecionar um aluno discursivo já corrigido.
- [ ] Alterar uma das opções de competência clicando em um valor diferente de nota (o botão pill correspondente deve ficar azul).
- [ ] Clicar no botão `"**Salvar**"` (botão roxo/primário `tw-bg-primary-600`).
- [ ] Observar a aba Rede: a requisição enviada para `/correcoes/api/textuais/<uuid>/` deve ser do método **`PUT`** (atualização), e **NÃO `POST`** (criação).
- [ ] Fechar o modal de correção clicando no botão `"**Fechar**"` (ícone `X` no canto superior direito).
- [ ] Reabrir a mesma questão clicando em `"**Corrigir**"` e selecionar novamente o mesmo aluno.
- [ ] Clicar em `"**Salvar**"` mais uma vez.
- [ ] Verificar no banco de dados (ou via API) que o número de registros em `CorrectionTextualAnswer` para aquela resposta permaneceu exatamente o mesmo (sem linhas duplicadas geradas).

**Referência técnica (para automação):**
- URL: `/correcoes/api/textuais/<uuid>/`
- Seletor: `#answers-accordion button:has-text("Salvar")`
- Estado esperado no DOM: Mensagem de confirmação `"Correção salva!"` exibida; requisição HTTP PUT com status 200.
- Fixture: `CorrectionTextualAnswer.objects.filter(textual_answer=answer).count()` constante antes e após a regravação.

---

### 5.3 Questões de Arquivo Anexado (OMR) e Objetivas [Automatizável ✅]

#### Cenário 5 — Seleção e salvamento em questão de "Arquivo anexado" (OMR)

**Ação humana:**
- [ ] Acessar o caderno do Caso 2 (`/provas/93faa67a-e3a2-4388-931c-273b3177c1a0/enunciados/detalhes/?turma=8839f1ab-94c9-49d8-90e4-45aa09960576`).
- [ ] Localizar a questão de categoria Arquivo anexado com rubrica de critérios e clicar no botão `"**Corrigir**"`.
- [ ] Selecionar um aluno no acordeon e verificar que as folhas digitalizadas do aluno aparecem na coluna direita no visualizador de imagens.
- [ ] Conferir que as notas por critério são hidratadas corretamente na tabela de competências.
- [ ] Modificar uma nota e clicar no botão `"**Salvar**"`.
- [ ] Confirmar na aba Rede que a requisição foi disparada via **`PUT`** para `/correcoes/api/arquivos/<uuid>/`.

**Referência técnica (para automação):**
- URL: `/provas/93faa67a-e3a2-4388-931c-273b3177c1a0/enunciados/detalhes/`
- Seletor: `#answers-accordion button:has-text("Salvar")`
- Estado esperado no DOM: Requisição PUT para rota de arquivo respondendo 200; visualizador `#image` carregado com o scan OMR.
- Fixture: `CorrectionFileAnswer.objects.filter(file_answer=fa).count()` invariante.

#### Cenário 6 — Preservação de comportamento em Questões Objetivas e sem Rubrica

**Ação humana:**
- [ ] Na tela de correção por enunciado, clicar no filtro `"**Objetivas**"` (botão pill na barra superior de filtros).
- [ ] Clicar no botão `"**Corrigir**"` de uma questão objetiva.
- [ ] Verificar que o modal abre exibindo as alternativas marcadas pelos alunos, acertos e erros, sem qualquer tabela de rubrica de critérios.
- [ ] Conferir que o payload do endpoint v2 retorna `criterion_scores: []` vazio, sem falhas de renderização ou quebras de script no console do navegador.

**Referência técnica (para automação):**
- URL: `/provas/<exam_id>/enunciados/detalhes/`
- Seletor: `button:has-text("Objetivas")`
- Estado esperado no DOM: Tabela de competências ausente; alternativas objetivas renderizadas com classes `.alternative-correct` / `.alternative-incorrect`.
- Fixture: `question.category == Question.CHOICE`.

---

### 5.4 Isolamento de Critérios entre Questões [Automatizável ✅]

#### Cenário 7 — Isolamento de notas entre questões distintas com a mesma rubrica

**Ação humana:**
- [ ] Em uma prova com duas questões discursivas (Q1 e Q2) associadas à mesma rubrica/template de correção:
- [ ] Corrigir as notas de um aluno na questão Q1 e salvar.
- [ ] Fechar o modal e abrir o modal de correção da questão Q2.
- [ ] Selecionar o mesmo aluno na questão Q2.
- [ ] Confirmar que as notas marcadas em Q1 **NÃO aparecem** em Q2 (as competências em Q2 devem aparecer limpas/zeradas para esse aluno).

**Referência técnica (para automação):**
- URL: `/provas/<exam_id>/enunciados/detalhes/`
- Seletor: `#answers-accordion h6:has-text("<Aluno>")`
- Estado esperado no DOM: `label.tw-bg-blue-50` ausente na Q2 para o aluno; `criterion_scores` de Q2 vazio no payload.
- Fixture: Duas instâncias de `ExamQuestion` com `question.text_correction` idêntico, notas vinculadas apenas à resposta de Q1.

---

### 5.5 Tratamento de Falhas e Indicadores Visuais [Apenas Manual 👁]

#### Cenário 8 — Simulação de falha na gravação e exibição de alerta de erro

**Ação humana:**
- [ ] Abrir o modal de correção de uma questão discursiva e selecionar um aluno.
- [ ] Abrir as ferramentas de desenvolvedor (F12) ➔ aba Rede (Network) ➔ ativar bloqueio de requisições ou simular falha na rota `/correcoes/api/textuais/`.
- [ ] Modificar uma nota e clicar no botão `"**Salvar**"`.
- [ ] Confirmar que o indicador exibe a mensagem em vermelho: `"**Erro no envio, tente novamente**"`.
- [ ] Confirmar que o console não trava a aplicação e que o usuário pode tentar submeter novamente após restabelecer a conexão.

**Referência técnica (para automação):**
- URL: `/correcoes/api/textuais/`
- Seletor: `#answers-accordion span:has-text("Erro no envio, tente novamente")`
- Estado esperado no DOM: Elemento `span.text-danger` visível no DOM; chamada `handleApplicationStudentStatus('error')` disparada.
- Fixture: Interceptação HTTP 500 no endpoint de correção.

---

### 5.6 Integridade Visual e Regressão de Layout [Apenas Manual 👁]

#### Cenário 9 — Verificação visual de layout, acordeons e visualizador de imagem

**Ação humana:**
- [ ] Conferir o visual da listagem de questões: cabeçalho com nome do caderno, dropdown de turmas `"select[name='turma']"`, botões de filtro (`"Todas"`, `"Objetivas"`, `"Dissertativas"`, `"Somatórias"`).
- [ ] Conferir a barra de progresso de cada card de questão (`"X de Y corrigidas"`).
- [ ] No modal de correção, testar o botão `"**Detalhes da questão**"` e verificar a expansão suave do enunciado (`transition: height 200ms`).
- [ ] Verificar a navegação sequencial entre questões pelos botões `"**Anterior**"` e `"**Próximo**"` no topo do modal.
- [ ] Testar os botões rápidos de atribuição de nota (`0%`, `25%`, `50%`, `75%`, `100%`) em questões sem rubrica e conferir preenchimento correto no input de nota.

**Referência técnica (para automação):**
- URL: `/provas/<exam_id>/enunciados/detalhes/`
- Seletor: `button[aria-controls="collapseEnunciation"]`, `#detailModal button:has-text("Próximo")`
- Estado esperado no DOM: Expansão do elemento `#collapseEnunciation`; chevron com classe `.tw-rotate-180`.
- Fixture: Renderização padrão do template `exam_detail_enunciation_new.html`.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Validar que nenhum componente Tailwind com prefixo `tw-*` perdeu estilos ou sofreu quebra de padding/margin na listagem de cards.
- [ ] Validar que a tabela de rubricas (`Competências` e `Pontos`) possui bordas arredondadas e divisores cinzas (`tw-border-gray-100`, `tw-divide-gray-200`).
- [ ] Confirmar que os pills de seleção de notas mantêm a transição visual de cinza (`tw-ring-gray-200`) para azul suave (`tw-bg-blue-50 tw-text-blue-700`) quando ativos.
- [ ] Confirmar que o visualizador de imagens (ViewerJS / OpenSeaDragon) carrega os scans OMR na coluna direita sem distorção e com suporte a zoom/pan.
- [ ] Validar que o botão fechar do modal (`data-dismiss="modal"`) encerra o modal e devolve o foco para a listagem sem travar o scroll da página.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!WARNING]
> **[Backend Logic / Cobertura] Pendência Crítica de Testes Automatizados Registrada no ClickUp**
> - **Título:** Ausência da suíte de testes automatizados `test_correction_screen_loading.py`.
> - **Contexto / Causa Raiz:** O desenvolvedor responsável (Richard Ataliba) alertou nos comentários da task ClickUp que os testes automatizados da tarefa 4 da OpenSpec (`test_correction_screen_loading.py`) ficaram como pendência técnica. O arquivo ainda não existe no repositório.
> - **Comportamento Esperado:** Conforme `specs/correction-screen-loading/spec.md`, o teto constante de queries (2 vs 20 alunos) e a equivalência de payload devem ser blindados por testes unitários/integração.
> - **Workaround para QA:** Executar a validação funcional exploratória completa descrita na Seção 5 utilizando os cadernos reais já existentes no banco local (Caso 1 e Caso 2).

> [!NOTE]
> **[Database / Scope Gap] Duplicados Históricos em Produção Não Foram Removidos**
> - **Contexto:** Registros de duplicidades em `CorrectionTextualAnswer` gerados no passado permanecem no banco. O refactor atual impede a criação de *novos* duplicados através do reuso de IDs e envio de `PUT`, mas a limpeza retroativa é deliberadamente tratada como não-objetivo deste ciclo e deverá ocorrer em card futuro.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Constraint de Integridade no Banco de Dados (`unique_together`):**
> Adicionar `unique_together = ('textual_answer', 'correction_criterion')` no model `CorrectionTextualAnswer` e no `CorrectionFileAnswer` após execução de script de higienização de registros duplicados em produção.

> [!NOTE]
> **Refatoração do Modal de Correção por Aluno:**
> O modal alternativo de correção por aluno (`exam-detail-functions.js`) ainda segue o caminho legado. Recomenda-se estender o uso de `CorrectionScreenLoader` também para esse modal em uma entrega futura.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_detail_enunciation_new.md)**

### Automation Snippet (Python Playwright + Mixer Data Setup):

```python
import pytest
from playwright.sync_api import Page, expect
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.students.models import Student
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.corrections.models import TextCorrection, CorrectionCriterion
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.answers.models import TextualAnswer

def test_correction_screen_discursive_hydration_and_put(page: Page, live_server):
    # 1. Setup de dados via Mixer
    client = mixer.blend(Client, name="Escola QA")
    coord = mixer.blend(User, client=client, user_type=2, is_superuser=True)
    coord.set_password("123456")
    coord.save()

    exam = mixer.blend(Exam, created_by=coord, name="Exame QA Discursivo")
    s_class = mixer.blend(SchoolClass, name="Turma 101")
    app = mixer.blend(Application, exam=exam, deadline_for_correction_of_responses=None)
    app.school_classes.add(s_class)

    rubric = mixer.blend(TextCorrection, client=client, name="Rubrica")
    crit = mixer.blend(CorrectionCriterion, text_correction=rubric, name="Critério 1", order=1, maximum_score=5.0)

    q = mixer.blend(Question, category=Question.TEXTUAL, text_correction=rubric, enunciation="Enunciado de teste")
    eq = mixer.blend(ExamQuestion, exam=exam, question=q, weight=10.0)

    student = mixer.blend(Student, client=client, name="Aluno Playwright")
    s_class.students.add(student)
    app_student = mixer.blend(ApplicationStudent, application=app, student=student)
    ans = mixer.blend(TextualAnswer, question=q, student_application=app_student, content="Resposta do aluno")

    # 2. Login
    page.goto(f"{live_server.url}/conta/entrar/")
    page.fill("#id_username", coord.email)
    page.fill("#id_password", "123456")
    page.click("button[type='submit']")

    # 3. Navegação para Correção por Enunciado
    page.goto(f"{live_server.url}/provas/{exam.pk}/enunciados/detalhes/?turma={s_class.pk}")
    
    # 4. Abertura do Modal de Correção
    page.click("div[role='list'] button:has-text('Corrigir')")
    expect(page.locator("#detailModal")).to_be_visible()

    # 5. Seleção do Aluno e Atribuição de Nota no Critério
    page.click(f"#answers-accordion h6:has-text('{student.name}')")
    crit_pill = page.locator(f"label[for*='line-competence-enem-{crit.id}']").first
    crit_pill.click()
    expect(crit_pill).to_have_class(re.compile(r"tw-bg-blue-50"))

    # 6. Salvar e Validar Confirmação
    page.click("#answers-accordion button:has-text('Salvar')")
    expect(page.locator("#answers-accordion span:has-text('Correção salva!')")).to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante o planejamento:** A ausência dos testes automatizados declarados na OpenSpec, que foi expressamente sinalizada pelo desenvolvedor nos comentários do ClickUp e impede a validação automatizada imediata do teto de queries via CI.
- **Interações e alinhamento técnico:** Discussão entre a equipe (comentários de Dioney e Luiz no ClickUp) reforçou a importância de manter o escopo enxuto, focando em resolver o gargalo de performance O(1) e a duplicação no Vue sem abrir frentes arriscadas de banco de dados neste ciclo.
- **Melhorias de processo sugeridas:** Criar os testes unitários da camada de serviço (`test_correction_screen_loading.py`) antes de mover o card para a coluna de QA/Testing no ClickUp, evitando que tarefas cheguem para validação com pendências técnicas abertas.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias:
1. Adicionar no workflow /qa-criar-plano uma checagem automática de comentários no ClickUp para sinalizar explicitamente pendências técnicas e status de PR declarados pelo time.
2. Identificar se o repositório possui dados de baseline já cadastrados no banco local (como os cadernos do Caso 1 e Caso 2) para permitir execução imediata de testes sem necessidade de fixtures manuais em todos os cenários.
-->

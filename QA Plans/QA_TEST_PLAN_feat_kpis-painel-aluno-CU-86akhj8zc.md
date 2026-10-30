## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-30 |
| **Tarefa ClickUp:** | [#86akhj8zc](https://app.clickup.com/t/3120759/86akhj8zc) — Maior clareza nos resultados dos KPIs no painel do aluno |
| **Branch Backend (lizeedu):** | `feat/kpis-painel-aluno-CU-86akhj8zc` (base: `dev`) |
| **Branch Student (lize-student):** | `feat/86akhj8zc-kpis-painel-aluno` (base: `origin/dev`) |
| **Ambiente de Integração:** | Integrado em `dev` (staging) — CI Run `40937504443` (success) |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | App do Aluno / Painel Geral / KPIs de Desempenho / Estatísticas |
| **Nível de Risco:** | Médio (alteração de cálculo de KPI cacheado, janela cronológica e impacto multi-repo) |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (completa com proposal, design, spec e tasks no student) |

---

## 1. Summary of Changes (Resumo das Alterações)

Esta entrega atende à solicitação de escolas parceiras (em especial a Rede Integral) que apontaram falta de clareza e transparência no cálculo dos três KPIs de topo do Painel do Aluno: **Questões**, **Desempenho** e **Nota**.

### Backend (`lizeedu` — app `students` / API v3)

* **Restrição da Nota ao Ano Letivo Corrente (`D1`):** A média de notas (`grade_avg`) do aluno antes agregava todas as aplicações históricas sem filtro de ano. Agora a consulta filtra estritamente por `application__date__year = timezone.now().year`, unificando a regra temporal com Questões e Desempenho.
* **Cálculo da Tendência de Evolução (`D4`):** Criação do módulo dedicado [`fiscallizeon/app/students/performance_summary.py`](file:///home/israel/Workspace/lizeedu/fiscallizeon/app/students/performance_summary.py) com funções puras e de agregação cronológica (`split_windows`, `build_trend`, `grade_trend`, `performance_trend`):
  * Compara a janela das **5 avaliações mais recentes** do ano corrente com as **até 5 avaliações anteriores a elas**.
  * Retorna o nó aditivo `'trend': {'direction': 'up' | 'down' | 'stable', 'recent': float, 'previous': float}` ou `None` caso o histórico tenha 5 avaliações ou menos.
  * O cálculo de Desempenho agrega o percentual total de acertos da janela (acertos totais ÷ questões totais), mantendo fidelidade com a métrica global.
* **Invalidação de Cache (`D5`):** Chave de cache atualizada para `student_{user.student.id}_performance_summary_v2_{type}` (20 minutos), impedindo que dados do formato legado persistam em produção.
* **Cobertura de Testes Automatizados:** Criação de [`fiscallizeon/app/students/tests/test_performance_summary.py`](file:///home/israel/Workspace/lizeedu/fiscallizeon/app/students/tests/test_performance_summary.py) cobrindo regras puras de janelas e o endpoint completo via `APIClient` e fixtures com `mixer`.

### Frontend Aluno (`lize-student` / `app-aluno` — SPA React)

* **Atualização de Rótulo ("Média das notas"):** O KPI anteriormente rotulado como `"Nota"` agora exibe `"Média das notas"` tanto na versão desktop quanto na versão compacta mobile.
* **Tooltips Explicativos Acessíveis (`KpiInfo`):** Implementado botão circular com ícone ⓘ ao lado de cada rótulo de KPI, acessível via hover e foco de teclado (desktop) e clique/toque (mobile), exibindo explicações concisas e transparentes sobre o que compõe cada número.
* **Indicadores Visuais de Tendência (`KpiTrend`):** Exibição de ícones direcionais sutis:
  * Seta verde para cima (`ChevronUp` com `text-green-600`) para evolução positiva.
  * Seta vermelha para baixo (`ChevronDown` com `text-red-600`) para declínio.
  * Ocultação da seta quando a tendência for estável (`stable`) ou quando não houver histórico suficiente (`null`).
  * Texto exclusivo para leitores de tela (`sr-only`) garantindo acessibilidade auditiva.
* **Leitura Resiliente do Payload (`parsePerformanceSummary`):** A leitura dos itens do endpoint agora busca pelo campo `type` (`question`, `performance`, `grade`), eliminando a dependência frágil de índices fixos no array.

---

## 2. Scope Boundaries (Diferenças de Escopo)

**IN SCOPE:**

- Exibição do rótulo `"Média das notas"` no desktop e no mobile no topo do Painel do Aluno.
- Exibição de ícone ⓘ com tooltip explicativo em cada um dos 3 cards de KPI.
- Exibição de seta verde (`up`) ou vermelha (`down`) ao lado do valor nos cards de **Desempenho** e **Média das notas** quando houver histórico >= 6 avaliações no ano.
- Omissão de seta no card de **Questões** (não possui tendência).
- Omissão de seta quando a direção for `stable` ou quando o aluno tiver 5 avaliações ou menos no ano corrente.
- Restrição do cálculo da média das notas estritamente para o ano letivo corrente (`application__date__year`).
- Funcionamento do tooltip via toque no mobile (evitando que o Radix Tooltip feche imediatamente).
- Compatibilidade e resiliência caso o endpoint retorne `trend: null` ou dados de cache.

**OUT OF SCOPE:**

- Normalização da nota para a escala 0 a 10 (a pontuação respeita a soma ponderada de cada caderno).
- Inclusão de questões discursivas, arquivo ou somatória no percentual de Desempenho (mantido apenas objetivas conforme especificação).
- Gráficos de linha, área ou sparklines nos cards de KPI (a entrega contempla exclusivamente as setas direcionais).
- Alterações em outros cards do painel (ex: Simulado SiSU, Colegas de Turma ou Próximas Provas).
- Alteração no comportamento de faltas (`missed=True`), mantendo a regra existente de peso zero.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL SPA Aluno (`lize-student`) | Endpoint Backend Django (`lizeedu`) |
|---|---|---|---|
| Login do Aluno | Formulário de Login | `http://localhost:5173/login` | `/api/v3/auth/token/` |
| Painel do Aluno | `"Visão Geral"` (sidebar do aluno) | `http://localhost:5173/painel/` | `GET /api/v3/student/performance_summary/?type=all` |

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente a rota/componente da SPA Aluno (`src/components/dashboard/stats-cards.tsx`).
🔗 **[Ver Mapeamento de Tela](docs/tests/usability/stats_cards.md)**

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos de Testes Automatizados

**1. Testes Unitários e de Integração do Backend (`lizeedu`):**
```bash
source venv/bin/activate && pytest fiscallizeon/app/students/tests/test_performance_summary.py --reuse-db
```

**2. Testes de Componentes e Libs do Frontend (`lize-student`):**
```bash
cd ../lize-student && bun x vitest run src/components/dashboard/stats-cards.test.tsx src/lib/performance-summary.test.ts
```

### Persona do Testador

* **Aluno:** `cloud.student@lize.local` (ou aluno criado com vínculo ativo em cliente com `can_access_app=True`). Senha padrão: `123456` (ou `lize-cloud-lab`).

### Setup de Massa de Dados via Mixer (Cenários Determinísticos)

Para simular os cenários de teste diretamente no banco de dados local através do Django Shell (`python manage.py shell`):

```python
from datetime import timedelta
from django.utils import timezone
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.answers.models import OptionAnswer
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.clients.models import Client
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question, QuestionOption
from fiscallizeon.students.models import Student

# 1. Recupera ou cria o aluno de teste
user = User.objects.filter(email='cloud.student@lize.local').first()
if not user:
    client = mixer.blend(Client, can_access_app=True, type_client=1)
    user = mixer.blend(User, email='cloud.student@lize.local', can_access_app=True, must_change_password=False)
    user.set_password('123456')
    user.save()
    student = mixer.blend(Student, user=user, client=client)
else:
    student = user.student

def criar_avaliacao_finalizada(student, data_aplicacao, peso=10, acertou=True):
    exam = mixer.blend(Exam, is_abstract=True)
    question = mixer.blend(Question, category=Question.CHOICE)
    mixer.blend(ExamQuestion, exam=exam, question=question, weight=peso)
    option = mixer.blend(QuestionOption, question=question, is_correct=acertou)

    app = mixer.blend(
        Application,
        exam=exam,
        category=Application.MONITORIN_EXAM,
        date=data_aplicacao,
        release_result_at_end=True,
        student_stats_permission_date=timezone.now() - timedelta(days=1),
    )
    app_student = mixer.blend(
        ApplicationStudent,
        application=app,
        student=student,
    )
    ApplicationStudent.objects.filter(pk=app_student.pk).update(
        start_time=timezone.now(),
        end_time=timezone.now(),
    )
    answer = OptionAnswer.objects.create(
        question_option=option,
        student_application=app_student,
        status=OptionAnswer.ACTIVE,
    )
    return app_student
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Validação Visual dos Rótulos e Tooltips [Automatizável ✅]

Persona: Aluno logado (`cloud.student@lize.local`).

#### Cenário 1 — Verificação do novo rótulo "Média das notas" em Desktop

**Ação humana:**
- [x] Acessar o app do aluno e navegar para o Painel Geral (`/painel/`).
- [x] Localizar a linha superior de 3 cards de estatísticas.
- [x] Verificar se o terceiro card exibe o título `"Média das notas"` (em substituição ao antigo rótulo `"Nota"`).
- [x] Confirmar a presença do ícone de medalha 🏅 e valor formatado com 2 casas decimais.
![alt text](../evidencias/image-25.png)

**Referência técnica (para automação):**
- URL: `/painel/`
- Seletor: `div.hidden.lg\:flex div:has-text("Média das notas")`
- Estado esperado: Elemento visível, contendo texto `"Média das notas"`
- Fixture: Aluno autenticado com dados carregados no endpoint `/api/v3/student/performance_summary/`

---

#### Cenário 2 — Abertura e texto do Tooltip no Desktop (Hover e Foco)

**Ação humana:**
- [x] Passar o cursor do mouse sobre o ícone ⓘ do card `"Questões"`.
- [x] Confirmar que o tooltip abre com o texto: `"Total de questões objetivas que você respondeu nas avaliações e listas do ano letivo com resultado já liberado."`.
![alt text](../evidencias/image-26.png)
- [x] Passar o cursor sobre o ícone ⓘ do card `"Desempenho"`.
- [x] Confirmar que o tooltip abre com o texto: `"Percentual de acertos nas questões objetivas que você respondeu no ano letivo. A seta compara suas 5 últimas avaliações com as 5 anteriores."`.
![alt text](../evidencias/image-27.png)
- [x] Passar o cursor sobre o ícone ⓘ do card `"Média das notas"`.
- [x] Confirmar que o tooltip abre com o texto: `"Média das notas que você obteve nas avaliações e listas do ano letivo. A seta compara suas 5 últimas avaliações com as 5 anteriores."`.
![alt text](../evidencias/image-28.png)
- [x] Navegar via tecla `Tab` até os botões ⓘ e validar se o tooltip é exibido ao receber foco via teclado.
![alt text](../evidencias/image-29.png)
**Referência técnica (para automação):**
- URL: `/painel/`
- Seletor: `button[aria-label="Como é calculado: Desempenho"]`
- Ação: `.hover()` ou `.focus()`
- Estado esperado: `[role="tooltip"]:has-text("Percentual de acertos nas questões objetivas")` visível no DOM
- Fixture: Aluno autenticado

---

#### Cenário 3 — Comportamento de Toque no Mobile [Apenas Manual 👁]

**Ação humana:**
- [x] Alternar o navegador para modo responsivo (viewport de smartphone, ex: 390x844 ou tela mobile < 768px).
- [x] Verificar a exibição da barra condensada de 3 colunas no topo (`Questões`, `Desempenho`, `Média das notas`).
- [x] Tocar com o dedo no ícone ⓘ de `"Desempenho"`.
- [x] Verificar se o tooltip abre e permanece visível na tela sem sumir imediatamente.
- [x] Tocar novamente no ícone ⓘ e confirmar que o tooltip se fecha adequadamente.

**Referência técnica (para automação):**
- URL: `/painel/`
- Seletor: `div.grid.grid-cols-3 button[aria-label="Como é calculado: Desempenho"]`
- Estado esperado: Tooltip toggle ativo no evento `click`

---

### 5.2 Validação do Cálculo de Tendência [Automatizável ✅]

#### Cenário 4 — Aluno com Histórico Insuficiente (<= 5 avaliações no ano)

**Ação humana:**
- [x] Logar com aluno que possui apenas 3 avaliações concluídas no ano corrente.
- [x] Observar os cards de `"Desempenho"` e `"Média das notas"`.
- [x] Confirmar que **nenhuma seta** (nem verde nem vermelha) é exibida ao lado dos valores.
- [x] Confirmar que o card de `"Questões"` nunca exibe setas.
![alt text](../evidencias/image-30.png)

**Referência técnica (para automação):**
- URL: `/painel/`
- API Payload: `trend: null` nos itens `performance` e `grade`
- Seletor: `span[data-trend]`
- Estado esperado: `locator('span[data-trend]').count() === 0`
- Fixture: Criar 3 avaliações finalizadas no ano corrente via mixer

---

#### Cenário 5 — Tendência de Alta em Desempenho e Média das Notas

**Ação humana:**
- [x] Preparar aluno com 7 avaliações no ano corrente:
  - 2 avaliações mais antigas com notas baixas (ex: 2.0 e 3.0) e erros nas questões objetivas.
  - 5 avaliações mais recentes com notas altas (ex: 9.0 e 10.0) e acertos nas questões.
- [x] Recarregar o Painel do Aluno.
- [x] Observar o card `"Desempenho"`:
  - Confirmar a presença da **seta verde para cima** (`ChevronUp`).
- [x] Observar o card `"Média das notas"`:
  - Confirmar a presença da **seta verde para cima** (`ChevronUp`).
![alt text](../evidencias/image-31.png)

**Referência técnica (para automação):**
- URL: `/painel/`
- API Payload: `trend.direction === "up"`
- Seletor: `span[data-trend="up"]`
- Estado esperado: Elemento visível com classe `text-green-600` e elemento filho `svg` (`ChevronUp`)
- Fixture: 2 aplicações antigas (nota baixa) + 5 aplicações recentes (nota alta)

---

#### Cenário 6 — Tendência de Queda em Desempenho e Média das Notas

**Ação humana:**
- [x] Preparar aluno com avaliações no ano corrente onde a pontuação recente é menor que a anterior (testado com Sarah Nogueira).
- [x] Recarregar o Painel do Aluno.
- [x] Observar os cards `"Desempenho"` e `"Média das notas"`.
- [x] Confirmar a presença da **seta vermelha para baixo** (`ChevronDown`).
![alt text](../evidencias/image-32.png)

**Referência técnica (para automação):**
- URL: `/painel/`
- API Payload: `trend.direction === "down"`
- Seletor: `span[data-trend="down"]`
- Estado esperado: Elemento visível com classe `text-red-600` e elemento filho `svg` (`ChevronDown`)
- Fixture: 2 aplicações antigas (nota alta) + 5 aplicações recentes (nota baixa)

---

#### Cenário 7 — Tendência Estável (Valores Idênticos nas Janelas)

**Ação humana:**
- [ ] Preparar aluno com avaliações cuja média das 5 recentes seja idêntica (arredondada a 2 casas) à média das anteriores.
- [ ] Recarregar o Painel do Aluno.
- [ ] Confirmar que **nenhuma seta** é exibida (o sistema não exibe seta de traço ou neutra, preservando a limpeza do layout).

**Referência técnica (para automação):**
- URL: `/painel/`
- API Payload: `trend.direction === "stable"`
- Seletor: `span[data-trend]`
- Estado esperado: Não renderizado no DOM (`null`)
- Fixture: Avaliações com valores idênticos entre janelas

---

### 5.3 Isolamento Temporal do Ano Letivo [Automatizável ✅]

#### Cenário 8 — Avaliações do Ano Anterior Não Impactam o Painel Atual

**Ação humana:**
- [ ] Inserir para o aluno uma avaliação finalizada no ano anterior com nota `0.0`.
- [ ] Inserir para o mesmo aluno 1 avaliação finalizada no ano corrente com nota `10.0`.
- [ ] Acessar o Painel do Aluno.
- [ ] Verificar o card `"Média das notas"`.
- [ ] Confirmar que a média exibida é **10.0** (e não 5.0), provando que o ano anterior é completamente ignorado no cálculo anual.

**Referência técnica (para automação):**
- URL: `/painel/`
- API Endpoint: `GET /api/v3/student/performance_summary/?type=all`
- Estado esperado: `gradeAvg === 10.0`
- Fixture: 1 aplicação em `ano_corrente - 1` + 1 aplicação em `ano_corrente`

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Alinhamento do Card Desktop:** O valor numérico e o emoji ficam alinhados horizontalmente à esquerda, enquanto a seta de tendência se posiciona à direita sem quebrar a altura do card.
- [ ] **Alinhamento no Mobile:** A seta de tendência fica posicionada ao lado do emoji de forma compacta, sem empurrar o rótulo para fora da coluna.
- [ ] **Contraste e Cores:**
  - Seta de alta: verde nítido (`text-green-600`).
  - Seta de queda: vermelho nítido (`text-red-600`).
  - Botão ⓘ: cinza suave (`text-muted-foreground`), escurecendo no hover (`hover:text-foreground`).
- [ ] **Comparação com Mockups do ClickUp:** Conferir se a disposição dos elementos reflete fielmente as imagens anexadas na tarefa `CU-86akhj8zc`.

---

## 7. Bugs and Observations (Problemas Encontrados)

### 7.1. ⚠️ Inconsistência Crítica: Dessincronização de Janelas entre Média de Notas e Desempenho

| Item | Descrição |
|---|---|
| **Tipo:** | Inconsistência na Regra de Negócio / Lógica de Agregação |
| **Componente:** | Backend (`fiscallizeon/app/students/performance_summary.py`) |
| **Gravidade:** | Média (Não quebra a tela, mas gera dados temporalmente incoerentes entre cards) |

#### 1. Descrição do Problema
Os cards de **"Média das notas"** e **"Desempenho"** são apresentados lado a lado no dashboard com a premissa de indicar a tendência recente do aluno ("baseado nas últimas 5 avaliações"). No entanto, os dois cálculos utilizam conjuntos de dados diferentes no banco:
* **Média das Notas (`get_grades_current_year`):** Consulta todas as `ApplicationStudent` finalizadas no ano corrente.
* **Desempenho (`get_corrects_and_totals_current_year`):** Consulta apenas aplicações que possuem respostas objetivas registradas (`OptionAnswer`).

#### 2. Evidência Real de Produção (Aluna Sarah - Rede Decisão)
* **Provas usadas na Média de Notas:** 5 provas P6 realizadas em **24 e 25 de Setembro de 2026** (onde a aluna tirou 0.0).
* **Provas usadas no Desempenho:** 5 provas P4 realizadas em **25 e 26 de Junho de 2026** (**3 meses antes!**).

**Efeito visível na tela:** O card de notas olha para Setembro e o card de desempenho olha para Junho. O aluno vê ao mesmo tempo uma seta vermelha $\downarrow$ e uma seta verde $\uparrow$ que referenciam momentos totalmente distintos da sua vida escolar.

#### 3. Sugestão de Melhoria para o Time de Desenvolvimento
Unificar a lista base de aplicações antes de calcular as janelas móveis:
* Determinar primeiro as 5 últimas `ApplicationStudent` finalizadas no ano letivo;
* Calcular a média de notas **e** a taxa de acertos objetivas referentes a **esse mesmo conjunto fixo de aplicações**.

---

### 7.2. ⚠️ Assimetria e Distorção Estatística no Histórico entre 6 e 9 Avaliações

| Item | Descrição |
|---|---|
| **Tipo:** | Distorção de Amostragem / Falha Metodológica |
| **Componente:** | Backend (`split_windows` em `performance_summary.py`) |
| **Gravidade:** | Média |

* **Regra Atual:** O algoritmo exige `len(series) > 5` para habilitar a tendência. Ele fixa as **5 mais recentes** no bloco `recent` e joga as restantes no bloco `previous` (`series[-10:-5]`).
* **Impacto Real (Cenário de 6 avaliações):**
  * O sistema compara a média de **5 provas recentes** contra **1 única prova antiga**.
  * Se o aluno tirou **10.0** na 1ª prova do ano e manteve médias constantes de **9.0** nas 5 seguintes, o cálculo faz: `recent (9.0) < previous (10.0)` $\rightarrow$ **Seta Vermelha de Queda $\downarrow$**!
  * O aluno é penalizado visualmente com declínio mesmo tendo desempenho altíssimo e consistente. A amostragem só se equilibra de verdade (5 contra 5) a partir da 10ª avaliação.
* **Recomendação:** Avaliar se a tendência só deve ser exibida com pelo menos 10 avaliações (5 vs 5 equilibradas), ou ponderar a comparação para evitar que 1 prova isolada distorça a métrica.

---

### 7.3. ⚠️ Distorção da Média Aritmética Simples com Provas de Escalas Heterogêneas

| Item | Descrição |
|---|---|
| **Tipo:** | Regra de Negócio / Interpretação Pedagógica |
| **Componente:** | Backend (`grade_avg` em `views.py` e `performance_summary.py`) |
| **Gravidade:** | Alta para a Percepção da Família/Aluno |

* **Contexto:** Na plataforma, cada caderno pode ter sua própria escala máxima (ex: lista semanal valendo **2.0**, simulado valendo **10.0**, prova bimestral valendo **20.0**).
* **Impacto Real:** A média é uma soma bruta dividida pela quantidade (`sum(grades) / len(grades)`), sem normalização para escala 0 a 10.
  * Se o aluno fez 4 testes de valor máximo 2.0 e tirou 2.0 em todos (100% de acerto), a média exibida no dashboard será **`2.00`**.
  * Isso induz a família a acreditar que o aluno está com nota vermelha/reprovado, gerando atrito no atendimento das escolas parceiras.

---

### 7.4. ⚠️ Penalização Desproporcional de Faltas (`missed=True` = `0.0`)

| Item | Descrição |
|---|---|
| **Tipo:** | Regra Pedagógica |
| **Componente:** | Backend (`get_grades_current_year`) |
| **Gravidade:** | Média |

* **Comportamento Atual:** Faltas do aluno entram em `ApplicationStudent` com nota `0.0`.
* **Impacto Real:** Se o aluno faltou a 2 provas por motivo de saúde justificado, a média recente despenca imediatamente para zero, disparando a seta vermelha $\downarrow$. A ausência administrativa destrói o indicador de aprendizado real do aluno.

---

### 7.5. ⚠️ Cache Rígido de 20 Minutos sem Invalidação por Eventos

| Item | Descrição |
|---|---|
| **Tipo:** | Arquitetura / Experiência do Usuário (Latência) |
| **Componente:** | Backend (`cache_key` em `views.py`) |
| **Gravidade:** | Baixa / Média |

* **Comportamento Atual:** O payload fica em cache Redis por 20 minutos (`timeout=20 * 60`).
* **Impacto Real:** Quando um professor termina de corrigir uma prova discursiva ou o coordenador libera o resultado de um simulado, o aluno entra no app e **por até 20 minutos continua vendo a média e a tendência antigas**, gerando a sensação de que o resultado não foi lançado.

---

### 7.6. ⚠️ Sobrecarga Cognitiva e Densidade Visual no Mobile (< 380px)

| Item | Descrição |
|---|---|
| **Tipo:** | UX / Design de Interface |
| **Componente:** | Frontend (`lize-student` / `app-aluno`) |
| **Gravidade:** | Baixa / Usabilidade |

* **Problema:** Em telas estreitas (360px a 375px), 3 colunas contendo simultaneamente `Número grande` + `Emoji` + `Seta direcional` + `Rótulo textual` + `Botão de Tooltip (i)` causam poluição visual e esmagamento dos elementos.
* **Redundância:** Na maioria dos casos, as setas de Notas e Desempenho sobem ou descem juntas. Ter duas setas disputando atenção em poucos pixels aumenta a carga cognitiva do estudante sem trazer clareza acionável.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Tratamento de faltas na média:** Conforme documentado no `design.md`, faltas (`missed=True`) entram no cálculo de `total_grade` como valor `0.0`. Se o aluno faltar a uma prova, isso derruba a média e gera seta de queda. Sugerir a produto avaliar no futuro se faltas justificadas deveriam ser descartadas da série de tendência.

> [!NOTE]
> **Identificadores estáveis no DOM (`data-testid`):** Adicionar atributos `data-testid="kpi-card-grade"` e `data-testid="kpi-trend"` para tornar a automação Playwright ainda mais desacoplada da estrutura CSS do Tailwind.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

Snippet Playwright de exemplo para execução do teste de fumaça na tela:

```python
def test_stats_cards_kpis_visiveis(page):
    # Navega para o painel do aluno autenticado
    page.goto("http://localhost:5173/painel/")
    
    # Valida presença dos três rótulos principais
    expect(page.locator("text=Questões")).to_be_visible()
    expect(page.locator("text=Desempenho")).to_be_visible()
    expect(page.locator("text=Média das notas")).to_be_visible()
    
    # Valida hover do tooltip de Média das notas
    info_btn = page.locator('button[aria-label="Como é calculado: Média das notas"]')
    info_btn.hover()
    expect(page.locator('[role="tooltip"]')).to_contain_text("Média das notas que você obteve")
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalos durante a validação:** Necessidade de rodar duas suítes independentes (Vitest na SPA do aluno e Pytest no backend Django).
- **Alinhamento de contrato:** A introdução do campo aditivo `trend` e a chave de cache `v2` garantiram que o frontend pudesse ser integrado sem risco de quebra para alunos com respostas cacheadas antigas.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias: O fluxo multi-repo (backend lizeedu + frontend lize-student) funcionou com extrema fluidez, cruzando o OpenSpec presente no repo do student com os modelos do lizeedu. -->


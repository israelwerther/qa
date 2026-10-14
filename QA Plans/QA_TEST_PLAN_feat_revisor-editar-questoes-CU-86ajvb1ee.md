# QA Test Plan — Revisor específico editar questões no período de revisão

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-13 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Questions / Exams / Clients Configuration |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ |
| **Branch:** | `feat/revisor-editar-questoes-CU-86ajvb1ee` |
| **ClickUp:** | [86ajvb1ee](https://app.clickup.com/t/86ajvb1ee) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend
- **Nova configuração `reviewers_can_edit_questions`** em `ClientQuestionsConfiguration` (booleano, `default=False`) — `fiscallizeon/clients/models.py`.
- **Property helper `reviewers_can_edit_questions`** no modelo `Client` para acesso simplificado.
- **Migration `0214_clientquestionsconfiguration_reviewers_can_edit_questions`** em `fiscallizeon/clients/migrations/`.
- **Lógica de permissão estendida** em `Question.reason_can_be_updated(user)` — `fiscallizeon/questions/models.py`:
  - Nova variável `reviewer_can_edit` que verifica se o professor está em `reviewed_by` da solicitação e se o caderno está em status elegível (`ELABORATING`, `OPENED`) ou a questão está em `CORRECTION_PENDING`.
  - A permissão do revisor específico é combinada com as regras existentes de coordenador e autor original.
  - O bypass de prazo de elaboração expirado agora respeita `reviewer_can_edit`.
- **Ajuste em `ExamQuestion.can_review`** — `fiscallizeon/exams/models.py`: permite que revisor específico revise questões elaboradas por ele mesmo quando `reviewers_can_review_own_questions` está ativo.

### Frontend
- **Novo toggle** em `/membros/questoes/configuracoes` — `fiscallizeon/clients/templates/dashboard/members/questions_configutation.html`:
  - Checkbox "Revisores específicos podem editar questões no período de revisão" ao lado da opção de coordenadores.

### Testes Automatizados
- **9 novos testes** em `fiscallizeon/questions/tests/test_models.py` cobrindo:
  - Revisor específico pode editar quando config ativa.
  - Revisor específico NÃO pode editar quando config desativada.
  - Professor não nomeado não edita mesmo com config ativa.
  - Campo `reviewed_by` vazio não concede edição.
  - Coordenador continua editando independentemente.
  - Autor original continua editando.
  - Questão usada em aplicação permanece bloqueada.
  - Revisor específico bloqueado quando caderno fora de elaboração/revisão.
  - Revisor específico pode editar questão em `CORRECTION_PENDING`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### IN SCOPE
- Ativação/desativação da configuração `reviewers_can_edit_questions` em `/membros/questoes/configuracoes`.
- Edição de questões por revisor específico nomeado em `reviewed_by` durante a janela de revisão.
- Bloqueio de edição quando o campo `Revisores` está vazio.
- Bloqueio de edição para professores não nomeados.
- Edição de questões em status `Aguardando correção` por elaborador e revisor.
- Preservação de bloqueios existentes (aplicação iniciada, caderno fechado).
- Independência da configuração de coordenadores.
- Registro de autoria no histórico da questão.

### OUT OF SCOPE
- Alterações na configuração `teachers_coordinations_can_edit_questions` (comportamento existente).
- Criação de novas telas ou fluxos.
- Alterações no app SPA do aluno (`/api/v3/`).
- Revisão por status com prazos por etapa (`ExamReviewDeadline`) — mencionado no design mas não implementado nesta branch.
- Notificação ao autor sobre edição realizada pelo rastreamento via `history` apenas.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Configurações das questões | "Configurações das questões" [verificar] | `/membros/questoes/configuracoes` | `questions_configuration` |
| Fila "Para você revisar" | "Para você revisar" [verificar] | `/provas/` | `exams_list` |
| Edição de questão | Modal/tela de edição de questão | `/provas/` (inline) | — |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comando para executar os testes automatizados

```bash
source venv/bin/activate && pytest fiscallizeon/questions/tests/test_models.py --reuse-db -v
```

### Personas dos Testes

| Persona | Descrição |
|---------|-----------|
| **Coordenação** | Usuário com `user_type=COORDINATION` e acesso à configuração |
| **Professor A (Elaborador)** | Professor que criou a questão |
| **Professor B (Revisor)** | Professor nomeado em `reviewed_by` da solicitação |
| **Professor C (Não revisor)** | Professor da disciplina que não é revisor da solicitação |

### Fixture/Mixer para Setup Manual

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User, Inspector
from fiscallizeon.clients.models import Client, ClientQuestionsConfiguration, Unity, SchoolCoordination
from fiscallizeon.exams.models import Exam, ExamTeacherSubject, ExamQuestion, StatusQuestion
from fiscallizeon.questions.models import Question

# Cliente com configuração ativa
client = mixer.blend(Client)
mixer.blend(ClientQuestionsConfiguration, client=client, reviewers_can_edit_questions=True)

# Unidade e coordenação
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)

# Professor A (Elaborador)
elaborator_user = mixer.blend(User)
elaborator_inspector = mixer.blend(Inspector, user=elaborator_user, inspector_type=Inspector.TEACHER)
elaborator_inspector.coordinations.add(coordination)

# Professor B (Revisor)
reviewer_user = mixer.blend(User)
reviewer_inspector = mixer.blend(Inspector, user=reviewer_user, inspector_type=Inspector.TEACHER)
reviewer_inspector.coordinations.add(coordination)

# Professor C (Não revisor)
other_user = mixer.blend(User)
other_inspector = mixer.blend(Inspector, user=other_user, inspector_type=Inspector.TEACHER)
other_inspector.coordinations.add(coordination)

# Caderno em elaboração
exam = mixer.blend(Exam, coordinations=[coordination.id], status=Exam.ELABORATING)

# Solicitação com revisor nomeado
ets = mixer.blend(ExamTeacherSubject, exam=exam)
ets.reviewed_by.add(reviewer_inspector)

# Questão criada pelo Professor A
question = mixer.blend(Question, created_by=elaborator_user)
eq = ExamQuestion(exam=exam, exam_teacher_subject=ets, question=question)
eq.save(skip_hooks=True)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Configuração da Funcionalidade [Automatizável ✅]

#### Cenário 1 — Ativar configuração de revisores específicos

**Ação humana:**
- [x] Acessar `/membros/questoes/configuracoes` como **Coordenação**
- [x] Verificar que o toggle "**Revisores específicos podem editar questões no período de revisão**" aparece ao lado de "Professores coordenadores podem editar questões de outros professores"
- [x] Ativar o toggle e clicar em "**Salvar**"
- [x] Verificar mensagem de sucesso
- [x] Recarregar a página e verificar que o toggle permanece ativo

**Referência técnica (para automação):**
- URL: `/membros/questoes/configuracoes`
- Seletor: `input[name="reviewers_can_edit_questions"]` ou `label:has-text("Revisores específicos podem editar questões no período de revisão")`
- Estado esperado: checkbox marcado após save
- Fixture: `mixer.blend(ClientQuestionsConfiguration, client=client, reviewers_can_edit_questions=True)`

---

#### Cenário 2 — Desativar configuração de revisores específicos

**Ação humana:**
- [x] Acessar `/membros/questoes/configuracoes` como **Coordenação**
- [x] Desativar o toggle "**Revisores específicos podem editar questões no período de revisão**"
- [x] Clicar em "**Salvar**"
- [x] Verificar mensagem de sucesso
- [x] Recarregar a página e verificar que o toggle permanece desativado

**Referência técnica (para automação):**
- URL: `/membros/questoes/configuracoes`
- Seletor: `input[name="reviewers_can_edit_questions"]`
- Estado esperado: checkbox desmarcado após save
- Fixture: `mixer.blend(ClientQuestionsConfiguration, client=client, reviewers_can_edit_questions=False)`

---

### 5.2 Edição por Revisor Específico [Automatizável ✅]

#### Cenário 3 — Revisor edita questão dentro da janela de revisão

**Ação humana:**
- [x] Com configuração **ativa**, criar caderno em status "**Elaborando**"
- [x] Criar solicitação com **Professor A** (autor) e adicionar **Professor B** no campo "**Revisores**"
- [x] Como **Professor A**, criar uma questão na solicitação
- [x] Fazer login como **Professor B** (revisor)
- [x] Acessar a fila "**Para você revisar**" ou abrir a questão criada
- [x] Verificar que o botão "**Editar**" está disponível
- [x] Alterar o texto do enunciado ou alternativas
- [x] Clicar em "**Salvar**"
- [x] Verificar que as alterações são salvas com sucesso

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: `button:has-text("Editar")` ou `a:has-text("Editar")`
- Estado esperado: botão visível e clicável; após save, dados atualizados
- Fixture: ver seção 4

---

#### Cenário 4 — Revisor fora da janela de revisão não edita

**Ação humana:**
- [x] Com configuração **ativa**, avançar o status do caderno para "**Fechado**" ou outro status fora de elaboração/revisão
- [x] Fazer login como **Professor B** (revisor)
- [x] Abrir a questão criada pelo **Professor A**
- [x] Verificar que o botão "**Editar**" está bloqueado/oculto. (Botão edição completa permanece)
- [x] Se tentar editar, verificar mensagem: "**Essa questão foi criada por outro professor e não pode ser editada.**"

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: `button:has-text("Editar")` ou mensagem de erro
- Estado esperado: botão oculto ou mensagem de bloqueio
- Fixture: `mixer.blend(Exam, status=Exam.CLOSED)`

---

### 5.3 Restrições de Segurança [Automatizável ✅]

#### Cenário 5 — Campo Revisores vazio não concede edição

**Ação humana:**
- [x] Com configuração **ativa**, criar solicitação com campo "**Revisores**" vazio
- [x] Como **Professor A**, criar uma questão nessa solicitação
- [x] Fazer login com **Professor C** (outro professor da disciplina, não revisor)
- [x] Tentar editar a questão do **Professor A**
- [x] Verificar que edição está bloqueada

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: `button:has-text("Editar")`
- Estado esperado: botão oculto ou mensagem de bloqueio
- Fixture: `mixer.blend(ExamTeacherSubject, exam=exam)` sem `reviewed_by`

---

#### Cenário 6 — Professor não nomeado não ganha edição

**Ação humana:**
- [x] Com configuração **ativa**, criar solicitação nomeando apenas **Professor B** como revisor
- [x] Fazer login como **Professor C** (não é revisor desta solicitação)
- [x] Tentar abrir e editar a questão do **Professor A**
- [x] Verificar que edição está bloqueada, mesmo que **Professor C** seja coordenador ou revisor de outra solicitação

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: `button:has-text("Editar")`
- Estado esperado: botão oculto ou mensagem de bloqueio
- Fixture: ver seção 4

---

### 5.4 Status "Aguardando Correção" [Automatizável ✅]

#### Cenário 7 — Elaborador e revisor editam questão em Aguardando correção

**Ação humana:**
- [x] Com configuração **ativa**, colocar a questão no status "**Aguardando correção**" (`CORRECTION_PENDING`)
- [x] Fazer login como **Professor A** (autor) → verificar que consegue editar
- [x] Fazer login como **Professor B** (revisor) → verificar que consegue editar
- [x] Verificar que ambos têm permissão de edição liberada

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: `button:has-text("Editar")`
- Estado esperado: botão visível para ambos
- Fixture: `mixer.blend(StatusQuestion, exam_question=eq, status=StatusQuestion.CORRECTION_PENDING, active=True)`

---

### 5.5 Bloqueios Soberanos [Automatizável ✅]

#### Cenário 8 — Questão usada em aplicação permanece bloqueada

**Ação humana:**
- [x] Em um caderno que já possua aplicação iniciada por alunos ou cartão OMR gerado
- [x] Tentar editar uma questão logado como **revisor**, **autor** ou **coordenador**
- [x] Verificar que edição está rigorosamente bloqueada para todos
- [x] Verificar mensagem informando que a questão já foi utilizada em prova

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: `button:has-text("Editar")`
- Estado esperado: botão oculto ou mensagem de bloqueio
- Fixture: `mixer.blend(Application, exam=exam)` com `start_time` preenchido

---

### 5.6 Não-Regressão [Automatizável ✅]

#### Cenário 9 — Coordenador continua editando independentemente

**Ação humana:**
- [x] Desativar a opção de revisores específicos
- [x] Ativar a opção "**Professores coordenadores podem editar questões de outros professores**"
- [x] Fazer login como **Coordenador de Disciplina**
- [x] Abrir e editar a questão do **Professor A**
- [x] Verificar que o coordenador consegue editar normalmente, sem interferência da nova configuração

**Referência técnica (para automação):**
- URL: `/membros/questoes/configuracoes`
- Seletor: `input[name="teachers_coordinations_can_edit_questions"]`
- Estado esperado: coordenador pode editar
- Fixture: `mixer.blend(ClientQuestionsConfiguration, client=client, teachers_coordinations_can_edit_questions=True, reviewers_can_edit_questions=False)`

---

#### Cenário 10 — Autor original continua editando

**Ação humana:**
- [x] Com configuração **ativa**, fazer login como **Professor A** (autor da questão)
- [x] Abrir a questão criada por ele
- [x] Verificar que consegue editar normalmente

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: `button:has-text("Editar")`
- Estado esperado: botão visível
- Fixture: `mixer.blend(Question, created_by=elaborator_user)`

---

### 5.7 Rastreabilidade [Apenas Manual 👁]

#### Cenário 11 — Registro da autoria da edição no histórico

**Ação humana:**
- [x] Com configuração **ativa**, fazer login como **Professor B** (revisor)
- [x] Editar a questão criada pelo **Professor A**
- [x] Salvar as alterações
- [x] Fazer login como **Professor A** (autor)
- [x] Acessar o histórico da questão
- [x] Verificar que o registro indica que a alteração foi feita pelo revisor

**Referência técnica (para automação):**
- URL: `/provas/`
- Seletor: histórico da questão
- Estado esperado: registro com `history_user` = revisor
- Fixture: ver seção 4

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] Verificar que o toggle "**Revisores específicos podem editar questões no período de revisão**" está alinhado com o toggle de coordenadores
- [x] Verificar que o texto de ajuda (help_text) aparece abaixo do toggle
- [x] Verificar que o formulário de configurações mantém o layout existente sem quebras

![ ](../evidencias/toggle.png)

---

## 7. Bugs and Observations (Problemas Encontrados)

> Reservado para documentar bugs encontrados durante a execução dos testes.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> Avaliar com o time de produto se basta a rastreabilidade via `history` ou se será conveniente uma tag/badge "Editada por [Nome do Revisor]" no cabeçalho da questão.

> [!NOTE]
> Confirmar o comportamento quando o revisor está editando e o status do caderno muda automaticamente no meio da edição, encerrando a janela.

> [!NOTE]
> Definir se a coordenação precisa enxergar em algum lugar quais solicitações têm revisores com poder de edição ativo, ou se a configuração global basta.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [ ] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.

🔗 **[Ver Mapeamento de Tela](docs/tests/usability/questions_configutation.md)**

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante os testes:** _(preencher após execução)_
- **Muitos vai-e-vens com o desenvolvedor:** _(preencher após execução)_
- **Como o fluxo de desenvolvimento/QA poderia melhorar:** _(preencher após execução)_

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

---

## Objetivos da Sessão Atual de Teste

1. **Otimização:** Descobrir formas de otimizar ainda mais o Prompt V2.
2. **Entendimento de Fluxo:** Validar se a forma como o plano é estruturado realmente ajuda a IA a compreender com clareza o fluxo da tela testada.
3. **Mapeamento para Automação Futura:** Confirmar se o mapeamento técnico criado (seletores, URLs reais, fixtures) permitiria à IA testar *novas funcionalidades* desta tela no futuro, com total autonomia.
4. **Sugestões de Melhorias:** Registrar ativamente minhas sugestões (como IA) de ajustes ou correções na especificação, no teste ou no próprio prompt durante a nossa interação.

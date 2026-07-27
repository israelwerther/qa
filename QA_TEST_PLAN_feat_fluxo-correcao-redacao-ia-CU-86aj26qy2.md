---
date: "2026-07-27"
feature_area: "Exams / Answers (Redação ENEM AI)"
risk_level: "High"
openspec_quality: 5
---

# QA Test Plan: Fluxo de Correção de Redação IA (ENEM)

## 1. Summary of Changes (Resumo das Alterações)
- **Backend (Integração):** Integração com `corretor-redacao-api` via Celery (fila `celery-priority`) para enviar transcrições de redações e receber sugestões (competências, desvios, feedbacks e notas).
- **Backend (Modelos e APIs):** Novos modelos `EssayAICorrection` e `EssayAISuggestion`. Novos endpoints sob `/respostas/` no app `answers` para gerenciar as sugestões (enfileirar, consultar, aceitar, rejeitar), restritos a redações padrão ENEM e clientes com `has_essay_system`.
- **Frontend (UI do Painel):** Novo painel lateral "Lize AI" na tela de correção de redação (aba Corrigir) com accordions aninhados para visualizar, aceitar ou rejeitar sugestões da IA (inclusive "Aceitar tudo"). O painel só é exibido se a redação for do tipo ENEM e a funcionalidade estiver ativada.
- **Frontend (Digitalização):** Toggle entre "Texto digitalizado" e "Texto original". O modo digitalizado exibe a transcrição com highlights dos desvios sugeridos, vinculados aos itens do painel (com tooltip).

## 2. Scope Boundaries (Diferenças de Escopo)
- **IN SCOPE:** 
  - Geração e exibição de sugestões da IA na tela de correção para redações ENEM.
  - Testes dos toggles de texto digitalizado/original e highlights na transcrição.
  - Ações de aceitar/rejeitar sugestões individualmente e em lote.
  - Sobrescrita das notas por competência no FileAnswer.
  - Permissões de tenant (exige `has_essay_system`).
- **OUT OF SCOPE:** 
  - Correção de redações de outros modelos que não sejam ENEM.
  - OCR/Correção IA nativos do Lize (apenas consumo da API externa `corretor-redacao-api` ocorre).
  - Mapeamento de spans do texto para bounding boxes no Annotorious.
  - Correção discursiva genérica.

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)
| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Correção de Redação | Instrumentos Avaliativos [verificar] -> Redações -> Corrigir | `/exams/<uuid>/redacoes/correcao/` | `exam_answers_correction` |

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)
- **Execução:** 
  ```bash
  ./scripts/tests/run-tests.sh fiscallizeon/answers/tests/ --no-tty
  ```
- **Persona:** Coordenador ou Professor vinculado à prova da redação.
- **Fixture / Setup (Mixer):**
  Para acessar a UI de testes de forma consistente, a IA pode usar o seguinte setup com `mixer`:
  ```python
  from fiscallizeon.core.tests.utils import login_user
  from fiscallizeon.exams.models import Exam
  from fiscallizeon.answers.models import FileAnswer, QuestionAnswer
  
  # Ensure the client has has_essay_system=True
  client_obj = mixer.blend('core.Client', has_essay_system=True)
  
  # Setup Teacher
  teacher = mixer.blend('users.User', role='teacher', client=client_obj)
  login_user(self.client, teacher)
  
  # Create an Exam and Answer (ENEM Template)
  exam = mixer.blend(Exam, client=client_obj)
  # Ensure template is ENEM for the related Question/QuestionAnswer
  # ...
  # Need to check exactly how the `is_enem_essay_question` checks for ENEM template.
  ```

## 5. Execution Test Script (Roteiro de Testes com Checkboxes)

### Configuração e Permissões
- [ ] **Ação humana:** Fazer login com um usuário pertencente a um cliente **sem** `has_essay_system` e acessar uma tela de correção de redação ENEM.
  - **Referência técnica:** Acessar URL `/exams/<uuid>/redacoes/correcao/`
  - **Resultado esperado:** O painel "Lize AI" **não** deve estar visível no sidebar. `[Automatizável ✅]`

- [ ] **Ação humana:** Fazer login com um usuário pertencente a um cliente **com** `has_essay_system` e acessar uma redação **NÃO ENEM**.
  - **Referência técnica:** Acessar URL `/exams/<uuid>/redacoes/correcao/`
  - **Resultado esperado:** O painel "Lize AI" **não** deve estar visível no sidebar. `[Automatizável ✅]`

### Fluxo de Exibição e Geração (Redações ENEM + has_essay_system)
- [ ] **Ação humana:** Acessar a tela de correção de uma redação ENEM.
  - **Referência técnica:** Acessar URL `/exams/<uuid>/redacoes/correcao/` com client que tenha `has_essay_system=True`.
  - **Resultado esperado:** Ao entrar na tela, o painel Lize AI deve disparar a geração (estado loading/pendente) e exibir o badge de pendências. `[Automatizável ✅]`

- [ ] **Ação humana:** Expandir o Accordion "Lize AI" na sidebar.
  - **Referência técnica:** Clicar no botão que expande o painel Lize AI.
  - **Resultado esperado:** Deve exibir os accordions aninhados: Desvios sugeridos, Feedbacks por competência, Notas sugeridas, Rúbricas. Os itens devem estar com o status de sugeridos (ícones de ✓ e × visíveis). `[Apenas Manual 👁]`

### Texto Digitalizado e Highlights
- [ ] **Ação humana:** No painel central, alternar entre "Texto original" e "Texto digitalizado".
  - **Referência técnica:** Clicar no toggle de texto digitalizado.
  - **Resultado esperado:** A transcrição é exibida. Os highlights (tracejado laranja) representam os desvios. `[Apenas Manual 👁]`

- [ ] **Ação humana:** Passar o mouse sobre um texto destacado (highlight) no texto digitalizado.
  - **Referência técnica:** Hover no span do highlight correspondente ao desvio.
  - **Resultado esperado:** Um tooltip "Lize AI — {rótulo}" deve ser exibido. `[Apenas Manual 👁]`

### Aceite e Rejeição de Sugestões
- [ ] **Ação humana:** Clicar no ícone de "×" (Rejeitar) de uma sugestão de desvio no painel Lize AI.
  - **Referência técnica:** Clicar no botão rejeitar associado a uma sugestão (`EssayAISuggestion`).
  - **Resultado esperado:** A sugestão é marcada como rejeitada. O highlight correspondente no texto digitalizado **desaparece**. `[Automatizável ✅]`

- [ ] **Ação humana:** Clicar no ícone de "✓" (Aceitar) de uma sugestão de nota para uma competência.
  - **Referência técnica:** Clicar no botão aceitar da sugestão de nota. POST para API em `/respostas/.../accept`.
  - **Resultado esperado:** A sugestão é aceita. O sistema sobrescreve a nota daquela competência na correção e reflete na tela. `[Automatizável ✅]`

- [ ] **Ação humana:** Clicar no botão "Aceitar tudo" no painel Lize AI.
  - **Referência técnica:** Clicar no botão "Aceitar tudo". POST para API em `/respostas/.../accept-all`.
  - **Resultado esperado:** Todas as sugestões pendentes mudam para aceitas e são aplicadas na correção do arquivo (FileAnswer). O painel atualiza a visualização, reduzindo o badge de pendências para 0. `[Automatizável ✅]`

## 6. Visual and Layout Validation (Validação Visual e de Layout)
- [ ] O painel Lize AI corresponde fielmente ao mockup `references/images/lize-ai-panel-reference.png`. (Accordions, badge, tipografia).
- [ ] O comportamento e layout do texto digitalizado com highlights tracejados na cor laranja correspondem ao mockup `references/images/digitalized-text-highlights-reference.png`.

## 7. Bugs and Observations (Problemas Encontrados)
> [!NOTE]
> Nenhum bug reportado nesta fase inicial do plano. Use esta seção para adicionar bugs encontrados durante a execução. (Lembre-se da regra de formatar com Título, Root Cause, Expected Behavior citando fonte e Workaround).

## 8. Future Improvements & Tech Debt (Melhorias Futuras)
> [!NOTE]
> Mapeamento de spans do texto digitalizado para as bounding boxes na imagem do Annotorious será uma melhoria futura.
> Mapear suporte para outros modelos de prova discursiva/redação além do ENEM no Lize AI.

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)
🔗 **[Ver Mapeamento de Tela](../../../docs/tests/usability/exam_essay_correction.md)**
(Nota: Caso este arquivo não exista, crie-o na primeira execução registrando seletores reais como botões de toggle e botões de aceitar/rejeitar sugestão).

## 9. QA Retrospective (Retrospectiva de QA)
- **Principal gargalo:** (A ser preenchido após execução)
- **Integração:** (A ser preenchido após execução)
- **Melhorias de Processo:** (A ser preenchido após execução)

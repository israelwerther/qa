---
date: "2026-07-27"
feature_area: "Exams / Answers (Redação ENEM AI)"
risk_level: "High"
openspec_quality: 5
---

# QA Test Plan: Fluxo de Correção de Redação IA (ENEM)

## 0. Metadata (Metadados de QA)
| Field | Value |
|-------|-------|
| Date | 2026-07-27 |
| Feature Area | Exams / Answers (Redação ENEM AI) |
| Risk Level | High |
| OpenSpec Quality | 5 |

## 1. Summary of Changes (Resumo das Alterações)
- **Integração do Pipeline de IA:** A IA processa o texto e identifica falhas (gramaticais e estruturais) que agora são expostas na lista `ai_correction_data` (campo JSON) do `FileAnswer`.
- **Etapa de Revisão Humana:** Adicionada uma nova etapa de revisão na UI de correção (Painel Lize AI). O professor pode visualizar os desvios organizados por tipo e possui 3 ações: **Aceitar, Editar ou Rejeitar** cada desvio antes que eles afetem a nota.
- **Backend (Integração Celery):** Integração com `corretor-redacao-api` via fila `celery-priority` para enviar transcrições e receber sugestões.
- **Cálculo da Nota:** Ao finalizar a correção, o sistema soma o impacto dos desvios *aceitos* ou *editados* ao cálculo da nota, ignorando os rejeitados ou pendentes.
- **Texto Digitalizado:** Modo de leitura da transcrição em HTML com highlights visuais (laranja) para os trechos que possuem desvios.

## 2. Scope Boundaries (Diferenças de Escopo)
- **IN SCOPE:** 
  - Exibição de sugestões da IA na tela de correção para redações ENEM, condicionadas pela flag `has_essay_system` do cliente e template `Competências ENEM` da questão.
  - Fluxo de Aceite, Edição e Rejeição de desvios pelo professor e cálculo do impacto na nota.
  - Toggles de texto digitalizado/original e renderização de highlights com tooltips.
  - Regressões de navegação, carregamento de imagens no OpenSeadragon e troca de alunos.
- **OUT OF SCOPE:** 
  - Correção automática sem revisão do professor (a IA nunca aplica desvios diretamente à nota sem controle humano).
  - Novos tipos de desvios além de `falha_gramatical` e `falha_estrutural` neste ciclo.
  - Correção de questões discursivas textuais (`TextualAnswer`), o escopo é apenas redações (`FileAnswer`).
  - Mapeamento de spans do texto digitalizado para bounding boxes no Annotorious (imagem).

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)
| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Listagem de Redações | Turmas [verificar] -> Filtrar Turma | `/provas/<exam_id>/redacoes/` | `exam_answers_list` |
| Correção de Redação | Clicar em um aluno na lista | `/exams/<uuid>/redacoes/correcao/` | `exam_answers_correction` |

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)
- **Execução:** 
  ```bash
  ./scripts/tests/run-tests.sh fiscallizeon/answers/tests/ --no-tty
  ```
- **Persona:** Coordenador ou Professor.
- **Mixer Setup (Setup de Dados Mínimos):**
  Para acessar a UI sem erros, precisamos de Caderno ENEM, Cliente com permissão e Turma com alunos:
  ```python
  from fiscallizeon.core.tests.utils import login_user
  from fiscallizeon.exams.models import Exam
  from fiscallizeon.answers.models import FileAnswer
  
  # Setup Cliente e Professor
  client_obj = mixer.blend('core.Client', has_essay_system=True)
  teacher = mixer.blend('users.User', role='teacher', client=client_obj)
  login_user(self.client, teacher)
  
  # Setup Exame ENEM com template
  # Nota: A questão deve ter is_essay=True e text_correction="Competências ENEM"
  exam = mixer.blend(Exam, client=client_obj)
  ```

## 5. Execution Test Script (Roteiro de Testes com Checkboxes)

### Bloco A — Regressões de navegação (C01–C02, C20)
- [ ] **Ação humana:** Selecionar uma turma e filtrar (C01).
  - **Referência técnica:** Acessar `/provas/<exam_id>/redacoes/` e abrir o Console do browser.
  - **Resultado esperado:** Cards dos alunos aparecem sem tela em branco. O Console não deve apresentar `TypeError: Cannot read properties of undefined (reading 'criterion')`. A pontuação exibida nos cards não deve quebrar o render, mesmo com anotações incompletas. `[Automatizável ✅]`

- [ ] **Ação humana:** Clicar em um aluno da listagem para iniciar a correção (C02).
  - **Referência técnica:** Observar o painel central ao carregar a página `/exams/<uuid>/redacoes/correcao/`.
  - **Resultado esperado:** Imagem da redação carrega no OpenSeadragon (não fica travada no loading). O Console não deve apresentar `Cannot read properties of null (reading 'appendChild')`. Toolbar de zoom/home disponível no modo Texto original. `[Automatizável ✅]`

- [ ] **Ação humana:** Com correção aberta, avançar para o próximo aluno (C20).
  - **Referência técnica:** Clicar na seta de "Próximo" na navegação do corretor.
  - **Resultado esperado:** A imagem e as anotações do aluno anterior **não "vazam"** para o próximo. O Painel Lize AI reinicia para o novo FileAnswer. Sem erros no Console ao trocar rapidamente. `[Automatizável ✅]`

### Bloco B — Visibilidade e Disparo (C03–C08, C21)
- [ ] **Ação humana:** Fazer login com um usuário pertencente a um cliente **sem** `has_essay_system` e tentar acessar o fluxo (C21).
  - **Referência técnica:** Acessar URL `/exams/<uuid>/redacoes/correcao/`.
  - **Resultado esperado:** Acesso ao módulo de redação deve ser bloqueado (redirect ou aviso “Cliente não possui este módulo”). O painel "Lize AI" **não** deve estar visível/operacional. `[Automatizável ✅]`

- [ ] **Ação humana:** Acessar uma redação **NÃO ENEM** em cliente permitido (C04).
  - **Referência técnica:** Acessar correção de questão cujo `text_correction` não é "Competências ENEM".
  - **Resultado esperado:** O Accordion Lize AI não aparece. O toggle de texto digitalizado também não aparece. `[Automatizável ✅]`

- [ ] **Ação humana:** Acessar a tela de correção de uma redação ENEM virgem (C05).
  - **Referência técnica:** Abrir aluno sem `EssayAICorrection` prévia.
  - **Resultado esperado:** Ao entrar na tela, o painel Lize AI dispara a geração (estado de loading: "Gerando sugestões…"). Logo após o Celery processar o job, o status muda para `ready` e popula as seções. `[Automatizável ✅]`

- [ ] **Ação humana:** Recarregar (F5) a mesma página de correção após o processamento (C06).
  - **Referência técnica:** Recarregar a página com painel em estado `ready`.
  - **Resultado esperado:** Não cria segundo job desnecessário. O painel carrega diretamente com as sugestões, sem ficar preso em `ready` vazio. Transcrição disponível. `[Automatizável ✅]`

- [ ] **Ação humana:** Interagir enquanto o job processa (C07).
  - **Referência técnica:** Abrir a correção (ideal simular rede lenta).
  - **Resultado esperado:** Mensagem de processamento com spinner é exibida. O polling atualiza até `ready` ou `failed` sem precisar dar F5. `[Automatizável ✅]`

- [ ] **Ação humana:** Simular falha na API ou conexão e usar retry (C08).
  - **Referência técnica:** Usar correção com status `failed` no Admin ou bloquear rede.
  - **Resultado esperado:** A UI mostra mensagem de erro legível. O botão "Tentar novamente" reenfileira o fluxo e, com a infra restabelecida, o status chega em `ready`. `[Apenas Manual 👁]`

### Bloco C — Estrutura do Painel (C09–C10)
- [ ] **Ação humana:** Verificar as seções do painel após processamento (C09).
  - **Referência técnica:** Observar os accordions filhos do Lize AI.
  - **Resultado esperado:** O Badge do header reflete o total de pendências. Existem as seções: Desvios sugeridos, Feedbacks, Notas sugeridas, Rúbricas. Cada seção com itens pendentes mostra seu próprio badge coerente. Se vazia, mostra "Nenhum item nesta seção" sem quebrar JS. `[Automatizável ✅]`

- [ ] **Ação humana:** Expandir e recolher o painel e suas seções (C10).
  - **Referência técnica:** Clicar nos cabeçalhos dos accordions.
  - **Resultado esperado:** Painel expande e recolhe sem quebrar layout. Os itens exibem título, detalhe e os ícones sutis de ✓ e × à direita. `[Apenas Manual 👁]`

### Bloco D — Aceite e Rejeição (C11–C16)
- [ ] **Ação humana:** Clicar no ícone de "×" (Rejeitar) de uma sugestão de desvio (C12).
  - **Referência técnica:** Rejeitar desvio com highlight visível na transcrição.
  - **Resultado esperado:** Status do item muda para "Recusada". O highlight correspondente **some** no texto digitalizado. O badge decrementa. A nota não é afetada. `[Automatizável ✅]`

- [ ] **Ação humana:** Clicar no ícone de "✓" (Aceitar) de um desvio gramatical/estrutural (C11).
  - **Referência técnica:** Aceitar desvio com highlight.
  - **Resultado esperado:** Status vira "Aceita". Badge decrementa. Highlight no digitalizado permanece com estilo visual de aceito. Não deve quebrar o Annotorious no modo original (desvios da IA não devem gravar geometria na imagem). `[Automatizável ✅]`

- [ ] **Ação humana:** Editar a descrição de um desvio antes de aceitar.
  - **Referência técnica:** Usar o fluxo de edição de desvio do Lize AI.
  - **Resultado esperado:** O texto editado pelo professor é persistido e entra no cálculo. `[Automatizável ✅]`

- [ ] **Ação humana:** Aceitar sugestão de nota que conflita com anotação manual (C13).
  - **Referência técnica:** O professor cria uma dedução manual para C2 na sidebar. Depois aceita a nota da IA para a mesma competência.
  - **Resultado esperado:** A nota da competência passa a refletir a sugestão aceita (sobrescrevendo as deduções manuais anteriores da mesma competência). Anotações manuais em *outras* competências continuam desenhadas e intactas. Console limpo de erros do Annotorious (`can't access property "type"`). `[Automatizável ✅]`

- [ ] **Ação humana:** Aceitar sugestão de Feedback (C14).
  - **Referência técnica:** Clicar em aceitar feedback para uma competência que já possui texto do professor.
  - **Resultado esperado:** O texto existente não é apagado. O comentário sugerido recebe um *append* (é adicionado ao final) com o prefixo `[Lize AI — Cx]`. Status vira Aceita. `[Automatizável ✅]`

- [ ] **Ação humana:** Clicar no botão "Aceitar Tudo" (C16).
  - **Referência técnica:** Clicar em Aceitar Tudo com várias pendências.
  - **Resultado esperado:** Todas as pendentes passam para "aceitas" ou ocorre falha atômica com mensagem clara (sem estado inconsistente). Badge zera. Notas/feedbacks refletem os aceites. Sem erros no Annotorious. `[Automatizável ✅]`

### Bloco E — Texto Digitalizado e Highlights (C17–C19)
- [ ] **Ação humana:** Alternar entre "Texto digitalizado" e "Texto original" (C17).
  - **Referência técnica:** Usar o toggle no painel central com transcrição disponível.
  - **Resultado esperado:** Modo Digitalizado mostra texto HTML e oculta o viewer da imagem. Modo Original volta a imagem do Annotorious com a toolbar. A alternância não destrói o estado das sugestões no painel. `[Apenas Manual 👁]`

- [ ] **Ação humana:** Inspecionar highlights na transcrição (C18).
  - **Referência técnica:** Localizar trechos grifados de desvios. Hover para tooltips.
  - **Resultado esperado:** Os highlights usam estilo tracejado na cor laranja (não adotam as cores das competências como as demarcações manuais). O tooltip exibe `Lize AI — {rótulo}`. `[Apenas Manual 👁]`

- [ ] **Ação humana:** Clicar em Texto Digitalizado antes de haver transcrição (C19).
  - **Referência técnica:** Abrir painel em `loading` ou que falhou sem `transcription`.
  - **Resultado esperado:** Exibe mensagem “Aguardando transcrição da Lize AI…” ou mantém o toggle desabilitado por enquanto. `[Apenas Manual 👁]`

### Bloco F — Persistência no Backend (C22)
- [ ] **Ação humana:** Verificar o reflexo no banco/admin após um processo bem-sucedido (C22).
  - **Referência técnica:** Inspecionar o model `EssayAICorrection` via Django Admin para a redação testada.
  - **Resultado esperado:** `status=ready` e `transcription` preenchida. Metadados de uso da API presentes no campo `metadata`. Itens em `EssayAISuggestion` criados com status e tipo (`kind`, `competency`) coerentes. `[Automatizável ✅]`

## 6. Visual and Layout Validation (Validação Visual e de Layout)
- [ ] O painel Lize AI corresponde fielmente aos mockups de design. (Accordions, badge, tipografia).
- [ ] A etapa extra de revisão condicional (que lista falhas separadas por gramatical e estrutural) aparece visualmente correta.
- [ ] O comportamento do texto digitalizado com highlights tracejados em laranja foi verificado.

## 7. Bugs and Observations (Problemas Encontrados)
> [!WARNING]
> Risco: A estrutura de `ai_correction_data` precisa estar alinhada com o contrato. O JSON deve possuir o `type` (falha_gramatical ou falha_estrutural) para separar visualmente a revisão. 
> 
> [!NOTE]
> Nenhum bug reportado nesta fase inicial. Ao encontrar, descreva com (1) Título, (2) Root Cause, (3) Expected Behavior citado, (4) Workaround.

## 8. Future Improvements & Tech Debt (Melhorias Futuras)
> [!NOTE]
> Mapeamento de spans do texto digitalizado para as bounding boxes na imagem nativa do Annotorious será feito futuramente.
> 
> [!NOTE]
> Avaliar comportamento de pendências se o professor salvar a correção sem terminar a revisão dos desvios.

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)
🔗 **[Ver Mapeamento de Tela](../../../docs/tests/usability/exam_essay_correction.md)**
*(Criar/atualizar este arquivo na primeira execução registrando seletores reais como botões de toggle e aceitar/rejeitar).*

## 9. QA Retrospective (Retrospectiva de QA)
- **Principal gargalo:** (A ser preenchido após execução)
- **Integração:** (A ser preenchido após execução)
- **Melhorias de Processo:** (A ser preenchido após execução)

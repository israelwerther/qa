# Proposta: Gerador de Cadernos e Questões para Testes de QA

## Why
A validação manual e automatizada de novos fluxos de aplicações (como Aplicações Híbridas, randomização e diagramação) é extremamente repetitiva e consome tempo significativo dos testadores de QA. Atualmente, para cada cenário (ex.: "caderno com questões discursivas e redação", ou "caderno com randomização de alternativas ativada"), o QA precisa navegar pelo banco de dados ou criar manualmente cadernos via interface web, configurando disciplinas, questões e opções uma a uma.

Este gerador automatiza a instanciação de massas de testes sob medida diretamente no ambiente local, gerando cadernos (`Exam`) e questões (`Question`) completas e válidas em menos de 2 segundos.

## What Changes
- **Script Gerador (`.ai_qa_acervo/scripts/create_test_exam.py`):**
  - Permite configurar por CLI ou modo interativo a quantidade exata de questões por tipo:
    - Questões objetivas (`Question.CHOICE`) com 5 alternativas (A, B, C, D, E) e gabarito associado.
    - Questões discursivas (`Question.TEXTUAL`, `is_essay=False`).
    - Propostas de redação (`Question.TEXTUAL`, `is_essay=True`, 30 linhas).
  - Configura parâmetros de embaralhamento (`random_questions=True`, `random_alternatives=True`).
  - Vincula automaticamente o caderno e as questões às coordenações do cliente do usuário ativo (`fiscallize_geral` ou personas do Cloud Lab), tornando-o instantaneamente selecionável no campo "Instrumento avaliativo" de `/aplicacoes/cadastrar/`.
- **Atalho Executável (`.ai_qa_acervo/scripts/create-exam.sh`):**
  - Wrapper Shell para execução rápida sem necessidade de especificar o caminho do Python da `venv`.

## Capabilities

### New Capabilities
- `test-exam-questions-generator`: Geração parametrizada de cadernos e questões no banco de dados para aceleração de testes de QA e automação.

### Modified Capabilities
- Nenhuma capacidade pré-existente de produção é alterada; trata-se de ferramenta interna do acervo de QA.

## Impact
- **Arquivos:** Adicionados em `.ai_qa_acervo/scripts/`.
- **Banco de Dados:** Cria registros válidos de `Exam`, `Question`, `QuestionOption` e `ExamQuestion`.
- **Produção:** Sem impacto em código de produção ou rotas expostas a clientes.

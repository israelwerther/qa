---
description: Cria cadernos de prova e questões de teste sob medida para validações de QA a partir de texto livre
---

# Workflow: Criar Caderno de Teste para QA (`/qa-create-test-exam`)

Este comando permite gerar cadernos (`Exam`) completos, com questões (`Question`), alternativas (`QuestionOption`), amarrações pedagógicas (`ExamTeacherSubject`) e configuração de diagramação (`ExamPrintConfig`) diretamente no banco de dados, interpretando pedidos em linguagem natural.

---

**Input**: O texto passado após `/qa-create-test-exam` descreve o caderno desejado.  
*Exemplos:*
- `/qa-create-test-exam 10 questões objetivas com alternativas embaralhadas`
- `/qa-create-test-exam 5 objetivas, 2 discursivas e 1 redação para teste híbrido`
- `/qa-create-test-exam Simulado PAS com 15 objetivas e 3 discursivas`
- `/qa-create-test-exam` (sem texto — o assistente infere um padrão equilibrado ou pergunta ao usuário)

---

## Passos de Execução para a IA

### 1. Interpretar a Solicitação do Usuário
Analise o texto fornecido pelo usuário e extraia os seguintes parâmetros:
- **Quantidade de Objetivas (`-obj`)**: Número de questões de múltipla escolha A–E (se não especificado e nenhuma outra quantidade for informada, use `5`).
- **Quantidade de Discursivas (`-disc`)**: Número de questões discursivas padrão (default `0`).
- **Quantidade de Redações (`-ess`)**: Número de propostas de redação (default `0`).
- **Disciplina (`-s` / `--subject`)**: Nome ou parte do nome da matéria (ex.: "Matemática", "História").
- **Professor (`-t` / `--teacher`)**: Nome ou login do professor (ex.: "Adriano", "barbara.brito"). Se omitido, o script prioriza automaticamente um professor com conta **ativa** no cliente e exibe seu login. Se a disciplina não tiver professores ativos, o script auto-vincula um professor ativo do cliente para permitir o acesso do QA.
- **Cliente (`-c` / `--client`)**: Nome do cliente específico (ex.: "Rede Decisão"). **Se não especificado, o script detecta automaticamente o cliente da sessão ativa logada no navegador (localhost / runserver)**.
- **Embaralhar Questões (`-rq`)**: `True` se o usuário mencionar "embaralhar questões", "questões aleatórias", "ordem diferente", etc.
- **Embaralhar Alternativas (`-ra`)**: `True` se o usuário mencionar "embaralhar alternativas", "alternativas aleatórias", etc.
- **Nome do Caderno (`-n`)**: Se o usuário fornecer um nome específico (ex.: "Simulado PAS"), use-o. Caso contrário, deixe omitido para geração automática com timestamp.
- **Usuário (`-u`)**: Se omitido, o script detecta o usuário da sessão ativa no localhost (ou usa `fiscallize_geral` como fallback).

### 2. Executar o Script de Criação
Construa o comando chamando o script do acervo com os argumentos interpretados:

```bash
./venv/bin/python .ai_qa_acervo/scripts/create_test_exam.py [FLAGS]
```

*Exemplo:*
```bash
./venv/bin/python .ai_qa_acervo/scripts/create_test_exam.py -n "[QA] Simulado Híbrido" -obj 5 -disc 2 -ess 1 -rq -ra
```

Execute o comando usando `run_command`.

### 3. Apresentar o Resumo Formatado ao Usuário
Capture a saída da execução e informe ao usuário:
1. ✅ **Confirmação de Criação** com o **Nome Exato** e **ID do Exam**.
2. 📋 **Composição da Prova**: total de questões, quebra por tipo (objetivas, discursivas, redação) e status de randomização.
3. 🎯 **Como Utilizar na Interface**:
   - URL da tela (ex.: `http://127.0.0.1:8000/aplicacoes/cadastrar/?category=hibrid` ou `/provas/<id>/v2/imprimir/`).
   - Termo exato para buscar no autocomplete de "Instrumento avaliativo".

---
description: Cria aplicações de teste sob medida para validações de QA a partir de texto livre (vincula caderno existente ou encadeia qa-create-exam)
---

# Workflow: Criar Aplicação de Teste para QA (`/qa-create-application`)

Este comando cria aplicações (`Application`) prontas para realização de prova imediata por alunos e fiscais, com turma e alunos associados (senhas `123456`), interpretando pedidos em linguagem natural.

O comando observa duas regras fundamentais de execução:
1. **Caderno Existente**: Se o usuário mencionar um caderno existente (por nome ou ID), a automação busca e vincula esse caderno à aplicação.
2. **Encadear Criação de Caderno (`qa-create-exam`)**: Se o usuário pedir para criar um caderno para a aplicação (ou especificar número/tipo de questões sem citar caderno existente), o comando **encadeia** a geração de um novo caderno completo com suas questões antes de criar a aplicação.

---

**Input**: O texto passado após `/qa-create-application` descreve a aplicação e o caderno desejado.  
*Exemplos:*
- `/qa-create-application usando o caderno "Simulado PAS"` (Usa caderno existente)
- `/qa-create-application criando um caderno com 10 questões objetivas e 2 discursivas` (Encadeia criação de caderno)
- `/qa-create-application online com 5 objetivas embaralhadas` (Encadeia criação de caderno)
- `/qa-create-application presencial para a turma 3ª Série A` (Se não citar questões nem caderno existente, gera caderno padrão e vincula à turma)

---

## Passos de Execução para a IA

### 1. Interpretar a Solicitação do Usuário

Analise o texto fornecido pelo usuário e extraia os seguintes parâmetros:

#### A. Decisão do Caderno (Existente vs. Encadeamento)
- **Cenário 1 — Caderno Existente (`-e` / `--exam`)**:
  - Se o usuário mencionar "usando o caderno X", "com o caderno Y", "para o exame <UUID>", extraia o nome/ID e passe `-e "<identificador>"`.
- **Cenário 2 — Encadeamento com `qa-create-exam` (`--create-exam`)**:
  - Se o usuário disser "criando um caderno...", "criar um caderno para aplicação", ou listar formatos/quantidades:
    - `--pas`: Ativar se o usuário pedir **Modelo PAS** (cria caderno PAS com questões Tipos A, B, C e D).
    - `-sum <n>`: Quantidade de questões de **Somatório** (proposições binárias 01, 02, 04, 08...).
    - `-obj <n>`: Quantidade de questões objetivas (default 5 se encadear padrão).
    - `-disc <n>`: Quantidade de questões discursivas (default 0).
    - `-ess <n>`: Quantidade de redações (default 0).
    - `-rq`: Se pediu embaralhar questões.
    - `-ra`: Se pediu embaralhar alternativas.
    - `-en "<nome>"`: Nome do caderno se especificado.
    - `-s "<disciplina>"`: Disciplina se especificada.
    - `-t "<professor>"`: Professor se especificado.

#### B. Aplicação Respondida (`--answered`)
- **Aplicação Respondida (`--answered`)**:
  - Se o usuário pedir uma aplicação "respondida", "com respostas", "com alunos que fizeram a prova", passe `--answered`.
  - O script simula respostas completas para os alunos, preenche datas de término da prova no `ApplicationStudent` e **gera trocas de alternativas para permitir validar a auditoria de histórico de respostas**!

#### C. Modalidade da Aplicação (`-cat` / `--category`)
- `online`: Padrão. Aplicação online para realização via web/app.
- `presential`: Aplicação presencial (cartão resposta / folha OMR).
- `homework`: Lista de exercícios / lição de casa.

#### D. Turma e Alunos (Sempre Existentes)
- **Turma (`-cl` / `--class-name`)**: *(Opcional)* Nome ou UUID da turma existente (ex.: "F9MA", "M1MA", "3º Ano B"). Se omitido, o script busca automaticamente uma turma do cliente que já possua alunos matriculados.
- **Quantidade de Alunos (`-sc` / `--students-count`)**: *(Opcional)* Quantidade de alunos a vincular (ex.: `3`, `5`, `10`). **Se omitido, vincula todos os alunos existentes da turma**.
- **Senha dos Alunos**: O script garante que os alunos vinculados fiquem com a senha `123456` para login direto no QA.

#### E. Cliente
- **Cliente (`-c` / `--client`)**: Nome do cliente (ex.: "Rede Decisão"). Se omitido, o script detecta automaticamente o cliente da sessão ativa logada no navegador local.

---

### 2. Executar o Script de Criação

Construa o comando chamando o script wrapper ou Python com os argumentos interpretados:

```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_application.py [FLAGS]
```
*(Ou alternativamente: `./.ai_qa_acervo/scripts/generators/create-application.sh [FLAGS]`)*

#### Exemplos de Execução:

**Exemplo 1 (Caderno Existente com Turma e Alunos Específicos):**
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_application.py -e "Simulado PAS" -cl "F9MA" -sc 5 -cat online
```

**Exemplo 2 (Modelo PAS encadeado e 100% Respondido para teste de correção e histórico):**
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_application.py --pas --answered -sc 5
```

**Exemplo 3 (Encadeando criação de caderno com Somatório e Discursivas):**
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_application.py --create-exam -obj 5 -sum 3 -disc 2 -cl "M1MA" --answered
```

**Exemplo 4 (Criação rápida padrão — tudo automático):**
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_application.py --create-exam -obj 5
```

Execute o comando usando a ferramenta `run_command`.

---

### 3. Apresentar o Resumo Formatado ao Usuário

Capture a saída da execução e informe ao usuário:
1. ✅ **Status da Aplicação**: Modalidade (Online / Presencial / Lista), ID e confirmação de que está **Ativa para realização imediata**.
2. 📖 **Caderno Vinculado**: Nome do caderno, total de questões e se foi reutilizado ou criado sob medida no fluxo encadeado.
3. 🏫 **Turma e Alunos de Teste**: Nome da turma e credenciais (login/email e senha padrão `123456`) para fazer login e realizar a prova agora.
4. 🔗 **Links Diretos**:
   - URL do app do aluno para realizar a prova ou tela de correção (`http://localhost:8000/...`).

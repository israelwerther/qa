---
description: Diagnostica e limpa colunas residuais de banco de dados (Schema Drift) com validação de segurança anti-perda de dados
---

# Workflow: Limpeza Segura de Coluna Residual (`/qa-limpar-coluna-residual`)

Este comando resolve erros causados por **Schema Drift** no PostgreSQL local — quando migrações de outras branches deixaram colunas órfãs com restrição `NOT NULL` que quebram a branch atual.

Possui **trava de segurança obrigatória**: se a coluna pertencer aos modelos da branch atual, a operação é **bloqueada automaticamente** para impedir a perda acidental de dados da tarefa em desenvolvimento.

---

## 🚀 Como Usar na IDE

### 1. Colando a Mensagem de Erro do Postgres
Basta invocar o comando colando o erro ou traceback recebido:

```bash
/qa-limpar-coluna-residual null value in column "has_pedagogical_automations" of relation "clients_historicalclient" violates not-null constraint
```

Ou informando diretamente o nome da coluna:

```bash
/qa-limpar-coluna-residual --column has_pedagogical_automations
```

---

## 🛡️ Regras de Execução para a IA

1. **Executar em modo Inspeção (Dry-run) Primeiro:**
   ```bash
   ./venv/bin/python .ai_qa_acervo/scripts/drop_residual_column.py "<TEXTO_DO_ERRO_OU_COLUNA>"
   ```

2. **Interpretar a Saída:**
   - 🛑 **Se a ferramenta bloquear (código de saída 2):**  
     A coluna pertence à branch atual! A IA deve alertar o usuário:
     *"A coluna `<coluna>` faz parte do código da sua branch. O erro é de validação no formulário/view e NÃO deve ser excluída."*
   - 🟢 **Se a ferramenta confirmar o resíduo:**  
     A coluna não existe no código desta branch. A IA deve apresentar as tabelas afetadas e os comandos SQL correspondentes gerados pela ferramenta.

3. **Confirmação do Usuário para Execução:**
   - A IA **NUNCA** aplica a flag `--execute` por conta própria sem a autorização explícita do desenvolvedor.
   - Quando o usuário confirmar (ex.: *"pode executar"*, *"aplique a limpeza"*), a IA roda:
     ```bash
     ./venv/bin/python .ai_qa_acervo/scripts/drop_residual_column.py --column <coluna> --execute
     ```


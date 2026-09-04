---
description: Reseta senhas de usuários para 123456, desativa 2FA/login Google e limpa sessões em ambientes locais de QA
---

# Workflow: Resetar Senhas e Acessos para QA (`/qa-reset-passwords`)

Este comando permite resetar a senha de todos os usuários (ou de um usuário específico) no banco de dados local para `123456`, desativar travas de 2FA/login Google obrigatório nos clientes e limpar sessões, permitindo login imediato do testador no navegador.

---

**Input**: O texto passado após `/qa-reset-passwords` pode conter parâmetros opcionais.  
*Exemplos:*
- `/qa-reset-passwords` (reseta todos os usuários para `123456` e desativa 2FA)
- `/qa-reset-passwords para o usuario cloud.admin@lize.local com a senha abc123`
- `/qa-reset-passwords --password 654321`
- `/qa-reset-passwords -u fiscallize_geral`

---

## Passos de Execução para a IA

### 1. Interpretar a Solicitação do Usuário
Analise o texto fornecido pelo usuário e extraia os seguintes parâmetros:
- **Senha (`-p` / `--password`)**: Se o usuário pedir uma senha específica (ex.: "com a senha admin123"), use-a. Caso contrário, mantenha o padrão `'123456'`.
- **Usuário (`-u` / `--user`)**: Se o usuário especificar um e-mail ou username (ex.: "apenas para o professor Adriano" ou "cloud.admin@lize.local"), passe esse filtro. Se for geral, deixe omitido para resetar todos.
- **Manter 2FA (`--keep-2fa`)**: Apenas se o usuário pedir explicitamente para não mexer em 2FA.
- **Manter Sessões (`--keep-sessions`)**: Apenas se o usuário pedir para não derrubar sessões.

### 2. Executar o Script de Reset
Construa o comando chamando o script de manutenção:

```bash
./venv/bin/python .ai_qa_acervo/scripts/maintenance/reset_passwords.py [FLAGS]
```

*Exemplo:*
```bash
./venv/bin/python .ai_qa_acervo/scripts/maintenance/reset_passwords.py -p 123456
```

Execute o comando usando `run_command`.

### 3. Apresentar o Resumo Formatado ao Usuário
Capture a saída da execução e informe ao usuário:
1. ✅ **Confirmação de Reset**: quantidade de usuários e clientes atualizados.
2. 🔑 **Credenciais Prontas**: informe a senha definida (`123456` ou personalizada) e liste 2 a 3 logins comuns para teste (ex.: `cloud.admin@lize.local`, `fiscallize_geral`, etc.).
3. 🚪 **URL de Login**: link direto para `http://127.0.0.1:8000/conta/entrar/`.

---
description: Validação de conectividade e smoke test do Playwright MCP no Lize Edu
---

# Workflow: Smoke Test do Playwright MCP (`/qa-mcp-health` ou `/qa-mcp`)

Este comando executa um teste rápido de conectividade e validação visual do Playwright no ambiente do Lize Edu. Ele acessa a tela de autenticação (`http://127.0.0.1:8000/conta/entrar/`), valida a renderização e gera uma captura de tela para confirmar que a automação de browser está operando perfeitamente.

---

## Passos de Execução para a IA

### 1. Interpretar a Solicitação do Usuário
- **URL Alvo (`-u` / `--url`)**: Por padrão, utiliza `http://127.0.0.1:8000/conta/entrar/`. Se o usuário passar outra rota (ex.: `/provas/`, `/aplicacoes/`), use a URL indicada.
- **Saída (`-o` / `--output`)**: Salva a evidência em `.ai_qa_acervo/evidencias/mcp_health.png` por padrão.

### 2. Executar o Script de Smoke Test
Execute o script via venv do projeto:

```bash
./venv/bin/python .ai_qa_acervo/scripts/smoke/playwright_smoke.py [FLAGS]
```

*Exemplo:*
```bash
./venv/bin/python .ai_qa_acervo/scripts/smoke/playwright_smoke.py
```

### 3. Apresentar os Resultados ao Usuário
Capture a saída da execução e informe ao usuário:
1. ✅ **Status da Conectividade**: tempo de resposta, título da página capturada e código HTTP (ex.: 200).
2. 🖼️ **Evidência Visual**: link markdown para a imagem gerada em [mcp_health.png](file:///home/israel/Workspace/lizeedu/.ai_qa_acervo/evidencias/mcp_health.png).
3. 🚀 **Próximos Passos**: indicar que o ambiente está apto para validações automatizadas de tela.

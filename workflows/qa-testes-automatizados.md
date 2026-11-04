---
description: Gerencia o servidor de testes automatizados de QA (porta 8001) e executa validações de tela via Playwright
---

# Workflow: Testes Automatizados de QA (`/qa-testes-automatizados`)

Este comando gerencia o ambiente dedicado de **testes automatizados de QA** do Lize Edu (executado de forma isolada na porta `8001` com `DEBUG=True`) e orienta a execução de simulações com Playwright.

O objetivo é garantir que os testes automatizados da IA e as validações visuais ocorram em uma instância de servidor isolada, com logs claros e detalhados, sem conflitar com o ambiente de desenvolvimento principal na porta `8000`.

---

## 🛠️ Comandos de Gestão do Servidor QA (Porta 8001)

O controle do processo é feito pelo script seguro `.ai_qa_acervo/scripts/start-qa-server.sh`:

### 1. Iniciar o Servidor QA
```bash
.ai_qa_acervo/scripts/start-qa-server.sh start
```
- Inicia o Django na porta `8001` com `DEBUG=True` e `ALLOWED_HOSTS="*"` em segundo plano (PID gravado em `.ai_qa_acervo/logs/qa_server_8001.pid`).
- Os logs detalhados do servidor ficam salvos em `.ai_qa_acervo/logs/qa_server_8001.log`.

### 2. Verificar o Status
```bash
.ai_qa_acervo/scripts/start-qa-server.sh status
```
- Informa se o servidor está ativo, seu PID e a URL de acesso (`http://127.0.0.1:8001/`).

### 3. Parar o Servidor QA
```bash
.ai_qa_acervo/scripts/start-qa-server.sh stop
```
- Finaliza o processo de forma limpa, liberando a porta `8001`.

### 4. Reiniciar o Servidor QA
```bash
.ai_qa_acervo/scripts/start-qa-server.sh restart
```

---

## 🧪 Execução de Testes Automatizados (Playwright)

Ao rodar scripts automatizados de QA ou navegar simulando o usuário:

1. **Garantir que o servidor está rodando:**
   ```bash
   .ai_qa_acervo/scripts/start-qa-server.sh start
   ```

2. **Apontar sempre para a porta 8001:**
   - URLs de teste: `http://127.0.0.1:8001/...`
   - O script de smoke do acervo (`.ai_qa_acervo/scripts/smoke/playwright_smoke.py`) já tem a porta `8001` configurada como padrão:
     ```bash
     ./venv/bin/python .ai_qa_acervo/scripts/smoke/playwright_smoke.py
     ```

3. **Diagnóstico de Erros (Anti-Falso-Positivo / Schema Drift):**
   Quando qualquer tela ou requisição falhar (ex.: HTTP 500), inspecione os logs do servidor QA:
   ```bash
   tail -n 50 .ai_qa_acervo/logs/qa_server_8001.log
   ```
   - **Atenção para `IntegrityError` / `NotNullViolation`:** Se o traceback apontar erro de banco em uma coluna específica, verifique se a coluna existe no modelo (`models.py`) da branch atual.
   - **Se NÃO pertencer à branch atual:** Trata-se de contaminação de banco local (Schema Drift de migrações de outras branches).
   - **Regra:** NÃO registre como bug da tarefa. Avise o desenvolvedor no chat informando a tabela/coluna residual e forneça o comando `DROP COLUMN` para ele revisar e executar. NUNCA execute mutações no banco sem autorização.

4. **Desligar após a conclusão dos testes:**
   Finalizada a suite ou a validação de QA, pare o servidor para liberar recursos da máquina:
   ```bash
   .ai_qa_acervo/scripts/start-qa-server.sh stop
   ```


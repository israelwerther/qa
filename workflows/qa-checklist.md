---
description: Gerencia o servidor de Checklist Interativo do Plano de Testes (Porta 8002)
---

# /qa-checklist - Checklist Interativo do Plano de Testes

Inicia ou gerencia a interface web do Checklist Interativo (porta 8002).
Permite visualizar o Plano de Testes da branch atual no navegador e marcar/desmarcar checkboxes com um único clique, sincronizando diretamente com o arquivo `.md` no disco.

## Como Usar

### 1. Iniciar o servidor de Checklist
Para iniciar o servidor independente em background:
```bash
bash .ai_qa_acervo/scripts/start-checklist.sh start
```
Ou use o atalho de tarefas da IDE (`Ctrl+Shift+B` ou `Terminal -> Run Task... -> QA: Iniciar Checklist Interativo`).

### 2. Acessar a Interface Web
Abra o navegador em:
👉 **http://127.0.0.1:8002/**

### 3. Verificar Status
```bash
bash .ai_qa_acervo/scripts/start-checklist.sh status
```

### 4. Parar o servidor
```bash
bash .ai_qa_acervo/scripts/start-checklist.sh stop
```

## Recursos do Checklist Interativo
- **Detecção Automática do Plano**: Identifica o plano de testes `.md` em `.ai_qa_acervo/QA Plans/` baseado no nome da branch git ativa.
- **Sincronização Bidirecional Direta**: Cada clique em um checkbox no navegador atualiza imediatamente o `[x]` ou `[ ]` na linha exata do arquivo `.md`.
- **Barra de Progresso em Tempo Real**: Mostra o percentual e a contagem de itens executados.
- **Isolamento Total**: Roda em processo daemon de usuário desvinculado de sessões de chat de IA.


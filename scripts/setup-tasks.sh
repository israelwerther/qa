#!/usr/bin/env bash
# Script para configurar os atalhos, tasks do VS Code e Slash Commands (/qa-create-test-exam) em qualquer máquina (Notebook/Desktop)
set -e

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VSCODE_DIR="$WORKSPACE_ROOT/.vscode"
TASKS_SOURCE="$(cd "$(dirname "$0")/../vscode" && pwd)/tasks.json"

# 1. Configura tasks.json para inicialização de serviços locais (Ctrl+Shift+B)
mkdir -p "$VSCODE_DIR"
cp "$TASKS_SOURCE" "$VSCODE_DIR/tasks.json"

# 2. Configura slash commands (/qa-create-test-exam) nas IDEs (Antigravity e Cursor)
mkdir -p "$WORKSPACE_ROOT/.agent/workflows"
mkdir -p "$WORKSPACE_ROOT/.cursor/commands"
ln -sf "../../.ai_qa_acervo/workflows/qa-create-test-exam.md" "$WORKSPACE_ROOT/.agent/workflows/qa-create-test-exam.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-create-test-exam.md" "$WORKSPACE_ROOT/.cursor/commands/qa-create-test-exam.md"

# 3. Garante que os links e o acervo fiquem isolados e não sujem o git status do lizeedu
EXCLUDE_FILE="$WORKSPACE_ROOT/.git/info/exclude"
if [ -f "$EXCLUDE_FILE" ]; then
    grep -q "\.ai_qa_acervo/" "$EXCLUDE_FILE" || echo ".ai_qa_acervo/" >> "$EXCLUDE_FILE"
    grep -q "qa\*.md" "$EXCLUDE_FILE" || echo -e ".agent/workflows/qa*.md\n.cursor/commands/qa*.md" >> "$EXCLUDE_FILE"
fi

echo "✅ Tasks do VS Code e Slash Command (/qa-create-test-exam) configurados com sucesso!"
echo "👉 Pressione Ctrl+Shift+B para iniciar todos os serviços."
echo "👉 Digite /qa-create-test-exam no chat da IDE para acionar o gerador de cadernos."

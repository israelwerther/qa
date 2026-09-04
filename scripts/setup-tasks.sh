#!/usr/bin/env bash
# Script para configurar os atalhos e tasks do VS Code em qualquer máquina (Notebook/Desktop)

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VSCODE_DIR="$WORKSPACE_ROOT/.vscode"
TASKS_SOURCE="$(cd "$(dirname "$0")/../vscode" && pwd)/tasks.json"

mkdir -p "$VSCODE_DIR"
cp "$TASKS_SOURCE" "$VSCODE_DIR/tasks.json"

# Configura slash commands na IDE (Antigravity e Cursor)
mkdir -p "$WORKSPACE_ROOT/.agent/workflows"
mkdir -p "$WORKSPACE_ROOT/.cursor/commands"
ln -sf "../../.ai_qa_acervo/workflows/qa-create-exam.md" "$WORKSPACE_ROOT/.agent/workflows/qa.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-create-exam.md" "$WORKSPACE_ROOT/.cursor/commands/qa.md"

# Garante que os links não sujem o git do repositório principal
EXCLUDE_FILE="$WORKSPACE_ROOT/.git/info/exclude"
if [ -f "$EXCLUDE_FILE" ]; then
    grep -q "qa\*.md" "$EXCLUDE_FILE" || echo -e ".agent/workflows/qa*.md\n.cursor/commands/qa*.md" >> "$EXCLUDE_FILE"
fi

echo "✅ Tasks do VS Code e Slash Command (/qa) configurados com sucesso!"
echo "👉 Pressione Ctrl+Shift+B para iniciar todos os serviços."

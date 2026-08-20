#!/usr/bin/env bash
# Script para configurar os atalhos e tasks do VS Code em qualquer máquina (Notebook/Desktop)

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VSCODE_DIR="$WORKSPACE_ROOT/.vscode"
TASKS_SOURCE="$(cd "$(dirname "$0")/../vscode" && pwd)/tasks.json"

mkdir -p "$VSCODE_DIR"
cp "$TASKS_SOURCE" "$VSCODE_DIR/tasks.json"

echo "✅ Tasks do VS Code configuradas com sucesso em $VSCODE_DIR/tasks.json!"
echo "👉 Pressione Ctrl+Shift+B para iniciar todos os serviços."

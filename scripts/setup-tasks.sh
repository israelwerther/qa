#!/usr/bin/env bash
# Script para configurar as tasks do VS Code e Slash Commands (/qa-create-exam, /qa-reset-passwords)
set -e

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VSCODE_DIR="$WORKSPACE_ROOT/.vscode"
TASKS_SOURCE="$(cd "$(dirname "$0")/../vscode" && pwd)/tasks.json"

# 1. Configura tasks.json para inicialização de serviços locais (Ctrl+Shift+B)
mkdir -p "$VSCODE_DIR"
cp "$TASKS_SOURCE" "$VSCODE_DIR/tasks.json"

# 2. Limpa links legados ou obsoletos
rm -f "$WORKSPACE_ROOT/.agent/workflows/qa-create-test-exam.md"
rm -f "$WORKSPACE_ROOT/.cursor/commands/qa-create-test-exam.md"
rm -f "$WORKSPACE_ROOT/.agent/workflows/qa.md"
rm -f "$WORKSPACE_ROOT/.cursor/commands/qa.md"

# 3. Configura slash commands nas IDEs (Antigravity e Cursor)
mkdir -p "$WORKSPACE_ROOT/.agent/workflows"
mkdir -p "$WORKSPACE_ROOT/.cursor/commands"

# /qa-create-plan (Gerador oficial de QA Test Plans)
ln -sf "../../.ai_qa_acervo/workflows/qa-create-plan.md" "$WORKSPACE_ROOT/.agent/workflows/qa-create-plan.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-create-plan.md" "$WORKSPACE_ROOT/.cursor/commands/qa-create-plan.md"

# /qa-create-application (Gerador de aplicações de teste e alunos)
ln -sf "../../.ai_qa_acervo/workflows/qa-create-application.md" "$WORKSPACE_ROOT/.agent/workflows/qa-create-application.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-create-application.md" "$WORKSPACE_ROOT/.cursor/commands/qa-create-application.md"

# /qa-create-exam (Gerador de cadernos e questões)
ln -sf "../../.ai_qa_acervo/workflows/qa-create-exam.md" "$WORKSPACE_ROOT/.agent/workflows/qa-create-exam.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-create-exam.md" "$WORKSPACE_ROOT/.cursor/commands/qa-create-exam.md"

# /qa-reset-passwords (Reset de senhas, 2FA e sessões)
ln -sf "../../.ai_qa_acervo/workflows/qa-reset-passwords.md" "$WORKSPACE_ROOT/.agent/workflows/qa-reset-passwords.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-reset-passwords.md" "$WORKSPACE_ROOT/.cursor/commands/qa-reset-passwords.md"

# /qa-export-pdf (Exportação de plano com evidências para PDF consolidado)
ln -sf "../../.ai_qa_acervo/workflows/qa-export-pdf.md" "$WORKSPACE_ROOT/.agent/workflows/qa-export-pdf.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-export-pdf.md" "$WORKSPACE_ROOT/.cursor/commands/qa-export-pdf.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-export-pdf.md" "$WORKSPACE_ROOT/.agent/workflows/qa-export.md"
ln -sf "../../.ai_qa_acervo/workflows/qa-export-pdf.md" "$WORKSPACE_ROOT/.cursor/commands/qa-export.md"

# 4. Garante que os links e o acervo fiquem isolados e não sujem o git status do lizeedu
EXCLUDE_FILE="$WORKSPACE_ROOT/.git/info/exclude"
if [ -f "$EXCLUDE_FILE" ]; then
    grep -q "\.ai_qa_acervo/" "$EXCLUDE_FILE" || echo ".ai_qa_acervo/" >> "$EXCLUDE_FILE"
    grep -q "qa\*.md" "$EXCLUDE_FILE" || echo -e ".agent/workflows/qa*.md\n.cursor/commands/qa*.md" >> "$EXCLUDE_FILE"
fi

echo "✅ Tasks do VS Code e Slash Commands (/qa-create-plan, /qa-create-application, /qa-create-exam, /qa-reset-passwords, /qa-export-pdf) configurados com sucesso!"
echo "👉 Pressione Ctrl+Shift+B para iniciar todos os serviços."
echo "👉 Comandos disponíveis na IDE:"
echo "   • /qa-create-plan        -> Gera o plano de testes de QA (QA Test Plan) da branch atual"
echo "   • /qa-create-application -> Cria aplicações prontas com turmas/alunos (ou respondidas)"
echo "   • /qa-create-exam        -> Cria cadernos e questões de teste sob medida"
echo "   • /qa-reset-passwords    -> Reseta senhas, 2FA e sessões para login limpo"
echo "   • /qa-export-pdf         -> Exporta o plano para PDF com imagens embutidas (Base64) em exports/"
echo "   (Atalho rápido: /qa-export aciona o /qa-export-pdf)"

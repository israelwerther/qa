#!/usr/bin/env bash
# Script para configurar as tasks do VS Code e Slash Commands (/qa-create-exam, /qa-reset-passwords)
set -e

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
ACERVO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$ACERVO_DIR/.." && pwd)"
VSCODE_DIR="$WORKSPACE_ROOT/.vscode"
TASKS_SOURCE="$ACERVO_DIR/vscode/tasks.json"

# 1. Configura tasks.json para inicialização de serviços locais (Ctrl+Shift+B)
mkdir -p "$VSCODE_DIR"
cp "$TASKS_SOURCE" "$VSCODE_DIR/tasks.json"

# 2. Limpa links legados ou obsoletos (antigos em inglês)
rm -f "$WORKSPACE_ROOT/.agent/workflows/qa-create-*.md"
rm -f "$WORKSPACE_ROOT/.agent/workflows/qa-export*.md"
rm -f "$WORKSPACE_ROOT/.agent/workflows/qa-reset*.md"
rm -f "$WORKSPACE_ROOT/.agent/workflows/qa-answer*.md"
rm -f "$WORKSPACE_ROOT/.agent/workflows/qa.md"

rm -f "$WORKSPACE_ROOT/.agents/workflows/qa-create-*.md"
rm -f "$WORKSPACE_ROOT/.agents/workflows/qa-export*.md"
rm -f "$WORKSPACE_ROOT/.agents/workflows/qa-reset*.md"
rm -f "$WORKSPACE_ROOT/.agents/workflows/qa-answer*.md"
rm -f "$WORKSPACE_ROOT/.agents/workflows/qa.md"

rm -f "$WORKSPACE_ROOT/.cursor/commands/qa-create-*.md"
rm -f "$WORKSPACE_ROOT/.cursor/commands/qa-export*.md"
rm -f "$WORKSPACE_ROOT/.cursor/commands/qa-reset*.md"
rm -f "$WORKSPACE_ROOT/.cursor/commands/qa-answer*.md"
rm -f "$WORKSPACE_ROOT/.cursor/commands/qa.md"

# 3. Configura slash commands nas IDEs (Antigravity e Cursor) em pt-BR
mkdir -p "$WORKSPACE_ROOT/.agent/workflows"
mkdir -p "$WORKSPACE_ROOT/.agents/workflows"
mkdir -p "$WORKSPACE_ROOT/.cursor/commands"

WORKFLOWS_DIR="$WORKSPACE_ROOT/.ai_qa_acervo/workflows"

link_workflow() {
    local src_file="$1"
    local alias_name="$2"
    if [ -f "$WORKFLOWS_DIR/$src_file" ]; then
        ln -sf "../../.ai_qa_acervo/workflows/$src_file" "$WORKSPACE_ROOT/.agent/workflows/$alias_name"
        ln -sf "../../.ai_qa_acervo/workflows/$src_file" "$WORKSPACE_ROOT/.agents/workflows/$alias_name"
        ln -sf "../../.ai_qa_acervo/workflows/$src_file" "$WORKSPACE_ROOT/.cursor/commands/$alias_name"
    fi
}

link_workflow "qa-create-application.md" "qa-criar-aplicacao.md"
link_workflow "qa-create-exam.md"        "qa-criar-caderno.md"
link_workflow "qa-create-plan.md"        "qa-criar-plano.md"
link_workflow "qa-export-pdf.md"         "qa-exportar-plano.md"
link_workflow "qa-reset-passwords.md"    "qa-resetar-senhas.md"
link_workflow "qa-answer-omr.md"         "qa-responder-gabarito.md"

# 4. Garante que os links e o acervo fiquem isolados e não sujem o git status do lizeedu
EXCLUDE_FILE="$WORKSPACE_ROOT/.git/info/exclude"
if [ -f "$EXCLUDE_FILE" ]; then
    grep -q "\.ai_qa_acervo/" "$EXCLUDE_FILE" || echo ".ai_qa_acervo/" >> "$EXCLUDE_FILE"
    grep -q "\.agent/workflows/qa\*" "$EXCLUDE_FILE" || echo ".agent/workflows/qa*.md" >> "$EXCLUDE_FILE"
    grep -q "\.agents/workflows/qa\*" "$EXCLUDE_FILE" || echo ".agents/workflows/qa*.md" >> "$EXCLUDE_FILE"
    grep -q "\.cursor/commands/qa\*" "$EXCLUDE_FILE" || echo ".cursor/commands/qa*.md" >> "$EXCLUDE_FILE"
fi

if [ "$1" != "--silent" ]; then
    echo "✅ Tasks do VS Code e Slash Commands configurados com sucesso!"
    echo "👉 Pressione Ctrl+Shift+B para iniciar todos os serviços."
    echo "👉 Comandos disponíveis na IDE:"
    echo "   • /qa-criar-plano        -> Gera o plano de testes de QA (QA Test Plan)"
    echo "   • /qa-criar-aplicacao    -> Cria aplicações prontas com turmas/alunos"
    echo "   • /qa-criar-caderno      -> Cria cadernos e questões de teste sob medida"
    echo "   • /qa-resetar-senhas     -> Reseta senhas, 2FA e sessões para login limpo"
    echo "   • /qa-exportar-plano     -> Exporta o plano para PDF com imagens embutidas"
    echo "   • /qa-responder-gabarito -> Gera cartões resposta preenchidos (PDF A4) para simulação OMR"
fi

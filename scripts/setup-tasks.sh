#!/usr/bin/env bash
# Script para configurar as tasks do VS Code e Slash Commands (/qa-create-exam, /qa-reset-passwords)
set -e

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
ACERVO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$ACERVO_DIR/.." && pwd)"
VSCODE_DIR="$WORKSPACE_ROOT/.vscode"
TASKS_SOURCE="$ACERVO_DIR/vscode/tasks.json"
SETTINGS_SOURCE="$ACERVO_DIR/vscode/settings.json"

# 1. Configura tasks.json e settings.json (serviços locais e colagem de prints em evidencias/)
mkdir -p "$VSCODE_DIR"
cp "$TASKS_SOURCE" "$VSCODE_DIR/tasks.json"
if [ -f "$SETTINGS_SOURCE" ]; then
    if [ ! -f "$VSCODE_DIR/settings.json" ]; then
        cp "$SETTINGS_SOURCE" "$VSCODE_DIR/settings.json"
    else
        python3 -c "
import json
try:
    with open('$VSCODE_DIR/settings.json', 'r') as f:
        dest = json.load(f)
except Exception:
    dest = {}
with open('$SETTINGS_SOURCE', 'r') as f:
    src = json.load(f)
for k, v in src.items():
    dest[k] = v
with open('$VSCODE_DIR/settings.json', 'w') as f:
    json.dump(dest, f, indent=2)
" 2>/dev/null || true
    fi
fi

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

rm -rf "$WORKSPACE_ROOT/.agents/skills/qa-"*
rm -rf "$WORKSPACE_ROOT/.agent/skills/qa-"*

# 3. Configura slash commands nas IDEs (Antigravity Skills e Cursor Commands) em pt-BR
mkdir -p "$WORKSPACE_ROOT/.agent/workflows"
mkdir -p "$WORKSPACE_ROOT/.agents/workflows"
mkdir -p "$WORKSPACE_ROOT/.cursor/commands"
mkdir -p "$WORKSPACE_ROOT/.agents/skills"

WORKFLOWS_DIR="$WORKSPACE_ROOT/.ai_qa_acervo/workflows"

link_workflow() {
    local src_file="$1"
    local alias_name="$2"
    local cmd_name="${alias_name%.md}"

    if [ -f "$WORKFLOWS_DIR/$src_file" ]; then
        # Retrocompatibilidade (Workflows legados e Cursor)
        ln -sf "../../.ai_qa_acervo/workflows/$src_file" "$WORKSPACE_ROOT/.agent/workflows/$alias_name"
        ln -sf "../../.ai_qa_acervo/workflows/$src_file" "$WORKSPACE_ROOT/.agents/workflows/$alias_name"
        ln -sf "../../.ai_qa_acervo/workflows/$src_file" "$WORKSPACE_ROOT/.cursor/commands/$alias_name"

        # Antigravity Skills (necessário para slash commands / no chat)
        local skill_dir="$WORKSPACE_ROOT/.agents/skills/$cmd_name"
        mkdir -p "$skill_dir"
        python3 -c "
import re

src_path = '$WORKFLOWS_DIR/$src_file'
cmd_name = '$cmd_name'
out_path = '$skill_dir/SKILL.md'

with open(src_path, 'r', encoding='utf-8') as f:
    content = f.read()

desc = 'Comandos de QA para Lize Edu'
body = content
if content.startswith('---'):
    parts = content.split('---', 2)
    if len(parts) >= 3:
        fm = parts[1]
        body = parts[2].lstrip()
        m = re.search(r'description:\s*(.+)', fm)
        if m:
            desc = m.group(1).strip()

new_content = f'''---
name: {cmd_name}
description: {desc}
---

{body}'''

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
"
    fi
}

link_workflow "qa-create-application.md" "qa-criar-aplicacao.md"
link_workflow "qa-create-exam.md"        "qa-criar-caderno.md"
link_workflow "qa-create-plan.md"        "qa-criar-plano.md"
link_workflow "qa-export-pdf.md"         "qa-exportar-plano.md"
link_workflow "qa-reset-passwords.md"    "qa-resetar-senhas.md"
link_workflow "qa-answer-omr.md"         "qa-responder-gabarito.md"
link_workflow "qa-create-mixed-distribution.md" "qa-criar-ensalamento-misto.md"
link_workflow "qa-create-mixed-distribution.md" "qa-criar-ensalamento.md"
link_workflow "qa-mcp-health.md"         "qa-mcp-health.md"
link_workflow "qa-mcp-health.md"         "qa-mcp.md"

# 4. Configura MCP servers para Antigravity e Cursor
MCP_SOURCE="$ACERVO_DIR/mcp/mcp_config.json"
if [ -f "$MCP_SOURCE" ]; then
    ln -sf "../.ai_qa_acervo/mcp/mcp_config.json" "$WORKSPACE_ROOT/.agents/mcp_config.json"
    mkdir -p "$WORKSPACE_ROOT/.cursor"
    ln -sf "../.ai_qa_acervo/mcp/mcp_config.json" "$WORKSPACE_ROOT/.cursor/mcp.json"
fi

# 5. Garante que os links e o acervo fiquem isolados e não sujem o git status do lizeedu
EXCLUDE_FILE="$WORKSPACE_ROOT/.git/info/exclude"
if [ -f "$EXCLUDE_FILE" ]; then
    grep -q "\.ai_qa_acervo/" "$EXCLUDE_FILE" || echo ".ai_qa_acervo/" >> "$EXCLUDE_FILE"
    grep -q "\.agent/workflows/qa\*" "$EXCLUDE_FILE" || echo ".agent/workflows/qa*.md" >> "$EXCLUDE_FILE"
    grep -q "\.agents/workflows/qa\*" "$EXCLUDE_FILE" || echo ".agents/workflows/qa*.md" >> "$EXCLUDE_FILE"
    grep -q "\.cursor/commands/qa\*" "$EXCLUDE_FILE" || echo ".cursor/commands/qa*.md" >> "$EXCLUDE_FILE"
    grep -q "\.agents/skills/qa\*" "$EXCLUDE_FILE" || echo ".agents/skills/qa*" >> "$EXCLUDE_FILE"
    grep -q "\.agent/skills/qa\*" "$EXCLUDE_FILE" || echo ".agent/skills/qa*" >> "$EXCLUDE_FILE"
    grep -q "\.agents/mcp_config\.json" "$EXCLUDE_FILE" || echo ".agents/mcp_config.json" >> "$EXCLUDE_FILE"
    grep -q "\.cursor/mcp\.json" "$EXCLUDE_FILE" || echo ".cursor/mcp.json" >> "$EXCLUDE_FILE"
fi

if [ "$1" != "--silent" ]; then
    echo "✅ Tasks do VS Code e Slash Commands configurados com sucesso!"
    echo "👉 Pressione Ctrl+Shift+B para iniciar todos os serviços."
    echo "👉 Comandos disponíveis na IDE:"
    echo "   • /qa-criar-plano             -> Gera o plano de testes de QA (QA Test Plan)"
    echo "   • /qa-criar-aplicacao         -> Cria aplicações prontas com turmas/alunos"
    echo "   • /qa-criar-caderno           -> Cria cadernos e questões de teste sob medida"
    echo "   • /qa-criar-ensalamento-misto -> Cria cadernos e aplicações sincronizadas (ou ensalamento) para testes mistos"
    echo "   • /qa-resetar-senhas          -> Reseta senhas, 2FA e sessões para login limpo"
    echo "   • /qa-exportar-plano          -> Exporta o plano para PDF com imagens embutidas"
    echo "   • /qa-responder-gabarito      -> Gera cartões resposta preenchidos (PDF A4) para simulação OMR"
fi

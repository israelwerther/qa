#!/usr/bin/env bash
# Atalho para executar o resetador de senhas e acessos para QA
# Uso:
#   ./.ai_qa_acervo/scripts/maintenance/reset-passwords.sh
#   ./.ai_qa_acervo/scripts/maintenance/reset-passwords.sh -p "minhasenha"
#   ./.ai_qa_acervo/scripts/maintenance/reset-passwords.sh -u "cloud.admin@lize.local"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PYTHON_BIN="$ROOT_DIR/venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/reset_passwords.py" "$@"

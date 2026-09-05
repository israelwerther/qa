#!/usr/bin/env bash
# Atalho para executar o gerador de aplicações de teste para QA
# Uso:
#   ./.ai_qa_acervo/scripts/generators/create-application.sh
#   ./.ai_qa_acervo/scripts/generators/create-application.sh -e "<NOME_OU_ID_DO_CADERNO>"
#   ./.ai_qa_acervo/scripts/generators/create-application.sh --create-exam -obj 10 -disc 2 -cat online

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PYTHON_BIN="$ROOT_DIR/venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/create_application.py" "$@"

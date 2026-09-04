#!/usr/bin/env bash
# Atalho para executar o gerador de cadernos e questões de teste para QA
# Uso:
#   ./.ai_qa_acervo/scripts/generators/create-exam.sh
#   ./.ai_qa_acervo/scripts/generators/create-exam.sh -obj 5 -disc 2 -ess 1 -rq -ra

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PYTHON_BIN="$ROOT_DIR/venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/create_exam.py" "$@"

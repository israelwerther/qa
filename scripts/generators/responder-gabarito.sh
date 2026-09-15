#!/usr/bin/env bash
# Atalho para executar o respondendor de cartões resposta OMR para QA
# Uso:
#   ./.ai_qa_acervo/scripts/generators/answer-omr-sheets.sh
#   ./.ai_qa_acervo/scripts/generators/answer-omr-sheets.sh -a "<NOME_OU_UUID_DA_APLICACAO>"
#   ./.ai_qa_acervo/scripts/generators/answer-omr-sheets.sh -a "<APLICACAO>" -sc 5 -m pendings

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PYTHON_BIN="$ROOT_DIR/venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/answer_omr_sheets.py" "$@"

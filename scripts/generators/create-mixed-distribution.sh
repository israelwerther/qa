#!/usr/bin/env bash
# Atalho para executar o gerador de dados para testes de ensalamento misto
# Uso:
#   ./.ai_qa_acervo/scripts/generators/create-mixed-distribution.sh
#   ./.ai_qa_acervo/scripts/generators/create-mixed-distribution.sh --ensalar
#   ./.ai_qa_acervo/scripts/generators/create-mixed-distribution.sh --date 2026-10-15 --client "Rede Decisão"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PYTHON_BIN="$ROOT_DIR/venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/create_mixed_distribution_data.py" "$@"

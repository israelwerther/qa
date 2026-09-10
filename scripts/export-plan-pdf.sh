#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$1" ]; then
  echo "Uso: ./scripts/export-plan-pdf.sh <caminho-para-o-plano.md> [saida.pdf]"
  exit 1
fi

bun "$SCRIPT_DIR/export-plan-pdf.js" "$@"

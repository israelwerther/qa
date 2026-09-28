#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$1" ]; then
  echo "Uso: ./scripts/export-plan-pdf.sh <plano.md> [saida.pdf] [--skip A,B|none]"
  echo "  --skip A,B    Pula seções (ex.: 4 ou 4,3). Padrão: exporta 100%, sem pular nada"
  echo "  --skip none   Não pula nenhuma seção (explícito)"
  exit 1
fi

bun "$SCRIPT_DIR/export-plan-pdf.js" "$@"

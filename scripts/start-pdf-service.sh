#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AI_QA_BIN="$SCRIPT_DIR/../bin"

if [ -f "$AI_QA_BIN/pdf-service" ]; then
    PDF_DIR="$AI_QA_BIN"
else
    PDF_DIR="${PDF_SERVICE_DIR:-$HOME/Downloads}"
fi

if [ ! -f "$PDF_DIR/pdf-service" ]; then
    echo "Erro: pdf-service não encontrado nem em $AI_QA_BIN nem em $HOME/Downloads."
    exit 1
fi

cd "$PDF_DIR"
chmod +x ./pdf-service

export AUTHORIZATION_TOKEN=7c20153c755006e6637c5faf1aa50310456de199
export AWS_ACCESS_KEY_ID=6DQCXN434NBPMV66H62W
export AWS_SECRET_ACCESS_KEY=Rr6WSyrykmLIIqoaJp0LD0iyK/Tc/Yu3fp6EPXgGNtA
export AWS_S3_ENDPOINT_URL=nyc3.digitaloceanspaces.com
export AWS_S3_REGION=nyc3
export AWS_S3_BUCKET_NAME=fiscallizeremote

echo "Iniciando PDF Service em $PDF_DIR..."
./pdf-service


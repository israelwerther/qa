#!/usr/bin/env bash
# ==============================================================================
# Script do Acervo de QA: Inicia ou gerencia o servidor Django QA dedicado
# Garante DEBUG=True e porta dedicada (8001 por padrão) para servir estáticos
# locais e evitar tela branca por dependência de CDN remota em testes de QA.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$REPO_DIR/venv"
PORT="${QA_PORT:-8001}"
HOST="${QA_HOST:-127.0.0.1}"
PID_FILE="/tmp/lize_qa_server_${PORT}.pid"
LOG_FILE="/tmp/lize_qa_server_${PORT}.log"

usage() {
    echo "Uso: $0 [start|stop|restart|status]"
    echo "  start   - Inicia o servidor QA em background com DEBUG=True na porta $PORT"
    echo "  stop    - Encerra o servidor QA ativo"
    echo "  restart - Reinicia o servidor QA"
    echo "  status  - Verifica se o servidor QA está respondendo"
    exit 1
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    # Fallback checando porta
    if ss -ltn 2>/dev/null | grep -q ":${PORT} "; then
        return 0
    fi
    return 1
}

start_server() {
    if is_running; then
        echo "ℹ️  Servidor QA já está rodando em http://${HOST}:${PORT}/"
        return 0
    fi

    if [ ! -d "$VENV_DIR" ]; then
        echo "❌ Ambiente virtual não encontrado em $VENV_DIR"
        exit 1
    fi

    echo "🚀 Iniciando servidor QA dedicado..."
    echo "   • Host: http://${HOST}:${PORT}/"
    echo "   • Modo: DEBUG=True (servindo estáticos locais)"
    echo "   • Log: $LOG_FILE"

    cd "$REPO_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"

    # Exporta DEBUG=True explicitamente para o processo filho
    nohup env DEBUG=True python manage.py runserver "${HOST}:${PORT}" --noreload > "$LOG_FILE" 2>&1 &
    local server_pid=$!
    echo "$server_pid" > "$PID_FILE"

    # Aguarda até 15 segundos para responder
    echo -n "⏳ Aguardando servidor subir..."
    for _ in {1..30}; do
        if curl -s -o /dev/null "http://${HOST}:${PORT}/conta/entrar/" 2>/dev/null; then
            echo " ✅ Pronto!"
            echo "🌐 Servidor QA ativo em http://${HOST}:${PORT}/ (PID $server_pid)"
            return 0
        fi
        sleep 0.5
        echo -n "."
    done

    echo " ⚠️ Servidor iniciado mas não respondeu ao healthcheck a tempo. Verifique $LOG_FILE"
}

stop_server() {
    echo "🛑 Parando servidor QA..."
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$PID_FILE"
    fi

    # Limpa processos remanescentes na porta se houver
    local port_pids
    port_pids=$(ss -lptn "sport = :${PORT}" 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2 || true)
    if [ -n "$port_pids" ]; then
        for p in $port_pids; do
            kill "$p" 2>/dev/null || true
        done
    fi

    echo "✅ Servidor QA encerrado."
}

status_server() {
    if is_running; then
        local code
        code=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST}:${PORT}/conta/entrar/" 2>/dev/null || echo "000")
        echo "✅ Servidor QA ATIVO em http://${HOST}:${PORT}/ (HTTP $code)"
        if [ -f "$PID_FILE" ]; then
            echo "   PID: $(cat "$PID_FILE")"
        fi
        return 0
    else
        echo "⚪ Servidor QA parado."
        return 1
    fi
}

case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        status_server
        ;;
    *)
        usage
        ;;
esac


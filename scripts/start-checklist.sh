#!/usr/bin/env bash
# ==============================================================================
# Script do Acervo de QA: Inicia ou gerencia o servidor de Checklist Interativo
# Permite marcar e desmarcar checkboxes do Plano de Testes diretamente no browser,
# sincronizando em tempo real com o arquivo markdown do plano na branch ativa.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PORT="${CHECKLIST_PORT:-8002}"
HOST="${CHECKLIST_HOST:-127.0.0.1}"
PID_FILE="/tmp/lize_qa_checklist_${PORT}.pid"
LOG_FILE="/tmp/lize_qa_checklist_${PORT}.log"

usage() {
    echo "Uso: $0 [start|stop|restart|status]"
    echo "  start   - Inicia o servidor de Checklist Interativo na porta $PORT"
    echo "  stop    - Encerra o servidor de Checklist ativo"
    echo "  restart - Reinicia o servidor de Checklist"
    echo "  status  - Verifica o status do servidor"
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
        echo "ℹ️  Servidor de Checklist já está rodando em http://${HOST}:${PORT}/"
        return 0
    fi

    echo "📋 Iniciando Servidor de Checklist Interativo..."
    echo "   • Interface Web: http://${HOST}:${PORT}/"
    echo "   • Log: $LOG_FILE"

    nohup setsid python3 "$SCRIPT_DIR/checklist_server.py" </dev/null > "$LOG_FILE" 2>&1 &
    local server_pid=$!
    echo "$server_pid" > "$PID_FILE"

    echo -n "⏳ Aguardando servidor subir..."
    for _ in {1..20}; do
        if curl -s -o /dev/null "http://${HOST}:${PORT}/" 2>/dev/null; then
            echo " ✅ Pronto!"
            echo "🌐 Checklist interativo ativo em http://${HOST}:${PORT}/ (PID $server_pid)"
            return 0
        fi
        sleep 0.3
        echo -n "."
    done

    echo " ⚠️ Servidor iniciado mas não respondeu a tempo. Verifique $LOG_FILE"
}

stop_server() {
    echo "🛑 Parando servidor de Checklist..."
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
        echo "   Matando processos remanescentes na porta $PORT..."
        echo "$port_pids" | xargs -r kill -9 2>/dev/null || true
    fi

    echo "✅ Servidor de Checklist encerrado."
}

status_server() {
    if is_running; then
        local pid="desconhecido"
        [ -f "$PID_FILE" ] && pid=$(cat "$PID_FILE")
        echo "🟢 Servidor de Checklist está RODANDO (PID: $pid)"
        echo "   • URL: http://${HOST}:${PORT}/"
        echo "   • Log: $LOG_FILE"
    else
        echo "🔴 Servidor de Checklist está PARADO"
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

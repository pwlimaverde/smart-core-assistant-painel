#!/bin/bash
# ============================================
# Health Monitor - Smart Core Assistant
# ============================================
# Monitora containers e reinicia em caso de falha.
# Executar via cron a cada 3-5 minutos:
#   */3 * * * * /opt/smartcore/scripts/health-monitor.sh >> /var/log/smartcore-health.log 2>&1
# ============================================

set -euo pipefail

LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"
RESTART_PERFORMED=false

# --- Configuracao ---
EVOLUTION_CONTAINER="paulo-ecoprint-evolution"
EVOLUTION_API_URL="http://localhost:8080"
EVOLUTION_API_KEY="${EVOLUTION_API_KEY:-1ad575386187bef01faf6a009f881c3081b91bab472956536f730ca7497b0b7e}"
EVOLUTION_INSTANCE="${EVOLUTION_INSTANCE:-atendimento}"

DJANGO_CONTAINER="smartcoreassistant_app"
DJANGO_URL="https://smartcoreassistant.com.br/"

CELERY_CONTAINER="smartcoreassistant_celery_worker"
CELERY_BEAT_CONTAINER="smartcoreassistant_celery_beat"

MAX_RESTART_WAIT=30  # segundos para aguardar apos restart

# --- Funcoes auxiliares ---
log() {
    echo "$LOG_PREFIX $1"
}

restart_container() {
    local container="$1"
    local reason="$2"
    log "RESTART: $container - $reason"
    docker restart "$container" --time 15
    RESTART_PERFORMED=true
    sleep "$MAX_RESTART_WAIT"
}

# --- Check 1: Evolution API - Conexao WhatsApp ---
check_evolution() {
    # Verificar se o container esta rodando
    if ! docker ps --format '{{.Names}}' | grep -q "^${EVOLUTION_CONTAINER}$"; then
        log "ERRO: Container $EVOLUTION_CONTAINER nao esta rodando"
        docker start "$EVOLUTION_CONTAINER" 2>/dev/null || true
        return
    fi

    # Verificar se o HTTP server responde
    local http_code
    http_code=$(curl -sf -o /dev/null -w '%{http_code}' \
        "${EVOLUTION_API_URL}/instance/connectionState/${EVOLUTION_INSTANCE}" \
        -H "apikey: ${EVOLUTION_API_KEY}" 2>/dev/null || echo "000")

    if [ "$http_code" = "000" ]; then
        restart_container "$EVOLUTION_CONTAINER" "HTTP server nao responde (code=$http_code)"
        return
    fi

    # Verificar estado da conexao WhatsApp
    local state
    state=$(curl -sf "${EVOLUTION_API_URL}/instance/connectionState/${EVOLUTION_INSTANCE}" \
        -H "apikey: ${EVOLUTION_API_KEY}" 2>/dev/null \
        | grep -o '"state":"[^"]*"' | cut -d'"' -f4 || echo "unknown")

    if [ "$state" != "open" ]; then
        restart_container "$EVOLUTION_CONTAINER" "WhatsApp desconectado (state=$state)"
        return
    fi

    log "OK: Evolution API - WhatsApp conectado"
}

# --- Check 2: Django App ---
check_django() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${DJANGO_CONTAINER}$"; then
        log "ERRO: Container $DJANGO_CONTAINER nao esta rodando"
        return
    fi

    local http_code
    http_code=$(curl -sf -o /dev/null -w '%{http_code}' --max-time 15 \
        "$DJANGO_URL" 2>/dev/null || echo "000")

    if [ "$http_code" = "000" ] || [ "$http_code" = "502" ] || [ "$http_code" = "503" ]; then
        restart_container "$DJANGO_CONTAINER" "Django nao responde (code=$http_code)"
        return
    fi

    log "OK: Django App (HTTP $http_code)"
}

# --- Check 3: Celery Worker ---
check_celery() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CELERY_CONTAINER}$"; then
        log "ERRO: Container $CELERY_CONTAINER nao esta rodando"
        return
    fi

    # Verificar se o worker esta responsivo via celery inspect ping
    local ping_result
    ping_result=$(docker exec "$CELERY_CONTAINER" \
        celery -A smart_core_assistant_painel.app.core inspect ping --timeout 10 2>/dev/null || echo "FAIL")

    if echo "$ping_result" | grep -q "pong"; then
        log "OK: Celery Worker respondendo"
    else
        restart_container "$CELERY_CONTAINER" "Worker nao responde ao ping"
    fi
}

# --- Check 4: Celery Beat ---
check_celery_beat() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CELERY_BEAT_CONTAINER}$"; then
        log "ERRO: Container $CELERY_BEAT_CONTAINER nao esta rodando"
        docker start "$CELERY_BEAT_CONTAINER" 2>/dev/null || true
        return
    fi
    log "OK: Celery Beat rodando"
}

# --- Execucao ---
log "=== Inicio do health check ==="

check_evolution
check_django
check_celery
check_celery_beat

if [ "$RESTART_PERFORMED" = true ]; then
    log "ALERTA: Um ou mais containers foram reiniciados"
fi

log "=== Fim do health check ==="

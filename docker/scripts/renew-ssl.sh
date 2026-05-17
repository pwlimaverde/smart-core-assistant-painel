#!/bin/bash
# ============================================
# Smart Core - Renovação automática de certificado SSL
# Uso: crontab -e → 0 3 * * * /root/smart-core-assistant-painel/docker/scripts/renew-ssl.sh
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

echo "[$(date)] Iniciando renovação de certificado SSL..."

SMARTCORE_ENV_FILE=.env.prod docker compose --env-file .env.prod \
    -p smart-core-proxy -f docker/compose/proxy.yml \
    --profile ssl run --rm certbot renew --quiet

echo "[$(date)] Recarregando Nginx..."
docker exec smartcoreassistant_nginx nginx -s reload

echo "[$(date)] Renovação concluída."

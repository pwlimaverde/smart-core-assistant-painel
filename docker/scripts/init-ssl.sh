#!/bin/bash
# ============================================
# Smart Core - Inicialização SSL com Let's Encrypt
# Uso: bash docker/scripts/init-ssl.sh
# ============================================
set -e

DOMAIN="${CERTBOT_DOMAIN:-smartcoreassistant.com.br}"
EMAIL="${CERTBOT_EMAIL:-admin@$DOMAIN}"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

echo "================================================"
echo "  SMART CORE - INIT SSL"
echo "  Domínio: $DOMAIN"
echo "  Email: $EMAIL"
echo "================================================"

# --- Passo 1: Criar certificado auto-assinado temporário ---
echo ""
echo ">>> Passo 1: Criando certificado temporário..."

# Cria diretório para o certificado
docker run --rm \
    -v smartcore_ssl_certs:/etc/letsencrypt \
    alpine sh -c "
        mkdir -p /etc/letsencrypt/live/$DOMAIN &&
        openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
            -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
            -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
            -subj '/CN=$DOMAIN' &&
        cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
           /etc/letsencrypt/live/$DOMAIN/chain.pem
    "

echo "    Certificado temporário criado."

# --- Passo 2: Iniciar Nginx com cert temporário ---
echo ""
echo ">>> Passo 2: Iniciando Nginx..."

SMARTCORE_ENV_FILE=.env.prod docker compose --env-file .env.prod \
    -p smart-core-proxy -f docker/compose/proxy.yml \
    up -d nginx

echo "    Nginx iniciado com certificado temporário."

# --- Passo 3: Solicitar certificado real via DNS-01 ---
echo ""
echo ">>> Passo 3: Solicitando certificado real (DNS-01)..."
echo "    Aguarde a propagação DNS (pode levar até 2 minutos)..."

SMARTCORE_ENV_FILE=.env.prod docker compose --env-file .env.prod \
    -p smart-core-proxy -f docker/compose/proxy.yml \
    --profile ssl run --rm certbot certonly \
    --dns-cloudflare \
    --dns-cloudflare-credentials /etc/cloudflare/cloudflare.ini \
    --dns-cloudflare-propagation-seconds 60 \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "*.$DOMAIN" \
    --force-renewal

echo "    Certificado wildcard obtido com sucesso!"

# --- Passo 4: Recarregar Nginx com cert real ---
echo ""
echo ">>> Passo 4: Recarregando Nginx com certificado real..."

docker exec smartcoreassistant_nginx nginx -s reload

echo ""
echo "================================================"
echo "  SSL CONFIGURADO COM SUCESSO!"
echo "  Domínio: $DOMAIN + *.$DOMAIN"
echo "  Certificado: $CERT_PATH"
echo "================================================"

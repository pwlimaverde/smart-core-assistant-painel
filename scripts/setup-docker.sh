#!/bin/bash

# Script de configuração inicial para Docker
# Smart Core Assistant Painel + Evolution API

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_message() {
    echo -e "${2}${1}${NC}"
}

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Função para gerar chave secreta Django
generate_django_secret() {
    python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
}

# Função para gerar senha aleatória
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

print_message "🚀 Configuração Docker - Smart Core Assistant Painel" "$BLUE"
print_message "================================================" "$BLUE"

# Verificar pré-requisitos
print_message "\n📋 Verificando pré-requisitos..." "$YELLOW"

if ! command_exists docker; then
    print_message "❌ Docker não encontrado. Instale o Docker primeiro." "$RED"
    exit 1
fi

if ! command_exists docker-compose; then
    print_message "❌ Docker Compose não encontrado. Instale o Docker Compose primeiro." "$RED"
    exit 1
fi

if ! command_exists python3; then
    print_message "❌ Python 3 não encontrado. Instale o Python 3 primeiro." "$RED"
    exit 1
fi

print_message "✅ Todos os pré-requisitos atendidos!" "$GREEN"

# Verificar se arquivo .env já existe
if [ -f ".env" ]; then
    print_message "\n⚠️  Arquivo .env já existe." "$YELLOW"
    read -p "Deseja sobrescrever? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "Mantendo arquivo .env existente." "$BLUE"
        ENV_EXISTS=true
    fi
fi

# Criar arquivo .env se não existir ou se usuário escolheu sobrescrever
if [ "$ENV_EXISTS" != true ]; then
    print_message "\n🔧 Configurando variáveis de ambiente..." "$YELLOW"
    
    # Gerar senhas e chaves
    DJANGO_SECRET=$(generate_django_secret)
    EVOLUTION_API_KEY=$(generate_password)
    MONGO_PASSWORD=$(generate_password)
    REDIS_PASSWORD=$(generate_password)
    
    # Solicitar OpenAI API Key
    echo
    read -p "Digite sua OpenAI API Key: " OPENAI_API_KEY
    
    # Criar arquivo .env
    cat > .env << EOF
# Django Configuration
SECRET_KEY_DJANGO=${DJANGO_SECRET}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# OpenAI Configuration
OPENAI_API_KEY=${OPENAI_API_KEY}

# Evolution API Configuration
EVOLUTION_API_KEY=${EVOLUTION_API_KEY}
EVOLUTION_API_URL=http://localhost:8080

# Database Configuration (MongoDB for Evolution API)
MONGO_USERNAME=admin
MONGO_PASSWORD=${MONGO_PASSWORD}

# Redis Configuration
REDIS_PASSWORD=${REDIS_PASSWORD}

# Webhook Configuration
WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/

# Server Configuration
SERVER_PORT=8000
EVOLUTION_PORT=8080

# Security
CORS_ORIGIN=*

# Logging
LOG_LEVEL=INFO
EOF

    print_message "✅ Arquivo .env criado com sucesso!" "$GREEN"
    print_message "📝 Credenciais geradas:" "$BLUE"
    print_message "   - Evolution API Key: ${EVOLUTION_API_KEY}" "$BLUE"
    print_message "   - MongoDB Password: ${MONGO_PASSWORD}" "$BLUE"
    print_message "   - Redis Password: ${REDIS_PASSWORD}" "$BLUE"
fi

# Escolher ambiente
print_message "\n🏗️  Escolha o ambiente:" "$YELLOW"
echo "1) Produção (otimizado)"
echo "2) Desenvolvimento (com hot reload)"
echo "3) Desenvolvimento + Ferramentas (MongoDB Express, Redis Commander)"
read -p "Escolha uma opção (1-3): " ENV_CHOICE

case $ENV_CHOICE in
    1)
        COMPOSE_FILE="docker-compose.yml"
        ENV_NAME="Produção"
        ;;
    2)
        COMPOSE_FILE="docker-compose.dev.yml"
        ENV_NAME="Desenvolvimento"
        ;;
    3)
        COMPOSE_FILE="docker-compose.dev.yml"
        COMPOSE_PROFILES="--profile tools"
        ENV_NAME="Desenvolvimento + Ferramentas"
        ;;
    *)
        print_message "Opção inválida. Usando produção." "$YELLOW"
        COMPOSE_FILE="docker-compose.yml"
        ENV_NAME="Produção"
        ;;
esac

print_message "\n🔨 Construindo imagens Docker..." "$YELLOW"
docker-compose -f $COMPOSE_FILE build

print_message "\n🚀 Iniciando serviços ($ENV_NAME)..." "$YELLOW"
docker-compose -f $COMPOSE_FILE $COMPOSE_PROFILES up -d

# Aguardar serviços ficarem prontos
print_message "\n⏳ Aguardando serviços ficarem prontos..." "$YELLOW"
sleep 10

# Executar migrações
print_message "\n📊 Executando migrações do banco de dados..." "$YELLOW"
docker-compose -f $COMPOSE_FILE exec -T django-app python src/smart_core_assistant_painel/app/ui/manage.py migrate

# Coletar arquivos estáticos
print_message "\n📁 Coletando arquivos estáticos..." "$YELLOW"
docker-compose -f $COMPOSE_FILE exec -T django-app python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput

# Verificar status dos serviços
print_message "\n📊 Status dos serviços:" "$YELLOW"
docker-compose -f $COMPOSE_FILE ps

# Informações finais
print_message "\n🎉 Configuração concluída com sucesso!" "$GREEN"
print_message "\n📱 URLs de acesso:" "$BLUE"
print_message "   - Django Admin: http://localhost:8000/admin/" "$BLUE"
print_message "   - Evolution API: http://localhost:8080" "$BLUE"

if [ "$ENV_CHOICE" = "3" ]; then
    print_message "   - MongoDB Express: http://localhost:8081" "$BLUE"
    print_message "   - Redis Commander: http://localhost:8082" "$BLUE"
fi

print_message "\n🔧 Próximos passos:" "$YELLOW"
print_message "   1. Acesse http://localhost:8000/admin/ para criar um superusuário" "$YELLOW"
print_message "   2. Configure sua instância do WhatsApp na Evolution API" "$YELLOW"
print_message "   3. Teste o webhook em http://localhost:8000/oraculo/webhook_whatsapp/" "$YELLOW"

print_message "\n📚 Comandos úteis:" "$BLUE"
print_message "   - Ver logs: docker-compose -f $COMPOSE_FILE logs -f" "$BLUE"
print_message "   - Parar: docker-compose -f $COMPOSE_FILE down" "$BLUE"
print_message "   - Reiniciar: docker-compose -f $COMPOSE_FILE restart" "$BLUE"

print_message "\n✨ Setup concluído! Bom desenvolvimento!" "$GREEN"
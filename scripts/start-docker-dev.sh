#!/bin/bash

# Script para iniciar o ambiente de desenvolvimento com Docker
set -e

echo "🐳 Iniciando ambiente de desenvolvimento Smart Core Assistant..."

# Verificar se o Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Parar containers existentes se estiverem rodando
echo "🛑 Parando containers existentes..."
docker-compose down

# Construir imagens
echo "🔨 Construindo imagens Docker..."
docker-compose build

# Iniciar serviços
echo "🚀 Iniciando serviços..."
docker-compose up -d

# Aguardar um pouco para os serviços iniciarem
echo "⏳ Aguardando serviços iniciarem..."
sleep 10

# Mostrar status dos containers
echo "📊 Status dos containers:"
docker-compose ps

# Mostrar logs do Django
echo "📝 Logs do Django (últimas 20 linhas):"
docker-compose logs --tail=20 django-app

echo "✅ Ambiente de desenvolvimento iniciado com sucesso!"
echo "🌐 Aplicação disponível em: http://localhost:8000"
echo "🔧 Evolution API disponível em: http://localhost:8080"
echo ""
echo "📋 Comandos úteis:"
echo "  - Ver logs: docker-compose logs -f"
echo "  - Parar: docker-compose down"
echo "  - Reiniciar: docker-compose restart"
echo "  - Shell Django: docker-compose exec django-app bash"
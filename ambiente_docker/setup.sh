#!/bin/bash

# Script unificado para configurar e iniciar o ambiente de desenvolvimento Docker
# Este script consolida toda a lógica de setup, garantindo um ambiente limpo e pronto para uso.

set -e  # Exit on any error

echo "=== Configurando o ambiente de desenvolvimento Docker ==="

# Verificar se estamos na raiz do projeto
if [ ! -f "pyproject.toml" ]; then
    echo "ERRO: Este script deve ser executado na raiz do projeto."
    exit 1
fi

# 1. Verificar e carregar o arquivo .env
echo "1. Verificando o arquivo de configuração .env..."

if [ ! -f ".env" ]; then
    echo "ERRO: Arquivo .env não encontrado na raiz do projeto."
    echo "Por favor, crie um arquivo .env antes de continuar."
    exit 1
fi
# Exportar variáveis do .env para o shell atual
export $(grep -v '^#' .env | xargs)

echo "Arquivo .env encontrado e variáveis carregadas."

# 2. Verificar e criar o firebase_key.json
echo "2. Verificando as credenciais do Firebase..."

if [ -z "$FIREBASE_KEY_JSON_CONTENT" ]; then
    echo "AVISO: A variável FIREBASE_KEY_JSON_CONTENT não está definida no .env."
    echo "Se o seu GOOGLE_APPLICATION_CREDENTIALS aponta para um arquivo que já existe, tudo bem."
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] || [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "ERRO: GOOGLE_APPLICATION_CREDENTIALS não aponta para um arquivo válido e FIREBASE_KEY_JSON_CONTENT não está definida."
        exit 1
    fi
else
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "ERRO: A variável GOOGLE_APPLICATION_CREDENTIALS não está definida no .env."
        exit 1
    fi
    FIREBASE_KEY_PATH="$GOOGLE_APPLICATION_CREDENTIALS"
    FIREBASE_KEY_DIR=$(dirname "$FIREBASE_KEY_PATH")
    
    echo "Criando o arquivo firebase_key.json em $FIREBASE_KEY_PATH..."
    mkdir -p "$FIREBASE_KEY_DIR"
    echo "$FIREBASE_KEY_JSON_CONTENT" > "$FIREBASE_KEY_PATH"
    echo "Arquivo firebase_key.json criado com sucesso."
fi

# 2.1. Verificar configurações do Redis para Django Q Cluster
echo "2.1. Verificando configurações do Redis para Django Q Cluster..."

if ! grep -q "^REDIS_HOST=" .env; then
    echo "AVISO: Variável REDIS_HOST não encontrada no .env. Adicionando valor padrão: redis"
    echo "REDIS_HOST=redis" >> .env
fi

if ! grep -q "^REDIS_PORT=" .env; then
    echo "AVISO: Variável REDIS_PORT não encontrada no .env. Adicionando valor padrão: 6379"
    echo "REDIS_PORT=6379" >> .env
fi

echo "Configurações do Redis verificadas."


# 3. Limpeza completa do ambiente Docker anterior
echo "3. Limpando ambiente Docker anterior (containers, volumes e redes)..."
docker compose down -v --remove-orphans

# 4. Apagar migrações antigas dos apps Django
echo "4. Apagando migrações antigas do Django..."
find src/smart_core_assistant_painel/app/ui -path '*/migrations/*.py' -not -name '__init__.py' -delete
find src/smart_core_assistant_painel/app/ui -path '*/migrations/*.pyc' -delete
echo "Migrações antigas removidas."

# 5. Construir e iniciar os containers
echo "5. Construindo imagens Docker e iniciando os containers..."
docker compose build
docker compose up -d
echo "5.1. Parando temporariamente o django-qcluster ate concluir as migracoes..."
docker compose stop django-qcluster

# 6. Aguardar o banco de dados ficar pronto
wait_for_db() {
    echo "🔍 Aguardando conexão com o banco de dados..."
    # Acessa as variáveis de ambiente do container django-app
    until docker compose exec -T django-app sh -c "uv run python -c \"import psycopg, os; psycopg.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), dbname=os.getenv('POSTGRES_DB'))\"" 2>/dev/null; do
        echo "⏳ Banco de dados não está pronto. Aguardando 5 segundos..."
        sleep 5
    done
    echo "✅ Banco de dados conectado com sucesso!"
}

wait_for_db

# 7. Criar e aplicar novas migrações do Django
echo "7. Criando e aplicando novas migrações do Django..."
docker compose exec -T django-app uv run task makemigrations
docker compose exec -T django-app uv run task migrate
echo "Aplicando migracoes especificas do django_q..."
docker compose exec -T django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate django_q --noinput

# 8. Criar superusuário
echo "8. Criando superusuário 'admin' com senha '123456'..."
SUPERUSER_COMMAND="from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', '123456')"
docker compose exec -T django-app uv run python -c "$SUPERUSER_COMMAND"
echo "Superusuário criado com sucesso!"
echo "9. Iniciando o django-qcluster apos as migracoes..."
docker compose start django-qcluster

echo ""
echo "=== Ambiente Docker pronto! ==="
echo "A aplicação está disponível em http://localhost:8000"
echo "O painel administrativo está em http://localhost:8000/admin/"
echo "Use 'docker compose logs -f' para ver os logs."
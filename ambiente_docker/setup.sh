#!/bin/bash

# Script unificado para configurar e iniciar o ambiente Docker completo
# Este script inclui todos os arquivos necessários inline, sem dependências externas

set -e  # Exit on any error

echo "=== Configurando o ambiente Docker ==="

# Verificar se estamos na raiz do projeto
if [ ! -f "pyproject.toml" ]; then
    echo "ERRO: Este script deve ser executado na raiz do projeto."
    exit 1
fi

# 1. Verificar pré-requisitos
echo "1. Verificando pré-requisitos..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "ERRO: Docker não está instalado ou não está no PATH."
    echo "Instale o Docker Desktop e tente novamente."
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "ERRO: Docker Compose não está instalado ou não está no PATH."
    exit 1
fi

# Verificar se Docker está rodando
if ! docker info &> /dev/null; then
    echo "ERRO: Docker não está rodando. Inicie o Docker Desktop e tente novamente."
    exit 1
fi

echo "✅ Docker e Docker Compose encontrados e funcionando."

# 2. Verificar arquivos de configuração necessários
echo "2. Verificando arquivos de configuração..."

if [ ! -f ".env" ]; then
    echo "ERRO: Antes de executar a criação do ambiente Docker, salve o arquivo .env na raiz do projeto."
    echo ""
    echo "Copie o arquivo .env.example do ambiente_docker e configure suas variáveis:"
    echo "cp ambiente_docker/.env.example .env"
    echo ""
    echo "Configure especialmente as seguintes variáveis obrigatórias:"
    echo "- SECRET_KEY_DJANGO"
    echo "- EVOLUTION_API_KEY"
    echo "- FIREBASE_KEY_JSON_CONTENT"
    echo "- GOOGLE_APPLICATION_CREDENTIALS"
    echo ""
    exit 1
fi

echo "Arquivo .env encontrado."

# 3. Processar credenciais Firebase usando GOOGLE_APPLICATION_CREDENTIALS do .env
echo "3. Validando e criando credenciais Firebase..."

# Extrair GOOGLE_APPLICATION_CREDENTIALS do .env
FIREBASE_PATH=$(grep "^GOOGLE_APPLICATION_CREDENTIALS=" .env | cut -d'=' -f2-)
if [ -z "$FIREBASE_PATH" ]; then
    echo "ERRO: Variável GOOGLE_APPLICATION_CREDENTIALS não encontrada no arquivo .env"
    echo "Por favor, adicione a variável GOOGLE_APPLICATION_CREDENTIALS no .env"
    echo "Exemplo: GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json"
    exit 1
fi

echo "Caminho do firebase_key.json definido por GOOGLE_APPLICATION_CREDENTIALS: $FIREBASE_PATH"

# Criar diretório se não existir
FIREBASE_KEY_DIR=$(dirname "$FIREBASE_PATH")
if [ ! -d "$FIREBASE_KEY_DIR" ]; then
    echo "Criando diretório: $FIREBASE_KEY_DIR"
    mkdir -p "$FIREBASE_KEY_DIR"
fi

# Verificar se FIREBASE_KEY_JSON_CONTENT existe no .env
if ! grep -q "^FIREBASE_KEY_JSON_CONTENT=" .env; then
    echo "ERRO: Variável FIREBASE_KEY_JSON_CONTENT não encontrada no arquivo .env"
    echo "Por favor, adicione a variável FIREBASE_KEY_JSON_CONTENT no .env com o conteúdo JSON do Firebase"
    echo 'Exemplo: FIREBASE_KEY_JSON_CONTENT={"type":"service_account","project_id":"seu-projeto",...}'
    exit 1
fi

echo "Criando firebase_key.json a partir da variável FIREBASE_KEY_JSON_CONTENT..."
FIREBASE_CONTENT=$(grep "^FIREBASE_KEY_JSON_CONTENT=" .env | cut -d'=' -f2-)

if [ -n "$FIREBASE_CONTENT" ]; then
    echo "$FIREBASE_CONTENT" > "$FIREBASE_PATH"
    echo "Arquivo firebase_key.json criado com sucesso em $FIREBASE_PATH"
else
    echo "ERRO: Variável FIREBASE_KEY_JSON_CONTENT está vazia no arquivo .env"
    echo "Por favor, adicione o conteúdo JSON do Firebase na variável FIREBASE_KEY_JSON_CONTENT"
    exit 1
fi

# 4. Criar docker-compose.yml
echo "3. Criando docker-compose.yml..."

# Definir caminhos do Firebase
CONTAINER_FIREBASE_PATH="/app/$FIREBASE_PATH"
FIREBASE_KEY_DIR_HOST=$(dirname "$FIREBASE_PATH")
FIREBASE_KEY_DIR_CONTAINER="/app/$FIREBASE_KEY_DIR_HOST"

cat > docker-compose.yml << EOF
services:
  # Aplicação Django para desenvolvimento
  django-app:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8001:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=smart_core_assistant_painel.app.ui.core.settings
      - DJANGO_DEBUG=True
      - SECRET_KEY_DJANGO=temp-secret-key-for-initial-startup-will-be-replaced-by-firebase-remote-config
      - POSTGRES_DB=smart_core_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres123
      - POSTGRES_HOST=postgres-django
      - POSTGRES_PORT=5432
      - GOOGLE_APPLICATION_CREDENTIALS=$CONTAINER_FIREBASE_PATH
      # Configuração para acesso ao Ollama local
      - OLLAMA_HOST=host.docker.internal
      - OLLAMA_PORT=11434
      # Variáveis dinâmicas serão configuradas pelo start_services
      # SECRET_KEY_DJANGO, OPENAI_API_KEY, GROQ_API_KEY, etc. vêm do Firebase Remote Config
    volumes:
      # Mount source code for hot reload
      - ./src:/app/src
      - ./tests:/app/tests
      - ./pyproject.toml:/app/pyproject.toml
      # Persistent data
      - ./src/smart_core_assistant_painel/app/ui/db:/app/src/smart_core_assistant_painel/app/ui/db
      - ./src/smart_core_assistant_painel/app/ui/media:/app/src/smart_core_assistant_painel/app/ui/media
      # Mount Firebase credentials dynamically
      - ./$FIREBASE_KEY_DIR_HOST:$FIREBASE_KEY_DIR_CONTAINER
    depends_on:
      - postgres-django
    networks:
      - smart-core-network
    extra_hosts:
      - "host.docker.internal:host-gateway"
    entrypoint: ["/usr/local/bin/docker-entrypoint.sh"]
    command: ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "runserver", "0.0.0.0:8000"]

  # Django Q Cluster para desenvolvimento
  django-qcluster:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=smart_core_assistant_painel.app.ui.core.settings
      - DJANGO_DEBUG=True
      - SECRET_KEY_DJANGO=temp-secret-key-for-initial-startup-will-be-replaced-by-firebase-remote-config
      - POSTGRES_DB=smart_core_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres123
      - POSTGRES_HOST=postgres-django
      - POSTGRES_PORT=5432
      - GOOGLE_APPLICATION_CREDENTIALS=$CONTAINER_FIREBASE_PATH
      # Configuração para acesso ao Ollama local
      - OLLAMA_HOST=host.docker.internal
      - OLLAMA_PORT=11434
      # Variáveis dinâmicas serão configuradas pelo start_services
      # SECRET_KEY_DJANGO, OPENAI_API_KEY, GROQ_API_KEY, etc. vêm do Firebase Remote Config
    volumes:
      - ./src:/app/src
      - ./src/smart_core_assistant_painel/app/ui/db:/app/src/smart_core_assistant_painel/app/ui/db
      - ./src/smart_core_assistant_painel/app/ui/media:/app/src/smart_core_assistant_painel/app/ui/media
      # Mount Firebase credentials dynamically
      - ./$FIREBASE_KEY_DIR_HOST:$FIREBASE_KEY_DIR_CONTAINER
    depends_on:
      - django-app
    networks:
      - smart-core-network
    extra_hosts:
      - "host.docker.internal:host-gateway"
    entrypoint: ["/usr/local/bin/docker-entrypoint-qcluster.sh"]
    command: ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "qcluster"]

  # PostgreSQL para Django
  postgres-django:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=smart_core_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres123
    ports:
      - "5435:5432"
    volumes:
      - postgres_django_data:/var/lib/postgresql/data
    networks:
      - smart-core-network

  # PostgreSQL para Evolution API
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=evolution
      - POSTGRES_USER=evolution
      - POSTGRES_PASSWORD=evolution123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - smart-core-network

  # Redis para Evolution API
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6380:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - smart-core-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Evolution API para desenvolvimento
  evolution-api:
    image: atendai/evolution-api:v2.1.1
    restart: unless-stopped
    ports:
      - "8081:8080"
    environment:
      # Configuração de autenticação
      - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
      
      # Configuração do webhook global (com tratamento UTF-8 robusto)
      - WEBHOOK_GLOBAL_URL=http://django-app:8000/oraculo/webhook_whatsapp/
      - WEBHOOK_GLOBAL_ENABLED=true
      - WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=false
      
      # Configuração do banco de dados PostgreSQL
      - DATABASE_ENABLED=true
      - DATABASE_PROVIDER=postgresql
      - DATABASE_CONNECTION_URI=postgresql://evolution:evolution123@postgres:5432/evolution?schema=public
      - DATABASE_CONNECTION_CLIENT_NAME=evolution_exchange
      - DATABASE_SAVE_DATA_INSTANCE=true
      - DATABASE_SAVE_DATA_NEW_MESSAGE=true
      - DATABASE_SAVE_MESSAGE_UPDATE=true
      - DATABASE_SAVE_DATA_CONTACTS=true
      - DATABASE_SAVE_DATA_CHATS=true
      - DATABASE_SAVE_DATA_LABELS=true
      - DATABASE_SAVE_DATA_HISTORIC=true
      
      # Configuração do Redis Cache
      - CACHE_REDIS_ENABLED=true
      - CACHE_REDIS_URI=redis://redis:6379/6
      - CACHE_REDIS_TTL=604800
      - CACHE_REDIS_PREFIX_KEY=evolution
      - CACHE_REDIS_SAVE_INSTANCES=false
      - CACHE_LOCAL_ENABLED=false
      
      # Configuração do QR Code (Correções Implementadas)
      - QRCODE_LIMIT=30
      - QRCODE_COLOR=#198754
      
      # Configurações de servidor
      - SERVER_TYPE=http
      - SERVER_PORT=8080
      - SERVER_URL=http://localhost:8081
      
      # Configurações de log
      - LOG_LEVEL=ERROR
      - LOG_COLOR=true
      - LOG_BAILEYS=error
      - CONFIG_SESSION_PHONE_VERSION=2.3000.1023204200
    volumes:
      - evolution_instances:/evolution/instances
    depends_on:
      - postgres
      - redis
    networks:
      - smart-core-network
    env_file:
      - .env

volumes:
  evolution_instances:
    driver: local
  postgres_data:
    driver: local
  postgres_django_data:
    driver: local
  redis_data:
    driver: local

networks:
  smart-core-network:
    driver: bridge
EOF

echo "Arquivo docker-compose.yml criado com sucesso."

# 5. Criar scripts de entrypoint
echo "4. Criando scripts de entrypoint..."

# Criar docker-entrypoint.sh
cat > docker-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Função para aguardar o banco de dados
wait_for_db() {
    echo "🔍 Aguardando conexão com o banco de dados..."
    while ! uv run python -c "import psycopg; psycopg.connect(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
        echo "⏳ Banco de dados não está pronto. Aguardando..."
        sleep 2
    done
    echo "✅ Banco de dados conectado com sucesso!"
}

# Função para verificar se as credenciais do Firebase existem
check_firebase_credentials() {
    echo "🔑 Verificando credenciais do Firebase..."
    if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "❌ Erro: Arquivo de credenciais do Firebase não encontrado em $GOOGLE_APPLICATION_CREDENTIALS"
        echo "📋 Certifique-se de que o arquivo firebase_key.json está presente no diretório correto."
        exit 1
    fi
    echo "✅ Credenciais do Firebase encontradas!"
}

# Função para executar inicialização completa
run_initialization() {
    echo "🔥 Iniciando processo de inicialização completo..."
    
    # Verifica credenciais do Firebase
    check_firebase_credentials
    
    # Executa start_initial_loading (inicialização do Firebase)
    echo "📱 Executando start_initial_loading (Firebase Remote Config)..."
    uv run python -c "
from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import start_initial_loading
try:
    start_initial_loading()
    print('✅ start_initial_loading executado com sucesso!')
except Exception as e:
    print(f'❌ Erro em start_initial_loading: {e}')
    raise
"
    
    # Executa start_services (carregamento de remote config e configuração de variáveis)
    echo "⚙️  Executando start_services (carregamento de configurações)..."
    uv run python -c "
from smart_core_assistant_painel.modules.services.start_services import start_services
try:
    start_services()
    print('✅ start_services executado com sucesso!')
except Exception as e:
    print(f'❌ Erro em start_services: {e}')
    raise
"
    
    echo "✅ Inicialização completa finalizada com sucesso!"
}

# Função para verificar conectividade com Ollama
check_ollama_connectivity() {
    echo "🤖 Verificando conectividade com Ollama..."
    if curl -s "http://${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}/api/tags" > /dev/null 2>&1; then
        echo "✅ Ollama está acessível!"
    else
        echo "⚠️  Aviso: Ollama não está acessível. Verifique se está rodando localmente."
        echo "📋 Host: ${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}"
    fi
}

# Aguarda o banco de dados estar disponível
wait_for_db

# Verifica conectividade com Ollama
check_ollama_connectivity

# Executa a inicialização completa (Firebase + Services)
run_initialization

# Executa migrações
echo "📊 Executando migrações..."
uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate

# Cria superusuário se não existir
echo "👤 Criando superusuário..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', '123456')" | uv run python src/smart_core_assistant_painel/app/ui/manage.py shell

# Executa o comando passado como argumento
echo "🚀 Iniciando aplicação Django..."
exec "$@"
EOF

# Criar docker-entrypoint-qcluster.sh
cat > docker-entrypoint-qcluster.sh << 'EOF'
#!/bin/bash
set -e

# Função para aguardar o banco de dados
wait_for_db() {
    echo "🔍 Aguardando conexão com o banco de dados..."
    while ! uv run python -c "import psycopg; psycopg.connect(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
        echo "⏳ Banco de dados não está pronto. Aguardando..."
        sleep 2
    done
    echo "✅ Banco de dados conectado com sucesso!"
}

# Função para verificar se as credenciais do Firebase existem
check_firebase_credentials() {
    echo "🔑 Verificando credenciais do Firebase..."
    if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "❌ Erro: Arquivo de credenciais do Firebase não encontrado em $GOOGLE_APPLICATION_CREDENTIALS"
        echo "📋 Certifique-se de que o arquivo firebase_key.json está presente no diretório correto."
        exit 1
    fi
    echo "✅ Credenciais do Firebase encontradas!"
}

# Função para executar inicialização completa
run_initialization() {
    echo "🔥 Iniciando processo de inicialização completo para QCluster..."
    
    # Verifica credenciais do Firebase
    check_firebase_credentials
    
    # Executa start_initial_loading (inicialização do Firebase)
    echo "📱 Executando start_initial_loading (Firebase Remote Config)..."
    uv run python -c "
from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import start_initial_loading
try:
    start_initial_loading()
    print('✅ start_initial_loading executado com sucesso!')
except Exception as e:
    print(f'❌ Erro em start_initial_loading: {e}')
    raise
"
    
    # Executa start_services (carregamento de remote config e configuração de variáveis)
    echo "⚙️  Executando start_services (carregamento de configurações)..."
    uv run python -c "
from smart_core_assistant_painel.modules.services.start_services import start_services
try:
    start_services()
    print('✅ start_services executado com sucesso!')
except Exception as e:
    print(f'❌ Erro em start_services: {e}')
    raise
"
    
    echo "✅ Inicialização completa finalizada com sucesso para QCluster!"
}

# Função para verificar conectividade com Ollama
check_ollama_connectivity() {
    echo "🤖 Verificando conectividade com Ollama..."
    if curl -s "http://${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}/api/tags" > /dev/null 2>&1; then
        echo "✅ Ollama está acessível!"
    else
        echo "⚠️  Aviso: Ollama não está acessível. Verifique se está rodando localmente."
        echo "📋 Host: ${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}"
    fi
}

# Função para aguardar o Django principal estar pronto
wait_for_django_app() {
    echo "⏳ Aguardando Django principal estar pronto..."
    while ! curl -s http://django-app:8000/admin/ > /dev/null 2>&1; do
        echo "🔄 Django principal ainda não está pronto. Aguardando..."
        sleep 5
    done
    echo "✅ Django principal está pronto!"
}

# Aguarda o banco de dados estar disponível
wait_for_db

# Verifica conectividade com Ollama
check_ollama_connectivity

# Executa a inicialização completa (Firebase + Services)
run_initialization

# Aguarda o Django principal estar pronto
wait_for_django_app

# Executa o comando passado como argumento
echo "🚀 Iniciando QCluster..."
exec "$@"
EOF

chmod +x docker-entrypoint.sh docker-entrypoint-qcluster.sh

echo "Scripts de entrypoint criados com sucesso."

# 6. Atualizar Dockerfile para incluir os entrypoints
echo "5. Atualizando Dockerfile..."

# Backup do Dockerfile original
cp "Dockerfile" "Dockerfile.backup"

# Adicionar cópia dos scripts ao Dockerfile se não existir
if ! grep -q "docker-entrypoint" Dockerfile; then
    # Adicionar antes da última linha
    sed -i '$i\
# Copiar scripts de entrypoint para o ambiente Docker\
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh\
COPY docker-entrypoint-qcluster.sh /usr/local/bin/docker-entrypoint-qcluster.sh\
RUN dos2unix /usr/local/bin/docker-entrypoint.sh /usr/local/bin/docker-entrypoint-qcluster.sh\
RUN chmod +x /usr/local/bin/docker-entrypoint.sh /usr/local/bin/docker-entrypoint-qcluster.sh\
' Dockerfile
fi

# Restaurar ENTRYPOINT e CMD se estiverem comentados
sed -i 's/^# *ENTRYPOINT/ENTRYPOINT/' Dockerfile
sed -i 's/^# *CMD/CMD/' Dockerfile

echo "Dockerfile atualizado com sucesso."

# 7. Parar containers existentes
echo "6. Parando containers existentes..."

docker-compose down -v 2>/dev/null || true

# 8. Construir imagens Docker
echo "7. Construindo imagens Docker..."

docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao construir as imagens Docker."
    exit 1
fi

echo "✅ Imagens Docker construídas com sucesso."

# 9. Iniciar serviços de banco de dados primeiro
echo "8. Iniciando serviços de banco de dados..."

docker-compose up -d postgres-django postgres redis

# Aguardar bancos de dados ficarem prontos
echo "Aguardando PostgreSQL ficar pronto..."
for i in {1..30}; do
    if docker-compose exec -T postgres-django pg_isready -U postgres &>/dev/null; then
        echo "✅ PostgreSQL Django pronto."
        break
    fi
    echo "Aguardando PostgreSQL Django... ($i/30)"
    sleep 2
done

echo "Aguardando segundo PostgreSQL ficar pronto..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U evolution &>/dev/null; then
        echo "✅ PostgreSQL Evolution pronto."
        break
    fi
    echo "Aguardando PostgreSQL Evolution... ($i/30)"
    sleep 2
done

echo "Aguardando Redis ficar pronto..."
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        echo "✅ Redis pronto."
        break
    fi
    echo "Aguardando Redis... ($i/30)"
    sleep 2
done

# 10. Executar migrações do Django
echo "9. Executando migrações do Django..."

# Resetar migrações: remover todos os arquivos (exceto __init__.py)
echo "Limpando arquivos de migrações existentes..."
find src/smart_core_assistant_painel/app/ui -type d -name migrations -prune -exec bash -c 'shopt -s nullglob; for f in "$1"/*; do [[ $(basename "$f") != "__init__.py" ]] && rm -f "$f"; done' _ {} \;

# Criar novas migrações antes de aplicar
docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py makemigrations
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao criar migrações do Django."
    exit 1
fi

docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate

if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao executar migrações do Django."
    exit 1
fi

echo "✅ Migrações do Django executadas com sucesso."

# 11. Coletar arquivos estáticos
echo "10. Coletando arquivos estáticos..."

docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput

if [ $? -ne 0 ]; then
    echo "AVISO: Falha ao coletar arquivos estáticos."
fi

# 12. Criar superusuário
echo "11. Criando superusuário..."

docker-compose run --rm django-app bash -c "
echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@example.com','123456')\" | uv run python src/smart_core_assistant_painel/app/ui/manage.py shell
"

if [ $? -ne 0 ]; then
    echo "AVISO: Falha ao criar superusuário."
fi

# 13. Iniciar todos os serviços
echo "12. Iniciando todos os serviços..."

docker-compose up -d

# 14. Verificar status dos serviços
echo "13. Verificando status dos serviços..."

sleep 10

# Verificar se os containers estão rodando
if ! docker-compose ps | grep -q "Up"; then
    echo "AVISO: Alguns containers podem não estar rodando corretamente."
    docker-compose ps
fi

echo ""
echo "=== Ambiente Docker configurado com sucesso! ==="
echo ""
echo "Serviços disponíveis:"
echo "🌐 Django App: http://localhost:8001"
echo "📊 Evolution API: http://localhost:8081" 
echo "🗄️  PostgreSQL Django: localhost:5435"
echo "🗄️  PostgreSQL Evolution: localhost:5432 (interno)"
echo "🔄 Redis: localhost:6380"
echo ""
echo "Para monitorar os logs:"
echo "docker-compose logs -f"
echo ""
echo "Para parar todos os serviços:"
echo "docker-compose down"
echo ""
echo "Usuário admin criado:"
echo "Username: admin"
echo "Password: 123456"
echo "Email: admin@example.com"
echo ""
echo "🎉 Ambiente pronto para desenvolvimento!"
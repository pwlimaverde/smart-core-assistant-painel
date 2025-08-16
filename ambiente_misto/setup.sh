#!/bin/bash

# Script unificado para configurar e iniciar o ambiente de desenvolvimento misto
# Este script combina todas as funcionalidades dos scripts individuais em ambiente_misto

set -e  # Exit on any error

echo "=== Configurando o ambiente de desenvolvimento misto ==="

# Verificar se estamos na raiz do projeto
if [ ! -f "pyproject.toml" ]; then
    echo "ERRO: Este script deve ser executado na raiz do projeto."
    exit 1
fi

# 1. Verificar arquivos de configuração necessários
echo "1. Verificando arquivos de configuração..."

if [ ! -f ".env" ] || [ ! -f "firebase_key.json" ]; then
    echo "ERRO: Antes de executar a criação do ambiente local, salve os arquivos .env e firebase_key.json na raiz do projeto."
    echo ""
    echo "Crie um arquivo .env com o seguinte conteúdo mínimo:"
    echo "
# Firebase Configuration (OBRIGATÓRIO)
GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json

# Django Configuration (OBRIGATÓRIO)
SECRET_KEY_DJANGO=sua-chave-secreta-django-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Evolution API Configuration (OBRIGATÓRIO)
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua-chave-evolution-api-aqui
EVOLUTION_API_GLOBAL_WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/

# Redis e PostgreSQL - Altere as portas se as padrões estiverem em uso
REDIS_PORT=6381
POSTGRES_PORT=5434

# PostgreSQL Configuration
POSTGRES_DB=smart_core_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost
"
    exit 1
fi

echo "Arquivos .env e firebase_key.json encontrados."

# 2. Mover firebase_key.json para o local correto
echo "2. Movendo firebase_key.json para o local correto..."

# Ler variável GOOGLE_APPLICATION_CREDENTIALS do .env
GAC_PATH=$(grep "^GOOGLE_APPLICATION_CREDENTIALS=" .env | cut -d'=' -f2 | tr -d ' ')

if [ -z "$GAC_PATH" ]; then
    echo "ERRO: A variável GOOGLE_APPLICATION_CREDENTIALS não está definida no arquivo .env."
    exit 1
fi

# Criar diretório se não existir
GAC_DIR=$(dirname "$GAC_PATH")
mkdir -p "$GAC_DIR"

# Mover arquivo se necessário
if [ "$(realpath firebase_key.json)" != "$(realpath "$GAC_PATH")" ]; then
    if [ -f "$GAC_PATH" ]; then
        echo "Aviso: O arquivo de destino '$GAC_PATH' já existe. Ele não será sobrescrito."
    else
        mv firebase_key.json "$GAC_PATH"
        echo "Arquivo 'firebase_key.json' movido para '$GAC_PATH'"
    fi
else
    echo "Arquivo 'firebase_key.json' já está no local correto."
fi

# 3. Configurar Git para ignorar alterações locais
echo "3. Configurando Git para ignorar alterações locais..."

# Garantir que o diretório .git/info exista
mkdir -p .git/info

# Adicionar regras ao .git/info/exclude
EXCLUDE_FILE=".git/info/exclude"
{
    echo ""
    echo "# Arquivos de configuração para o ambiente_misto"
    echo "/docker-compose.yml"
    echo "/Dockerfile"
    echo "/.gitignore"
    echo "/.env"
    echo "/src/smart_core_assistant_painel/app/ui/core/settings.py"
    echo "/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json"
} >> "$EXCLUDE_FILE"

# Arquivos para marcar com assume-unchanged
FILES_TO_ASSUME=(
    "Dockerfile"
    "docker-compose.yml"
    ".gitignore"
    "src/smart_core_assistant_painel/app/ui/core/settings.py"
)

# Limpar flags existentes e marcar arquivos
echo "Limpando flags 'assume-unchanged' existentes..."
git update-index --no-assume-unchanged "${FILES_TO_ASSUME[@]}" 2>/dev/null || true

echo "Marcando arquivos de configuração para serem ignorados localmente..."
git update-index --assume-unchanged "${FILES_TO_ASSUME[@]}" 2>/dev/null || true

echo "Configuração do Git concluída com sucesso."

# 4. Atualizar settings.py para usar PostgreSQL e Redis do Docker
echo "4. Atualizando settings.py..."

SETTINGS_PATH="src/smart_core_assistant_painel/app/ui/core/settings.py"

# Backup do arquivo original
cp "$SETTINGS_PATH" "${SETTINGS_PATH}.backup"

# Substituir configuração do banco de dados
sed -i '/^DATABASES = {/,/^}/c\
DATABASES = {\
    "default": {\
        "ENGINE": "django.db.backends.postgresql",\
        "NAME": os.getenv("POSTGRES_DB", "smart_core_db"),\
        "USER": os.getenv("POSTGRES_USER", "postgres"),\
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres123"),\
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),\
        "PORT": os.getenv("POSTGRES_PORT", "5434"),\
    }\
}' "$SETTINGS_PATH"

# Substituir configuração do cache
sed -i '/^CACHES = {/,/^}/c\
CACHES = {\
    "default": {\
        "BACKEND": "django_redis.cache.RedisCache",\
        "LOCATION": f"redis://127.0.0.1:{os.getenv("REDIS_PORT", "6381")}/1",\
        "OPTIONS": {\
            "CLIENT_CLASS": "django_redis.client.DefaultClient",\
        }\
    }\
}' "$SETTINGS_PATH"

echo "Arquivo settings.py atualizado com sucesso."

# 5. Atualizar docker-compose.yml para conter apenas os serviços de banco de dados
echo "5. Atualizando docker-compose.yml..."

PROJECT_NAME=$(basename "$(pwd)")

cat > docker-compose.yml << EOF
# Arquivo gerenciado pelo ambiente_misto
name: $PROJECT_NAME

services:
  postgres:
    image: postgres:13
    container_name: postgres_db
    environment:
      POSTGRES_DB: \${POSTGRES_DB:-smart_core_db}
      POSTGRES_USER: \${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-postgres123}
    ports:
      - "\${POSTGRES_PORT:-5434}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  redis:
    image: redis:6.2-alpine
    container_name: redis_cache
    ports:
      - "\${REDIS_PORT:-6381}:6379"
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
EOF

echo "Arquivo docker-compose.yml atualizado com sucesso."

# 6. Limpar Dockerfile
echo "6. Limpando Dockerfile..."

# Comentar linhas ENTRYPOINT e CMD
sed -i '/^\s*ENTRYPOINT\|^\s*CMD/s/^/# /' Dockerfile
echo "" >> Dockerfile
echo "# As linhas ENTRYPOINT e CMD foram comentadas pelo ambiente_misto." >> Dockerfile

echo "Arquivo Dockerfile atualizado com sucesso."

# 7. Iniciar containers
echo "7. Iniciando os containers (Postgres e Redis)..."

docker-compose --env-file ./.env up -d

echo ""
echo "=== Ambiente misto pronto! ==="
echo "Para iniciar a aplicação Django, execute o seguinte comando em outro terminal:"
echo "python src/smart_core_assistant_painel/app/ui/manage.py runserver 0.0.0.0:8000"
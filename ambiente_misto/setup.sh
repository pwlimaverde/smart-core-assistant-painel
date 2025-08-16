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

if [ ! -f ".env" ]; then
    echo "ERRO: Antes de executar a criação do ambiente local, salve o arquivo .env na raiz do projeto."
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
POSTGRES_PORT=5435

# PostgreSQL Configuration
POSTGRES_DB=smart_core_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost
"
    exit 1
fi

echo "Arquivo .env encontrado."

if [ ! -f "firebase_key.json" ]; then
    echo "ERRO: Antes de executar a criação do ambiente local, salve o arquivo firebase_key.json na raiz do projeto."
    echo ""
    echo "Obtenha o arquivo de credenciais do Firebase (service account key) e salve-o como firebase_key.json na raiz do projeto."
    echo "O script moverá automaticamente este arquivo para o diretório correto."
    echo ""
    exit 1
fi

echo "Arquivo firebase_key.json encontrado."

# Criar diretório para o arquivo firebase_key.json se não existir
FIREBASE_KEY_DIR="src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config"
mkdir -p "$FIREBASE_KEY_DIR"

# Mover firebase_key.json para o diretório correto
mv "firebase_key.json" "$FIREBASE_KEY_DIR/firebase_key.json"

echo "Arquivo firebase_key.json movido para $FIREBASE_KEY_DIR/firebase_key.json"

# 2. Configurar Git para ignorar alterações locais
echo "2. Configurando Git para ignorar alterações locais..."

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
    echo "/firebase_key.json"
    echo "/src/smart_core_assistant_painel/app/ui/core/settings.py"
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

# 3. Atualizar settings.py para usar PostgreSQL e Redis do Docker
echo "3. Atualizando settings.py..."

SETTINGS_PATH="src/smart_core_assistant_painel/app/ui/core/settings.py"

# Backup do arquivo original
cp "$SETTINGS_PATH" "${SETTINGS_PATH}.backup"

# Substituir configuração do banco de dados e cache
SETTINGS_PATH="src/smart_core_assistant_painel/app/ui/core/settings.py"

# Substituir HOST do PostgreSQL
sed -i 's/"HOST": os.getenv("POSTGRES_HOST", "postgres")/"HOST": os.getenv("POSTGRES_HOST", "localhost")/g' "$SETTINGS_PATH"

# Substituir PORT do PostgreSQL
sed -i 's/"PORT": os.getenv("POSTGRES_PORT", "5432")/"PORT": os.getenv("POSTGRES_PORT", "5435")/g' "$SETTINGS_PATH"

# Substituir configuração do cache Redis para usar cache em memória
sed -i 's/CACHES = {[^}]*}/CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}/g' "$SETTINGS_PATH"

echo "Arquivo settings.py atualizado com sucesso."

# 4. Atualizar docker-compose.yml para conter apenas os serviços de banco de dados
echo "4. Atualizando docker-compose.yml..."

PROJECT_NAME=$(basename "$(pwd)")

cat > docker-compose.yml << EOF
# Arquivo gerenciado pelo ambiente_misto
name: $PROJECT_NAME

services:
  postgres:
    image: postgres:14
    container_name: postgres_db
    environment:
      POSTGRES_DB: \${POSTGRES_DB:-smart_core_db}
      POSTGRES_USER: \${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-postgres123}
    ports:
      - "\${POSTGRES_PORT:-5435}:5432"
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

# 5. Limpar Dockerfile
echo "5. Limpando Dockerfile..."

# Comentar linhas ENTRYPOINT e CMD
sed -i '/^\s*ENTRYPOINT\|^\s*CMD/s/^/# /' Dockerfile
echo "" >> Dockerfile
echo "# As linhas ENTRYPOINT e CMD foram comentadas pelo ambiente_misto." >> Dockerfile

echo "Arquivo Dockerfile atualizado com sucesso."

# 6. Iniciar containers
echo "6. Iniciando os containers (Postgres e Redis)..."

docker-compose down -v
docker-compose up -d

# 7. Instalar dependências Python necessárias
echo "7. Instalando dependências Python necessárias..."

pip install psycopg2-binary
pip install firebase-admin
pip install langchain-ollama
pip install django-redis
pip install redis==3.5.3
pip install markdown

# 8. Apagar migrações do Django
echo "8. Apagando migrações do Django..."

# Navegar para o diretório da aplicação
cd src/smart_core_assistant_painel/app/ui

# Apagar arquivos de migração (exceto __init__.py)
find ../../../modules -name 'migrations' -type d -exec sh -c 'cd "{}" && ls *.py 2>/dev/null | grep -v __init__.py | xargs -r rm && echo > __init__.py' \;

# Voltar ao diretório raiz
cd ../../../../..

# 9. Aplicar migrações do Django
echo "9. Aplicando migrações do Django..."

export PYTHONPATH=$(pwd)/src
python src/smart_core_assistant_painel/app/ui/manage.py migrate

# 10. Criar superusuário
echo "10. Criando superusuário admin..."

export PYTHONPATH=$(pwd)/src
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', '123456')" | python src/smart_core_assistant_painel/app/ui/manage.py shell

echo ""
echo "=== Ambiente misto pronto! ==="
echo "Para iniciar a aplicação Django, execute o seguinte comando em outro terminal:"
echo "python src/smart_core_assistant_painel/app/ui/manage.py runserver 0.0.0.0:8000"
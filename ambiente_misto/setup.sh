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
    echo "ERRO: Arquivo .env não encontrado na raiz do projeto."
    echo "Coloque o arquivo .env manualmente antes de executar este setup."
    exit 1
fi

echo "Arquivo .env encontrado."

# Verificar se GOOGLE_APPLICATION_CREDENTIALS está definido no .env
FIREBASE_PATH=$(grep "^GOOGLE_APPLICATION_CREDENTIALS=" .env | cut -d'=' -f2)
if [ -z "$FIREBASE_PATH" ]; then
    echo "ERRO: A variável GOOGLE_APPLICATION_CREDENTIALS não está definida no arquivo .env"
    echo "Defina GOOGLE_APPLICATION_CREDENTIALS apontando para o caminho do firebase_key.json"
    exit 1
fi

# Verificar existência do arquivo de credenciais do Firebase (deve ser colocado manualmente)
if [ ! -f "$FIREBASE_PATH" ]; then
    echo "ERRO: Arquivo de credenciais do Firebase não encontrado em: $FIREBASE_PATH"
    echo "Coloque o arquivo firebase_key.json manualmente no caminho configurado em GOOGLE_APPLICATION_CREDENTIALS no .env"
    exit 1
fi

# Extrair diretório do caminho do firebase_key.json
FIREBASE_KEY_DIR=$(dirname "$FIREBASE_PATH")
mkdir -p "$FIREBASE_KEY_DIR"


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
    # Ignorar novas migrações locais (não rastrear futuras criações)
    echo "/src/smart_core_assistant_painel/app/ui/*/migrations/"
    echo "/src/smart_core_assistant_painel/app/ui/*/migrations/*.py"
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

# Marcar arquivos rastreados de migrations como assume-unchanged (local)
echo "Marcando arquivos de migrações (rastreados) como assume-unchanged..."
while IFS= read -r f; do
  git update-index --no-assume-unchanged "$f" 2>/dev/null || true
  git update-index --assume-unchanged "$f" 2>/dev/null || true
done < <(git ls-files 'src/smart_core_assistant_painel/app/ui/*/migrations/*' 2>/dev/null)

# Marcar arquivos de configuração para serem ignorados localmente
echo "Marcando arquivos de configuração para serem ignorados localmente..."
git update-index --assume-unchanged "${FILES_TO_ASSUME[@]}" 2>/dev/null || true

# Opcional: aconselhar o uso de update-index caso novas migrações sejam criadas e rastreadas
# git update-index --assume-unchanged caminho/do/arquivo.py

echo "Configuração do Git concluída com sucesso."

# 3. Atualizar settings.py para usar PostgreSQL local e cache em memória
echo "3. Atualizando settings.py..."

SETTINGS_PATH="src/smart_core_assistant_painel/app/ui/core/settings.py"

# Backup do arquivo original
cp "$SETTINGS_PATH" "${SETTINGS_PATH}.backup"

# Substituir HOST do PostgreSQL para localhost (ambiente misto)
sed -i 's/"HOST": os.getenv("POSTGRES_HOST", "postgres") /"HOST": os.getenv("POSTGRES_HOST", "localhost") /g' "$SETTINGS_PATH"

# Substituir PORT do PostgreSQL para 5436 (padrão ambiente misto)  
sed -i 's/"PORT": os.getenv("POSTGRES_PORT", "5432") /"PORT": os.getenv("POSTGRES_PORT", "5436") /g' "$SETTINGS_PATH"

# Substituir configuração do cache para usar Redis (ambiente misto)
python3 -c "
import re, os
with open('$SETTINGS_PATH', 'r', encoding='utf-8') as f:
    content = f.read()

cache_config = '''CACHES = {
    \"default\": {
        # Configuração Redis para ambiente_misto
        # Se preferir cache em memória, altere para:
        # \"BACKEND\": \"django.core.cache.backends.locmem.LocMemCache\",
        # \"LOCATION\": \"unique-snowflake\",
        \"BACKEND\": \"django_redis.cache.RedisCache\",
        \"LOCATION\": \"redis://\" + os.getenv(\"REDIS_HOST\", \"localhost\") + \":\" + os.getenv(\"REDIS_PORT\", \"6382\") + \"/1\",
        \"OPTIONS\": {
            \"CLIENT_CLASS\": \"django_redis.client.DefaultClient\",
        }
    }
}'''

content = re.sub(r'CACHES\s*=\s*\{[^}]*\}', cache_config, content, flags=re.DOTALL)

with open('$SETTINGS_PATH', 'w', encoding='utf-8') as f:
    f.write(content)
"

echo "Arquivo settings.py atualizado com sucesso."

# 4. Atualizar docker-compose.yml para conter apenas os serviços de banco de dados
echo "4. Atualizando docker-compose.yml..."

PROJECT_NAME=$(basename "$(pwd)")

cat > docker-compose.yml << EOF
# Arquivo gerenciado pelo ambiente_misto
name: ${PROJECT_NAME}-amb-misto

services:
  postgres:
    image: postgres:14
    container_name: postgres_db
    environment:
      POSTGRES_DB: ">${POSTGRES_DB:-smart_core_db}"
      POSTGRES_USER: ">${POSTGRES_USER:-postgres}"
      POSTGRES_PASSWORD: ">${POSTGRES_PASSWORD:-postgres123}"
    ports:
      - "">${POSTGRES_PORT:-5436}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  redis:
    image: redis:6.2-alpine
    container_name: redis_cache
    ports:
      - "">${REDIS_PORT:-6382}:6379"
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
sed -i '/^\s*ENTRYPOINT|^\s*CMD/s/^/# /' Dockerfile
echo "" >> Dockerfile
echo "# As linhas ENTRYPOINT e CMD foram comentadas pelo ambiente_misto." >> Dockerfile

echo "Arquivo Dockerfile atualizado com sucesso."

# 6. Iniciar containers
echo "6. Iniciando os containers (Postgres e Redis)..."

docker rm -f postgres_db redis_cache || true
docker compose down -v
docker compose up -d

# 7. Instalar dependências Python necessárias
echo "7. Instalando dependências Python necessárias..."

# O comando uv sync --dev foi removido para evitar o downgrade do python-dotenv

# 8. Resetar migrações do Django
echo "8. Resetando migrações do Django..."

# Remover arquivos de migração exceto __init__.py
find src/smart_core_assistant_painel/app/ui -type d -name migrations -prune -exec bash -c 'shopt -s nullglob; for f in "$1"/*; do [[ $(basename "$f") != "__init__.py" ]] && rm -f "$f"; done' _ {} \;

# 9. Criar e aplicar novas migrações do Django
echo "9. Criando e aplicando novas migrações do Django..."

.venv/bin/python -m dotenv.cli run uv run task makemigrations || { echo "Erro ao criar migrações do Django"; exit 1; }
.venv/bin/python -m dotenv.cli run uv run task migrate || { echo "Erro ao aplicar migrações do Django"; exit 1; }

# 10. Criar superusuário
echo "10. Criando superusuário admin..."

# Comando idempotente: cria apenas se não existir
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@example.com','123456')" | .venv/bin/python -m dotenv.cli run uv run task shell
if [ $? -ne 0 ]; then
    echo "Erro ao criar superusuário"
    exit 1
fi

echo ""
echo "=== Ambiente misto pronto! ==="
echo "Para iniciar a aplicação Django, execute o seguinte comando em outro terminal:"
echo "uv run task start"

echo ""
echo "A aplicação estará disponível em http://localhost:8000"

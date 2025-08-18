@echo off
REM Script unificado para configurar e iniciar o ambiente de desenvolvimento misto
REM Este script combina todas as funcionalidades dos scripts individuais em ambiente_misto

echo === Configurando o ambiente de desenvolvimento misto ===

REM Verificar se estamos na raiz do projeto
if not exist "pyproject.toml" (
    echo ERRO: Este script deve ser executado na raiz do projeto.
    exit /b 1
)

REM 1. Verificar arquivos de configuração necessários
echo 1. Verificando arquivos de configuração...

if not exist ".env" (
    echo ERRO: Antes de executar a criação do ambiente local, salve o arquivo .env na raiz do projeto.
    echo.
    echo Crie um arquivo .env com o seguinte conteúdo mínimo:
    echo.
    echo # Firebase Configuration ^(OBRIGATÓRIO^)
    echo GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
    echo.
    echo # Django Configuration ^(OBRIGATÓRIO^)
    echo SECRET_KEY_DJANGO=sua-chave-secreta-django-aqui
    echo DJANGO_DEBUG=True
    echo DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
    echo.
    echo # Evolution API Configuration ^(OBRIGATÓRIO^)
    echo EVOLUTION_API_URL=http://localhost:8080
    echo EVOLUTION_API_KEY=sua-chave-evolution-api-aqui
    echo EVOLUTION_API_GLOBAL_WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/
    echo.
    echo # Redis e PostgreSQL - Altere as portas se as padrões estiverem em uso
    echo REDIS_PORT=6382
    echo POSTGRES_PORT=5436
    echo.
    echo # PostgreSQL Configuration
    echo POSTGRES_DB=smart_core_db
    echo POSTGRES_USER=postgres
    echo POSTGRES_PASSWORD=postgres123
    echo POSTGRES_HOST=localhost
    echo.
    exit /b 1
)

echo Arquivo .env encontrado.

REM Obter caminho do GOOGLE_APPLICATION_CREDENTIALS do .env
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"GOOGLE_APPLICATION_CREDENTIALS=" .env`) do set FIREBASE_PATH=%%B
if not defined FIREBASE_PATH (
    echo ERRO: A variavel GOOGLE_APPLICATIONS_CREDENTIALS nao esta definida no arquivo .env
    echo Adicione a linha: GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
    exit /b 1
)

REM Extrair diretorio do caminho informado
for %%I in ("%FIREBASE_PATH%") do set FIREBASE_KEY_DIR=%%~dpI
if not exist "%FIREBASE_KEY_DIR%" mkdir "%FIREBASE_KEY_DIR%"

REM 2. Criar credenciais Firebase usando FIREBASE_KEY_JSON_CONTENT
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"FIREBASE_KEY_JSON_CONTENT=" .env`) do set FIREBASE_CONTENT=%%B

if not defined FIREBASE_CONTENT (
    echo ERRO: Variavel FIREBASE_KEY_JSON_CONTENT nao encontrada ou vazia no arquivo .env
    echo Por favor, adicione a variavel FIREBASE_KEY_JSON_CONTENT no .env com o conteudo JSON do Firebase
    echo Exemplo: FIREBASE_KEY_JSON_CONTENT={"type":"service_account","project_id":"seu-projeto",...}
    exit /b 1
)

echo Criando firebase_key.json a partir da variavel FIREBASE_KEY_JSON_CONTENT...
mkdir "%FIREBASE_KEY_DIR%" 2>nul
echo %FIREBASE_CONTENT% > "%FIREBASE_PATH%"
echo Arquivo firebase_key.json criado com sucesso em %FIREBASE_PATH%

REM 2. Configurar Git para ignorar alterações locais
echo 2. Configurando Git para ignorar alterações locais...

REM Garantir que o diretório .git/info exista
if not exist ".git\info" mkdir ".git\info"

REM Adicionar regras ao .git/info/exclude
echo. >> .git\info\exclude
echo # Arquivos de configuração para o ambiente_misto >> .git\info\exclude
echo /docker-compose.yml >> .git\info\exclude
echo /Dockerfile >> .git\info\exclude
echo /.gitignore >> .git\info\exclude
echo /.env >> .git\info\exclude
echo /firebase_key.json >> .git\info\exclude
echo /src/smart_core_assistant_painel/app/ui/core/settings.py >> .git\info\exclude
REM Ignorar novas migrações locais (não rastrear futuras criações)
echo /src/smart_core_assistant_painel/app/ui/*/migrations/ >> .git\info\exclude
echo /src/smart_core_assistant_painel/app/ui/*/migrations/*.py >> .git\info\exclude

REM Arquivos para marcar com assume-unchanged
set FILES_TO_ASSUME=Dockerfile docker-compose.yml .gitignore src/smart_core_assistant_painel/app/ui/core/settings.py

REM Limpar flags existentes e marcar arquivos
echo Limpando flags 'assume-unchanged' existentes...
git update-index --no-assume-unchanged %FILES_TO_ASSUME% 2>nul

echo Marcando arquivos de configuração para serem ignorados localmente...
git update-index --assume-unchanged %FILES_TO_ASSUME% 2>nul

REM Marcar arquivos de migração rastreados como assume-unchanged (local)
echo Marcando arquivos de migracoes (rastreados) como assume-unchanged...
for /f "usebackq delims=" %%F in (`git ls-files src/smart_core_assistant_painel/app/ui/*/migrations/* 2^>nul`) do (
    git update-index --no-assume-unchanged "%%F" 2>nul
    git update-index --assume-unchanged "%%F" 2>nul
)

echo Configuração do Git concluída com sucesso.

REM 3. Atualizar settings.py para usar PostgreSQL local e cache em memória
echo 3. Atualizando settings.py...

set SETTINGS_PATH=src/smart_core_assistant_painel/app/ui/core/settings.py

REM Backup do arquivo original
copy "src\smart_core_assistant_painel\app\ui\core\settings.py" "src\smart_core_assistant_painel\app\ui\core\settings.py.backup" >nul

REM Substituir HOST do PostgreSQL para localhost (ambiente misto)
python -c "import re; content = open('%SETTINGS_PATH%', 'r', encoding='utf-8').read(); content = re.sub(r'\"HOST\": os\.getenv\(\"POSTGRES_HOST\", \"postgres\"\)', '"HOST": os.getenv("POSTGRES_HOST", "localhost")', content); open('%SETTINGS_PATH%', 'w', encoding='utf-8').write(content)"
if %errorlevel% neq 0 (
    echo Erro ao atualizar o HOST do PostgreSQL no settings.py
    exit /b 1
)

REM Substituir PORT do PostgreSQL para 5436 (padrão ambiente misto)
python -c "import re; content = open('%SETTINGS_PATH%', 'r', encoding='utf-8').read(); content = re.sub(r'\"PORT\": os\.getenv\(\"POSTGRES_PORT\", \"5432\"\)', '"PORT": os.getenv("POSTGRES_PORT", "5436")', content); open('%SETTINGS_PATH%', 'w', encoding='utf-8').write(content)"
if %errorlevel% neq 0 (
    echo Erro ao atualizar a PORT do PostgreSQL no settings.py
    exit /b 1
)

REM Substituir configuração do cache para usar Redis (ambiente misto)
python -c "import re, os; content = open('%SETTINGS_PATH%', 'r', encoding='utf-8').read(); cache_config = '''CACHES = {\n    \"default\": {\n        \"BACKEND\": \"django_redis.cache.RedisCache\",\n        \"LOCATION\": \"redis://\" + os.getenv(\"REDIS_HOST\", \"localhost\") + \":\" + os.getenv(\"REDIS_PORT\", \"6382\") + \"/1\",\n        \"OPTIONS\": {\n            \"CLIENT_CLASS\": \"django_redis.client.DefaultClient\",\n        },\n        \"TIMEOUT\": 300,\n    }\n}'''; content = re.sub(r'CACHES\s*=\s*\{(?:[^\{\}]*|{[^\{\}]*})*\}', cache_config, content, flags=re.DOTALL); open('%SETTINGS_PATH%', 'w', encoding='utf-8').write(content)"
if %errorlevel% neq 0 (
    echo Erro ao atualizar a configuração de CACHE no settings.py
    exit /b 1
)

echo Arquivo settings.py atualizado com sucesso.

REM 4. Atualizar docker-compose.yml para conter apenas os serviços de banco de dados
echo 4. Atualizando docker-compose.yml...

REM Obter nome do projeto (nome do diretório atual)
for %%f in (.) do set PROJECT_NAME=%%~nxf

REM Criar novo docker-compose.yml
(
    echo # Arquivo gerenciado pelo ambiente_misto
    echo name: %PROJECT_NAME%-amb-misto
    echo.
    echo services:
    echo   postgres:
    echo     image: postgres:14
    echo     container_name: postgres_db
    echo     environment:
    echo       POSTGRES_DB: ${POSTGRES_DB:-smart_core_db}
    echo       POSTGRES_USER: ${POSTGRES_USER:-postgres}
    echo       POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}
    echo     ports:
    echo       - "${POSTGRES_PORT:-5436}:5432"
    echo     volumes:
    echo       - postgres_data:/var/lib/postgresql/data
    echo     networks:
    echo       - app-network
    echo.
    echo   redis:
    echo     image: redis:6.2-alpine
    echo     container_name: redis_cache
    echo     ports:
    echo       - "${REDIS_PORT:-6382}:6379"
    echo     networks:
    echo       - app-network
    echo.
    echo volumes:
    echo   postgres_data:
    echo.
    echo networks:
    echo   app-network:
    echo     driver: bridge
) > docker-compose.yml

echo Arquivo docker-compose.yml atualizado com sucesso.

REM 5. Limpar Dockerfile
echo 5. Limpando Dockerfile...

REM Comentar linhas ENTRYPOINT e CMD usando Python
python -c "import re; content = open('Dockerfile', 'r', encoding='utf-8').read(); content = re.sub(r'^\s*ENTRYPOINT', '# ENTRYPOINT', content, flags=re.MULTILINE); content = re.sub(r'^\s*CMD', '# CMD', content, flags=re.MULTILINE); open('Dockerfile', 'w', encoding='utf-8').write(content)"

echo. >> Dockerfile
echo # As linhas ENTRYPOINT e CMD foram comentadas pelo ambiente_misto. >> Dockerfile

echo Arquivo Dockerfile atualizado com sucesso.

REM 6. Iniciar containers
echo 6. Iniciando os containers (Postgres e Redis)...

docker rm -f postgres_db redis_cache || true
docker compose down -v
docker compose up -d

REM 7. Instalar dependências Python necessárias
echo 7. Instalando dependências Python necessárias...

REM O comando uv sync --dev foi removido para evitar o downgrade do python-dotenv

REM 8. Resetar migrações do Django
echo 8. Resetando migrações do Django...

REM Apagar arquivos de migração (exceto __init__.py)
for /d %%d in (src\smart_core_assistant_painel\app\ui\*) do (
    if exist "%%d\migrations" (
        for %%f in ("%%d\migrations\*") do (
            if not "%%~nxf"=="__init__.py" (
                del "%%f" 2>nul
            )
        )
    )
)

REM 9. Criar e aplicar novas migrações
echo 9. Criando e aplicando novas migrações do Django...

.venv\Scripts\python.exe -m dotenv.cli run uv run task makemigrations
if %errorlevel% neq 0 (
    echo Erro ao criar migrações do Django
    exit /b 1
)

.venv\Scripts\python.exe -m dotenv.cli run uv run task migrate
if %errorlevel% neq 0 (
    echo Erro ao aplicar migrações do Django
    exit /b 1
)

REM 10. Criar superusuário
echo 10. Criando superusuário admin...

REM Comando idempotente: cria apenas se não existir
echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@example.com','123456') | .venv\Scripts\python.exe -m dotenv.cli run uv run task shell
if %errorlevel% neq 0 (
    echo Erro ao criar superusuário
    exit /b 1
)

echo.

echo === Ambiente misto pronto! ===
echo Para iniciar a aplicação Django, execute o seguinte comando em outro terminal:

echo uv run task start

echo.

A aplicação estará disponível em http://localhost:8000

pause

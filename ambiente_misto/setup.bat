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
    echo ERRO: Antes de executar a criação do ambiente local, salve os arquivos .env e firebase_key.json na raiz do projeto.
    echo.
    echo Crie um arquivo .env com o seguinte conteúdo mínimo:
    echo.
    echo # Firebase Configuration (OBRIGATÓRIO)
    echo GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
    echo.
    echo # Django Configuration (OBRIGATÓRIO)
    echo SECRET_KEY_DJANGO=sua-chave-secreta-django-aqui
    echo DJANGO_DEBUG=True
    echo DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
    echo.
    echo # Evolution API Configuration (OBRIGATÓRIO)
    echo EVOLUTION_API_URL=http://localhost:8080
    echo EVOLUTION_API_KEY=sua-chave-evolution-api-aqui
    echo EVOLUTION_API_GLOBAL_WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/
    echo.
    echo # Redis e PostgreSQL - Altere as portas se as padrões estiverem em uso
    echo REDIS_PORT=6381
    echo POSTGRES_PORT=5434
    echo.
    echo # PostgreSQL Configuration
    echo POSTGRES_DB=smart_core_db
    echo POSTGRES_USER=postgres
    echo POSTGRES_PASSWORD=postgres123
    echo POSTGRES_HOST=localhost
    echo.
    exit /b 1
)

if not exist "firebase_key.json" (
    echo ERRO: Antes de executar a criação do ambiente local, salve os arquivos .env e firebase_key.json na raiz do projeto.
    echo.
    echo Crie um arquivo .env com o seguinte conteúdo mínimo:
    echo.
    echo # Firebase Configuration (OBRIGATÓRIO)
    echo GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
    echo.
    echo # Django Configuration (OBRIGATÓRIO)
    echo SECRET_KEY_DJANGO=sua-chave-secreta-django-aqui
    echo DJANGO_DEBUG=True
    echo DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
    echo.
    echo # Evolution API Configuration (OBRIGATÓRIO)
    echo EVOLUTION_API_URL=http://localhost:8080
    echo EVOLUTION_API_KEY=sua-chave-evolution-api-aqui
    echo EVOLUTION_API_GLOBAL_WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/
    echo.
    echo # Redis e PostgreSQL - Altere as portas se as padrões estiverem em uso
    echo REDIS_PORT=6381
    echo POSTGRES_PORT=5434
    echo.
    echo # PostgreSQL Configuration
    echo POSTGRES_DB=smart_core_db
    echo POSTGRES_USER=postgres
    echo POSTGRES_PASSWORD=postgres123
    echo POSTGRES_HOST=localhost
    echo.
    exit /b 1
)

echo Arquivos .env e firebase_key.json encontrados.

REM 2. Mover firebase_key.json para o local correto
echo 2. Movendo firebase_key.json para o local correto...

REM Ler variável GOOGLE_APPLICATION_CREDENTIALS do .env
for /f "tokens=2 delims==" %%a in ('findstr "^GOOGLE_APPLICATION_CREDENTIALS=" .env') do set GAC_PATH=%%a

if "%GAC_PATH%"=="" (
    echo ERRO: A variável GOOGLE_APPLICATION_CREDENTIALS não está definida no arquivo .env.
    exit /b 1
)

REM Remover possíveis aspas
set GAC_PATH=%GAC_PATH:"=%

REM Criar diretório se não existir
for %%f in ("%GAC_PATH%") do set GAC_DIR=%%~dpf
if not exist "%GAC_DIR%" mkdir "%GAC_DIR%"

REM Mover arquivo se necessário
for %%f in ("%GAC_PATH%") do set GAC_FULL_PATH=%%~ff
for %%f in ("firebase_key.json") do set FB_FULL_PATH=%%~ff

if /i not "%GAC_FULL_PATH%"=="%FB_FULL_PATH%" (
    if exist "%GAC_PATH%" (
        echo Aviso: O arquivo de destino '%GAC_PATH%' já existe. Ele não será sobrescrito.
    ) else (
        move "firebase_key.json" "%GAC_PATH%"
        echo Arquivo 'firebase_key.json' movido para '%GAC_PATH%'
    )
) else (
    echo Arquivo 'firebase_key.json' já está no local correto.
)

REM 3. Configurar Git para ignorar alterações locais
echo 3. Configurando Git para ignorar alterações locais...

REM Garantir que o diretório .git/info exista
if not exist ".git\info" mkdir ".git\info"

REM Adicionar regras ao .git/info/exclude
echo. >> .git\info\exclude
echo # Arquivos de configuração para o ambiente_misto >> .git\info\exclude
echo /docker-compose.yml >> .git\info\exclude
echo /Dockerfile >> .git\info\exclude
echo /.gitignore >> .git\info\exclude
echo /.env >> .git\info\exclude
echo /src/smart_core_assistant_painel/app/ui/core/settings.py >> .git\info\exclude
echo /src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json >> .git\info\exclude

REM Arquivos para marcar com assume-unchanged
set FILES_TO_ASSUME=Dockerfile docker-compose.yml .gitignore src/smart_core_assistant_painel/app/ui/core/settings.py

REM Limpar flags existentes e marcar arquivos
echo Limpando flags 'assume-unchanged' existentes...
git update-index --no-assume-unchanged %FILES_TO_ASSUME% 2>nul

echo Marcando arquivos de configuração para serem ignorados localmente...
git update-index --assume-unchanged %FILES_TO_ASSUME% 2>nul

echo Configuração do Git concluída com sucesso.

REM 4. Atualizar settings.py para usar PostgreSQL e Redis do Docker
echo 4. Atualizando settings.py...

set SETTINGS_PATH=src\smart_core_assistant_painel\app\ui\core\settings.py

REM Backup do arquivo original
copy "%SETTINGS_PATH%" "%SETTINGS_PATH%.backup" >nul

REM Substituir configuração do banco de dados
powershell -Command "(gc '%SETTINGS_PATH%') -replace '(?s)^DATABASES = \{.*?^\}', 'DATABASES = {`n    \"default\": {`n        \"ENGINE\": \"django.db.backends.postgresql\",`n        \"NAME\": os.getenv(\"POSTGRES_DB\", \"smart_core_db\"),`n        \"USER\": os.getenv(\"POSTGRES_USER\", \"postgres\"),`n        \"PASSWORD\": os.getenv(\"POSTGRES_PASSWORD\", \"postgres123\"),`n        \"HOST\": os.getenv(\"POSTGRES_HOST\", \"localhost\"),`n        \"PORT\": os.getenv(\"POSTGRES_PORT\", \"5434\"),`n    }`n}' | Out-File -encoding UTF8 '%SETTINGS_PATH%'"

REM Substituir configuração do cache
powershell -Command "(gc '%SETTINGS_PATH%') -replace '(?s)^CACHES = \{.*?^\}', 'CACHES = {`n    \"default\": {`n        \"BACKEND\": \"django_redis.cache.RedisCache\",`n        \"LOCATION\": f\"redis://127.0.0.1:{os.getenv(`\"REDIS_PORT`\", `\"6381`\")}/1\",`n        \"OPTIONS\": {`n            \"CLIENT_CLASS\": \"django_redis.client.DefaultClient\",`n        }`n    }`n}' | Out-File -encoding UTF8 '%SETTINGS_PATH%'"

echo Arquivo settings.py atualizado com sucesso.

REM 5. Atualizar docker-compose.yml para conter apenas os serviços de banco de dados
echo 5. Atualizando docker-compose.yml...

REM Obter nome do projeto (nome do diretório atual)
for %%f in (.) do set PROJECT_NAME=%%~nxf

REM Criar novo docker-compose.yml
(
echo # Arquivo gerenciado pelo ambiente_misto
echo name: %PROJECT_NAME%
echo.
echo services:
echo   postgres:
echo     image: postgres:13
echo     container_name: postgres_db
echo     environment:
echo       POSTGRES_DB: ${POSTGRES_DB:-smart_core_db}
echo       POSTGRES_USER: ${POSTGRES_USER:-postgres}
echo       POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}
echo     ports:
echo       - "${POSTGRES_PORT:-5434}:5432"
echo     volumes:
echo       - postgres_data:/var/lib/postgresql/data
echo     networks:
echo       - app-network
echo.
echo   redis:
echo     image: redis:6.2-alpine
echo     container_name: redis_cache
echo     ports:
echo       - "${REDIS_PORT:-6381}:6379"
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

REM 6. Limpar Dockerfile
echo 6. Limpando Dockerfile...

REM Comentar linhas ENTRYPOINT e CMD
powershell -Command "(gc Dockerfile) -replace '^\s*ENTRYPOINT', '# ENTRYPOINT' | Out-File -encoding UTF8 Dockerfile"
powershell -Command "(gc Dockerfile) -replace '^\s*CMD', '# CMD' | Out-File -encoding UTF8 Dockerfile"
echo. >> Dockerfile
echo # As linhas ENTRYPOINT e CMD foram comentadas pelo ambiente_misto. >> Dockerfile

echo Arquivo Dockerfile atualizado com sucesso.

REM 7. Iniciar containers
echo 7. Iniciando os containers (Postgres e Redis)...

docker-compose --env-file ./.env up -d

echo.
echo === Ambiente misto pronto! ===
echo Para iniciar a aplicação Django, execute o seguinte comando em outro terminal:
echo python src\smart_core_assistant_painel\app\ui\manage.py runserver 0.0.0.0:8000

pause
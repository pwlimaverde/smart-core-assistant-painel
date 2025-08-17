@echo off
chcp 65001
setlocal EnableDelayedExpansion

REM ================================================================
REM Script unificado para configurar e iniciar o ambiente Docker (Windows)
REM Este script inclui todos os arquivos necessarios inline, sem dependencias externas
REM ================================================================

REM Verificar se estamos na raiz do projeto
if not exist "pyproject.toml" (
    echo ERRO: Este script deve ser executado na raiz do projeto.
    exit /b 1
)

REM 1. Verificar pre-requisitos
call :section "1. Verificando pre-requisitos..."

where docker >nul 2>nul
if errorlevel 1 (
    echo ERRO: Docker nao esta instalado ou nao esta no PATH.
    echo Instale o Docker Desktop e tente novamente.
    exit /b 1
)

REM Detectar versao do Docker Compose
set "COMPOSE_CMD="
where docker-compose >nul 2>nul
if not errorlevel 1 (
    set "COMPOSE_CMD=docker-compose"
) else (
    docker compose version >nul 2>nul
    if not errorlevel 1 (
        set "COMPOSE_CMD=docker compose"
    ) else (
        echo ERRO: Docker Compose nao esta instalado ou nao esta no PATH.
        echo Instale Docker Desktop ou Docker Compose standalone e tente novamente.
        exit /b 1
    )
)

echo Docker Compose encontrado: %COMPOSE_CMD%

docker info >nul 2>nul
if errorlevel 1 (
    echo ERRO: Docker nao esta rodando. Inicie o Docker Desktop e tente novamente.
    exit /b 1
)

echo Docker e Docker Compose encontrados e funcionando.

REM 2. Verificar arquivos de configuracao
call :section "2. Verificando arquivos de configuracao..."

if not exist ".env" (
    echo ERRO: Antes de executar a criacao do ambiente Docker, salve o arquivo .env na raiz do projeto.
    echo.
    echo Copie o arquivo .env.example do ambiente_docker e configure suas variaveis:
    echo copy ambiente_docker\.env.example .env
    echo.
    echo Configure especialmente as seguintes variaveis obrigatorias:
    echo - SECRET_KEY_DJANGO
    echo - EVOLUTION_API_KEY
    echo - FIREBASE_KEY_JSON_CONTENT
    echo.
    exit /b 1
)

echo Arquivo .env encontrado.

REM 3. Processar credenciais Firebase
set "FIREBASE_PATH=src\smart_core_assistant_painel\modules\initial_loading\utils\keys\firebase_config\firebase_key.json"
for %%I in ("%FIREBASE_PATH%") do set "FIREBASE_KEY_DIR=%%~dpI"
if not exist "%FIREBASE_KEY_DIR%" (
    mkdir "%FIREBASE_KEY_DIR%"
)

for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"FIREBASE_KEY_JSON_CONTENT=" .env') do set "FIREBASE_CONTENT=%%B"
if not defined FIREBASE_CONTENT (
    echo ERRO: Variavel FIREBASE_KEY_JSON_CONTENT nao encontrada no arquivo .env
    echo Por favor, adicione a variavel FIREBASE_KEY_JSON_CONTENT no .env com o conteudo JSON do Firebase
    echo Exemplo: FIREBASE_KEY_JSON_CONTENT={"type":"service_account","project_id":"seu-projeto",...}
    exit /b 1
)

echo Criando firebase_key.json a partir da variavel FIREBASE_KEY_JSON_CONTENT...
echo %FIREBASE_CONTENT%> "%FIREBASE_PATH%"

echo Arquivo firebase_key.json criado com sucesso em %FIREBASE_PATH%

REM 4. Criar docker-compose.yml
call :section "3. Criando docker-compose.yml..."

echo services:> docker-compose.yml
echo   # Aplicacao Django para desenvolvimento>> docker-compose.yml
echo   django-app:>> docker-compose.yml
echo     build:>> docker-compose.yml
echo       context: .>> docker-compose.yml
echo       dockerfile: Dockerfile>> docker-compose.yml
echo     restart: unless-stopped>> docker-compose.yml
echo     ports:>> docker-compose.yml
echo       - "8001:8000">> docker-compose.yml
echo     environment:>> docker-compose.yml
echo       - DJANGO_SETTINGS_MODULE=smart_core_assistant_painel.app.ui.core.settings>> docker-compose.yml
echo       - DJANGO_DEBUG=True>> docker-compose.yml
echo       - SECRET_KEY_DJANGO=temp-secret-key-for-initial-startup-will-be-replaced-by-firebase-remote-config>> docker-compose.yml
echo       - POSTGRES_DB=smart_core_db>> docker-compose.yml
echo       - POSTGRES_USER=postgres>> docker-compose.yml
echo       - POSTGRES_PASSWORD=postgres123>> docker-compose.yml
echo       - POSTGRES_HOST=postgres-django>> docker-compose.yml
echo       - POSTGRES_PORT=5432>> docker-compose.yml
echo       - GOOGLE_APPLICATION_CREDENTIALS=/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json>> docker-compose.yml
echo       # Configuracao para acesso ao Ollama local>> docker-compose.yml
echo       - OLLAMA_HOST=host.docker.internal>> docker-compose.yml
echo       - OLLAMA_PORT=11434>> docker-compose.yml
echo       # Variaveis dinamicas serao configuradas pelo start_services>> docker-compose.yml
echo       # SECRET_KEY_DJANGO, OPENAI_API_KEY, GROQ_API_KEY, etc. vem do Firebase Remote Config>> docker-compose.yml
echo     volumes:>> docker-compose.yml
echo       # Mount source code for hot reload>> docker-compose.yml
echo       - ./src:/app/src>> docker-compose.yml
echo       - ./tests:/app/tests>> docker-compose.yml
echo       - ./pyproject.toml:/app/pyproject.toml>> docker-compose.yml
echo       # Persistent data>> docker-compose.yml
echo       - ./src/smart_core_assistant_painel/app/ui/db:/app/src/smart_core_assistant_painel/app/ui/db>> docker-compose.yml
echo       - ./src/smart_core_assistant_painel/app/ui/media:/app/src/smart_core_assistant_painel/app/ui/media>> docker-compose.yml
echo       # Mount Firebase credentials>> docker-compose.yml
echo       - ./src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config:/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config>> docker-compose.yml
echo     depends_on:>> docker-compose.yml
echo       - postgres-django>> docker-compose.yml
echo     networks:>> docker-compose.yml
echo       - smart-core-network>> docker-compose.yml
echo     extra_hosts:>> docker-compose.yml
echo       - "host.docker.internal:host-gateway">> docker-compose.yml
echo     entrypoint: ["/usr/local/bin/docker-entrypoint.sh"]>> docker-compose.yml
echo     command: ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "runserver", "0.0.0.0:8000"]>> docker-compose.yml
echo.>> docker-compose.yml
echo   # Django Q Cluster para desenvolvimento>> docker-compose.yml
echo   django-qcluster:>> docker-compose.yml
echo     build:>> docker-compose.yml
echo       context: .>> docker-compose.yml
echo       dockerfile: Dockerfile>> docker-compose.yml
echo     restart: unless-stopped>> docker-compose.yml
echo     environment:>> docker-compose.yml
echo       - DJANGO_SETTINGS_MODULE=smart_core_assistant_painel.app.ui.core.settings>> docker-compose.yml
echo       - DJANGO_DEBUG=True>> docker-compose.yml
echo       - SECRET_KEY_DJANGO=temp-secret-key-for-initial-startup-will-be-replaced-by-firebase-remote-config>> docker-compose.yml
echo       - POSTGRES_DB=smart_core_db>> docker-compose.yml
echo       - POSTGRES_USER=postgres>> docker-compose.yml
echo       - POSTGRES_PASSWORD=postgres123>> docker-compose.yml
echo       - POSTGRES_HOST=postgres-django>> docker-compose.yml
echo       - POSTGRES_PORT=5432>> docker-compose.yml
echo       - GOOGLE_APPLICATION_CREDENTIALS=/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json>> docker-compose.yml
echo       # Configuracao para acesso ao Ollama local>> docker-compose.yml
echo       - OLLAMA_HOST=host.docker.internal>> docker-compose.yml
echo       - OLLAMA_PORT=11434>> docker-compose.yml
echo       # Variaveis dinamicas serao configuradas pelo start_services>> docker-compose.yml
echo       # SECRET_KEY_DJANGO, OPENAI_API_KEY, GROQ_API_KEY, etc. vem do Firebase Remote Config>> docker-compose.yml
echo     volumes:>> docker-compose.yml
echo       - ./src:/app/src>> docker-compose.yml
echo       - ./src/smart_core_assistant_painel/app/ui/db:/app/src/smart_core_assistant_painel/app/ui/db>> docker-compose.yml
echo       - ./src/smart_core_assistant_painel/app/ui/media:/app/src/smart_core_assistant_painel/app/ui/media>> docker-compose.yml
echo       # Mount Firebase credentials>> docker-compose.yml
echo       - ./src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config:/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config>> docker-compose.yml
echo     depends_on:>> docker-compose.yml
echo       - django-app>> docker-compose.yml
echo     networks:>> docker-compose.yml
echo       - smart-core-network>> docker-compose.yml
echo     extra_hosts:>> docker-compose.yml
echo       - "host.docker.internal:host-gateway">> docker-compose.yml
echo     entrypoint: ["/usr/local/bin/docker-entrypoint-qcluster.sh"]>> docker-compose.yml
echo     command: ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "qcluster"]>> docker-compose.yml
echo     healthcheck:>> docker-compose.yml
echo       test: ["CMD", "curl", "-f", "http://django-app:8000/admin/"]>> docker-compose.yml
echo       interval: 30s>> docker-compose.yml
echo       timeout: 10s>> docker-compose.yml
echo       retries: 3>> docker-compose.yml
echo       start_period: 60s>> docker-compose.yml
echo.>> docker-compose.yml
echo   # PostgreSQL para Django>> docker-compose.yml
echo   postgres-django:>> docker-compose.yml
echo     image: postgres:15-alpine>> docker-compose.yml
echo     restart: unless-stopped>> docker-compose.yml
echo     environment:>> docker-compose.yml
echo       - POSTGRES_DB=smart_core_db>> docker-compose.yml
echo       - POSTGRES_USER=postgres>> docker-compose.yml
echo       - POSTGRES_PASSWORD=postgres123>> docker-compose.yml
echo     ports:>> docker-compose.yml
echo       - "5435:5432">> docker-compose.yml
echo     volumes:>> docker-compose.yml
echo       - postgres_django_data:/var/lib/postgresql/data>> docker-compose.yml
echo     networks:>> docker-compose.yml
echo       - smart-core-network>> docker-compose.yml
echo.>> docker-compose.yml
echo   # PostgreSQL para Evolution API>> docker-compose.yml
echo   postgres:>> docker-compose.yml
echo     image: postgres:15-alpine>> docker-compose.yml
echo     restart: unless-stopped>> docker-compose.yml
echo     environment:>> docker-compose.yml
echo       - POSTGRES_DB=evolution>> docker-compose.yml
echo       - POSTGRES_USER=evolution>> docker-compose.yml
echo       - POSTGRES_PASSWORD=evolution123>> docker-compose.yml
echo     volumes:>> docker-compose.yml
echo       - postgres_data:/var/lib/postgresql/data>> docker-compose.yml
echo     networks:>> docker-compose.yml
echo       - smart-core-network>> docker-compose.yml
echo.>> docker-compose.yml
echo   # Redis para Evolution API>> docker-compose.yml
echo   redis:>> docker-compose.yml
echo     image: redis:7-alpine>> docker-compose.yml
echo     restart: unless-stopped>> docker-compose.yml
echo     ports:>> docker-compose.yml
echo       - "6380:6379">> docker-compose.yml
echo     command: redis-server --appendonly yes>> docker-compose.yml
echo     volumes:>> docker-compose.yml
echo       - redis_data:/data>> docker-compose.yml
echo     networks:>> docker-compose.yml
echo       - smart-core-network>> docker-compose.yml
echo     healthcheck:>> docker-compose.yml
echo       test: ["CMD", "redis-cli", "ping"]>> docker-compose.yml
echo       interval: 10s>> docker-compose.yml
echo       timeout: 5s>> docker-compose.yml
echo       retries: 5>> docker-compose.yml
echo.>> docker-compose.yml
echo   # Evolution API para desenvolvimento>> docker-compose.yml
echo   evolution-api:>> docker-compose.yml
echo     image: atendai/evolution-api:v2.1.1>> docker-compose.yml
echo     restart: unless-stopped>> docker-compose.yml
echo     ports:>> docker-compose.yml
echo       - "8081:8080">> docker-compose.yml
echo     environment:>> docker-compose.yml
echo       # Configuracao de autenticacao>> docker-compose.yml
echo       - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}>> docker-compose.yml
echo       # Configuracao do webhook global>> docker-compose.yml
echo       - WEBHOOK_GLOBAL_URL=http://django-app:8000/oraculo/webhook_whatsapp/>> docker-compose.yml
echo       - WEBHOOK_GLOBAL_ENABLED=true>> docker-compose.yml
echo       - WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=false>> docker-compose.yml
echo       # Configuracao do banco de dados PostgreSQL>> docker-compose.yml
echo       - DATABASE_ENABLED=true>> docker-compose.yml
echo       - DATABASE_PROVIDER=postgresql>> docker-compose.yml
echo       - DATABASE_CONNECTION_URI=postgresql://evolution:evolution123@postgres:5432/evolution?schema=public>> docker-compose.yml
echo       - DATABASE_CONNECTION_CLIENT_NAME=evolution_exchange>> docker-compose.yml
echo       - DATABASE_SAVE_DATA_INSTANCE=true>> docker-compose.yml
echo       - DATABASE_SAVE_DATA_NEW_MESSAGE=true>> docker-compose.yml
echo       - DATABASE_SAVE_MESSAGE_UPDATE=true>> docker-compose.yml
echo       - DATABASE_SAVE_DATA_CONTACTS=true>> docker-compose.yml
echo       - DATABASE_SAVE_DATA_CHATS=true>> docker-compose.yml
echo       - DATABASE_SAVE_DATA_LABELS=true>> docker-compose.yml
echo       - DATABASE_SAVE_DATA_HISTORIC=true>> docker-compose.yml
echo       # Configuracao do Redis Cache>> docker-compose.yml
echo       - CACHE_REDIS_ENABLED=true>> docker-compose.yml
echo       - CACHE_REDIS_URI=redis://redis:6379/6>> docker-compose.yml
echo       - CACHE_REDIS_TTL=604800>> docker-compose.yml
echo       - CACHE_REDIS_PREFIX_KEY=evolution>> docker-compose.yml
echo       - CACHE_REDIS_SAVE_INSTANCES=false>> docker-compose.yml
echo       - CACHE_LOCAL_ENABLED=false>> docker-compose.yml
echo       # Configuracao do QR Code>> docker-compose.yml
echo       - QRCODE_LIMIT=30>> docker-compose.yml
echo       - QRCODE_COLOR=#198754>> docker-compose.yml
echo       # Configuracoes de servidor>> docker-compose.yml
echo       - SERVER_TYPE=http>> docker-compose.yml
echo       - SERVER_PORT=8080>> docker-compose.yml
echo       - SERVER_URL=http://localhost:8081>> docker-compose.yml
echo       # Configuracoes de log>> docker-compose.yml
echo       - LOG_LEVEL=ERROR>> docker-compose.yml
echo       - LOG_COLOR=true>> docker-compose.yml
echo       - LOG_BAILEYS=error>> docker-compose.yml
echo       - CONFIG_SESSION_PHONE_VERSION=2.3000.1023204200>> docker-compose.yml
echo     volumes:>> docker-compose.yml
echo       - evolution_instances:/evolution/instances>> docker-compose.yml
echo     depends_on:>> docker-compose.yml
echo       - postgres>> docker-compose.yml
echo       - redis>> docker-compose.yml
echo     networks:>> docker-compose.yml
echo       - smart-core-network>> docker-compose.yml
echo     env_file:>> docker-compose.yml
echo       - .env>> docker-compose.yml
echo.>> docker-compose.yml
echo volumes:>> docker-compose.yml
echo   evolution_instances:>> docker-compose.yml
echo     driver: local>> docker-compose.yml
echo   postgres_data:>> docker-compose.yml
echo     driver: local>> docker-compose.yml
echo   postgres_django_data:>> docker-compose.yml
echo     driver: local>> docker-compose.yml
echo   redis_data:>> docker-compose.yml
echo     driver: local>> docker-compose.yml
echo.>> docker-compose.yml
echo networks:>> docker-compose.yml
echo   smart-core-network:>> docker-compose.yml
echo     driver: bridge>> docker-compose.yml

echo Arquivo docker-compose.yml criado com sucesso.

REM 5. Criar scripts de entrypoint
call :section "4. Criando scripts de entrypoint..."

REM Criar docker-entrypoint.sh
echo #!/bin/bash> docker-entrypoint.sh
echo set -e>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Funcao para aguardar o banco de dados>> docker-entrypoint.sh
echo wait_for_db^(^) {>> docker-entrypoint.sh
echo     echo "Aguardando conexao com o banco de dados...">> docker-entrypoint.sh
echo     while ! uv run python -c "import psycopg; psycopg.connect^(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB'^)" 2^>/dev/null; do>> docker-entrypoint.sh
echo         echo "Banco de dados nao esta pronto. Aguardando...">> docker-entrypoint.sh
echo         sleep 2>> docker-entrypoint.sh
echo     done>> docker-entrypoint.sh
echo     echo "Banco de dados conectado com sucesso!">> docker-entrypoint.sh
echo }>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Funcao para verificar se as credenciais do Firebase existem>> docker-entrypoint.sh
echo check_firebase_credentials^(^) {>> docker-entrypoint.sh
echo     echo "Verificando credenciais do Firebase...">> docker-entrypoint.sh
echo     if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then>> docker-entrypoint.sh
echo         echo "Erro: Arquivo de credenciais do Firebase nao encontrado em $GOOGLE_APPLICATION_CREDENTIALS">> docker-entrypoint.sh
echo         echo "Certifique-se de que o arquivo firebase_key.json esta presente no diretorio correto.">> docker-entrypoint.sh
echo         exit 1>> docker-entrypoint.sh
echo     fi>> docker-entrypoint.sh
echo     echo "Credenciais do Firebase encontradas!">> docker-entrypoint.sh
echo }>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Funcao para executar inicializacao completa>> docker-entrypoint.sh
echo run_initialization^(^) {>> docker-entrypoint.sh
echo     echo "Iniciando processo de inicializacao completo...">> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo     # Verifica credenciais do Firebase>> docker-entrypoint.sh
echo     check_firebase_credentials>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo     # Executa start_initial_loading ^(inicializacao do Firebase^)>> docker-entrypoint.sh
echo     echo "Executando start_initial_loading ^(Firebase Remote Config^)...">> docker-entrypoint.sh
echo     uv run python -c ">> docker-entrypoint.sh
echo from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import start_initial_loading>> docker-entrypoint.sh
echo try:>> docker-entrypoint.sh
echo     start_initial_loading^(^)>> docker-entrypoint.sh
echo     print^('start_initial_loading executado com sucesso!'^)>> docker-entrypoint.sh
echo except Exception as e:>> docker-entrypoint.sh
echo     print^(f'Erro em start_initial_loading: {e}'^)>> docker-entrypoint.sh
echo     raise>> docker-entrypoint.sh
echo ">> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo     # Executa start_services ^(carregamento de remote config e configuracao de variaveis^)>> docker-entrypoint.sh
echo     echo "Executando start_services ^(carregamento de configuracoes^)...">> docker-entrypoint.sh
echo     uv run python -c ">> docker-entrypoint.sh
echo from smart_core_assistant_painel.modules.services.start_services import start_services>> docker-entrypoint.sh
echo try:>> docker-entrypoint.sh
echo     start_services^(^)>> docker-entrypoint.sh
echo     print^('start_services executado com sucesso!'^)>> docker-entrypoint.sh
echo except Exception as e:>> docker-entrypoint.sh
echo     print^(f'Erro em start_services: {e}'^)>> docker-entrypoint.sh
echo     raise>> docker-entrypoint.sh
echo ">> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo     echo "Inicializacao completa finalizada com sucesso!">> docker-entrypoint.sh
echo }>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Funcao para verificar conectividade com Ollama>> docker-entrypoint.sh
echo check_ollama_connectivity^(^) {>> docker-entrypoint.sh
echo     echo "Verificando conectividade com Ollama...">> docker-entrypoint.sh
echo     if curl -s "http://${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}/api/tags" ^> /dev/null 2^>^&1; then>> docker-entrypoint.sh
echo         echo "Ollama esta acessivel!">> docker-entrypoint.sh
echo     else>> docker-entrypoint.sh
echo         echo "Aviso: Ollama nao esta acessivel. Verifique se esta rodando localmente.">> docker-entrypoint.sh
echo         echo "Host: ${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}">> docker-entrypoint.sh
echo     fi>> docker-entrypoint.sh
echo }>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Aguarda o banco de dados estar disponivel>> docker-entrypoint.sh
echo wait_for_db>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Verifica conectividade com Ollama>> docker-entrypoint.sh
echo check_ollama_connectivity>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Executa a inicializacao completa ^(Firebase + Services^)>> docker-entrypoint.sh
echo run_initialization>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Executa migracoes>> docker-entrypoint.sh
echo echo "Executando migracoes...">> docker-entrypoint.sh
echo uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Cria superusuario se nao existir>> docker-entrypoint.sh
echo echo "Criando superusuario...">> docker-entrypoint.sh
echo echo "from django.contrib.auth import get_user_model; User = get_user_model^(^); User.objects.filter^(username='admin'^).exists^(^) or User.objects.create_superuser^('admin', 'admin@example.com', '123456'^)" ^| uv run python src/smart_core_assistant_painel/app/ui/manage.py shell>> docker-entrypoint.sh
echo.>> docker-entrypoint.sh
echo # Executa o comando passado como argumento>> docker-entrypoint.sh
echo echo "Iniciando aplicacao Django...">> docker-entrypoint.sh
echo exec "$@">> docker-entrypoint.sh

REM Criar docker-entrypoint-qcluster.sh
echo #!/bin/bash> docker-entrypoint-qcluster.sh
echo set -e>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Funcao para aguardar o banco de dados>> docker-entrypoint-qcluster.sh
echo wait_for_db^(^) {>> docker-entrypoint-qcluster.sh
echo     echo "Aguardando conexao com o banco de dados...">> docker-entrypoint-qcluster.sh
echo     while ! uv run python -c "import psycopg; psycopg.connect^(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB'^)" 2^>/dev/null; do>> docker-entrypoint-qcluster.sh
echo         echo "Banco de dados nao esta pronto. Aguardando...">> docker-entrypoint-qcluster.sh
echo         sleep 2>> docker-entrypoint-qcluster.sh
echo     done>> docker-entrypoint-qcluster.sh
echo     echo "Banco de dados conectado com sucesso!">> docker-entrypoint-qcluster.sh
echo }>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Funcao para verificar se as credenciais do Firebase existem>> docker-entrypoint-qcluster.sh
echo check_firebase_credentials^(^) {>> docker-entrypoint-qcluster.sh
echo     echo "Verificando credenciais do Firebase...">> docker-entrypoint-qcluster.sh
echo     if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then>> docker-entrypoint-qcluster.sh
echo         echo "Erro: Arquivo de credenciais do Firebase nao encontrado em $GOOGLE_APPLICATION_CREDENTIALS">> docker-entrypoint-qcluster.sh
echo         echo "Certifique-se de que o arquivo firebase_key.json esta presente no diretorio correto.">> docker-entrypoint-qcluster.sh
echo         exit 1>> docker-entrypoint-qcluster.sh
echo     fi>> docker-entrypoint-qcluster.sh
echo     echo "Credenciais do Firebase encontradas!">> docker-entrypoint-qcluster.sh
echo }>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Funcao para executar inicializacao completa>> docker-entrypoint-qcluster.sh
echo run_initialization^(^) {>> docker-entrypoint-qcluster.sh
echo     echo "Iniciando processo de inicializacao completo para QCluster...">> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo     # Verifica credenciais do Firebase>> docker-entrypoint-qcluster.sh
echo     check_firebase_credentials>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo     # Executa start_initial_loading ^(inicializacao do Firebase^)>> docker-entrypoint-qcluster.sh
echo     echo "Executando start_initial_loading ^(Firebase Remote Config^)...">> docker-entrypoint-qcluster.sh
echo     uv run python -c ">> docker-entrypoint-qcluster.sh
echo from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import start_initial_loading>> docker-entrypoint-qcluster.sh
echo try:>> docker-entrypoint-qcluster.sh
echo     start_initial_loading^(^)>> docker-entrypoint-qcluster.sh
echo     print^('start_initial_loading executado com sucesso!'^)>> docker-entrypoint-qcluster.sh
echo except Exception as e:>> docker-entrypoint-qcluster.sh
echo     print^(f'Erro em start_initial_loading: {e}'^)>> docker-entrypoint-qcluster.sh
echo     raise>> docker-entrypoint-qcluster.sh
echo ">> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo     # Executa start_services ^(carregamento de remote config e configuracao de variaveis^)>> docker-entrypoint-qcluster.sh
echo     echo "Executando start_services ^(carregamento de configuracoes^)...">> docker-entrypoint-qcluster.sh
echo     uv run python -c ">> docker-entrypoint-qcluster.sh
echo from smart_core_assistant_painel.modules.services.start_services import start_services>> docker-entrypoint-qcluster.sh
echo try:>> docker-entrypoint-qcluster.sh
echo     start_services^(^)>> docker-entrypoint-qcluster.sh
echo     print^('start_services executado com sucesso!'^)>> docker-entrypoint-qcluster.sh
echo except Exception as e:>> docker-entrypoint-qcluster.sh
echo     print^(f'Erro em start_services: {e}'^)>> docker-entrypoint-qcluster.sh
echo     raise>> docker-entrypoint-qcluster.sh
echo ">> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo     echo "Inicializacao completa finalizada com sucesso para QCluster!">> docker-entrypoint-qcluster.sh
echo }>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Funcao para verificar conectividade com Ollama>> docker-entrypoint-qcluster.sh
echo check_ollama_connectivity^(^) {>> docker-entrypoint-qcluster.sh
echo     echo "Verificando conectividade com Ollama...">> docker-entrypoint-qcluster.sh
echo     if curl -s "http://${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}/api/tags" ^> /dev/null 2^>^&1; then>> docker-entrypoint-qcluster.sh
echo         echo "Ollama esta acessivel!">> docker-entrypoint-qcluster.sh
echo     else>> docker-entrypoint-qcluster.sh
echo         echo "Aviso: Ollama nao esta acessivel. Verifique se esta rodando localmente.">> docker-entrypoint-qcluster.sh
echo         echo "Host: ${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}">> docker-entrypoint-qcluster.sh
echo     fi>> docker-entrypoint-qcluster.sh
echo }>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Funcao para aguardar o Django principal estar pronto>> docker-entrypoint-qcluster.sh
echo wait_for_django_app^(^) {>> docker-entrypoint-qcluster.sh
echo     echo "Aguardando Django principal estar pronto...">> docker-entrypoint-qcluster.sh
echo     while ! curl -s http://django-app:8000/admin/ ^> /dev/null 2^>^&1; do>> docker-entrypoint-qcluster.sh
echo         echo "Django principal ainda nao esta pronto. Aguardando...">> docker-entrypoint-qcluster.sh
echo         sleep 5>> docker-entrypoint-qcluster.sh
echo     done>> docker-entrypoint-qcluster.sh
echo     echo "Django principal esta pronto!">> docker-entrypoint-qcluster.sh
echo }>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Aguarda o banco de dados estar disponivel>> docker-entrypoint-qcluster.sh
echo wait_for_db>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Verifica conectividade com Ollama>> docker-entrypoint-qcluster.sh
echo check_ollama_connectivity>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Executa a inicializacao completa ^(Firebase + Services^)>> docker-entrypoint-qcluster.sh
echo run_initialization>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Aguarda o Django principal estar pronto>> docker-entrypoint-qcluster.sh
echo wait_for_django_app>> docker-entrypoint-qcluster.sh
echo.>> docker-entrypoint-qcluster.sh
echo # Executa o comando passado como argumento>> docker-entrypoint-qcluster.sh
echo echo "Iniciando QCluster...">> docker-entrypoint-qcluster.sh
echo exec "$@">> docker-entrypoint-qcluster.sh

echo Scripts de entrypoint criados com sucesso.

REM 6. Atualizar Dockerfile para incluir os entrypoints
call :section "5. Atualizando Dockerfile..."
if not exist "Dockerfile" (
    echo ERRO: Dockerfile nao encontrado na raiz do projeto.
    exit /b 1
)

REM Cria backup
copy /Y "Dockerfile" "Dockerfile.backup" >nul

REM Adiciona os entrypoints caso nao existam
findstr /c:"docker-entrypoint" Dockerfile >nul
if errorlevel 1 (
    echo # Copiar scripts de entrypoint para o ambiente Docker>> Dockerfile
    echo COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh>> Dockerfile
    echo COPY docker-entrypoint-qcluster.sh /usr/local/bin/docker-entrypoint-qcluster.sh>> Dockerfile
    echo RUN chmod +x /usr/local/bin/docker-entrypoint.sh /usr/local/bin/docker-entrypoint-qcluster.sh>> Dockerfile
    echo RUN dos2unix /usr/local/bin/docker-entrypoint.sh /usr/local/bin/docker-entrypoint-qcluster.sh>> Dockerfile
    echo.>> Dockerfile
)

echo Dockerfile atualizado com sucesso.

REM 7. Parar containers existentes
call :section "6. Parando containers existentes..."

%COMPOSE_CMD% down -v

REM 8. Construir imagens Docker
call :section "7. Construindo imagens Docker..."

%COMPOSE_CMD% build --no-cache
if errorlevel 1 (
    echo ERRO: Falha ao construir as imagens Docker.
    exit /b 1
)

echo Imagens Docker construidas com sucesso.

REM 9. Iniciar servicos de banco de dados primeiro
call :section "8. Iniciando servicos de banco de dados..."

%COMPOSE_CMD% up -d postgres-django postgres redis

REM Aguardar bancos de dados ficarem prontos
call :wait_for_service postgres-django "pg_isready -U postgres"
call :wait_for_service postgres "pg_isready -U evolution"
call :wait_for_service redis "redis-cli ping"

REM 10. Executar migracoes do Django
call :section "9. Executando migracoes do Django..."

REM Resetar migracoes: remover todos os arquivos (exceto __init__.py)
echo Limpando arquivos de migracoes existentes...
for /d %%d in (src\smart_core_assistant_painel\app\ui\*) do (
    if exist "%%d\migrations" (
        for %%f in ("%%d\migrations\*") do (
            if /I not "%%~nxf"=="__init__.py" del /Q "%%f" 2>nul
        )
    )
)

REM Criar novas migracoes antes de aplicar
%COMPOSE_CMD% run --rm --entrypoint "" django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py makemigrations
if errorlevel 1 (
    echo ERRO: Falha ao criar migracoes do Django.
    exit /b 1
)

%COMPOSE_CMD% run --rm --entrypoint "" django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate
if errorlevel 1 (
    echo ERRO: Falha ao executar migracoes do Django.
    exit /b 1
)

REM 11. Coletar arquivos estaticos
call :section "10. Coletando arquivos estaticos..."

%COMPOSE_CMD% run --rm --entrypoint "" django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput
if errorlevel 1 (
    echo AVISO: Falha ao coletar arquivos estaticos.
)

REM 12. Criar superusuario
call :section "11. Criando superusuario..."

%COMPOSE_CMD% run --rm --entrypoint "" django-app bash -c "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@example.com','123456')\" | uv run python src/smart_core_assistant_painel/app/ui/manage.py shell"
if errorlevel 1 (
    echo AVISO: Falha ao criar superusuario.
)

REM 13. Iniciar todos os servicos
call :section "12. Iniciando todos os servicos..."

%COMPOSE_CMD% up -d

REM 14. Verificar status dos servicos
call :section "13. Verificando status dos servicos..."

timeout /t 10 >nul

 %COMPOSE_CMD% ps | findstr /i "Up" >nul
if errorlevel 1 (
    echo AVISO: Alguns containers podem nao estar rodando corretamente.
    %COMPOSE_CMD% ps
)

echo.
echo === Ambiente Docker configurado com sucesso! ===
echo.
echo Servicos disponiveis:
echo - Django App: http://localhost:8001
echo - Evolution API: http://localhost:8081
echo - PostgreSQL Django: localhost:5435
echo - Redis: localhost:6380
echo.
echo Para monitorar os logs:
echo %COMPOSE_CMD% logs -f
echo.
echo Para parar todos os servicos:
echo %COMPOSE_CMD% down
echo.
echo Usuario admin criado:
echo Username: admin
echo Password: 123456
echo Email: admin@example.com
echo.
echo Ambiente pronto para desenvolvimento!
exit /b 0

:section
set MSG=%~1
echo ================================================================
echo %MSG%
echo ================================================================
exit /b 0

:wait_for_service
set SERVICE=%~1
set COMMAND=%~2
echo Aguardando servico %SERVICE% ficar pronto...
for /l %%i in (1,1,30) do (
    %COMPOSE_CMD% exec -T %SERVICE% %COMMAND% >nul 2>nul
    if not errorlevel 1 (
        echo Servico %SERVICE% pronto.
        exit /b 0
    )
    echo Aguardando %SERVICE%... (%%i/30)
    timeout /t 2 >nul
)
echo AVISO: Timeout aguardando %SERVICE%.
exit /b 0
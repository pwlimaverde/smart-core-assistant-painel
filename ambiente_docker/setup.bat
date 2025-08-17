@echo off
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

where docker-compose >nul 2>nul
if errorlevel 1 (
    echo ERRO: Docker Compose nao esta instalado ou nao esta no PATH.
    exit /b 1
)

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
set FIREBASE_PATH=src\smart_core_assistant_painel\modules\initial_loading\utils\keys\firebase_config\firebase_key.json
for %%I in ("%FIREBASE_PATH%") do set FIREBASE_KEY_DIR=%%~dpI
if not exist "%FIREBASE_KEY_DIR%" (
    mkdir "%FIREBASE_KEY_DIR%"
)

for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"FIREBASE_KEY_JSON_CONTENT=" .env') do set FIREBASE_CONTENT=%%B
if not defined FIREBASE_CONTENT (
    echo ERRO: Variavel FIREBASE_KEY_JSON_CONTENT nao encontrada no arquivo .env
    echo Por favor, adicione a variavel FIREBASE_KEY_JSON_CONTENT no .env com o conteudo JSON do Firebase
    echo Exemplo: FIREBASE_KEY_JSON_CONTENT={"type":"service_account","project_id":"seu-projeto",...}
    exit /b 1
)

echo Criando firebase_key.json a partir da variavel FIREBASE_KEY_JSON_CONTENT...
(
    echo %FIREBASE_CONTENT%
) > "%FIREBASE_PATH%"

echo Arquivo firebase_key.json criado com sucesso em %FIREBASE_PATH%

REM 4. Criar docker-compose.yml
call :section "3. Criando docker-compose.yml..."

(
echo services:
echo   # Aplicacao Django para desenvolvimento
echo   django-app:
echo     build:
echo       context: .
echo       dockerfile: Dockerfile
echo     restart: unless-stopped
echo     ports:
echo       - "8001:8000"
echo     environment:
echo       - DJANGO_SETTINGS_MODULE=core.settings
echo       - DJANGO_DEBUG=True
echo       - SECRET_KEY_DJANGO=temp-secret-key-for-initial-startup-will-be-replaced-by-firebase-remote-config
echo       - POSTGRES_DB=smart_core_db
echo       - POSTGRES_USER=postgres
echo       - POSTGRES_PASSWORD=postgres123
echo       - POSTGRES_HOST=postgres-django
echo       - POSTGRES_PORT=5432
echo       - GOOGLE_APPLICATION_CREDENTIALS=/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
echo       # Configuracao para acesso ao Ollama local
echo       - OLLAMA_HOST=host.docker.internal
echo       - OLLAMA_PORT=11434
echo       # Variaveis dinamicas serao configuradas pelo start_services
echo       # SECRET_KEY_DJANGO, OPENAI_API_KEY, GROQ_API_KEY, etc. vem do Firebase Remote Config
echo     volumes:
echo       # Mount source code for hot reload
echo       - ./src:/app/src
echo       - ./tests:/app/tests
echo       - ./pyproject.toml:/app/pyproject.toml
echo       # Persistent data
echo       - ./src/smart_core_assistant_painel/app/ui/db:/app/src/smart_core_assistant_painel/app/ui/db
echo       - ./src/smart_core_assistant_painel/app/ui/media:/app/src/smart_core_assistant_painel/app/ui/media
echo       # Mount Firebase credentials
echo       - ./src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config:/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config
echo     depends_on:
echo       - postgres-django
echo     networks:
echo       - smart-core-network
echo     extra_hosts:
echo       - "host.docker.internal:host-gateway"
echo     entrypoint: ["/usr/local/bin/docker-entrypoint.sh"]
echo     command: ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "runserver", "0.0.0.0:8000"]
echo.
echo   # Django Q Cluster para desenvolvimento
echo   django-qcluster:
echo     build:
echo       context: .
echo       dockerfile: Dockerfile
echo     restart: unless-stopped
echo     environment:
echo       - DJANGO_SETTINGS_MODULE=core.settings
echo       - DJANGO_DEBUG=True
echo       - SECRET_KEY_DJANGO=temp-secret-key-for-initial-startup-will-be-replaced-by-firebase-remote-config
echo       - POSTGRES_DB=smart_core_db
echo       - POSTGRES_USER=postgres
echo       - POSTGRES_PASSWORD=postgres123
echo       - POSTGRES_HOST=postgres-django
echo       - POSTGRES_PORT=5432
echo       - GOOGLE_APPLICATION_CREDENTIALS=/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
echo       # Configuracao para acesso ao Ollama local
echo       - OLLAMA_HOST=host.docker.internal
echo       - OLLAMA_PORT=11434
echo       # Variaveis dinamicas serao configuradas pelo start_services
echo       # SECRET_KEY_DJANGO, OPENAI_API_KEY, GROQ_API_KEY, etc. vem do Firebase Remote Config
echo     volumes:
echo       - ./src:/app/src
echo       - ./src/smart_core_assistant_painel/app/ui/db:/app/src/smart_core_assistant_painel/app/ui/db
echo       - ./src/smart_core_assistant_painel/app/ui/media:/app/src/smart_core_assistant_painel/app/ui/media
echo       # Mount Firebase credentials
echo       - ./src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config:/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config
echo     depends_on:
echo       - django-app
echo     networks:
echo       - smart-core-network
echo     extra_hosts:
echo       - "host.docker.internal:host-gateway"
echo     entrypoint: ["/usr/local/bin/docker-entrypoint-qcluster.sh"]
echo     command: ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "qcluster"]
echo.
echo   # PostgreSQL para Django
echo   postgres-django:
echo     image: postgres:15-alpine
echo     restart: unless-stopped
echo     environment:
echo       - POSTGRES_DB=smart_core_db
echo       - POSTGRES_USER=postgres
echo       - POSTGRES_PASSWORD=postgres123
echo     ports:
echo       - "5435:5432"
echo     volumes:
echo       - postgres_django_data:/var/lib/postgresql/data
echo     networks:
echo       - smart-core-network
echo.
echo   # PostgreSQL para Evolution API
echo   postgres:
echo     image: postgres:15-alpine
echo     restart: unless-stopped
echo     environment:
echo       - POSTGRES_DB=evolution
echo       - POSTGRES_USER=evolution
echo       - POSTGRES_PASSWORD=evolution123
echo     volumes:
echo       - postgres_data:/var/lib/postgresql/data
echo     networks:
echo       - smart-core-network
echo.
echo   # Redis para Evolution API
echo   redis:
echo     image: redis:7-alpine
echo     restart: unless-stopped
echo     ports:
echo       - "6380:6379"
echo     command: redis-server --appendonly yes
echo     volumes:
echo       - redis_data:/data
echo     networks:
echo       - smart-core-network
echo     healthcheck:
echo       test: ["CMD", "redis-cli", "ping"]
echo       interval: 10s
echo       timeout: 5s
echo       retries: 5
echo.
echo   # Evolution API para desenvolvimento
echo   evolution-api:
echo     image: atendai/evolution-api:v2.1.1
echo     restart: unless-stopped
echo     ports:
echo       - "8081:8080"
echo     environment:
echo       # Configuracao de autenticacao
echo       - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
echo       
echo       # Configuracao do webhook global (com tratamento UTF-8 robusto^)
echo       - WEBHOOK_GLOBAL_URL=http://django-app:8000/oraculo/webhook_whatsapp/
echo       - WEBHOOK_GLOBAL_ENABLED=true
echo       - WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=false
echo       
echo       # Configuracao do banco de dados PostgreSQL
echo       - DATABASE_ENABLED=true
echo       - DATABASE_PROVIDER=postgresql
echo       - DATABASE_CONNECTION_URI=postgresql://evolution:evolution123@postgres:5432/evolution?schema=public
echo       - DATABASE_CONNECTION_CLIENT_NAME=evolution_exchange
echo       - DATABASE_SAVE_DATA_INSTANCE=true
echo       - DATABASE_SAVE_DATA_NEW_MESSAGE=true
echo       - DATABASE_SAVE_MESSAGE_UPDATE=true
echo       - DATABASE_SAVE_DATA_CONTACTS=true
echo       - DATABASE_SAVE_DATA_CHATS=true
echo       - DATABASE_SAVE_DATA_LABELS=true
echo       - DATABASE_SAVE_DATA_HISTORIC=true
echo       
echo       # Configuracao do Redis Cache
echo       - CACHE_REDIS_ENABLED=true
echo       - CACHE_REDIS_URI=redis://redis:6379/6
echo       - CACHE_REDIS_TTL=604800
echo       - CACHE_REDIS_PREFIX_KEY=evolution
echo       - CACHE_REDIS_SAVE_INSTANCES=false
echo       - CACHE_LOCAL_ENABLED=false
echo       
echo       # Configuracao do QR Code (Correcoes Implementadas^)
echo       - QRCODE_LIMIT=30
echo       - QRCODE_COLOR=#198754
echo       
echo       # Configuracoes de servidor
echo       - SERVER_TYPE=http
echo       - SERVER_PORT=8080
echo       - SERVER_URL=http://localhost:8081
echo       
echo       # Configuracoes de log
echo       - LOG_LEVEL=ERROR
echo       - LOG_COLOR=true
echo       - LOG_BAILEYS=error
echo       - CONFIG_SESSION_PHONE_VERSION=2.3000.1023204200
echo     volumes:
echo       - evolution_instances:/evolution/instances
echo     depends_on:
echo       - postgres
echo       - redis
echo     networks:
echo       - smart-core-network
echo     env_file:
echo       - .env
echo.
echo volumes:
echo   evolution_instances:
echo     driver: local
echo   postgres_data:
echo     driver: local
echo   postgres_django_data:
echo     driver: local
echo   redis_data:
echo     driver: local
echo.
echo networks:
echo   smart-core-network:
echo     driver: bridge
) > docker-compose.yml

echo Arquivo docker-compose.yml criado com sucesso.

REM 5. Criar scripts de entrypoint
call :section "4. Criando scripts de entrypoint..."

REM Criar docker-entrypoint.sh
(
echo #!/bin/bash
echo set -e
echo.
echo # Funcao para aguardar o banco de dados
echo wait_for_db(^) {
echo     echo "Aguardando conexao com o banco de dados..."
echo     while ! uv run python -c "import psycopg; psycopg.connect(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
echo         echo "Banco de dados nao esta pronto. Aguardando..."
echo         sleep 2
echo     done
echo     echo "Banco de dados conectado com sucesso!"
echo }
echo.
echo # Funcao para verificar se as credenciais do Firebase existem
echo check_firebase_credentials(^) {
echo     echo "Verificando credenciais do Firebase..."
echo     if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
echo         echo "Erro: Arquivo de credenciais do Firebase nao encontrado em $GOOGLE_APPLICATION_CREDENTIALS"
echo         echo "Certifique-se de que o arquivo firebase_key.json esta presente no diretorio correto."
echo         exit 1
echo     fi
echo     echo "Credenciais do Firebase encontradas!"
echo }
echo.
echo # Funcao para executar inicializacao completa
echo run_initialization(^) {
echo     echo "Iniciando processo de inicializacao completo..."
echo     
echo     # Verifica credenciais do Firebase
echo     check_firebase_credentials
echo     
echo     # Executa start_initial_loading (inicializacao do Firebase^)
echo     echo "Executando start_initial_loading (Firebase Remote Config^)..."
echo     uv run python -c "
echo from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import start_initial_loading
echo try:
echo     start_initial_loading(^)
echo     print('start_initial_loading executado com sucesso!'
echo except Exception as e:
echo     print(f'Erro em start_initial_loading: {e}'
echo     raise
echo "
echo     
echo     # Executa start_services (carregamento de remote config e configuracao de variaveis^)
echo     echo "Executando start_services (carregamento de configuracoes^)..."
echo     uv run python -c "
echo from smart_core_assistant_painel.modules.services.start_services import start_services
echo try:
echo     start_services(^)
echo     print('start_services executado com sucesso!'
echo except Exception as e:
echo     print(f'Erro em start_services: {e}'
echo     raise
echo "
echo     
echo     echo "Inicializacao completa finalizada com sucesso!"
echo }
echo.
echo # Funcao para verificar conectividade com Ollama
echo check_ollama_connectivity(^) {
echo     echo "Verificando conectividade com Ollama..."
echo     if curl -s "http://${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}/api/tags" ^> /dev/null 2^>^&1; then
echo         echo "Ollama esta acessivel!"
echo     else
echo         echo "Aviso: Ollama nao esta acessivel. Verifique se esta rodando localmente."
echo         echo "Host: ${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}"
echo     fi
echo }
echo.
echo # Aguarda o banco de dados estar disponivel
echo wait_for_db
echo.
echo # Verifica conectividade com Ollama
echo check_ollama_connectivity
echo.
echo # Executa a inicializacao completa (Firebase + Services^)
echo run_initialization
echo.
echo # Executa migracoes
echo echo "Executando migracoes..."
echo uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate
echo.
echo # Cria superusuario se nao existir
echo echo "Criando superusuario..."
echo echo "from django.contrib.auth import get_user_model; User = get_user_model(^); User.objects.filter(username='admin'^).exists(^) or User.objects.create_superuser('admin', 'admin@example.com', '123456'^)" ^| uv run python src/smart_core_assistant_painel/app/ui/manage.py shell
echo.
echo # Executa o comando passado como argumento
echo echo "Iniciando aplicacao Django..."
echo exec "$@"
) > docker-entrypoint.sh

REM Criar docker-entrypoint-qcluster.sh
(
echo #!/bin/bash
echo set -e
echo.
echo # Funcao para aguardar o banco de dados
echo wait_for_db(^) {
echo     echo "Aguardando conexao com o banco de dados..."
echo     while ! uv run python -c "import psycopg; psycopg.connect(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
echo         echo "Banco de dados nao esta pronto. Aguardando..."
echo         sleep 2
echo     done
echo     echo "Banco de dados conectado com sucesso!"
echo }
echo.
echo # Funcao para verificar se as credenciais do Firebase existem
echo check_firebase_credentials(^) {
echo     echo "Verificando credenciais do Firebase..."
echo     if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
echo         echo "Erro: Arquivo de credenciais do Firebase nao encontrado em $GOOGLE_APPLICATION_CREDENTIALS"
echo         echo "Certifique-se de que o arquivo firebase_key.json esta presente no diretorio correto."
echo         exit 1
echo     fi
echo     echo "Credenciais do Firebase encontradas!"
echo }
echo.
echo # Funcao para executar inicializacao completa
echo run_initialization(^) {
echo     echo "Iniciando processo de inicializacao completo para QCluster..."
echo     
echo     # Verifica credenciais do Firebase
echo     check_firebase_credentials
echo     
echo     # Executa start_initial_loading (inicializacao do Firebase^)
echo     echo "Executando start_initial_loading (Firebase Remote Config^)..."
echo     uv run python -c "
echo from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import start_initial_loading
echo try:
echo     start_initial_loading(^)
echo     print('start_initial_loading executado com sucesso!'
echo except Exception as e:
echo     print(f'Erro em start_initial_loading: {e}'
echo     raise
echo "
echo     
echo     # Executa start_services (carregamento de remote config e configuracao de variaveis^)
echo     echo "Executando start_services (carregamento de configuracoes^)..."
echo     uv run python -c "
echo from smart_core_assistant_painel.modules.services.start_services import start_services
echo try:
echo     start_services(^)
echo     print('start_services executado com sucesso!'
echo except Exception as e:
echo     print(f'Erro em start_services: {e}'
echo     raise
echo "
echo     
echo     echo "Inicializacao completa finalizada com sucesso para QCluster!"
echo }
echo.
echo # Funcao para verificar conectividade com Ollama
echo check_ollama_connectivity(^) {
echo     echo "Verificando conectividade com Ollama..."
echo     if curl -s "http://${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}/api/tags" ^> /dev/null 2^>^&1; then
echo         echo "Ollama esta acessivel!"
echo     else
echo         echo "Aviso: Ollama nao esta acessivel. Verifique se esta rodando localmente."
echo         echo "Host: ${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}"
echo     fi
echo }
echo.
echo # Funcao para aguardar o Django principal estar pronto
echo wait_for_django_app(^) {
echo     echo "Aguardando Django principal estar pronto..."
echo     while ! curl -s http://django-app:8000/admin/ ^> /dev/null 2^>^&1; do
echo         echo "Django principal ainda nao esta pronto. Aguardando..."
echo         sleep 5
echo     done
echo     echo "Django principal esta pronto!"
echo }
echo.
echo # Aguarda o banco de dados estar disponivel
echo wait_for_db
echo.
echo # Verifica conectividade com Ollama
echo check_ollama_connectivity
echo.
echo # Executa a inicializacao completa (Firebase + Services^)
echo run_initialization
echo.
echo # Aguarda o Django principal estar pronto
echo wait_for_django_app
echo.
echo # Executa o comando passado como argumento
echo echo "Iniciando QCluster..."
echo exec "$@"
) > docker-entrypoint-qcluster.sh

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
    powershell -Command "$content = Get-Content -Raw -Path 'Dockerfile'; $content += \"`n# Copiar scripts de entrypoint para o ambiente Docker`nCOPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh`nCOPY docker-entrypoint-qcluster.sh /usr/local/bin/docker-entrypoint-qcluster.sh`nRUN chmod +x /usr/local/bin/docker-entrypoint.sh /usr/local/bin/docker-entrypoint-qcluster.sh`n\"; Set-Content -Path 'Dockerfile' -Value $content"
)

REM Restaura ENTRYPOINT e CMD se estiverem comentados
powershell -Command "(Get-Content 'Dockerfile') -replace '^# *ENTRYPOINT','ENTRYPOINT' -replace '^# *CMD','CMD' | Set-Content 'Dockerfile'"

echo Dockerfile atualizado com sucesso.

REM 7. Parar containers existentes
call :section "6. Parando containers existentes..."

docker-compose down -v

REM 8. Construir imagens Docker
call :section "7. Construindo imagens Docker..."

docker-compose build --no-cache
if errorlevel 1 (
    echo ERRO: Falha ao construir as imagens Docker.
    exit /b 1
)

echo Imagens Docker construidas com sucesso.

REM 9. Iniciar servicos de banco de dados primeiro
call :section "8. Iniciando servicos de banco de dados..."

docker-compose up -d postgres-django postgres redis

REM Aguardar bancos de dados ficarem prontos
call :wait_for_service postgres-django "pg_isready -U postgres"
call :wait_for_service postgres "pg_isready -U evolution"
call :wait_for_service redis "redis-cli ping"

REM 10. Executar migracoes do Django
call :section "9. Executando migracoes do Django..."

docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate
if errorlevel 1 (
    echo ERRO: Falha ao executar migracoes do Django.
    exit /b 1
)

echo Migracoes do Django executadas com sucesso.

REM 11. Coletar arquivos estaticos
call :section "10. Coletando arquivos estaticos..."

docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput
if errorlevel 1 (
    echo AVISO: Falha ao coletar arquivos estaticos.
)

REM 12. Criar superusuario
call :section "11. Criando superusuario..."

docker-compose run --rm django-app bash -c "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@example.com','123456')\" | uv run python src/smart_core_assistant_painel/app/ui/manage.py shell"
if errorlevel 1 (
    echo AVISO: Falha ao criar superusuario.
)

REM 13. Iniciar todos os servicos
call :section "12. Iniciando todos os servicos..."

docker-compose up -d

REM 14. Verificar status dos servicos
call :section "13. Verificando status dos servicos..."

timeout /t 10 >nul

docker-compose ps | findstr /i "Up" >nul
if errorlevel 1 (
    echo AVISO: Alguns containers podem nao estar rodando corretamente.
    docker-compose ps
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
echo docker-compose logs -f

echo.
echo Para parar todos os servicos:
echo docker-compose down

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
    docker-compose exec -T %SERVICE% %COMMAND% >nul 2>nul
    if not errorlevel 1 (
        echo Servico %SERVICE% pronto.
        exit /b 0
    )
    echo Aguardando %SERVICE%... (%%i/30)
    timeout /t 2 >nul
)
echo AVISO: Timeout aguardando %SERVICE%.
exit /b 0
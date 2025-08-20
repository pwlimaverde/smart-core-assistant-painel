@echo off

:: Script unificado para configurar e iniciar o ambiente de desenvolvimento Docker
:: Este script consolida toda a lógica de setup, garantindo um ambiente limpo e pronto para uso.

setlocal enabledelayedexpansion

echo === Configurando o ambiente de desenvolvimento Docker ===

:: Verificar se estamos na raiz do projeto
if not exist "pyproject.toml" (
    echo ERRO: Este script deve ser executado na raiz do projeto.
    exit /b 1
)

:: 1. Verificar e carregar o arquivo .env
echo 1. Verificando o arquivo de configuracao .env...

if not exist ".env" (
    echo ERRO: Arquivo .env nao encontrado na raiz do projeto.
    echo Por favor, crie um arquivo .env antes de continuar.
    exit /b 1
)

echo Arquivo .env encontrado.

:: 2. Verificar e criar o firebase_key.json
echo 2. Verificando as credenciais do Firebase...

:: Obter caminho do GOOGLE_APPLICATION_CREDENTIALS do .env
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"GOOGLE_APPLICATION_CREDENTIALS=" .env`) do set "FIREBASE_PATH=%%B"

if not defined FIREBASE_PATH (
    echo ERRO: GOOGLE_APPLICATION_CREDENTIALS nao esta definida no arquivo .env.
    echo Por favor, defina o caminho para o arquivo firebase_key.json.
    exit /b 1
)

:: Verificar se o arquivo Firebase existe
if not exist "!FIREBASE_PATH!" (
    echo ERRO: Arquivo Firebase nao encontrado em: !FIREBASE_PATH!
    echo Por favor, coloque o arquivo firebase_key.json no caminho especificado.
    exit /b 1
)

:: Verificar se o arquivo Firebase é um JSON válido
echo Verificando se o arquivo Firebase é um JSON valido...
powershell -Command "try { Get-Content '!FIREBASE_PATH!' | ConvertFrom-Json | Out-Null; Write-Host 'JSON valido' } catch { Write-Host 'ERRO: Arquivo Firebase nao e um JSON valido'; exit 1 }" || (
    echo ERRO: O arquivo Firebase nao e um JSON valido.
    exit /b 1
)

echo Credenciais do Firebase verificadas com sucesso.

:: Verificar se FIREBASE_KEY_JSON_CONTENT existe para Docker build
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"FIREBASE_KEY_JSON_CONTENT=" .env`) do set "FIREBASE_CONTENT=%%B"

if not defined FIREBASE_CONTENT (
    echo Criando FIREBASE_KEY_JSON_CONTENT a partir do arquivo...
    powershell -Command "$content = Get-Content '!FIREBASE_PATH!' -Raw; $env:FIREBASE_KEY_JSON_CONTENT = $content; Add-Content -Path '.env' -Value ('FIREBASE_KEY_JSON_CONTENT=' + $content)" || (
        echo ERRO: Falha ao criar FIREBASE_KEY_JSON_CONTENT.
        exit /b 1
    )
    echo FIREBASE_KEY_JSON_CONTENT criado com sucesso.
) else (
    echo FIREBASE_KEY_JSON_CONTENT ja existe no arquivo .env.
)

:: 2.1. Verificar configurações do Redis para Django Q Cluster
echo 2.1. Verificando configuracoes do Redis para Django Q Cluster...

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"REDIS_HOST=" .env`) do set "REDIS_HOST_VAR=%%B"
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"REDIS_PORT=" .env`) do set "REDIS_PORT_VAR=%%B"

if not defined REDIS_HOST_VAR (
    echo AVISO: Variavel REDIS_HOST nao encontrada no .env. Usando valor padrao: redis
    echo REDIS_HOST=redis >> .env
)

if not defined REDIS_PORT_VAR (
    echo AVISO: Variavel REDIS_PORT nao encontrada no .env. Usando valor padrao: 6379
    echo REDIS_PORT=6379 >> .env
)

echo Configuracoes do Redis verificadas.


:: 3. Limpeza completa do ambiente Docker anterior
echo 3. Limpando ambiente Docker anterior (containers, volumes e redes)...
docker compose down -v --remove-orphans

:: 4. Apagar migrações antigas dos apps Django
echo 4. Apagando migrações antigas do Django...
for /d /r "src\smart_core_assistant_painel\app\ui" %%d in (migrations) do (
    if exist "%%d" (
        for %%f in ("%%d\*.py") do (
            if not "%%~nxf"=="__init__.py" (
                del "%%f"
            )
        )
        for %%f in ("%%d\*.pyc") do (
            del "%%f"
        )
    )
)
echo Migracoes antigas removidas.

:: 5. Construir e iniciar os containers
echo 5. Construindo imagens Docker e iniciando os containers...
docker compose build
docker compose up -d
echo 5.1. Parando temporariamente o django-qcluster ate concluir as migracoes...
docker compose stop django-qcluster

:: 6. Aguardar o banco de dados ficar pronto
echo 6. Aguardando o banco de dados ficar pronto...
:wait_for_db
echo Verificando conexao com o banco de dados...
docker compose exec -T django-app sh -c "uv run python -c \"import psycopg, os; psycopg.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), dbname=os.getenv('POSTGRES_DB'))\"" >nul 2>&1
if %errorlevel% neq 0 (
    echo Banco de dados nao esta pronto. Aguardando 5 segundos...
    timeout /t 5 /nobreak >nul
    goto wait_for_db
)
echo Banco de dados conectado com sucesso!


:: 7. Criar e aplicar novas migrações do Django
echo 7. Criando e aplicando novas migrações do Django...
docker compose exec -T django-app uv run task makemigrations
docker compose exec -T django-app uv run task migrate
echo Aplicando migracoes especificas do django_q...
docker compose exec -T django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate django_q --noinput

:: 8. Criar superusuário
echo 8. Criando superusuario 'admin' com senha '123456'...
docker compose exec -T django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', '123456')"
echo Superusuario criado com sucesso!

echo 9. Iniciando o django-qcluster apos as migracoes...
docker compose start django-qcluster

echo.
echo === Ambiente Docker pronto! ===
echo A aplicacao esta disponivel em http://localhost:8000
echo O painel administrativo esta em http://localhost:8000/admin/
echo Use 'docker compose logs -f' para ver os logs.

endlocal
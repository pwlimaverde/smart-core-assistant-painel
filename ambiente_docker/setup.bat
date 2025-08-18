@echo off

:: Script unificado para configurar e iniciar o ambiente de desenvolvimento Docker
:: Este script consolida toda a lógica de setup, garantindo um ambiente limpo e pronto para uso.

setlocal

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

:: Carregar variáveis do .env
for /f "usebackq delims=" %%a in (".env") do (set "%%a")

echo Arquivo .env encontrado e variaveis carregadas.

:: 2. Verificar e criar o firebase_key.json
echo 2. Verificando as credenciais do Firebase...

if not defined FIREBASE_KEY_JSON_CONTENT (
    echo AVISO: A variavel FIREBASE_KEY_JSON_CONTENT nao esta definida no .env.
    echo Se o seu GOOGLE_APPLICATION_CREDENTIALS aponta para um arquivo que ja existe, tudo bem.
    if not defined GOOGLE_APPLICATION_CREDENTIALS (
        echo ERRO: GOOGLE_APPLICATION_CREDENTIALS nao aponta para um arquivo valido e FIREBASE_KEY_JSON_CONTENT nao esta definida.
        exit /b 1
    )
) else (
    if not defined GOOGLE_APPLICATION_CREDENTIALS (
        echo ERRO: A variavel GOOGLE_APPLICATION_CREDENTIALS nao esta definida no .env.
        exit /b 1
    )
    echo Criando o arquivo firebase_key.json em %GOOGLE_APPLICATION_CREDENTIALS%...
    powershell -Command "New-Item -Path (Split-Path -Path '%GOOGLE_APPLICATION_CREDENTIALS%') -ItemType Directory -Force | Out-Null"
    echo %FIREBASE_KEY_JSON_CONTENT% > "%GOOGLE_APPLICATION_CREDENTIALS%"
    echo Arquivo firebase_key.json criado com sucesso.
)


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

:: 8. Criar superusuário
echo 8. Criando superusuario 'admin' com senha '123456'...
set SUPERUSER_COMMAND="from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', '123456')"
docker compose exec -T django-app uv run python -c %SUPERUSER_COMMAND%
echo Superusuario criado com sucesso!

echo.
echo === Ambiente Docker pronto! ===
echo A aplicacao esta disponivel em http://localhost:8000
echo O painel administrativo esta em http://localhost:8000/admin/
echo Use 'docker compose logs -f' para ver os logs.

endlocal
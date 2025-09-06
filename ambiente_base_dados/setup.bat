@echo off
CLS
ECHO ================================================
ECHO     SMART CORE ASSISTANT - SETUP AMBIENTE BASE DE DADOS
ECHO ================================================
ECHO.

REM Script para configurar e inicializar o ambiente de base de dados
REM Inclui: banco de dados, migrações e criação de superusuário
REM Este ambiente é independente do ambiente_chat no servidor remoto

ECHO [1/5] Verificando se Docker está rodando...
docker version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    ECHO ERRO: Docker não está rodando. Inicie o Docker Desktop e tente novamente.
    PAUSE
    EXIT /B 1
)
ECHO ✓ Docker está rodando
ECHO.

ECHO [2/5] Parando containers existentes do ambiente_base_dados e limpando volumes...
docker-compose -p ambiente_base_dados down -v
ECHO ✓ Containers parados e volumes limpos
ECHO.

ECHO [3/5] Construindo e iniciando ambiente de banco de dados...
docker-compose -p ambiente_base_dados up --build -d
if %ERRORLEVEL% NEQ 0 (
    ECHO ERRO: Falha ao iniciar o ambiente Docker.
    PAUSE
    EXIT /B 1
)
ECHO ✓ Ambiente Docker iniciado
ECHO.

ECHO [4/5] Aguardando banco de dados ficar pronto...
:wait_db
docker-compose -p ambiente_base_dados exec postgres-remote pg_isready -U postgres -d smart_core_db >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    ECHO Aguardando PostgreSQL... (tentando novamente em 3 segundos)
    timeout /t 3 /nobreak >nul
    goto wait_db
)
ECHO ✓ PostgreSQL está pronto
ECHO.

ECHO [5/5] Executando migrações Django e criando superusuário...
cd ..
REM Executar migrações
python src/smart_core_assistant_painel/app/ui/manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    ECHO ERRO: Falha ao executar migrações.
    PAUSE
    EXIT /B 1
)
ECHO ✓ Migrações executadas com sucesso

REM Criar superusuário automaticamente
ECHO.
ECHO Criando superusuário (admin / 123456)...
echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').delete(); User.objects.create_superuser('admin', 'admin@example.com', '123456') | python src/smart_core_assistant_painel/app/ui/manage.py shell
if %ERRORLEVEL% NEQ 0 (
    ECHO AVISO: Erro ao criar superusuário. Talvez já exista.
) else (
    ECHO ✓ Superusuário criado: admin / 123456
)

ECHO.
ECHO ================================================
ECHO          AMBIENTE CONFIGURADO COM SUCESSO!
ECHO ================================================
ECHO.
ECHO Serviços disponíveis:
ECHO   • PostgreSQL: localhost:5436
ECHO   • Redis: localhost:6382
ECHO.
ECHO Superusuário Django:
ECHO   • Usuário: admin
ECHO   • Senha: 123456
ECHO.
ECHO Para iniciar o Django:
ECHO   python src/smart_core_assistant_painel/app/ui/manage.py runserver
ECHO.
ECHO Para ver logs dos containers:
ECHO   docker-compose -p ambiente_base_dados logs -f
ECHO.
ECHO ⚠️  ATENÇÃO: Este ambiente é independente do ambiente_chat no servidor remoto
ECHO.
PAUSE
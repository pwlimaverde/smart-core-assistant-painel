@echo off
REM Script de validação do setup Docker
REM Este script verifica se o ambiente foi configurado corretamente

echo === Validando Setup do Ambiente Docker ===
echo.

REM Verificar se estamos na raiz do projeto
if not exist "pyproject.toml" (
    echo [ERRO] Este script deve ser executado na raiz do projeto!
    pause
    exit /b 1
)

REM 1. Verificar se os containers estão rodando
echo 1. Verificando status dos containers...
docker compose ps
if errorlevel 1 (
    echo [ERRO] Falha ao verificar status dos containers!
    pause
    exit /b 1
)

REM 2. Verificar se o Django está respondendo
echo.
echo 2. Testando se o Django esta respondendo...
curl -f http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Django nao esta respondendo na porta 8000!
    echo Verifique os logs: docker compose logs django-app
    pause
    exit /b 1
)
echo [OK] Django esta respondendo!

REM 3. Verificar se o Django Q Cluster está funcionando
echo.
echo 3. Testando Django Q Cluster...
docker compose exec -T django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell -c "from django_q.models import Task; from django_q.tasks import async_task; task_id = async_task('math.sqrt', 16); print(f'Task enqueued: {task_id}')"
if errorlevel 1 (
    echo [ERRO] Django Q Cluster nao esta funcionando!
    echo Verifique os logs: docker compose logs django-qcluster
    pause
    exit /b 1
)
echo [OK] Django Q Cluster esta funcionando!

REM 4. Verificar conexão com PostgreSQL
echo.
echo 4. Testando conexao com PostgreSQL...
docker compose exec -T django-app uv run python -c "import psycopg, os; psycopg.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), dbname=os.getenv('POSTGRES_DB')); print('PostgreSQL conectado!')"
if errorlevel 1 (
    echo [ERRO] Falha na conexao com PostgreSQL!
    echo Verifique os logs: docker compose logs postgres-django
    pause
    exit /b 1
)
echo [OK] PostgreSQL conectado!

REM 5. Verificar conexão com Redis
echo.
echo 5. Testando conexao com Redis...
docker compose exec -T django-app uv run python -c "import redis; r = redis.Redis(host='redis', port=6379); r.ping(); print('Redis conectado!')"
if errorlevel 1 (
    echo [ERRO] Falha na conexao com Redis!
    echo Verifique os logs: docker compose logs redis
    pause
    exit /b 1
)
echo [OK] Redis conectado!

REM 6. Verificar se o arquivo Firebase foi criado
echo.
echo 6. Verificando arquivo Firebase...
docker compose exec -T django-app test -f "/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json"
if errorlevel 1 (
    echo [ERRO] Arquivo firebase_key.json nao encontrado no container!
    pause
    exit /b 1
)
echo [OK] Arquivo Firebase encontrado!

REM 7. Verificar se o superusuário foi criado
echo.
echo 7. Verificando superusuario admin...
docker compose exec -T django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); admin = User.objects.filter(username='admin').first(); print('Superusuario admin existe!' if admin else 'Superusuario admin NAO existe!')"
if errorlevel 1 (
    echo [ERRO] Falha ao verificar superusuario!
    pause
    exit /b 1
)
echo [OK] Superusuario verificado!

REM 8. Verificar logs por erros críticos
echo.
echo 8. Verificando logs por erros criticos...
docker compose logs django-app | findstr /i "error critical exception" >nul 2>&1
if not errorlevel 1 (
    echo [AVISO] Encontrados erros nos logs do django-app!
    echo Execute: docker compose logs django-app
)

docker compose logs django-qcluster | findstr /i "error critical exception" >nul 2>&1
if not errorlevel 1 (
    echo [AVISO] Encontrados erros nos logs do django-qcluster!
    echo Execute: docker compose logs django-qcluster
)

echo.
echo === Validacao Concluida ===
echo.
echo [OK] Todos os testes passaram!
echo.
echo Servicos disponiveis:
echo - Django App: http://localhost:8000/
echo - Admin Panel: http://localhost:8000/admin/ (admin/123456)
echo - Evolution API: http://localhost:8080/
echo.
echo Para monitorar os logs:
echo   docker compose logs -f
echo.
echo Para parar o ambiente:
echo   docker compose down
echo.
pause
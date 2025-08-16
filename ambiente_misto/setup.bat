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
    echo FIREBASE_CREDENTIALS_JSON={chave JSON completa aqui}
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
    echo REDIS_PORT=6381
    echo POSTGRES_PORT=5435
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
echo /src/smart_core_assistant_painel/app/ui/core/settings.py >> .git\info\exclude

REM Arquivos para marcar com assume-unchanged
set FILES_TO_ASSUME=Dockerfile docker-compose.yml .gitignore src/smart_core_assistant_painel/app/ui/core/settings.py

REM Limpar flags existentes e marcar arquivos
echo Limpando flags 'assume-unchanged' existentes...
git update-index --no-assume-unchanged %FILES_TO_ASSUME% 2>nul

echo Marcando arquivos de configuração para serem ignorados localmente...
git update-index --assume-unchanged %FILES_TO_ASSUME% 2>nul

echo Configuração do Git concluída com sucesso.

REM 3. Atualizar settings.py para usar PostgreSQL e Redis do Docker
echo 3. Atualizando settings.py...

set SETTINGS_PATH=src\smart_core_assistant_painel\app\ui\core\settings.py

REM Backup do arquivo original
copy "%SETTINGS_PATH%" "%SETTINGS_PATH%.backup" >nul

REM Substituir configuração do banco de dados e cache
set SETTINGS_PATH=src\smart_core_assistant_painel\app\ui\core\settings.py

REM Substituir HOST do PostgreSQL
powershell -Command "(Get-Content '%SETTINGS_PATH%') -replace '\"HOST\": os.getenv\(\"POSTGRES_HOST\", \"postgres\"\)', '\"HOST\": os.getenv(\"POSTGRES_HOST\", \"localhost\")' | Out-File -Encoding UTF8 '%SETTINGS_PATH%'"

REM Substituir PORT do PostgreSQL
powershell -Command "(Get-Content '%SETTINGS_PATH%') -replace '\"PORT\": os.getenv\(\"POSTGRES_PORT\", \"5432\"\)', '\"PORT\": os.getenv(\"POSTGRES_PORT\", \"5435\")' | Out-File -Encoding UTF8 '%SETTINGS_PATH%'"

REM Substituir configuração do cache Redis para usar cache em memória
powershell -Command "(Get-Content '%SETTINGS_PATH%') -replace 'CACHES = {[^}]+}', 'CACHES = {
    \"default\": {
        \"BACKEND\": \"django.core.cache.backends.locmem.LocMemCache\",
        \"LOCATION\": \"unique-snowflake\",
    }
}' | Out-File -Encoding UTF8 '%SETTINGS_PATH%'"

echo Arquivo settings.py atualizado com sucesso.

REM 4. Atualizar docker-compose.yml para conter apenas os serviços de banco de dados
echo 4. Atualizando docker-compose.yml...

REM Obter nome do projeto (nome do diretório atual)
for %%f in (.) do set PROJECT_NAME=%%~nxf

REM Criar novo docker-compose.yml
(
echo # Arquivo gerenciado pelo ambiente_misto
echo name: %PROJECT_NAME%
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
echo       - "${POSTGRES_PORT:-5435}:5432"
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

REM 5. Limpar Dockerfile
echo 5. Limpando Dockerfile...

REM Comentar linhas ENTRYPOINT e CMD
powershell -Command "(gc Dockerfile) -replace '^\s*ENTRYPOINT', '# ENTRYPOINT' | Out-File -encoding UTF8 Dockerfile"
powershell -Command "(gc Dockerfile) -replace '^\s*CMD', '# CMD' | Out-File -encoding UTF8 Dockerfile"
echo. >> Dockerfile
echo # As linhas ENTRYPOINT e CMD foram comentadas pelo ambiente_misto. >> Dockerfile

echo Arquivo Dockerfile atualizado com sucesso.

REM 6. Iniciar containers
echo 6. Iniciando os containers (Postgres e Redis)...

docker-compose down -v
docker-compose up -d

REM 7. Instalar dependências Python necessárias
echo 7. Instalando dependências Python necessárias...

pip install psycopg2-binary
pip install firebase-admin
pip install langchain-ollama
pip install django-redis
pip install redis==3.5.3
pip install markdown

REM 8. Apagar migrações do Django
echo 8. Apagando migrações do Django...

REM Navegar para o diretório da aplicação
cd src\smart_core_assistant_painel\app\ui

REM Apagar arquivos de migração (exceto __init__.py)
for /d %%i in (..\..\..\modules\*) do (
    if exist "%%i\migrations" (
        echo Apagando migrações de %%i
        del "%%i\migrations\*.py" >nul 2>&1
        del "%%i\migrations\*.pyc" >nul 2>&1
        echo. > "%%i\migrations\__init__.py"
    )
)

REM Voltar ao diretório raiz
cd ..\..\..\..\..

REM 9. Aplicar migrações do Django
echo 9. Aplicando migrações do Django...

set PYTHONPATH=%cd%\src
python src\smart_core_assistant_painel\app\ui\manage.py migrate

REM 10. Criar superusuário
echo 10. Criando superusuário admin...

set PYTHONPATH=%cd%\src
echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', '123456') | python src\smart_core_assistant_painel\app\ui\manage.py shell

echo.
echo === Ambiente misto pronto! ===
echo Para iniciar a aplicação Django, execute o seguinte comando em outro terminal:
echo python src\smart_core_assistant_painel\app\ui\manage.py runserver 0.0.0.0:8000

pause
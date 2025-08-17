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

if not exist "firebase_key.json" (
    echo ERRO: Antes de executar a criação do ambiente local, salve o arquivo firebase_key.json na raiz do projeto.
    echo.
    echo Obtenha o arquivo de credenciais do Firebase ^(service account key^) e salve-o como firebase_key.json na raiz do projeto.
    echo O script moverá automaticamente este arquivo para o diretório correto.
    echo.
    exit /b 1
)

echo Arquivo firebase_key.json encontrado.

REM Criar diretório para o arquivo firebase_key.json se não existir
set FIREBASE_KEY_DIR=src\smart_core_assistant_painel\modules\initial_loading\utils\keys\firebase_config
if not exist "%FIREBASE_KEY_DIR%" mkdir "%FIREBASE_KEY_DIR%"

REM Mover firebase_key.json para o diretório correto
move "firebase_key.json" "%FIREBASE_KEY_DIR%\firebase_key.json" >nul

echo Arquivo firebase_key.json movido para %FIREBASE_KEY_DIR%\firebase_key.json

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

REM Substituir HOST do PostgreSQL
%~dp0..\..\.venv\Scripts\python.exe -c "import re; content = open('%SETTINGS_PATH%', 'r', encoding='utf-8').read(); content = re.sub(r'\"HOST\": os.getenv\(\"POSTGRES_HOST\", \"postgres\"\)', '\"HOST\": os.getenv(\"POSTGRES_HOST\", \"localhost\")', content); open('%SETTINGS_PATH%', 'w', encoding='utf-8').write(content)"

REM Substituir PORT do PostgreSQL
%~dp0..\..\.venv\Scripts\python.exe -c "import re; content = open('%SETTINGS_PATH%', 'r', encoding='utf-8').read(); content = re.sub(r'\"PORT\": os.getenv\(\"POSTGRES_PORT\", \"5432\"\)', '\"PORT\": os.getenv(\"POSTGRES_PORT\", \"5435\")', content); open('%SETTINGS_PATH%', 'w', encoding='utf-8').write(content)"

REM Substituir configuração do cache Redis para usar cache em memória
%~dp0..\..\.venv\Scripts\python.exe -c "import re; content = open('%SETTINGS_PATH%', 'r', encoding='utf-8').read(); content = re.sub(r'CACHES = {[^}]+}', 'CACHES = {
    \"default\": {
        \"BACKEND\": \"django.core.cache.backends.locmem.LocMemCache\",
        \"LOCATION\": \"unique-snowflake\",
    }
}', content, flags=re.DOTALL); open('%SETTINGS_PATH%', 'w', encoding='utf-8').write(content)"

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

REM Comentar linhas ENTRYPOINT e CMD usando Python
%~dp0..\..\.venv\Scripts\python.exe -c "import re; content = open('Dockerfile', 'r', encoding='utf-8').read(); content = re.sub(r'^\s*ENTRYPOINT', '# ENTRYPOINT', content, flags=re.MULTILINE); content = re.sub(r'^\s*CMD', '# CMD', content, flags=re.MULTILINE); open('Dockerfile', 'w', encoding='utf-8').write(content)"

echo. >> Dockerfile
echo # As linhas ENTRYPOINT e CMD foram comentadas pelo ambiente_misto. >> Dockerfile

echo Arquivo Dockerfile atualizado com sucesso.

REM 6. Iniciar containers
echo 6. Iniciando os containers (Postgres e Redis)...

docker-compose down -v
docker-compose up -d

REM 7. Instalar dependências Python necessárias
echo 7. Instalando dependências Python necessárias...

REM Usar o uv para sincronizar as dependências
uv sync --dev
if %errorlevel% neq 0 (
    echo Erro ao sincronizar dependências com uv
    exit /b 1
)

REM 8. Apagar migrações do Django
echo 8. Apagando migrações do Django...

REM 9. Aplicar migrações do Django
echo 9. Aplicando migrações do Django...

uv run task migrate
if %errorlevel% neq 0 (
    echo Erro ao aplicar migrações do Django
    exit /b 1
)

REM 10. Criar superusuário
echo 10. Criando superusuário admin...

echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', '123456') | uv run task shell
if %errorlevel% neq 0 (
    echo Erro ao criar superusuário
    exit /b 1
)

echo.
echo === Ambiente misto pronto! ===
echo Para iniciar a aplicação Django, execute o seguinte comando em outro terminal:
echo python src\smart_core_assistant_painel\app\ui\manage.py runserver 0.0.0.0:8000

pause
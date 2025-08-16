@echo off
REM Script para configurar e iniciar o ambiente de desenvolvimento misto

ECHO Configurando o ambiente...

REM Prepara o ambiente, verificando e movendo arquivos necessarios
python ambiente_misto\prepare_env.py
if %errorlevel% neq 0 exit /b %errorlevel%

REM Executa os scripts de configuracao
python ambiente_misto\update_git_exclude.py
python ambiente_misto\update_settings.py
python ambiente_misto\update_docker_compose.py
python ambiente_misto\update_dockerfile.py

ECHO Iniciando os containers (Postgres e Redis)...
docker-compose --env-file ./.env up -d

ECHO.
ECHO Ambiente misto pronto!
ECHO Para iniciar a aplicacao Django, execute o seguinte comando em outro terminal:
ECHO python src\smart_core_assistant_painel\app\ui\manage.py runserver 0.0.0.0:8000

pause
@echo off
CLS
ECHO ================================================
ECHO   SMART CORE ASSISTANT - MIGRAR (BANCO REMOTO)
ECHO ================================================
ECHO.

SETLOCAL EnableExtensions EnableDelayedExpansion

REM Objetivo: aplicar APENAS as migrações no PostgreSQL remoto, sem rebuild nem subir containers.
REM Compatível com Windows PowerShell instalado (usa Test-NetConnection).

REM [1] Defaults (podem ser sobrescritos por .env ou variáveis de ambiente)
if not defined POSTGRES_HOST set "POSTGRES_HOST=192.168.3.127"
if not defined POSTGRES_PORT set "POSTGRES_PORT=5436"
if not defined POSTGRES_DB set "POSTGRES_DB=smart_core_db"
if not defined POSTGRES_USER set "POSTGRES_USER=postgres"
if not defined POSTGRES_PASSWORD set "POSTGRES_PASSWORD=postgres123"
if not defined REDIS_HOST set "REDIS_HOST=192.168.3.127"
if not defined REDIS_PORT set "REDIS_PORT=6382"

REM [2] Carrega overrides do .env da RAIZ (se existir) ou desta pasta (fallback)
set "ENV_FILE=..\.env"
if not exist "%ENV_FILE%" (
    set "ENV_FILE=.env"
)
if exist "%ENV_FILE%" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
        if /I "%%~A"=="POSTGRES_HOST" set "POSTGRES_HOST=%%~B"
        if /I "%%~A"=="POSTGRES_PORT" set "POSTGRES_PORT=%%~B"
        if /I "%%~A"=="POSTGRES_DB" set "POSTGRES_DB=%%~B"
        if /I "%%~A"=="POSTGRES_USER" set "POSTGRES_USER=%%~B"
        if /I "%%~A"=="POSTGRES_PASSWORD" set "POSTGRES_PASSWORD=%%~B"
        if /I "%%~A"=="REDIS_HOST" set "REDIS_HOST=%%~B"
        if /I "%%~A"=="REDIS_PORT" set "REDIS_PORT=%%~B"
    )
)

ECHO [1/3] Alvo do banco: %POSTGRES_HOST%:%POSTGRES_PORT%

REM [3] Testa conectividade TCP (timeout ~2min)
ECHO [2/3] Testando conectividade com o PostgreSQL remoto...
powershell -NoProfile -Command "\
  $ok=$false; \
  for ($i=0; $i -lt 40; $i++) { \
    if (Test-NetConnection -ComputerName '%POSTGRES_HOST%' -Port %POSTGRES_PORT% -InformationLevel Quiet) { $ok=$true; break } \
    Start-Sleep -Seconds 3 \
  }; \
  if (-not $ok) { Write-Error 'Falha ao conectar no banco remoto.'; exit 1 } \
"
if %ERRORLEVEL% NEQ 0 (
    ECHO ERRO: Conexao com %POSTGRES_HOST%:%POSTGRES_PORT% indisponivel.
    EXIT /B 1
)
ECHO ✓ Conectividade OK
ECHO.

REM [4] Executa migrações usando as variáveis já setadas neste shell
ECHO [3/3] Aplicando migrações no banco remoto...
pushd ..
uv run task migrate
if %ERRORLEVEL% NEQ 0 (
    ECHO ERRO: Falha ao executar migrações.
    popd
    EXIT /B 1
)

ECHO.
ECHO Conferindo pendencias com showmigrations...
python src/smart_core_assistant_painel/app/ui/manage.py showmigrations
set _RC=%ERRORLEVEL%
popd

if %_RC% NEQ 0 (
    ECHO AVISO: showmigrations retornou erro (verifique logs acima).
) else (
    ECHO ✓ Migrações aplicadas com sucesso.
)

ECHO.
ECHO Concluido.
EXIT /B 0
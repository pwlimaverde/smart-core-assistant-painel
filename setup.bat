@echo off
CLS
ECHO ================================================
ECHO     SMART CORE ASSISTANT - SETUP AMBIENTE BASE DE DADOS
ECHO ================================================
ECHO.

REM Script para configurar e inicializar o ambiente de base de dados
REM Redireciona para o script no diretório ambiente_base_dados

ECHO Navegando para o diretório ambiente_base_dados...
cd ambiente_base_dados

ECHO Executando o script de setup...
call setup.bat

ECHO.
ECHO ================================================
ECHO          PROCESSO DE SETUP CONCLUÍDO!
ECHO ================================================
ECHO.
ECHO Para verificar o status dos containers:
ECHO   cd ambiente_base_dados
ECHO   docker-compose -p ambiente_base_dados ps
ECHO.
ECHO Para ver os logs:
ECHO   cd ambiente_base_dados
ECHO   docker-compose -p ambiente_base_dados logs -f
ECHO.
PAUSE
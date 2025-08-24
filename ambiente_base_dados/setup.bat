@echo off

REM Script para iniciar o ambiente de banco de dados (PostgreSQL e Redis)

ECHO "Iniciando os contêineres do banco de dados em modo detached no servidor remoto..."
docker-compose -H tcp://192.168.3.127:2375 up -d

ECHO "Ambiente de banco de dados iniciado."
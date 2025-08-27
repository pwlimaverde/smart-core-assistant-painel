#!/bin/bash

# Script para configurar e inicializar o ambiente de base de dados
# Redireciona para o script no diretório ambiente_base_dados

clear
echo "================================================"
echo "    SMART CORE ASSISTANT - SETUP AMBIENTE BASE DE DADOS"
echo "================================================"
echo

echo "Navegando para o diretório ambiente_base_dados..."
cd ambiente_base_dados

echo "Executando o script de setup..."
./setup.sh

echo
echo "================================================"
echo "         PROCESSO DE SETUP CONCLUÍDO!"
echo "================================================"
echo
echo "Para verificar o status dos containers:"
echo "  cd ambiente_base_dados"
echo "  docker-compose -p ambiente_base_dados ps"
echo
echo "Para ver os logs:"
echo "  cd ambiente_base_dados"
echo "  docker-compose -p ambiente_base_dados logs -f"
echo
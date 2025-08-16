#!/bin/bash
# Script para configurar e iniciar o ambiente de desenvolvimento misto

echo "Configurando o ambiente..."

# Prepara o ambiente, verificando e movendo arquivos necessarios
python3 ambiente_misto/prepare_env.py
if [ $? -ne 0 ]; then
    exit 1
fi

# Executa os scripts de configuracao
python3 ambiente_misto/update_git_exclude.py
python3 ambiente_misto/update_settings.py
python3 ambiente_misto/update_docker_compose.py
python3 ambiente_misto/update_dockerfile.py

echo "Iniciando os containers (Postgres e Redis)..."
docker-compose --env-file ./.env up -d

echo ""
echo "Ambiente misto pronto!"
echo "Para iniciar a aplicacao Django, execute o seguinte comando em outro terminal:"
echo "python3 src/smart_core_assistant_painel/app/ui/manage.py runserver 0.0.0.0:8000"
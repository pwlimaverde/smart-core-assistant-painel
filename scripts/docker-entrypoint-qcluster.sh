#!/bin/bash
set -e

# Função para aguardar o banco de dados
wait_for_db() {
    echo "Aguardando conexão com o banco de dados..."
    while ! uv run python -c "import psycopg; psycopg.connect(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
        echo "Banco de dados não está pronto. Aguardando..."
        sleep 2
    done
    echo "Banco de dados conectado com sucesso!"
}

# Função para executar inicialização completa
run_initialization() {
    echo "🔥 Iniciando processo de inicialização completo para QCluster..."
    
    # Executa start_initial_loading (inicialização do Firebase)
    echo "📱 Executando start_initial_loading (Firebase Remote Config)..."
    uv run python -c "
from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import start_initial_loading
try:
    start_initial_loading()
    print('✅ start_initial_loading executado com sucesso!')
except Exception as e:
    print(f'❌ Erro em start_initial_loading: {e}')
    raise
"
    
    # Executa start_services (carregamento de remote config e configuração de variáveis)
    echo "⚙️  Executando start_services (carregamento de configurações)..."
    uv run python -c "
from smart_core_assistant_painel.modules.services.start_services import start_services
try:
    start_services()
    print('✅ start_services executado com sucesso!')
except Exception as e:
    print(f'❌ Erro em start_services: {e}')
    raise
"
    
    echo "✅ Inicialização completa finalizada com sucesso para QCluster!"
}

# Aguarda o banco de dados estar disponível
wait_for_db

# Executa a inicialização completa (Firebase + Services)
run_initialization

# Aguarda um pouco para garantir que o Django principal já executou as migrações
echo "⏳ Aguardando Django principal finalizar migrações..."
sleep 10

# Executa o comando passado como argumento
echo "🚀 Iniciando QCluster..."
exec "$@"
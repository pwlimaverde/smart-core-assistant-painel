#!/bin/bash
set -e

# Função para aguardar o banco de dados
wait_for_db() {
    echo "🔍 Aguardando conexão com o banco de dados..."
    while ! uv run python -c "import psycopg; psycopg.connect(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
        echo "⏳ Banco de dados não está pronto. Aguardando..."
        sleep 2
    done
    echo "✅ Banco de dados conectado com sucesso!"
}

# Função para verificar se as credenciais do Firebase existem
check_firebase_credentials() {
    echo "🔑 Verificando credenciais do Firebase..."
    if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "❌ Erro: Arquivo de credenciais do Firebase não encontrado em $GOOGLE_APPLICATION_CREDENTIALS"
        echo "📋 Certifique-se de que o arquivo firebase_key.json está presente no diretório correto."
        exit 1
    fi
    echo "✅ Credenciais do Firebase encontradas!"
}

# Função para executar inicialização completa
run_initialization() {
    echo "🔥 Iniciando processo de inicialização completo..."
    
    # Verifica credenciais do Firebase
    check_firebase_credentials
    
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
    
    echo "✅ Inicialização completa finalizada com sucesso!"
}

# Função para verificar conectividade com Ollama
check_ollama_connectivity() {
    echo "🤖 Verificando conectividade com Ollama..."
    if curl -s "http://${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}/api/tags" > /dev/null 2>&1; then
        echo "✅ Ollama está acessível!"
    else
        echo "⚠️  Aviso: Ollama não está acessível. Verifique se está rodando localmente."
        echo "📋 Host: ${OLLAMA_HOST:-host.docker.internal}:${OLLAMA_PORT:-11434}"
    fi
}

# Aguarda o banco de dados estar disponível
wait_for_db

# Verifica conectividade com Ollama
check_ollama_connectivity

# Executa a inicialização completa (Firebase + Services)
run_initialization

# Executa migrações
echo "📊 Executando migrações..."
uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate

# Cria superusuário se não existir
echo "👤 Criando superusuário..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', '123456')" | uv run python src/smart_core_assistant_painel/app/ui/manage.py shell

# Executa o comando passado como argumento
echo "🚀 Iniciando aplicação Django..."
exec "$@"
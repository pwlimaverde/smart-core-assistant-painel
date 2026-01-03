#!/bin/bash
# ============================================
# SMART CORE ASSISTANT - INSTALAÇÃO AUTOMÁTICA
# ============================================
# Este script configura toda a infraestrutura
# necessária para o ambiente de teste local.
# ============================================

set -e  # Sair em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
log_error() { echo -e "${RED}[ERRO]${NC} $1"; }

# Banner
echo "============================================"
echo "  SMART CORE ASSISTANT - TESTE LOCAL"
echo "============================================"
echo ""

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    log_warning "Recomendado executar como root para instalar Docker."
    log_info "Continue apenas se o Docker já estiver instalado."
    read -p "Continuar? (s/N): " confirm
    if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
        exit 1
    fi
fi

# Verificar sistema operacional
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    else
        log_error "Sistema operacional não suportado."
        exit 1
    fi
    log_info "Sistema detectado: $OS $VERSION"
}

# Instalar Docker se não existir
install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker já instalado: $(docker --version)"
        return 0
    fi

    log_info "Instalando Docker..."
    
    # Atualizar pacotes
    apt-get update -y
    
    # Instalar dependências
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Adicionar chave GPG do Docker
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Adicionar repositório
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Instalar Docker
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Iniciar serviço
    systemctl start docker
    systemctl enable docker

    log_success "Docker instalado com sucesso!"
}

# Validar arquivo .env
validate_env() {
    log_info "Validando arquivo .env..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.local" ]; then
            log_warning ".env não encontrado. Copiando de .env.local..."
            cp .env.local .env
            log_success "Arquivo .env criado a partir de .env.local"
        else
            log_error "Arquivo .env.local não encontrado!"
            exit 1
        fi
    fi

    log_success "Arquivo .env validado!"
}

# Subir containers
start_containers() {
    log_info "Iniciando containers..."
    
    docker compose up -d
    
    log_info "Aguardando containers ficarem saudáveis..."
    
    # Aguardar até 90 segundos (mais tempo para dois PostgreSQL)
    timeout=90
    elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        # Verificar saúde de TODOS os containers
        postgres_cliente_health=$(docker inspect --format='{{.State.Health.Status}}' smartcore_cliente_postgres_teste 2>/dev/null || echo "not_found")
        postgres_evolution_health=$(docker inspect --format='{{.State.Health.Status}}' smartcore_evolution_postgres_teste 2>/dev/null || echo "not_found")
        redis_cliente_health=$(docker inspect --format='{{.State.Health.Status}}' smartcore_cliente_redis_teste 2>/dev/null || echo "not_found")
        redis_evolution_health=$(docker inspect --format='{{.State.Health.Status}}' smartcore_evolution_redis_teste 2>/dev/null || echo "not_found")
        
        if [ "$postgres_cliente_health" == "healthy" ] && [ "$postgres_evolution_health" == "healthy" ] && [ "$redis_cliente_health" == "healthy" ] && [ "$redis_evolution_health" == "healthy" ]; then
            log_success "Todos os containers estão saudáveis!"
            break
        fi
        
        sleep 3
        elapsed=$((elapsed + 3))
        echo -n "."
    done
    echo ""
    
    if [ $elapsed -ge $timeout ]; then
        log_warning "Timeout aguardando containers. Verifique os logs."
    fi
    
    # Mostrar status
    echo ""
    log_info "Status dos containers:"
    docker compose ps
}

# Exibir informações finais
show_summary() {
    echo ""
    echo "============================================"
    echo "  AMBIENTE DE TESTE INICIADO!"
    echo "============================================"
    echo ""
    
    SERVER_IP="192.168.3.127"
    
    log_success "Seus serviços estão rodando:"
    echo ""
    echo "  PostgreSQL (Django):    ${SERVER_IP}:5436  (smartcore_cliente_db)"
    echo "  PostgreSQL (Evolution): ${SERVER_IP}:5437  (smartcore_evolution_db)"
    echo "  Redis (Django):         ${SERVER_IP}:6382"
    echo "  Redis (Evolution):      ${SERVER_IP}:6383"
    echo "  Evolution API:          http://${SERVER_IP}:8080"
    echo ""
    log_info "Webhook configurado para: http://192.168.3.90:8000/sync/evolution/webhook/"
    echo ""
    log_info "Para ver logs: docker compose logs -f"
}

# Execução principal
main() {
    detect_os
    install_docker
    validate_env
    start_containers
    show_summary
}

main

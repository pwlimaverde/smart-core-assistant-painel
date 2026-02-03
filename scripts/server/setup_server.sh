#!/bin/bash
# =====================================================
# Script de Setup Inicial do Servidor
# Smart Core Assistant Painel v1.0.0
# =====================================================
# Uso: curl -fsSL https://raw.githubusercontent.com/SEU_USER/smart-core-assistant-painel/master/scripts/server/setup_server.sh | bash
# Ou: wget -qO- https://raw.githubusercontent.com/SEU_USER/smart-core-assistant-painel/master/scripts/server/setup_server.sh | bash
# =====================================================

set -e  # Sair em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Smart Core Assistant - Setup do Servidor de Produção     ║"
echo "║                        Versão 1.0.0                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# =====================================================
# 1. Atualizar Sistema
# =====================================================
echo -e "${YELLOW}[1/7] Atualizando sistema...${NC}"
apt update && apt upgrade -y

# =====================================================
# 2. Instalar Dependências Básicas
# =====================================================
echo -e "${YELLOW}[2/7] Instalando dependências básicas...${NC}"
apt install -y \
    curl \
    wget \
    git \
    htop \
    nano \
    unzip \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release

# =====================================================
# 3. Instalar Docker
# =====================================================
echo -e "${YELLOW}[3/7] Instalando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}Docker instalado com sucesso!${NC}"
else
    echo -e "${GREEN}Docker já está instalado.${NC}"
fi

# Adicionar usuário atual ao grupo docker (se não for root)
if [ "$EUID" -ne 0 ]; then
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}Você foi adicionado ao grupo docker. Faça logout/login para aplicar.${NC}"
fi

# Verificar Docker
docker --version
docker compose version

# =====================================================
# 4. Instalar Node.js (para Claude Code)
# =====================================================
echo -e "${YELLOW}[4/7] Instalando Node.js 22 LTS...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt install -y nodejs
    echo -e "${GREEN}Node.js instalado com sucesso!${NC}"
else
    echo -e "${GREEN}Node.js já está instalado.${NC}"
fi

node --version
npm --version

# =====================================================
# 5. Instalar Claude Code (Opcional)
# =====================================================
echo -e "${YELLOW}[5/7] Instalando Claude Code...${NC}"
read -p "Deseja instalar o Claude Code? (s/n): " install_claude
if [ "$install_claude" = "s" ] || [ "$install_claude" = "S" ]; then
    npm install -g @anthropic-ai/claude-code
    echo -e "${GREEN}Claude Code instalado com sucesso!${NC}"
else
    echo -e "${YELLOW}Claude Code não instalado.${NC}"
fi

# =====================================================
# 6. Clonar Repositório
# =====================================================
echo -e "${YELLOW}[6/7] Configurando repositório...${NC}"
REPO_DIR="$HOME/smart-core-assistant-painel"

if [ -d "$REPO_DIR" ]; then
    echo -e "${YELLOW}Diretório já existe. Atualizando...${NC}"
    cd "$REPO_DIR"
    git pull origin master
else
    read -p "URL do repositório Git (ex: https://github.com/user/repo.git): " GIT_URL
    git clone "$GIT_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# =====================================================
# 7. Configurar Arquivo .env
# =====================================================
echo -e "${YELLOW}[7/7] Configurando variáveis de ambiente...${NC}"
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo -e "${YELLOW}Arquivo .env criado a partir do exemplo.${NC}"
    echo -e "${RED}IMPORTANTE: Edite o arquivo .env com suas configurações!${NC}"
    echo -e "${YELLOW}Execute: nano $REPO_DIR/.env${NC}"
else
    echo -e "${GREEN}Arquivo .env já existe.${NC}"
fi

# =====================================================
# Criar Rede Docker Compartilhada
# =====================================================
echo -e "${YELLOW}Criando rede Docker compartilhada...${NC}"
docker network create shared_network 2>/dev/null || echo "Rede shared_network já existe."

# =====================================================
# Resumo Final
# =====================================================
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Setup concluído com sucesso!                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}Próximos passos:${NC}"
echo ""
echo "1. Edite o arquivo .env com suas configurações:"
echo "   ${YELLOW}nano $REPO_DIR/.env${NC}"
echo ""
echo "2. Inicie os serviços de dados (PostgreSQL + Redis):"
echo "   ${YELLOW}cd $REPO_DIR${NC}"
echo "   ${YELLOW}docker compose -f docker/compose/data.yml up -d${NC}"
echo ""
echo "3. Inicie a aplicação:"
echo "   ${YELLOW}docker compose -f docker/compose/app.yml up -d${NC}"
echo ""
echo "4. Inicie os workers Celery:"
echo "   ${YELLOW}docker compose -f docker/compose/workers.yml up -d${NC}"
echo ""
echo "5. Inicie o túnel Cloudflare:"
echo "   ${YELLOW}docker compose -f docker/compose/infra.yml up -d${NC}"
echo ""
echo "6. Verifique os logs:"
echo "   ${YELLOW}docker compose -f docker/compose/app.yml logs -f${NC}"
echo ""
echo -e "${GREEN}Ou use o comando completo para subir tudo:${NC}"
echo "   ${YELLOW}docker compose -f docker/compose/data.yml -f docker/compose/app.yml -f docker/compose/workers.yml -f docker/compose/infra.yml up -d${NC}"
echo ""

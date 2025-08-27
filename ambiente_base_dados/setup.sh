#!/bin/bash

# Script para configurar e inicializar o ambiente de base de dados
# Inclui: banco de dados, migrações e criação de superusuário
# Este ambiente é independente do ambiente_chat no servidor remoto

clear
echo "================================================"
echo "    SMART CORE ASSISTANT - SETUP AMBIENTE BASE DE DADOS"
echo "================================================"
echo

# Script para configurar e inicializar o ambiente de base de dados
# Inclui: banco de dados, migrações e criação de superusuário
# Este ambiente é independente do ambiente_chat no servidor remoto

echo "[1/5] Verificando se Docker está rodando..."
if ! command -v docker &> /dev/null; then
    echo "ERRO: Docker não está instalado."
    exit 1
fi

if ! docker version &> /dev/null; then
    echo "ERRO: Docker não está rodando. Inicie o Docker Desktop e tente novamente."
    exit 1
fi

echo "✓ Docker está rodando"
echo

echo "[2/5] Parando containers existentes do ambiente_base_dados e limpando volumes..."
docker-compose -p ambiente_base_dados down -v
echo "✓ Containers parados e volumes limpos"
echo

echo "[3/5] Construindo e iniciando ambiente de banco de dados..."
if ! docker-compose -p ambiente_base_dados up --build -d; then
    echo "ERRO: Falha ao iniciar o ambiente Docker."
    exit 1
fi
echo "✓ Ambiente Docker iniciado"
echo

echo "[4/5] Aguardando banco de dados ficar pronto..."
while ! docker-compose -p ambiente_base_dados exec postgres-remote pg_isready -U postgres -d smart_core_db &> /dev/null; do
    echo "Aguardando PostgreSQL... (tentando novamente em 3 segundos)"
    sleep 3
done
echo "✓ PostgreSQL está pronto"
echo

echo "[5/5] Executando migrações Django e criando superusuário..."
cd ..
# Executar migrações
if ! python src/smart_core_assistant_painel/app/ui/manage.py migrate; then
    echo "ERRO: Falha ao executar migrações."
    exit 1
fi
echo "✓ Migrações executadas com sucesso"

# Criar superusuário automaticamente
echo
echo "Criando superusuário (admin / 123456)..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').delete(); User.objects.create_superuser('admin', 'admin@example.com', '123456')" | python src/smart_core_assistant_painel/app/ui/manage.py shell
if [ $? -ne 0 ]; then
    echo "AVISO: Erro ao criar superusuário. Talvez já exista."
else
    echo "✓ Superusuário criado: admin / 123456"
fi

echo
echo "================================================"
echo "         AMBIENTE CONFIGURADO COM SUCESSO!"
echo "================================================"
echo
echo "Serviços disponíveis:"
echo "  • PostgreSQL: localhost:5436"
echo "  • Redis: localhost:6382"
echo
echo "Superusuário Django:"
echo "  • Usuário: admin"
echo "  • Senha: 123456"
echo
echo "Para iniciar o Django:"
echo "  python src/smart_core_assistant_painel/app/ui/manage.py runserver"
echo
echo "Para ver logs dos containers:"
echo "  docker-compose -p ambiente_base_dados logs -f"
echo
echo "⚠️  ATENÇÃO: Este ambiente é independente do ambiente_chat no servidor remoto"
echo
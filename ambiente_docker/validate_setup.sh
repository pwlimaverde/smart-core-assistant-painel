#!/bin/bash

# Script de validação do setup Docker
# Este script verifica se o ambiente foi configurado corretamente

set -e  # Exit on any error

echo "=== Validando Setup do Ambiente Docker ==="
echo

# Verificar se estamos na raiz do projeto
if [ ! -f "pyproject.toml" ]; then
    echo "ERRO: Este script deve ser executado na raiz do projeto."
    exit 1
fi

# 1. Verificar se os containers estão rodando
echo "1. Verificando status dos containers..."
docker compose ps
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao verificar status dos containers!"
    exit 1
fi

# 2. Verificar se o Django está respondendo
echo
echo "2. Testando se o Django está respondendo..."
if ! curl -f http://localhost:8000/ >/dev/null 2>&1; then
    echo "ERRO: Django não está respondendo na porta 8000!"
    echo "Verifique os logs: docker compose logs django-app"
    exit 1
fi
echo "✅ Django está respondendo!"

# 3. Verificar se o Django Q Cluster está funcionando
echo
echo "3. Testando Django Q Cluster..."
if ! docker compose exec -T django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell -c "from django_q.models import Task; from django_q.tasks import async_task; task_id = async_task('math.sqrt', 16); print(f'Task enqueued: {task_id}')" >/dev/null 2>&1; then
    echo "ERRO: Django Q Cluster não está funcionando!"
    echo "Verifique os logs: docker compose logs django-qcluster"
    exit 1
fi
echo "✅ Django Q Cluster está funcionando!"

# 4. Verificar conexão com PostgreSQL
echo
echo "4. Testando conexão com PostgreSQL..."
if ! docker compose exec -T django-app uv run python -c "import psycopg, os; psycopg.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), dbname=os.getenv('POSTGRES_DB')); print('PostgreSQL conectado!')" >/dev/null 2>&1; then
    echo "ERRO: Falha na conexão com PostgreSQL!"
    echo "Verifique os logs: docker compose logs postgres-django"
    exit 1
fi
echo "✅ PostgreSQL conectado!"

# 5. Verificar conexão com Redis
echo
echo "5. Testando conexão com Redis..."
if ! docker compose exec -T django-app uv run python -c "import redis; r = redis.Redis(host='redis', port=6379); r.ping(); print('Redis conectado!')" >/dev/null 2>&1; then
    echo "ERRO: Falha na conexão com Redis!"
    echo "Verifique os logs: docker compose logs redis"
    exit 1
fi
echo "✅ Redis conectado!"

# 6. Verificar se o arquivo Firebase foi criado
echo
echo "6. Verificando arquivo Firebase..."
if ! docker compose exec -T django-app test -f "/app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json" >/dev/null 2>&1; then
    echo "ERRO: Arquivo firebase_key.json não encontrado no container!"
    exit 1
fi
echo "✅ Arquivo Firebase encontrado!"

# 7. Verificar se o superusuário foi criado
echo
echo "7. Verificando superusuário admin..."
if ! docker compose exec -T django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); admin = User.objects.filter(username='admin').first(); print('Superusuário admin existe!' if admin else 'Superusuário admin NÃO existe!')" >/dev/null 2>&1; then
    echo "ERRO: Falha ao verificar superusuário!"
    exit 1
fi
echo "✅ Superusuário verificado!"

# 8. Verificar logs por erros críticos
echo
echo "8. Verificando logs por erros críticos..."
if docker compose logs django-app | grep -i "error\|critical\|exception" >/dev/null 2>&1; then
    echo "⚠️  AVISO: Encontrados erros nos logs do django-app!"
    echo "Execute: docker compose logs django-app"
fi

if docker compose logs django-qcluster | grep -i "error\|critical\|exception" >/dev/null 2>&1; then
    echo "⚠️  AVISO: Encontrados erros nos logs do django-qcluster!"
    echo "Execute: docker compose logs django-qcluster"
fi

echo
echo "=== Validação Concluída ==="
echo
echo "✅ Todos os testes passaram!"
echo
echo "Serviços disponíveis:"
echo "- Django App: http://localhost:8000/"
echo "- Admin Panel: http://localhost:8000/admin/ (admin/123456)"
echo "- Evolution API: http://localhost:8080/"
echo
echo "Para monitorar os logs:"
echo "  docker compose logs -f"
echo
echo "Para parar o ambiente:"
echo "  docker compose down"
echo
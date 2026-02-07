# Guia de Deploy - Smart Core Assistant Painel

## Visão Geral

Este documento descreve o processo de deploy do Smart Core Assistant Painel em um servidor de produção.

## Requisitos do Servidor

### Hardware Mínimo (MVP ~10 clientes)
- **CPU**: 2-4 vCPU
- **RAM**: 8GB
- **Armazenamento**: 80GB SSD
- **Sistema Operacional**: Ubuntu 24.04 LTS

### Consumo Estimado de Recursos

| Serviço | RAM | CPU |
|---------|-----|-----|
| PostgreSQL + pgvector | 2-3 GB | 1-2 cores |
| Redis | 300-500 MB | 0.5 cores |
| Django App | 1-1.5 GB | 1-2 cores |
| Celery Worker (3) | 1.5 GB | 1-2 cores |
| Celery Beat | 512 MB | 0.5 cores |
| Sistema + Docker | 1 GB | - |
| **Total** | **~6.5 GB** | **~4-8 cores** |

---

## Setup Inicial do Servidor

### Opção 1: Script Automatizado

```bash
# Conectar ao servidor via SSH
ssh root@SEU_SERVIDOR

# Executar script de setup
curl -fsSL https://raw.githubusercontent.com/SEU_USER/smart-core-assistant-painel/master/scripts/server/setup_server.sh | bash
```

### Opção 2: Manual

```bash
# 1. Atualizar sistema
apt update && apt upgrade -y

# 2. Instalar Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# 3. Instalar Node.js (para Claude Code)
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt install -y nodejs

# 4. Instalar Claude Code (opcional)
npm install -g @anthropic-ai/claude-code

# 5. Clonar repositório
git clone https://github.com/SEU_USER/smart-core-assistant-painel.git
cd smart-core-assistant-painel

# 6. Criar rede Docker compartilhada
docker network create shared_network

# 7. Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Editar com suas configurações
```

---

## Configuração do .env

Variáveis **obrigatórias** para produção:

```ini
# Django
SECRET_KEY_DJANGO=sua-chave-secreta-aqui
DEBUG=False
DJANGO_ALLOWED_HOSTS=painel.seudominio.com

# PostgreSQL
POSTGRES_PASSWORD=senha-forte-aqui

# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=seu-token-aqui

# OpenAI (para IA)
OPENAI_API_KEY=sk-...
```

---

## Subir os Serviços

### Ordem de Inicialização

```bash
cd ~/smart-core-assistant-painel

# 1. Dados (PostgreSQL + Redis) - PRIMEIRO
docker compose -f docker/compose/data.yml up -d

# Aguardar healthcheck (30 segundos)
sleep 30

# 2. Aplicação (Django + Migrations)
docker compose -f docker/compose/app.yml up -d

# 3. Workers (Celery)
docker compose -f docker/compose/workers.yml up -d

# 4. Infraestrutura (Cloudflare Tunnel)
docker compose -f docker/compose/infra.yml up -d
```

### Comando Único (após primeiro setup)

```bash
docker compose \
  -f docker/compose/data.yml \
  -f docker/compose/app.yml \
  -f docker/compose/workers.yml \
  -f docker/compose/infra.yml \
  up -d
```

---

## Verificar Status

```bash
# Ver todos os containers
docker ps

# Logs da aplicação
docker logs -f smartcore_app

# Logs do Celery
docker logs -f smartcore_celery_worker

# Logs do PostgreSQL
docker logs -f smartcore_postgres
```

---

## Criar Superusuário

```bash
docker exec -it smartcore_app python -m smart_core_assistant_painel.app.manage createsuperuser
```

---

## Configurar Cloudflare Tunnel

1. Acesse [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. Vá em **Networks → Tunnels**
3. Crie um novo túnel ou selecione existente
4. Configure os **Public Hostnames**:

| Hostname | Service |
|----------|---------|
| painel.seudominio.com | http://smartcore_app:8000 |
| evolution.seudominio.com | http://evolution_api:8080 (futuro) |

5. Copie o **Tunnel Token** para o `.env`

---

## Deploy Automático via Tags

### Fluxo Recomendado

```
feature/* → merge → master → tag v1.0.0 → push tag → GitHub Actions → Deploy
```

### Criar Nova Release

```bash
# 1. Atualizar versão no pyproject.toml
# version = "1.0.1"

# 2. Commit das alterações
git add .
git commit -m "chore: bump version to 1.0.1"

# 3. Merge para master
git checkout master
git merge feature/sua-feature

# 4. Criar tag
git tag -a v1.0.1 -m "Release 1.0.1 - Descrição das mudanças"

# 5. Push
git push origin master
git push origin v1.0.1
```

### Configurar Secrets no GitHub

Vá em **Settings → Secrets and variables → Actions** e adicione:

| Secret | Descrição |
|--------|-----------|
| `SERVER_HOST` | IP ou domínio do servidor |
| `SERVER_USER` | Usuário SSH (ex: root) |
| `SERVER_SSH_KEY` | Chave privada SSH |
| `SERVER_PORT` | Porta SSH (padrão: 22) |

---

## Rede Compartilhada (Multi-Stack)

A rede `shared_network` permite comunicação entre diferentes stacks Docker:

```
┌─────────────────────────────────────────────────────┐
│                   shared_network                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Smart Core Stack          Evolution Stack          │
│  ─────────────────         ──────────────          │
│  • smartcore_app           • evolution_api          │
│  • smartcore_postgres      • evolution_postgres     │
│  • smartcore_redis         • evolution_redis        │
│  • smartcore_celery_*      │                        │
│  • smartcore_tunnel        │                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

Para o stack do Evolution (futuro), basta usar a mesma rede:

```yaml
# No docker-compose do Evolution
networks:
  shared_network:
    name: shared_network
    external: true
```

---

## Troubleshooting

### Container não inicia
```bash
docker logs smartcore_app
docker compose -f docker/compose/app.yml logs
```

### Erro de conexão com PostgreSQL
```bash
# Verificar se PostgreSQL está rodando
docker exec smartcore_postgres pg_isready

# Testar conexão
docker exec -it smartcore_app python -c "from django.db import connection; connection.ensure_connection(); print('OK')"
```

### Erro de conexão com Redis
```bash
docker exec smartcore_redis redis-cli ping
```

### Reiniciar serviços
```bash
docker compose -f docker/compose/app.yml restart
docker compose -f docker/compose/workers.yml restart
```

### Rebuild completo
```bash
docker compose -f docker/compose/app.yml build --no-cache
docker compose -f docker/compose/app.yml up -d --force-recreate
```

---

## Backup

### PostgreSQL
```bash
docker exec smartcore_postgres pg_dump -U postgres smart_core_db > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
cat backup.sql | docker exec -i smartcore_postgres psql -U postgres smart_core_db
```

---

## Monitoramento (Opcional)

### Habilitar Flower (Celery Monitor)

```bash
docker compose -f docker/compose/infra.yml --profile debug up -d flower
```

Acesse: `http://servidor:5555` (usuário/senha no `.env`)

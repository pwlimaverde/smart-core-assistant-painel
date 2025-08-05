# Comandos Docker - Smart Core Assistant Painel

Guia de referência rápida para comandos Docker e troubleshooting.

## 🚀 Comandos Rápidos

### Inicialização

```bash
# Setup inicial (Windows)
make setup
# ou
powershell -ExecutionPolicy Bypass -File scripts/setup-docker.ps1

# Setup inicial (Linux/Mac)
make setup-linux
# ou
./scripts/setup-docker.sh

# Desenvolvimento
make dev

# Desenvolvimento com ferramentas
make dev-tools

# Produção
make prod
```

### Gerenciamento de Serviços

```bash
# Ver status
make ps
docker-compose ps

# Ver logs
make logs
docker-compose logs -f

# Parar serviços
make stop

# Remover containers
make down

# Reiniciar
make restart
```

### Comandos Django

```bash
# Migrações
make migrate
make makemigrations

# Superusuário
make createsuperuser

# Shell Django
make shell

# Arquivos estáticos
make collectstatic
```

### Testes e Qualidade

```bash
# Testes
make test
make test-cov

# Linting e formatação
make lint
make format
make type-check
```

## 🔧 Comandos Docker Compose Detalhados

### Ambiente de Desenvolvimento

```bash
# Iniciar desenvolvimento
docker-compose up -d

# Iniciar com rebuild
docker-compose up -d --build

# Iniciar com ferramentas (MongoDB Express, Redis Commander)
docker-compose --profile tools up -d

# Ver logs específicos
docker-compose logs -f django-app
docker-compose logs -f evolution-api

# Parar desenvolvimento
docker-compose down
```

### Ambiente de Produção

```bash
# Iniciar produção
docker-compose -f docker-compose.yml up -d

# Iniciar com rebuild
docker-compose -f docker-compose.yml up -d --build

# Ver logs
docker-compose -f docker-compose.yml logs -f

# Parar produção
docker-compose -f docker-compose.yml down
```

### Comandos de Container Individual

```bash
# Acessar shell do Django
docker-compose exec django-app bash

# Executar comando Django
docker-compose exec django-app python src/smart_core_assistant_painel/app/ui/manage.py shell

# Acessar MongoDB
docker-compose exec mongodb mongosh

# Acessar Redis
docker-compose exec redis redis-cli

# Ver logs específicos
docker-compose logs -f django-app
docker-compose logs -f evolution-api
docker-compose logs -f mongodb
docker-compose logs -f redis
```

## 🏥 Health Check e Monitoramento

```bash
# Verificar saúde dos serviços
python scripts/health-check.py

# Aguardar serviços ficarem prontos
python scripts/health-check.py --wait

# Health check silencioso
python scripts/health-check.py --quiet

# Verificar status dos containers
docker-compose ps
docker ps

# Verificar uso de recursos
docker stats

# Verificar logs de erro
docker-compose logs --tail=50 django-app | grep -i error
docker-compose logs --tail=50 evolution-api | grep -i error
```

## 💾 Backup e Restore

### Backup MongoDB

```bash
# Backup automático
make backup-db

# Backup manual
docker-compose exec mongodb mongodump --out /tmp/backup
docker cp $(docker-compose ps -q mongodb):/tmp/backup ./backups/mongodb-$(date +%Y%m%d_%H%M%S)

# Backup de database específico
docker-compose exec mongodb mongodump --db smart_core --out /tmp/backup
```

### Backup Redis

```bash
# Backup automático
make backup-redis

# Backup manual
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./backups/redis-$(date +%Y%m%d_%H%M%S).rdb
```

### Restore

```bash
# Restore MongoDB
docker cp ./backups/mongodb-backup $(docker-compose ps -q mongodb):/tmp/restore
docker-compose exec mongodb mongorestore /tmp/restore

# Restore Redis
docker cp ./backups/redis-backup.rdb $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis
```

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Containers não iniciam

```bash
# Verificar logs
docker-compose logs

# Verificar status
docker-compose ps

# Rebuild containers
docker-compose down
docker-compose up -d --build

# Limpar cache Docker
docker system prune -f
```

#### 2. Erro de porta em uso

```bash
# Verificar portas em uso
netstat -tulpn | grep :8000
netstat -tulpn | grep :8080

# Parar processo usando a porta
sudo kill -9 $(lsof -t -i:8000)

# Alterar porta no .env
SERVER_PORT=8001
EVOLUTION_PORT=8081
```

#### 3. Problemas de permissão

```bash
# Verificar permissões dos volumes
ls -la volumes/

# Corrigir permissões
sudo chown -R $USER:$USER volumes/
sudo chmod -R 755 volumes/
```

#### 4. Banco de dados não conecta

```bash
# Verificar se MongoDB está rodando
docker-compose ps mongodb

# Verificar logs do MongoDB
docker-compose logs mongodb

# Testar conexão
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Verificar variáveis de ambiente
docker-compose exec django-app env | grep MONGO
```

#### 5. Evolution API não responde

```bash
# Verificar logs
docker-compose logs evolution-api

# Verificar se está rodando
curl http://localhost:8080/manager

# Reiniciar serviço
docker-compose restart evolution-api

# Verificar configuração
docker-compose exec evolution-api env | grep EVOLUTION
```

### Comandos de Diagnóstico

```bash
# Informações do sistema
make info

# Verificar uso de espaço
docker system df

# Verificar imagens
docker images

# Verificar volumes
docker volume ls

# Verificar redes
docker network ls

# Inspecionar container
docker inspect <container_name>

# Verificar recursos
docker stats --no-stream
```

### Limpeza e Manutenção

```bash
# Limpeza completa
make clean

# Remover containers parados
docker container prune -f

# Remover imagens não utilizadas
docker image prune -f

# Remover volumes não utilizados
docker volume prune -f

# Remover redes não utilizadas
docker network prune -f

# Limpeza completa do sistema
docker system prune -a -f
```

## 🔄 Atualizações

### Atualizar Imagens

```bash
# Atualizar todas as imagens
make update

# Atualizar imagem específica
docker-compose pull evolution-api

# Rebuild após atualização
make rebuild
```

### Atualizar Código

```bash
# Para desenvolvimento (hot reload automático)
git pull origin main

# Para produção
git pull origin main
docker-compose -f docker-compose.yml up -d --build django-app
```

## 📊 Monitoramento

### Logs em Tempo Real

```bash
# Todos os serviços
docker-compose logs -f

# Serviço específico
docker-compose logs -f django-app

# Últimas N linhas
docker-compose logs --tail=100 django-app

# Filtrar por nível de log
docker-compose logs django-app | grep ERROR
docker-compose logs django-app | grep WARNING
```

### Métricas de Performance

```bash
# Uso de recursos em tempo real
docker stats

# Uso de recursos específico
docker stats django-app evolution-api

# Informações detalhadas
docker inspect django-app | jq '.[0].State'
```

## 🔐 Segurança

### Verificações de Segurança

```bash
# Verificar variáveis de ambiente
docker-compose config

# Verificar portas expostas
docker-compose ps

# Verificar usuários dos containers
docker-compose exec django-app whoami
docker-compose exec evolution-api whoami

# Verificar permissões
docker-compose exec django-app ls -la /app
```

### Rotação de Senhas

```bash
# Gerar novas senhas
openssl rand -base64 32

# Atualizar .env
vim .env

# Reiniciar serviços
docker-compose down
docker-compose up -d
```

## 📱 URLs de Acesso

- **Django Admin**: http://localhost:8000/admin/
- **Django App**: http://localhost:8000/
- **Evolution API**: http://localhost:8080
- **MongoDB Express**: http://localhost:8081 (apenas dev-tools)
- **Redis Commander**: http://localhost:8082 (apenas dev-tools)
- **Webhook WhatsApp**: http://localhost:8000/oraculo/webhook_whatsapp/

## 📞 Suporte

Para problemas não cobertos neste guia:

1. Verifique os logs: `docker-compose logs`
2. Execute health check: `python scripts/health-check.py`
3. Consulte a documentação do Docker
4. Verifique issues no repositório do projeto
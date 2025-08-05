# Configuração Docker - Smart Core Assistant Painel

Este documento descreve como configurar e executar o Smart Core Assistant Painel junto com a Evolution API usando Docker e Docker Compose.

## 📋 Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

## 🚀 Configuração Inicial

### 1. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure suas variáveis:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Django Configuration
SECRET_KEY_DJANGO=sua-chave-secreta-django-aqui
DJANGO_DEBUG=False

# OpenAI Configuration
OPENAI_API_KEY=sua-chave-openai-aqui

# Evolution API Configuration
EVOLUTION_API_KEY=sua-chave-evolution-api-aqui

# Database Configuration
MONGO_USERNAME=admin
MONGO_PASSWORD=senha-segura-mongo

# Redis Configuration
REDIS_PASSWORD=senha-segura-redis
```

### 2. Gerar Chave Secreta Django

Para gerar uma chave secreta segura:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 🏗️ Ambientes Disponíveis

### Produção

Para ambiente de produção com todas as otimizações:

```bash
# Construir e iniciar todos os serviços
docker-compose up -d

# Verificar status dos containers
docker-compose ps

# Visualizar logs
docker-compose logs -f
```

### Desenvolvimento

Para desenvolvimento com hot reload e ferramentas de debug:

```bash
# Usar configuração de desenvolvimento
docker-compose up -d

# Com ferramentas de visualização (MongoDB Express e Redis Commander)
docker-compose --profile tools up -d
```

### Apenas Produção com Nginx

Para usar com proxy reverso Nginx:

```bash
docker-compose --profile production up -d
```

## 🔧 Serviços Incluídos

### Django Application (smart-core-assistant)
- **Porta**: 8000
- **Descrição**: Aplicação principal Django
- **Health Check**: `/admin/`
- **Volumes**: Banco SQLite, media files, static files

### Django Q Cluster (smart-core-qcluster)
- **Descrição**: Processamento assíncrono de tarefas
- **Dependências**: Redis, Django App

### Evolution API (evolution-api)
- **Porta**: 8080
- **Descrição**: API para integração WhatsApp
- **Versão**: v2.1.1
- **Webhook**: Configurado para Django app

### MongoDB (mongodb)
- **Porta**: 27017
- **Descrição**: Banco de dados para Evolution API
- **Usuário**: admin (configurável)

### Redis (redis)
- **Porta**: 6379
- **Descrição**: Cache e filas para Django Q
- **Persistência**: Habilitada

### Nginx (nginx-proxy) - Opcional
- **Portas**: 80, 443
- **Descrição**: Proxy reverso com rate limiting
- **Profile**: production

## 🛠️ Comandos Úteis

### Gerenciamento de Containers

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Reconstruir imagens
docker-compose build --no-cache

# Reiniciar um serviço específico
docker-compose restart django-app

# Visualizar logs de um serviço
docker-compose logs -f django-app
```

### Django Management

```bash
# Executar migrações
docker-compose exec django-app python src/smart_core_assistant_painel/app/ui/manage.py migrate

# Criar superusuário
docker-compose exec django-app python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser

# Coletar arquivos estáticos
docker-compose exec django-app python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput

# Acessar shell Django
docker-compose exec django-app python src/smart_core_assistant_painel/app/ui/manage.py shell
```

### Backup e Restore

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /data/backup

# Backup Redis
docker-compose exec redis redis-cli --rdb /data/backup.rdb

# Backup SQLite
docker cp smart-core-assistant:/app/src/smart_core_assistant_painel/app/ui/db ./backup/
```

## 🔍 Monitoramento e Debug

### URLs de Acesso

- **Django Admin**: http://localhost:8000/admin/
- **Evolution API**: http://localhost:8080
- **MongoDB Express** (dev): http://localhost:8081
- **Redis Commander** (dev): http://localhost:8082

### Health Checks

Todos os serviços possuem health checks configurados:

```bash
# Verificar status de saúde
docker-compose ps

# Detalhes do health check
docker inspect smart-core-assistant | grep -A 10 Health
```

### Logs

```bash
# Logs de todos os serviços
docker-compose logs -f

# Logs de um serviço específico
docker-compose logs -f django-app

# Logs com timestamp
docker-compose logs -f -t django-app
```

## 🔒 Segurança

### Configurações de Segurança Implementadas

1. **Usuário não-root** nos containers
2. **Health checks** para todos os serviços
3. **Rate limiting** no Nginx
4. **Senhas configuráveis** para todos os serviços
5. **Rede isolada** para comunicação entre containers
6. **Headers de segurança** no Nginx

### Recomendações Adicionais

1. **Altere todas as senhas padrão**
2. **Use HTTPS em produção**
3. **Configure firewall** adequadamente
4. **Monitore logs** regularmente
5. **Mantenha imagens atualizadas**

## 🚨 Troubleshooting

### Problemas Comuns

#### Container não inicia
```bash
# Verificar logs
docker-compose logs django-app

# Verificar configuração
docker-compose config
```

#### Erro de conexão com banco
```bash
# Verificar se MongoDB está rodando
docker-compose ps mongodb

# Testar conexão
docker-compose exec django-app python -c "import pymongo; print('OK')"
```

#### Evolution API não conecta
```bash
# Verificar logs da Evolution API
docker-compose logs evolution-api

# Verificar webhook
curl -X POST http://localhost:8000/oraculo/webhook_whatsapp/
```

#### Problemas de permissão
```bash
# Corrigir permissões
sudo chown -R $USER:$USER ./src/smart_core_assistant_painel/app/ui/db
sudo chown -R $USER:$USER ./src/smart_core_assistant_painel/app/ui/media
```

### Limpeza Completa

Para remover tudo e começar do zero:

```bash
# Parar e remover containers, redes e volumes
docker-compose down -v --remove-orphans

# Remover imagens
docker-compose down --rmi all

# Limpeza geral do Docker
docker system prune -a
```

## 📊 Performance

### Otimizações Implementadas

1. **Multi-stage builds** para imagens menores
2. **Cache de dependências** com uv
3. **Compressão gzip** no Nginx
4. **Volumes nomeados** para persistência
5. **Health checks** otimizados
6. **Resource limits** configuráveis

### Monitoramento de Recursos

```bash
# Uso de recursos por container
docker stats

# Informações detalhadas
docker-compose top
```

## 🔄 Atualizações

### Atualizar Evolution API

```bash
# Parar serviço
docker-compose stop evolution-api

# Atualizar imagem
docker-compose pull evolution-api

# Reiniciar
docker-compose up -d evolution-api
```

### Atualizar Aplicação Django

```bash
# Reconstruir imagem
docker-compose build django-app

# Reiniciar com nova imagem
docker-compose up -d django-app
```

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique os logs dos containers
2. Consulte a documentação da Evolution API
3. Verifique as configurações de rede
4. Teste as conexões entre serviços

---

**Nota**: Esta configuração segue as melhores práticas de Docker e está otimizada para produção e desenvolvimento.
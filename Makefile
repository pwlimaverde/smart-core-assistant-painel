# Makefile para Smart Core Assistant Painel + Evolution API
# Facilita o gerenciamento dos comandos Docker

# Variáveis
DOCKER_COMPOSE_PROD = docker-compose.yml
DOCKER_COMPOSE_DEV = docker-compose.yml
DJANGO_SERVICE = django-app
PROJECT_NAME = smart-core-assistant-painel
DOCKER_COMPOSE_CMD = docker compose

# Cores para output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

# Comandos padrão
.PHONY: help
help: ## Mostra esta ajuda
	@echo "$(BLUE)Smart Core Assistant Painel - Comandos Docker$(NC)"
	@echo "================================================"
	@echo ""
	@echo "$(YELLOW)Comandos de Setup:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(setup|install|init)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Comandos de Desenvolvimento:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(dev|test|lint|format)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Comandos de Produção:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(prod|deploy|release)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Comandos de Gerenciamento:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -vE '(setup|install|init|dev|test|lint|format|prod|deploy|release)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Setup e Instalação
.PHONY: setup
setup: ## Configuração inicial completa (Windows)
	@echo "$(BLUE)🚀 Configuração inicial...$(NC)"
	@powershell -ExecutionPolicy Bypass -File scripts/setup-docker.ps1

.PHONY: setup-linux
setup-linux: ## Configuração inicial completa (Linux/Mac)
	@echo "$(BLUE)🚀 Configuração inicial...$(NC)"
	@chmod +x scripts/setup-docker.sh
	@./scripts/setup-docker.sh

.PHONY: init-env
init-env: ## Cria arquivo .env a partir do exemplo
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✅ Arquivo .env criado. Configure as variáveis necessárias.$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Arquivo .env já existe.$(NC)"; \
	fi

# Desenvolvimento
.PHONY: dev
dev: ## Inicia ambiente de desenvolvimento
	@echo "$(BLUE)🚀 Iniciando ambiente de desenvolvimento...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) up -d
	@echo "$(GREEN)✅ Ambiente de desenvolvimento iniciado!$(NC)"
	@echo "$(BLUE)📱 URLs disponíveis:$(NC)"
	@echo "   - Django: http://localhost:8000"
	@echo "   - Evolution API: http://localhost:8080"

.PHONY: dev-tools
dev-tools: ## Inicia desenvolvimento com ferramentas (MongoDB Express, Redis Commander)
	@echo "$(BLUE)🚀 Iniciando desenvolvimento com ferramentas...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) --profile tools up -d
	@echo "$(GREEN)✅ Ambiente de desenvolvimento com ferramentas iniciado!$(NC)"
	@echo "$(BLUE)📱 URLs disponíveis:$(NC)"
	@echo "   - Django: http://localhost:8000"
	@echo "   - Evolution API: http://localhost:8080"
	@echo "   - MongoDB Express: http://localhost:8081"
	@echo "   - Redis Commander: http://localhost:8082"

.PHONY: dev-build
dev-build: ## Reconstrói e inicia ambiente de desenvolvimento
	@echo "$(BLUE)🔨 Reconstruindo ambiente de desenvolvimento...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) up -d --build

.PHONY: dev-logs
dev-logs: ## Mostra logs do ambiente de desenvolvimento
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) logs -f

# Produção
.PHONY: prod
prod: ## Inicia ambiente de produção
	@echo "$(BLUE)🚀 Iniciando ambiente de produção...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_PROD) up -d
	@echo "$(GREEN)✅ Ambiente de produção iniciado!$(NC)"

.PHONY: prod-build
prod-build: ## Reconstrói e inicia ambiente de produção
	@echo "$(BLUE)🔨 Reconstruindo ambiente de produção...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_PROD) up -d --build

.PHONY: prod-logs
prod-logs: ## Mostra logs do ambiente de produção
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_PROD) logs -f

# Comandos Django
.PHONY: migrate
migrate: ## Executa migrações do Django
	@echo "$(BLUE)📊 Executando migrações...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) python src/smart_core_assistant_painel/app/ui/manage.py migrate

.PHONY: makemigrations
makemigrations: ## Cria novas migrações do Django
	@echo "$(BLUE)📝 Criando migrações...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) python src/smart_core_assistant_painel/app/ui/manage.py makemigrations

.PHONY: createsuperuser
createsuperuser: ## Cria superusuário do Django
	@echo "$(BLUE)👤 Criando superusuário...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser

.PHONY: collectstatic
collectstatic: ## Coleta arquivos estáticos
	@echo "$(BLUE)📁 Coletando arquivos estáticos...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput

.PHONY: shell
shell: ## Abre shell do Django
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) python src/smart_core_assistant_painel/app/ui/manage.py shell

.PHONY: dbshell
dbshell: ## Abre shell do banco de dados
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) python src/smart_core_assistant_painel/app/ui/manage.py dbshell

# Testes e Qualidade
.PHONY: test
test: ## Executa testes
	@echo "$(BLUE)🧪 Executando testes...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) python -m pytest tests/ -v

.PHONY: test-cov
test-cov: ## Executa testes com cobertura
	@echo "$(BLUE)🧪 Executando testes com cobertura...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

.PHONY: lint
lint: ## Executa linting
	@echo "$(BLUE)🔍 Executando linting...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) ruff check src/

.PHONY: format
format: ## Formata código
	@echo "$(BLUE)✨ Formatando código...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) ruff format src/

.PHONY: type-check
type-check: ## Verifica tipos
	@echo "$(BLUE)🔍 Verificando tipos...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) mypy src/

# Gerenciamento de Containers
.PHONY: ps
ps: ## Lista containers
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) ps

.PHONY: logs
logs: ## Mostra logs de todos os serviços
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) logs -f

.PHONY: stop
stop: ## Para todos os serviços
	@echo "$(YELLOW)⏹️  Parando serviços...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) stop
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_PROD) stop

.PHONY: down
down: ## Para e remove containers
	@echo "$(YELLOW)🗑️  Removendo containers...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) down
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_PROD) down

.PHONY: restart
restart: ## Reinicia serviços
	@echo "$(BLUE)🔄 Reiniciando serviços...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) restart

.PHONY: clean
clean: ## Remove containers, volumes e imagens
	@echo "$(RED)🧹 Limpando ambiente Docker...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) down -v --rmi all
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_PROD) down -v --rmi all
	docker system prune -f

# Health Check
.PHONY: health
health: ## Verifica saúde dos serviços
	@echo "$(BLUE)🏥 Verificando saúde dos serviços...$(NC)"
	@python scripts/health-check.py

.PHONY: wait-ready
wait-ready: ## Aguarda serviços ficarem prontos
	@echo "$(BLUE)⏳ Aguardando serviços ficarem prontos...$(NC)"
	@python scripts/health-check.py --wait

# Backup e Restore
.PHONY: backup-db
backup-db: ## Backup do banco de dados
	@echo "$(BLUE)💾 Fazendo backup do banco...$(NC)"
	@mkdir -p backups
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec mongodb mongodump --out /tmp/backup
	docker cp $$($(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) ps -q mongodb):/tmp/backup ./backups/mongodb-$$(date +%Y%m%d_%H%M%S)
	@echo "$(GREEN)✅ Backup concluído!$(NC)"

.PHONY: backup-redis
backup-redis: ## Backup do Redis
	@echo "$(BLUE)💾 Fazendo backup do Redis...$(NC)"
	@mkdir -p backups
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec redis redis-cli BGSAVE
	docker cp $$($(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) ps -q redis):/data/dump.rdb ./backups/redis-$$(date +%Y%m%d_%H%M%S).rdb
	@echo "$(GREEN)✅ Backup do Redis concluído!$(NC)"

# Utilitários
.PHONY: exec-django
exec-django: ## Acessa shell do container Django
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec $(DJANGO_SERVICE) bash

.PHONY: exec-mongo
exec-mongo: ## Acessa shell do MongoDB
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec mongodb mongosh

.PHONY: exec-redis
exec-redis: ## Acessa shell do Redis
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) exec redis redis-cli

.PHONY: update
update: ## Atualiza imagens Docker
	@echo "$(BLUE)🔄 Atualizando imagens...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) pull
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_PROD) pull

.PHONY: rebuild
rebuild: ## Reconstrói todas as imagens
	@echo "$(BLUE)🔨 Reconstruindo todas as imagens...$(NC)"
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_DEV) build --no-cache
	$(DOCKER_COMPOSE_CMD) -f $(DOCKER_COMPOSE_PROD) build --no-cache

# Comandos de informação
.PHONY: info
info: ## Mostra informações do ambiente
	@echo "$(BLUE)ℹ️  Informações do Ambiente$(NC)"
	@echo "================================"
	@echo "Docker Version:"
	@docker --version
	@echo "\nDocker Compose Version:"
	@$(DOCKER_COMPOSE_CMD) --version
	@echo "\nContainers em execução:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo "\nUso de espaço:"
	@docker system df

.PHONY: urls
urls: ## Mostra URLs disponíveis
	@echo "$(BLUE)📱 URLs Disponíveis$(NC)"
	@echo "=================="
	@echo "Django Admin: http://localhost:8000/admin/"
	@echo "Django App: http://localhost:8000/"
	@echo "Evolution API: http://localhost:8080"
	@echo "MongoDB Express: http://localhost:8081 (apenas em dev-tools)"
	@echo "Redis Commander: http://localhost:8082 (apenas em dev-tools)"
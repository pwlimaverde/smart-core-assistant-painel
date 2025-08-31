# Makefile - Ambiente Base de Dados (Smart Core Assistant Painel)

DOCKER_COMPOSE = docker compose
DOCKER_COMPOSE_PROJECT = ambiente_base_dados
POSTGRES_SERVICE = postgres-remote
REDIS_SERVICE = redis-remote

.PHONY: help
help: ## Mostra esta ajuda
	@echo "Ambiente Base de Dados - Comandos" 
	@echo "================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Desenvolvimento
.PHONY: dev
dev: ## Sobe o ambiente (build + up)
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) up -d --build

.PHONY: dev-build
dev-build: ## Reconstrói as imagens sem cache
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) build --no-cache
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) up -d

.PHONY: dev-logs
dev-logs: ## Mostra logs do ambiente
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) logs -f

# Banco de Dados
.PHONY: psql
psql: ## Abre shell do PostgreSQL
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) exec $(POSTGRES_SERVICE) psql -U postgres -d smart_core_db

.PHONY: redis-cli
redis-cli: ## Abre shell do Redis
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) exec $(REDIS_SERVICE) redis-cli

# Serviços
.PHONY: ps
ps: ## Lista containers
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) ps

.PHONY: logs
logs: ## Mostra logs de todos os serviços
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) logs -f

.PHONY: stop
stop: ## Para todos os serviços
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) stop

.PHONY: down
down: ## Para e remove containers e volumes
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) down -v --remove-orphans

.PHONY: restart
restart: ## Reinicia serviços
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) restart

.PHONY: clean
clean: ## Remove containers, volumes e imagens não utilizadas
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) down -v --rmi all --remove-orphans
	docker system prune -f

# Informações
.PHONY: info
info: ## Mostra informações do ambiente
	@echo "Docker Version:" && docker --version
	@echo "\nDocker Compose Version:" && $(DOCKER_COMPOSE) --version
	@echo "\nContainers em execução:" && docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

.PHONY: status
status: ## Mostra status dos serviços do ambiente base de dados
	@echo "Status dos serviços do ambiente base de dados:"
	$(DOCKER_COMPOSE) -p $(DOCKER_COMPOSE_PROJECT) ps
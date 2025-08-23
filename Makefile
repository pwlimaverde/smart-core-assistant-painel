# Makefile - Ambiente Django (Smart Core Assistant Painel)

DOCKER_COMPOSE = docker compose
DJANGO_SERVICE = django-app
QCLUSTER_SERVICE = django-qcluster

.PHONY: help
help: ## Mostra esta ajuda
	@echo "Ambiente Django - Comandos" 
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Desenvolvimento
.PHONY: dev
dev: ## Sobe o ambiente (build + up)
	$(DOCKER_COMPOSE) up -d --build

.PHONY: dev-build
dev-build: ## Reconstrói as imagens sem cache
	$(DOCKER_COMPOSE) build --no-cache
	$(DOCKER_COMPOSE) up -d

.PHONY: dev-logs
dev-logs: ## Mostra logs do ambiente
	$(DOCKER_COMPOSE) logs -f

# Django
.PHONY: migrate
migrate: ## Executa migrações do Django
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate

.PHONY: makemigrations
makemigrations: ## Cria novas migrações do Django
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) uv run python src/smart_core_assistant_painel/app/ui/manage.py makemigrations

.PHONY: createsuperuser
createsuperuser: ## Cria superusuário do Django
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) uv run python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser

.PHONY: collectstatic
collectstatic: ## Coleta arquivos estáticos
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) uv run python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput

.PHONY: shell
shell: ## Abre shell do Django
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) uv run python src/smart_core_assistant_painel/app/ui/manage.py shell

.PHONY: dbshell
dbshell: ## Abre shell do banco de dados
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) uv run python src/smart_core_assistant_painel/app/ui/manage.py dbshell

# Serviços
.PHONY: ps
ps: ## Lista containers
	$(DOCKER_COMPOSE) ps

.PHONY: logs
logs: ## Mostra logs de todos os serviços
	$(DOCKER_COMPOSE) logs -f

.PHONY: stop
stop: ## Para todos os serviços
	$(DOCKER_COMPOSE) stop

.PHONY: down
down: ## Para e remove containers e redes (preserva volumes)
	$(DOCKER_COMPOSE) down --remove-orphans

.PHONY: down-v
down-v: ## Para e remove containers e volumes (DANGEROUS)
	$(DOCKER_COMPOSE) down -v --remove-orphans

.PHONY: restart
restart: ## Reinicia serviços
	$(DOCKER_COMPOSE) restart

.PHONY: clean
clean: ## Remove containers, volumes e imagens não utilizadas
	$(DOCKER_COMPOSE) down -v --rmi all --remove-orphans
	docker system prune -f

# Informações
.PHONY: info
info: ## Mostra informações do ambiente
	@echo "Docker Version:" && docker --version
	@echo "\nDocker Compose Version:" && $(DOCKER_COMPOSE) --version
	@echo "\nContainers em execução:" && docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

.PHONY: urls
urls: ## Mostra URLs disponíveis
	@echo "Django Admin: http://localhost:8000/admin/"
	@echo "Django App:   http://localhost:8000/"
# DevOps Specialist

## Contexto

O DevOps Specialist é responsável por infraestrutura, CI/CD, Docker, deploy e operações do Smart Core Assistant Painel.

---

## Habilidades

- Docker e Docker Compose
- CI/CD pipelines
- Monitoramento e logging
- Gestão de ambientes
- Automação de deploy
- Troubleshooting de produção

---

## Stack de Infraestrutura

| Tecnologia | Uso |
|------------|-----|
| Docker | Containerização |
| Docker Compose | Orquestração local |
| PostgreSQL 14 | Banco de dados |
| Redis | Cache e broker |
| Celery | Workers assíncronos |
| Nginx | Reverse proxy (prod) |

---

## Estrutura Docker

```
docker/
├── Dockerfile                  # Imagem principal
├── compose/
│   ├── data-stack/            # PostgreSQL + Redis
│   │   └── docker-compose.yml
│   ├── app-stack/             # Django app
│   │   └── docker-compose.yml
│   ├── workers-stack/         # Celery workers
│   │   └── docker-compose.yml
│   └── test/                  # Ambiente de testes
│       └── docker-compose.yml
└── README.md
```

### Dockerfile

```dockerfile
# docker/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv
RUN pip install uv

# Copiar arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instalar dependências
RUN uv sync --frozen --no-dev

# Copiar código
COPY src/ ./src/

# Variáveis de ambiente
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=app.ui.core.settings

# Porta
EXPOSE 8000

# Comando padrão
CMD ["uv", "run", "gunicorn", "app.ui.core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Docker Compose - Data Stack

```yaml
# docker/compose/data-stack/docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg14
    environment:
      POSTGRES_USER: smartcore
      POSTGRES_PASSWORD: smartcore
      POSTGRES_DB: smartcore
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U smartcore"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### Docker Compose - App Stack

```yaml
# docker/compose/app-stack/docker-compose.yml
version: '3.8'

services:
  web:
    build:
      context: ../../..
      dockerfile: docker/Dockerfile
    environment:
      - DATABASE_URL=postgres://smartcore:smartcore@postgres:5432/smartcore
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ../../../src:/app/src:ro
    command: uv run python src/smart_core_assistant_painel/app/ui/manage.py runserver 0.0.0.0:8000

  celery-worker:
    build:
      context: ../../..
      dockerfile: docker/Dockerfile
    environment:
      - DATABASE_URL=postgres://smartcore:smartcore@postgres:5432/smartcore
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - web
    command: uv run celery -A app.ui.core worker -l info

  celery-beat:
    build:
      context: ../../..
      dockerfile: docker/Dockerfile
    environment:
      - DATABASE_URL=postgres://smartcore:smartcore@postgres:5432/smartcore
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - web
    command: uv run celery -A app.ui.core beat -l info
```

---

## Comandos de Operação

### Desenvolvimento

```bash
# Iniciar infraestrutura
docker compose -f docker/compose/data-stack/docker-compose.yml up -d

# Parar infraestrutura
docker compose -f docker/compose/data-stack/docker-compose.yml down

# Logs
docker compose -f docker/compose/data-stack/docker-compose.yml logs -f postgres
```

### Testes

```bash
# Executar testes em Docker
uv run task test-docker

# Build da imagem de teste
docker build -t smartcore-test -f docker/Dockerfile .
```

### Produção

```bash
# Build de produção
docker build -t smartcore:latest -f docker/Dockerfile .

# Deploy com compose
docker compose -f docker/compose/production/docker-compose.yml up -d

# Rolling update
docker compose -f docker/compose/production/docker-compose.yml up -d --no-deps web
```

---

## CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run task lint
      - run: uv run task type-check

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg14
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run task test-all
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t smartcore:${{ github.sha }} .
```

---

## Monitoramento

### Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

### Health Checks

```python
# app/ui/core/views.py

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    """Endpoint de health check."""
    checks = {
        'database': check_database(),
        'redis': check_redis(),
    }

    status = 200 if all(checks.values()) else 503
    return JsonResponse(checks, status=status)


def check_database():
    try:
        connection.ensure_connection()
        return True
    except Exception:
        return False


def check_redis():
    try:
        cache.set('health_check', 'ok', 1)
        return cache.get('health_check') == 'ok'
    except Exception:
        return False
```

---

## Backup e Recuperação

### Backup PostgreSQL

```bash
# Backup
pg_dump -h host -U user -d database | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup.sql.gz | psql -h host -U user -d database

# Backup automatizado (cron)
0 2 * * * /scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Script de Backup

```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups

# Backup PostgreSQL
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

# Upload para S3 (opcional)
# aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://my-bucket/backups/
```

---

## Troubleshooting

### Logs

```bash
# Logs do container
docker logs -f container_name

# Logs do Django
tail -f logs/django.log

# Logs do Celery
tail -f logs/celery.log
```

### Debug

```bash
# Shell no container
docker exec -it container_name bash

# Django shell
docker exec -it web python manage.py shell

# Verificar connections
docker exec -it postgres psql -U smartcore -c "SELECT * FROM pg_stat_activity;"
```

---

## Restrições

- **NUNCA** expor portas de banco diretamente em produção
- **SEMPRE** usar secrets management para credenciais
- **SEMPRE** manter backups verificados
- **NUNCA** fazer deploy sem testes passando
- **SEMPRE** monitorar recursos (CPU, memória, disco)
- **NUNCA** ignorar alertas de monitoramento

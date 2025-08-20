# Ambiente Misto - Smart Core Assistant Painel

Este ambiente foi criado para resolver o problema de desenvolvimento no Windows, onde a aplicação Django executa localmente (fora de containers) e os serviços de banco de dados (PostgreSQL e Redis) executam em containers Docker.

## Arquitectura

- **PostgreSQL**: Container Docker (porta 5436)
- **Redis**: Container Docker (porta 6382) 
- **Aplicação Django**: Execução local

## Pré-requisitos

1. **Docker Desktop** instalado e em execução
2. **Python 3.13+** 
3. **uv** (gerenciador de dependências)

## Configuração Inicial

### 1. Executar Setup

**Windows:**
```bash
# Na raiz do projeto
.\ambiente_misto\setup.bat
```

**Linux/macOS:**
```bash
# Na raiz do projeto
chmod +x ambiente_misto/setup.sh
./ambiente_misto/setup.sh
```

## O que o Script de Setup Faz

1. **Verificação de arquivos**: Confirma existência de `.env` e cria `firebase_key.json` a partir de variável de ambiente.
2. **Configuração Git**: Configura Git para ignorar mudanças locais nos arquivos de configuração.
3. **Ajuste do settings.py**:
   - Define `POSTGRES_HOST=localhost` e `POSTGRES_PORT=5436`
   - Configura Redis como cache padrão (`django_redis.cache.RedisCache`)
   - Usa variáveis `REDIS_HOST` e `REDIS_PORT` para conectividade
4. **Criação do docker-compose.yml**: Gera arquivo com PostgreSQL (5436:5432) e Redis (6382:6379) e define o nome do projeto como `<nome_da_pasta_raiz>-amb-misto`.
5. **Limpeza do Dockerfile**: Comenta `ENTRYPOINT` e `CMD` para desenvolvimento local.
6. **Subida dos containers**: Força a remoção de containers antigos e executa `docker compose up -d`.
7. **Criação e aplicação de migrações**: Executa `makemigrations` e `migrate` usando o python do ambiente virtual para garantir que as variáveis de ambiente sejam carregadas corretamente.
8. **Criação de superusuário**: Executa `createsuperuser` de forma idempotente.

## Execução da Aplicação

Depois do setup inicial, para iniciar a aplicação:

```bash
# Na raiz do projeto
uv run task start
```

O servidor estará disponível em: http://127.0.0.1:8000/

## Troubleshooting

### Erro `google.auth.exceptions.DefaultCredentialsError` ou `RefreshError`

Este erro ocorre quando a aplicação não consegue encontrar as credenciais do Firebase. Isso pode acontecer por alguns motivos:

1.  **O arquivo `.env` não está sendo carregado corretamente.** Os scripts de setup foram ajustados para forçar o carregamento do `.env` usando `python -m dotenv.cli run` antes de executar os comandos do Django.
2.  **A dependência `python-dotenv[cli]` não está instalada.** O `pyproject.toml` foi ajustado para incluir a opção `[cli]`. Caso o erro persista, garanta que a dependência está instalada corretamente executando:
    ```bash
    uv pip install "python-dotenv[cli]"
    ```

### Erro de conflito de containers

O script de setup agora força a remoção dos containers `postgres_db` e `redis_cache` antes de recriá-los para evitar conflitos de nome.

## Configurações Locais do Git 

O script configura o Git para ignorar mudanças locais em:
- `docker-compose.yml` 
- `settings.py`
- `Dockerfile`

Para desfazer (quando necessário):
```bash
git update-index --no-assume-unchanged docker-compose.yml src/smart_core_assistant_painel/app/ui/core/settings.py Dockerfile
```

## Cache Redis vs Memória Local

**Configuração Padrão (Redis):**
- Usa `django_redis.cache.RedisCache`
- Host: `REDIS_HOST` (fallback: localhost)
- Porta: `REDIS_PORT` (fallback: 6382)
- Melhor performance e persistência

**Alternativa (Cache em Memória):**

Se preferir usar cache local em vez de Redis, edite manualmente o `settings.py`:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
```

## Comandos Úteis

### Gerenciamento Docker
```bash
# Ver status dos containers
docker ps

# Parar containers
docker compose down

# Reiniciar containers
docker compose down && docker compose up -d

# Ver logs 
docker compose logs -f postgres
docker compose logs -f redis
```

### Comandos Django (via taskipy)
```bash
# Migrações
uv run task migrate
uv run task makemigrations

# Criar superusuário
uv run task createsuperuser

# Shell do Django
uv run task shell

# Testes
uv run task test

# Linting e formatação
uv run task lint
uv run task format
```

## Validação do Cache Redis

Para testar se o cache Redis está funcionando:

```bash
# Abrir shell do Django
uv run task shell

# Dentro do shell:
from django.core.cache import cache
cache.set('test_key', 'test_value', 60)
print(cache.get('test_key'))  # Deve retornar: test_value
```

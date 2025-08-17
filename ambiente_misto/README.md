# Ambiente Misto - Smart Core Assistant Painel

Este ambiente foi criado para resolver o problema de desenvolvimento no Windows, onde a aplicação Django executa localmente (fora de containers) e os serviços de banco de dados (PostgreSQL e Redis) executam em containers Docker.

## Arquitectura

- **PostgreSQL**: Container Docker (porta 5436)
- **Redis**: Container Docker (porta 6382) 
- **Aplicação Django**: Execução local no Windows

## Pré-requisitos

1. **Docker Desktop** instalado e em execução
2. **Python 3.13+** 
3. **uv** (gerenciador de dependências)

## Configuração Inicial

### 1. Executar Setup

**Windows:**
```bash
cd ambiente_misto
setup.bat
```

**Linux/macOS:**
```bash
cd ambiente_misto
chmod +x setup.sh
./setup.sh
```

## O que o Script de Setup Faz

1. **Verificação de arquivos**: Confirma existência de `.env` e `firebase_key.json`
2. **Movimentação de credenciais**: Move `firebase_key.json` para pasta adequada
3. **Configuração Git**: Configura Git para ignorar mudanças locais nos arquivos de configuração
4. **Ajuste do settings.py**:
   - Define `POSTGRES_HOST=localhost` e `POSTGRES_PORT=5436`
   - Configura Redis como cache padrão (`django_redis.cache.RedisCache`)
   - Usa variáveis `REDIS_HOST` e `REDIS_PORT` para conectividade
5. **Criação do docker-compose.yml**: Gera arquivo com PostgreSQL (5436:5432) e Redis (6382:6379)
6. **Limpeza do Dockerfile**: Comenta `ENTRYPOINT` e `CMD` para desenvolvimento local
7. **Subida dos containers**: Executa `docker-compose up -d`
8. **Instalação de dependências**: Executa `uv sync --dev`
9. **Aplicação de migrações**: Executa `uv run task migrate`
10. **Criação de superusuário**: Executa `uv run task createsuperuser`

## Execução da Aplicação

Depois do setup inicial, para iniciar a aplicação:

```bash
# Na raiz do projeto (não no ambiente_misto)
uv run task start
```

O servidor estará disponível em: http://127.0.0.1:8000/

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
docker-compose down

# Reiniciar containers
docker-compose down && docker-compose up -d

# Ver logs 
docker-compose logs -f postgres
docker-compose logs -f redis
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

## Resolução do Problema de Conexão PostgreSQL

### Problema Original

O projeto enfrentava erro `psycopg.OperationalError` devido a inconsistências nas configurações de porta do PostgreSQL:

- **docker-compose.yml**: Expunha PostgreSQL na porta 5433
- **settings.py**: Usava porta 5435 como padrão 
- **.env**: Definia POSTGRES_PORT=5436

### Solução Implementada

1. **Padronização da porta**: Todos os componentes agora usam **porta 5436**
2. **Configuração de host**: `settings.py` usa `localhost` por padrão no ambiente misto
3. **Cache Redis**: Migrado de `LocMemCache` para `RedisCache` com configuração via variáveis de ambiente
4. **Containers Docker**: PostgreSQL mapeado para `5436:5432`, Redis para `6382:6379`
5. **Recriação de containers**: Garantiu limpeza completa do ambiente

### Para Usuários Windows

1. **Verificar .env**: Confirme que `POSTGRES_PORT=5436` e `REDIS_PORT=6382`
2. **Subir serviços**: Execute o script `ambiente_misto/setup.bat`
3. **Aplicar migrações**: Automaticamente feito pelo script
4. **Iniciar servidor**: `uv run task start`

### Checklist de Verificação Rápida

- [ ] Docker Desktop está rodando
- [ ] Arquivo `.env` configurado corretamente
- [ ] Credenciais `firebase_key.json` no lugar certo
- [ ] Containers PostgreSQL e Redis estão ativos (`docker ps`)
- [ ] Porta 5436 está livre para PostgreSQL
- [ ] Porta 6382 está livre para Redis
- [ ] Migrações aplicadas sem erro
- [ ] Cache Redis funcionando

### Próximos Passos Recomendados

1. **Executar testes**: `uv run task test`
2. **Verificar linting**: `uv run task lint`
3. **Checar tipagem**: `uv run task type-check`

### Observações Importantes

- Os arquivos `settings.py`, `docker-compose.yml` e `Dockerfile` ficam ignorados pelo Git após o setup
- Para reverter configurações, use os comandos Git mencionados na seção "Configurações Locais do Git"
- O ambiente é específico para desenvolvimento - não use em produção
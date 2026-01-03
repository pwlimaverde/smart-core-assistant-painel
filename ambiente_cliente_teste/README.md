# Ambiente de Teste Local - Smart Core Assistant

Este diretório contém a configuração Docker para testar o ambiente do cliente localmente.

## Arquitetura

O ambiente utiliza **containers completamente separados** para evitar conflitos:

### Ambiente Cliente (Sistema Django)

| Serviço | Container | Porta Local |
|---------|-----------|-------------|
| PostgreSQL | `smartcore_cliente_postgres_teste` | 5436 |
| Redis | `smartcore_cliente_redis_teste` | 6382 |

### Ambiente Evolution (WhatsApp API)

| Serviço | Container | Porta Local |
|---------|-----------|-------------|
| PostgreSQL | `smartcore_evolution_postgres_teste` | 5437 |
| Redis | `smartcore_evolution_redis_teste` | 6383 |
| Evolution API | `smartcore_evolution_teste` | 8080 |

## Configuração

1. **Copie o arquivo de ambiente:**
   ```powershell
   Copy-Item .env.local .env
   ```

2. **Suba os containers:**
   ```powershell
   docker compose up -d
   ```

3. **Verifique os serviços:**
   ```powershell
   docker compose ps
   ```

## Endpoints

### Ambiente Cliente (Django)
- **PostgreSQL:** `192.168.3.127:5436` (banco: `smartcore_cliente_db`)
- **Redis:** `192.168.3.127:6382`

### Ambiente Evolution (WhatsApp)
- **PostgreSQL:** `192.168.3.127:5437` (banco: `smartcore_evolution_db`)
- **Redis:** `192.168.3.127:6383`
- **Evolution API:** `http://192.168.3.127:8080`

## Webhook

O webhook está configurado para apontar para o Django local em:
```
http://192.168.3.90:8000/sync/evolution/webhook/
```

## Comandos Úteis

```bash
# Ver status dos containers
docker compose ps

# Ver logs de todos os containers
docker compose logs -f

# Logs específicos de cada serviço
docker compose logs -f postgres_cliente
docker compose logs -f postgres_evolution
docker compose logs -f redis_cliente
docker compose logs -f redis_evolution
docker compose logs -f evolution

# Reiniciar tudo
docker compose restart

# Parar e remover containers
docker compose down

# Parar e remover containers + volumes (CUIDADO: apaga dados!)
docker compose down -v
```

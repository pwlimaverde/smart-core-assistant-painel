# Configurações Globais (CoreSettings)

Backup e sincronização das configurações globais do sistema.

## Arquivos

| Arquivo                     | Descrição                                     |
| --------------------------- | --------------------------------------------- |
| `coresettings.json`         | Dados das 24 configurações com descrições     |
| `sync_coresettings.py`      | Script para dump/restore no banco LOCAL (dev) |
| `sync_coresettings_prod.py` | Script para dump/restore no banco de PRODUÇÃO |

## Uso - Produção (Hostinger)

```powershell
# Testar conexão SSH com o servidor de produção
uv run python scripts/config_global/sync_coresettings_prod.py test

# Exportar do banco de PRODUÇÃO (atualizar backup local)
uv run python scripts/config_global/sync_coresettings_prod.py dump

# Restaurar no banco de PRODUÇÃO (a partir do backup local)
uv run python scripts/config_global/sync_coresettings_prod.py restore

# Restaurar sem confirmação interativa
uv run python scripts/config_global/sync_coresettings_prod.py restore --yes
```

### Pré-requisitos Produção

- Arquivo `.env.deploy` com credenciais SSH do Hostinger
- Arquivo `.env.prod` com credenciais do PostgreSQL
- Chave SSH configurada (alias `hostinger-root`) ou conexão direta

## Uso - Desenvolvimento (Local)

```powershell
# Exportar do banco local
uv run python scripts/config_global/sync_coresettings.py dump

# Restaurar no banco local
uv run python scripts/config_global/sync_coresettings.py restore --yes
```

## Ambientes

### Produção (Hostinger)

- **SSH Host**: `srv1321059.hstgr.cloud`
- **SSH User**: `root`
- **Container**: `smartcoreassistant_postgres`
- **Banco**: `smart_core_db`

### Desenvolvimento (Local)

- **Host**: `192.168.3.127`
- **Container**: `smartcoreassistant_postgres`
- **Banco**: `smart_core_db`

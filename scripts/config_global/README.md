# Configurações Globais (CoreSettings)

Backup e sincronização das configurações globais do sistema.

## Arquivos

| Arquivo                | Descrição                                 |
| ---------------------- | ----------------------------------------- |
| `coresettings.json`    | Dados das 24 configurações com descrições |
| `sync_coresettings.py` | Script para dump/restore no banco remoto  |

## Uso

```powershell
# Exportar do banco remoto (atualizar backup local)
uv run python scripts/config_global/sync_coresettings.py dump

# Restaurar no banco remoto (a partir do backup local)
uv run python scripts/config_global/sync_coresettings.py restore

# Restaurar sem confirmação interativa
uv run python scripts/config_global/sync_coresettings.py restore --yes
```

## Ambiente Remoto

- **Host**: `192.168.3.127`
- **Container**: `smartcoreassistant_postgres`
- **Banco**: `smart_core_db`

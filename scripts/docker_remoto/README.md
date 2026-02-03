# Docker Remoto

Módulo para gerenciar containers Docker em um servidor remoto via SSH.

## Arquivos

| Arquivo            | Descrição                                                      |
| ------------------ | -------------------------------------------------------------- |
| `manager.py`       | Script Python que executa comandos Docker local ou remotamente |
| `setup_server.ps1` | Script PowerShell para configurar SSH no servidor Windows      |

---

## Configuração Inicial

### 1. Gerar Chave SSH (máquina local)

```powershell
ssh-keygen -t ed25519
```

### 2. Copiar Chave Pública

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

### 3. Configurar Servidor (executar no servidor como Admin)

```powershell
.\setup_server.ps1 -PublicKey "ssh-ed25519 AAAA... seu@host"
```

### 4. Configurar `.env.prod` (máquina local)

```ini
SMART_CORE_DOCKER_HOST=ssh://usuario@ip_do_servidor
```

> O `manager.py` agora aceita `--env-file` para alternar entre ambientes.
> Exemplo: `--env-file .env` (dev-local) e `--env-file .env.prod` (produção).

---

## Comandos Disponíveis

### Docker Compose

```powershell
# Status de todos os containers
uv run task remote-status

# Iniciar stacks
uv run task remote-start-data   # PostgreSQL + Redis
uv run task remote-start-app    # Django

# Rebuild da aplicação
uv run task remote-restart-app

# Ver logs
uv run task remote-logs-app

# Parar tudo
uv run task remote-stop-all
```

### Django Management

```powershell
# Aplicar migrações
uv run task remote-migrate

# Criar superusuário
uv run task remote-createsuperuser

# Shell interativo
uv run task remote-shell

# Coletar arquivos estáticos
uv run task remote-collectstatic
```

---

## Troubleshooting

**SSH pedindo senha:**

- Verifique se a chave está em `C:\ProgramData\ssh\administrators_authorized_keys` no servidor
- Verifique permissões: apenas SYSTEM e Administrators devem ter acesso

**Erro de URL inválida:**

- Não use `\` no nome de usuário (use apenas o nome local, não `DOMINIO\usuario`)

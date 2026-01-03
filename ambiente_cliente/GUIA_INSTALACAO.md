# Guia de Instalação - Smart Core Assistant

Este guia descreve como configurar a infraestrutura necessária para utilizar o Smart Core Assistant em seu próprio servidor (Modelo Core as a Service).

## Pré-requisitos

| Requisito | Especificação |
|-----------|---------------|
| **Servidor** | VPS com mínimo 2GB RAM, 20GB SSD |
| **Sistema** | Ubuntu 22.04+ (recomendado) ou Windows Server/10+ |
| **Rede** | IP fixo ou domínio. Portas: 5432, 5433, 6379, 6380, 8080 |

> [!NOTE]
> O Docker será instalado automaticamente pelo script se não estiver presente.

---

## Arquitetura dos Serviços

O ambiente utiliza **containers completamente separados** para evitar conflitos:

### Ambiente Cliente (Sistema Django)

| Serviço | Container | Porta | Base de Dados |
|---------|-----------|-------|---------------|
| PostgreSQL | `smartcore_cliente_postgres` | 5432 | `smartcore_cliente_db` |
| Redis | `smartcore_cliente_redis` | 6379 | - |

### Ambiente Evolution (WhatsApp API)

| Serviço | Container | Porta | Base de Dados |
|---------|-----------|-------|---------------|
| PostgreSQL | `smartcore_evolution_postgres` | 5433 | `smartcore_evolution_db` |
| Redis | `smartcore_evolution_redis` | 6380 | - |
| Evolution API | `smartcore_evolution` | 8080 | - |

> [!IMPORTANT]
> Os ambientes Cliente e Evolution são **completamente isolados**. Cada um possui seu próprio PostgreSQL e Redis.

---

## Passo 1: Cadastro no Painel

1. Acesse `https://smartcoreassistant.com.br/cadastro`
2. Crie sua conta empresarial
3. Anote o **TENANT_SLUG** fornecido (ex: `minha-empresa`)

---

## Passo 2: Transferir Arquivos para o Servidor

Copie a pasta `ambiente_cliente/` para o servidor:

**Linux** (via SCP):
```bash
scp -r ambiente_cliente/ usuario@seu-servidor:~/smartcore
```

**Windows** (via RDP ou WinSCP):
- Copie a pasta para `C:\smartcore`

---

## Passo 3: Configurar o Arquivo .env

### Linux
```bash
cd ~/smartcore
cp .env.example .env
nano .env
```

### Windows
```powershell
cd C:\smartcore
Copy-Item .env.example .env
notepad .env
```

**Preencha os campos obrigatórios:**

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `TENANT_SLUG` | Identificador do Passo 1 | `minha-empresa` |
| `POSTGRES_PASSWORD` | Senha do banco Django | `MinhaSenha@123` |
| `EVOLUTION_POSTGRES_PASSWORD` | Senha do banco Evolution | `OutraSenha@456` |
| `EVOLUTION_API_KEY` | Chave aleatória (gere com UUID) | `abc123-def456...` |
| `EVOLUTION_SERVER_URL` | URL pública do servidor | `http://SEU_IP:8080` |
| `WEBHOOK_CORE_URL` | URL fornecida no painel | `https://smartcoreassistant.com.br/webhook/SEU_SLUG/evolution/` |

> [!IMPORTANT]
> Use senhas **diferentes** para `POSTGRES_PASSWORD` e `EVOLUTION_POSTGRES_PASSWORD` para maior segurança.

---

## Passo 4: Executar Script de Instalação

### Linux (Ubuntu/Debian)
```bash
chmod +x install.sh
sudo ./install.sh
```

### Windows (PowerShell como Administrador)
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\install.ps1
```

O script automaticamente:
- ✅ Instala Docker (se necessário)
- ✅ Configura firewall (portas 5432, 5433, 6379, 6380, 8080)
- ✅ Valida as variáveis do `.env`
- ✅ Sobe todos os containers
- ✅ Verifica a saúde dos serviços

Ao final, você verá uma mensagem com os endpoints dos serviços.

---

## Passo 5: Configurar no Painel

Acesse `https://smartcoreassistant.com.br/tenants/dashboard/` e configure:

### Aba PostgreSQL (Sistema Django)
| Campo | Valor |
|-------|-------|
| Host | IP do seu servidor |
| Porta | **5432** |
| Banco | `smartcore_cliente_db` |
| Usuário | `smartcore` |
| Senha | (valor de POSTGRES_PASSWORD) |

> [!NOTE]
> O PostgreSQL do Evolution (porta 5433) e os Redis são gerenciados automaticamente e não precisam ser configurados no painel.

### Aba Evolution API
| Campo | Valor |
|-------|-------|
| URL | http://SEU_IP:8080 |
| API Key | (do .env) |
| Instância | atendimento |

### Aba Trello (Opcional)
1. Obtenha API Key em [trello.com/app-key](https://trello.com/app-key)
2. Gere o Token clicando no link "Token"
3. Crie um Board e anote o ID (visível na URL)

---

## Passo 6: Validar e Ativar

1. Clique em **"Testar Conexão"** em cada aba
2. Se todos ficarem verdes, clique em **"Executar Migrations"**
3. Pronto! Seu ambiente está configurado.

---

## Solução de Problemas

| Problema | Solução |
|----------|---------|
| **Conexão recusada no banco Django** | Verifique se a porta 5432 está aberta: `sudo ufw status` |
| **Conexão recusada no banco Evolution** | Verifique se a porta 5433 está aberta |
| **Evolution API offline** | Verifique logs: `docker compose logs -f evolution` |
| **Containers não sobem** | Verifique o .env e logs: `docker compose logs` |
| **Webhook não funciona** | Confirme que `WEBHOOK_CORE_URL` está igual ao painel |

### Comandos Úteis

```bash
# Ver status dos containers
docker compose ps

# Ver logs em tempo real
docker compose logs -f

# Logs específicos de cada serviço
docker compose logs -f postgres_cliente
docker compose logs -f postgres_evolution
docker compose logs -f redis_cliente
docker compose logs -f redis_evolution
docker compose logs -f evolution

# Reiniciar serviços
docker compose restart

# Parar tudo
docker compose down
```

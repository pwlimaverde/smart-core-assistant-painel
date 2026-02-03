# Docker - Smart Core Assistant

Esta pasta contém toda a configuração Docker do projeto, organizada em 4 stacks modulares.

## Estrutura

```
docker/
├── Dockerfile           # Imagem base (Django + Celery)
├── compose/
│   ├── data.yml         # PostgreSQL + Redis (dados persistentes)
│   ├── app.yml          # Django App + Migrate (deploy frequente)
│   ├── workers.yml      # Celery Worker + Beat (processamento)
│   └── infra.yml        # Cloudflared + Flower (infraestrutura)
└── README.md            # Este arquivo
```

## Uso

**Todos os comandos devem ser executados da raiz do projeto!**

### Inicialização Completa (Novo Servidor)

```powershell
# 1. Criar rede compartilhada (uma vez)
docker network create smartcore-network

# 2. Iniciar na ordem correta
docker compose -f docker/compose/data.yml up -d
docker compose -f docker/compose/app.yml up -d
docker compose -f docker/compose/workers.yml up -d
docker compose -f docker/compose/infra.yml up -d
```

### Via Taskipy (Recomendado)

```powershell
# Iniciar tudo
uv run task remote-start-all

# Status
uv run task remote-status

# Parar tudo
uv run task remote-stop-all
```

### Stacks Individuais

| Stack     | Descrição            | Rebuild Frequente? |
| --------- | -------------------- | ------------------ |
| `data`    | PostgreSQL + Redis   | Não                |
| `app`     | Django App           | **Sim**            |
| `workers` | Celery Worker/Beat   | Às vezes           |
| `infra`   | Cloudflared + Flower | Não                |

## Replicação em Novo Servidor

1. Copiar pasta `docker/` e arquivo `.env.prod`
2. Atualizar variáveis no `.env.prod`:
   - `CLOUDFLARE_TUNNEL_TOKEN` (novo túnel)
   - Credenciais de banco
3. Executar sequência de inicialização

## Seleção de Ambiente

Os compose files usam `SMARTCORE_ENV_FILE` para selecionar o arquivo de ambiente:

- Dev-local: `SMARTCORE_ENV_FILE=.env`
- Produção: `SMARTCORE_ENV_FILE=.env.prod`

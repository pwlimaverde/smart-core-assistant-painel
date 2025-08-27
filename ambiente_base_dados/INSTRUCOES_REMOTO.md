# Instruções para Ambiente Remoto

Este documento contém instruções específicas para configurar e usar o ambiente_base_dados com o Docker remoto no IP 192.168.3.127.

## ⚠️ IMPORTANTE

- O servidor Docker remoto (192.168.3.127) já possui um ambiente chamado "ambiente_chat" que **NÃO DEVE SER MODIFICADO**
- Este ambiente ("ambiente_base_dados") será criado como um projeto Docker independente
- Todos os containers deste ambiente serão gerenciados separadamente do "ambiente_chat"

## Configuração do Docker Remoto

### 1. Configurar variáveis de ambiente

Antes de executar qualquer comando, configure as variáveis de ambiente para apontar para o Docker remoto:

```bash
# No Linux/Mac
export DOCKER_HOST=tcp://192.168.3.127:2376
export DOCKER_TLS_VERIFY=1
export DOCKER_CERT_PATH=/caminho/para/certificados

# No Windows (PowerShell)
$env:DOCKER_HOST="tcp://192.168.3.127:2376"
$env:DOCKER_TLS_VERIFY="1"
$env:DOCKER_CERT_PATH="C:\caminho\para\certificados"

# No Windows (CMD)
set DOCKER_HOST=tcp://192.168.3.127:2376
set DOCKER_TLS_VERIFY=1
set DOCKER_CERT_PATH=C:\caminho\para\certificados
```

### 2. Verificar conexão com Docker remoto

```bash
docker info
```

### 3. Construir e iniciar o ambiente

```bash
# Navegar até o diretório do ambiente_base_dados
cd ambiente_base_dados

# Construir e iniciar os serviços com o nome do projeto específico
docker-compose -p ambiente_base_dados up --build -d
```

### 4. Verificar os containers

```bash
# Listar apenas os containers deste projeto
docker-compose -p ambiente_base_dados ps

# Ver logs
docker-compose -p ambiente_base_dados logs -f
```

## Comandos úteis

### Gerenciamento do ambiente

```bash
# Parar os serviços
docker-compose -p ambiente_base_dados down

# Parar e remover volumes (CUIDADO: apaga os dados)
docker-compose -p ambiente_base_dados down -v

# Reiniciar serviços
docker-compose -p ambiente_base_dados restart

# Ver status
docker-compose -p ambiente_base_dados ps
```

### Acesso aos serviços

```bash
# Acessar o PostgreSQL
docker-compose -p ambiente_base_dados exec postgres-remote psql -U postgres -d smart_core_db

# Acessar o Redis
docker-compose -p ambiente_base_dados exec redis-remote redis-cli
```

## Configuração do Django

Após iniciar os containers, configure o Django para usar os serviços:

1. Certifique-se de que o arquivo `.env` na raiz do projeto está configurado corretamente:

```
# Configurações do PostgreSQL
POSTGRES_DB=smart_core_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost
POSTGRES_PORT=5436

# Configurações do Redis
REDIS_HOST=localhost
REDIS_PORT=6382
```

2. Execute as migrações:

```bash
cd ..
python src/smart_core_assistant_painel/app/ui/manage.py migrate
```

3. Crie o superusuário:

```bash
python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser
```

## Isolamento de Ambientes

- O "ambiente_chat" no servidor remoto permanece inalterado
- O "ambiente_base_dados" é gerenciado como um projeto Docker independente
- Os containers do "ambiente_base_dados" têm nomes específicos:
  - `postgres-remote`
  - `redis-remote`
- Os volumes são nomeados especificamente:
  - `postgres_remote_data`
  - `redis_remote_data`
- A rede é isolada:
  - `remote-network`

## Troubleshooting

### Se não conseguir conectar ao Docker remoto:

1. Verifique se o Docker Engine está configurado para aceitar conexões remotas
2. Verifique se as portas estão abertas no firewall (2376 para TLS)
3. Verifique se os certificados estão configurados corretamente

### Se os containers não iniciarem:

1. Verifique os logs: `docker-compose -p ambiente_base_dados logs`
2. Verifique se as portas estão disponíveis localmente
3. Verifique as variáveis de ambiente

### Se o Django não conseguir conectar ao banco:

1. Verifique se as portas estão corretamente mapeadas (5436 para PostgreSQL)
2. Verifique se o arquivo `.env` está com as configurações corretas
3. Teste a conexão manualmente com um cliente PostgreSQL
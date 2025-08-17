# Ambiente de Desenvolvimento Misto

Este guia descreve como configurar e executar o ambiente de desenvolvimento "misto", onde os bancos de dados (PostgreSQL e Redis) rodam em containers Docker, e a aplicação Django roda localmente na sua máquina.

As portas usadas são:
- PostgreSQL: `5436` (porta do host mapeada para `5432` do container)
- Redis: `6382` (porta do host mapeada para `6379` do container)

## Estrutura

- `setup.sh`/`setup.bat`: Script unificado para configurar e iniciar todo o ambiente.
- `README.md`: Este arquivo.

Nota: Os scripts individuais foram substituídos por um único script unificado que realiza todas as operações necessárias.

## Pré-requisitos

1. Docker Desktop instalado e rodando
2. Python 3.13+ instalado
3. uv instalado (gerenciador de dependências)
4. Arquivo `firebase_key.json` (service account key) obtido no Firebase

## Configuração e Execução

Siga os passos abaixo para subir o ambiente:

### 1. Crie o Arquivo de Configuração

Antes de iniciar o ambiente, você precisa:

1) Criar o arquivo `.env` na raiz do projeto
2) Obter o arquivo `firebase_key.json` com as credenciais do Firebase

Exemplo de `.env` mínimo:

```env
# Firebase Configuration (OBRIGATÓRIO)
GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json

# Django Configuration (OBRIGATÓRIO)
SECRET_KEY_DJANGO=sua-chave-secreta-django-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Evolution API Configuration (OBRIGATÓRIO)
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua-chave-evolution-api-aqui
EVOLUTION_API_GLOBAL_WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/

# Redis e PostgreSQL - Altere as portas se as padrões estiverem em uso
REDIS_PORT=6382
POSTGRES_PORT=5436

# PostgreSQL Configuration
POSTGRES_DB=smart_core_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost
```

O script moverá automaticamente o `firebase_key.json` para:
`src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json`

### 2. Execute o Script de Início

A partir da raiz do projeto, execute:

- Windows:
  ```powershell
  ambiente_misto\setup.bat
  ```
- Linux/macOS:
  ```bash
  chmod +x ambiente_misto/setup.sh
  ./ambiente_misto/setup.sh
  ```

O script executa, em sequência:

1. Verificação do `.env` e `firebase_key.json`
2. Movimentação do `firebase_key.json` para o caminho esperado
3. Configuração do Git para ignorar alterações locais em arquivos de ambiente
4. Ajuste do `settings.py` para:
   - HOST do PostgreSQL: `localhost`
   - PORT do PostgreSQL: `5436` (padrão do ambiente misto)
   - Cache: `LocMemCache` (evita dependência do Redis no Django local)
5. Recriação do `docker-compose.yml` com apenas os serviços:
   - `postgres` (imagem `postgres:14`, porta `${POSTGRES_PORT:-5436}:5432`)
   - `redis` (imagem `redis:6.2-alpine`, porta `${REDIS_PORT:-6382}:6379`)
6. Comentário das diretivas `ENTRYPOINT` e `CMD` no Dockerfile
7. Subida dos containers (`docker-compose up -d`)
8. Instalação das dependências Python com `uv sync --dev`
9. Aplicação das migrações `uv run task migrate`
10. Criação de superusuário `admin/123456`

### 3. Inicie a Aplicação Django

Após a finalização do script `setup`, abra um novo terminal na raiz do projeto e execute:

```powershell
uv run task start
```

A aplicação estará disponível em: http://localhost:8000/

## Gerenciamento de Configurações Locais

O ambiente misto modifica arquivos rastreados pelo Git (como `docker-compose.yml` e `settings.py`). Para evitar commits acidentais dessas mudanças locais, o script configura o Git para ignorar alterações locais:

```bash
git update-index --assume-unchanged <arquivo>
```

Para reverter e commitar mudanças intencionais em algum desses arquivos:

```bash
git update-index --no-assume-unchanged <caminho/para/o/arquivo>
```

Após o commit, execute novamente `ambiente_misto/setup.bat` ou `setup.sh` para reaplicar a configuração.

## Parando o Ambiente

Para parar os containers do PostgreSQL e Redis (na raiz do projeto):

```powershell
docker-compose down -v
```

Para manter os dados (sem apagar volumes):

```powershell
docker-compose down
```

## Notas sobre o problema resolvido

- Sintoma original: erro de conexão `psycopg.OperationalError` ao iniciar o servidor.
- Causa: inconsistência de portas entre `.env` (5436), `settings.py` (porta padrão anterior 5435/5432) e `docker-compose` (outras portas).
- Correção implementada no ambiente_misto:
  - `settings.py` ajustado para `HOST=localhost` e `PORT=5436` por padrão
  - `docker-compose.yml` fixa mapeamento `${POSTGRES_PORT:-5436}:5432`
  - Cache do Django alterado para `LocMemCache` por padrão, evitando dependência do Redis na app local
- Resultado: após rodar `setup` e `uv run task start`, o servidor sobe com conexão estável ao PostgreSQL em `localhost:5436`.
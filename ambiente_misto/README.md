# Ambiente de Desenvolvimento Misto

Este guia descreve como configurar e executar o ambiente de desenvolvimento "misto", onde os bancos de dados (PostgreSQL e Redis) rodam em containers Docker, e a aplicacao Django roda localmente na sua maquina.

## Estrutura

- `run.bat`/`run.sh`: Scripts para iniciar o ambiente.
- `stop.bat`/`stop.sh`: Scripts para parar os containers Docker.
- `prepare_env.py`: Verifica se os arquivos de configuracao necessarios existem e os move para os locais corretos.
- `update_git_exclude.py`: Configura o Git para ignorar alteracoes locais em arquivos de configuracao especificos do ambiente.
- `update_settings.py`: Altera o `settings.py` do Django para se conectar aos bancos de dados no Docker.
- `update_docker_compose.py`: Altera o `docker-compose.yml` na raiz do projeto para subir apenas os servicos `postgres` e `redis`.
- `update_dockerfile.py`: Limpa o `Dockerfile` na raiz do projeto, pois a aplicacao nao sera executada em um container.
- `README.md`: Este arquivo.

## Pre-requisitos

1.  **Docker e Docker Compose**: [Instale o Docker Desktop](https://www.docker.com/products/docker-desktop).
2.  **Python**: Versao 3.8 ou superior.
3.  **Dependencias Python**: Instale as dependencias do projeto com `pip install -r requirements.txt`.

## Configuracao e Execucao

Siga os passos abaixo para subir o ambiente:

### 1. Crie os Arquivos de Configuracao

Antes de iniciar o ambiente, voce precisa criar dois arquivos na **raiz do projeto**:

**a) `firebase_key.json`**

- Obtenha o arquivo de credenciais do Firebase e salve-o com o nome `firebase_key.json` na raiz do projeto.

**b) `.env`**

- Crie um arquivo chamado `.env` na raiz do projeto. Voce pode usar o template abaixo como base. **Certifique-se de preencher os valores das chaves secretas.**

```env
# Firebase Configuration (OBRIGATÓRIO)
# O caminho deve ser relativo à raiz do projeto.
GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json

# Django Configuration (OBRIGATÓRIO)
SECRET_KEY_DJANGO=sua-chave-secreta-django-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Evolution API Configuration (OBRIGATÓRIO)
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua-chave-evolution-api-aqui
EVOLUTION_API_GLOBAL_WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/

# Redis e PostgreSQL - Altere as portas se as padroes estiverem em uso
REDIS_PORT=6381
POSTGRES_PORT=5434

# PostgreSQL Configuration
POSTGRES_DB=smart_core_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost

# Outras configurações (opcional)
# ... adicione outras variáveis de ambiente conforme necessário ...
```

### 2. Execute o Script de Inicio

- No Windows, execute a partir da **raiz do projeto**:
  ```bash
  ambiente_misto\run.bat
  ```
- No Linux ou macOS, execute a partir da **raiz do projeto**:
  ```bash
  chmod +x ambiente_misto/run.sh
  ./ambiente_misto/run.sh
  ```

O script realizara as seguintes acoes:

1.  **Verificará e Moverá Configurações**: O script `prepare_env.py` garantirá que `.env` e `firebase_key.json` existem e moverá a chave do Firebase para o diretório correto.
2.  **Configurará o Git**: O script `update_git_exclude.py` será executado para marcar arquivos de configuração (`Dockerfile`, `docker-compose.yml`, etc.) como "inalterados" para o Git.
3.  **Ajustará o `settings.py`**: O arquivo de configuracao do Django sera modificado para apontar para o PostgreSQL e Redis rodando no Docker.
4.  **Ajustará o `docker-compose.yml`**: O arquivo do Docker Compose sera reescrito para conter apenas os servicos de banco de dados.
5.  **Limpara o `Dockerfile`**: O Dockerfile principal sera esvaziado.
6.  **Subira os Containers**: Os containers do `postgres` e `redis` serao iniciados em background.

### 3. Inicie a Aplicacao Django

- Apos a finalizacao do script `run`, abra um **novo terminal**.
- Navegue ate a raiz do projeto.
- Execute o servidor de desenvolvimento do Django:

  ```bash
  python src/smart_core_assistant_painel/app/ui/manage.py runserver 0.0.0.0:8000
  ```

- A aplicacao estara disponivel em [http://localhost:8000](http://localhost:8000).

## Gerenciamento de Configurações Locais

O ambiente misto modifica arquivos que são rastreados pelo Git (como `docker-compose.yml` e `settings.py`). Para evitar que essas modificações locais sejam acidentalmente commitadas, o script `update_git_exclude.py` utiliza o seguinte comando do Git:

```bash
git update-index --assume-unchanged <arquivo>
```

Isso informa ao Git para "ignorar" as alterações locais no arquivo. Elas não aparecerão no `git status` e não serão incluídas em commits.

### Revertendo a Configuração

Se você precisar **deliberadamente** commitar uma alteração em um desses arquivos, você deve primeiro reverter essa configuração. Para fazer isso, execute o seguinte comando na raiz do projeto para o arquivo desejado:

```bash
git update-index --no-assume-unchanged <caminho/para/o/arquivo>
```

Após commitar suas alterações, recomenda-se executar o script `ambiente_misto/run.bat` ou `run.sh` novamente para reaplicar a configuração e garantir que futuras modificações locais sejam ignoradas.

## Parando o Ambiente

Para parar os containers do PostgreSQL e Redis, utilize os scripts a partir da **raiz do projeto**:

- No Windows: `ambiente_misto\stop.bat`
- No Linux/macOS: `./ambiente_misto/stop.sh`

Isso **nao** apaga os dados do banco de dados, que sao persistidos em um volume Docker.

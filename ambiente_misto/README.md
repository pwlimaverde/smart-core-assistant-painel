# Ambiente de Desenvolvimento Misto

Este guia descreve como configurar e executar o ambiente de desenvolvimento "misto", onde os bancos de dados (PostgreSQL e Redis) rodam em containers Docker, e a aplicacao Django roda localmente na sua maquina.

## Estrutura

- `setup.sh`/`setup.bat`: Script unificado para configurar e iniciar todo o ambiente.
- `README.md`: Este arquivo.

**Nota:** Os scripts individuais foram substituídos por um único script unificado que realiza todas as operações necessárias.

## Pre-requisitos

1.  **Docker e Docker Compose**: [Instale o Docker Desktop](https://www.docker.com/products/docker-desktop).
2.  **Python**: Versao 3.8 ou superior.

## Configuracao e Execucao

Siga os passos abaixo para subir o ambiente:

### 1. Crie o Arquivo de Configuração

Antes de iniciar o ambiente, voce precisa criar o arquivo `.env` na **raiz do projeto**:

- Crie um arquivo chamado `.env` na raiz do projeto. Voce pode usar o template abaixo como base. **Certifique-se de preencher os valores das chaves secretas.**

```env
# Firebase Configuration (usando JSON direto no .env)
# Substitua o conteúdo abaixo pelo JSON completo das suas credenciais de service account do Firebase
# Nota: O JSON deve estar em uma única linha com \n para quebras de linha
FIREBASE_CREDENTIALS_JSON={"type": "service_account","project_id": "seu-project-id","private_key_id": "sua-private-key-id","private_key": "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA_AQUI\n-----END PRIVATE KEY-----\n","client_email": "seu-client-email@seu-project-id.iam.gserviceaccount.com","client_id": "seu-client-id","auth_uri": "https://accounts.google.com/o/oauth2/auth","token_uri": "https://oauth2.googleapis.com/token","auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/seu-client-email%40seu-project-id.iam.gserviceaccount.com"}

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
POSTGRES_PORT=5435

# PostgreSQL Configuration
POSTGRES_DB=smart_core_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost

# Outras configurações (opcional)
# ... adicione outras variáveis de ambiente conforme necessário ...
```

### 2. Execute o Script de Inicio

A partir da **raiz do projeto**, execute:

- No Windows:
  ```bash
  ambiente_misto\\setup.bat
  ```
- No Linux ou macOS:
  ```bash
  chmod +x ambiente_misto/setup.sh
  ./ambiente_misto/setup.sh
  ```

O script realizara todas as seguintes acoes em sequencia:

1.  **Verificará o Arquivo de Configuração**: Garantirá que `.env` existe.
2.  **Configurará o Git**: Configurará o Git para ignorar alterações locais em arquivos de configuração específicos do ambiente.
3.  **Ajustará o `settings.py`**: O arquivo de configuracao do Django sera modificado para apontar para o PostgreSQL rodando no Docker e usar cache em memória.
4.  **Ajustará o `docker-compose.yml`**: O arquivo do Docker Compose sera reescrito para conter apenas os servicos de banco de dados, usando PostgreSQL versão 14.
5.  **Limpara o `Dockerfile`**: O Dockerfile principal sera esvaziado.
6.  **Subira os Containers**: Os containers do `postgres` e `redis` serao iniciados em background.
7.  **Instalará as dependências Python necessárias**.
8.  **Apagará as migrações do Django**.
9.  **Aplicará as migrações do Django**.
10. **Criará um superusuário com nome `admin` e senha `123456`**.

### 3. Inicie a Aplicacao Django

- Apos a finalizacao do script `setup`, abra um **novo terminal**.
- Navegue ate a raiz do projeto.
- Execute o servidor de desenvolvimento do Django:

  ```bash
  python src/smart_core_assistant_painel/app/ui/manage.py runserver 0.0.0.0:8000
  ```

- A aplicacao estara disponivel em [http://localhost:8000](http://localhost:8000).

## Gerenciamento de Configurações Locais

O ambiente misto modifica arquivos que são rastreados pelo Git (como `docker-compose.yml` e `settings.py`). Para evitar que essas modificações locais sejam acidentalmente commitadas, o script configura o Git para "ignorar" essas alterações locais usando o seguinte comando:

```bash
git update-index --assume-unchanged <arquivo>
```

Isso informa ao Git para ignorar as alterações locais no arquivo. Elas não aparecerão no `git status` e não serão incluídas em commits.

### Revertendo a Configuração

Se você precisar **deliberadamente** commitar uma alteração em um desses arquivos, você deve primeiro reverter essa configuração. Para fazer isso, execute o seguinte comando na raiz do projeto para o arquivo desejado:

```bash
git update-index --no-assume-unchanged <caminho/para/o/arquivo>
```

Após commitar suas alterações, recomenda-se executar o script `ambiente_misto/setup.bat` ou `setup.sh` novamente para reaplicar a configuração e garantir que futuras modificações locais sejam ignoradas.

## Parando o Ambiente

Para parar os containers do PostgreSQL e Redis, utilize docker-compose a partir da **raiz do projeto**:

```bash
docker-compose down -v
```

Isso irá parar e remover os containers, além de apagar os volumes de dados. Para manter os dados, use:

```bash
docker-compose down
```
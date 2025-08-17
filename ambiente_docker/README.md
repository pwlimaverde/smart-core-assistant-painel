# Ambiente Docker Completo

Este ambiente utiliza Docker Compose para executar toda a aplicação e seus serviços dependentes em containers isolados. É ideal para produção, demonstrações e desenvolvimento em equipe.

## 🏗️ Arquitetura do Ambiente

### Containers incluídos:
- **django-app**: Aplicação Django principal
- **django-qcluster**: Serviço de processamento assíncrono (Q-cluster)
- **postgres-django**: Banco PostgreSQL para a aplicação Django
- **postgres**: Banco PostgreSQL para Evolution API
- **redis**: Cache Redis para sessões e Q-cluster
- **evolution-api**: API para WhatsApp Business

### Portas expostas:
- `8001`: Django App (interface web principal)
- `8081`: Evolution API
- `5435`: PostgreSQL Django (acesso externo)
- `6380`: Redis (acesso externo)

## 📋 Pré-requisitos

Antes de executar o ambiente Docker, certifique-se de ter:

### Sistema Operacional
- **Windows**: Docker Desktop for Windows
- **Linux/macOS**: Docker e Docker Compose

### Software necessário
1. **Docker Desktop** (versão 4.0 ou superior)
2. **Docker Compose** (geralmente incluído no Docker Desktop)
3. **Git** (para clonar o repositório)

### Verificar instalação
```bash
# Verificar Docker
docker --version
docker-compose --version

# Verificar se Docker está rodando
docker info
```

## ⚙️ Configuração Inicial

### 1. Arquivo .env
Na raiz do projeto, crie o arquivo `.env` baseado no `.env.example`:

```bash
# Copiar arquivo de exemplo
cp ambiente_docker/.env.example .env
```

Configure as seguintes variáveis **obrigatórias**:

```env
# Django
SECRET_KEY_DJANGO=sua_chave_secreta_django_aqui
DEBUG=True

# Evolution API
EVOLUTION_API_KEY=sua_chave_evolution_api

# Firebase
GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json

# Opção 1: Salvar firebase_key.json na raiz do projeto
# OU
# Opção 2: Adicionar conteúdo JSON diretamente no .env
FIREBASE_KEY_JSON_CONTENT={"type":"service_account","project_id":"seu-projeto-id"...}

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# PostgreSQL Django
POSTGRES_DJANGO_HOST=postgres-django
POSTGRES_DJANGO_PORT=5432
POSTGRES_DJANGO_DB=smart_core_assistant
POSTGRES_DJANGO_USER=django_user
POSTGRES_DJANGO_PASSWORD=django_password

# PostgreSQL Evolution
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=evolution
POSTGRES_USER=evolution
POSTGRES_PASSWORD=evolution_password
```

### 2. Credenciais Firebase

**Você tem duas opções para fornecer as credenciais do Firebase:**

#### Opção 1: Arquivo físico (Recomendado para desenvolvimento local)
1. Salve o arquivo `firebase_key.json` na raiz do projeto
2. O script automaticamente moverá para o local correto

#### Opção 2: Variável de ambiente (Recomendado para CI/CD e produção)
1. Copie todo o conteúdo JSON do seu arquivo Firebase
2. Adicione no arquivo `.env`:
```env
FIREBASE_KEY_JSON_CONTENT={"type":"service_account","project_id":"seu-projeto","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
```

## 🚀 Executar o Ambiente

### Script de Setup Automático

Para configurar e iniciar todo o ambiente Docker automaticamente:

**No Windows:**
```cmd
cd ambiente_docker
setup.bat
```

**No Linux/macOS:**
```bash
cd ambiente_docker
chmod +x setup.sh
./setup.sh
```

### O que o script faz:

1. **Verifica pré-requisitos**: Docker, Docker Compose, arquivos de configuração
2. **Processa credenciais Firebase**: Cria `firebase_key.json` dinamicamente
3. **Configura docker-compose.yml**: Copia para raiz do projeto
4. **Atualiza Dockerfile**: Adiciona scripts de entrypoint necessários
5. **Constrói imagens**: Build das imagens Docker com dependências
6. **Inicia bancos de dados**: PostgreSQL e Redis primeiro
7. **Executa migrações**: Configura banco de dados Django
8. **Coleta arquivos estáticos**: Prepara arquivos CSS/JS
9. **Cria superusuário**: admin/123456 para acesso inicial
10. **Inicia todos os serviços**: Aplicação completa funcionando

## 🌐 Acessar a Aplicação

Após a execução bem-sucedida do script:

### Serviços Disponíveis
- **Django App**: http://localhost:8001
- **Evolution API**: http://localhost:8081
- **Admin Django**: http://localhost:8001/admin (admin/123456)

### Credenciais Padrão
- **Username**: admin
- **Password**: 123456
- **Email**: admin@example.com

## 🔧 Comandos Úteis

### Docker Compose

```bash
# Visualizar status dos containers
docker-compose ps

# Monitorar logs em tempo real
docker-compose logs -f

# Logs de um serviço específico
docker-compose logs -f django-app

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (CUIDADO: apaga dados)
docker-compose down -v

# Reiniciar um serviço específico
docker-compose restart django-app

# Executar comando dentro do container
docker-compose exec django-app bash
```

### Django

```bash
# Executar comandos Django
docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py <comando>

# Exemplos:
docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate
docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser
docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell
docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py collectstatic
```

### Banco de Dados

```bash
# Conectar ao PostgreSQL Django
docker-compose exec postgres-django psql -U django_user -d smart_core_assistant

# Conectar ao PostgreSQL Evolution
docker-compose exec postgres psql -U evolution -d evolution

# Conectar ao Redis
docker-compose exec redis redis-cli
```

## 🐛 Resolução de Problemas

### Docker não está rodando
```
ERRO: Docker não está rodando. Inicie o Docker Desktop e tente novamente.
```
**Solução**: Inicie o Docker Desktop e aguarde ele ficar completamente carregado.

### Falha na construção das imagens
```
ERRO: Falha ao construir as imagens Docker.
```
**Soluções**:
1. Verificar se o arquivo `.env` está configurado corretamente
2. Executar `docker system prune -a` para limpar cache
3. Reiniciar o Docker Desktop

### Container sai imediatamente
```bash
# Verificar logs para identificar o erro
docker-compose logs django-app
```

**Possíveis causas**:
- Credenciais Firebase inválidas
- Variáveis de ambiente mal configuradas
- Problemas de conexão com banco de dados

### Problemas de conexão PostgreSQL
```bash
# Verificar se o PostgreSQL está rodando
docker-compose ps postgres-django

# Verificar logs do PostgreSQL
docker-compose logs postgres-django

# Testar conexão manualmente
docker-compose exec postgres-django pg_isready -U postgres
```

### Redis não conecta
```bash
# Verificar se Redis está rodando
docker-compose ps redis

# Testar conexão
docker-compose exec redis redis-cli ping
```

### Problemas de permissão (Linux/macOS)
```bash
# Dar permissão aos scripts
chmod +x ambiente_docker/setup.sh
```

### Limpar ambiente completamente
```bash
# Parar e remover tudo (CUIDADO: remove dados!)
docker-compose down -v --rmi all

# Limpar sistema Docker
docker system prune -a
```

## 📊 Monitoramento

### Verificar saúde dos serviços
```bash
# Status resumido
docker-compose ps

# Uso de recursos
docker stats

# Logs em tempo real
docker-compose logs -f --tail=50
```

### Verificar conectividade
```bash
# Testar Django
curl http://localhost:8001

# Testar Evolution API
curl http://localhost:8081

# Testar Redis
docker-compose exec redis redis-cli ping

# Testar PostgreSQL
docker-compose exec postgres-django pg_isready -U django_user
```

## 🔄 Atualizar Ambiente

### Atualizar código
```bash
# Parar serviços
docker-compose down

# Atualizar código (git pull, etc.)

# Reconstruir e iniciar
docker-compose build --no-cache
docker-compose up -d
```

### Aplicar novas migrações
```bash
docker-compose run --rm django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate
```

## ✅ Checklist de Verificação Rápida

- [ ] Docker Desktop instalado e rodando
- [ ] Arquivo `.env` criado e configurado na raiz do projeto
- [ ] Credenciais Firebase configuradas (arquivo ou variável de ambiente)
- [ ] Script `setup.sh` ou `setup.bat` executado com sucesso
- [ ] Todos os containers rodando: `docker-compose ps`
- [ ] Django acessível em http://localhost:8001
- [ ] Admin acessível com admin/123456
- [ ] Evolution API respondendo em http://localhost:8081

## 🆘 Suporte

Se encontrar problemas:

1. **Verificar logs**: `docker-compose logs -f`
2. **Verificar status**: `docker-compose ps`
3. **Verificar configuração**: Revisar arquivo `.env`
4. **Limpar cache**: `docker system prune -a`
5. **Reconstruir**: `docker-compose build --no-cache`

Para problemas específicos, verifique a seção **Resolução de Problemas** acima.
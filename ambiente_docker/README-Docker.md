# Guia de Configuração Docker - Smart Core Assistant Painel

Este documento fornece instruções para configurar e executar o Smart Core Assistant Painel usando Docker.

## 📋 Pré-requisitos

- **Docker Engine 20.10+**
- **Docker Compose 2.0+**
- **PowerShell 5.0+** (Windows)
- **Git**

### Verificação dos Pré-requisitos
```powershell
# Verificar Docker
docker --version
docker-compose --version

# Verificar se Docker está rodando
docker info
```

## 🚀 Configuração e Execução

### 1. Configuração Rápida (Recomendado)

Use o script `docker-manager.ps1` para configuração automática:

```powershell
# Navegar para o diretório do projeto
cd c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\ambiente_docker

# Executar configuração inicial completa
.\docker-manager.ps1 setup

# Iniciar serviços
.\docker-manager.ps1 start
```

### 2. Configuração Manual

#### 2.1. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo na raiz do projeto:
```bash
cp .env.example .env
```

Edite o arquivo `.env` na raiz do projeto com suas configurações:

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

# PostgreSQL Configuration
POSTGRES_DB=smart_core_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Webhook Configuration
WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/
WEBHOOK_SECRET=seu-webhook-secret

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
WORKERS=4

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Logging
LOG_LEVEL=INFO

# Ollama Configuration (opcional)
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
```

#### 2.2. Configurar Firebase

1. **Obter credenciais do Firebase:**
   - Acesse o [Console do Firebase](https://console.firebase.google.com/)
   - Vá em **Configurações do Projeto > Contas de Serviço**
   - Clique em **"Gerar nova chave privada"**
   - Salve o arquivo como `firebase_key.json`

2. **Colocar arquivo no local correto:**
   ```
   src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
   ```

3. **Configurar Remote Config:**
   Configure as seguintes variáveis no Firebase Remote Config:
   - `OPENAI_API_KEY`
   - `GROQ_API_KEY`
   - `WHATSAPP_API_BASE_URL`
   - `WHATSAPP_API_SEND_TEXT_URL`
   - `WHATSAPP_API_START_TYPING_URL`
   - `WHATSAPP_API_STOP_TYPING_URL`
   - `LLM_CLASS`
   - `MODEL`
   - `TEMPERATURE`
   - Prompts do sistema
   - Configurações do FAISS

#### 2.3. Gerar Chave Secreta Django

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 2.4. Construir e Iniciar Serviços

```powershell
# Construir as imagens Docker
docker-compose build

# Iniciar os serviços
docker-compose up -d
```

#### 2.5. Configurar Banco de Dados

Após iniciar os serviços, é necessário criar e aplicar as migrações do Django:

```powershell
# Aplicar migrações
docker-compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate

# Criar superusuário (opcional)
docker-compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser
```

**Nota Importante**: O passo de migrações é essencial para criar as tabelas do banco de dados.

## 🛠️ Comandos do Docker Manager

```powershell
# Configuração inicial completa
.\docker-manager.ps1 setup

# Iniciar serviços
.\docker-manager.ps1 start

# Parar serviços
.\docker-manager.ps1 stop

# Reiniciar serviços
.\docker-manager.ps1 restart

# Ver status dos serviços
.\docker-manager.ps1 status

# Ver logs em tempo real
.\docker-manager.ps1 logs

# Construir imagens
.\docker-manager.ps1 build

# Limpeza completa
.\docker-manager.ps1 clean

# Acessar shell do Django
.\docker-manager.ps1 shell

# Executar migrações
.\docker-manager.ps1 migrate

# Criar superusuário
.\docker-manager.ps1 createsuperuser

# Mostrar ajuda
.\docker-manager.ps1 help
```

## 🏗️ Arquitetura dos Serviços

### Serviços Incluídos

1. **Django Application** (porta 8000)
   - Aplicação principal Django
   - URL: http://localhost:8000
   - Health Check: `/admin/`

2. **Django Q Cluster**
   - Processamento assíncrono de tarefas
   - Dependente do Redis

3. **Evolution API** (porta 8080)
   - API para integração WhatsApp
   - URL: http://localhost:8080
   - Versão: v2.1.1
   - Webhook configurado para Django app

4. **PostgreSQL Django** (interno)
   - Banco de dados principal do Django
   - Database: `smart_core_db`

5. **PostgreSQL Evolution** (interno)
   - Banco de dados dedicado para Evolution API
   - Database: `evolution`

6. **Redis** (porta 6379)
   - Cache para Evolution API e filas Django Q
   - Persistência habilitada

### Dependências entre Serviços

```
PostgreSQL Django → Django App → Django QCluster
Redis → Django App, Django QCluster, Evolution API
PostgreSQL Evolution → Evolution API
Firebase → Django App
```

## 📚 Comandos Úteis

### Gerenciamento de Containers

```bash
# Ver todos os containers
docker-compose ps

# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f django-app

# Reiniciar um serviço específico
docker-compose restart django-app

# Parar todos os serviços
docker-compose down

# Reconstruir imagens
docker-compose build --no-cache
```

### Django Management

```bash
# Executar migrações
docker-compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate

# Criar superusuário
docker-compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser

# Acessar shell Django
docker-compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell

# Acessar bash do container
docker-compose exec django-app bash
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Container não inicia
```bash
# Verificar logs
docker-compose logs django-app

# Verificar configuração
docker-compose config
```

#### 2. Erro de conexão com banco
```bash
# Verificar se PostgreSQL está rodando
docker-compose ps postgres-django

# Verificar logs do PostgreSQL
docker-compose logs postgres-django
```

#### 3. Erro de tabela não encontrada (Django)
```bash
# Verificar migrações pendentes
docker-compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py showmigrations

# Aplicar migrações
docker-compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate
```

#### 4. Evolution API não conecta
```bash
# Verificar logs da Evolution API
docker-compose logs evolution-api

# Verificar se Redis está rodando
docker-compose ps redis

# Testar conexão Redis
docker-compose exec redis redis-cli ping
```

#### 5. Firebase não inicializa
```bash
# Verificar se arquivo existe
ls -la src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/

# Verificar conteúdo do arquivo
cat src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json | jq .
```

#### 6. Erro de decodificação UTF-8 no Webhook WhatsApp

**Sintomas**: Erro `UnicodeDecodeError: 'utf-8' codec can't decode byte` nos logs do Django

**Solução**: O sistema possui tratamento automático para múltiplos encodings:
- UTF-8 (padrão)
- Latin-1 (fallback)
- CP1252 (fallback final)

```bash
# Verificar se a correção está aplicada
docker-compose exec django-app grep -n "latin-1\|cp1252" src/smart_core_assistant_painel/app/ui/oraculo/views.py

# Verificar logs do webhook
docker-compose logs -f django-app | grep webhook
```

### Limpeza Completa

Para resolver problemas persistentes:

```bash
# Parar e remover tudo
docker-compose down -v --remove-orphans

# Limpeza geral do Docker
docker system prune -a

# Recriar do zero
.\docker-manager.ps1 setup -Force
```

## 🔒 URLs de Acesso

- **Django Admin**: http://localhost:8000/admin/
- **Django App**: http://localhost:8000/
- **Evolution API**: http://localhost:8080/ (requer apikey no header)

## 📞 Suporte

Para problemas ou dúvidas:

1. **Verifique os logs** dos containers
2. **Consulte este README** para soluções comuns
3. **Use o comando** `docker-manager.ps1 help`

### Comandos de Diagnóstico

```bash
# Diagnóstico completo
.\docker-manager.ps1 status
docker-compose config
docker system info

# Verificar conectividade
docker-compose exec django-app ping postgres-django
docker-compose exec django-app ping redis
```

---

**Nota**: Esta configuração está otimizada para desenvolvimento e produção. O script `docker-manager.ps1` automatiza a maioria das operações e deve ser usado como ponto de entrada principal.
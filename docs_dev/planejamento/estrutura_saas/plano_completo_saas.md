# Plano Completo - Transformação SaaS Multi-Tenant

> **Domínio**: smartcoreassistant.com.br  
> **Modelo**: Core as a Service (núcleo centralizado, dados distribuídos)  
> **Alvo Inicial**: 1-10 clientes

---

## Sumário de Etapas

| Etapa | Nome | Descrição |
|-------|------|-----------|
| **1** | Infraestrutura do Cliente | Docker image padrão + guia de instalação |
| **2** | Painel de Controle (Core) | Aplicação Django para gestão de tenants |
| **3** | Refatoração de Serviços | Remoção do Remote Config, nova fonte de dados |
| **4** | Chaveamento Multi-Tenant | Roteamento dinâmico por tenant |
| **4.5** | TenantAdminSite | Admin separado para clientes (Django Admin dedicado) |
| **5** | Integração de Pagamento | Controle de assinatura e bloqueio automático |
| **6** | Infraestrutura Celery | Migração Django Q → Celery + Docker Compose |

---

## Mapeamento Completo de Configurações

### Configurações por TENANT (Cliente fornece)

#### PostgreSQL (Banco de Dados)
| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `POSTGRES_HOST` | Host do servidor PostgreSQL | `db.supabase.co` |
| `POSTGRES_PORT` | Porta do PostgreSQL | `5432` |
| `POSTGRES_DB` | Nome do banco de dados | `smartcore_db` |
| `POSTGRES_USER` | Usuário do banco | `postgres` |
| `POSTGRES_PASSWORD` | Senha do banco | `****` |
| `POSTGRES_SSLMODE` | Modo SSL | `require` |

#### Evolution API (WhatsApp)
| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `EVOLUTION_API_URL` | URL do servidor Evolution | `https://evo.cliente.com` |
| `EVOLUTION_API_KEY` | Chave de API | `ACB5ED4B...` |
| `EVOLUTION_INSTANCE_NAME` | Nome da instância | `atendimento` |
| `EVOLUTION_WEBHOOK_SECRET` | Secret para validar webhooks | `abc123...` |

#### Trello (Integração Kanban)
| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `TRELLO_API_KEY` | Chave de API do Trello | `9cc88ac4...` |
| `TRELLO_API_SECRET` | Segredo da API | `f503feea...` |
| `TRELLO_TOKEN` | Token de acesso | `ATTAda0f...` |
| `TRELLO_WORKSPACE_ID` | ID do Workspace | `6913d8e5...` |
| `TRELLO_BOARD_ID` | ID do Board principal | `abc123...` |

#### Configurações Personalizáveis (via Portal)
| Categoria | Configuração | Descrição |
|-----------|--------------|-----------|
| **LLM** | `llm_class` | Classe do LLM (ChatGroq, ChatOpenAI) |
| | `model` | Modelo (gpt-4o-mini, llama3.1) |
| | `llm_temperature` | Temperatura (0-1) |
| **API Keys** | `groq_api_key` | Chave Groq (se usar) |
| | `openai_api_key` | Chave OpenAI (se usar) |
| **Prompts** | `prompt_system_dados_empresa` | Contexto da empresa |
| | `prompt_regras_resposta` | Regras de resposta |
| **Mensagens** | `msg_fallback_sem_info` | Fallback sem informação |
| | `msg_fallback_geral` | Fallback genérico |
| | `msg_transferencia_generica` | Mensagem de transferência |

### Configurações do CORE (Fixas no servidor)
| Variável | Descrição |
|----------|-----------|
| `SECRET_KEY_DJANGO` | Chave secreta Django |
| `GOOGLE_APPLICATION_CREDENTIALS` | Credenciais Firebase (autenticação) |
| `LANGSMITH_API_KEY` | Monitoramento LLM |
| `REDIS_HOST`, `REDIS_PORT` | Cache e filas |
| `EMBEDDINGS_CLASS`, `EMBEDDINGS_MODEL` | Configuração de embeddings |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Configuração RAG |

---

# ETAPA 1: Infraestrutura do Cliente

## 1.1 Objetivo
Fornecer uma imagem Docker completa e documentação para o cliente configurar sua própria infraestrutura de dados.

## 1.2 Componentes da Imagem Docker

### docker-compose.yml (Template para Cliente)
```yaml
version: '3.8'

services:
  # ============================================
  # PostgreSQL com pgvector para RAG
  # ============================================
  postgres:
    image: ankane/pgvector:v0.7.4-pg16
    container_name: smartcore_postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-smartcore_db}
      POSTGRES_USER: ${POSTGRES_USER:-smartcore}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Defina POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-smartcore}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # ============================================
  # Redis para cache e filas
  # ============================================
  redis:
    image: redis:7-alpine
    container_name: smartcore_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "${REDIS_PORT:-6379}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # ============================================
  # Evolution API para WhatsApp
  # ============================================
  evolution:
    image: atendai/evolution-api:v2.1.1
    container_name: smartcore_evolution
    environment:
      # Configurações básicas
      SERVER_URL: ${EVOLUTION_SERVER_URL:-http://localhost:8080}
      AUTHENTICATION_API_KEY: ${EVOLUTION_API_KEY:?Defina EVOLUTION_API_KEY}
      
      # Banco de dados
      DATABASE_ENABLED: true
      DATABASE_PROVIDER: postgresql
      DATABASE_CONNECTION_URI: postgresql://${POSTGRES_USER:-smartcore}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-smartcore_db}
      DATABASE_SAVE_DATA_INSTANCE: true
      DATABASE_SAVE_DATA_NEW_MESSAGE: true
      DATABASE_SAVE_MESSAGE_UPDATE: true
      DATABASE_SAVE_DATA_CONTACTS: true
      DATABASE_SAVE_DATA_CHATS: true
      DATABASE_SAVE_DATA_LABELS: true
      DATABASE_SAVE_DATA_HISTORIC: true
      
      # Redis cache
      CACHE_REDIS_ENABLED: true
      CACHE_REDIS_URI: redis://redis:6379/0
      CACHE_REDIS_PREFIX_KEY: evolution
      CACHE_LOCAL_ENABLED: false
      
      # Webhook para o Core
      WEBHOOK_GLOBAL_URL: ${WEBHOOK_CORE_URL:?Defina WEBHOOK_CORE_URL}
      WEBHOOK_GLOBAL_ENABLED: true
      WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS: false
      
      # QR Code
      QRCODE_LIMIT: 30
      QRCODE_COLOR: "#198754"
      
      # Logging
      LOG_LEVEL: WARN
      LOG_COLOR: true
      LOG_BAILEYS: error
    ports:
      - "${EVOLUTION_PORT:-8080}:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### .env.example (Template para Cliente)
```bash
# ============================================
# SMART CORE ASSISTANT - CONFIGURAÇÃO DO CLIENTE
# ============================================
# Copie este arquivo para .env e preencha os valores

# === IDENTIFICAÇÃO DO TENANT ===
# Slug fornecido pelo painel (ex: empresa-abc)
TENANT_SLUG=

# === POSTGRESQL ===
POSTGRES_DB=smartcore_db
POSTGRES_USER=smartcore
POSTGRES_PASSWORD=  # OBRIGATÓRIO: senha forte
POSTGRES_PORT=5432

# === EVOLUTION API ===
EVOLUTION_API_KEY=  # OBRIGATÓRIO: gere uma chave única
EVOLUTION_PORT=8080
EVOLUTION_SERVER_URL=http://seu-dominio.com:8080

# === WEBHOOK (fornecido pelo painel) ===
# URL onde o Core receberá os webhooks da Evolution
WEBHOOK_CORE_URL=https://smartcoreassistant.com.br/webhook/SEU_TENANT_SLUG/evolution/
```

## 1.3 Guia de Instalação do Cliente

### Pré-requisitos
1. VPS com mínimo 2GB RAM, 20GB SSD (Hostinger KVM 2 ou similar)
2. Docker e Docker Compose instalados
3. Domínio ou IP fixo com portas 5432, 6379, 8080 acessíveis
4. Conta no Smart Core Assistant (smartcoreassistant.com.br)

### Passo a Passo

#### 1. Cadastro no Painel
1. Acesse `https://smartcoreassistant.com.br/cadastro`
2. Crie sua conta empresarial
3. Anote o `TENANT_SLUG` fornecido

#### 2. Preparação do Servidor
```bash
# Criar diretório
mkdir -p ~/smartcore && cd ~/smartcore

# Baixar arquivos de configuração
curl -O https://smartcoreassistant.com.br/setup/docker-compose.yml
curl -O https://smartcoreassistant.com.br/setup/.env.example

# Copiar e editar configuração
cp .env.example .env
nano .env  # Preencher todas as variáveis
```

#### 3. Iniciar Serviços
```bash
# Subir containers
docker compose up -d

# Verificar status
docker compose ps
docker compose logs -f evolution
```

#### 4. Configurar Trello
1. Acesse https://trello.com/app-key
2. Copie a **API Key**
3. Clique em "Token" para gerar token de acesso
4. Crie um Workspace e Board para atendimentos
5. Anote os IDs (visíveis na URL do Trello)

#### 5. Cadastrar no Painel
No painel `https://smartcoreassistant.com.br/config`:

**Aba PostgreSQL:**
- Host: `seu-ip-ou-dominio`
- Porta: `5432`
- Banco: `smartcore_db`
- Usuário: `smartcore`
- Senha: `sua-senha`

**Aba Evolution API:**
- URL: `http://seu-ip:8080`
- API Key: `sua-api-key`
- Nome da Instância: `atendimento`

**Aba Trello:**
- API Key: `9cc88ac4...`
- API Secret: `f503feea...`
- Token: `ATTAda0f...`
- Workspace ID: `6913d8e5...`
- Board ID: `abc123...`

#### 6. Validar Conexões
1. Clique em "Testar Conexão" em cada aba
2. Se tudo verde, clique em "Ativar Tenant"
3. O sistema rodará as migrations automaticamente

### Dados Fornecidos ao Painel
| Dado | Onde Obter |
|------|------------|
| Connection String PostgreSQL | Seu servidor |
| URL + API Key Evolution | Seu servidor |
| API Key + Token Trello | https://trello.com/app-key |
| Workspace ID Trello | URL do Trello |
| Board ID Trello | URL do Trello |

---

# ETAPA 2: Painel de Controle (Core)

## 2.1 Arquitetura do Painel

### Estrutura de URLs (Separação Lógica)

#### 1. Painel do Cliente (SaaS Product)
Acessível pelos clientes para gerenciar seu negócio e configurações.
- `smartcoreassistant.com.br/dashboard/` - Visão geral
- `smartcoreassistant.com.br/atendimentos/` - Gestão de tickets (CRM)
- `smartcoreassistant.com.br/config/` - Configurações de Infra (DB, Evolution, Trello)
- `smartcoreassistant.com.br/tenant-admin/` - **TenantAdminSite** (Django Admin dedicado)
    - Gestão de Departamentos, Atendentes, Fluxos
    - Gestão de Instâncias Evolution
    - Visualização de Atendimentos (read-only)
    - *Nota: Abordagem simplificada que reutiliza Django Admin (ver Etapa 4.5)*
- `smartcoreassistant.com.br/billing/` - Assinatura e Faturas

#### 2. Backoffice (Super Admin)
Acessível apenas por você (Staff/Superuser) para gestão do SaaS.
- `smartcoreassistant.com.br/bo/` - Dashboard Financeiro/Sistêmico
- `smartcoreassistant.com.br/bo/tenants/` - Gestão de Inquilinos (Criar, Bloquear)
- `smartcoreassistant.com.br/bo/subscriptions/` - Gestão de Assinaturas (Override)
- `smartcoreassistant.com.br/admin/` - Django Admin Nativo (Fallback/Low-level)

### Novo App Django: `tenants` (Base)
Responsável apenas pela infraestrutura multi-tenant e modelos do Core. Os módulos de negócio (`atendimentos`, `operacional`) serão consumidos pelo Painel do Cliente via roteamento dinâmico.

#### Estrutura de Arquivos
```
src/smart_core_assistant_painel/app/
└── tenants/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py              # Tenant, TenantDatabase, TenantEvolution, etc.
    ├── middleware.py          # TenantMiddleware
    ├── db_router.py           # TenantDatabaseRouter
    ├── forms.py               # Forms de configuração
    ├── views.py               # Views do portal
    ├── api/
    │   ├── __init__.py
    │   ├── serializers.py
    │   └── views.py           # API REST
    ├── services/
    │   ├── __init__.py
    │   ├── connection_tester.py
    │   ├── migration_runner.py
    │   └── tenant_service_hub.py
    ├── management/
    │   └── commands/
    │       ├── migrate_tenant.py
    │       └── validate_tenant.py
    ├── templates/
    │   └── tenants/
    │       ├── dashboard.html
    │       ├── config_database.html
    │       ├── config_evolution.html
    │       ├── config_trello.html
    │       └── config_ai.html
    ├── migrations/
    └── tests/
```

## 2.2 Modelagem de Dados (Core DB)

### Modelo: Tenant
```python
class Tenant(models.Model):
    """Representa um cliente cadastrado."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # Identificação
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    api_key = models.CharField(max_length=64, unique=True)
    
    # Contato
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Usuário proprietário
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tenants"
    )
    
    # Status
    active = models.BooleanField(default=False)
    setup_completed = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "core_tenant"
```

### Modelo: TenantDatabase
```python
class TenantDatabase(models.Model):
    """Configuração do PostgreSQL do cliente."""
    
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="database"
    )
    
    # Conexão (password criptografado via Fernet)
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=5432)
    database = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    _password = models.CharField(max_length=500, db_column="password")
    ssl_mode = models.CharField(max_length=20, default="require")
    
    # Status
    connection_valid = models.BooleanField(default=False)
    last_check = models.DateTimeField(null=True)
    schema_version = models.CharField(max_length=20, null=True)
    
    class Meta:
        db_table = "core_tenant_database"
```

### Modelo: TenantEvolution
```python
class TenantEvolution(models.Model):
    """Configuração da Evolution API do cliente."""
    
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="evolution_instances"
    )
    
    name = models.CharField(max_length=100)
    server_url = models.URLField()
    _api_key = models.CharField(max_length=500, db_column="api_key")
    instance_name = models.CharField(max_length=100)
    webhook_secret = models.CharField(max_length=64)
    
    active = models.BooleanField(default=True)
    connection_valid = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True)
    
    class Meta:
        db_table = "core_tenant_evolution"
```

### Modelo: TenantTrello
```python
class TenantTrello(models.Model):
    """Configuração do Trello do cliente."""
    
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="trello"
    )
    
    # Credenciais (criptografadas)
    _api_key = models.CharField(max_length=500, db_column="api_key")
    _api_secret = models.CharField(max_length=500, db_column="api_secret")
    _token = models.CharField(max_length=500, db_column="token")
    
    # IDs
    workspace_id = models.CharField(max_length=50)
    board_id = models.CharField(max_length=50)
    
    # Webhook
    webhook_id = models.CharField(max_length=50, blank=True)
    webhook_callback_url = models.URLField(blank=True)
    
    # Status
    connection_valid = models.BooleanField(default=False)
    last_check = models.DateTimeField(null=True)
    
    class Meta:
        db_table = "core_tenant_trello"
```

### Modelo: TenantConfig
```python
class TenantConfig(models.Model):
    """Configurações personalizadas do tenant."""
    
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="config"
    )
    
    # LLM
    llm_settings = models.JSONField(default=dict)
    # {"llm_class": "ChatOpenAI", "model": "gpt-4o-mini", "temperature": 0}
    
    # API Keys do cliente (criptografadas)
    api_keys = models.JSONField(default=dict)
    # {"openai_api_key": "encrypted...", "groq_api_key": "encrypted..."}
    
    # Prompts personalizados
    prompts = models.JSONField(default=dict)
    # {"dados_empresa": "...", "regras_resposta": "..."}
    
    # Mensagens
    messages = models.JSONField(default=dict)
    # {"fallback_sem_info": "...", "fallback_geral": "...", "transferencia": "..."}
    
    # Entidades customizadas
    custom_entities = models.JSONField(default=dict)
    
    class Meta:
        db_table = "core_tenant_config"
```

### Modelo: Plan
```python
class Plan(models.Model):
    """Planos comerciais do SaaS."""
    
    name = models.CharField(max_length=100)  # Ex: Básico, Pro, Ilimitado
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Limites
    max_instances = models.IntegerField(default=1, help_text="Máximo de instâncias Evolution. -1 para ilimitado")
    max_departments = models.IntegerField(default=1, help_text="Máximo de departamentos. -1 para ilimitado")
    
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

### Modelo: Subscription
```python
class Subscription(models.Model):
    """Controle de assinatura."""
    
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativo"
        PAST_DUE = "PAST_DUE", "Pagamento Pendente"
        SUSPENDED = "SUSPENDED", "Suspenso"
        CANCELLED = "CANCELLED", "Cancelado"
    
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="subscription"
    )
    
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Período
    current_period_start = models.DateTimeField(null=True)
    current_period_end = models.DateTimeField(null=True)
    
    # Gateway
    payment_gateway = models.CharField(max_length=50, blank=True)  # asaas, stripe
    external_customer_id = models.CharField(max_length=100, blank=True)
    external_subscription_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = "core_subscription"
    
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE
```

## 2.3 Autenticação e Autorização

### Fluxo de Cadastro
1. Usuário acessa `/cadastro/`
2. Preenche: email, senha, nome da empresa
3. Sistema cria `User` + `Tenant` + `Subscription(trial)`
4. Email de confirmação enviado
5. Trial de 14 dias iniciado

### Fluxo de Login
1. Login padrão Django com email/senha
2. Após login, redireciona para `/dashboard/`
3. Dashboard mostra tenants do usuário

## 2.4 Seções do Portal

### Dashboard
- Status do tenant (ativo/inativo)
- Status das integrações (PostgreSQL, Evolution, Trello)
- Estatísticas de atendimentos (últimos 30 dias)
- Alertas de configuração pendente

### Configuração PostgreSQL
- Formulário para host, porta, banco, usuário, senha
- Botão "Testar Conexão"
- Botão "Executar Migrations" (após conexão válida)

### Configuração Evolution
- URL do servidor
- API Key
- Nome da instância
- Botão "Testar Conexão"
- Exibe webhook URL para configurar na Evolution

### Configuração Trello
- Formulário para API Key, Secret, Token
- Workspace ID, Board ID
- Botão "Testar Conexão"
- Botão "Registrar Webhook"

### Configuração IA
- Seleção de LLM (OpenAI, Groq)
- Campos para API Keys
- Prompts personalizáveis
- Mensagens de fallback

---

# ETAPA 3: Refatoração de Serviços

## 3.1 Remoção do Firebase Remote Config

### Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `modules/services/features/set_environ_remote/` | **REMOVER** diretório completo |
| `modules/services/features/features_compose.py` | Remover `set_environ_remote()` |
| `modules/services/start_services.py` | Atualizar fluxo de inicialização |
| `modules/initial_loading/` | Manter apenas init Firebase Auth |

### Nova Fonte de Dados: TenantConfigService

```python
# app/tenants/services/tenant_config_service.py

class TenantConfigService:
    """Fornece configurações do tenant a partir do Core DB."""
    
    _cache: dict[str, dict] = {}
    _cache_ttl = 300  # 5 minutos
    
    @classmethod
    def get_config(cls, tenant: Tenant) -> dict:
        """Retorna configurações completas do tenant."""
        cache_key = str(tenant.id)
        
        if cache_key in cls._cache:
            cached = cls._cache[cache_key]
            if time.time() - cached["timestamp"] < cls._cache_ttl:
                return cached["data"]
        
        config = cls._load_from_db(tenant)
        cls._cache[cache_key] = {
            "timestamp": time.time(),
            "data": config
        }
        return config
    
    @classmethod
    def _load_from_db(cls, tenant: Tenant) -> dict:
        """Carrega configurações do banco."""
        tc = tenant.config
        defaults = CoreDefaults.get_all()
        
        return {
            # LLM
            "llm_class": tc.llm_settings.get("llm_class", defaults["llm_class"]),
            "model": tc.llm_settings.get("model", defaults["model"]),
            "temperature": tc.llm_settings.get("temperature", defaults["temperature"]),
            
            # API Keys
            "openai_api_key": cls._decrypt(tc.api_keys.get("openai_api_key", "")),
            "groq_api_key": cls._decrypt(tc.api_keys.get("groq_api_key", "")),
            
            # Prompts (merge com defaults)
            "prompts": {**defaults["prompts"], **tc.prompts},
            
            # Messages
            "messages": {**defaults["messages"], **tc.messages},
            
            # Trello
            "trello": {
                "api_key": cls._decrypt(tenant.trello.api_key),
                "api_secret": cls._decrypt(tenant.trello.api_secret),
                "token": cls._decrypt(tenant.trello.token),
                "workspace_id": tenant.trello.workspace_id,
                "board_id": tenant.trello.board_id,
            },
            
            # Evolution
            "evolution": [
                {
                    "server_url": evo.server_url,
                    "api_key": cls._decrypt(evo.api_key),
                    "instance_name": evo.instance_name,
                }
                for evo in tenant.evolution_instances.filter(active=True)
            ],
        }
```

### CoreDefaults (Valores Padrão)

```python
# app/tenants/services/core_defaults.py

class CoreDefaults:
    """Valores padrão carregados das env vars do Core."""
    
    _defaults: Optional[dict] = None
    
    @classmethod
    def get_all(cls) -> dict:
        if cls._defaults is None:
            cls._defaults = cls._load()
        return cls._defaults
    
    @classmethod
    def _load(cls) -> dict:
        return {
            "llm_class": os.environ.get("DEFAULT_LLM_CLASS", "ChatOpenAI"),
            "model": os.environ.get("DEFAULT_MODEL", "gpt-4o-mini"),
            "temperature": int(os.environ.get("DEFAULT_TEMPERATURE", "0")),
            
            "prompts": {
                "system_analise_conteudo": os.environ.get("PROMPT_SYSTEM_ANALISE_CONTEUDO", ""),
                "human_analise_conteudo": os.environ.get("PROMPT_HUMAN_ANALISE_CONTEUDO", ""),
                # ... outros prompts
            },
            
            "messages": {
                "fallback_sem_info": "Desculpe, não encontrei informações...",
                "fallback_geral": "Recebemos sua mensagem...",
                "transferencia": "Vou transferir seu atendimento...",
            },
            
            "embeddings_class": os.environ.get("EMBEDDINGS_CLASS", "OpenAIEmbeddings"),
            "embeddings_model": os.environ.get("EMBEDDINGS_MODEL", ""),
            "chunk_size": int(os.environ.get("CHUNK_SIZE", "1000")),
            "chunk_overlap": int(os.environ.get("CHUNK_OVERLAP", "200")),
        }
```

---

# ETAPA 4: Chaveamento Multi-Tenant

## 4.1 TenantMiddleware

```python
# app/tenants/middleware.py

import threading
from typing import Optional
from django.http import HttpRequest, HttpResponse, JsonResponse

_tenant_context = threading.local()

def get_current_tenant() -> Optional["Tenant"]:
    return getattr(_tenant_context, "tenant", None)

def set_current_tenant(tenant: Optional["Tenant"]) -> None:
    _tenant_context.tenant = tenant

class TenantMiddleware:
    """Identifica e valida tenant por requisição."""
    
    EXEMPT_PATHS = [
        "/admin/",
        "/cadastro/",
        "/login/",
        "/logout/",
        "/static/",
        "/health/",
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Paths isentos
        if any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
            set_current_tenant(None)
            return self.get_response(request)
        
        # Identifica tenant
        tenant = self._resolve_tenant(request)
        
        if tenant is None:
            return JsonResponse({"error": "Tenant não identificado"}, status=400)
        
        if not tenant.active:
            return JsonResponse({"error": "Tenant inativo"}, status=403)
        
        if not tenant.subscription.is_active():
            return JsonResponse(
                {"error": "Assinatura expirada", "status": tenant.subscription.status},
                status=402
            )
        
        set_current_tenant(tenant)
        request.tenant = tenant
        
        try:
            response = self.get_response(request)
        finally:
            set_current_tenant(None)
        
        return response
    
    def _resolve_tenant(self, request: HttpRequest) -> Optional["Tenant"]:
        # 1. Webhook: /webhook/{slug}/...
        if request.path.startswith("/webhook/"):
            parts = request.path.strip("/").split("/")
            if len(parts) >= 2:
                slug = parts[1]
                return self._get_tenant_by_slug(slug)
        
        # 2. Header: X-Tenant-Slug
        slug = request.headers.get("X-Tenant-Slug")
        if slug:
            return self._get_tenant_by_slug(slug)
        
        # 3. Sessão do usuário logado
        if request.user.is_authenticated:
            return request.user.tenants.filter(active=True).first()
        
        return None
    
    def _get_tenant_by_slug(self, slug: str) -> Optional["Tenant"]:
        from .models import Tenant
        try:
            return Tenant.objects.select_related(
                "database", "subscription", "config", "trello"
            ).prefetch_related(
                "evolution_instances"
            ).get(slug=slug)
        except Tenant.DoesNotExist:
            return None
```

## 4.2 TenantDatabaseRouter

```python
# app/tenants/db_router.py

from django.db import connections

class TenantDatabaseRouter:
    """Roteia queries para o banco do tenant atual."""
    
    CORE_APPS = ["tenants", "auth", "admin", "contenttypes", "sessions"]
    TENANT_APPS = ["clientes", "atendimentos", "operacional", "evolution_sync", "trello_sync", "treinamento"]
    
    def db_for_read(self, model, **hints):
        return self._route(model)
    
    def db_for_write(self, model, **hints):
        return self._route(model)
    
    def allow_relation(self, obj1, obj2, **hints):
        return True  # Permite se no mesmo contexto
    
    def allow_migrate(self, db, app_label, **hints):
        if app_label in self.CORE_APPS:
            return db == "default"
        return None
    
    def _route(self, model) -> str:
        app = model._meta.app_label
        
        if app in self.CORE_APPS:
            return "default"
        
        from .middleware import get_current_tenant
        tenant = get_current_tenant()
        
        if tenant is None:
            return "default"
        
        alias = f"tenant_{tenant.slug}"
        
        if alias not in connections.databases:
            self._configure_connection(tenant, alias)
        
        return alias
    
    def _configure_connection(self, tenant, alias):
        params = tenant.database.get_connection_params()
        connections.databases[alias] = params
```

## 4.3 Comunicação Evolution/Trello

### Fluxo de Webhook Evolution
```
1. Evolution (cliente) → POST /webhook/{tenant_slug}/evolution/
2. TenantMiddleware → identifica tenant, valida subscription
3. TenantDatabaseRouter → configura conexão com DB do tenant
4. evolution_sync/views.py → processa mensagem
5. AI Engine → usa TenantServiceHub para configs
6. Resposta → usa Evolution do tenant (URL + API Key do TenantEvolution)
```

### TenantServiceHub

```python
# app/tenants/services/tenant_service_hub.py

class TenantServiceHub:
    """ServiceHub específico para o tenant atual."""
    
    _instances: dict[str, "TenantServiceHub"] = {}
    
    @classmethod
    def current(cls) -> "TenantServiceHub":
        from .middleware import get_current_tenant
        tenant = get_current_tenant()
        if tenant is None:
            raise RuntimeError("Sem tenant no contexto")
        
        key = str(tenant.id)
        if key not in cls._instances:
            cls._instances[key] = cls(tenant)
        return cls._instances[key]
    
    def __init__(self, tenant: "Tenant"):
        self._tenant = tenant
        self._config = TenantConfigService.get_config(tenant)
    
    @property
    def MODEL(self) -> str:
        return self._config["model"]
    
    @property
    def TRELLO_API_KEY(self) -> str:
        return self._config["trello"]["api_key"]
    
    @property
    def TRELLO_TOKEN(self) -> str:
        return self._config["trello"]["token"]
    
    @property
    def EVOLUTION_INSTANCES(self) -> list[dict]:
        return self._config["evolution"]
    
    # ... demais propriedades
```

---

# ETAPA 4.5: TenantAdminSite (Painel Administrativo do Cliente)

> **Task Master**: Task 35  
> **Dependência**: Task 33 (TenantMiddleware + TenantDatabaseRouter)  
> **Status**: Planejado (a implementar após Task 33)

## 4.5.1 Decisão Arquitetural

### Problema Original
No MVP, todas as configurações (Departamentos, Atendentes, Fluxos, etc.) eram feitas via Django Admin. Com multi-tenancy, cada cliente precisa de um painel para gerenciar seus recursos **sem acessar configurações do Core**.

### Abordagens Avaliadas

| Critério | Frontend Customizado | TenantAdminSite ✅ |
|----------|---------------------|-------------------|
| Tempo de implementação | Alto | Baixo |
| Reutilização de código | Nenhuma | Total |
| Superfície de bugs | Grande | Pequena |
| Manutenção | Dois sistemas | Unificada |

### Decisão Final
**Criar um Django Admin Site dedicado** (`TenantAdminSite`) que reutiliza a infraestrutura existente do Django Admin.

## 4.5.2 Arquitetura

### Separação de URLs
```
/admin/          → Super Admin (backoffice) - modelos do Core
/tenant-admin/   → Admin do Cliente - apenas modelos de negócio
```

### Modelos por Painel

#### Tenant Admin (Cliente)
| App | Modelos | Permissões |
|-----|---------|------------|
| `operacional` | `Departamento`, `Atendente`, `AppInstance`, `FluxoAtendimento`, `EtapaFluxo` | CRUD |
| `evolution_sync` | `EvolutionInstance` | Read, Update |
| `treinamento` | `Documento`, `Trecho` | CRUD, Read-only |
| `atendimentos` | `Atendimento`, `Mensagem` | Read-only |

#### Super Admin (Backoffice)
- `Tenant`, `TenantDatabase`, `TenantConfig`
- `Plan`, `Subscription`
- `CoreSettings`
- `User`

## 4.5.3 Implementação

### Arquivos Principais
```
app/tenants/
├── admin_client.py          # TenantAdminSite
├── mixins.py                 # TenantModelAdminMixin

app/operacional/
├── tenant_admin.py           # Registros para tenant admin

app/evolution_sync/
├── tenant_admin.py           # Registros para tenant admin
```

### TenantAdminSite
```python
# app/tenants/admin_client.py

from django.contrib.admin import AdminSite
from .middleware import get_current_tenant

class TenantAdminSite(AdminSite):
    """Admin Site dedicado para clientes (tenants)."""
    
    site_header = "Painel de Configuração"
    site_title = "Smart Core Assistant"
    index_title = "Gerenciamento"
    
    def has_permission(self, request):
        """Permite acesso apenas a usuários com tenant ativo."""
        if not request.user.is_authenticated:
            return False
        tenant = getattr(request, 'tenant', None)
        if tenant is None or not tenant.active:
            return False
        # Verifica se usuário é owner ou membro
        return request.user == tenant.owner

# Instância global
tenant_admin_site = TenantAdminSite(name='tenant_admin')
```

### TenantModelAdminMixin
```python
# app/tenants/mixins.py

from .middleware import get_current_tenant

class TenantModelAdminMixin:
    """
    Mixin para ModelAdmin que valida permissões por tenant.
    O TenantDatabaseRouter já garante o banco correto.
    """
    
    def has_add_permission(self, request):
        tenant = get_current_tenant()
        if tenant is None or not tenant.active:
            return False
        return super().has_add_permission(request)
    
    def has_change_permission(self, request, obj=None):
        tenant = get_current_tenant()
        if tenant is None or not tenant.active:
            return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        tenant = get_current_tenant()
        if tenant is None or not tenant.active:
            return False
        return super().has_delete_permission(request, obj)
```

### Exemplo de Registro
```python
# app/operacional/tenant_admin.py

from django.contrib import admin
from smart_core_assistant_painel.app.tenants.admin_client import tenant_admin_site
from smart_core_assistant_painel.app.tenants.mixins import TenantModelAdminMixin
from .models import Departamento, Atendente

class TenantDepartamentoAdmin(TenantModelAdminMixin, admin.ModelAdmin):
    list_display = ['id', 'nome', 'slug', 'ativo']
    search_fields = ['nome']

class TenantAtendenteAdmin(TenantModelAdminMixin, admin.ModelAdmin):
    list_display = ['id', 'nome', 'departamento', 'ativo']
    search_fields = ['nome']

# Registrar no TenantAdminSite (não no admin padrão)
tenant_admin_site.register(Departamento, TenantDepartamentoAdmin)
tenant_admin_site.register(Atendente, TenantAtendenteAdmin)
```

### Configuração de URLs
```python
# config/urls.py

from smart_core_assistant_painel.app.tenants.admin_client import tenant_admin_site

urlpatterns = [
    path('admin/', admin.site.urls),              # Super Admin
    path('tenant-admin/', tenant_admin_site.urls), # Admin do Cliente
    # ...
]
```

## 4.5.4 Validações de Segurança

1. **TenantMiddleware** injeta `request.tenant` baseado em:
   - Sessão do usuário logado
   - Header `X-Tenant-Slug`
   - URL do webhook

2. **TenantDatabaseRouter** roteia queries para banco do tenant

3. **TenantAdminSite.has_permission()** valida:
   - Usuário autenticado
   - Tenant ativo
   - Usuário é owner do tenant

4. **TenantModelAdminMixin** valida permissões de CRUD

## 4.5.5 Checklist de Implementação

- [ ] Criar `TenantAdminSite` em `admin_client.py`
- [ ] Criar `TenantModelAdminMixin` em `mixins.py`
- [ ] Criar `TenantXxxAdmin` para cada modelo
- [ ] Configurar URL `/tenant-admin/`
- [ ] Testes de isolamento entre tenants
- [ ] Verificar que modelos do Core não aparecem

---

# ETAPA 5: Integração de Pagamento

## 5.1 Gateway Recomendado: Asaas

Por ser brasileiro, com boleto, PIX e cartão, ideal para B2B.

### Fluxo de Pagamento
1. Tenant criado → subscription `trial` por 14 dias
2. Próximo do fim do trial → email lembrando
3. Cliente acessa `/billing/` → escolhe plano → paga via Asaas
4. Webhook Asaas → atualiza subscription para `active`
5. Falha no pagamento → subscription `past_due` → 3 dias → `suspended`
6. `suspended` → TenantMiddleware bloqueia acesso

### Modelo de Planos

| Plano | Preço | Atendimentos/mês | Features |
|-------|-------|------------------|----------|
| Starter | R$ 197/mês | Até 500 | 1 instância Evolution |
| Pro | R$ 497/mês | Até 2000 | 3 instâncias, relatórios |
| Enterprise | Sob consulta | Ilimitado | Customizações |

## 5.2 Views de Billing

```python
# app/tenants/views/billing.py

class BillingView(LoginRequiredMixin, View):
    def get(self, request):
        tenant = request.user.tenants.first()
        subscription = tenant.subscription
        
        return render(request, "tenants/billing.html", {
            "tenant": tenant,
            "subscription": subscription,
            "plans": Plan.choices,
        })
    
    def post(self, request):
        # Cria cobrança no Asaas
        plan = request.POST.get("plan")
        # ... integração Asaas
```

---

# ETAPA 6: Infraestrutura de Processamento (Celery)

> **Task Master**: Task 37  
> **Status**: Concluído  
> **Servidor Alvo**: Hostinger KVM 2 (2 vCPU, 8GB RAM)

## 6.1 Decisão Arquitetural

### Worker Centralizado vs Distribuído

| Aspecto | Distribuído (cliente) | Centralizado (core) ✅ |
|---------|----------------------|------------------------|
| Manutenção | N servidores | 1 servidor |
| Deploy | Complexo | Simples |
| Segurança | API keys no cliente | API keys centralizadas |
| Debug | Difícil | Fácil |

**Decisão**: Workers Celery rodam no servidor Core.

## 6.2 Dimensionamento

### Distribuição de Recursos (8GB RAM)

| Componente | RAM | CPU |
|------------|-----|-----|
| Django (Gunicorn 4w) | 800 MB | 0.3 |
| PostgreSQL Core | 1.5 GB | 0.3 |
| Redis | 256 MB | 0.1 |
| Celery Worker (3 procs) | 1.5 GB | 0.8 |
| Celery Beat | 100 MB | 0.05 |
| Buffer/Sistema | 3.8 GB | 0.4 |

### Configuração Celery

```python
CELERY_WORKER_CONCURRENCY = 3      # Otimizado para 2 vCPU
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = 120  # 2 min warning
CELERY_TASK_TIME_LIMIT = 300       # 5 min hard kill
CELERY_TASK_ACKS_LATE = True       # Não perde task em crash
```

## 6.3 Filas por Tipo de Workload

| Fila | Uso | Prioridade |
|------|-----|------------|
| `webhooks` | Evolution, Trello | Alta |
| `ai_processing` | Embeddings, RAG | Média (recursos intensivos) |
| `default` | Todo o resto | Normal |

## 6.4 Docker Compose

```yaml
services:
  celery_worker:
    build: .
    command: celery -A smart_core_assistant_painel.app.core worker
             --concurrency=3 --queues=webhooks,ai_processing,default
    depends_on: [postgres, redis]
    deploy:
      resources:
        limits:
          memory: 1536M

  celery_beat:
    build: .
    command: celery -A smart_core_assistant_painel.app.core beat
             --scheduler=django_celery_beat.schedulers:DatabaseScheduler
    deploy:
      resources:
        limits:
          memory: 128M

  flower:
    image: mher/flower:2.0
    profiles: [debug]  # Só sobe com --profile debug
    environment:
      - FLOWER_BASIC_AUTH=admin:${FLOWER_PASSWORD}
```

## 6.5 Migração de Tasks

| Arquivo | De | Para |
|---------|-----|------|
| `trello_sync/signals.py` | `async_task()` | `task.delay()` |
| `treinamento/signals.py` | `async_task()` | `task.delay()` |
| `evolution_sync/message_buffer.py` | `Schedule` | `ClockedSchedule` |

---

# Checklist de Verificação

## Etapa 1 - Infraestrutura Cliente
- [ ] Docker Compose funcional
- [ ] PostgreSQL com pgvector
- [ ] Evolution API configurável
- [ ] Documentação de instalação

## Etapa 2 - Painel de Controle
- [ ] Cadastro/Login funcionando
- [ ] Formulários de configuração
- [ ] Testes de conexão
- [ ] Migrations remotas

## Etapa 3 - Refatoração
- [ ] Remote Config removido
- [ ] TenantConfigService funcionando
- [ ] CoreDefaults carregando

## Etapa 4 - Chaveamento
- [ ] Middleware identificando tenant
- [ ] Router direcionando queries
- [ ] Webhooks multi-tenant

## Etapa 4.5 - TenantAdminSite
- [ ] TenantAdminSite criado
- [ ] TenantModelAdminMixin implementado
- [ ] Modelos de negócio registrados
- [ ] URL `/tenant-admin/` configurada
- [ ] Isolamento de dados entre tenants
- [ ] Modelos do Core ocultos no tenant admin

## Etapa 5 - Pagamentos
- [ ] Integração Asaas
- [ ] Webhooks de pagamento
- [ ] Bloqueio automático

## Etapa 6 - Infraestrutura Celery
- [ ] Dependências atualizadas (celery, django-celery-beat, django-celery-results)
- [ ] celery.py criado
- [ ] settings.py configurado (CELERY_*)
- [ ] docker-compose.yml atualizado (worker, beat, flower)
- [ ] Tasks migradas (7 arquivos)
- [ ] Scripts taskipy atualizados
- [ ] Worker inicia e processa filas
- [ ] Beat agenda tasks periódicas

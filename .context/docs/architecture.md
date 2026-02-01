# Arquitetura do Sistema

## Visão Geral

O Smart Core Assistant Painel segue uma arquitetura **monolítica modular** com capacidade de evolução para microserviços. O sistema utiliza padrões de Domain-Driven Design (DDD) nos módulos de negócio.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Django Templates)               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │   Jazzmin    │ │   Dashboard  │ │     Public Pages         │ │
│  │    Admin     │ │    Views     │ │    (Landing, Auth)       │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (Django 5.2)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      Django Apps (UI)                       │ │
│  │  ┌─────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────┐ │ │
│  │  │  core   │ │ atendimentos│ │ operacional│ │   clientes  │ │ │
│  │  └─────────┘ └─────────────┘ └───────────┘ └─────────────┘ │ │
│  │  ┌─────────┐ ┌─────────────┐ ┌───────────┐                 │ │
│  │  │usuarios │ │ treinamento │ │  oraculo  │                 │ │
│  │  └─────────┘ └─────────────┘ └───────────┘                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Sync Apps (Integrations)                 │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────────┐  │ │
│  │  │   tenants  │ │evolution_  │ │    trello_sync         │  │ │
│  │  │            │ │   sync     │ │ clickup_sync (planned) │  │ │
│  │  └────────────┘ └────────────┘ └────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                    MODULES (Business Logic)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                        ai_engine                            │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────────────┐ │ │
│  │  │  analise_   │ │  generate_  │ │   load_document_      │ │ │
│  │  │  mensagem   │ │  embeddings │ │      file             │ │ │
│  │  └─────────────┘ └─────────────┘ └───────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                        services                             │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │              unifield_data_services                  │   │ │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐   │   │ │
│  │  │  │  trello    │ │  clickup   │ │     notion     │   │   │ │
│  │  │  │  adapter   │ │  adapter   │ │    adapter     │   │   │ │
│  │  │  └────────────┘ └────────────┘ └────────────────┘   │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │  PostgreSQL  │ │    Redis     │ │     Celery Workers       │ │
│  │  + pgvector  │ │   (Broker)   │ │     (Async Tasks)        │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ Evolution API│ │   Firebase   │ │   LLM Providers          │ │
│  │  (WhatsApp)  │ │(Remote Config)│ │(OpenAI, Groq, Ollama)   │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │    Trello    │ │   ClickUp    │ │        Notion            │ │
│  │     API      │ │     API      │ │         API              │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Padrões Arquiteturais

### 1. Multi-Tenant Database Isolation

Cada tenant possui seu próprio banco de dados PostgreSQL, garantindo isolamento completo de dados.

```python
# TenantDatabaseRouter roteia queries para o banco correto
class TenantDatabaseRouter:
    def db_for_read(self, model, **hints):
        return get_current_tenant_db()

    def db_for_write(self, model, **hints):
        return get_current_tenant_db()
```

**Arquivos principais:**
- `src/smart_core_assistant_painel/app/tenants/db_router.py`
- `src/smart_core_assistant_painel/app/tenants/middleware.py`

### 2. Service Layer Pattern

O `ServiceHub` atua como factory para criação de instâncias de features via `FeaturesCompose`.

```python
# Uso do ServiceHub
from modules.services import ServiceHub

hub = ServiceHub()
result = hub.unified_data.create_task(title="Nova tarefa")
```

**Arquivos principais:**
- `src/smart_core_assistant_painel/modules/services/features/service_hub.py`
- `src/smart_core_assistant_painel/modules/services/features/features_compose.py`

### 3. Adapter Pattern (Unified Data Services)

Interface unificada `UnifiedDataService` com adapters para diferentes plataformas.

```python
# Interface unificada
class UnifiedDataServiceInterface(Protocol):
    def create_task(self, title: str, ...) -> Result
    def get_task(self, task_id: str) -> Result
    def update_task(self, task_id: str, ...) -> Result

# Adapters específicos
class TrelloAdapter(UnifiedDataServiceInterface): ...
class ClickUpAdapter(UnifiedDataServiceInterface): ...
class NotionAdapter(UnifiedDataServiceInterface): ...
```

**Arquivos principais:**
- `src/smart_core_assistant_painel/modules/services/features/unifield_data_services/`

### 4. Domain-Driven Design (Modules)

Cada feature de módulo segue estrutura DDD:

```
feature/
├── datasource/          # Acesso a dados externos
├── domain/
│   ├── model/           # Entidades e value objects
│   ├── interface/       # Contratos/protocolos
│   └── usecase/         # Casos de uso (lógica de negócio)
└── __init__.py          # Exports públicos
```

### 5. Signals para Integrações

Django signals disparam sincronização automática com sistemas externos.

```python
# Exemplo: atendimento criado -> sincroniza com Trello
@receiver(post_save, sender=Atendimento)
def sync_atendimento_to_trello(sender, instance, created, **kwargs):
    if created:
        trello_sync_task.delay(instance.id)
```

**Arquivos principais:**
- `src/smart_core_assistant_painel/app/trello_sync/signals.py`
- `src/smart_core_assistant_painel/app/evolution_sync/signals.py`

### 6. Result Pattern

Tratamento de erros com `py-return-success-or-error`:

```python
from py_return_success_or_error import Success, Failure, Result

def process_message(msg: str) -> Result[AnalysisResult, Error]:
    if not msg:
        return Failure(ValidationError("Mensagem vazia"))
    return Success(AnalysisResult(...))
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Multi-Tenant via Database Isolation

**Contexto:** Necessidade de isolar completamente dados entre clientes.

**Decisão:** Utilizar bancos de dados separados por tenant com router dinâmico.

**Consequências:**
- (+) Isolamento total de dados
- (+) Facilidade para backup/restore por cliente
- (-) Maior complexidade de migrations
- (-) Mais recursos de infraestrutura

### ADR-002: LangChain como Orquestrador de IA

**Contexto:** Necessidade de suportar múltiplos provedores de LLM.

**Decisão:** Utilizar LangChain como camada de abstração.

**Consequências:**
- (+) Fácil troca de provedores (OpenAI, Groq, Ollama)
- (+) Suporte nativo a RAG e embeddings
- (-) Dependência de biblioteca externa
- (-) Overhead de abstração

### ADR-003: Celery para Processamento Assíncrono

**Contexto:** Necessidade de processar webhooks e análises de IA sem bloquear requests.

**Decisão:** Utilizar Celery com Redis como broker.

**Consequências:**
- (+) Processamento não-bloqueante
- (+) Retry automático em falhas
- (+) Escalabilidade horizontal de workers
- (-) Complexidade operacional adicional

### ADR-004: Django Jazzmin para Admin UI

**Contexto:** Necessidade de interface administrativa moderna.

**Decisão:** Utilizar Jazzmin como tema do Django Admin.

**Consequências:**
- (+) Interface moderna sem desenvolvimento frontend
- (+) Totalmente customizável via settings
- (-) Limitações de UX comparado a frontend dedicado

---

## Dependências Entre Módulos

```
                    ┌─────────────┐
                    │   Django    │
                    │   Settings  │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │  tenants │     │   core   │     │ usuarios │
   └────┬─────┘     └────┬─────┘     └────┬─────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ clientes │   │operacion.│   │treinament│
   └────┬─────┘   └────┬─────┘   └────┬─────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ atendimentos │
                 └──────┬───────┘
                        │
      ┌─────────────────┼─────────────────┐
      │                 │                 │
      ▼                 ▼                 ▼
┌────────────┐   ┌────────────┐   ┌────────────┐
│evolution_  │   │trello_sync │   │ ai_engine  │
│   sync     │   │            │   │  (module)  │
└────────────┘   └────────────┘   └────────────┘
```

---

## Limites de Contexto (Bounded Contexts)

### Contexto: Atendimento
- **Domínio:** Gestão de tickets e mensagens
- **Apps:** atendimentos, clientes
- **Integrações:** Evolution API, Trello

### Contexto: Operacional
- **Domínio:** Configuração de fluxos e departamentos
- **Apps:** operacional, usuarios
- **Integrações:** -

### Contexto: IA
- **Domínio:** Processamento de linguagem natural
- **Apps:** treinamento, oraculo
- **Modules:** ai_engine
- **Integrações:** LLM providers, Firebase

### Contexto: Multi-Tenancy
- **Domínio:** Isolamento e gestão de tenants
- **Apps:** tenants
- **Integrações:** -

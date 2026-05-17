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
│  │  ┌─────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────┐ │ │
│  │  │usuarios │ │ treinamento │ │  oraculo  │ │ atendimento_│ │ │
│  │  └─────────┘ └─────────────┘ └───────────┘ │  unificado  │ │ │
│  │                                            └─────────────┘ │ │
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

### ADR-005: Independência cross-app no `atendimento_unificado`

**Contexto:** O Workspace combina dados de `atendimentos`, `operacional`,
`trello_sync`, `evolution_sync` e `ai_engine`. Editar essas apps para
atender necessidades do Workspace criaria acoplamento bidirecional e
risco em apps de produção já em uso.

**Decisão:** Toda integração do `atendimento_unificado` com os demais apps
acontece via signals e Celery tasks **dentro** de `atendimento_unificado/`.
Nenhum app de produção é editado para servir o Workspace. FKs cross-app
ficam como `BigIntegerField` lógico (não `ForeignKey`).

**Consequências:**
- (+) Rollback do Workspace = remover app de `INSTALLED_APPS`. Nenhuma
  migration em tabela legada.
- (+) Tabelas próprias `atu_*` (`atu_leitura_atendimento`,
  `atu_campo_personalizado`, `atu_valor_campo`) podem ser dropadas sem
  efeito colateral.
- (+) Princípio é o mesmo já adotado por `trello_sync` (escuta signals de
  `Atendimento`/`Mensagem` sem que `atendimentos` saiba do Trello).
- (-) Exige criar helpers locais (ex.: `selectors.get_campos_for_prompt`)
  para evitar imports cruzados.
- (-) Única exceção justificada: `analise_mensage_datasource.py` recebeu
  o helper `_formatar_campos_personalizados` porque a construção do
  prompt é síncrona em request-time — signals não se aplicam.

### ADR-006: SSE via Django async view + Redis pub/sub

**Contexto:** O Workspace precisa atualização em tempo real (mensagens,
movimentos no Kanban, edição de campos personalizados) sem polling.

**Decisão:** Usar `StreamingHttpResponse` com iterator `async` (Django
4.1+) ouvindo `redis.asyncio` em canal por tenant
(`sse:{tenant_slug}:events`). Worker Uvicorn substitui Gunicorn sync
para evitar travamento de processo. Sem dependência de Django Channels.

**Consequências:**
- (+) Stack já existente (Redis broker do Celery + Django) — sem novos
  serviços.
- (+) Isolamento multi-tenant pelo nome do canal + filtro defense-in-depth
  no consumidor.
- (+) Mantém o mesmo asgi.py do projeto (sem rota dedicada).
- (-) Exige worker Uvicorn (config documentada em
  `.context/docs/workspace-sse-nginx.md`).
- (-) Nginx precisa `proxy_buffering off` + `proxy_read_timeout 1h` na
  rota `/workspace/events/`.

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

### Contexto: Workspace (Atendimento Unificado)
- **Domínio:** Tela única operacional combinando chat estilo WhatsApp Web
  e Kanban sobre `EtapaFluxo`/`Atendimento`, com campos personalizados
  híbridos extraídos pela IA.
- **Apps:** atendimento_unificado
- **Modules:** ai_engine.features.extracao_campos
- **Integrações:** Redis (SSE pub/sub), Evolution API (envio outbound de
  mídia), LLM provider (extração de campos)
- **Princípio:** Independência cross-app (ADR-005). Observa via signals
  os apps `atendimentos`, `operacional`, `evolution_sync`, `trello_sync`
  sem editá-los.
- **Feature flag:** `ATENDIMENTO_UNIFICADO_ENABLED` em `settings.py` +
  allowlist por tenant via `ATENDIMENTO_UNIFICADO_TENANT_SLUGS`.

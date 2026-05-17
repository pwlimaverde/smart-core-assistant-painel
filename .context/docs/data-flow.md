# Fluxo de Dados

Este documento descreve os principais fluxos de dados do sistema Smart Core Assistant Painel.

---

## 1. Fluxo de Recebimento de Mensagem WhatsApp

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE MENSAGEM WHATSAPP                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   WhatsApp   │────▶│ Evolution API│────▶│   Webhook    │────▶│  Normalize   │
│   (Cliente)  │     │   (Server)   │     │   Receiver   │     │    Data      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                       │
                                                                       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Resposta   │◀────│   Message    │◀────│   AI Engine  │◀────│   Find/      │
│  WhatsApp    │     │   Sender     │     │   Analysis   │     │Create Ticket │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Componentes Envolvidos

| Etapa | Componente | Arquivo |
|-------|------------|---------|
| Webhook Receiver | `evolution_sync.views` | `app/evolution_sync/views.py` |
| Normalize Data | `evolution_sync.normalizers` | `app/evolution_sync/normalizers.py` |
| Find/Create Ticket | `evolution_sync.services.webhook` | `app/evolution_sync/services/webhook.py` |
| AI Analysis | `ai_engine.features.analise_mensage` | `modules/ai_engine/features/analise_mensage/` |
| Message Sender | `evolution_sync.services.evolution_api` | `app/evolution_sync/services/evolution_api.py` |

### Detalhamento do Fluxo

1. **Recebimento do Webhook**
   - Evolution API envia POST para `/webhook/evolution/`
   - Payload contém dados da mensagem (texto, mídia, sender)

2. **Normalização**
   - Dados são normalizados para formato interno
   - Validação de campos obrigatórios

3. **Identificação de Atendimento**
   - Busca atendimento existente pelo número do remetente
   - Se não existe, cria novo atendimento

4. **Análise de IA**
   - Mensagem é enviada para `analise_mensage` usecase
   - Processamento via LangChain com contexto do atendimento

5. **Resposta**
   - Resposta gerada é enviada via Evolution API
   - Status de entrega é monitorado

---

## 2. Fluxo de Processamento de Documento

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE DOCUMENTO PARA RAG                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Upload     │────▶│   Load       │────▶│   Generate   │────▶│    Store     │
│   Document   │     │   Document   │     │   Chunks     │     │   Chunks     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                       │
                                                                       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Ready      │◀────│   Store      │◀────│   Generate   │◀────│   Process    │
│   for RAG    │     │  to pgvector │     │  Embeddings  │     │   Celery     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Componentes Envolvidos

| Etapa | Componente | Arquivo |
|-------|------------|---------|
| Upload Document | `treinamento.views` | `app/treinamento/views.py` |
| Load Document | `ai_engine.features.load_document_file` | `modules/ai_engine/features/load_document_file/` |
| Generate Chunks | `ai_engine.features.generate_chunks` | `modules/ai_engine/features/generate_chunks/` |
| Generate Embeddings | `ai_engine.features.generate_embeddings` | `modules/ai_engine/features/generate_embeddings/` |
| Store to pgvector | `treinamento.services` | `app/treinamento/services.py` |

### Tipos de Documento Suportados

- PDF (via PyPDF)
- DOCX (via docx2txt)
- TXT
- XLSX/CSV (via openpyxl)
- Markdown

---

## 3. Fluxo de Sincronização com Trello

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE SINCRONIZAÇÃO TRELLO                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Atendimento  │────▶│   Django     │────▶│   Celery     │────▶│   Trello     │
│   Created    │     │   Signal     │     │    Task      │     │   API Call   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ TrelloSync   │
                    │   Model      │
                    └──────────────┘
```

### Eventos que Disparam Sincronização

| Evento Django | Ação Trello |
|---------------|-------------|
| Atendimento criado | Criar card |
| Atendimento atualizado | Atualizar card |
| Atendimento encerrado | Mover para lista "Concluído" |
| Mensagem adicionada | Adicionar comentário |

### Componentes Envolvidos

| Componente | Arquivo |
|------------|---------|
| Signals | `app/trello_sync/signals.py` |
| Tasks | `app/trello_sync/tasks.py` |
| Models | `app/trello_sync/models.py` |

---

## 3.b Workspace de Atendimento Unificado — SSE + Extração de Campos

### Fluxo de tempo real (Server-Sent Events)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            FLUXO SSE — sse:{tenant_slug}:events (Redis pub/sub)              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Signal     │──▶│   Service    │──▶│    Redis     │──▶│  async view  │
│  post_save   │   │   publish_   │   │  PUBLISH     │   │ /workspace/  │
│  (Mensagem,  │   │   event()    │   │ sse:<slug>:..│   │  events/     │
│  Atendimento,│   └──────────────┘   └──────────────┘   └──────┬───────┘
│ MovimentoFl.)│                                                  │
└──────────────┘                                                  ▼
                                                          ┌──────────────┐
                                                          │ EventSource  │
                                                          │ (Alpine.js)  │
                                                          │ atualiza UI  │
                                                          └──────────────┘
```

### Componentes

| Etapa | Componente | Arquivo |
|---|---|---|
| Signal receivers | `atendimento_unificado.signals` | `app/atendimento_unificado/signals.py` |
| Realtime publisher | `services.realtime_publisher.publish_event` | `app/atendimento_unificado/services/realtime_publisher.py` |
| Async stream | `views_sse.workspace_events` | `app/atendimento_unificado/views_sse.py` |
| Feature flag / canal | `feature_flags.get_sse_channel` | `app/atendimento_unificado/feature_flags.py` |

### Tipos de evento publicados

| Evento | Origem | Payload |
|---|---|---|
| `message.new` / `message.updated` | `post_save Mensagem` | `atendimento_id`, `mensagem_id`, `remetente`, `tipo`, `preview`, `respondida`, `timestamp` |
| `board.moved` | `post_save MovimentoFluxo` | `atendimento_id`, `etapa_origem_id`, `etapa_destino_id`, `automatico` |
| `atendimento.created` / `atendimento.updated` | `post_save Atendimento` | `atendimento_id`, `status`, `prioridade`, `etapa_id`, `fluxo_id`, `atendente_id` |
| `custom_field.updated` | task `extract_custom_fields_async` + PATCH manual | `atendimento_id`, `slug`, `valor`, `origem`, `confianca` |

### Isolamento multi-tenant

- Canal Redis exclusivo por tenant: `sse:{tenant_slug}:events`.
- `views_sse.workspace_events` valida `tenant_slug` da request e filtra
  defense-in-depth no consumidor (descarta payload se `tenant_slug` no
  evento não bate).
- Heartbeat `: ping` a cada 25s evita timeouts intermediários.

---

## 3.c Extração de Campos Personalizados (LLM)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FLUXO DE EXTRAÇÃO DE CAMPOS POR RESPOSTA DO BOT                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Mensagem   │──▶│   Signal     │──▶│   Celery     │──▶│  ai_engine.  │
│  (TipoRem.   │   │ _on_mensagem │   │   task       │   │  extracao_   │
│   BOT)       │   │  _bot_       │   │ extract_     │   │  campos      │
│  post_save   │   │  extrair_    │   │ custom_      │   │ (with_struct.│
│              │   │  campos      │   │ fields_async │   │  _output)    │
└──────────────┘   └──────────────┘   └──────┬───────┘   └──────┬───────┘
                                              │                  │
                                              ▼                  ▼
                                      ┌──────────────┐   ┌──────────────┐
                                      │ select_for_  │   │ pydantic.    │
                                      │ update +     │   │ create_model │
                                      │ idempotência │   │ dinâmico     │
                                      │ (nunca       │   │ (schema dos  │
                                      │  sobrescreve │   │  campos      │
                                      │  MANUAL;     │   │  ativos)     │
                                      │  BOT só se   │   └──────────────┘
                                      │  conf maior) │
                                      └──────┬───────┘
                                             │
                                             ▼
                                      ┌──────────────┐    ┌──────────────┐
                                      │  Valor       │───▶│   publish    │
                                      │ Campo        │    │ custom_field.│
                                      │ Atendimento  │    │   updated    │
                                      └──────────────┘    └──────────────┘
                                             │
                                             ▼
                                  Próxima resposta do bot
                                  (analise_mensage_datasource):
                                  injeta `### CAMPOS COLETADOS`
                                  e `### CAMPOS PENDENTES` no
                                  system prompt
```

### Componentes

| Etapa | Componente | Arquivo |
|---|---|---|
| Signal de extração | `atendimento_unificado.signals._on_mensagem_bot_extrair_campos` | `app/atendimento_unificado/signals.py` |
| Celery task | `tasks.extract_custom_fields_async` | `app/atendimento_unificado/tasks.py` |
| Feature LLM | `ai_engine.features.extracao_campos` | `modules/ai_engine/features/extracao_campos/` |
| Helper para prompt | `selectors.get_campos_for_prompt` | `app/atendimento_unificado/selectors.py` |
| Injeção no prompt | `_formatar_campos_personalizados` | `modules/ai_engine/features/analise_mensage/datasource/analise_mensage_datasource.py` |

### Regras de idempotência

1. `confianca>=0.9` no BOT → skip nova extração para o slug.
2. Valor existente com `origem=MANUAL` → nunca sobrescreve.
3. Valor existente com `origem=BOT` → sobrescreve apenas se nova
   confiança for **maior**.
4. Idempotência protegida por `select_for_update` na transação.

---

## 4. Fluxo de Autenticação e Multi-Tenancy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE REQUEST COM TENANT                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Request    │────▶│   Tenant     │────▶│   Auth       │────▶│   Route to   │
│   HTTP       │     │  Middleware  │     │  Middleware  │     │  Tenant DB   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                       │
                                                                       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Response   │◀────│   Process    │◀────│   Query      │◀────│   View       │
│   HTTP       │     │   Response   │     │   Tenant DB  │     │   Handler    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Detalhamento

1. **TenantMiddleware** (`app/tenants/middleware.py`)
   - Identifica tenant pelo header ou subdomain
   - Configura contexto de tenant para request

2. **TenantDatabaseRouter** (`app/tenants/db_router.py`)
   - Roteia todas as queries para o banco do tenant
   - Garante isolamento de dados

3. **Auth Middleware**
   - Verifica autenticação e permissões
   - Valida acesso do usuário ao tenant

---

## 5. Integrações Externas

### 5.1 Evolution API (WhatsApp)

```
Smart Core <──────> Evolution API <──────> WhatsApp Business
           HTTP/REST              Cloud API
```

**Endpoints principais:**
- `POST /message/sendText` - Enviar mensagem
- `POST /instance/connect` - Conectar instância
- `GET /instance/fetchInstances` - Listar instâncias

### 5.2 Firebase Remote Config

```
Smart Core <──────> Firebase Admin SDK <──────> Remote Config
           Python SDK                   Cloud
```

**Uso:** Gerenciamento dinâmico de prompts de IA.

### 5.3 LLM Providers

```
                     ┌──────────────┐
                     │   LangChain  │
                     └──────┬───────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │  OpenAI  │      │   Groq   │      │  Ollama  │
   │   API    │      │   API    │      │  (Local) │
   └──────────┘      └──────────┘      └──────────┘
```

**Configuração:** Via variáveis de ambiente no `.env`.

---

## 6. Diagrama de Banco de Dados (Simplificado)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENTIDADES PRINCIPAIS                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Tenant     │────▶│   Usuario    │────▶│ Departamento │
│              │     │              │     │              │
│ - nome       │     │ - email      │     │ - nome       │
│ - database   │     │ - tenant_fk  │     │ - tenant_fk  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Cliente    │────▶│ Atendimento  │◀────│FluxoAtendim. │
│              │     │              │     │              │
│ - nome       │     │ - status     │     │ - nome       │
│ - telefone   │     │ - cliente_fk │     │ - departam.  │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Mensagem   │
                     │              │
                     │ - conteudo   │
                     │ - direcao    │
                     │ - timestamp  │
                     └──────────────┘
```

Para diagrama completo, consulte: `docs_dev/diagramas/oraculo/entidades/`

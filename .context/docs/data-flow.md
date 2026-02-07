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

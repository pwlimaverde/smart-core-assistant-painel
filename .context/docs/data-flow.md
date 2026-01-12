# Fluxo de Dados e Integrações

## Visão Geral

Este documento descreve como os dados fluem através do sistema Smart Core Assistant Painel, desde a entrada (webhooks, APIs, interfaces) até o armazenamento e sincronização com sistemas externos.

## Fluxos Principais

### 1. Recebimento de Mensagens WhatsApp

```
┌──────────────┐     ┌─────────────────┐     ┌────────────────┐
│ Evolution API│────►│  Webhook Django │────►│  Validação     │
│   (WhatsApp) │     │  /webhook/wa/   │     │  UTF-8/JSON    │
└──────────────┘     └─────────────────┘     └────────────────┘
                                                     │
                                                     ▼
┌──────────────┐     ┌─────────────────┐     ┌────────────────┐
│  Resposta    │◄────│   ai_engine     │◄────│  Celery Task   │
│  ao Usuário  │     │ AnaliseMensage  │     │ (Queue: ai)    │
└──────────────┘     └─────────────────┘     └────────────────┘
```

**Detalhes do fluxo:**

1. A Evolution API envia um webhook com a mensagem recebida
2. O endpoint Django valida o encoding (UTF-8 com fallback automático)
3. Uma task Celery é enfileirada para processamento assíncrono
4. O módulo `analise_mensage` classifica e processa a mensagem
5. A resposta é enviada de volta via Evolution API

### 2. Sincronização de Atendimentos (Trello/ClickUp)

```
┌──────────────┐     ┌─────────────────┐     ┌────────────────┐
│ Django Model │────►│  Signal Handler │────►│  Celery Task   │
│  (post_save) │     │  (receivers.py) │     │ (Queue: sync)  │
└──────────────┘     └─────────────────┘     └────────────────┘
                                                     │
                     ┌───────────────────────────────┼───────────────────┐
                     │                               │                   │
                     ▼                               ▼                   ▼
              ┌─────────────┐              ┌─────────────┐      ┌─────────────┐
              │ Trello API  │              │ ClickUp API │      │ Notion API  │
              │  (Cards)    │              │   (Tasks)   │      │ (Pages)     │
              └─────────────┘              └─────────────┘      └─────────────┘
```

**Detalhes do fluxo:**

1. Ao salvar/atualizar um modelo Django, um signal é disparado
2. O handler do signal enfileira uma task Celery
3. A task sincroniza os dados com a plataforma correspondente
4. Mapeamentos são gerados: `Departamento` → `Folder/Space`, `Fluxo` → `List`, `Atendimento` → `Card/Task`

### 3. Processamento de IA (Análise de Conteúdo)

```
┌──────────────┐     ┌─────────────────┐     ┌────────────────┐
│  Conteúdo    │────►│  AnaliseConteudo│────►│  LangChain     │
│  (Texto/PDF) │     │    Usecase      │     │   Pipeline     │
└──────────────┘     └─────────────────┘     └────────────────┘
                                                     │
                                                     ▼
                                             ┌────────────────┐
                                             │   Embeddings   │
                                             │  (HuggingFace) │
                                             └────────────────┘
                                                     │
                                                     ▼
                                             ┌────────────────┐
                                             │   pgvector     │
                                             │  (PostgreSQL)  │
                                             └────────────────┘
```

## Camada de Serviços

### Serviços de Sincronização

| Serviço                     | Arquivo                                           | Função                        |
| --------------------------- | ------------------------------------------------- | ----------------------------- |
| `TreinamentoService`        | `app/ui/treinamento/services.py`                  | Gestão de treinamentos IA     |
| `WebhookProcessingService`  | `app/trello_sync/services/webhook_processing*.py` | Processa webhooks Trello      |
| `TicketSyncService`         | `app/trello_sync/services/ticket_sync*.py`        | Sincroniza tickets            |
| `MemberSyncService`         | `app/trello_sync/services/member_sync*.py`        | Sincroniza membros            |
| `FlowSyncService`           | `app/trello_sync/services/flow_sync*.py`          | Sincroniza fluxos             |
| `TenantProvisioningService` | `app/tenants/services/provisioning.py`            | Provisiona novos tenants      |
| `EvolutionWhatsAppService`  | `app/evolution_sync/services/evolution_api.py`    | Comunicação com Evolution API |

### Serviços do Motor de IA

| Serviço                     | Módulo              | Função                       |
| --------------------------- | ------------------- | ---------------------------- |
| `AnaliseMensageUsecase`     | `analise_mensage`   | Classifica mensagens         |
| `AnaliseConteudoUseCase`    | `analise_conteudo`  | Extrai informações de textos |
| `AnaliseAvaliacaoUsecase`   | `analise_avaliacao` | Processa avaliações          |
| `UnifiedDataServiceAdapter` | `unified_data*`     | Abstração multi-fonte        |

## Dependências entre Módulos

```
app/ui/core/urls.py
    └── app/ui/usuarios/urls.py
    └── app/ui/treinamento/urls.py
    └── app/trello_sync/api_urls.py

modules/ai_engine/
    └── features/unified_data_services/
        └── features/analise_mensage/
        └── features/analise_conteudo/
        └── features/analise_avaliacao/
```

## Filas Celery

O sistema utiliza filas especializadas para diferentes tipos de processamento:

| Fila            | Propósito                               | Workers |
| --------------- | --------------------------------------- | ------- |
| `webhooks`      | Processamento de webhooks em tempo real | Alta    |
| `ai_processing` | Tarefas de IA (análise, embeddings)     | Média   |
| `default`       | Tarefas gerais e sincronização          | Normal  |

## APIs Públicas Principais

### Endpoints REST

| Endpoint                | Método | Descrição                |
| ----------------------- | ------ | ------------------------ |
| `/api/v1/atendimentos/` | CRUD   | Gestão de atendimentos   |
| `/api/v1/mensagens/`    | CRUD   | Histórico de mensagens   |
| `/webhook/trello/`      | POST   | Recebe webhooks Trello   |
| `/webhook/evolution/`   | POST   | Recebe webhooks WhatsApp |

### Exports Principais

| Símbolo                        | Módulo                       | Tipo       |
| ------------------------------ | ---------------------------- | ---------- |
| `SERVICEHUB`                   | `modules/services/features/` | Singleton  |
| `AdminStaffRequiredMiddleware` | `app/ui/core/middleware.py`  | Middleware |
| `TenantProvisioningService`    | `app/tenants/services/`      | Service    |

## Tratamento de Erros

Todos os serviços utilizam o padrão `ReturnSuccessOrError`:

```python
result = usecase.execute(params)
if result.is_success():
    data = result.get_value()
else:
    error = result.get_error()
    logger.error(f"Falha: {error}")
```

---

_Documentação gerada via ai-context com análise das dependências reais do código._

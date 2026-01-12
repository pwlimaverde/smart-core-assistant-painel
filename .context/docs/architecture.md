# Arquitetura do Sistema

## Visão Geral

O Smart Core Assistant Painel segue uma arquitetura modular baseada em camadas, combinando o padrão Django tradicional com Clean Architecture nos módulos de lógica de negócio. O sistema é projetado para alta coesão e baixo acoplamento.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAMADA DE APRESENTAÇÃO                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Django    │  │    REST     │  │      Webhooks           │  │
│  │   Admin     │  │    APIs     │  │  (Trello/ClickUp/WA)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      CAMADA DE APLICAÇÃO                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Views     │  │  Services   │  │     Serializers         │  │
│  │  (Django)   │  │  (Sync)     │  │   (DRF + Pydantic)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       CAMADA DE DOMÍNIO                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     ai_engine (modules/)                     ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  ││
│  │  │   Features  │  │   Utils     │  │     Domain          │  ││
│  │  │  (Usecases) │  │  (Types)    │  │    (Entities)       │  ││
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE INFRAESTRUTURA                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │PostgreSQL│ │  Redis   │ │  Celery  │ │   APIs Externas    │  │
│  │(pgvector)│ │ (Cache)  │ │ (Workers)│ │(Evolution/Trello)  │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Padrões Arquiteturais

### 1. Clean Architecture (Módulos)

Os módulos de lógica de negócio seguem Clean Architecture com:

```
modules/ai_engine/
├── features/                      # Casos de uso específicos
│   ├── analise_avaliacao/
│   │   ├── datasource/           # Implementação de acesso a dados
│   │   ├── domain/
│   │   │   └── usecase/          # Regras de negócio
│   │   └── repository/           # Abstração de dados
│   ├── analise_conteudo/
│   ├── analise_mensage/
│   └── unified_data_services/    # Serviço unificado de dados
└── utils/
    ├── types.py                  # Tipos Pydantic compartilhados
    ├── parameters.py             # Parâmetros de configuração
    └── erros.py                  # Exceções customizadas
```

### 2. Padrão py-return-success-or-error

Todas as operações de negócio retornam `ReturnSuccessOrError`:

```python
from py_return_success_or_error import ReturnSuccessOrError

class AnaliseMensageUsecase:
    def execute(self, params: AnaliseMensageParameters) -> ReturnSuccessOrError:
        # Validação e processamento
        # Retorna Success(data) ou Error(exception)
```

### 3. Signals para Sincronização

Cada app de sincronização utiliza signals do Django para disparar sincronizações:

```python
# Exemplo: ao salvar um Departamento
@receiver(post_save, sender=Departamento)
def sync_departamento_to_clickup(sender, instance, created, **kwargs):
    # Enfileira tarefa Celery para sincronização
    sync_department_task.delay(instance.id)
```

## Componentes Principais

### Apps Django (`app/`)

| App              | Responsabilidade                            |
| ---------------- | ------------------------------------------- |
| `ui/core`        | Configurações Django, middleware, templates |
| `ui/usuarios`    | Autenticação, permissões, perfis            |
| `ui/treinamento` | Interface de treinamento de modelos IA      |
| `tenants`        | Multi-tenancy e provisionamento             |
| `trello_sync`    | Sincronização bidirecional com Trello       |
| `clickup_sync`   | Integração com ClickUp Spaces/Lists         |
| `notion_sync`    | Sincronização com databases Notion          |
| `evolution_sync` | WhatsApp via Evolution API                  |

### Módulos de Negócio (`modules/`)

| Módulo                  | Funcionalidade                           |
| ----------------------- | ---------------------------------------- |
| `analise_avaliacao`     | Processamento de avaliações              |
| `analise_conteudo`      | Extração de informações de textos        |
| `analise_mensage`       | Classificação de mensagens               |
| `unified_data_services` | Abstração para múltiplas fontes de dados |

## Fluxo de Dados

### Webhook WhatsApp (Evolution API)

```
Evolution API
     │
     ▼
[Webhook Endpoint] ──► [Celery Task: webhooks]
     │                        │
     ▼                        ▼
[Validação UTF-8]      [Processamento Assíncrono]
     │                        │
     ▼                        ▼
[Fallback Encoding]    [ai_engine: Análise]
                              │
                              ▼
                       [Resposta via API]
```

### Sincronização Trello/ClickUp

```
[Django Signal: post_save] ──► [Celery Task]
           │                        │
           ▼                        ▼
    [Validação]              [API Externa]
           │                        │
           ▼                        ▼
    [Atualização Local]      [Sync Concluída]
```

## Configuração e Ambiente

### Variáveis de Ambiente Principais

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis/Celery
REDIS_URL=redis://host:6379/0

# Integrações
EVOLUTION_API_URL=https://...
EVOLUTION_API_KEY=...
TRELLO_API_KEY=...
CLICKUP_API_TOKEN=...
NOTION_TOKEN=...

# IA
OPENAI_API_KEY=...
GROQ_API_KEY=...
```

## Decisões Arquiteturais

### Por que Django + Clean Architecture?

1. **Django** fornece uma base sólida para apps web com ORM, admin e autenticação
2. **Clean Architecture nos módulos** permite testar regras de negócio isoladamente
3. **Celery** desacopla processamento pesado (IA, webhooks) do request principal

### Por que múltiplos provedores de IA?

- **Fallback**: Se um provedor falha, outro assume
- **Otimização de custos**: Groq para tarefas simples, OpenAI para complexas
- **Especialização**: Ollama para embeddings locais

---

_Documentação gerada via ai-context com análise semântica detalhada._

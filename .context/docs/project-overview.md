# Visão Geral do Projeto

## Resumo Executivo

O **Smart Core Assistant Painel** é uma plataforma de assistente virtual inteligente desenvolvida em Django 5.2 com Python 3.13. O sistema centraliza operações de atendimento ao cliente através de múltiplas integrações externas, incluindo WhatsApp (via Evolution API), Trello, ClickUp e Notion.

A arquitetura segue o padrão `py-return-success-or-error` para tratamento de erros e retornos de sucesso, garantindo robustez e previsibilidade no fluxo de dados. O projeto utiliza uma infraestrutura containerizada com Docker, suportando tanto desenvolvimento local quanto deploy remoto.

## Características Principais

### Integrações Nativas

- **WhatsApp** via Evolution API com tratamento UTF-8 robusto e fallback de encoding automático
- **Trello** para sincronização de fluxos de atendimento
- **ClickUp** para gestão de tarefas e departamentos
- **Notion** para bases de dados e documentação
- **Firebase** para autenticação e notificações

### Processamento de Linguagem Natural

- Integração com múltiplos provedores de IA (OpenAI, Groq, Ollama, XAI)
- Pipelines LangChain para análise de conteúdo e mensagens
- Sistema de embeddings com HuggingFace
- Armazenamento vetorial com pgvector

### Infraestrutura

- **Django 5.2** como framework web principal
- **PostgreSQL** com extensão pgvector para busca vetorial
- **Redis** para cache e filas Celery
- **Celery** para processamento assíncrono de webhooks e IA

## Arquitetura

### Métricas do Código

| Categoria    | Quantidade |
| ------------ | ---------- |
| Arquivos     | 381        |
| Símbolos     | 605        |
| Serviços     | 91         |
| Modelos      | 97         |
| Componentes  | 63         |
| Repositórios | 25         |
| Controllers  | 9          |
| Utilitários  | 27         |

### Estrutura de Diretórios

```
src/smart_core_assistant_painel/
├── app/                    # Aplicações Django
│   ├── ui/                 # Interface web e admin
│   │   ├── core/          # Configurações centrais
│   │   ├── usuarios/      # Gestão de usuários
│   │   └── treinamento/   # Módulo de treinamento IA
│   ├── tenants/           # Multi-tenancy
│   ├── trello_sync/       # Sincronização Trello
│   ├── clickup_sync/      # Sincronização ClickUp
│   ├── notion_sync/       # Sincronização Notion
│   └── evolution_sync/    # WhatsApp via Evolution API
└── modules/               # Lógica de negócio
    └── ai_engine/         # Motor de IA
        ├── features/      # Casos de uso
        └── utils/         # Utilitários
```

## Componentes Principais

### Motor de IA (`ai_engine`)

O módulo central de processamento de linguagem natural, responsável por:

- **Análise de Mensagens**: Processamento e classificação de mensagens WhatsApp
- **Análise de Conteúdo**: Extração de informações estruturadas
- **Análise de Avaliações**: Processamento de feedback de usuários
- **Serviços Unificados de Dados**: Abstração para múltiplas fontes de dados

### Sincronização Externa

Cada módulo de sincronização segue o padrão de signals do Django:

- **evolution_sync**: Gestão de instâncias WhatsApp, webhooks e mensagens
- **trello_sync**: Sincronização de tickets e fluxos de atendimento
- **clickup_sync**: Gestão de espaços, pastas e listas
- **notion_sync**: Sincronização de bases de dados e páginas

### Multi-Tenancy (`tenants`)

Sistema de provisionamento de tenants com:

- Isolamento de dados por organização
- Gestão de convites e ativação de contas
- Configurações específicas por tenant

## Stack Tecnológica

### Backend

- Python 3.13+
- Django 5.2
- Django REST Framework
- Celery com Redis
- PostgreSQL com pgvector

### IA/ML

- LangChain (core, community, text-splitters)
- OpenAI, Groq, Ollama, XAI
- HuggingFace Hub
- TikToken

### Ferramentas de Desenvolvimento

- `uv` para gestão de dependências
- `ruff` para linting e formatação
- `pyright` para verificação de tipos (modo estrito)
- `pytest` para testes
- `mkdocs` para documentação

## Ambientes de Desenvolvimento

### Local

Desenvolvimento com bancos de dados em Docker e aplicação local.

### Remoto

Deploy via Docker Compose com stacks separados:

- **Data Stack**: PostgreSQL + Redis
- **App Stack**: Django + Migrate
- **Workers Stack**: Celery Worker + Beat
- **Infra Stack**: Cloudflared + Flower

---

_Documentação gerada automaticamente via ai-context e enriquecida com análise semântica._
_Última atualização: Janeiro 2026_

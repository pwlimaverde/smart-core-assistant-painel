# Project Context

## Purpose

**Smart Core Assistant Painel** é um painel de administração inteligente para assistentes virtuais com integração WhatsApp. O projeto oferece uma plataforma multi-tenant SaaS para empresas gerenciarem atendimentos automatizados por IA, bases de conhecimento, fluxos de atendimento e integrações com serviços externos.

### Objetivos Principais

- Centralizar a gestão de assistentes virtuais baseados em IA
- Fornecer integração robusta com WhatsApp via Evolution API
- Habilitar criação e gestão de bases de conhecimento (RAG/Vector Storage)
- Suportar múltiplos tenants (empresas) com isolamento de dados
- Integrar com plataformas de gestão de projetos (Trello, ClickUp, Notion)

## Tech Stack

### Backend

- **Python 3.13+** - Linguagem principal
- **Django 5.2** - Framework web principal
- **Django REST Framework** - API RESTful
- **Celery + Redis** - Processamento assíncrono de tarefas
- **PostgreSQL + pgvector** - Banco de dados com suporte a embeddings vetoriais

### AI e NLP

- **LangChain** - Framework para aplicações de LLM
- **OpenAI / Groq / Ollama / HuggingFace** - Provedores de LLM
- **LangSmith** - Observabilidade e tracing de LLM

### Integrações

- **Evolution API** - WhatsApp Business API
- **Trello / ClickUp / Notion** - Gestão de projetos
- **Firebase Admin** - Autenticação e serviços

### DevOps e Ferramentas

- **Docker / Docker Compose** - Containerização
- **uv** - Gerenciador de dependências Python
- **Taskipy** - Automação de tarefas
- **mkdocs + material** - Documentação

### Qualidade de Código

- **Ruff** - Linting e formatação (PEP8)
- **Pyright (strict)** - Verificação estática de tipos
- **Loguru** - Logging estruturado
- **Rich** - Saídas de terminal

## Project Conventions

### Code Style

- **Guia de Estilo**: PEP8 estrito
- **Comprimento de Linha**: Máximo 79 caracteres
- **Nomenclatura**:
  - Variáveis e funções: `snake_case` (em Inglês)
  - Classes: `PascalCase` (em Inglês)
  - Comentários: Português
- **Type Hints**: Obrigatórios em TODAS as funções e métodos
- **Docstrings**: Estilo Google

### Architecture Patterns

- **Layout src/**: Todo código em `src/smart_core_assistant_painel/`
- **Separação**:
  - `app/ui/` - Django apps (models, views, templates, signals)
  - `modules/` - Lógica de negócio pura (services, usecases)
- **py-return-success-or-error**: Padrão para tratamento de erros em serviços
- **Facade Pattern**: `__init__.py` expõe API pública via `__all__`

### Testing Strategy

- Testes executados no Docker: `uv run task test-docker`
- Scripts de debug isolados em `teste_debug/`
- Testes são responsabilidade de agente dedicado

### Git Workflow

- **Branching**: GitFlow
  - `feature/` - novas funcionalidades
  - `bugfix/` - correções em desenvolvimento
  - `hotfix/` - correções urgentes em produção
  - `release/` - preparação de versões
- **Commits**: Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `chore`)
- **Pre-commit hooks** ativos

## Domain Context

### Multi-Tenancy

O sistema suporta múltiplos *tenants* (empresas clientes). Cada tenant possui:

- Isolamento de dados completo
- Configurações próprias de IA (persona, mensagens de fallback)
- Usuários com permissões granulares por módulo
- Subdomínio próprio (`{slug}.app.smartcoreassistant.com.br`)

### Fluxo de Atendimento

1. Mensagem recebida via webhook (Evolution API/WhatsApp)
2. Identificação do contato/cliente
3. Processamento por IA com contexto do tenant
4. Consulta à base de conhecimento (RAG)
5. Resposta enviada via WhatsApp
6. Registro e sincronização com plataformas externas

### Conceitos-Chave

- **Departamento**: Unidade organizacional do tenant
- **FluxoAtendimento**: Sequência de etapas de atendimento
- **Atendente**: Usuário que pode intervir em atendimentos
- **Base de Conhecimento**: Documentos vetorizados para RAG

## Important Constraints

- **Ambiente**: Windows como SO de desenvolvimento primário
- **Segurança**: Nenhum secret em código; usar `.env` + `python-decouple`
- **Python**: Versão 3.13+ obrigatória
- **Tipos**: Pyright em modo estrito; erros de tipo bloqueiam merge
- **Idioma**: Documentação e comunicação em Português; código em Inglês

## External Dependencies

### APIs Externas

| Serviço        | Propósito                        | Configuração           |
|----------------|----------------------------------|------------------------|
| Evolution API  | WhatsApp Business                | `EVOLUTION_*` no .env  |
| OpenAI         | LLM principal                    | `OPENAI_API_KEY`       |
| Groq           | LLM alternativo (rápido)         | `GROQ_API_KEY`         |
| LangSmith      | Tracing de LLM                   | `LANGSMITH_*`          |
| Notion         | Sincronização de dados           | `NOTION_*`             |
| Trello         | Gestão de tarefas                | `TRELLO_*`             |
| ClickUp        | Gestão de projetos               | `CLICKUP_*`            |
| Firebase       | Autenticação                     | Credenciais JSON       |

### Serviços de Infraestrutura

- **PostgreSQL**: Banco principal (local ou remoto)
- **Redis**: Cache e broker do Celery
- **Cloudflare Pages**: Hospedagem da landing page

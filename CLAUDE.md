# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) para trabalhar com o código deste repositório.

**IMPORTANTE: O idioma padrão de comunicação neste projeto é Português. Todas as respostas, planos de implementação, explicações e feedbacks devem ser em Português.**

## Contexto do Projeto (AI-Context MCP)

Este projeto utiliza o MCP ai-context para organizar documentação e contexto. Consulte os recursos abaixo conforme necessário:

### Documentação Principal
- [Índice de Documentação](.context/docs/README.md) - Ponto de entrada para toda documentação
- [Visão Geral do Projeto](.context/docs/project-overview.md) - Roadmap e notas de stakeholders
- [Arquitetura](.context/docs/architecture.md) - ADRs, limites de serviços, grafos de dependência
- [Fluxo de Dados](.context/docs/data-flow.md) - Diagramas de sistema, specs de integração
- [Workflow de Desenvolvimento](.context/docs/development-workflow.md) - Regras de branching, CI
- [Estratégia de Testes](.context/docs/testing-strategy.md) - Configs de teste, gates de CI
- [Glossário](.context/docs/glossary.md) - Terminologia de negócio e conceitos de domínio
- [Segurança](.context/docs/security.md) - Modelo de auth, gestão de secrets
- [Ferramentas](.context/docs/tooling.md) - Scripts CLI, configs de IDE

### Agentes Especializados
- [Handbook de Agentes](.context/agents/README.md) - Índice de todos os playbooks
- Playbooks disponíveis: code-reviewer, bug-fixer, feature-developer, refactoring-specialist, test-writer, documentation-writer, performance-optimizer, security-auditor, backend-specialist, frontend-specialist, architect-specialist, devops-specialist, database-specialist

### Planos de Implementação
- [Planos Ativos](.context/plans/README.md) - Planos de features e refatorações em andamento

### Workflows e Slash Commands

Os workflows do projeto estão definidos em `.agent/workflows/` e mapeados para slash commands em `.claude/commands/`:

| Slash Command | Workflow | Descrição |
|---------------|----------|-----------|
| `/openspec-proposal` | [openspec-proposal.md](.agent/workflows/openspec-proposal.md) | Cria plano AI-Context e proposta OpenSpec com validação em duas etapas |
| `/openspec-apply` | [openspec-apply.md](.agent/workflows/openspec-apply.md) | Implementa mudança aprovada consultando plano e documentação |
| `/openspec-archive` | [openspec-archive.md](.agent/workflows/openspec-archive.md) | Arquiva mudança concluída e move plano para histórico |

> **Nota**: Os commands em `.claude/commands/` referenciam os workflows em `.agent/workflows/` via `$INCLUDE`. Ao alterar um workflow, o command correspondente refletirá automaticamente as mudanças.

## Visão Geral do Projeto

Smart Core Assistant Painel é uma plataforma SaaS multi-tenant para atendimento inteligente ao cliente via WhatsApp. Construído com Django 5.2, integra análise de mensagens com IA (LangChain), mensagens WhatsApp (Evolution API) e sincronização de tarefas (Trello, ClickUp, Notion).

## Comandos Essenciais

Todos os comandos usam o gerenciador de pacotes `uv` com taskipy. Sempre execute com `uv run task <nome>`.

### Desenvolvimento
```bash
uv run task start              # Inicia servidor Django (0.0.0.0:8000)
uv run task celery-worker      # Inicia worker Celery
uv run task celery-beat        # Inicia agendador Celery beat
uv run task start-all          # Inicia todos os serviços (abas Windows Terminal)
```

### Banco de Dados
```bash
uv run task makemigrations     # Cria migrações Django
uv run task migrate            # Aplica migrações locais
uv run task migrate-remoto     # Aplica migrações no PostgreSQL remoto
uv run task createsuperuser    # Cria superusuário Django
```

### Qualidade de Código
```bash
uv run task lint               # Executa linter ruff
uv run task format             # Formata código com ruff
uv run task type-check         # Executa pyright (modo estrito)
```

### Testes
```bash
uv run task test-docker        # PREFERIDO - Executa testes no Docker
uv run task test               # Executa apenas diretório tests/
uv run task test-apps          # Executa apenas testes de apps Django
uv run task test-all           # Executa todos os testes localmente
```

Para executar um teste específico: `uv run task test-docker -- -k "nome_do_teste"`

## Arquitetura

### Estrutura de Diretórios
```
src/smart_core_assistant_painel/
├── main.py                    # Ponto de entrada da aplicação
├── app/
│   ├── ui/                    # Apps Django (views, models, templates)
│   │   ├── core/              # Configurações principais, middleware, views base
│   │   ├── atendimentos/      # Tickets de suporte e mensagens
│   │   ├── operacional/       # Departamentos, fluxos, atendentes
│   │   ├── clientes/          # Contatos e clientes
│   │   ├── usuarios/          # Gerenciamento de usuários
│   │   ├── treinamento/       # Treinamento de IA e gestão de documentos
│   │   └── oraculo/           # Interface do motor de IA
│   ├── tenants/               # Multi-tenancy (isolamento de BD por tenant)
│   ├── evolution_sync/        # Integração WhatsApp Evolution API
│   ├── trello_sync/           # Sincronização Trello
│   ├── clickup_sync/          # Sincronização ClickUp
│   ├── notion_sync/           # Sincronização Notion
│   └── settings_manager/      # Gerenciamento de configurações
└── modules/                   # Lógica de negócio reutilizável
    ├── services/              # Camada de serviços com factory ServiceHub
    │   └── features/          # unifield_data_services (adapters Trello/Notion/ClickUp)
    ├── ai_engine/             # Features de processamento IA (LangChain)
    │   └── features/          # load_document, generate_embeddings, analise_mensagem, etc.
    └── initial_loading/       # Inicialização Firebase
```

### Padrões Arquiteturais Principais

- **Multi-Tenant SaaS**: `TenantDatabaseRouter` roteia queries para bancos específicos por tenant
- **Camada de Serviços**: Factory `ServiceHub` cria instâncias de features via `FeaturesCompose`
- **Padrão Adapter**: Interface `UnifiedDataService` com adapters Trello/ClickUp/Notion
- **Integrações por Signals**: Signals Django disparam sincronização Trello/ClickUp automaticamente
- **Padrão Result**: Usa `py-return-success-or-error` para tratamento de erros

### Stack Tecnológica
- **Backend**: Django 5.2 + DRF + Celery (broker Redis)
- **Banco de Dados**: PostgreSQL 14 + pgvector (embeddings)
- **IA/NLP**: LangChain com múltiplos provedores LLM (OpenAI, Groq, Ollama)
- **WhatsApp**: Integração Evolution API
- **Admin UI**: Django Jazzmin

## Padrões de Código

### Idioma
- **Comunicação**: Português (planos, explicações, comentários no código)
- **Código**: Inglês (variáveis, funções, classes)

### Estilo
- PEP8 com limite de 79 caracteres por linha
- Type hints obrigatórios em todas as funções (pyright modo estrito)
- Docstrings no estilo Google
- `snake_case` para variáveis/funções, `PascalCase` para classes

### Type Hints
```python
# Sempre verifique tipos Union antes de acessar membros
if isinstance(response, dict):
    value = response.get("key", default)
else:
    value = response.attribute

# Signals usam: sender: Any, instance: ModelClass, created: bool, **kwargs: Any
```

### Imports em `__init__.py`
Centralize exports com `__all__`:
```python
"""Descrição do módulo."""
from .feature import FeatureClass
from .utils import helper_function

__all__ = ["FeatureClass", "helper_function"]
```

## Política de Testes

**NÃO crie testes automatizados** - isso é responsabilidade de um agente dedicado a testes. Para debugging, crie scripts exclusivamente no diretório `teste_debug/`.

## Convenções Git

- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`)
- **Branches**: Nomenclatura GitFlow
  - `feature/` - novas funcionalidades
  - `bugfix/` - correções de bugs em desenvolvimento
  - `hotfix/` - correções urgentes em produção
  - `release/` - preparação de versão

## Configurações Importantes

- Segredos vão no `.env` (nunca hardcode)
- Configurações Django: `src/smart_core_assistant_painel/app/ui/core/settings.py`
- Template de ambiente: `.env.example`

## Integrações Externas

- **WhatsApp**: Evolution API via app `evolution_sync`
- **Sincronização de Tarefas**: Adapters Trello, ClickUp, Notion em `modules/services/features/unifield_data_services/`
- **Prompts de IA**: Firebase Remote Config para gerenciamento dinâmico de prompts

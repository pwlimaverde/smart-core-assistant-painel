# GitHub Copilot Instructions - Smart Core Assistant Painel

## Language Configuration

**IMPORTANT**: All communication must be in **Portuguese (pt-BR)**. Code identifiers should be in English.

## Project Overview

**Smart Core Assistant Painel** is a multi-tenant SaaS platform for intelligent customer service via WhatsApp.

### Tech Stack

- **Backend**: Django 5.2 + Django REST Framework + Celery
- **Database**: PostgreSQL 14 + pgvector (embeddings)
- **AI/NLP**: LangChain with multiple LLM providers (OpenAI, Groq, Ollama)
- **WhatsApp**: Evolution API integration
- **Admin UI**: Django Jazzmin

## Code Standards

### Type Hints (Required - Pyright Strict)

```python
def process_message(
    message: str,
    context: dict[str, Any] | None = None,
) -> Result[AnalysisResult, Exception]:
    """Process customer message."""
    ...
```

### Result Pattern

```python
from py_return_success_or_error import Success, Failure, Result

def execute() -> Result[Data, Exception]:
    if validation_failed:
        return Failure(ValueError("Validation error"))
    return Success(processed_data)
```

### Multi-Tenancy (Always Filter)

```python
def get_queryset(self):
    return Model.objects.filter(tenant=self.request.user.tenant)
```

### Docstrings (Google Style)

```python
def function(param: str) -> str:
    """Brief description.

    Args:
        param: Parameter description.

    Returns:
        Return description.
    """
```

## Project Structure

```
src/smart_core_assistant_painel/
├── app/
│   ├── ui/                    # Django apps
│   │   ├── core/              # Settings, middleware
│   │   ├── atendimentos/      # Tickets and messages
│   │   ├── operacional/       # Departments, flows
│   │   ├── clientes/          # Contacts
│   │   ├── usuarios/          # Users
│   │   ├── treinamento/       # AI training
│   │   └── oraculo/           # AI engine interface
│   ├── tenants/               # Multi-tenancy
│   ├── evolution_sync/        # WhatsApp integration
│   └── trello_sync/           # Trello sync
└── modules/
    ├── ai_engine/             # LangChain features
    ├── services/              # Service layer
    └── initial_loading/       # Firebase init
```

## Commands

```bash
uv run task start              # Django server
uv run task celery-worker      # Celery worker
uv run task lint               # Linting (ruff)
uv run task type-check         # Type check (pyright)
uv run task test-docker        # Tests in Docker
uv run task makemigrations     # Create migrations
uv run task migrate            # Apply migrations
```

## Git Conventions

### Commits (Conventional Commits)
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` refactoring

### Branches (GitFlow)
- `feature/` new features
- `bugfix/` bug fixes
- `hotfix/` urgent fixes

## AI Context

- Documentation: `.context/docs/`
- Agents: `.context/agents/`
- Skills: `.context/skills/`
- Workflow: `.context/workflow/`
- Plans: `.context/plans/`

## Restrictions

1. **DO NOT create automated tests** - dedicated agent responsibility
2. **DO NOT hardcode secrets** - use environment variables
3. **ALWAYS respect tenant isolation**
4. **ALWAYS use type hints in functions**

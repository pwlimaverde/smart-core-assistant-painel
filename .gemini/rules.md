# Gemini Rules - Smart Core Assistant Painel

## Configuração de Idioma

**IMPORTANTE**: Toda comunicação deve ser em **Português (pt-BR)**. Código deve usar identificadores em inglês.

## Sobre o Projeto

**Smart Core Assistant Painel** é uma plataforma SaaS multi-tenant para atendimento inteligente ao cliente via WhatsApp.

### Tecnologias Principais

| Camada | Tecnologia |
|--------|------------|
| Backend | Django 5.2 + Django REST Framework |
| Async | Celery + Redis |
| Banco | PostgreSQL 14 + pgvector |
| IA | LangChain (OpenAI, Groq, Ollama) |
| WhatsApp | Evolution API |
| Admin | Django Jazzmin |

## Estrutura do Projeto

```
src/smart_core_assistant_painel/
├── app/
│   ├── ui/                    # Apps Django de interface
│   │   ├── core/              # Configurações centrais
│   │   ├── atendimentos/      # Tickets e mensagens
│   │   ├── operacional/       # Departamentos e fluxos
│   │   ├── clientes/          # Gestão de contatos
│   │   ├── usuarios/          # Gerenciamento de usuários
│   │   ├── treinamento/       # Treinamento de IA
│   │   └── oraculo/           # Interface do motor de IA
│   ├── tenants/               # Multi-tenancy
│   ├── evolution_sync/        # Integração WhatsApp
│   └── trello_sync/           # Sincronização Trello
└── modules/
    ├── ai_engine/             # Motor de IA com LangChain
    ├── services/              # Camada de serviços
    └── initial_loading/       # Inicialização Firebase
```

## Padrões Obrigatórios

### 1. Type Hints (Pyright Strict)

```python
def process_message(
    message: str,
    context: dict[str, Any] | None = None,
) -> Result[AnalysisResult, Exception]:
    """Processa mensagem de cliente."""
    ...
```

### 2. Result Pattern

```python
from py_return_success_or_error import Success, Failure, Result

def execute() -> Result[Data, Exception]:
    if validation_failed:
        return Failure(ValueError("Erro de validação"))
    return Success(processed_data)
```

### 3. Multi-Tenancy

```python
# SEMPRE filtrar por tenant
def get_queryset(self):
    return Model.objects.filter(tenant=self.request.user.tenant)
```

### 4. Docstrings (Google Style)

```python
def function(param: str) -> str:
    """Descrição breve.

    Args:
        param: Descrição do parâmetro.

    Returns:
        Descrição do retorno.

    Raises:
        ValueError: Quando parâmetro é inválido.
    """
```

## Comandos de Desenvolvimento

```bash
# Servidor
uv run task start              # Django dev server
uv run task celery-worker      # Celery worker
uv run task celery-beat        # Celery beat

# Qualidade
uv run task lint               # Linting (ruff)
uv run task format             # Formatação (ruff)
uv run task type-check         # Type check (pyright)

# Testes
uv run task test-docker        # Testes em Docker

# Banco
uv run task makemigrations     # Criar migrações
uv run task migrate            # Aplicar migrações
```

## Convenções Git

### Conventional Commits
- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` documentação
- `refactor:` refatoração
- `test:` testes
- `chore:` manutenção

### Branches (GitFlow)
- `feature/` novas funcionalidades
- `bugfix/` correções em desenvolvimento
- `hotfix/` correções urgentes
- `release/` preparação de versão

## Contexto de IA

O projeto utiliza o sistema ai-context para organização:

| Diretório | Conteúdo |
|-----------|----------|
| `.context/docs/` | Documentação técnica |
| `.context/agents/` | Playbooks de agentes |
| `.context/skills/` | Skills PREVC |
| `.context/workflow/` | Workflow de desenvolvimento |
| `.context/plans/` | Planos de implementação |

## Restrições

1. **NÃO criar testes automatizados** - responsabilidade de agente dedicado
2. **NÃO hardcodar secrets** - usar variáveis de ambiente
3. **SEMPRE respeitar isolamento de tenant**
4. **SEMPRE usar type hints em funções**

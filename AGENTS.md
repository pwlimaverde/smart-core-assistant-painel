# AGENTS.md - Smart Core Assistant Painel

Este arquivo fornece orientações para agentes de IA trabalharem com este repositório.

## Idioma

**IMPORTANTE**: Toda comunicação deve ser em **Português (pt-BR)**. Código deve usar identificadores em inglês.

## Sobre o Projeto

**Smart Core Assistant Painel** é uma plataforma SaaS multi-tenant para atendimento inteligente ao cliente via WhatsApp.

### Stack Tecnológica

| Camada | Tecnologia |
|--------|------------|
| Backend | Django 5.2 + Django REST Framework |
| Async | Celery + Redis |
| Banco | PostgreSQL 14 + pgvector |
| IA | LangChain (OpenAI, Groq, Ollama) |
| WhatsApp | Evolution API |
| Admin | Django Jazzmin |

## Contexto de IA (ai-context)

O projeto utiliza o sistema ai-context para organização estruturada de documentação e contexto.

### Documentação Principal

| Documento | Caminho | Descrição |
|-----------|---------|-----------|
| Índice | [.context/docs/README.md](.context/docs/README.md) | Ponto de entrada |
| Visão Geral | [.context/docs/project-overview.md](.context/docs/project-overview.md) | Roadmap e stakeholders |
| Arquitetura | [.context/docs/architecture.md](.context/docs/architecture.md) | ADRs e padrões |
| Fluxo de Dados | [.context/docs/data-flow.md](.context/docs/data-flow.md) | Diagramas de integração |
| Desenvolvimento | [.context/docs/development-workflow.md](.context/docs/development-workflow.md) | Git e CI/CD |
| Testes | [.context/docs/testing-strategy.md](.context/docs/testing-strategy.md) | Estratégia de testes |
| Glossário | [.context/docs/glossary.md](.context/docs/glossary.md) | Termos de domínio |
| Segurança | [.context/docs/security.md](.context/docs/security.md) | Auth e secrets |
| Ferramentas | [.context/docs/tooling.md](.context/docs/tooling.md) | Scripts e IDEs |

### Agentes Especializados

| Agente | Caminho | Especialidade |
|--------|---------|---------------|
| Feature Developer | [.context/agents/feature-developer.md](.context/agents/feature-developer.md) | Novas features |
| Bug Fixer | [.context/agents/bug-fixer.md](.context/agents/bug-fixer.md) | Correção de bugs |
| Code Reviewer | [.context/agents/code-reviewer.md](.context/agents/code-reviewer.md) | Revisão de código |
| Refactoring | [.context/agents/refactoring-specialist.md](.context/agents/refactoring-specialist.md) | Refatoração |
| Backend | [.context/agents/backend-specialist.md](.context/agents/backend-specialist.md) | Django/APIs |
| Frontend | [.context/agents/frontend-specialist.md](.context/agents/frontend-specialist.md) | Templates/CSS |
| Database | [.context/agents/database-specialist.md](.context/agents/database-specialist.md) | PostgreSQL |
| AI/ML | [.context/agents/ai-specialist.md](.context/agents/ai-specialist.md) | LangChain/RAG |
| Test Writer | [.context/agents/test-writer.md](.context/agents/test-writer.md) | Testes |
| Documentation | [.context/agents/documentation-writer.md](.context/agents/documentation-writer.md) | Documentação |
| Performance | [.context/agents/performance-optimizer.md](.context/agents/performance-optimizer.md) | Otimização |
| Security | [.context/agents/security-auditor.md](.context/agents/security-auditor.md) | Segurança |
| Architect | [.context/agents/architect-specialist.md](.context/agents/architect-specialist.md) | Arquitetura |
| DevOps | [.context/agents/devops-specialist.md](.context/agents/devops-specialist.md) | CI/CD/Docker |

### Skills PREVC

| Skill | Caminho | Fases |
|-------|---------|-------|
| Commit Message | [.context/skills/commit-message/SKILL.md](.context/skills/commit-message/SKILL.md) | E, C |
| PR Review | [.context/skills/pr-review/SKILL.md](.context/skills/pr-review/SKILL.md) | R, V |
| Code Review | [.context/skills/code-review/SKILL.md](.context/skills/code-review/SKILL.md) | R, V |
| Test Generation | [.context/skills/test-generation/SKILL.md](.context/skills/test-generation/SKILL.md) | E, V |
| Documentation | [.context/skills/documentation/SKILL.md](.context/skills/documentation/SKILL.md) | E, C |
| Refactoring | [.context/skills/refactoring/SKILL.md](.context/skills/refactoring/SKILL.md) | E, V |
| Bug Investigation | [.context/skills/bug-investigation/SKILL.md](.context/skills/bug-investigation/SKILL.md) | P, E |
| Feature Breakdown | [.context/skills/feature-breakdown/SKILL.md](.context/skills/feature-breakdown/SKILL.md) | P, R |
| API Design | [.context/skills/api-design/SKILL.md](.context/skills/api-design/SKILL.md) | P, R |
| Security Audit | [.context/skills/security-audit/SKILL.md](.context/skills/security-audit/SKILL.md) | R, V |

### Workflow PREVC

O projeto usa o workflow PREVC para desenvolvimento estruturado:

- **P** (Planning): Requisitos, especificações
- **R** (Review): Validação de arquitetura
- **E** (Execution): Implementação
- **V** (Validation): Testes e code review
- **C** (Confirmation): Documentação e deploy

Status atual: [.context/workflow/status.yaml](.context/workflow/status.yaml)

### Planos de Implementação

Planos ativos: [.context/plans/README.md](.context/plans/README.md)

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
uv run task test-docker        # Testes em Docker (preferido)

# Banco
uv run task makemigrations     # Criar migrações
uv run task migrate            # Aplicar migrações
```

## Padrões de Código

### Type Hints (Obrigatório)

```python
def function(param: str, optional: int | None = None) -> Result[Data, Exception]:
    ...
```

### Result Pattern

```python
from py_return_success_or_error import Success, Failure, Result

def execute() -> Result[Data, Exception]:
    if error:
        return Failure(ValueError("Mensagem"))
    return Success(data)
```

### Multi-Tenancy

```python
# SEMPRE filtrar por tenant
queryset.filter(tenant=request.user.tenant)
```

### Docstrings (Google Style)

```python
def function(param: str) -> str:
    """Descrição breve.

    Args:
        param: Descrição do parâmetro.

    Returns:
        Descrição do retorno.
    """
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

## Configurações de IDE

O projeto inclui configurações para múltiplas ferramentas:

| Ferramenta | Arquivo |
|------------|---------|
| Claude Code | `CLAUDE.md` |
| Cursor | `.cursorrules`, `.cursor/rules/` |
| Gemini | `.gemini/rules.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Antigravity | `.antigravity/context.md` |

## Restrições

1. **NÃO criar testes automatizados** - responsabilidade de agente dedicado
2. **NÃO hardcodar secrets** - usar variáveis de ambiente (.env)
3. **SEMPRE respeitar isolamento de tenant**
4. **SEMPRE usar type hints em funções**
5. **SEMPRE comunicar em Português**

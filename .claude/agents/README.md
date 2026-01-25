# Claude Agents

Este diretório contém referências aos agentes especializados para uso no Claude Code.

## Agentes Disponíveis

Os playbooks completos estão em `.context/agents/`. Abaixo estão os links rápidos:

### Desenvolvimento

| Agente | Descrição |
|--------|-----------|
| [feature-developer](../../.context/agents/feature-developer.md) | Desenvolve novas features |
| [bug-fixer](../../.context/agents/bug-fixer.md) | Investiga e corrige bugs |
| [refactoring-specialist](../../.context/agents/refactoring-specialist.md) | Refatora código |
| [code-reviewer](../../.context/agents/code-reviewer.md) | Revisa código |

### Especialistas

| Agente | Descrição |
|--------|-----------|
| [backend-specialist](../../.context/agents/backend-specialist.md) | Django, APIs |
| [frontend-specialist](../../.context/agents/frontend-specialist.md) | Templates, CSS, JS |
| [database-specialist](../../.context/agents/database-specialist.md) | PostgreSQL, pgvector |
| [ai-specialist](../../.context/agents/ai-specialist.md) | LangChain, RAG |

### Qualidade

| Agente | Descrição |
|--------|-----------|
| [test-writer](../../.context/agents/test-writer.md) | Testes automatizados |
| [documentation-writer](../../.context/agents/documentation-writer.md) | Documentação |
| [performance-optimizer](../../.context/agents/performance-optimizer.md) | Otimização |
| [security-auditor](../../.context/agents/security-auditor.md) | Segurança |

### Arquitetura

| Agente | Descrição |
|--------|-----------|
| [architect-specialist](../../.context/agents/architect-specialist.md) | Decisões arquiteturais |
| [devops-specialist](../../.context/agents/devops-specialist.md) | CI/CD, Docker |

## Como Usar

No Claude Code, referencie o agente relevante ao executar tarefas:

```
Consulte o agente backend-specialist para esta tarefa de API
```

Ou use os slash commands que automaticamente consultam os agentes apropriados:

- `/plan` - Usa feature-breakdown skill
- `/implement` - Usa agentes de especialidade
- `/review` - Usa code-reviewer
- `/fix-bug` - Usa bug-fixer
- `/refactor` - Usa refactoring-specialist

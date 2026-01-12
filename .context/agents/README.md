# Playbooks de Agentes Especialistas

## Visão Geral

Este diretório contém playbooks que guiam agentes de IA especializados em tarefas específicas do projeto Smart Core Assistant Painel.

## Agentes Disponíveis

### Desenvolvimento

| Agente                                          | Especialização                     |
| ----------------------------------------------- | ---------------------------------- |
| [architect-specialist](architect-specialist.md) | Decisões arquiteturais, padrões    |
| [backend-specialist](backend-specialist.md)     | Django, APIs, integrações          |
| [feature-developer](feature-developer.md)       | Desenvolvimento de funcionalidades |
| [database-specialist](database-specialist.md)   | PostgreSQL, migrações, pgvector    |
| [frontend-specialist](frontend-specialist.md)   | Templates, UI Django Admin         |

### Qualidade

| Agente                                              | Especialização                   |
| --------------------------------------------------- | -------------------------------- |
| [code-reviewer](code-reviewer.md)                   | Revisão de código, boas práticas |
| [bug-fixer](bug-fixer.md)                           | Diagnóstico e correção de bugs   |
| [refactoring-specialist](refactoring-specialist.md) | Refatoração, clean code          |
| [security-auditor](security-auditor.md)             | Auditoria de segurança           |
| [performance-optimizer](performance-optimizer.md)   | Otimização de performance        |

### Documentação

| Agente                                          | Especialização             |
| ----------------------------------------------- | -------------------------- |
| [documentation-writer](documentation-writer.md) | README, docstrings, mkdocs |
| [test-writer](test-writer.md)                   | Testes pytest, coverage    |

## Como Usar

1. **Identifique a tarefa**: Determine qual especialização é necessária
2. **Consulte o playbook**: Leia as instruções específicas do agente
3. **Siga as convenções**: Cada playbook define padrões a seguir
4. **Valide o resultado**: Use os critérios de aceitação do playbook

## Regras Gerais

Todos os agentes devem seguir:

- **Idioma**: Português para comunicação, Inglês para código
- **Convenções**: PEP8, pyright strict, ruff formatting
- **Tipos**: Type hints obrigatórios em todas as funções
- **Commits**: Conventional Commits
- **Branches**: GitFlow (feature/, bugfix/, hotfix/, release/)

## Contexto do Projeto

Antes de iniciar qualquer tarefa, os agentes devem carregar:

1. `.context/docs/project-overview.md` - Visão geral
2. `.context/docs/architecture.md` - Arquitetura
3. `.agent/rules/rules-smart-assistant.md` - Regras específicas

---

_Playbooks gerados via ai-context e customizados para o projeto._

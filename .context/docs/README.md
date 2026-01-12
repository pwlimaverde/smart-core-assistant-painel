# Documentação do Contexto - Smart Core Assistant Painel

## Sobre Este Diretório

Este diretório `.context` contém documentação estruturada do projeto, gerada via **ai-context MCP** e enriquecida com análise semântica detalhada.

## Estrutura

```
.context/
├── docs/                   # Documentação técnica
│   ├── project-overview.md # Visão geral do projeto
│   ├── architecture.md     # Arquitetura do sistema
│   ├── data-flow.md        # Fluxo de dados e integrações
│   ├── development-workflow.md # Fluxo de desenvolvimento
│   ├── tooling.md          # Ferramentas e tecnologias
│   ├── security.md         # Práticas de segurança
│   ├── testing-strategy.md # Estratégia de testes
│   └── glossary.md         # Glossário de termos
│
└── agents/                 # Playbooks de agentes IA
    ├── architect-specialist.md
    ├── backend-specialist.md
    ├── feature-developer.md
    ├── database-specialist.md
    └── ...
```

## Documentação Principal

| Documento                                               | Descrição                        |
| ------------------------------------------------------- | -------------------------------- |
| [project-overview.md](docs/project-overview.md)         | Resumo executivo e arquitetura   |
| [architecture.md](docs/architecture.md)                 | Padrões e decisões arquiteturais |
| [data-flow.md](docs/data-flow.md)                       | Integrações e fluxo de dados     |
| [development-workflow.md](docs/development-workflow.md) | Comandos e convenções            |
| [tooling.md](docs/tooling.md)                           | Stack tecnológica                |
| [security.md](docs/security.md)                         | Práticas de segurança            |
| [glossary.md](docs/glossary.md)                         | Termos técnicos                  |

## Playbooks de Agentes

Os playbooks guiam agentes de IA especializados em tarefas específicas do projeto.

## Atualização

Esta documentação foi gerada automaticamente e deve ser atualizada quando:

- Novos módulos são adicionados
- Integrações são modificadas
- Padrões arquiteturais mudam

Para regenerar, use:

```bash
# Via MCP ai-context
mcp_ai-context_initializeContext
```

---

_Última atualização: Janeiro 2026_
_Gerado via ai-context MCP_

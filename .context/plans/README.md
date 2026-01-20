# Planos de Implementação

Este diretório contém planos para coordenar trabalho de documentação, playbooks e implementação de features.

## 📋 Planos Ativos

| Plano                                                             | Status | Descrição                               |
| ----------------------------------------------------------------- | ------ | --------------------------------------- |
| [add-query-compose-playground](./add-query-compose-playground.md) | Ativo  | Adicionar playground para Query Compose |

## 📦 Planos Arquivados

| Plano                                                               | Concluído  | OpenSpec                                                                                                                     |
| ------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------- |
| [refactor-ui-design-system](./archive/refactor-ui-design-system.md) | 20/01/2026 | [changes/archive/2026-01-20-refactor-ui-design-system](../../openspec/changes/archive/2026-01-20-refactor-ui-design-system/) |

## Como Criar ou Atualizar Planos

### Via Workflow (Recomendado)

Use `/openspec-proposal` que automaticamente:

1. Verifica/inicializa scaffolding AI-Context
2. Cria plano via `mcp_ai-context_scaffoldPlan`
3. Solicita aprovação antes de criar proposta OpenSpec

### Via CLI

- `ai-context plan <name>` - cria template de novo plano
- `ai-context plan <name> --fill` - atualiza plano com contexto do repositório

## Como Arquivar Planos

Use `/openspec-archive` que automaticamente:

1. Move o plano para `archive/`
2. Atualiza este índice
3. Preserva links entre artefatos AI-Context e OpenSpec

## Estrutura de Diretórios

```
.context/plans/
├── README.md              # Este arquivo
├── plano-ativo.md         # Planos em andamento
└── archive/               # Planos concluídos
    └── plano-concluido.md
```

## Recursos Relacionados

- [Agent Handbook](../agents/README.md)
- [Documentation Index](../docs/README.md)
- [Agent Knowledge Base](../../AGENTS.md)
- [Contributor Guidelines](../../CONTRIBUTING.md)

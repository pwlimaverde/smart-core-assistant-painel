---
source_tool: antigravity
source_path: .agent\workflows\README.md
imported_at: 2026-05-14T18:16:27.555Z
ai_context_version: 0.9.2
---
# Antigravity Workflows

Este diretório contém workflows ativos para o Antigravity IDE, sincronizados com o sistema ai-context via MCP.

## Estrutura

```
.agent/
├── rules/                    # Regras passivas (constraints)
│   └── rules-smart-assistant.md
└── workflows/                # Workflows ativos (procedimentos)
    ├── README.md             # Este arquivo
    ├── prevc-planning.md     # Fase P do PREVC
    ├── prevc-review.md       # Fase R do PREVC
    ├── prevc-execution.md    # Fase E do PREVC
    ├── prevc-validation.md   # Fase V do PREVC
    └── prevc-confirmation.md # Fase C do PREVC
```

## Workflows PREVC

| Workflow | Fase | Skills Associados |
|----------|------|-------------------|
| [prevc-planning](prevc-planning.md) | P | feature-breakdown, api-design |
| [prevc-review](prevc-review.md) | R | code-review, security-audit |
| [prevc-execution](prevc-execution.md) | E | commit-message, refactoring |
| [prevc-validation](prevc-validation.md) | V | test-generation, pr-review |
| [prevc-confirmation](prevc-confirmation.md) | C | prevc-final-review, documentation, commit-message |
| [prevc-final-review](../prevc-final-review/prevc-final-review.md) | C (gate) | code-review, security-audit — auditoria final via subagente Opus antes de arquivar |

## Sincronização via MCP ai-context

Este diretório é sincronizado pelo MCP ai-context. Para atualizar:

```bash
# Sincronizar workflows
npx @ai-coders/context quick-sync --components workflows

# Exportar para Antigravity
npx @ai-coders/context export-rules --target antigravity
```

## Referências

- [Skills PREVC](../../.context/skills/README.md)
- [Workflow Status](../../.context/workflow/status.yaml)
- [Documentação](../../.context/docs/README.md)

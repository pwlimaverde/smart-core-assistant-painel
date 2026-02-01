# Sincronização de Contexto AI

Este arquivo documenta a sincronização do contexto ai-context com diferentes ferramentas de IA.

## Ferramentas Configuradas

| Ferramenta | Arquivo de Configuração | Status |
|------------|-------------------------|--------|
| Claude Code | `CLAUDE.md`, `.claude/commands/`, `.claude/mcp.json` | ✅ Configurado |
| Cursor IDE | `.cursorrules`, `.cursor/rules/project.md` | ✅ Configurado |
| Gemini | `.gemini/rules.md` | ✅ Configurado |
| GitHub Copilot | `.github/copilot-instructions.md` | ✅ Configurado |
| Antigravity IDE | `.agent/rules/`, `.agent/workflows/` | ✅ Configurado |

## Estrutura de Contexto

```
.context/
├── docs/                    # Documentação técnica
│   ├── README.md
│   ├── project-overview.md
│   ├── architecture.md
│   ├── data-flow.md
│   ├── development-workflow.md
│   ├── testing-strategy.md
│   ├── glossary.md
│   ├── security.md
│   ├── tooling.md
│   └── codebase-map.json
│
├── agents/                  # Playbooks de agentes
│   ├── README.md
│   ├── feature-developer.md
│   ├── bug-fixer.md
│   ├── code-reviewer.md
│   ├── refactoring-specialist.md
│   ├── backend-specialist.md
│   ├── frontend-specialist.md
│   ├── database-specialist.md
│   ├── ai-specialist.md
│   ├── test-writer.md
│   ├── documentation-writer.md
│   ├── performance-optimizer.md
│   ├── security-auditor.md
│   ├── architect-specialist.md
│   └── devops-specialist.md
│
├── skills/                  # Skills PREVC
│   ├── README.md
│   ├── commit-message/SKILL.md
│   ├── pr-review/SKILL.md
│   ├── code-review/SKILL.md
│   ├── test-generation/SKILL.md
│   ├── documentation/SKILL.md
│   ├── refactoring/SKILL.md
│   ├── bug-investigation/SKILL.md
│   ├── feature-breakdown/SKILL.md
│   ├── api-design/SKILL.md
│   └── security-audit/SKILL.md
│
├── workflow/                # Workflow PREVC
│   ├── README.md
│   ├── status.yaml
│   └── docs/
│       ├── prd-template.md
│       └── technical-spec-template.md
│
├── plans/                   # Planos de implementação
│   ├── README.md
│   └── archive/
│
└── SYNC.md                  # Este arquivo
```

## Comandos de Sincronização

### Sincronização Automática (ai-coders/context)

```bash
# Sincronizar tudo
npx @ai-coders/context quick-sync

# Sincronizar apenas agentes
npx @ai-coders/context quick-sync --components agents

# Sincronizar para ferramentas específicas
npx @ai-coders/context quick-sync --targets claude,cursor

# Exportar regras
npx @ai-coders/context export-rules --preset all

# Sincronizar agentes
npx @ai-coders/context sync-agents --preset all
```

### Sincronização Manual

Se o CLI não estiver disponível, copie manualmente o conteúdo relevante para:

1. **Claude Code**: `CLAUDE.md`, `.claude/commands/`, `.claude/mcp.json`
2. **Cursor**: `.cursorrules` e `.cursor/rules/`
3. **Gemini**: `.gemini/rules.md`
4. **GitHub Copilot**: `.github/copilot-instructions.md`
5. **Antigravity**: `.agent/rules/`, `.agent/workflows/`

## Atualização de Contexto

Ao atualizar documentação em `.context/`:

1. Atualize o arquivo de origem em `.context/docs/` ou `.context/agents/`
2. Execute sincronização para propagar mudanças
3. Verifique se arquivos de destino foram atualizados

## Workflow PREVC

O status do workflow é mantido em `.context/workflow/status.yaml`:

```yaml
phases:
  P: # Planning
    status: pending|in_progress|completed
  R: # Review
    status: pending|in_progress|completed
  E: # Execution
    status: pending|in_progress|completed
  V: # Validation
    status: pending|in_progress|completed
  C: # Confirmation
    status: pending|in_progress|completed
```

## Estrutura do Antigravity IDE

```
.agent/
├── rules/                      # Regras passivas (constraints)
│   └── rules-smart-assistant.md
└── workflows/                  # Workflows ativos (procedimentos PREVC)
    ├── README.md
    ├── prevc-planning.md       # Fase P do PREVC
    ├── prevc-review.md         # Fase R do PREVC
    ├── prevc-execution.md      # Fase E do PREVC
    ├── prevc-validation.md     # Fase V do PREVC
    └── prevc-confirmation.md   # Fase C do PREVC
```

## Estrutura do Claude Code

```
.claude/
├── mcp.json                    # Configuração de MCP servers
├── settings.local.json         # Configurações locais
├── agents/
│   └── README.md               # Referência para agentes
└── commands/                   # Slash commands
    ├── plan.md
    ├── implement.md
    ├── review.md
    ├── fix-bug.md
    ├── refactor.md
    ├── commit.md
    ├── test.md
    ├── docs.md
    ├── security.md
    ├── status.md
    └── context.md
```

## Verificação de Integridade

Para verificar se todos os arquivos estão sincronizados:

```bash
# Listar todos os arquivos de contexto
find .context -type f -name "*.md" -o -name "*.yaml" -o -name "*.json" | sort

# Verificar configurações de IDE
ls -la .cursorrules .gemini/ .github/copilot-instructions.md .agent/ .claude/ 2>/dev/null
```

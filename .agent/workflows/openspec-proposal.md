---
description: Cria plano AI-Context e proposta OpenSpec com validação em duas etapas.
---

<!-- OPENSPEC:START -->

**Regras**

- Implementações simples primeiro; complexidade apenas quando solicitada.
- Mudanças restritas ao escopo solicitado.
- Consulte `openspec/AGENTS.md` para convenções OpenSpec.
- Esclareça ambiguidades ANTES de editar arquivos.
- NÃO escreva código nesta fase. Apenas documentos de design.
- **IDIOMA**: Toda documentação em **PORTUGUÊS**.

---

# FASE 1: Contexto e Plano (AI-Context)

**Objetivo**: Carregar contexto existente e criar plano ANTES dos artefatos OpenSpec.

> 📖 **Ref**: `docs_dev/planejamento/fluxo_planejamento_ai_context.md`

## 1.1: Verificar Status

```javascript
mcp_ai - context_workflow - status();
```

- Se não existir workflow, prossiga para 1.3
- **NÃO execute `workflow-init` se já existir workflow ativo**

## 1.2: Orquestrar Agentes

```javascript
mcp_ai -
  context_agent({
    action: "orchestrate",
    task: "<descrição da funcionalidade>",
    phase: "P"
  });
```

**⚠️ Use `orchestrate`, NÃO use `discover`**

## 1.3: Carregar Contexto Focado

```javascript
mcp_ai - context_context({ action: "getMap", section: "architecture" });
```

| Seção          | Quando Usar   |
| -------------- | ------------- |
| `architecture` | Sempre        |
| `publicAPI`    | Integrações   |
| `structure`    | Novos módulos |
| `symbols`      | Refatoração   |

**⚠️ NÃO use `buildSemanticContext` - consome muitos tokens**

## 1.4: Iniciar Workflow (Se Necessário)

**Apenas se não existir workflow ativo:**

```javascript
mcp_ai -
  context_workflow -
  init({
    name: "<nome da feature>",
    scale: "MEDIUM" // QUICK, SMALL, MEDIUM, LARGE
  });
```

## 1.5: Criar Plano

1. Defina `change-id` (ex: `add-reports-module`, `fix-auth-bug`)

2. Execute:

```javascript
mcp_ai -
  context_context({
    action: "scaffoldPlan",
    planName: "<change-id>",
    summary: "<resumo>",
    autoFill: true
  });
```

3. Preencha `.context/plans/<change-id>.md`:

```markdown
# <Título>

> 📋 **Status**: Aguardando Aprovação

## Objetivo

[O que será alcançado]

## Escopo

### Incluído

- [Item 1]

### Não Incluído

- [Item fora do escopo]

## Arquitetura Proposta

[Solução técnica]

## Riscos

| Risco | Impacto | Mitigação |
| ----- | ------- | --------- |
| [R1]  | Alto    | [Ação]    |

## Tarefas

- [ ] Task 1
- [ ] Task 2
```

## 1.6: Vincular Plano

```javascript
mcp_ai - context_plan({ action: "link", planSlug: "<change-id>" });
```

## 1.7: 🛑 PARADA OBRIGATÓRIA

1. Apresente resumo do plano
2. Aguarde aprovação explícita antes da Fase 2
3. Se ajustes, atualize e peça nova aprovação

---

# FASE 2: Proposta OpenSpec

**Pré-requisito**: Plano aprovado na Fase 1.

## 2.1: Criar Estrutura

```
openspec/changes/<change-id>/
├── proposal.md
├── tasks.md
└── specs/<capability>/spec.md
```

## 2.2: Gerar `proposal.md`

```markdown
# <Título>

> 📋 **Plano**: [<change-id>.md](../../../.context/plans/<change-id>.md)
> 📅 **Data**: <data>
> 🏷️ **Status**: Em Revisão

## Objetivo

[Do plano]

## Escopo

[Do plano]

## Decisões de Design

[Decisões técnicas]

## Critérios de Aceite

- [ ] Critério 1
```

## 2.3: Gerar `tasks.md`

```markdown
# Tasks

> 📋 **Plano**: [<change-id>.md](../../../.context/plans/<change-id>.md)

## Checklist

- [ ] **Task 1**: [Descrição]
  - Arquivos: `path/file.py`
  - Critério: [Verificação]
```

## 2.4: Criar Specs

```markdown
## ADDED Requirements

### Requirement: <nome>

[Descrição]

#### Scenario: <cenário>

- **Given**: [Pré-condição]
- **When**: [Ação]
- **Then**: [Resultado]
```

## 2.5: Validar

```bash
openspec validate <change-id> --strict
```

## 2.6: Avançar Workflow

```javascript
mcp_ai -
  context_workflow -
  advance({
    outputs: ["openspec/changes/<change-id>/proposal.md"]
  });
```

## 2.7: 🛑 PARADA OBRIGATÓRIA

1. Apresente resumo da proposta
2. Aguarde aprovação antes de `/openspec-apply`

---

# Anti-Padrões

| ❌ Evitar                 | ✅ Preferir       |
| ------------------------- | ----------------- |
| `buildSemanticContext`    | `getMap` focado   |
| `discover` agentes        | `orchestrate`     |
| `workflow-init` duplicado | `workflow-status` |
| `context init` repetido   | `context check`   |

---

**Referências**

- `openspec show <id> --json --deltas-only`
- `rg -n "Requirement:" openspec/specs`
- `docs_dev/planejamento/fluxo_planejamento_ai_context.md`

<!-- OPENSPEC:END -->

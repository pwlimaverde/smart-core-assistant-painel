# Guia de Configuração: Fluxo Integrado OpenSpec + AI-Context

> **Objetivo**: Configurar qualquer projeto para utilizar o fluxo integrado de
> planejamento, execução e arquivamento usando OpenSpec e AI-Context MCP.

## Pré-requisitos

Antes de aplicar este guia, o projeto deve ter:

1. ✅ **OpenSpec inicializado**: pasta `openspec/` com estrutura básica
2. ✅ **AI-Context inicializado**: pasta `.context/` com `docs/`, `agents/`, `plans/`
3. ✅ **Pasta de workflows**: `.agent/workflows/` criada

Para inicializar (se ainda não feito):

```bash
# OpenSpec
npx openspec init

# AI-Context (via MCP)
mcp_ai-context_context({ action: "init", type: "both", semantic: true })
```

---

## Visão Geral do Fluxo

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  /openspec-      │────▶│  /openspec-      │────▶│  /openspec-      │
│  proposal        │     │  apply           │     │  archive         │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ • Orquestra      │     │ • Executa tasks  │     │ • Finaliza       │
│   agentes        │     │ • Valida código  │     │   AI-Context     │
│ • Carrega        │     │ • Avança fases   │     │ • Arquiva        │
│   contexto       │     │   E → V → C      │     │   OpenSpec       │
│ • Cria plano     │     │                  │     │ • Move planos    │
│ • Cria proposta  │     │                  │     │   para archive/  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
     Fase P → R               Fase R → C              Finalização
```

---

## Estrutura de Diretórios Esperada

```
projeto/
├── .agent/
│   └── workflows/
│       ├── openspec-proposal.md    ← Workflow de planejamento
│       ├── openspec-apply.md       ← Workflow de execução
│       └── openspec-archive.md     ← Workflow de arquivamento
├── .context/
│   ├── agents/                     ← Playbooks de agentes
│   ├── docs/                       ← Documentação do projeto
│   ├── plans/                      ← Planos ativos
│   │   └── archive/                ← Planos arquivados
│   └── workflow/                   ← Estado do workflow PREVC
└── openspec/
    ├── changes/                    ← Propostas ativas
    │   └── archive/                ← Propostas arquivadas
    └── specs/                      ← Especificações
```

---

## Comandos MCP Essenciais

### Consultas (Leitura - Baixo Custo de Tokens)

| Comando                                           | Uso                              |
| ------------------------------------------------- | -------------------------------- |
| `workflow-status()`                               | Verificar fase atual do workflow |
| `context({ action: "check" })`                    | Verificar se scaffolding existe  |
| `context({ action: "getMap", section: "..." })`   | Carregar contexto focado         |
| `agent({ action: "orchestrate", task: "..." })`   | Selecionar agentes para task     |
| `plan({ action: "getDetails", planSlug: "..." })` | Detalhes de um plano             |

### Ações (Escrita)

| Comando                                                      | Uso                        |
| ------------------------------------------------------------ | -------------------------- |
| `workflow-init({ name, scale })`                             | Iniciar workflow PREVC     |
| `workflow-advance({ outputs })`                              | Avançar para próxima fase  |
| `context({ action: "scaffoldPlan", planName, autoFill })`    | Criar plano                |
| `plan({ action: "link", planSlug })`                         | Vincular plano ao workflow |
| `plan({ action: "updatePhase", planSlug, phaseId, status })` | Atualizar fase             |
| `plan({ action: "syncMarkdown", planSlug })`                 | Sincronizar status         |

### Anti-Padrões a Evitar

| ❌ Evitar                              | ✅ Preferir                        |
| -------------------------------------- | ---------------------------------- |
| `buildSemanticContext` frequente       | `getMap` com seção específica      |
| `agent({ action: "discover" })`        | `agent({ action: "orchestrate" })` |
| `workflow-init` duplicado              | `workflow-status` primeiro         |
| `context({ action: "init" })` repetido | `context({ action: "check" })`     |

---

## Seções do getMap

| Seção               | Conteúdo                | Quando Usar            |
| ------------------- | ----------------------- | ---------------------- |
| `all`               | Tudo                    | Raramente (alto custo) |
| `architecture`      | Padrões arquiteturais   | Sempre no planejamento |
| `structure`         | Estrutura de diretórios | Novos módulos          |
| `symbols`           | Classes e funções       | Refatoração            |
| `symbols.classes`   | Apenas classes          | Foco em OOP            |
| `symbols.functions` | Apenas funções          | Foco em funções        |
| `publicAPI`         | APIs expostas           | Integrações            |
| `stack`             | Tecnologias usadas      | Decisões de tech       |
| `dependencies`      | Dependências            | Atualizações           |

---

## Agentes Disponíveis

| Tipo                     | Descrição                       | Doc Principal |
| ------------------------ | ------------------------------- | ------------- |
| `code-reviewer`          | Revisa qualidade e estilo       | Architecture  |
| `bug-fixer`              | Identifica e corrige bugs       | Architecture  |
| `feature-developer`      | Implementa novas features       | Architecture  |
| `refactoring-specialist` | Melhora estrutura do código     | Architecture  |
| `test-writer`            | Cria suítes de teste            | Testing       |
| `documentation-writer`   | Mantém documentação             | Documentation |
| `performance-optimizer`  | Otimiza performance             | Architecture  |
| `security-auditor`       | Audita vulnerabilidades         | Security      |
| `backend-specialist`     | Desenvolve APIs e lógica server | Architecture  |
| `frontend-specialist`    | Constrói interfaces             | Architecture  |
| `architect-specialist`   | Design de arquitetura           | Architecture  |
| `devops-specialist`      | CI/CD e deploy                  | Deployment    |
| `database-specialist`    | Otimiza banco de dados          | Architecture  |
| `mobile-specialist`      | Desenvolve apps mobile          | Architecture  |

---

## Escalas do Workflow PREVC

| Escala   | Fases             | Quando Usar                   |
| -------- | ----------------- | ----------------------------- |
| `QUICK`  | E → V             | Correções simples, typos      |
| `SMALL`  | P → E → V         | Features pequenas sem revisão |
| `MEDIUM` | P → R → E → V     | Features regulares            |
| `LARGE`  | P → R → E → V → C | Features complexas, segurança |

---

## Templates dos Workflows

### Instruções para a IA

Ao configurar um novo projeto, a IA deve:

1. **Criar a pasta** `.agent/workflows/` se não existir
2. **Criar os 3 arquivos** de workflow conforme templates abaixo
3. **Ajustar comandos de validação** conforme stack do projeto
4. **Criar pasta** `.context/plans/archive/` para planos arquivados

---

### Template: openspec-proposal.md

````markdown
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

## 1.1: Verificar Status

```javascript
mcp_ai - context_workflow - status();
```
````

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

## 1.3: Carregar Contexto Focado

```javascript
mcp_ai - context_context({ action: "getMap", section: "architecture" });
```

**⚠️ NÃO use `buildSemanticContext` - consome muitos tokens**

## 1.4: Iniciar Workflow (Se Necessário)

```javascript
mcp_ai -
  context_workflow -
  init({
    name: "<nome da feature>",
    scale: "MEDIUM"
  });
```

## 1.5: Criar Plano

```javascript
mcp_ai -
  context_context({
    action: "scaffoldPlan",
    planName: "<change-id>",
    summary: "<resumo>",
    autoFill: true
  });
```

## 1.6: Vincular Plano

```javascript
mcp_ai - context_plan({ action: "link", planSlug: "<change-id>" });
```

## 1.7: 🛑 PARADA OBRIGATÓRIA

Aguarde aprovação antes da Fase 2.

---

# FASE 2: Proposta OpenSpec

## 2.1: Criar Estrutura

Diretório: `openspec/changes/<change-id>/`

## 2.2-2.4: Gerar proposal.md, tasks.md, specs

[Conteúdo conforme padrão OpenSpec]

## 2.5: Validar

```bash
openspec validate <change-id> --strict
```

## 2.6: Avançar Workflow

```javascript
mcp_ai-context_workflow-advance({ outputs: [...] })
```

## 2.7: 🛑 PARADA OBRIGATÓRIA

Aguarde aprovação antes de `/openspec-apply`

<!-- OPENSPEC:END -->

````

---

### Template: openspec-apply.md

```markdown
---
description: Implementa mudança aprovada consultando plano e documentação AI-Context.
---

<!-- OPENSPEC:START -->

**Regras**

- Implementações simples primeiro.
- Mudanças restritas ao escopo da proposta.
- NÃO implemente além do escopo.
- **IDIOMA**: Comunicações em **PORTUGUÊS**.

---

# FASE 1: Preparação

## 1.1: Verificar Status

```javascript
mcp_ai-context_workflow-status()
````

## 1.2: Carregar Contexto Focado

```javascript
mcp_ai - context_context({ action: "getMap", section: "architecture" });
```

## 1.3: Carregar Documentos

1. `.context/plans/<change-id>.md`
2. `openspec/changes/<change-id>/tasks.md`

---

# FASE 2: Execução

## 2.1: Avançar R → E

```javascript
mcp_ai - context_workflow - advance({ outputs: [] });
```

## 2.2: Implementar Tasks

Para cada task: ler → implementar → verificar → atualizar tasks.md

---

# FASE 3: Validação

## 3.1: Avançar E → V

```javascript
mcp_ai-context_workflow-advance({ outputs: [...] })
```

## 3.2: Executar Verificações

// turbo

```bash
# Ajuste conforme stack do projeto:
# Python: uv run task lint && uv run task type-check
# Node: npm run lint && npm run type-check
# Go: go vet ./... && golangci-lint run
```

---

# FASE 4: Conclusão

## 4.1: Avançar V → C

```javascript
mcp_ai-context_workflow-advance({ outputs: [...] })
```

## 4.2: 🛑 PARADA

Aguarde confirmação para `/openspec-archive`

<!-- OPENSPEC:END -->

````

---

### Template: openspec-archive.md

```markdown
---
description: Arquiva mudança concluída e move plano para histórico.
---

<!-- OPENSPEC:START -->

**Regras**

- Finalize AMBOS os fluxos: AI-Context e OpenSpec.
- Mova planos para `.context/plans/archive/`.
- **IDIOMA**: Comunicações em **PORTUGUÊS**.

---

# FASE 1: Validação

## 1.1: Identificar Change ID

```bash
openspec list
````

## 1.2: Verificar Workflow

```javascript
mcp_ai - context_workflow - status();
```

---

# FASE 2: Finalizar AI-Context

## 2.1: Sincronizar Status

```javascript
mcp_ai - context_plan({ action: "syncMarkdown", planSlug: "<change-id>" });
```

## 2.2: Marcar Completo

```javascript
mcp_ai -
  context_plan({
    action: "updatePhase",
    planSlug: "<change-id>",
    phaseId: "C",
    status: "completed"
  });
```

---

# FASE 3: Arquivar OpenSpec

// turbo

```bash
openspec archive <change-id> --yes
```

---

# FASE 4: Mover Plano

Mover: `.context/plans/<change-id>.md` → `.context/plans/archive/<change-id>.md`

Atualizar referências em:

- Plano arquivado (status + link OpenSpec)
- `proposal.md` arquivado (link do plano)
- `.context/plans/README.md` (índice)

---

# FASE 5: Conclusão

Confirmar:

- ✅ OpenSpec em `openspec/changes/archive/<change-id>/`
- ✅ Plano em `.context/plans/archive/<change-id>.md`
- ✅ Referências atualizadas

<!-- OPENSPEC:END -->

```

---

## Checklist de Configuração

Ao configurar um novo projeto:

- [ ] Inicializar OpenSpec (`npx openspec init`)
- [ ] Inicializar AI-Context (`context({ action: "init" })`)
- [ ] Criar `.agent/workflows/`
- [ ] Criar `openspec-proposal.md` (template acima)
- [ ] Criar `openspec-apply.md` (template acima)
- [ ] Criar `openspec-archive.md` (template acima)
- [ ] Criar `.context/plans/archive/`
- [ ] Ajustar comandos de validação para stack do projeto
- [ ] Criar `.context/plans/README.md` (índice de planos)

---

## Prompt para Solicitar Configuração

Use este prompt para instruir a IA a configurar um novo projeto:

```

Configure este projeto para usar o fluxo integrado OpenSpec + AI-Context.

Siga a documentação em docs_dev/planejamento/instrucoes_desenvolvimento/
configuracao_fluxo_integrado.md

Ajuste os comandos de validação para a stack deste projeto:

- Linguagem: [Python/Node/Go/etc]
- Gerenciador de pacotes: [uv/npm/pnpm/etc]
- Comandos de lint: [especificar]
- Comandos de type-check: [especificar]

```

---

*Documento criado em: 2026-01-22*
*Baseado no projeto: smart-core-assistant-painel*
```

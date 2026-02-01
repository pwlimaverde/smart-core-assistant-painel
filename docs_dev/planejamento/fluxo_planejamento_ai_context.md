# Fluxo de Planejamento com AI-Context MCP

> **Objetivo**: Definir o processo otimizado para planejamento de novas funcionalidades
> utilizando o MCP `ai-context`, maximizando contexto e minimizando consumo de tokens.

## Pré-requisitos

O scaffolding `.context/` **já deve existir** com as pastas:

- `.context/docs/` - Documentação do projeto
- `.context/agents/` - Playbooks dos agentes especializados
- `.context/plans/` - Planos de implementação

Para verificar: `mcp_ai-context_context({ action: "check" })`

---

## Fluxo Otimizado em 4 Etapas

### Etapa 1: Verificar Status do Workflow

**Objetivo**: Confirmar estado atual sem gastar tokens lendo arquivos.

**Ação MCP**:

```javascript
mcp_ai - context_workflow - status();
```

**Retorno esperado**:

- Fase atual (P/R/E/V/C)
- Planos já vinculados
- Gates ativos

**Quando pular**: Se você sabe que não há workflow ativo.

---

### Etapa 2: Orquestrar Agentes para a Tarefa

**Objetivo**: Selecionar apenas os especialistas relevantes para a task.

**Ação MCP**:

```javascript
mcp_ai -
  context_agent({
    action: "orchestrate",
    task: "Descrição detalhada da funcionalidade",
    phase: "P" // Planning
  });
```

**Retorno esperado**:

- Lista de agentes recomendados (ex: `backend-specialist`, `architect-specialist`)
- Justificativa para cada seleção

**Dica**: Não use `discover` (lista todos). Use `orchestrate` com a task específica.

---

### Etapa 3: Carregar Contexto Focado

**Objetivo**: Trazer para memória apenas informações arquiteturais relevantes.

**Ações MCP** (escolha conforme necessidade):

| Seção       | Quando Usar   | Comando                               |
| ----------- | ------------- | ------------------------------------- |
| Arquitetura | Sempre        | `getMap({ section: "architecture" })` |
| API Pública | Integrações   | `getMap({ section: "publicAPI" })`    |
| Estrutura   | Novos módulos | `getMap({ section: "structure" })`    |
| Símbolos    | Refatoração   | `getMap({ section: "symbols" })`      |
| Stack       | Decisões tech | `getMap({ section: "stack" })`        |

**Exemplo**:

```javascript
mcp_ai -
  context_context({
    action: "getMap",
    section: "architecture"
  });
```

**Importante**: NÃO use `buildSemantic` a menos que o contexto esteja desatualizado.
Isso reconstrói tudo e consome muitos tokens.

---

### Etapa 4: Criar o Plano

**Objetivo**: Gerar o arquivo de plano usando contexto existente.

**Ação MCP**:

```javascript
mcp_ai -
  context_context({
    action: "scaffoldPlan",
    planName: "nome-da-feature", // Formato: verbo-substantivo (ex: add-reports-module)
    title: "Título Descritivo do Plano",
    summary: "Resumo do objetivo e escopo da mudança",
    autoFill: true // Usa contexto existente para preencher seções
  });
```

**Resultado**: Arquivo criado em `.context/plans/<nome-da-feature>.md`

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

## Comandos de Referência Rápida

### Consultas (Leitura)

```javascript
// Status do workflow
mcp_ai - context_workflow - status();

// Verificar scaffolding
mcp_ai - context_context({ action: "check" });

// Mapa do código (seções: all, stack, structure, architecture, symbols, publicAPI)
mcp_ai - context_context({ action: "getMap", section: "architecture" });

// Detalhes de um plano
mcp_ai - context_plan({ action: "getDetails", planSlug: "nome-do-plano" });

// Documentação de um agente
mcp_ai - context_agent({ action: "getDocs", agent: "feature-developer" });
```

### Ações (Escrita)

```javascript
// Criar plano
mcp_ai -
  context_context({
    action: "scaffoldPlan",
    planName: "nome",
    summary: "...",
    autoFill: true
  });

// Vincular plano ao workflow
mcp_ai - context_plan({ action: "link", planSlug: "nome-do-plano" });

// Iniciar workflow (apenas se não existir)
mcp_ai -
  context_workflow -
  init({
    name: "Nome da Feature",
    scale: "MEDIUM" // QUICK, SMALL, MEDIUM, LARGE
  });

// Avançar fase
mcp_ai - context_workflow - advance({ outputs: ["path/to/artifact"] });
```

---

## Anti-Padrões a Evitar

| ❌ Evitar                                 | ✅ Preferir                              |
| ----------------------------------------- | ---------------------------------------- |
| `buildSemanticContext` em toda task       | `getMap` com seção específica            |
| `agent({ action: "discover" })`           | `agent({ action: "orchestrate", task })` |
| `workflow-init` quando já existe workflow | `workflow-status` para verificar         |
| Ler playbooks completos dos agentes       | `getDocs` para agente específico         |

---

## Prompt Template para Solicitar Planejamento

```
Orquestre os agentes para a tarefa "[DESCRIÇÃO DA FEATURE]".
Consulte o mapa de arquitetura existente e crie o plano "[nome-da-feature]"
aproveitando o contexto já carregado, sem reconstruí-lo.
```

---

_Documento criado em: 2026-01-22_
_Última atualização: 2026-01-22_

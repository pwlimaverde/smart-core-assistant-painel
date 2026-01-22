---
description: Implementa mudança aprovada consultando plano e documentação AI-Context.
---

<!-- OPENSPEC:START -->

**Regras**

- Implementações simples primeiro; complexidade apenas quando necessária.
- Mudanças restritas ao escopo da proposta aprovada.
- NÃO implemente além do escopo; documente trabalho adicional para futuras tasks.
- **IDIOMA**: Comunicações e atualizações em **PORTUGUÊS**.

---

**Pré-requisitos**

1. ✅ Proposta aprovada em `openspec/changes/<change-id>/`
2. ✅ Plano em `.context/plans/<change-id>.md`
3. ✅ Workflow em fase "R" (Review)

Se não atendido, execute `/openspec-proposal` primeiro.

---

# FASE 1: Preparação

## 1.1: Verificar Status do Workflow

```javascript
mcp_ai - context_workflow - status();
```

- Confirme fase "R" (Review) ativa
- Verifique planos vinculados

## 1.2: Carregar Contexto Focado

**⚠️ NÃO use `buildSemanticContext` - use consultas focadas:**

```javascript
mcp_ai - context_context({ action: "getMap", section: "architecture" });
```

Seções conforme necessidade:
| Seção | Quando |
|-------|--------|
| `architecture` | Sempre |
| `symbols` | Refatoração |
| `publicAPI` | Integrações |

## 1.3: Carregar Documentos da Proposta

Leia na ordem:

1. `.context/plans/<change-id>.md` - plano aprovado
2. `openspec/changes/<change-id>/tasks.md` - lista de tasks
3. `openspec/changes/<change-id>/design.md` - decisões (se existir)

## 1.4: Consultar Agente Especialista (Se Necessário)

```javascript
mcp_ai -
  context_agent({
    action: "getDocs",
    agent: "<tipo>" // backend-specialist, frontend-specialist, etc.
  });
```

---

# FASE 2: Execução

## 2.1: Avançar para Fase de Execução

```javascript
mcp_ai -
  context_workflow -
  advance({
    outputs: []
  });
```

Confirme transição R → E.

## 2.2: Implementar Tasks

Para cada task em `tasks.md`:

1. **Ler** descrição e critérios de aceite
2. **Consultar** `design.md` para decisões relevantes
3. **Implementar** com edits mínimos e focados
4. **Verificar** critério atendido
5. **Atualizar** `tasks.md`:

```markdown
- [x] **Task 1**: Criar modelo de dados
  - Arquivos: `src/models/report.py`
  - ✅ Concluído
```

## 2.3: Manter Foco no Escopo

- ❌ NÃO implemente além do escopo
- ❌ NÃO refatore código não relacionado
- ✅ Documente trabalho adicional descoberto

## 2.4: Registrar Progresso (Opcional)

```javascript
mcp_ai -
  context_plan({
    action: "updateStep",
    planSlug: "<change-id>",
    phaseId: "E",
    stepIndex: 1,
    status: "completed",
    notes: "Modelo criado"
  });
```

---

# FASE 3: Validação

## 3.1: Avançar para Fase de Validação

Após TODAS as tasks concluídas:

```javascript
mcp_ai -
  context_workflow -
  advance({
    outputs: ["<arquivos modificados>"]
  });
```

Transição E → V.

## 3.2: Executar Verificações

// turbo

```bash
uv run task format
```

// turbo

```bash
uv run task lint
```

// turbo

```bash
uv run task type-check
```

## 3.3: Validar Implementação

1. ✅ Todos os tasks em `tasks.md` marcados `[x]`
2. ✅ Critérios de aceite da proposta atendidos
3. ✅ Lint e type-check passando

## 3.4: Corrigir Problemas (Se Houver)

Se encontrar erros:

1. Corrija imediatamente
2. Atualize tasks se necessário
3. Re-execute verificações

---

# FASE 4: Conclusão

## 4.1: Avançar para Fase Completa

```javascript
mcp_ai -
  context_workflow -
  advance({
    outputs: ["openspec/changes/<change-id>/tasks.md"]
  });
```

Transição V → C.

## 4.2: Atualizar Status da Proposta

Em `openspec/changes/<change-id>/proposal.md`:

- Mude status para "✅ Implementado"

## 4.3: 🛑 PARADA

1. Apresente resumo da implementação
2. Liste arquivos modificados
3. Aguarde confirmação para `/openspec-archive`

---

**Referências**

- `openspec show <id> --json --deltas-only`
- `.context/agents/` - playbooks de especialistas
- `docs_dev/planejamento/fluxo_planejamento_ai_context.md`

<!-- OPENSPEC:END -->

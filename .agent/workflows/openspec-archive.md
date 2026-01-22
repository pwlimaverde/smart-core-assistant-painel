---
description: Arquiva mudança concluída e move plano para histórico com links preservados.
---

<!-- OPENSPEC:START -->

**Regras**

- Finalize AMBOS os fluxos: AI-Context e OpenSpec.
- Atualize referências para apontar para diretórios de arquivo.
- Mova planos para `.context/plans/archive/`.
- **IDIOMA**: Comunicações em **PORTUGUÊS**.

---

**Pré-requisitos**

1. ✅ Implementação concluída via `/openspec-apply`
2. ✅ Todas as tasks marcadas `[x]` em `tasks.md`
3. ✅ Verificações de qualidade passando

---

# FASE 1: Identificação e Validação

## 1.1: Identificar Change ID

Se não informado:

```bash
openspec list
```

**NÃO prossiga sem change ID confirmado.**

## 1.2: Validar Estado

1. Verifique estado da mudança:

```bash
openspec show <change-id>
```

2. Confirme tasks concluídas em `openspec/changes/<change-id>/tasks.md`

3. Verifique plano existe em `.context/plans/<change-id>.md`

## 1.3: Verificar Workflow AI-Context

```javascript
mcp_ai - context_workflow - status();
```

- Confirme fase "V" (Validation) ou "C" (Complete)
- Se estiver em fase anterior, complete via `/openspec-apply`

---

# FASE 2: Finalizar AI-Context

## 2.1: Avançar para Fase Completa

Se workflow ainda não está em "C":

```javascript
mcp_ai -
  context_workflow -
  advance({
    outputs: [
      "openspec/changes/<change-id>/tasks.md",
      ".context/plans/<change-id>.md"
    ]
  });
```

## 2.2: Sincronizar Status do Plano

```javascript
mcp_ai -
  context_plan({
    action: "syncMarkdown",
    planSlug: "<change-id>"
  });
```

## 2.3: Atualizar Fase Final do Plano

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

## 3.1: Executar Archive

// turbo

```bash
openspec archive <change-id> --yes
```

Resultado: `openspec/changes/<change-id>/` → `openspec/changes/archive/<change-id>/`

## 3.2: Validar Specs

// turbo

```bash
openspec validate --strict
```

---

# FASE 4: Mover Plano AI-Context

## 4.1: Garantir Diretório de Arquivo

Se `.context/plans/archive/` não existir, crie-o.

## 4.2: Mover Plano

```
.context/plans/<change-id>.md
  → .context/plans/archive/<change-id>.md
```

## 4.3: Atualizar Status no Plano Arquivado

Em `.context/plans/archive/<change-id>.md`:

```markdown
> 📋 **Status**: ✅ Concluído e Arquivado
> 📅 **Concluído**: <data atual>
> 🔗 **OpenSpec**: [archive/<change-id>](../../openspec/changes/archive/<change-id>/)
```

---

# FASE 5: Atualizar Referências

## 5.1: Atualizar `proposal.md` Arquivado

Em `openspec/changes/archive/<change-id>/proposal.md`:

**De:**

```markdown
> 📋 **Plano**: [<change-id>.md](../../../.context/plans/<change-id>.md)
```

**Para:**

```markdown
> 📋 **Plano**: [<change-id>.md](../../../.context/plans/archive/<change-id>.md)
```

## 5.2: Atualizar `.context/plans/README.md`

Remova da seção "Planos Ativos" e adicione em "Arquivados":

```markdown
## 📦 Planos Arquivados

| Plano                                   | Concluído | OpenSpec                                                           |
| --------------------------------------- | --------- | ------------------------------------------------------------------ |
| [<change-id>](./archive/<change-id>.md) | <data>    | [archive/<change-id>](../../openspec/changes/archive/<change-id>/) |
```

---

# FASE 6: Atualizar Contexto (Opcional)

Se a mudança alterou arquitetura significativa:

| Mudança        | Documento                       |
| -------------- | ------------------------------- |
| Arquitetura    | `.context/docs/architecture.md` |
| Fluxo de dados | `.context/docs/data-flow.md`    |
| APIs           | `.context/docs/api.md`          |
| Glossário      | `.context/docs/glossary.md`     |

**Apenas se necessário**, reconstrua contexto:

```javascript
mcp_ai -
  context_context({
    action: "getMap",
    section: "all"
  });
```

---

# FASE 7: Conclusão

## 7.1: 🛑 PARADA

1. Confirme arquivamento completo:
   - ✅ OpenSpec em `openspec/changes/archive/<change-id>/`
   - ✅ Plano em `.context/plans/archive/<change-id>.md`
   - ✅ Referências atualizadas
   - ✅ README atualizado

2. Apresente resumo ao usuário

---

**Referências**

- `openspec list` - listar mudanças
- `openspec list --specs` - verificar specs
- `.context/plans/archive/` - planos arquivados
- `openspec/changes/archive/` - propostas arquivadas

<!-- OPENSPEC:END -->

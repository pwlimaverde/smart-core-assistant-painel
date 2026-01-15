---
description: Arquiva mudança concluída e move plano para histórico com links preservados.
---

<!-- OPENSPEC:START -->

**Guardrails**

- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.
- **IDIOMA OBRIGATÓRIO**: Comunicações e documentação devem ser em **PORTUGUÊS**.

---

**Steps**

## Etapa 1: Identificar Change ID

1. Se o prompt incluir um change ID específico (ex: dentro de bloco `<ChangeId>`), use esse valor
2. Se a conversa mencionar uma mudança vagamente:
   - Execute `openspec list` para listar mudanças ativas
   - Identifique candidatos relevantes
   - Confirme com o usuário qual arquivar
3. Se não conseguir identificar, pergunte ao usuário e aguarde confirmação
4. **NÃO prossiga sem um change ID confirmado**

## Etapa 2: Validar Estado

1. Execute `openspec show <id>` para verificar estado da mudança
2. Confirme que:
   - A mudança existe e não está arquivada
   - Todas as tasks em `openspec/changes/<id>/tasks.md` estão `[x]`
3. Verifique que o plano existe em `.context/plans/<change-id>.md`
4. Se a mudança não estiver pronta, informe o usuário e pare

## Etapa 3: Arquivar no OpenSpec

1. Execute: `openspec archive <id> --yes`
   - Use `--skip-specs` apenas para trabalho apenas de tooling
2. Confirme que:
   - A mudança foi movida para `openspec/changes/archive/<id>/`
   - As specs foram atualizadas corretamente
3. Valide: `openspec validate --strict`

## Etapa 4: Mover Plano para Histórico

1. Garanta que o diretório de arquivo existe:

   - Se `.context/plans/archive/` não existir, crie-o

2. Mova o plano:

   ```
   .context/plans/<change-id>.md
     → .context/plans/archive/<change-id>.md
   ```

3. Atualize o status no plano arquivado:
   ```markdown
   > 📋 **Status**: ✅ Concluído e Arquivado
   > 📅 **Data de Conclusão**: <data atual>
   > 🔗 **OpenSpec**: [changes/archive/<change-id>](../../openspec/changes/archive/<change-id>/)
   ```

## Etapa 5: Atualizar Links e README

### 5.1: Atualizar `.context/plans/README.md`

Se o arquivo existir, atualize-o:

1. Remova o plano da seção "Planos Ativos"
2. Adicione na seção "Planos Arquivados":
   ```markdown
   | [<change-id>](./archive/<change-id>.md) | <data> | [changes/archive/<change-id>](../../openspec/changes/archive/<change-id>/) |
   ```

Se o arquivo NÃO existir, crie-o:

```markdown
# Planos de Implementação

Índice de planos gerenciados pelo AI-Context MCP.

## 📋 Planos Ativos

| Plano                  | Status | Criado | Descrição |
| ---------------------- | ------ | ------ | --------- |
| _(nenhum plano ativo)_ | -      | -      | -         |

## 📦 Planos Arquivados

| Plano                                   | Concluído | OpenSpec                                                                   |
| --------------------------------------- | --------- | -------------------------------------------------------------------------- |
| [<change-id>](./archive/<change-id>.md) | <data>    | [changes/archive/<change-id>](../../openspec/changes/archive/<change-id>/) |
```

### 5.2: Atualizar link em `proposal.md` arquivado

No arquivo `openspec/changes/archive/<id>/proposal.md`, atualize o link do plano:

- **De**: `[<change-id>.md](../../../.context/plans/<change-id>.md)`
- **Para**: `[<change-id>.md](../../../.context/plans/archive/<change-id>.md)`

Procure pelo padrão:

```markdown
> 📋 **Plano AI-Context**: [<change-id>.md](../../../.context/plans/<change-id>.md)
```

E substitua por:

```markdown
> 📋 **Plano AI-Context**: [<change-id>.md](../../../.context/plans/archive/<change-id>.md)
```

## Etapa 6: Atualizar Documentação AI-Context (se aplicável)

Avalie se a mudança arquivada requer atualização de documentação:

| Tipo de Mudança                     | Documentação a Atualizar                |
| ----------------------------------- | --------------------------------------- |
| Alterou arquitetura/padrões         | `.context/docs/architecture.md`         |
| Alterou fluxo de dados              | `.context/docs/data-flow.md`            |
| Adicionou/modificou APIs            | `.context/docs/api.md`                  |
| Alterou processo de desenvolvimento | `.context/docs/development-workflow.md` |
| Adicionou novos termos de domínio   | `.context/docs/glossary.md`             |

Se atualização for necessária:

1. Execute `mcp_ai-context_buildSemanticContext` para contexto atualizado
2. Atualize os documentos relevantes com as mudanças
3. Mantenha formato e estilo consistentes

## Etapa 7: Concluir Workflow PREVC

1. Execute `mcp_ai-context_workflowAdvance` para avançar da fase "V" (Validation) para "C" (Confirmation)
2. O workflow será marcado como concluído
3. Confirme com `mcp_ai-context_workflowStatus`

---

**Referência**

- Use `openspec list` para confirmar IDs de mudanças antes de arquivar.
- Inspect specs atualizadas com `openspec list --specs` e resolva issues de validação.
- Consulte `.context/docs/` para verificar documentação que pode precisar atualização.
- Use `mcp_ai-context_buildSemanticContext` para obter visão atualizada do projeto após arquivamento.

<!-- OPENSPEC:END -->

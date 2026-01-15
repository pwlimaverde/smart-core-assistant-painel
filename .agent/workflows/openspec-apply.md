---
description: Implementa mudança aprovada consultando plano e documentação AI-Context.
---

<!-- OPENSPEC:START -->

**Guardrails**

- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.
- **IDIOMA OBRIGATÓRIO**: Comunicações, atualizações de tasks e explicações devem ser em **PORTUGUÊS**.

---

**Pré-requisitos Obrigatórios**

Antes de iniciar este workflow, confirme:

1. ✅ Proposta OpenSpec aprovada em `openspec/changes/<change-id>/`
2. ✅ Plano AI-Context em `.context/plans/<change-id>.md`
3. ✅ Workflow PREVC em fase "R" (Review) - verifique com `mcp_ai-context_workflowStatus`

Se algum pré-requisito não for atendido, execute `/openspec-proposal` primeiro.

---

**Steps**

## Etapa 1: Carregar Contexto Completo

1. Execute `mcp_ai-context_buildSemanticContext`:

   - `repoPath`: caminho do repositório
   - `contextType`: `"compact"`

2. Leia os documentos essenciais:

   - `.context/plans/<change-id>.md` - plano aprovado
   - `openspec/changes/<change-id>/proposal.md` - proposta aprovada
   - `openspec/changes/<change-id>/tasks.md` - lista de tasks
   - `openspec/changes/<change-id>/design.md` - decisões técnicas (se existir)

3. Consulte documentação de apoio:

   - `.context/docs/architecture.md` - padrões arquiteturais
   - `.context/docs/data-flow.md` - fluxo de dados
   - `.context/docs/development-workflow.md` - padrões de desenvolvimento

4. Para contexto específico por tipo de trabalho, use `mcp_ai-context_getAgentDocs`:
   - `agent`: `"backend-specialist"` para trabalho de backend
   - `agent`: `"frontend-specialist"` para trabalho de frontend
   - `agent`: `"database-specialist"` para trabalho de banco de dados

## Etapa 2: Avançar para Execução

1. Execute `mcp_ai-context_workflowAdvance` para avançar da fase "R" (Review) para "E" (Execution)

2. Confirme a transição verificando `mcp_ai-context_workflowStatus`

## Etapa 3: Implementar Tasks

1. Trabalhe sequencialmente seguindo `tasks.md`
2. Para cada task:

   - Leia a descrição e critérios de aceite
   - Consulte `design.md` para decisões arquiteturais relevantes
   - Consulte `.context/docs/` para padrões do projeto
   - Implemente com edits mínimos e focados
   - Verifique que o critério de aceite foi atendido

3. Mantenha foco no escopo definido:
   - NÃO implemente funcionalidades além do escopo
   - NÃO refatore código não relacionado
   - Se descobrir trabalho adicional necessário, documente para future tasks

## Etapa 4: Atualizar Progresso

1. Após completar cada task, atualize `tasks.md`:

   - Mude `- [ ]` para `- [x]`
   - Adicione notas se houver desvios do planejado

2. Exemplo de atualização:

   ```markdown
   - [x] **Task 1**: Criar modelo de dados
     - Arquivos: `src/models/report.py`
     - Critério: Modelo validado com pyright
     - ✅ Concluído: Modelo criado com type hints completos
   ```

3. Periodicamente verifique `mcp_ai-context_workflowStatus` para confirmar estado

## Etapa 5: Avançar para Validação

1. Após completar TODAS as tasks, execute `mcp_ai-context_workflowAdvance` para avançar da fase "E" (Execution) para "V" (Validation)

## Etapa 6: Validar Implementação

1. Rode verificações de qualidade conforme projeto:

   - `uv run task lint` - verificação de estilo
   - `uv run task type-check` - verificação de tipos
   - `uv run task test-docker` - testes (se aplicável)

2. Verifique que TODOS os tasks em `tasks.md` estão marcados como `[x]`

3. Confirme que a implementação atende aos critérios de aceite da proposta

4. Se encontrar problemas:
   - Documente o problema
   - Corrija antes de prosseguir
   - Atualize tasks se necessário

---

**Referência**

- Use `openspec show <id> --json --deltas-only` se precisar de contexto adicional da proposta durante implementação.
- Consulte playbooks de agentes em `.context/agents/` para padrões específicos (backend, database, etc.).
- Use `mcp_ai-context_getAgentDocs` para documentação relevante por tipo de agente.
- Consulte `.context/docs/` para padrões de código e arquitetura.

<!-- OPENSPEC:END -->

---
description: Implement an approved OpenSpec change and keep tasks in sync.
---

<!-- OPENSPEC:START -->

**Guardrails**

- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.
- **IDIOMA OBRIGATÓRIO**: Comunicações, atualizações de tasks e explicações devem ser em **PORTUGUÊS**.

**Pré-requisitos: Carregar Contexto AI-Context**
Antes de iniciar a implementação, carregue o contexto semântico:

1. Execute `mcp_ai-context_buildSemanticContext` (contextType: "compact") para carregar o contexto atual do projeto.
2. Verifique se existe um plano em `.context/plans/<change-id>.md` criado durante a fase de proposal.
3. Consulte o plano e a documentação em `.context/docs/` para entender:
   - Arquitetura atual (`architecture.md`)
   - Fluxo de dados (`data-flow.md`)
   - Padrões de desenvolvimento (`development-workflow.md`)

**Steps**
Track these steps as TODOs and complete them one by one.

1. **[AI-CONTEXT]** Execute os pré-requisitos acima para carregar o contexto semântico.
2. Read `changes/<id>/proposal.md`, `design.md` (if present), and `tasks.md` to confirm scope and acceptance criteria.
3. Work through tasks sequentially, keeping edits minimal and focused on the requested change.
4. Confirm completion before updating statuses—make sure every item in `tasks.md` is finished.
5. Update the checklist after all work is done so each task is marked `- [x]` and reflects reality.
6. Reference `openspec list` or `openspec show <item>` when additional context is required.

**Reference**

- Use `openspec show <id> --json --deltas-only` if you need additional context from the proposal while implementing.
- Consulte playbooks de agentes em `.context/agents/` para padrões específicos (backend, database, etc.).
<!-- OPENSPEC:END -->

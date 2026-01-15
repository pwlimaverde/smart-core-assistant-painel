---
description: Cria plano AI-Context e proposta OpenSpec com validação em duas etapas.
---

<!-- OPENSPEC:START -->

**Guardrails**

- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.
- Identify any vague or ambiguous details and ask the necessary follow-up questions before editing files.
- Do not write any code during the proposal stage. Only create design documents (proposal.md, tasks.md, design.md, and spec deltas). Implementation happens in the apply stage after approval.
- **IDIOMA OBRIGATÓRIO**: Toda a documentação, proposals, tasks e design devem ser escritos em **PORTUGUÊS**.

---

# ═══════════════════════════════════════════════════════════════════════

# FASE 1: Context & Plan (AI-Context)

# ═══════════════════════════════════════════════════════════════════════

**Objetivo**: Criar contexto semântico e plano de implementação para aprovação ANTES de criar artefatos OpenSpec.

## Etapa 1.1: Verificar/Inicializar Scaffolding

1. Execute `mcp_ai-context_checkScaffolding` para verificar estado atual do `.context/`
2. Se `initialized: false`, execute `mcp_ai-context_initializeContext`:
   - `repoPath`: caminho do repositório (ex: `c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel`)
   - `type`: `"both"`
   - `semantic`: `true`
3. Confirme que a estrutura `.context/` foi criada com `docs/`, `agents/` e `plans/`

## Etapa 1.2: Construir Contexto Semântico

1. Execute `mcp_ai-context_buildSemanticContext`:
   - `repoPath`: caminho do repositório
   - `contextType`: `"compact"`
2. Se precisar de detalhes específicos, consulte `mcp_ai-context_getCodebaseMap`:
   - `section`: `"architecture"` para padrões arquiteturais
   - `section`: `"symbols"` para classes e funções principais

## Etapa 1.3: Iniciar Workflow PREVC

1. Execute `mcp_ai-context_workflowInit`:
   - `name`: nome da feature/mudança (ex: "Módulo de Relatórios")
   - `description`: descrição detalhada para auto-detectar escala
2. A escala (QUICK/SMALL/MEDIUM/LARGE/ENTERPRISE) será auto-detectada
3. O workflow iniciará na fase "P" (Planning)

## Etapa 1.4: Criar Plano de Implementação

1. Escolha um `change-id` único seguindo o padrão verbo-substantivo:

   - Exemplos: `add-reports-module`, `fix-auth-bug`, `refactor-api-layer`
   - O mesmo ID será usado no OpenSpec

2. Execute `mcp_ai-context_scaffoldPlan`:

   - `planName`: `<change-id>`
   - `summary`: resumo do objetivo da mudança
   - `semantic`: `true`

3. O plano será criado em `.context/plans/<change-id>.md`

4. Preencha o plano com as seguintes seções:

   ```markdown
   # <Título do Plano>

   > 📋 **Status**: Aguardando Aprovação
   > 🔗 **OpenSpec**: Será criado após aprovação

   ## Objetivo

   [Descrição clara do que será alcançado]

   ## Contexto

   [Por que esta mudança é necessária]

   ## Escopo

   ### Incluído

   - [Item 1]
   - [Item 2]

   ### Não Incluído

   - [Item que NÃO faz parte desta mudança]

   ## Arquitetura Proposta

   [Diagrama ou descrição da solução técnica]

   ## Dependências

   - [Dependência 1]
   - [Dependência 2]

   ## Riscos e Mitigações

   | Risco     | Probabilidade | Impacto | Mitigação      |
   | --------- | ------------- | ------- | -------------- |
   | [Risco 1] | Média         | Alto    | [Como mitigar] |

   ## Estimativa de Esforço

   - **Escala PREVC**: [Auto-detectada]
   - **Complexidade**: [Baixa/Média/Alta]
   - **Componentes afetados**: [Lista]

   ## Tarefas Preliminares

   - [ ] Task 1
   - [ ] Task 2
   ```

## Etapa 1.5: 🛑 PARADA OBRIGATÓRIA

**IMPORTANTE**: Você DEVE parar aqui e solicitar aprovação do plano.

1. Apresente o plano ao usuário com um resumo executivo
2. Destaque pontos que requerem decisão do usuário
3. Aguarde aprovação explícita ("aprovado", "ok", "prossiga") antes da Fase 2
4. Se houver ajustes solicitados:
   - Atualize o plano em `.context/plans/<change-id>.md`
   - Solicite nova aprovação
   - Repita até obter aprovação

---

# ═══════════════════════════════════════════════════════════════════════

# FASE 2: OpenSpec Proposal

# ═══════════════════════════════════════════════════════════════════════

**Pré-requisito OBRIGATÓRIO**: Plano AI-Context aprovado na Fase 1.

## Etapa 2.1: Carregar Contexto e Plano

1. Leia o plano aprovado em `.context/plans/<change-id>.md`
2. Execute `mcp_ai-context_buildSemanticContext` para contexto atualizado
3. Consulte documentação relevante:
   - `.context/docs/architecture.md` - padrões arquiteturais
   - `.context/docs/data-flow.md` - fluxo de dados
   - `.context/docs/api.md` - APIs existentes

## Etapa 2.2: Criar Estrutura OpenSpec

1. Use o mesmo `change-id` do plano AI-Context
2. Crie diretório: `openspec/changes/<change-id>/`
3. A estrutura final será:
   ```
   openspec/changes/<change-id>/
   ├── proposal.md
   ├── tasks.md
   ├── design.md (se necessário)
   └── specs/
       └── <capability>/
           └── spec.md
   ```

## Etapa 2.3: Gerar `proposal.md`

Crie o arquivo com referência explícita ao plano AI-Context:

```markdown
# <Título da Proposta>

> 📋 **Plano AI-Context**: [<change-id>.md](../../../.context/plans/<change-id>.md)
> 📅 **Data**: <data atual>
> 🏷️ **Status**: Em Revisão

## Objetivo

[Copie/adapte do plano AI-Context]

## Contexto

[Contexto técnico e de negócio]

## Escopo

### Incluído

- [Extraído do plano]

### Não Incluído

- [Extraído do plano]

## Decisões de Design

[Principais decisões técnicas tomadas]

## Dependências

[Lista de dependências identificadas]

## Critérios de Aceite

- [ ] Critério 1
- [ ] Critério 2
```

## Etapa 2.4: Gerar `tasks.md`

1. Baseie-se nas tarefas preliminares do plano AI-Context
2. Use `mcp_ai-context_getAgentSequence` para ordenar por tipo de trabalho:
   - `task`: descrição da feature
3. Cada task deve ser pequena e verificável

Formato:

```markdown
# Tasks

> 📋 **Plano AI-Context**: [<change-id>.md](../../../.context/plans/<change-id>.md)

## Checklist

- [ ] **Task 1**: [Descrição clara e verificável]

  - Arquivos: `path/to/file1.py`, `path/to/file2.py`
  - Critério: [Como verificar conclusão]

- [ ] **Task 2**: [Descrição]
  - Arquivos: `path/to/file.py`
  - Critério: [Verificação]

## Dependências entre Tasks

- Task 2 depende de Task 1
- Tasks 3 e 4 podem ser paralelizadas
```

## Etapa 2.5: Gerar `design.md` (se aplicável)

Necessário quando:

- Mudança afeta múltiplos sistemas
- Introduz novos padrões arquiteturais
- Requer discussão de trade-offs

Conteúdo:

- Diagramas de arquitetura
- Decisões técnicas com justificativas
- Alternativas consideradas
- Referência a `.context/docs/architecture.md`

## Etapa 2.6: Criar Spec Deltas

1. Crie diretório: `changes/<change-id>/specs/<capability>/`
2. Crie `spec.md` usando formato:

   ```markdown
   ## ADDED Requirements

   ### Requirement: <nome>

   [Descrição do requisito]

   #### Scenario: <cenário>

   - **Given**: [Pré-condição]
   - **When**: [Ação]
   - **Then**: [Resultado esperado]

   ## MODIFIED Requirements

   [Se modificar requisitos existentes]

   ## REMOVED Requirements

   [Se remover requisitos]
   ```

3. Inclua pelo menos um `#### Scenario:` por requirement

## Etapa 2.7: Validar Proposta

1. Execute: `openspec validate <change-id> --strict`
2. Resolva TODOS os issues reportados antes de prosseguir
3. Use `openspec show <change-id> --json --deltas-only` para inspecionar detalhes

## Etapa 2.8: Avançar Workflow PREVC

Execute `mcp_ai-context_workflowAdvance` para avançar da fase "P" (Planning) para "R" (Review)

## Etapa 2.9: 🛑 PARADA OBRIGATÓRIA

**IMPORTANTE**: Você DEVE parar aqui e solicitar aprovação da proposta OpenSpec.

1. Apresente resumo da proposta OpenSpec completa
2. Liste os arquivos criados
3. Destaque decisões de design importantes
4. Aguarde aprovação antes de iniciar `/openspec-apply`

---

**Referência**

- Use `openspec show <id> --json --deltas-only` ou `openspec show <spec> --type spec` para inspecionar detalhes quando validação falhar.
- Search existing requirements with `rg -n "Requirement:|Scenario:" openspec/specs` before writing new ones.
- Explore the codebase with `rg <keyword>`, `ls`, or direct file reads so proposals align with current implementation realities.
- Consulte `.context/docs/` para documentação de arquitetura e padrões.
- Use `mcp_ai-context_getAgentDocs` para obter documentação relevante por tipo de agente.

<!-- OPENSPEC:END -->

---
name: prevc-planning
trigger: auto
description: Fase P (Planning) do workflow PREVC - Definir o que construir
phases: [P]
skills: [feature-breakdown, api-design, bug-investigation]
source_tool: antigravity
source_path: .agent\workflows\prevc-planning.md
imported_at: 2026-05-14T18:16:27.550Z
ai_context_version: 0.9.2
---

# PREVC - Planning (Fase P)

Workflow para a fase de planejamento do sistema PREVC.

## Objetivo

Definir o que construir, levantar requisitos e criar especificações.

## Quando Ativar

- Nova feature solicitada
- Bug complexo a investigar
- Refatoração planejada

## Skills Associados

- [feature-breakdown](../../.context/skills/feature-breakdown/SKILL.md) - Decomposição de features
- [api-design](../../.context/skills/api-design/SKILL.md) - Design de APIs
- [bug-investigation](../../.context/skills/bug-investigation/SKILL.md) - Investigação de bugs

## Etapas

### 1. Entender o Contexto

```
1. Leia a solicitação/issue
2. Consulte .context/docs/project-overview.md
3. Identifique stakeholders e requisitos
```

### 2. Levantar Requisitos

Documente em `.context/workflow/docs/prd.md`:

- Requisitos funcionais
- Requisitos não-funcionais
- Restrições
- Dependências

### 3. Decompor em Tarefas

Use o skill `feature-breakdown`:

```
1. Identifique componentes principais
2. Quebre em tarefas atômicas
3. Estime complexidade (T-shirt sizing)
4. Identifique dependências entre tarefas
```

### 4. Especificação Técnica

Documente em `.context/workflow/docs/technical-spec.md`:

- Arquitetura proposta
- Interfaces/APIs
- Modelos de dados
- Fluxos de dados

### 5. Definir Critérios de Aceite

Para cada requisito:

```markdown
- [ ] Critério específico e mensurável
- [ ] Pode ser verificado objetivamente
- [ ] Tem escopo claro
```

## Outputs

| Arquivo | Descrição |
|---------|-----------|
| `prd.md` | Requisitos do produto |
| `technical-spec.md` | Especificação técnica |
| `tasks.md` | Lista de tarefas decompostas |

## Gate para Próxima Fase

Antes de ir para Review (R):

- [ ] PRD completo e revisado
- [ ] Spec técnica completa
- [ ] Tarefas decompostas
- [ ] Critérios de aceite definidos
- [ ] Stakeholders alinhados

## Atualizar Status

```yaml
# .context/workflow/status.yaml
phases:
  P:
    status: completed
    outputs:
      - path: ".context/workflow/docs/prd.md"
      - path: ".context/workflow/docs/technical-spec.md"
```

## Próxima Fase

→ [prevc-review](prevc-review.md)

# Skills

On-demand expertise for AI agents. Skills are task-specific procedures that get activated when relevant.

> Project: smart-core-assistant-painel

## How Skills Work

1. **Discovery**: AI agents discover available skills
2. **Matching**: When a task matches a skill's description, it's activated
3. **Execution**: The skill's instructions guide the AI's behavior

## Available Skills

### Built-in Skills

| Skill | Description | Phases |
|-------|-------------|--------|
| [commit-message](./commit-message/SKILL.md) | Gera mensagens de commit seguindo Conventional Commits | E, C |
| [pr-review](./pr-review/SKILL.md) | Revisa Pull Requests de forma estruturada | R, V |
| [code-review](./code-review/SKILL.md) | Verifica qualidade de código contra padrões | R, V |
| [test-generation](./test-generation/SKILL.md) | Gera casos de teste automatizados | E, V |
| [documentation](./documentation/SKILL.md) | Gera e atualiza documentação técnica | E, C |
| [refactoring](./refactoring/SKILL.md) | Refatoração segura de código | E, V |
| [bug-investigation](./bug-investigation/SKILL.md) | Fluxo estruturado de debugging | P, E |
| [feature-breakdown](./feature-breakdown/SKILL.md) | Decomposição de features em tarefas | P, R |
| [api-design](./api-design/SKILL.md) | Design de APIs RESTful | P, R |
| [security-audit](./security-audit/SKILL.md) | Auditoria de segurança e vulnerabilidades | R, V |

## Creating Custom Skills

Create a new skill by adding a directory with a `SKILL.md` file:

```
.context/skills/
└── my-skill/
    ├── SKILL.md          # Required: skill definition
    └── templates/        # Optional: helper resources
        └── checklist.md
```

### SKILL.md Format

```yaml
---
name: my-skill
description: When to use this skill
phases: [P, E, V]  # Optional: PREVC phases
mode: false        # Optional: mode command?
---

# My Skill

## When to Use
[Description of when this skill applies]

## Instructions
1. Step one
2. Step two

## Examples
[Usage examples]
```

## PREVC Phase Mapping

| Phase | Name | Skills |
|-------|------|--------|
| P | Planning | feature-breakdown, documentation, api-design |
| R | Review | pr-review, code-review, api-design, security-audit |
| E | Execution | commit-message, test-generation, refactoring, bug-investigation |
| V | Validation | pr-review, code-review, test-generation, security-audit |
| C | Confirmation | commit-message, documentation |

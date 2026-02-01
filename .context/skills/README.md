# Skills - Expertise On-Demand

Este diretório contém skills que representam procedimentos específicos de tarefas que os agentes de IA podem ativar conforme necessário.

## Skills Disponíveis

| Skill | Descrição | Fases PREVC |
|-------|-----------|-------------|
| [commit-message](commit-message/SKILL.md) | Gera mensagens de commit convencionais | E, C |
| [pr-review](pr-review/SKILL.md) | Revisa Pull Requests | R, V |
| [code-review](code-review/SKILL.md) | Verifica qualidade de código | R, V |
| [test-generation](test-generation/SKILL.md) | Gera casos de teste | E, V |
| [documentation](documentation/SKILL.md) | Gera/atualiza documentação | E, C |
| [refactoring](refactoring/SKILL.md) | Refatoração segura de código | E, V |
| [bug-investigation](bug-investigation/SKILL.md) | Fluxo de debugging | P, E |
| [feature-breakdown](feature-breakdown/SKILL.md) | Decomposição de features em tarefas | P, R |
| [api-design](api-design/SKILL.md) | Design de APIs RESTful | P, R |
| [security-audit](security-audit/SKILL.md) | Auditoria de segurança | R, V |

## Fases PREVC

- **P** (Planning): Planejamento, requisitos, especificações
- **R** (Review): Validação de approach, arquitetura, riscos
- **E** (Execution): Implementação seguindo specs aprovadas
- **V** (Validation): Verificação com testes e code review
- **C** (Confirmation): Documentação, deploy, handoff

## Estrutura de Skill

Cada skill é definido em um arquivo `SKILL.md` dentro de sua pasta:

```markdown
---
name: skill-name
description: Descrição breve
phases: [E, V]
---

# Skill Name

## Quando Usar
...

## Instruções
...

## Exemplos
...
```

## Comandos CLI

```bash
# Inicializar skills
npx @ai-coders/context skill init

# Preencher skills com conteúdo do projeto
npx @ai-coders/context skill fill .

# Listar skills disponíveis
npx @ai-coders/context skill list

# Exportar para ferramentas de IA
npx @ai-coders/context skill export --preset claude
```

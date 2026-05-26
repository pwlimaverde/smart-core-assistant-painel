---
name: restructure-plan
trigger: manual
description: Reestruturar Plano de Implementação com a documentação atual do repositório/libs
phases: [P]
skills: [plan-restructuring]
---

# Reestruturar Plano com Docs Atuais

Etapa de refinamento de planejamento: valida e corrige um plano de implementação contra a documentação **atual** das bibliotecas utilizadas no projeto.

## Instruções

Siga integralmente o procedimento em `.context/skills/plan-restructuring/SKILL.md`:

1. **Levante as libs** do plano (com versão, cruzando `pyproject.toml` e `uv.lock`).
2. **Colete documentação atual** disparando subagentes com modelo mais rápido (como Gemini 3.5 Flash) que usam o MCP context (`resolve-library-id` → `query-docs`). Rode em paralelo.
3. **Reestruture o plano** disparando um subagente com modelo mais capaz (como Gemini 1.5 Pro ou Opus), passando o plano original + a documentação coletada.
4. **Salve** o plano reestruturado em `.context/plans/{feature}.md` e atualize `.context/workflow/status.yaml`.

## Parâmetros

- `$ARGUMENTS`: Caminho ou nome do plano a reestruturar. Se omitido, use o plano ativo mais recente em `.context/plans/` ou o plano elaborado na conversa atual.

## Output Esperado

1. Plano reestruturado salvo em `.context/plans/{feature}.md`.
2. Seção "Correções aplicadas" com o que mudou e por quê (lib/versão/recurso).
3. Status do workflow atualizado.

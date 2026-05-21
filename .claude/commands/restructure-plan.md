# /restructure-plan - Reestruturar Plano com Docs Atuais

Etapa FINAL de planejamento: valida e corrige um plano já existente contra a
documentação **atual** das bibliotecas, via MCP context7, usando subagentes com
modelo otimizado por etapa (coleta = barato, reestruturação = caro).

## Instruções

Siga integralmente o procedimento em
`.context/skills/plan-restructuring/SKILL.md`:

1. **Levante as libs** do plano (com versão, cruzando `pyproject.toml`/`uv.lock`).
2. **Colete documentação atual** disparando subagentes `Agent` com `model: "haiku"`
   que usam o MCP context7 (`resolve-library-id` → `query-docs`). Rode em paralelo.
3. **Reestruture o plano** disparando um subagente `Agent` com `model: "opus"`,
   passando o plano original + a documentação coletada.
4. **Salve** o plano reestruturado em `.context/plans/{feature}.md` e atualize
   `.context/workflow/status.yaml`.

## Parâmetros

- `$ARGUMENTS`: Caminho ou nome do plano a reestruturar. Se omitido, use o plano
  ativo mais recente em `.context/plans/` ou o plano elaborado na conversa atual.

## Exemplo de Uso

```
/restructure-plan
/restructure-plan autenticação-oauth
/restructure-plan .context/plans/dashboard-analytics.md
```

## Output Esperado

1. Plano reestruturado salvo em `.context/plans/{feature}.md`.
2. Seção "Correções aplicadas" com o que mudou e por quê (lib/versão/recurso).
3. Status do workflow atualizado.

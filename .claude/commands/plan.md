# /plan - Criar Plano de Implementação

Cria um plano estruturado usando o workflow PREVC para uma nova feature ou mudança.

## Instruções

1. **Leia o contexto do projeto**
   - Consulte `.context/docs/project-overview.md` para visão geral
   - Consulte `.context/docs/architecture.md` para padrões

2. **Use o skill de feature-breakdown**
   - Siga `.context/skills/feature-breakdown/SKILL.md`

3. **Crie o plano em `.context/plans/`**
   - Use o template: `.context/workflow/docs/prd-template.md`
   - Nomeie como: `{nome-da-feature}.md`

4. **Atualize o status do workflow**
   - Atualize `.context/workflow/status.yaml` para fase P (Planning)

## Parâmetros

- `$ARGUMENTS`: Nome/descrição da feature a ser planejada

## Exemplo de Uso

```
/plan autenticação oauth
/plan integração notion
/plan dashboard analytics
```

## Output Esperado

1. Arquivo de plano em `.context/plans/{feature}.md`
2. Status atualizado em `.context/workflow/status.yaml`
3. Resumo das tarefas identificadas

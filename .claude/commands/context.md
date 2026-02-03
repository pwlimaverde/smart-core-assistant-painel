# /context - Carregar Contexto do Projeto

Carrega e exibe o contexto completo do projeto para orientar o trabalho.

## Instruções

1. **Documentação Principal**
   - `.context/docs/README.md` - Índice
   - `.context/docs/project-overview.md` - Visão geral
   - `.context/docs/architecture.md` - Arquitetura

2. **Agentes Disponíveis**
   - `.context/agents/README.md` - Lista completa

3. **Skills PREVC**
   - `.context/skills/README.md` - Lista de skills

4. **Workflow Atual**
   - `.context/workflow/status.yaml` - Status

## Parâmetros

- `$ARGUMENTS`: Área específica (docs, agents, skills, workflow)

## Exemplo de Uso

```
/context              # Visão geral completa
/context docs         # Apenas documentação
/context agents       # Apenas agentes
/context skills       # Apenas skills
/context workflow     # Apenas workflow
```

## Output Esperado

Resumo estruturado do contexto solicitado com links para documentação detalhada.

# Claude Code Configuration & Context

O ecossistema deste projeto está **100% centralizado** e coordenado pelo MCP `ai-context` sob o diretório base `.context/`. 
Todas as instruções, regras da arquitetura e perfis de agente devem emanar de lá.

**IMPORTANTE: O idioma de comunicação, reports e planos neste projeto é OBRIGATORIAMENTE o Português. O código e seus métodos estarão sempre em Inglês.**

## Roteamento de Diretrizes (.context)

Em qualquer atividade ou tomada de decisão em andamento, direcione-se ou chame os sub-recursos mapeados nas ramificações a seguir, ao invés de buscar referências fora do projeto:
- **Índice Mestre de Referências**: [.context/docs/README.md](.context/docs/README.md)
- **Especializações e Instruções (Agents)**: [.context/agents/README.md](.context/agents/README.md) - Encontre a especialidade associada (backend, architect, etc).
- **Skills Ativas**: [.context/skills/](.context/skills/)
- **Planejamento e Execução PREVC**: [.context/workflow/status.yaml](.context/workflow/status.yaml) (Monitoramento de estado), e [.context/plans/](.context/plans/) (Planos atuais).

### Ações Obrigatórias para Análises Profundas
1. Consulte o `bug-fixer.md` nos agents para fluxograma de investigação baseada em isolamento de causa.
2. Ao propor ou escrever código, verifique `architecture.md` (via `.context/docs`) e adote Multi-Tenant e Result Pattern rigidamente.
3. Não crie testes automatizados ativamente. Caso encontre problemas de linting e type checking (`pyright`), repare-os. Reduza a complexidade das interações do framework de ML mantendo os tokens isolados de `.env`.

Sincronize-se periodicamente conforme necessário com sua task MCP de `workflow-advance` do ai-context.

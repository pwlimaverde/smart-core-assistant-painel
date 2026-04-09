# Antigravity Context

Este projeto utiliza o MCP `ai-context` para gerenciar centralmente toda a documentação, configurações de agentes e habilidades (skills).
**IMPORTANTE: O idioma padrão de comunicação neste projeto é Português. Você deve operar nos limites e diretrizes da sua especialização estrita.**

## Centralização no `.context/`

Sempre que atuar ou buscar instruções contextuais detalhadas, direcione-se **exclusivamente** para o diretório `.context/`:

- **Documentação Master**: [.context/docs/README.md](../../.context/docs/README.md) - Ponto de entrada de arquitetura, workflow, segurança e convenções.
- **Instruções e Perfis de Agente**: [.context/agents/README.md](../../.context/agents/README.md) - Leia a configuração de especialização pertinente à task.
- **Planos e Históricos PREVC**: [.context/plans/README.md](../../.context/plans/README.md) e o status do workflow em `.context/workflow/status.yaml`.
- **Skills Ativas**: Todos os comandos PREVC de skills estão mantidos em `.context/skills/`.

Ao realizar tool calls analíticos, procure confirmar o escopo em suas definições locais dentro de `.context/` antes de assumir papéis não solicitados.
Você tem à disposição o set de ferramentas do MCP `ai-context` (ex: workflow-init, workflow-advance, agent discover/orchestrate) para registrar o lifecycle de sua colaboração. Utilize-os sempre que guiar as fases P R E V C.

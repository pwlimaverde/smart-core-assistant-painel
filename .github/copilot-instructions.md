# Codex / Copilot Context Mapping

Este projeto foi configurado com uma coordenação centralizada na estrutura `.context/`.
**IMPORTANTE: O idioma de explicação nos comentários e pull requests é o Português (pt-BR), enquanto todo o código deve se manter em Inglês.**

## Informação Centralizada (MCP AI-Context)

Para garantir aderência impecável à arquitetura, Multi-tenancy, patterns "Result" e segurança:
Você *DEVE* consumir a documentação e os escopos centralizados descritos nestes caminhos, em vez de recorrer a palpites ou conhecimentos arbitrários fora do projeto:

- **Documentation Root**: `.context/docs/README.md`
- **Agent Profiles & Specs**: `.context/agents/` (Leia o especialista relevante para sua task, como feature-developer.md ou backend-specialist.md)
- **Skills Ativas**: `.context/skills/`
- **Workflow Ativo**: Status em `.context/workflow/status.yaml` e planos em `.context/plans/README.md`

### Padrões Imediatos
1. Todo model/queryset deve conter `.filter(tenant=request.user.tenant)` quando em acesso isolado.
2. Não adicione "secrets", use sempre `decouple.config` ou instâncias `.env` baseadas no `.env.example`.
3. Garanta type hints em tudo (`-> Result[Data, Exception]`).
4. Os testes automatizados não devem ser refeitos sob escopos genéricos; caso acionado a debugar, preserve estritamente o flow de logs estruturados e consulte `bug-fixer.md`.

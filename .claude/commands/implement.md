# /implement - Implementar Feature

Implementa uma feature seguindo o plano aprovado e o workflow PREVC.

## Instruções

1. **Verifique o plano existente**
   - Leia o plano em `.context/plans/{feature}.md`
   - Confirme que está na fase E (Execution)

2. **Consulte o agente apropriado**
   - Feature Django: `.context/agents/backend-specialist.md`
   - Feature IA: `.context/agents/ai-specialist.md`
   - Feature Frontend: `.context/agents/frontend-specialist.md`

3. **Siga os padrões do projeto**
   - Type hints obrigatórios
   - Result pattern para erros
   - Multi-tenancy sempre filtrado

4. **Use os skills relevantes**
   - Código: `.context/skills/refactoring/SKILL.md`
   - Commits: `.context/skills/commit-message/SKILL.md`

5. **Atualize o status**
   - Marque fase E como `in_progress`
   - Ao concluir, marque como `completed`

## Parâmetros

- `$ARGUMENTS`: Nome da feature a implementar (deve ter plano aprovado)

## Exemplo de Uso

```
/implement autenticação-oauth
/implement integração-notion
```

## Checklist

- [ ] Plano existe e está aprovado
- [ ] Código segue padrões do projeto
- [ ] Type hints em todas as funções
- [ ] Multi-tenancy respeitado
- [ ] Commits seguem Conventional Commits

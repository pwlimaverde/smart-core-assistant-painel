# /review - Revisar Código

Realiza code review **pontual** (arquivos ou PR) seguindo os padrões do projeto e
skills PREVC. É um checklist de qualidade manual.

> Para a **auditoria final do ciclo** (planejado vs. implementado, com subagente
> Opus e auto-correção, antes de arquivar o plano), use [`/final-review`](final-review.md).

## Instruções

1. **Use os skills de review**
   - `.context/skills/code-review/SKILL.md`
   - `.context/skills/pr-review/SKILL.md`

2. **Consulte o agente de review**
   - `.context/agents/code-reviewer.md`

3. **Verifique os padrões**
   - Consulte `CLAUDE.md` para padrões de código
   - Verifique `.context/docs/architecture.md` para padrões arquiteturais

4. **Checklist de Review**
   - Type hints completos
   - Docstrings Google style
   - Multi-tenancy respeitado
   - Sem N+1 queries
   - Segurança (OWASP)

## Parâmetros

- `$ARGUMENTS`: Arquivo(s) ou PR a revisar

## Exemplo de Uso

```
/review src/smart_core_assistant_painel/app/atendimentos/views.py
/review PR #123
```

## Output Esperado

Relatório de review com:
- ✅ Pontos positivos
- 💡 Sugestões
- ⚠️ Mudanças necessárias
- Veredicto: Aprovado/Mudanças Solicitadas

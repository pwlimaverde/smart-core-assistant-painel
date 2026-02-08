# /refactor - Refatorar Código

Refatora código existente seguindo boas práticas e mantendo comportamento.

## Instruções

1. **Use o skill de refactoring**
   - `.context/skills/refactoring/SKILL.md`

2. **Consulte o agente especializado**
   - `.context/agents/refactoring-specialist.md`

3. **Processo Seguro**
   - Verificar testes existentes
   - Fazer mudanças incrementais
   - Testar após cada mudança
   - Commits atômicos

4. **Técnicas Comuns**
   - Extract Method
   - Extract Class
   - Replace Conditional with Polymorphism
   - Simplify Conditionals
   - Remove Duplication

## Parâmetros

- `$ARGUMENTS`: Arquivo ou módulo a refatorar

## Exemplo de Uso

```
/refactor src/smart_core_assistant_painel/app/atendimentos/services/
/refactor modules/ai_engine/features/analise_mensage/
```

## Checklist

- [ ] Testes passam antes
- [ ] Mudanças incrementais
- [ ] Testes passam depois
- [ ] Comportamento inalterado
- [ ] Código mais legível
- [ ] Commits atômicos: `refactor(módulo): descrição`

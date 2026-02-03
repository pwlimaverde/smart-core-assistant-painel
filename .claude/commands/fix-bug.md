# /fix-bug - Investigar e Corrigir Bug

Investiga e corrige bugs seguindo o fluxo estruturado de debugging.

## Instruções

1. **Use o skill de bug investigation**
   - `.context/skills/bug-investigation/SKILL.md`

2. **Consulte o agente especializado**
   - `.context/agents/bug-fixer.md`

3. **Fluxo de Correção**
   - Reproduzir o bug
   - Identificar causa raiz
   - Implementar correção
   - Validar correção

4. **Documente**
   - Crie script de reprodução em `teste_debug/` se necessário
   - Commit com `fix:` seguindo Conventional Commits

## Parâmetros

- `$ARGUMENTS`: Descrição do bug ou ID do issue

## Exemplo de Uso

```
/fix-bug webhook não processa mensagens de áudio
/fix-bug atendimento não sincroniza com Trello
/fix-bug issue #45
```

## Checklist

- [ ] Bug reproduzido localmente
- [ ] Causa raiz identificada
- [ ] Correção implementada
- [ ] Código de debug removido
- [ ] Testes existentes passam
- [ ] Commit: `fix(módulo): descrição`

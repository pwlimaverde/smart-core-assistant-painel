# /commit - Criar Commit

Cria commit seguindo Conventional Commits e padrões do projeto.

## Instruções

1. **Use o skill de commit-message**
   - `.context/skills/commit-message/SKILL.md`

2. **Analise as mudanças**
   ```bash
   git diff --staged
   git status
   ```

3. **Identifique o tipo**
   - `feat:` - Nova funcionalidade
   - `fix:` - Correção de bug
   - `docs:` - Documentação
   - `style:` - Formatação
   - `refactor:` - Refatoração
   - `test:` - Testes
   - `chore:` - Manutenção
   - `perf:` - Performance

4. **Formato**
   ```
   <tipo>(<escopo>): <descrição>

   [corpo opcional]

   [rodapé opcional]
   ```

## Parâmetros

- `$ARGUMENTS`: Mensagem de commit (opcional, será gerada se não fornecida)

## Exemplo de Uso

```
/commit
/commit feat(atendimentos): add status filter endpoint
```

## Checklist

- [ ] Mudanças staged (`git add`)
- [ ] Tipo correto identificado
- [ ] Escopo define módulo afetado
- [ ] Descrição clara e concisa
- [ ] Sem arquivos sensíveis (.env, credentials)

---
name: commit-message
description: Gera mensagens de commit seguindo Conventional Commits
phases: [E, C]
---

# Commit Message Skill

## Quando Usar

Use este skill quando:
- Criando commits Git após implementar mudanças
- Precisando padronizar mensagens de commit
- Gerando changelog automatizado

## Instruções

1. **Analise as mudanças staged**
   ```bash
   git diff --staged
   git status
   ```

2. **Identifique o tipo de mudança**
   - `feat:` - Nova funcionalidade
   - `fix:` - Correção de bug
   - `docs:` - Alterações em documentação
   - `style:` - Formatação (sem alteração de lógica)
   - `refactor:` - Refatoração de código
   - `test:` - Adição/modificação de testes
   - `chore:` - Tarefas de manutenção
   - `perf:` - Melhorias de performance
   - `ci:` - Alterações de CI/CD

3. **Defina o escopo (opcional)**
   - Use o nome do módulo ou app afetado
   - Exemplos: `feat(atendimentos):`, `fix(evolution_sync):`

4. **Escreva a descrição**
   - Use imperativo: "add", "fix", "update" (não "added", "fixed")
   - Máximo 72 caracteres na primeira linha
   - Seja conciso mas descritivo

5. **Adicione corpo se necessário**
   - Explique o "porquê", não o "o quê"
   - Quebre em linhas de 72 caracteres

## Formato

```
<tipo>(<escopo>): <descrição>

[corpo opcional]

[rodapé opcional]
```

## Exemplos

### Padrões do Projeto

```bash
# Nova feature
feat(atendimentos): add automatic status update on message received

# Correção de bug
fix(evolution_sync): resolve webhook signature validation error

# Documentação
docs(api): update webhook endpoint documentation

# Refatoração
refactor(ai_engine): extract message analysis to separate usecase

# Performance
perf(treinamento): optimize document chunk generation query

# Com corpo explicativo
feat(trello_sync): add card movement on status change

Automatically moves Trello cards when atendimento status changes.
Cards are moved to configured lists based on status mapping.

Closes #123
```

### Breaking Changes

```bash
feat(api)!: change authentication to JWT

BREAKING CHANGE: API now requires JWT token instead of session auth.
All clients must update their authentication flow.
```

## Verificação

Antes de commitar, verifique:
- [ ] Tipo correto para a mudança
- [ ] Escopo identifica módulo afetado
- [ ] Descrição clara e concisa
- [ ] Sem erros de ortografia
- [ ] Breaking changes marcados com `!`
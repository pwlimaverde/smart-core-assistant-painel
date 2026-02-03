---
name: prevc-validation
trigger: auto
description: Fase V (Validation) do workflow PREVC - Verificar que funciona
phases: [V]
skills: [test-generation, pr-review, code-review]
---

# PREVC - Validation (Fase V)

Workflow para a fase de validação do sistema PREVC.

## Objetivo

Verificar que a implementação funciona e atende aos critérios de aceite.

## Quando Ativar

- Após conclusão da fase E (Execution)
- Código implementado
- Pronto para testes e review

## Skills Associados

- [test-generation](../../.context/skills/test-generation/SKILL.md) - Geração de testes
- [pr-review](../../.context/skills/pr-review/SKILL.md) - Revisão de PRs
- [code-review](../../.context/skills/code-review/SKILL.md) - Revisão de código

## Etapas

### 1. Executar Testes

```bash
# Rodar testes no Docker (preferido)
uv run task test-docker

# Ou rodar teste específico
uv run task test-docker -- -k "nome_do_teste"
```

### 2. Verificar Qualidade

```bash
# Lint
uv run task lint

# Type check
uv run task type-check

# Formatação
uv run task format
```

### 3. Verificar Critérios de Aceite

Consulte o PRD e verifique cada critério:

```markdown
## Critérios de Aceite

- [x] Critério 1 - Verificado
- [x] Critério 2 - Verificado
- [ ] Critério 3 - Pendente
```

### 4. Code Review

Use o skill `code-review`:

- Verificar padrões de código
- Verificar segurança
- Verificar performance
- Verificar manutenibilidade

### 5. Criar Pull Request

```bash
# Push da branch
git push -u origin feature/[nome]

# Criar PR via GitHub CLI
gh pr create --title "feat: descrição" --body "..."
```

### 6. Aguardar Aprovação

- Responder feedback do review
- Fazer ajustes necessários
- Obter aprovação

## Checklist de Validação

### Funcionalidade
- [ ] Feature funciona conforme especificado
- [ ] Edge cases tratados
- [ ] Erros tratados graciosamente

### Qualidade
- [ ] Código legível e manutenível
- [ ] Sem código duplicado
- [ ] Documentação adequada

### Segurança
- [ ] Sem vulnerabilidades OWASP
- [ ] Dados sensíveis protegidos
- [ ] Input validado

### Performance
- [ ] Queries otimizadas
- [ ] Sem memory leaks
- [ ] Tempo de resposta aceitável

## Outputs

| Arquivo | Descrição |
|---------|-----------|
| `test-report.md` | Relatório de testes |
| PR aprovado | Pull Request revisado |

## Gate para Próxima Fase

Antes de ir para Confirmation (C):

- [ ] Testes passando
- [ ] Code review aprovado
- [ ] Critérios de aceite verificados
- [ ] PR mergeado

## Atualizar Status

```yaml
# .context/workflow/status.yaml
phases:
  V:
    status: completed
    outputs:
      - path: ".context/workflow/docs/test-report.md"
```

## Próxima Fase

→ [prevc-confirmation](prevc-confirmation.md)

---
name: prevc-confirmation
trigger: auto
description: Fase C (Confirmation) do workflow PREVC - Entregar e documentar
phases: [C]
skills: [documentation, commit-message]
source_tool: antigravity
source_path: .agent\workflows\prevc-confirmation.md
imported_at: 2026-05-14T18:16:27.547Z
ai_context_version: 0.9.2
---

# PREVC - Confirmation (Fase C)

Workflow para a fase de confirmação do sistema PREVC.

## Objetivo

Documentar a entrega, atualizar changelog e fazer handoff.

## Quando Ativar

- Após conclusão da fase V (Validation)
- Testes passando
- PR mergeado

## Skills Associados

- [documentation](../../.context/skills/documentation/SKILL.md) - Documentação
- [commit-message](../../.context/skills/commit-message/SKILL.md) - Mensagens de commit

## Etapas

### 1. Atualizar Documentação

Se necessário, atualize:

```
.context/docs/
├── architecture.md     # Mudanças arquiteturais
├── data-flow.md        # Novos fluxos de dados
├── glossary.md         # Novos termos
└── tooling.md          # Novas ferramentas
```

### 2. Gerar Changelog

Adicione entrada em `.context/workflow/docs/changelog.md`:

```markdown
## [YYYY-MM-DD] - Nome da Feature

### Adicionado
- Nova feature X
- Endpoint Y

### Modificado
- Refatoração do módulo Z

### Corrigido
- Bug W corrigido
```

### 3. Atualizar README (se necessário)

Se a feature adiciona comandos ou configurações novas:

```markdown
## Novo Comando

```bash
uv run task novo-comando
```
```

### 4. Notificar Stakeholders

- Comunicar conclusão
- Documentar onde encontrar a feature
- Fornecer instruções de uso

### 5. Arquivar Plano

Mova o plano para arquivo:

```bash
mv .context/plans/[nome]/ .context/plans/archive/[data]-[nome]/
```

### 6. Atualizar Status Final

```yaml
# .context/workflow/status.yaml
phases:
  C:
    status: completed
    outputs:
      - path: ".context/workflow/docs/changelog.md"

history:
  - phase: C
    status: completed
    timestamp: "YYYY-MM-DDTHH:MM:SSZ"
    notes: "[Nome da feature] entregue"
```

## Outputs

| Arquivo | Descrição |
|---------|-----------|
| `changelog.md` | Changelog atualizado |
| Documentação | Docs atualizados |
| Plano arquivado | Em `.context/plans/archive/` |

## Checklist Final

- [ ] Documentação atualizada
- [ ] Changelog gerado
- [ ] README atualizado (se aplicável)
- [ ] Stakeholders notificados
- [ ] Plano arquivado
- [ ] Status atualizado

## Conclusão

Após esta fase, o ciclo PREVC está completo:

```
✅ P (Planning) - Completo
✅ R (Review) - Completo
✅ E (Execution) - Completo
✅ V (Validation) - Completo
✅ C (Confirmation) - Completo
```

## Reset para Próximo Ciclo

Para iniciar novo ciclo:

```yaml
# .context/workflow/status.yaml
current_phase: P
phases:
  P:
    status: pending
  R:
    status: pending
  E:
    status: pending
  V:
    status: pending
  C:
    status: pending
```

## Referências

- [Workflow Status](../../.context/workflow/status.yaml)
- [Plans Archive](../../.context/plans/archive/)
- [Documentation Index](../../.context/docs/README.md)

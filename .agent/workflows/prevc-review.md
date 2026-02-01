---
name: prevc-review
trigger: auto
description: Fase R (Review) do workflow PREVC - Validar approach e arquitetura
phases: [R]
skills: [code-review, security-audit]
---

# PREVC - Review (Fase R)

Workflow para a fase de revisão do sistema PREVC.

## Objetivo

Validar o approach técnico, revisar arquitetura e avaliar riscos.

## Quando Ativar

- Após conclusão da fase P (Planning)
- PRD e spec técnica estão prontos
- Antes de iniciar implementação

## Skills Associados

- [code-review](../../.context/skills/code-review/SKILL.md) - Revisão de código/design
- [security-audit](../../.context/skills/security-audit/SKILL.md) - Auditoria de segurança

## Etapas

### 1. Revisar Especificações

```
1. Leia .context/workflow/docs/prd.md
2. Leia .context/workflow/docs/technical-spec.md
3. Verifique completude e clareza
```

### 2. Validar Arquitetura

Consulte `.context/docs/architecture.md` e verifique:

- Compatibilidade com arquitetura existente
- Padrões sendo seguidos
- Impacto em módulos existentes

### 3. Avaliação de Riscos

Identifique e documente:

```markdown
## Riscos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Risco 1 | Alta | Alto | Ação X |
| Risco 2 | Média | Baixo | Ação Y |
```

### 4. Security Review

Use o skill `security-audit`:

- Verifique OWASP Top 10
- Avalie superfície de ataque
- Identifique dados sensíveis

### 5. Criar ADRs (se necessário)

Para decisões arquiteturais significativas:

```markdown
# ADR-XXX: Título da Decisão

## Status
Proposto

## Contexto
Descrição do problema...

## Decisão
O que foi decidido...

## Consequências
Impactos positivos e negativos...
```

## Outputs

| Arquivo | Descrição |
|---------|-----------|
| `architecture.md` | Documento de arquitetura atualizado |
| `adr/*.md` | Architecture Decision Records |
| `risk-assessment.md` | Avaliação de riscos |

## Gate para Próxima Fase

Antes de ir para Execution (E):

- [ ] Arquitetura validada
- [ ] Riscos avaliados e mitigados
- [ ] Security review concluído
- [ ] ADRs criados (se aplicável)
- [ ] Aprovação do Tech Lead

## Atualizar Status

```yaml
# .context/workflow/status.yaml
phases:
  R:
    status: completed
    outputs:
      - path: ".context/workflow/docs/architecture.md"
```

## Próxima Fase

→ [prevc-execution](prevc-execution.md)

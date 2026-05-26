---
name: final-review
trigger: manual
description: Auditoria final comparando o planejado com o implementado e validação do ciclo
phases: [C]
skills: [prevc-final-review]
---

# Auditoria Final da Implementação (Gate da Fase C - Confirmation)

Audita a implementação do ciclo atual **contra o plano aprovado** usando um subagente com o modelo mais capaz, corrige automaticamente os desvios e libera o arquivamento do plano.

> Diferente de `/review` (checklist de qualidade pontual em arquivos/PR), este comando confronta **planejado vs. implementado** no diff inteiro do ciclo.

## Instruções

Siga integralmente o skill [.context/skills/prevc-final-review/prevc-final-review.md](../../.context/skills/prevc-final-review/prevc-final-review.md):

1. **Reunir contexto** (agente principal):
   - Plano ativo via `.context/workflow/plans.json` (`primary`) → `.context/plans/<slug>.md` + pasta `.context/plans/<slug>/`.
   - PRD/spec em `.context/workflow/docs/`.
   - Diff do ciclo: `git diff master...HEAD` + `git status --short`.

2. **Lançar subagente** com modelo mais capaz (Gemini 1.5 Pro ou Opus):
   - Prompt conforme a Etapa 1 do skill (auditar plano vs. código, **corrigir automaticamente**, revalidar com `lint`/`type-check`/testes existentes).

3. **Persistir relatório** em `.context/workflow/docs/final-review.md`.

4. **Veredito**:
   - `CONFORME` / `CORRIGIDO` → seguir fase C e **arquivar** o plano.
   - `FALHOU` → não arquivar; reportar o que travou.

## Regras

- **NÃO criar testes** automatizados (diretriz do projeto).
- Idioma: Português no relatório; código em Inglês.
- Política decidida: **auto-correção total** → corrige → revalida → arquiva.

## Parâmetros

- `$ARGUMENTS` (opcional): slug de um plano específico. Se vazio, usa o `primary` de `plans.json`.

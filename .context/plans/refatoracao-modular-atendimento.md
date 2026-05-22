---
status: in_progress
progress: 60
generated: 2026-05-20
restructured: 2026-05-22
agents:
  - type: "frontend-specialist"
    role: "Design system, modularização Alpine.js, tokens Tailwind v4"
  - type: "backend-specialist"
    role: "Mover views/selectors/signals do monolito para os apps"
  - type: "architect-specialist"
    role: "Decisão shell, roteamento, validação de integração"
  - type: "code-reviewer"
    role: "Validação manual de cada fase e build de produção"
docs:
  - "project-overview.md"
  - "architecture.md"
  - "development-workflow.md"
phases:
  - id: "F1"
    name: "Design System — componentes genéricos + core_alpine.js + tokens (Tailwind v4)"
    prevc: "E"
    agent: "frontend-specialist"
    status: "in_progress"
  - id: "F1V"
    name: "Validação Design System — render sem regressão no shell"
    prevc: "V"
    agent: "code-reviewer"
    status: "pending"
  - id: "F2"
    name: "chat_evolution — mover views/selectors/signals + templates + chat.css + chat_alpine.js"
    prevc: "E"
    agent: "backend-specialist"
    status: "in_progress"
  - id: "F2V"
    name: "Validação chat_evolution — endpoints /workspace/chat/api/ + Evolution send/markRead/presence"
    prevc: "V"
    agent: "code-reviewer"
    status: "pending"
  - id: "F3"
    name: "gestao_kanban — mover views/selectors/signals + templates + kanban.css + SortableJS"
    prevc: "E"
    agent: "backend-specialist"
    status: "in_progress"
  - id: "F3V"
    name: "Validação gestao_kanban — endpoints /workspace/kanban/api/ + drag-drop sincronizado"
    prevc: "V"
    agent: "code-reviewer"
    status: "pending"
  - id: "F4"
    name: "Integração UI Shell — workspace_coordinator.js + ordem de assets + reduzir workspace_alpine.js"
    prevc: "E"
    agent: "frontend-specialist"
    status: "pending"
  - id: "F4V"
    name: "Validação integração — eventos cross-app + SSE único"
    prevc: "V"
    agent: "architect-specialist"
    status: "pending"
  - id: "F5"
    name: "Limpeza do monolito — remover views/selectors/partials/css/js migrados"
    prevc: "E"
    agent: "backend-specialist"
    status: "pending"
  - id: "F6"
    name: "Build de produção Tailwind v4 (CLI/PostCSS) + validação final + deploy"
    prevc: "V"
    agent: "code-reviewer"
    status: "pending"
lastUpdated: "2026-05-22T00:00:00.000Z"
---

# Refatoração Modular do Atendimento Unificado Plan

> Separação em 3 apps (`chat_evolution`, `gestao_kanban`, shell `atendimento_unificado`) + módulo agnóstico `modules/design_system`. **Reestruturado em 2026-05-22** contra docs atuais (Django 5.2.7, Alpine.js v3, Tailwind v4, SortableJS, Evolution Go v2.3.7) e contra o **estado real do código (~60%)**.

## Artefatos detalhados

> A **verdade técnica** completa deste plano vive nos arquivos abaixo. Este canônico é só o mapa de fases PREVC.

- **Plano completo (etapas, snippets, riscos):** [`.context/plans/refatoracao-modular-atendimento/plano_completo_refatoracao-modular-atendimento.md`](refatoracao-modular-atendimento/plano_completo_refatoracao-modular-atendimento.md)
- **Documentação auxiliar (libs + Evolution Go):** [`.context/plans/refatoracao-modular-atendimento/info_aux_refatoracao-modular-atendimento.md`](refatoracao-modular-atendimento/info_aux_refatoracao-modular-atendimento.md)

## Task Snapshot

- **Objetivo:** separar o monolito `atendimento_unificado` em `chat_evolution` + `gestao_kanban` + shell + `modules/design_system`, preservando a UI, sem quebrar chat/SSE/kanban/drag-drop.
- **Estado:** ~60% concluído. Apps, settings, services, rotas e partials no lugar; falta **mover as VIEWS** do monolito, completar o design system, quebrar o JS/CSS monolítico e validar/limpar.
- **Sucesso:** workspace funcionando com a mesma UI a partir dos apps separados; SSE único (`/workspace/events/`), drag-drop sincronizado, sem import cruzado entre apps.

## Decisões-chave reconciliadas com o código

1. **Rotas reais sob `/workspace/`:** `chat/api/`, `kanban/api/`, `events/` (não `/chat/`,`/kanban/` na raiz). Verdade: `atendimento_unificado/urls.py`.
2. **SSE ÚNICO por tenant:** canal `sse:{tenant_slug}:events` + endpoint `/workspace/events/`. Apps **não** criam `views_sse.py`; apenas publicam `type` `chat.*`/`kanban.*` via `realtime_publisher`. Cliente usa **um** `EventSource` filtrando por `event:`.
3. **Models por import canônico** de `atendimentos.models` — `managed=False`/proxy/`db_table="atu_*"` **proibido** (quebra `makemigrations`; commit `db787ca`). `models.py` dos novos apps é docstring-only.
4. **Tasks de views:** "mover" (não recriar) as classes do monolito preservando os nomes já roteados nos `api_urls.py`.
5. **Tailwind v4 CSS-first** (`@theme`/`@utility`); CDN `@tailwindcss/browser` é **dev-only** → produção exige build CLI/PostCSS (Fase 6).
6. **Validação manual** (projeto não cria testes automatizados).

## Fases PREVC

Cada fase de execução (E) tem validação (V) emparelhada. Detalhe completo no plano completo.

| Fase | Nome | PREVC | Agente | Status |
|------|------|-------|--------|--------|
| F1 | Design System (componentes + core_alpine.js + tokens v4) | E | frontend-specialist | in_progress |
| F1V | Validação Design System | V | code-reviewer | pending |
| F2 | chat_evolution (mover views/selectors/signals + front) | E | backend-specialist | in_progress |
| F2V | Validação chat_evolution + Evolution Go | V | code-reviewer | pending |
| F3 | gestao_kanban (mover views/selectors/signals + SortableJS) | E | backend-specialist | in_progress |
| F3V | Validação gestao_kanban + drag-drop | V | code-reviewer | pending |
| F4 | Integração UI Shell (coordinator + ordem de assets) | E | frontend-specialist | pending |
| F4V | Validação integração + SSE único | V | architect-specialist | pending |
| F5 | Limpeza do monolito | E | backend-specialist | pending |
| F6 | Build produção Tailwind v4 + validação final + deploy | V | code-reviewer | pending |

**Dependências:** F1 → F1V → (F2 ∥ F3) → F2V/F3V → F4 → F4V → F5 → F6.

## Riscos principais

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| Reintroduzir `managed=False`/proxy cross-app | Baixa | Alta | Import canônico de `atendimentos.models`; `makemigrations --check` |
| Alpine registra fora de `alpine:init` (defer) | Média | Média | Módulos antes do core Alpine (ordem em F4.4) |
| SortableJS dessincroniza `x-for` | Média | Média | `splice` no array reativo no `onEnd` |
| CDN Tailwind em produção (sem purge) | Alta | Média | Build CLI/PostCSS estático (F6) |
| SSE async sob Gunicorn sync trava worker | Alta | Alta | Sync-stub + flag; SSE real só sob UvicornWorker |
| Mídia base64 >3MB ⇒ 500 Evolution | Média | Média | Enviar via URL acima de 3MB |
| Tick azul automático indevido | Média | Média | `readMessages=false` + markRead explícito |

## Correções aplicadas (reestruturação 2026-05-22)

Resumo (lista completa, com fontes, na seção 8 do plano completo):

1. Rotas reconciliadas para `/workspace/...` (estado real do código).
2. **SSE único** documentado (corrige plano v4.0 que duplicaria SSE em `/chat/events/` + `/kanban/events/`).
3. `managed=False`/proxy removido dos princípios → import canônico (`db787ca`, Django 5.2.7).
4. Tasks de views passam de "criar" para "mover", preservando nomes roteados.
5. Tailwind v4 CSS-first + build de produção (CDN dev-only).
6. Alpine v3: registro em `alpine:init`, ordem de `defer`, SortableJS sincronizado.
7. Evolution Go v2.3.7: endpoints/headers/body exatos, `readMessages=false`, `webhookBase64=false`, mídia grande via URL, markRead explícito.
8. Removidas tasks de testes automatizados (validação manual).
9. Estrutura PREVC E/V por fase mapeada a agentes.

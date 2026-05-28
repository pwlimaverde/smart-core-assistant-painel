---
status: archived
generated: 2026-05-26
title: "Design System Desacoplado — Migração DTL → Jinja2"
summary: "Centralizar toda a camada visual em modules/design_system/ com Jinja2, migrando 72 templates dos apps Django para o design system centralizado, mantendo DTL apenas para o Admin (Jazzmin)."
agents:
  - type: "frontend-specialist"
    role: "Migração de templates DTL → Jinja2 e criação de components.css"
  - type: "code-reviewer"
    role: "Revisão e validação de cada fase de migração"
docs:
  - "project-overview.md"
  - "architecture.md"
  - "development-workflow.md"
phases:
  - id: "phase-1-components-css"
    name: "Componentes CSS Utilitários"
    prevc: "E"
    agent: "frontend-specialist"
    status: "completed"
  - id: "phase-2-workspace"
    name: "Migração Workspace (Atendimento + Chat + Kanban)"
    prevc: "E"
    agent: "frontend-specialist"
    status: "completed"
  - id: "phase-3-tenants"
    name: "Migração Configurações e Tenants"
    prevc: "E"
    agent: "frontend-specialist"
    status: "completed"
  - id: "phase-4-settings-users"
    name: "Migração Settings, Treinamento e Usuários"
    prevc: "E"
    agent: "frontend-specialist"
    status: "completed"
  - id: "phase-5-core-errors"
    name: "Migração Core e Páginas de Erro"
    prevc: "E"
    agent: "frontend-specialist"
    status: "completed"
  - id: "phase-6-cleanup"
    name: "Limpeza Total e Finalização"
    prevc: "V"
    agent: "code-reviewer"
    status: "completed"
---

# Design System Desacoplado — Migração DTL → Jinja2

> Centralizar toda a camada visual em `modules/design_system/` com Jinja2,
> migrando 72 templates dos apps Django para o design system centralizado,
> mantendo DTL apenas para o Admin (Jazzmin).

## Artefatos Detalhados

| Artefato | Caminho | Descrição |
|----------|---------|-----------|
| Plano completo | [plano_completo](design-system-refactor/plano_completo_design-system-refactor.md) | Detalhamento técnico com todas as fases, templates e procedimentos |
| Documentação auxiliar | [info_aux](design-system-refactor/info_aux_design-system-refactor.md) | Docs de Django Jinja2, Tailwind v4, W3C Design Tokens, cheat sheet DTL→Jinja2 |

## Task Snapshot

- **Primary goal:** Migrar 72 templates DTL dos apps Django para Jinja2 no `modules/design_system/`, eliminando acoplamento frontend/backend.
- **Success signal:** Zero arquivos `.html` em `app/*/templates/` (exceto admin overrides), zero `{% load %}` no design_system, build CSS funcional.

## Fases PREVC

### Fase 1 — Componentes CSS Utilitários (E)
Criar `components.css` com classes utilitárias (`.ui-btn`, `.ui-badge`, `.ui-input`, `.ui-card`, etc.) que consomem os tokens `--ws-*`.

### Fase 2 — Migração Workspace (E)
Migrar 18 templates de atendimento_unificado, chat_evolution e gestao_kanban.

### Fase 3 — Migração Tenants (E)
Migrar 27 templates de tenants, evolution_sync (configs, onboarding, backoffice, users).

### Fase 4 — Settings, Treinamento e Usuários (E)
Migrar 17 templates de settings_manager, treinamento e usuarios.

### Fase 5 — Core e Erros (E)
Migrar 9 templates do core (dashboard, home, landing) e páginas de erro (403, 404, 500).

### Fase 6 — Limpeza e Validação (V)
Remover templates antigos, atualizar settings.py, rebuild CSS, validação final.

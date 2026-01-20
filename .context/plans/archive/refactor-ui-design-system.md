---
status: archived
generated: 2026-01-12
linked-openspec: changes/archive/2026-01-20-refactor-ui-design-system
---

# Refatoração do Sistema de Design UI Plan

> 📋 **Status**: ✅ Concluído e Arquivado
> 📅 **Data de Conclusão**: 20/01/2026
> 🔗 **OpenSpec**: [changes/archive/2026-01-20-refactor-ui-design-system](../../openspec/changes/archive/2026-01-20-refactor-ui-design-system/)

> Refatoração do sistema de design da UI do Django Admin, padronizando telas navegáveis, auditando permissões por role e documentando a estrutura final.

## Task Snapshot

- **Primary goal:** Padronizar 100% das telas navegáveis do sistema com o Design System definido e documentar a topologia final em `UI_MAP.md`.
- **Success signal:** Todas as views usam `base_dashboard.html`, sidebar funcional, permissões auditadas e `UI_MAP.md` completo.
- **Key references:**
  - [Documentation Index](../docs/README.md)
  - [Agent Handbook](../agents/README.md)
  - [OpenSpec Proposal](file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/openspec/changes/refactor-ui-design-system/proposal.md)
  - [OpenSpec Tasks](file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/openspec/changes/refactor-ui-design-system/tasks.md)

## Codebase Context

- **Total files analyzed:** 381
- **Total symbols discovered:** 605
- **Architecture layers:** Services, Repositories, Config, Controllers, Models, Components, Utils
- **Detected patterns:** Factory, Singleton, Service Layer

### Componentes Relevantes para UI

**Templates Django:**

- `src/smart_core_assistant_painel/app/ui/templates/` - Templates principais
- `src/smart_core_assistant_painel/app/tenants/templates/` - Templates de tenant
- `src/smart_core_assistant_painel/app/evolution_sync/templates/` - Templates Evolution

**Views:**

- `app/tenants/views/` - Views de dashboard, config, backoffice
- `app/ui/usuarios/views.py` - Views de autenticação
- `app/ui/treinamento/views.py` - Views de treinamento IA

**Permissões:**

- `TenantModule` @ `app/tenants/permissions.py:4` - Módulos de permissão
- `TenantRoleType` @ `app/tenants/permissions.py:22` - Tipos de role

## Agent Lineup

| Agent                | Papel neste plano                               | Playbook                                                     |
| -------------------- | ----------------------------------------------- | ------------------------------------------------------------ |
| Frontend Specialist  | Padronização de templates e componentes visuais | [frontend-specialist.md](../agents/frontend-specialist.md)   |
| Security Auditor     | Auditoria de permissões por role em cada tela   | [security-auditor.md](../agents/security-auditor.md)         |
| Documentation Writer | Criação do `UI_MAP.md` final                    | [documentation-writer.md](../agents/documentation-writer.md) |
| Code Reviewer        | Revisão de alterações em templates              | [code-reviewer.md](../agents/code-reviewer.md)               |

## Mapeamento OpenSpec ↔ AI-Context

Este plano complementa a proposta OpenSpec em `openspec/changes/refactor-ui-design-system/`:

| Módulo OpenSpec | Telas                               | Foco Principal      |
| --------------- | ----------------------------------- | ------------------- |
| Módulo 1        | Landing, Erros (403/404/500)        | Páginas públicas    |
| Módulo 2        | Backoffice (`/tenants/bo/`)         | Super Admin only    |
| Módulo 3        | Login, Signup, Onboarding           | Autenticação        |
| Módulo 4        | Dashboards (Tenant, Gerente)        | Navegação principal |
| Módulo 5        | Configs (DB, Evolution, Trello, AI) | Configurações       |
| Módulo 6        | Treinamento IA                      | Módulo de IA        |
| Módulo 7        | Gestão de Usuários                  | Permissões          |

## Risk Assessment

### Identified Risks

| Risk                                    | Probability | Impact | Mitigation                                  |
| --------------------------------------- | ----------- | ------ | ------------------------------------------- |
| Templates com dependências não mapeadas | Média       | Alta   | Verificar `{% extends %}` e `{% include %}` |
| Permissões inconsistentes entre views   | Média       | Alta   | Testar cada role manualmente                |
| Sidebar não aparecendo em algumas views | Alta        | Média  | Verificar herança de `base_dashboard.html`  |

### Dependencies

- **Internal:** Sistema de roles (`TenantModule`, `TenantRoleType`)
- **Technical:** Jazzmin theme configurado

## Working Phases

### Phase 1 — Discovery & Mapping (Módulos 1-3)

**Steps:**

1. Mapear todas as URLs e views correspondentes
2. Verificar herança de templates atual
3. Listar permissões por view

**Commit Checkpoint:** `chore(ui): complete phase 1 - discovery modules 1-3`

### Phase 2 — Padronização (Módulos 4-6)

**Steps:**

1. Aplicar `base_dashboard.html` onde necessário
2. Padronizar componentes (cards, tables, forms)
3. Corrigir sidebar e navegação

**Commit Checkpoint:** `feat(ui): complete phase 2 - standardize modules 4-6`

### Phase 3 — Auditoria & Documentação (Módulo 7 + Finalização)

**Steps:**

1. Auditar permissões em todas as telas
2. Criar/atualizar `UI_MAP.md`
3. Remover templates obsoletos

**Commit Checkpoint:** `docs(ui): complete phase 3 - audit and documentation`

## Evidence & Follow-up

- [ ] `UI_MAP.md` criado e completo
- [ ] Todas as tasks do OpenSpec marcadas como `[x]`
- [ ] Validação manual de cada módulo documentada
- [ ] PR com todas as alterações

---
status: in_progress
generated: 2026-05-20
agents:
  - type: "code-reviewer"
    role: "Review code changes for quality, style, and best practices"
  - type: "feature-developer"
    role: "Implement new features according to specifications"
  - type: "refactoring-specialist"
    role: "Identify code smells and improvement opportunities"
  - type: "test-writer"
    role: "Write comprehensive unit and integration tests"
  - type: "documentation-writer"
    role: "Create clear, comprehensive documentation"
  - type: "backend-specialist"
    role: "Design and implement server-side architecture"
  - type: "frontend-specialist"
    role: "Design and implement user interfaces"
  - type: "architect-specialist"
    role: "Design overall system architecture and patterns"
docs:
  - "project-overview.md"
  - "architecture.md"
  - "development-workflow.md"
  - "testing-strategy.md"
phases:
  - id: "phase-1"
    name: "Design System Agnóstico"
    prevc: "E"
    agent: "frontend-specialist"
  - id: "phase-2"
    name: "Backend - Separação Lógica"
    prevc: "E"
    agent: "backend-specialist"
  - id: "phase-3"
    name: "Frontend - Quebra do Monolito JS/CSS"
    prevc: "E"
    agent: "frontend-specialist"
  - id: "phase-4"
    name: "Limpeza e Validação"
    prevc: "V"
    agent: "code-reviewer"
---

# Refatoração Modular do Atendimento Unificado Plan

> Separação em 3 apps (chat, kanban, shell) e 1 módulo de design system

## Task Snapshot
- **Primary goal:** Refatorar o app monolítico `atendimento_unificado` em uma estrutura distribuída, limpa e modular.
- **Success signal:** O sistema funcionará com a mesma UI, porém rodando a partir de 3 apps independentes e 1 módulo agnóstico de design. Nenhuma quebra no fluxo principal de atendimento (chat e kanban).

## Agent Lineup
| Agent | Role in this plan | Focus |
| --- | --- | --- |
| Architect Specialist | Define a divisão de pastas e rotas | Estruturação de apps, models e caminhos globais do Django |
| Frontend Specialist | Move e refatora templates, CSS, JS | Criar o core.css, separar partials HTML, modularizar Alpine.js |
| Backend Specialist | Move Views, Services e rotas API | Registrar os apps no settings e mapear os proxy models |
| Code Reviewer | Valida a limpeza | Garantir que o monolito original esteja enxuto e limpo |

## Risk Assessment

### Identified Risks
| Risk | Probability | Impact | Mitigation Strategy | Owner (Agent) |
| --- | --- | --- | --- | --- |
| Regressão visual (CSS) | Medium | Medium | Migração cautelosa do Design System e uso do Tailwind | `frontend-specialist` |
| Erro de banco com `managed=False` | Low | High | Reutilizar `db_table` com nome original `atu_*` rigorosamente | `backend-specialist` |

## Working Phases

### Phase 1 — Criação da Estrutura e do Design System Agnóstico
> **Primary Agent:** `frontend-specialist`

**Objective:** Criar módulo independente base para padronizar UI.

**Tasks**
| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 1.1 | Criar pasta `modules/design_system/` | `frontend-specialist` | completed | Pasta com `core.css` criada |
| 1.2 | Configurar Django (settings) | `backend-specialist` | completed | Adicionado TEMPLATES/STATICFILES |
| 1.3 | Migrar CSS base e tokens | `frontend-specialist` | completed | `workspace-tokens.css` copiado |
| 1.4 | Mover componentes HTML parciais genéricos | `frontend-specialist` | pending | HTMLs globais em components/ |

**Commit Checkpoint**
`git commit -m "chore(ui): implement base design system agnostic structure"`

---

### Phase 2 — Backend: Separação Lógica
> **Primary Agent:** `backend-specialist`

**Objective:** Criar e isolar apps Django `chat_evolution` e `gestao_kanban`.

**Tasks**
| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 2.1 | Criar os dois novos apps e registrá-los | `backend-specialist` | pending | Apps no `INSTALLED_APPS` |
| 2.2 | Criar models proxies e services do Kanban | `backend-specialist` | pending | `db_table="atu_*"` e `managed=False` |
| 2.3 | Criar models proxies e services do Chat | `backend-specialist` | pending | `db_table="atu_*"` e `managed=False` |
| 2.4 | Isolar rotas sob prefixos `/chat/api` e `/kanban/api` | `backend-specialist` | pending | `urls.py` criados em cada app |

**Commit Checkpoint**
`git commit -m "refactor(backend): separate chat and kanban django apps"`

---

### Phase 3 — Frontend: Quebra do Monolito JS/CSS
> **Primary Agent:** `frontend-specialist`

**Objective:** Separar os JS de orquestração do Alpine e templates baseados no negócio.

**Tasks**
| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 3.1 | Mover templates parciais de domínio para seus apps | `frontend-specialist` | pending | `chat_evolution/templates` |
| 3.2 | Refatorar `workspace_alpine.js` quebrando em módulos | `frontend-specialist` | pending | Scopes reduzidos para `x-data` |
| 3.3 | Atualizar chamadas `fetch` do JS para os novos prefixos | `frontend-specialist` | pending | URLs consertadas |

**Commit Checkpoint**
`git commit -m "refactor(frontend): decouple alpinejs modules and domain partials"`

---

### Phase 4 — Limpeza e Validação
> **Primary Agent:** `code-reviewer`

**Objective:** Confirmar a integridade final e remover os vestígios do app antigo.

**Tasks**
| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 4.1 | Validar todo fluxo do Atendimento (SSE, Kanban, DND, Chat) | `code-reviewer` | pending | Teste completo da interface |
| 4.2 | Excluir arquivos obsoletos do core | `backend-specialist` | pending | App `atendimento_unificado` limpo |

**Commit Checkpoint**
`git commit -m "chore: cleanup unified workspace legacy files"`

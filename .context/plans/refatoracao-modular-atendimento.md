---
status: in_progress
progress: 60
generated: 2026-05-20
restructured: 2026-05-21
agents:
  - type: "code-reviewer"
    role: "Review code changes for quality, style, and best practices"
  - type: "feature-developer"
    role: "Implement new features according to specifications"
  - type: "refactoring-specialist"
    role: "Identify code smells and improvement opportunities"
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
phases:
  - id: "phase-1"
    name: "Design System Agnóstico"
    prevc: "E"
    agent: "frontend-specialist"
    status: "in_progress"
  - id: "phase-2"
    name: "Backend - Separação Lógica"
    prevc: "E"
    agent: "backend-specialist"
    status: "in_progress"
  - id: "phase-3"
    name: "Frontend - Quebra do Monolito JS/CSS"
    prevc: "E"
    agent: "frontend-specialist"
    status: "in_progress"
  - id: "phase-4"
    name: "Limpeza e Validação"
    prevc: "V"
    agent: "code-reviewer"
    status: "pending"
lastUpdated: "2026-05-21T00:00:00.000Z"
---

# Refatoração Modular do Atendimento Unificado Plan

> Separação em 3 apps (chat_evolution, gestao_kanban, shell=atendimento_unificado) e 1 módulo agnóstico de design system (`modules/design_system`)

## Task Snapshot
- **Primary goal:** Refatorar o app monolítico `atendimento_unificado` em uma estrutura distribuída, limpa e modular, preservando a mesma UI.
- **Success signal:** Sistema funcionando com a mesma UI, rodando a partir de `chat_evolution` + `gestao_kanban` + shell (`atendimento_unificado`) + módulo agnóstico `modules/design_system`. Nenhuma quebra no fluxo principal (chat, SSE, kanban, drag-and-drop).
- **Estado de progresso:** ~60% concluído. A estrutura de apps, settings, services, rotas e partials já está no lugar; falta mover as VIEWS do monolito, completar o design system de componentes e quebrar definitivamente o JS/CSS monolítico, além da validação/limpeza final.

### Justificativa da estimativa (~60%)
| Fase | Peso | Concluído | Contribuição |
|---|---|---|---|
| Fase 1 (Design System) | 20% | 3 de 4 tasks (estrutura, settings, tokens feitos; componentes não) | ~15% |
| Fase 2 (Backend) | 35% | 3 de 4 tasks de fato concluídas (apps, models canônicos, rotas); views ainda no monolito | ~25% |
| Fase 3 (Frontend JS/CSS) | 25% | partials movidos e JS iniciado; workspace.js/css ainda monolíticos | ~12% |
| Fase 4 (Validação/Limpeza) | 20% | não iniciada | 0% |
| **Total** | **100%** | | **~52-60%** |

O `progress: 100` original era contraditório (todas as tasks marcadas `pending`). Ajustado para `60`.

## Agent Lineup
| Agent | Role in this plan | Focus |
| --- | --- | --- |
| Architect Specialist | Define a divisão de pastas e rotas | Estruturação de apps, decisão shell vs. novo app, caminhos globais Django |
| Backend Specialist | Move Views, Services e rotas API | Mover `views_api`/`views_sse`/`selectors` para os apps; manter imports canônicos de models |
| Frontend Specialist | Move e refatora templates, CSS, JS | Componentes do design system, modularização Alpine.js, migração de tokens Tailwind v4 |
| Code Reviewer | Valida a limpeza | Garantir que o shell esteja enxuto, fluxo intacto e sem código órfão |

## Risk Assessment

### Identified Risks
| Risk | Probability | Impact | Mitigation Strategy | Owner (Agent) |
| --- | --- | --- | --- | --- |
| Regressão visual (CSS) ao migrar tokens/componentes | Medium | Medium | Migrar tokens 1:1 para `@theme`; comparar visual antes/depois; manter classes utilitárias existentes | `frontend-specialist` |
| **Tailwind CDN browser é dev-only** — `@tailwindcss/browser@4` em `core/templates/base.html` processa tudo em runtime no navegador; não confiável/performático em produção | High | High | Definir estratégia de build real para os tokens do design system: PostCSS `@tailwindcss/postcss` ou Tailwind CLI gerando CSS estático servido via `staticfiles`. Não depender do CDN para os `@theme`/`@utility` do `core.css` em produção | `frontend-specialist` |
| **Ordem de carregamento do Alpine** — componentes não registrados antes de o Alpine avaliar `x-data="chat"`/`x-data="kanban"` | Medium | High | Registrar componentes via `Alpine.data(...)` dentro de `document.addEventListener('alpine:init', ...)`; carregar `chat_alpine.js`/`kanban_alpine.js` com `defer` ANTES (ou junto) do core do Alpine; usar `alpine:initialized` para código pós-init | `frontend-specialist` |

> **Removido:** o risco "Erro de banco com `managed=False`" não se aplica mais. A abordagem `managed=False`/db_table duplicada foi abandonada (commit `db787ca`) em favor do import direto dos models canônicos, que é a recomendação oficial do Django 5.2 (ver Fase 2).

## Working Phases

### Phase 1 — Criação da Estrutura e do Design System Agnóstico
> **Primary Agent:** `frontend-specialist`

**Objective:** Criar módulo independente base (`modules/design_system`) para padronizar UI de forma agnóstica aos apps.

**Tasks**
| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 1.1 | Criar pasta `modules/design_system/` com `core.css` | `frontend-specialist` | completed | `modules/design_system/static/css/core.css` (186 linhas) criado |
| 1.2 | Configurar Django (settings) TEMPLATES['DIRS'] + STATICFILES_DIRS | `backend-specialist` | completed | `core/settings.py` (linhas ~221 e ~348) apontando para `modules/design_system/templates` e `/static` |
| 1.3 | Migrar CSS base e tokens (workspace-tokens.css) para o design system | `frontend-specialist` | completed | Tokens base presentes no `core.css` |
| 1.4 | Mover componentes HTML parciais GENÉRICOS (agnósticos de domínio) para `design_system/templates/components/` | `frontend-specialist` | in_progress | Componentes reutilizáveis em `components/`; hoje só existe `components/README.html` (1 linha) |

**Detalhamento 1.4 — componentes a mover (apenas genéricos, sem regra de chat/kanban):**
- `button.html` / `icon_button.html` — botões e ações base.
- `badge.html` / `tag.html` — pílulas e etiquetas visuais (sem lógica de etiqueta de domínio).
- `avatar.html` — avatar de contato/usuário.
- `modal.html` / `panel.html` — invólucros de painel lateral e modal reutilizáveis (a casca, não o `detail_panel.html` do kanban).
- `spinner.html` / `empty_state.html` — estados de carregamento e vazio.
- `dropdown.html` — menu suspenso genérico.

> Critério: permanecem nos apps os partials com regra de negócio (`chat_message.html`, `kanban_card.html`, `detail_panel.html`, `custom_fields_panel.html`); migram para o design system apenas casca/estrutura visual reutilizável. Componentes devem consumir tokens via `var(--...)` definidos no `@theme`.

**Commit Checkpoint**
`git commit -m "feat(ui): add agnostic design-system components"`

---

### Phase 2 — Backend: Separação Lógica
> **Primary Agent:** `backend-specialist`

**Objective:** Criar e isolar os apps Django `chat_evolution` e `gestao_kanban`, com models e rotas próprios, mantendo `atendimento_unificado` como dono dos models canônicos.

**Tasks**
| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 2.1 | Criar os dois novos apps e registrá-los no `INSTALLED_APPS` | `backend-specialist` | completed | `chat_evolution` e `gestao_kanban` com `apps.py`/`AppConfig` registrados em `core/settings.py` (linhas ~156-158) |
| 2.2 | Kanban: usar **import direto dos models canônicos** + mover services | `backend-specialist` | completed | `gestao_kanban/models.py` contém APENAS docstring instruindo importar de `atendimento_unificado.models`; services movidos (`board_service`, `card_renderer`, `etiquetas_service`, `notas_service`, `transfer_fluxo_service`) |
| 2.3 | Chat: usar **import direto dos models canônicos** + mover services | `backend-specialist` | completed | `chat_evolution/models.py` apenas docstring; services `message_dispatch_service`, `media_dispatch_service` movidos |
| 2.4 | Isolar rotas sob prefixos `chat/api/` e `kanban/api/` | `backend-specialist` | completed | `chat_evolution/api_urls.py` e `gestao_kanban/api_urls.py` incluídos via `atendimento_unificado/urls.py` (sob `/workspace/`) |
| 2.5 | **Mover as VIEWS do monolito para os apps** (views_api, views_sse, selectors) | `backend-specialist` | pending | Views de chat → `chat_evolution/`; views de kanban → `gestao_kanban/`; `api_urls` deixam de importar `from atendimento_unificado import views_api` |
| 2.6 | **Definir o app "shell"**: manter `atendimento_unificado` como shell da `WorkspaceView` + `base_workspace.html` | `architect-specialist` | pending | Decisão registrada; `WorkspaceView` e templates raiz permanecem no shell |

**Detalhamento 2.2 / 2.3 — decisão de models (REESCRITA vs. plano original):**
O plano original previa **proxy models / `managed=False` com `db_table="atu_*"`**. Essa abordagem foi tentada e **abandonada** (commit `db787ca` — *"remove duplicate unmanaged models and fix cross-app imports"*), pois duplicar a definição do model com a mesma `db_table` faz o Django detectar inconsistência e **quebrar o `makemigrations`**.

A solução adotada (e recomendada oficialmente pelo **Django 5.2**) é **importar o model canônico diretamente** do app dono:

```python
# Em gestao_kanban/services/board_service.py (consumo direto)
from smart_core_assistant_painel.app.atendimento_unificado.models import (
    CampoPersonalizado, Etiqueta, EtiquetaAtendimento, Nota, ValorCampoAtendimento,
)
```

`models.py` dos novos apps contém apenas docstring documentando essa convenção. Proxy models só se justificam para estender comportamento Python; `managed=False` só para views de banco/subset de campos — nenhum dos dois é o caso aqui.

**Detalhamento 2.5 — mover views:**
Hoje `chat_evolution/api_urls.py` e `gestao_kanban/api_urls.py` ainda fazem `from atendimento_unificado import views_api` (há comentário no código: *"Por enquanto as views ainda residem em atendimento_unificado / Serão movidas no próximo passo"*). Mover:
- Handlers de mensagem/mídia/SSE de chat (`views_api` parte chat, `views_sse`) → `chat_evolution/views_api.py` e `chat_evolution/views_sse.py`.
- Handlers de board/cards/etiquetas/notas/campos (`views_api` parte kanban) → `gestao_kanban/views_api.py`.
- `selectors.py`: dividir as queries por domínio entre os apps; queries compartilhadas/transversais permanecem em um `selectors.py` no shell.
- Manter Result Pattern (`py-return-success-or-error`) e contexto multi-tenant (`get_current_tenant()`) intactos na movimentação.

**Detalhamento 2.6 — decisão sobre o app "shell":**
O título menciona "3 apps: chat, kanban, shell". **Decisão: manter `atendimento_unificado` como o app shell** (não criar um novo app `shell`), justificativa:
- Ele já hospeda `WorkspaceView`, `base_workspace.html`/`workspace.html`, os models canônicos e as migrations — mover isso para um app novo geraria migration churn e risco sem ganho arquitetural.
- Atua de fato como shell: monta as rotas `chat/api/` e `kanban/api/` sob `/workspace/` e é o dono do estado canônico.
- Ação: documentar explicitamente o papel de shell e deixar nele apenas a `WorkspaceView`, templates raiz, models canônicos, migrations e o `realtime_publisher.py` (transversal).

**Commit Checkpoint**
`git commit -m "refactor(backend): move chat/kanban views and selectors into their apps"`

---

### Phase 3 — Frontend: Quebra do Monolito JS/CSS
> **Primary Agent:** `frontend-specialist`

**Objective:** Separar os JS de orquestração do Alpine e os CSS por domínio, eliminando o monolito `workspace_alpine.js`/`workspace.css`.

**Tasks**
| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 3.1 | Mover templates parciais de domínio para seus apps | `frontend-specialist` | completed | `chat_evolution/templates/chat_evolution/partials/` (chat_message, chat_mini_bar) e `gestao_kanban/templates/gestao_kanban/partials/` (detail_panel, kanban_card, kanban_column, custom_fields_panel) |
| 3.2 | Quebrar `workspace_alpine.js` em `Alpine.data()` por app + `Alpine.store()` compartilhado | `frontend-specialist` | in_progress | `chat_alpine.js` e `kanban_alpine.js` existem mas ainda mínimos (kanban com 8 linhas); `workspace_alpine.js` ainda monolítico no shell |
| 3.3 | Atualizar chamadas `fetch` do JS para os novos prefixos (`chat/api/`, `kanban/api/`) | `frontend-specialist` | in_progress | URLs atualizadas nos JS de cada app |
| 3.4 | Migrar `workspace.css`/`workspace-tokens.css` do monolito para o design system (Tailwind v4) | `frontend-specialist` | pending | Tokens em `@theme`, utilities em `@utility`/`@layer components` no `core.css`; remover CSS do `atendimento_unificado/static` |

**Detalhamento 3.2 — modularização Alpine.js v3 (com armadilha de ordem):**
Extrair os blocos do `workspace_alpine.js` para componentes registrados via `Alpine.data(...)` dentro de `alpine:init`, e o estado transversal (ex.: foco/seleção de conversa, painel aberto) para `Alpine.store(...)`:

```javascript
// chat_evolution/static/chat_evolution/js/chat_alpine.js
document.addEventListener('alpine:init', () => {
  Alpine.data('chat', () => ({
    messages: [],
    sendMessage() { /* fetch('/workspace/chat/api/...') */ },
  }))
})
```

```javascript
// gestao_kanban/static/gestao_kanban/js/kanban_alpine.js
document.addEventListener('alpine:init', () => {
  Alpine.data('kanban', () => ({
    columns: [],
    moveCard() { /* fetch('/workspace/kanban/api/...') */ },
  }))
})
```

```javascript
// estado transversal (no shell, ex.: workspace_store.js)
document.addEventListener('alpine:init', () => {
  Alpine.store('workspace', {
    selectedConversationId: null,
    detailPanelOpen: false,
  })
})
// uso no template: x-data="chat", $store.workspace.selectedConversationId
```

> **Armadilha de ordem (crítica):** `Alpine.data`/`Alpine.store` DEVEM ser registrados em `alpine:init`, que dispara ANTES de o Alpine percorrer o DOM. Os scripts `chat_alpine.js`/`kanban_alpine.js`/`workspace_store.js` devem ser carregados com `defer` ANTES (ou junto com) o core do Alpine, garantindo que `x-data="chat"` já encontre o componente registrado. Código que precisa rodar após o init usa o evento `alpine:initialized`.

**Detalhamento 3.4 — Tailwind v4 (`@theme`/`@utility`):**
Tailwind v4 abandonou `tailwind.config.js`; a configuração é CSS-first. Migrar os tokens do `workspace-tokens.css` para um bloco `@theme` no `core.css`, e as utilities customizadas para `@utility`:

```css
/* modules/design_system/static/css/core.css */
@import "tailwindcss";

@theme {
  --color-workspace-bg: #0f172a;
  --color-workspace-accent: #2563eb;
  --spacing-panel: 24rem;
  --font-workspace: "Inter", sans-serif;
}

@utility panel-shadow {
  box-shadow: 0 4px 24px rgb(0 0 0 / 0.18);
}

@layer components {
  .workspace-card { /* ... */ }
}
```

Tokens do `@theme` viram utilities automaticamente e ficam disponíveis como `var(--color-workspace-accent)`. **Ver risco de produção:** os `@theme`/`@utility` precisam de build real (PostCSS `@tailwindcss/postcss` ou CLI) para produção — o `@tailwindcss/browser@4` no `core/templates/base.html` é apenas para desenvolvimento.

**Commit Checkpoint**
`git commit -m "refactor(frontend): split alpine modules and migrate tokens to design-system"`

---

### Phase 4 — Limpeza e Validação
> **Primary Agent:** `code-reviewer`

**Objective:** Confirmar a integridade final, definir build de produção do Tailwind e remover vestígios do monolito.

**Tasks**
| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 4.1 | Validar todo o fluxo (SSE, Kanban, DND, Chat) e ordem de init do Alpine | `code-reviewer` | pending | Teste manual completo da interface sem regressão |
| 4.2 | Definir/implementar build de produção do Tailwind v4 (PostCSS/CLI) para o design system | `frontend-specialist` | pending | CSS estático gerado e servido via `staticfiles`, sem depender do CDN browser em prod |
| 4.3 | Excluir arquivos obsoletos do shell (`workspace.css`/`workspace-tokens.css`/`workspace_alpine.js` antigos e partials já migrados) | `backend-specialist` | pending | `atendimento_unificado` enxuto, apenas com shell + models canônicos + `realtime_publisher.py` |

**Commit Checkpoint**
`git commit -m "chore: cleanup unified workspace legacy files and set tailwind prod build"`

## Execution History

> Last updated: 2026-05-21 | Progress: ~60%

### phase-1 [IN PROGRESS]
- 1.1, 1.2, 1.3 concluídas (design system criado, settings configurados, tokens base no `core.css`).
- 1.4 pendente: só existe `components/README.html`; componentes genéricos ainda não migrados.

### phase-2 [IN PROGRESS]
- 2.1 concluída: apps `chat_evolution` e `gestao_kanban` criados e registrados no `INSTALLED_APPS`.
- 2.2/2.3 concluídas de forma DIFERENTE do plano: abandonado `managed=False` (commit `db787ca`) em favor de import direto dos models canônicos; services movidos para os apps.
- 2.4 concluída: rotas isoladas sob `chat/api/` e `kanban/api/` (montadas via urls do shell).
- 2.5 pendente: views ainda residem em `atendimento_unificado` (api_urls importam `views_api` de lá).
- 2.6 pendente: confirmar/documentar `atendimento_unificado` como shell.

### phase-3 [IN PROGRESS]
- 3.1 concluída: partials de domínio movidos para os apps.
- 3.2/3.3 iniciadas: `chat_alpine.js`/`kanban_alpine.js` criados porém mínimos; `workspace_alpine.js` ainda monolítico.
- 3.4 pendente: `workspace.css`/`workspace-tokens.css` ainda no shell.

### phase-4 [PENDING]
- Não iniciada (validação, build de produção do Tailwind e limpeza).

## Correções aplicadas

> Mudanças aplicadas nesta reestruturação, cruzando plano original × estado real do código × documentação atual das libs.

1. **Frontmatter:** `progress: 100` → `progress: 60` (o valor original era contraditório, com todas as tasks em `pending`). `status` mantido em `in_progress`. Adicionado campo `status` por fase e `restructured: 2026-05-21`. Removido o agente `test-writer` da execução ativa (projeto não cria testes automatizados ativamente, conforme diretriz do CLAUDE.md).

2. **Status reais das tasks:** Fase 1.1/1.2/1.3, 2.1/2.2/2.3/2.4 e 3.1 marcadas `completed`; 1.4, 3.2, 3.3 marcadas `in_progress`; Fase 4 inteira `pending`. Reflete o estado verificado no código.

3. **Fase 2.2/2.3 — `managed=False` → import canônico:** reescritas de "proxy/`managed=False` com `db_table="atu_*"`" para "import direto dos models canônicos", conforme recomendação oficial do **Django 5.2** (importar o model do app dono em vez de duplicar definição com mesma `db_table`, que quebra `makemigrations`) e conforme o commit **`db787ca`** ("remove duplicate unmanaged models and fix cross-app imports"). `models.py` dos novos apps contém apenas docstring.

4. **Nova task 2.5 (mover views):** adicionada para mover `views_api`/`views_sse`/`selectors` do monolito para `chat_evolution`/`gestao_kanban`, já que os `api_urls` ainda fazem `from atendimento_unificado import views_api`.

5. **Nova task 2.6 (app shell):** decisão registrada de **manter `atendimento_unificado` como shell** (em vez de criar um app `shell` novo), evitando migration churn — ele já é dono da `WorkspaceView`, templates raiz e models canônicos.

6. **Fase 1.4 detalhada:** especificados os componentes genéricos a migrar para `design_system/templates/components/` (button, badge, avatar, modal/panel, spinner, empty_state, dropdown), com critério para distinguir casca visual de partials de domínio.

7. **Fase 3.2/3.3 detalhadas (Alpine.js v3):** quebra do `workspace_alpine.js` via `Alpine.data('chat'/'kanban', ...)` e estado transversal via `Alpine.store('workspace', ...)`, com a armadilha de ordem documentada (registro em `alpine:init`, scripts com `defer`, pós-init em `alpine:initialized`).

8. **Nova task 3.4 + Fase 4.2 (Tailwind v4):** migração de `workspace.css`/`workspace-tokens.css` para `@theme`/`@utility` no `core.css` (v4 abandonou `tailwind.config.js`) e definição de build de produção real (PostCSS `@tailwindcss/postcss` ou CLI), pois o `@tailwindcss/browser@4` usado em `base.html` é dev-only.

9. **Risk Assessment:** REMOVIDO o risco de `managed=False` (não se aplica mais). ADICIONADOS: (a) Tailwind CDN browser dev-only → produção precisa de build; (b) ordem de carregamento do Alpine (componentes não registrados antes do `x-data`). MANTIDO o risco de regressão visual de CSS.

10. **Subtítulo do plano:** explicitado que os "3 apps" são `chat_evolution`, `gestao_kanban` e o shell `atendimento_unificado`.

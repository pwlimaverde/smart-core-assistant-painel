# Plano Completo de Refatoração Modular — Atendimento Unificado

> **Versão 5.0 (2026-05-22)** — Reestruturação do plano v4.0 reconciliada com o **estado real do código (~60%)** e com a **documentação ATUAL** de libs (Django 5.2.7, Alpine.js v3, Tailwind v4, SortableJS) e do serviço externo (Evolution API "Evolution Go" v2.3.7).
>
> Idioma: Português (pt-br). Código e identificadores: Inglês.
> Princípios rígidos: **Multi-Tenant** (`get_current_tenant()`) + **Result Pattern** (`py-return-success-or-error`). **Sem testes automatizados** (validação manual).

---

## ⚠️ Arquitetura Alvo v6.0 — CORRIGIDA (2026-05-22) — VIGENTE

> Esta seção **substitui** o §2 abaixo (que ficou desalinhado). Definida pelo dono
> do projeto após o deploy 1.2.2+017 ter exposto a violação: os models de
> informação ficaram no shell `atendimento_unificado` em vez de no centro.
> Status do plano: **REABERTO** (F2/F3/F5 voltaram a `in_progress`).

### Princípio central

`atendimentos` é o **CENTRO das informações**. Os apps periféricos não detêm
informação de domínio — eles **observam e atualizam o centro via signals** e o
**leem via selectors**.

| App | Papel | Models de informação? |
|-----|-------|------------------------|
| **`atendimentos`** | Centro: toda a informação do atendimento | **SIM** (todos) |
| **`chat_evolution`** | Apenas a estrutura de comunicação com o contato (Evolution/mensageria) | **NÃO** — atualiza o centro por signals |
| **`gestao_kanban`** | Apenas manipulação de cards (lê o centro) | **NÃO** (salvo algo que seja exclusivo de card e não exista no centro) |
| **`trello_sync`** | Sincroniza Trello | **NÃO** — atualiza o centro por signals (padrão `@receiver(post_save, sender=Atendimento/...)` já existente) |
| **`atendimento_unificado`** | Apenas a **ponte/UI** que une a visualização de chat + kanban | **NÃO** — só `WorkspaceView`, templates, `views_sse` (SSE único), `realtime_publisher`, `feature_flags` |

### Destino de cada model `atu_*` (hoje no shell — a corrigir)

| Model atual (shell) | Decisão | Destino |
|---------------------|---------|---------|
| `CampoPersonalizado` | mover (não existe no centro) | **`atendimentos`** |
| `ValorCampoAtendimento` | mover (não existe no centro) | **`atendimentos`** |
| `Nota` | mover (não existe no centro) | **`atendimentos`** |
| `Etiqueta` (catálogo cor/descrição) | mover (catálogo é "info que falta") | **`atendimentos`** ✅ |
| `EtiquetaAtendimento` (aplicação) | **manter o model** (decisão do dono: "etiqueta mantém em atendimento") | **`atendimentos`** ✅ (state-only, dados preservados) |
| `LeituraAtendimento` (não-lido por atendente) | **eliminar** → `Mensagem.lido` (sem multiatendente, confirmado) | **dropado** (audit log; não-lidos já usavam `Mensagem.lido`) ✅ |

> **Resolvido (2026-05-22):** sem multiatendente, `Mensagem.lido` (global) cobre os
> não-lidos. `LeituraAtendimento` era só audit log "quem leu por último" — removido.
> Etiquetas mantêm catálogo + aplicação como models (em `atendimentos`).

### Comunicação cross-app

- **Sem import direto** entre `chat_evolution` e `gestao_kanban` (mantém §2.4).
- Periféricos → centro via **Django signals** (`post_save`/`post_delete` em models de
  `atendimentos`), espelhando o padrão de `trello_sync`.
- Leitura do centro via **selectors** dos apps (consultam `atendimentos.models`).

### Plano de migração (PRODUÇÃO — tabelas `atu_*` já populadas no deploy 1.2.2+017)

1. **Mover `state` sem tocar dados** (`SeparateDatabaseAndState`, `database_operations=[]`)
   para `atu_campo_personalizado`, `atu_valor_campo`, `atu_nota`, `atu_etiqueta`:
   tabelas permanecem, muda só o `app_label` (shell → `atendimentos`).
2. **Migração de DADOS + drop** para os reaproveitados:
   - `atu_etiqueta_atendimento` → popular `Atendimento.tags` a partir das aplicações
     existentes; depois `DROP TABLE`.
   - `atu_leitura_atendimento` → (se confirmado) reconciliar com `Mensagem.lido`;
     depois `DROP TABLE`.
   - **Backup/validação obrigatórios** antes do drop em produção.
3. Atualizar imports (`selectors`/`services`/`views_api`) para `atendimentos.models`.
4. Mover `tenant_admin` desses models para `atendimentos`.
5. Reescrever a lógica de etiquetas/não-lidos para o novo modelo (tags/lido) — afeta
   `selectors`, `services`, `views_api`, JS e templates.

### Impacto (arquivos)

- Backend: `atendimentos/models.py` (+models), `atendimentos/migrations/*` (state + dados),
  `chat_evolution/{selectors,services,signals}.py`, `gestao_kanban/{selectors,services,views_api}.py`,
  `atendimento_unificado/{models,tenant_admin}.py` (esvaziar).
- Frontend: partials/JS que usam etiquetas coloridas e contadores de não-lido.

### Pendências de decisão — RESOLVIDAS (2026-05-22)

- [x] Aplicação de etiqueta: **manter `EtiquetaAtendimento`** (model), em `atendimentos`.
- [x] Não-lido: **reaproveitar `Mensagem.lido`** (sem multiatendente); `LeituraAtendimento` eliminado.

### Status da implementação (2026-05-22)

✅ Implementado: 5 models movidos para `atendimentos` (state-only, tabelas `atu_*`
preservadas); `LeituraAtendimento` dropado; `mark_read` usa `Mensagem.lido`; imports
e `tenant_admin` realocados; shell esvaziado. Validado: `makemigrations --check`
(sem mudanças), `manage.py check` (0 issues), `pyright` (0 erros), `ruff` (limpo no
código novo). Deploy: a aplicar (`migrate` roda as migrations state-only + drop).

---

## Frontmatter sugerido — Fases PREVC (para transcrever ao plano canônico)

```yaml
fases:
  - id: F1
    name: "Design System — componentes genéricos + core_alpine.js + tokens (Tailwind v4)"
    prevc: E
    agent: frontend-specialist
    status: in_progress     # estrutura+settings+core.css base feitos; componentes e core_alpine.js pendentes
  - id: F1V
    name: "Validação Design System — render sem regressão no shell atual"
    prevc: V
    agent: code-reviewer
    status: pending
  - id: F2
    name: "chat_evolution — mover views_api/views_sse/selectors/signals do monolito + templates + chat.css + chat_alpine.js"
    prevc: E
    agent: backend-specialist
    status: in_progress     # api_urls/services/partials existem; views ainda importadas do monolito
  - id: F2V
    name: "Validação chat_evolution — endpoints /workspace/chat/api/ e Evolution send/markRead/presence"
    prevc: V
    agent: code-reviewer
    status: pending
  - id: F3
    name: "gestao_kanban — mover views_api/selectors/signals do monolito + templates + kanban.css + SortableJS"
    prevc: E
    agent: backend-specialist
    status: in_progress     # api_urls/services/partials existem; views ainda importadas do monolito
  - id: F3V
    name: "Validação gestao_kanban — endpoints /workspace/kanban/api/ + drag-drop sincronizado"
    prevc: V
    agent: code-reviewer
    status: pending
  - id: F4
    name: "Integração UI Shell — workspace_coordinator.js + ordem de assets + reduzir workspace_alpine.js"
    prevc: E
    agent: frontend-specialist
    status: pending
  - id: F4V
    name: "Validação integração — eventos cross-app (card:clicked / chat:closed) e SSE único"
    prevc: V
    agent: architect-specialist
    status: pending
  - id: F5
    name: "Limpeza do monolito — remover views_api/views_sse/selectors/partials/css/js migrados"
    prevc: E
    agent: backend-specialist
    status: pending
  - id: F6
    name: "Build de produção Tailwind v4 (CLI/PostCSS) + validação final + deploy"
    prevc: V
    agent: code-reviewer
    status: pending
```

---

## 1. Contexto e Motivação

O app monolítico `atendimento_unificado` acumulou responsabilidades de domínios distintos (chat WhatsApp via Evolution + pipeline Kanban). Objetivo: separar em **quatro pilares**, transição não-destrutiva.

- **app `chat_evolution`** — Django app: mensageria/Evolution.
- **app `gestao_kanban`** — Django app: quadros/cards/campos/etiquetas/notas.
- **shell `atendimento_unificado`** — Django app residual: `WorkspaceView`, templates raiz, **models canônicos NÃO ficam aqui** (ver §2), migrations, `services/realtime_publisher.py`, `views_sse.py` (SSE único), `feature_flags.py`.
- **módulo `modules/design_system`** — **NÃO é app Django**; visível via `STATICFILES_DIRS` + `TEMPLATES[0]["DIRS"]`.

---

## 2. Arquitetura Alvo (reconciliada com o código real)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          atendimento_unificado (UI Shell)                    │
│  WorkspaceView · workspace.html · base_workspace.html                        │
│  views_sse.workspace_events  →  /workspace/events/   (SSE ÚNICO por tenant)  │
│  services/realtime_publisher.publish_event  →  canal  sse:{tenant_slug}:events│
│                                                                              │
│  ┌──────────────────────────────┐   ┌───────────────────────────────────┐   │
│  │        chat_evolution        │   │          gestao_kanban            │   │
│  │ API: /workspace/chat/api/    │   │ API: /workspace/kanban/api/       │   │
│  │ services/{message,media}_…   │   │ services/{board,card_renderer,    │   │
│  │ templates/chat_evolution/    │   │   etiquetas,notas,transfer_fluxo} │   │
│  │ static/chat_evolution/       │   │ templates/gestao_kanban/          │   │
│  └──────────────┬───────────────┘   └──────────────────┬────────────────┘   │
│                 │   import canônico de atendimentos.models                   │
│  ┌──────────────▼──────────────────────────────────────▼─────────────────┐  │
│  │                         modules/design_system                          │  │
│  │  core.css (Tailwind v4 @theme/@utility)  ·  core_alpine.js (stores)    │  │
│  │  templates/components/ (button, badge, modal_base, …)                  │  │
│  └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Roteamento REAL (verdade do código)

`atendimento_unificado/urls.py` (montado pelo projeto sob `/workspace/`) já faz:

```python
path("api/",        include(("...atendimento_unificado.api_urls", "atendimento_unificado_api"))),
path("chat/api/",   include(("...chat_evolution.api_urls",        "chat_evolution_api"))),
path("kanban/api/", include(("...gestao_kanban.api_urls",         "gestao_kanban_api"))),
path("events/",     views_sse.workspace_events, name="workspace_events"),
```

➡️ **Prefixos canônicos: `/workspace/chat/api/`, `/workspace/kanban/api/`, `/workspace/events/`.**
O plano v4.0 falava em `/chat/`, `/kanban/` na raiz e `/chat/events/` + `/kanban/events/` — **descartado**. Reflita o estado real. Mudança para raiz só se houver decisão futura explícita (não há).

### 2.2 Models — IMPORT CANÔNICO (decisão tomada, commit `db787ca`)

- Models canônicos vivem em **`atendimentos.models`** (`Atendimento`, `Mensagem`, `MovimentoFluxo`, etc.) — confirmado em `atendimento_unificado/signals.py`. O `models.py` dos novos apps é **docstring-only** e importa de lá.
- **PROIBIDO** reintroduzir `managed=False`/`db_table="atu_*"`/proxy para cross-app. `makemigrations` quebra com tabelas duplicadas. `proxy=True` só para estender comportamento; `managed=False` só para banco legado — nenhum dos dois se aplica aqui.

```python
# chat_evolution/selectors.py — padrão correto
from smart_core_assistant_painel.app.atendimentos.models import Atendimento, Mensagem
```

### 2.3 SSE — canal ÚNICO por tenant (verdade do código)

- **NÃO há** canais `sse:{tenant}:chat` / `sse:{tenant}:kanban` separados. Existe **um canal** `sse:{tenant_slug}:events` (`feature_flags.get_sse_channel`) e **um endpoint** `/workspace/events/` (`views_sse.workspace_events`).
- Publicação via `services/realtime_publisher.publish_event(...)`, payload `{type, data, tenant_slug}`. O cliente faz **um EventSource** e roteia por `event:` (`payload.type`).
- A view é **sync-stub + delegação async** sob flag `ATENDIMENTO_UNIFICADO_SSE_ENABLED` — porque sob **Gunicorn sync (WSGI)** um `async generator` em `StreamingHttpResponse` trava o worker até timeout/SIGKILL. Só habilitar SSE real com `uvicorn.workers.UvicornWorker` (ASGI). O `async generator` já trata `asyncio.CancelledError`, faz heartbeat `: ping\n\n` a cada 25s e seta `X-Accel-Buffering: no`.
- ➡️ **Mantenha o SSE único no shell.** Os apps filhos **não** criam `views_sse.py` próprio; eles apenas **diferenciam o `type`** ao publicar (`chat.message`, `chat.read`, `kanban.card_moved`, `kanban.card_assigned`, …). Isto corrige o plano v4.0 (que duplicaria SSE).

### 2.4 Comunicação cross-app

- **Backend**: Django signals. `@receiver(post_save, sender=...)` em `signals.py` de cada app, registrado em `AppConfig.ready()` importando o módulo (padrão já usado no shell). Zero import entre `chat_evolution` e `gestao_kanban`.
- **Frontend**: eventos Alpine. `$dispatch('card:clicked', {...})` / `$dispatch('chat:closed', {...})` com `.window` para componentes distantes; o `workspace_coordinator.js` escuta e re-despacha.

---

## 3. Estado Atual REAL (auditado no código)

### `atendimento_unificado` — shell funcional (monolito)
| Categoria | Existente |
|-----------|-----------|
| Backend | `models.py`, `views.py`, `views_api.py`, `views_sse.py` (SSE único async/WSGI-safe), `selectors.py`, `api_urls.py`, `urls.py`, `services/realtime_publisher.py`, `signals.py` (ready() OK), `feature_flags.py`, `admin.py`, `tenant_admin.py`, `tasks.py`, migrations |
| Frontend CSS | `static/atendimento_unificado/css/workspace.css`, `workspace-tokens.css` |
| Frontend JS | `static/atendimento_unificado/js/workspace_alpine.js` (monolítico) |
| Templates | `workspace.html`, `base_workspace.html`, `workspace_disabled.html`, `partials/{chat_drawer,conversation_item,focus_segmented}.html` |

### `chat_evolution` — backend parcial
| Item | Status | Detalhe |
|------|--------|---------|
| `models.py` | ✅ docstring-only (import canônico) | **NÃO** mexer / NÃO reintroduzir managed=False |
| `services/` | ✅ | `message_dispatch_service.py`, `media_dispatch_service.py` |
| `api_urls.py` | ⚠️ existe mas **importa `views_api` do monolito** | endpoints: `conversations/`, `.../messages/`, `.../detail/`, `.../send/`, `.../mark-read/`, `.../presence/`, `.../upload/`, `.../medias/`, `notifications/unread-count/` |
| `apps.py` | ✅ (sem `ready()` ainda) | falta carregar `signals` |
| `static/.../js/chat_alpine.js` | ⚠️ mínimo | não conectado aos endpoints finais |
| `templates/.../partials/` | ⚠️ parcial | `chat_message.html`, `chat_mini_bar.html` |
| `views_api.py` / `views_sse.py` / `selectors.py` / `signals.py` | ❌ | a criar/mover |
| `static/.../css/chat.css` | ❌ | a criar |

### `gestao_kanban` — backend parcial
| Item | Status | Detalhe |
|------|--------|---------|
| `models.py` | ✅ docstring-only (import canônico) | idem |
| `services/` | ✅ | `board_service.py`, `card_renderer.py`, `etiquetas_service.py`, `notas_service.py`, `transfer_fluxo_service.py` |
| `api_urls.py` | ⚠️ existe mas **importa `views_api` do monolito** | endpoints: `fluxos/`, `board/`, `board/move/`, `board/assign/`, `board/transfer-fluxo/`, `.../custom-fields/<slug>/`, `export/`, `etiquetas/`, `.../etiquetas/`, `.../etiquetas/<id>/toggle/`, `.../notas/`, `.../notas/<id>/`, `.../timeline/` |
| `apps.py` | ✅ (sem `ready()`) | falta carregar `signals` |
| `static/.../js/kanban_alpine.js` | ⚠️ mínimo | falta SortableJS conectado |
| `templates/.../partials/` | ⚠️ parcial | `custom_fields_panel.html`, `detail_panel.html`, `kanban_card.html`, `kanban_column.html` |
| `views_api.py` / `selectors.py` / `signals.py` | ❌ | a criar/mover |
| `static/.../css/kanban.css` | ❌ | a criar |

### `modules/design_system` — esqueleto
| Item | Status |
|------|--------|
| `static/css/core.css` | ✅ tokens base |
| Config `settings.py` (STATICFILES_DIRS + TEMPLATES DIRS) | ✅ |
| `templates/components/` | ⚠️ só `README.html` |
| `static/js/core_alpine.js` | ❌ |

---

## 4. Fases PREVC

Cada fase E (execução) tem fase V (validação) emparelhada. Validação é **manual** (sem testes automatizados).

---

### FASE 1 (E) — Design System · `frontend-specialist` · status: in_progress

**Objetivo**: componentes HTML genéricos + `core_alpine.js` + consolidar tokens em `core.css` no padrão **Tailwind v4 CSS-first**.

**1.1 — Consolidar tokens em `core.css` (Tailwind v4)**
`modules/design_system/static/css/core.css`. CSS-first: **sem `tailwind.config.js`**, **sem** `@tailwind base/components/utilities` (legado). Tokens em `@theme` viram **variáveis CSS + utilities automáticas**:

```css
@import "tailwindcss";

@theme {
  --color-brand-500: #1d4ed8;
  --color-chat-bubble-in: #ffffff;
  --color-chat-bubble-out: #d9fdd3;
  --color-kanban-col-bg: #f1f5f9;
  --spacing-drawer: 22rem;
  --font-sans: "Inter", system-ui, sans-serif;
}

/* utilities customizadas (substitui @layer utilities do v3) */
@utility scrollbar-thin {
  scrollbar-width: thin;
}

/* componentes ainda válidos em v4 */
@layer components {
  .ds-card { @apply rounded-lg bg-white shadow-sm; }
}
```

Migrar variáveis de `workspace-tokens.css` para `@theme`; remover duplicatas. **Não deletar** `workspace-tokens.css` ainda (Fase 5).

**1.2 — Componentes em `modules/design_system/templates/components/`**
`button.html`, `badge.html`, `modal_base.html`, `input_text.html`, `avatar.html`, `spinner.html`, `toast.html`, `drawer_base.html`, `empty_state.html` (params via `{% include with %}`). Agnósticos: sem regras de chat/kanban.

**1.3 — `core_alpine.js` (registro em `alpine:init`)**
`modules/design_system/static/js/core_alpine.js`. **Tudo que é `Alpine.data` / `Alpine.store` / `Alpine.directive` registra-se DENTRO de `document.addEventListener('alpine:init', …)`** (dispara antes do parse do DOM). Código pós-init (ex.: instanciar libs) vai em `alpine:initialized`.

```js
document.addEventListener('alpine:init', () => {
  Alpine.store('notifications', {
    items: [],
    push(t, msg) { const id = crypto.randomUUID(); this.items.push({ id, type: t, msg });
      setTimeout(() => this.dismiss(id), 4000); },
    dismiss(id) { this.items = this.items.filter(i => i.id !== id); },
  });
  Alpine.store('modal', {
    open: false, name: null, payload: null,
    show(name, payload = null) { this.name = name; this.payload = payload; this.open = true; },
    close() { this.open = false; this.name = null; this.payload = null; },
  });
  Alpine.directive('format-date', (el, { expression }, { evaluate }) => {
    const v = evaluate(expression);
    el.textContent = formatRelative(v);
  });
});

export function formatPhone(n) {            // BR: +55 (11) 91234-5678
  const d = String(n).replace(/\D/g, '');
  const m = d.match(/^55?(\d{2})(\d{4,5})(\d{4})$/);
  return m ? `+55 (${m[1]}) ${m[2]}-${m[3]}` : n;
}
export function debounce(fn, delay = 300) {
  let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), delay); };
}
```

> **Armadilha de ordem (defer)**: scripts de módulo que registram `Alpine.data/store/directive` DEVEM carregar **antes/junto** do core do Alpine, senão `alpine:init` já passou e o registro **falha silenciosamente**. Ordem definida na Fase 4.4.

**Commit**: `chore(ui): expand design system with base components and alpine helpers`

### FASE 1 (V) — `code-reviewer` · pending
- `core.css` compila (Tailwind v4) e o shell atual renderiza sem regressão visual.
- `core_alpine.js` carregado: `$store.notifications` / `$store.modal` acessíveis no console; diretiva `x-format-date` funciona.

---

### FASE 2 (E) — chat_evolution completo · `backend-specialist` (+`frontend-specialist`) · status: in_progress

**Objetivo**: **mover** views/SSE-publish/selectors/signals do monolito para o app, mantendo prefixo `/workspace/chat/api/`.

**2.1 — `selectors.py`** (`chat_evolution/selectors.py`)
Import canônico de `atendimentos.models`. Queries de leitura, filtradas por tenant (`get_current_tenant()`), retornando via Result Pattern quando expostas a service. Ex.: `get_conversas_ativas`, `get_historico_mensagens` (cursor), `get_contato_detalhes`, `get_nao_lidos_por_conversa`.

**2.2 — `signals.py`** (`chat_evolution/signals.py`) + `apps.py.ready()`
`@receiver(post_save, sender=Mensagem)` → publica via `realtime_publisher.publish_event` no canal **único** com `type="chat.message"` (e `chat.read` para leitura). Registrar em `ready()`:

```python
class ChatEvolutionConfig(AppConfig):
    name = "smart_core_assistant_painel.app.chat_evolution"
    def ready(self) -> None:
        try:
            from . import signals  # noqa: F401
        except Exception as exc:
            from loguru import logger
            logger.warning("Falha ao carregar sinais chat_evolution: {}", exc)
```

**2.3 — `views_api.py`** (`chat_evolution/views_api.py`)
**Mover** as classes hoje em `atendimento_unificado.views_api` que correspondem ao chat, **preservando os nomes já roteados** em `chat_evolution/api_urls.py`:
`ConversationsListView`, `ConversationMessagesView`, `ConversationDetailView`, `ConversationSendView`, `ConversationMarkReadView`, `ConversationPresenceView`, `ConversationUploadView`, `ConversationMediasView`, `NotificationsUnreadCountView`.
Multi-tenant + Result Pattern. **Integração Evolution Go v2.3.7** (via `message_dispatch_service` / `media_dispatch_service`) — ver §5.

**2.4 — SSE: NÃO criar `views_sse.py` no app**
Reusar o endpoint único `/workspace/events/`. Apenas garantir que os signals publicam `type` com prefixo `chat.*`. O `chat_alpine.js` filtra por `e.type` no único EventSource.

**2.5 — `api_urls.py`**: trocar `from atendimento_unificado import views_api` por `from . import views_api`. URLs e nomes **inalterados**.

**2.6 — Templates** (`chat_evolution/templates/chat_evolution/partials/`)
Já existem `chat_message.html`, `chat_mini_bar.html`. Adicionar: `composer.html`, `conversation_item.html`, `media_viewer.html`, `contact_info_panel.html`, `typing_indicator.html`. Reutilizar componentes do design system (`avatar`, `badge`, `spinner`).

**2.7 — `static/chat_evolution/css/chat.css`**: estilos do chat; tokens vêm de `core.css` (não duplicar `@theme`).

**2.8 — `chat_alpine.js`**: `Alpine.data('chat', …)` dentro de `alpine:init`; `fetch` para `/workspace/chat/api/...`; um `EventSource('/workspace/events/')` com `addEventListener('chat.message', …)` / `'chat.read'`.

**Commit**: `refactor(chat): move chat views/selectors/signals into chat_evolution`

### FASE 2 (V) — `code-reviewer` · pending
- `/workspace/chat/api/conversations/` etc. respondem sem importar nada do monolito.
- Envio de texto/mídia chega no WhatsApp; mark-read **explícito** (sem ticks azuis automáticos); presença "digitando" aparece.
- `manage.py makemigrations --check` sem migrations novas (models não tocados).

---

### FASE 3 (E) — gestao_kanban completo · `backend-specialist` (+`frontend-specialist`) · status: in_progress

**Objetivo**: mover views/selectors/signals do kanban, prefixo `/workspace/kanban/api/`.

**3.1 — `selectors.py`**: `get_snapshot_board` (`select_related`/`prefetch_related`), `get_card_detalhes`, `get_fluxos_por_tenant`, `get_timeline_card`. Tenant-scoped.

**3.2 — `signals.py`** + `apps.py.ready()`: `@receiver(post_save, sender=MovimentoFluxo)` (e Atendimento) → `publish_event` com `type="kanban.card_moved"`, `kanban.card_assigned`, `kanban.custom_field_updated`. Mesmo padrão `ready()` da 2.2.

**3.3 — `views_api.py`**: mover do monolito preservando nomes roteados:
`FluxosListView`, `BoardSnapshotView`, `BoardMoveView`, `BoardAssignView`, `BoardTransferFluxoView`, `CustomFieldPatchView`, `ExportView`, `EtiquetasListView`, `ConversationEtiquetasView`, `ConversationEtiquetaToggleView`, `ConversationNotasView`, `ConversationNotaDeleteView`, `ConversationTimelineView`. Lógica `tipo_etapa` no `BoardMoveView`. Result Pattern via `board_service`/`transfer_fluxo_service`.

**3.4 — SSE**: idem 2.4 — sem `views_sse.py` próprio; publicar `type="kanban.*"` no canal único.

**3.5 — `api_urls.py`**: trocar import do monolito por `from . import views_api`. URLs inalteradas.

**3.6 — Templates**: já há `kanban_card.html`, `kanban_column.html`, `detail_panel.html`, `custom_fields_panel.html`. Adicionar: `kanban_board.html`, `etiquetas_panel.html`, `notas_panel.html`, `transfer_modal.html` (usar `modal_base.html` do design system).

**3.7 — `static/gestao_kanban/css/kanban.css`**: colunas, cards, estados drag-over, handles. Tokens de `core.css`.

**3.8 — `kanban_alpine.js` + SortableJS**:
`Alpine.data('kanban', …)` em `alpine:init`; instanciar `Sortable` em `alpine:initialized` (ou `init()`) sobre `$refs`. **Sincronizar o array reativo** após `onEnd` — a reordenação do DOM pelo Sortable dessincroniza o array do `x-for`:

```js
document.addEventListener('alpine:initialized', () => {
  document.querySelectorAll('[data-kanban-col]').forEach((col) => {
    new Sortable(col, {
      group: { name: 'board', pull: true, put: true },
      animation: 150, handle: '.card-handle', ghostClass: 'opacity-40',
      onEnd: (evt) => {
        const data = Alpine.$data(col);
        // re-sincroniza o array reativo com a nova ordem do DOM
        const moved = data.cards.splice(evt.oldIndex, 1)[0];
        data.cards.splice(evt.newIndex, 0, moved);
        fetch('/workspace/kanban/api/board/move/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': data.csrf },
          body: JSON.stringify({ card_id: moved.id, to_column: evt.to.dataset.column, position: evt.newIndex }),
        });
      },
    });
  });
});
```

**Commit**: `refactor(kanban): move kanban views/selectors/signals into gestao_kanban`

### FASE 3 (V) — `code-reviewer` · pending
- `/workspace/kanban/api/...` sem import do monolito; drag-drop persiste e o array reativo permanece sincronizado; etiquetas/notas/campos custom/transfer cross-board OK; `makemigrations --check` limpo.

---

### FASE 4 (E) — Integração UI Shell · `frontend-specialist` · status: pending

**4.1 — `workspace.html`**: substituir blocos inline por `{% include "chat_evolution/partials/..." %}` e `{% include "gestao_kanban/partials/kanban_board.html" %}`. Shell só define layout macro.

**4.2 — `workspace_coordinator.js`** (`atendimento_unificado/static/.../js/`):
Só roteia eventos (sem lógica de domínio). Escuta `card:clicked` (kanban) → abre chat; `chat:closed` → atualiza seleção do kanban; gerencia sidebar; usa stores `notifications`/`modal` do design system. Usar `.window` nos `@listen`:

```js
document.addEventListener('alpine:init', () => {
  Alpine.data('workspaceCoordinator', () => ({
    selectedCardId: null,
    init() {
      window.addEventListener('card:clicked', (e) => {
        this.selectedCardId = e.detail.cardId;
        this.$dispatch('chat:open', { atendimentoId: e.detail.atendimentoId });
      });
      window.addEventListener('chat:closed', () => { this.selectedCardId = null; });
    },
  }));
});
```

**4.3 — Reduzir `workspace_alpine.js`**: remover lógica de chat (→ `chat_alpine.js`) e kanban (→ `kanban_alpine.js`); manter só layout + bridge ao coordinator.

**4.4 — Ordem de assets em `base_workspace.html`** (corrige armadilha defer do Alpine):
1. `design_system/css/core.css`
2. `chat_evolution/css/chat.css`
3. `gestao_kanban/css/kanban.css`
4. `design_system/js/core_alpine.js`
5. `chat_evolution/js/chat_alpine.js`
6. `gestao_kanban/js/kanban_alpine.js`
7. `atendimento_unificado/js/workspace_coordinator.js`
8. **SortableJS**
9. **Alpine core por último** (com `defer`) — só depois de todos os `alpine:init` listeners estarem registrados. Carregar Alpine antes dos módulos faz `alpine:init` disparar sem os registros → falha silenciosa.

**Commit**: `refactor(shell): integrate modular apps into workspace coordinator`

### FASE 4 (V) — `architect-specialist` · pending
- Zero import cruzado `chat_evolution`↔`gestao_kanban`. Um único `EventSource('/workspace/events/')` roteando `chat.*`/`kanban.*`. Clicar card abre chat correto; sem JS errors; sem requests duplicados.

---

### FASE 5 (E) — Limpeza do monolito · `backend-specialist` · status: pending

Só após F4 validada. Remover de `atendimento_unificado`: classes de chat/kanban em `views_api.py`; queries migradas em `selectors.py`; partials migrados; estilos de chat/kanban em `workspace.css`/`workspace-tokens.css`; lógica migrada em `workspace_alpine.js`.
**Manter**: `WorkspaceView`, `views_sse.py` (SSE único), `services/realtime_publisher.py`, `signals.py` do shell, `feature_flags.py`, migrations, `api_urls.py` do shell. Buscar referências a `workspace_alpine` antes de cortar.
**Commit**: `chore(cleanup): remove migrated chat and kanban logic from atendimento_unificado`

---

### FASE 6 (V) — Build de produção Tailwind v4 + Validação final + Deploy · `code-reviewer` · status: pending

**6.1 — Build de produção do Tailwind v4 (corrige CDN dev-only)**
`@tailwindcss/browser` (CDN, hoje em `core/templates/base.html`) **é DEV-ONLY** (compila no browser, sem purge). Produção exige CSS estático gerado:

```bash
# CLI v4 — gera CSS purgado para staticfiles
npx @tailwindcss/cli -i core.css -o static/css/core.build.css --minify
# ou via @tailwindcss/postcss no pipeline de build (sem autoprefixer/postcss-import — desnecessários no v4)
```

Servir o CSS estático via `collectstatic`; remover a tag do CDN do `base.html` em produção.

**6.2 — Checklist de validação manual**
- Backend: nenhuma rota de chat/kanban aponta para views do shell; SSE único entrega `chat.*`/`kanban.*` em tempo real (sob worker ASGI / `ATENDIMENTO_UNIFICADO_SSE_ENABLED=True`); `migrate --check` limpo; pyright sem erros nos novos apps.
- Frontend: chat texto/mídia/áudio; mark-read explícito sem ticks automáticos (`readMessages=false`); kanban drag-drop com array sincronizado; campos/etiquetas/notas; transfer cross-board; coordinator abre chat correto.
- Multi-tenant: troca de tenant não vaza dados; SSE de um tenant não aparece em outro (canal `sse:{slug}:events` + filtro defense-in-depth por `tenant_slug`).

**Deploy**: `uv run task server-deploy` (com `-p smart-core-app`/`-p smart-core-workers`), env `SMARTCORE_ENV_FILE=.env.prod --env-file .env.prod`.

---

## 5. Integração Evolution API "Evolution Go" v2.3.7 (técnica)

Server `http://76.13.229.210:8080` (em produção via `tenants_tenantevolution.server_url`), instância `atendimento` (UUID `3bb88a86-b965-4a30-8164-91d47877aad4`). Credenciais por tenant (NÃO env). Header `apikey` (**token da instância** p/ `/message`,`/chat`; **token global** p/ `/instance`). `Content-Type: application/json`.

| Ação | Método/Rota | Body essencial | Observação |
|------|-------------|----------------|------------|
| Texto | `POST /message/sendText/{instance}` | `{number, text, delay, quoted}` | 201 → `key.id` |
| Mídia | `POST /message/sendMedia/{instance}` | `{number, mediatype: image\|video\|document\|audio, mimetype, media, fileName, caption}` | **>3MB ⇒ usar URL** (base64 dá 500); base64 **sem** prefixo `data:` |
| Áudio (ptt) | `POST /message/sendWhatsAppAudio/{instance}` | `{number, audio, encoding}` | `encoding=true` base64 / `false` URL |
| Marcar lido | `PUT /chat/markMessageAsRead/{instance}` | `{read_messages:[{remoteJid, fromMe:false, id:<key.id>}]}` | **EXPLÍCITO** — só após resposta/abertura |
| Presença | `POST /chat/sendPresence/{instance}` | `{number, delay, presence: composing\|recording}` | |
| Advanced settings | `PUT /instance/{instance_id}/advanced-settings` | `{readMessages:false}` | **CRÍTICO**: `true` ⇒ ticks azuis automáticos no protocolo |

- **Webhook** `messages.upsert`: `webhookBase64:false` (true gera payload >50MB que crasha Gunicorn). Payload: `data.key.{id,remoteJid,fromMe}`, `data.pushName`, `data.message.{conversation|imageMessage|audioMessage}`.
- **Limites**: rate ~10–20 msg/min ⇒ fila com delay ≥3s. base64 máx ~3MB. Stream pode morrer (503) com container Up ⇒ healthcheck `/instance/fetchInstances` `connectionStatus:"open"`. Retry com backoff no download de mídia (403 transitório — commit `1d8e74a`).
- **Result Pattern**: `message_dispatch_service`/`media_dispatch_service` retornam sucesso/erro tipado; `error` em Parameters é o TYPE (classe), não instância.

---

## 6. Riscos e Mitigações

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| Reintroduzir `managed=False`/proxy cross-app | Baixa | Alta | **Proibido**; usar import canônico de `atendimentos.models`; `makemigrations --check` |
| Alpine registra fora de `alpine:init` (defer) | Média | Média | Ordem 4.4: módulos antes do core Alpine |
| SortableJS dessincroniza `x-for` | Média | Média | `splice` no array reativo no `onEnd` |
| CDN Tailwind em produção (sem purge) | Alta | Média | Build CLI/PostCSS estático (Fase 6.1) |
| SSE async sob Gunicorn sync trava worker | Alta | Alta | Sync-stub + flag; SSE real só sob UvicornWorker |
| Mídia base64 >3MB ⇒ 500 Evolution | Média | Média | Enviar via URL acima de 3MB |
| Tick azul automático indevido | Média | Média | `readMessages=false` + markRead explícito |
| Regressão CSS ao dividir workspace.css | Média | Média | Migrar em paralelo; deletar só na Fase 5 |

---

## 7. Dependências entre Fases

```
F1 (E) → F1V → F2 (E) ─┐
                       ├─ F2V ┐
              F3 (E) ──┘      ├→ F4 (E) → F4V → F5 (E) → F6 (V/deploy)
                       F3V ───┘
```
F2 e F3 paralelizáveis após F1V.

---

## 8. Correções aplicadas (o que mudou, por quê, fonte)

| # | Mudança | Motivo | Fonte |
|---|---------|--------|-------|
| 1 | Prefixos de rota para `/workspace/chat/api/`, `/workspace/kanban/api/`, `/workspace/events/` (não `/chat/`,`/kanban/` na raiz) | Reconciliar com o código real (`atendimento_unificado/urls.py`) | Código atual; instrução de reconciliação |
| 2 | **SSE único** (`sse:{tenant_slug}:events` + `/workspace/events/`), apps publicam `type` `chat.*`/`kanban.*`; sem `views_sse.py` por app | O código tem canal/endpoint únicos; duplicar SSE contradiz o real | `views_sse.py`, `feature_flags.get_sse_channel`, `realtime_publisher` |
| 3 | Remoção de `managed=False`/proxy/`db_table="atu_*"` dos "Princípios" e Riscos → **import canônico** de `atendimentos.models` | Decisão tomada no commit; managed=False quebra makemigrations | commit `db787ca`; Django 5.2.7 (models cross-app) |
| 4 | `models.py` dos novos apps permanecem docstring-only | Estado real; evitar duplicação | `chat_evolution/models.py`, `gestao_kanban/models.py` |
| 5 | Tarefas 2.3/3.3 passam de "criar views" para **mover views do monolito** preservando nomes já roteados | `api_urls.py` já existe importando do monolito | `chat_evolution/api_urls.py`, `gestao_kanban/api_urls.py` |
| 6 | Endpoints renomeados para os nomes reais (`conversations/.../send/`, `board/move/`, etc.) | Alinhar ao roteamento existente | `api_urls.py` ambos os apps |
| 7 | Tailwind v4 **CSS-first** (`@import "tailwindcss"`, `@theme`, `@utility`); remoção de `@tailwind base/...` e `tailwind.config.js` | API v4 atual | Tailwind CSS v4 |
| 8 | Fase 6.1: **build de produção** (CLI/PostCSS); CDN `@tailwindcss/browser` marcado dev-only | CDN não purga; produção exige CSS estático | Tailwind v4; `core/templates/base.html` |
| 9 | Registro de `Alpine.data/store/directive` em `alpine:init`; ordem de assets (módulos antes do core); `alpine:initialized` para libs | Evitar registro silenciosamente falho | Alpine.js v3 |
| 10 | SortableJS: `splice` no array reativo após `onEnd` | Reordenação do DOM dessincroniza `x-for` | SortableJS + Alpine v3 |
| 11 | `signals.py` por app registrado em `AppConfig.ready()` | Padrão Django; espelha o shell | Django 5.2.7; `atendimento_unificado/apps.py` |
| 12 | Seção Evolution Go v2.3.7 com rotas/headers/body exatos, `readMessages=false`, `webhookBase64=false`, mídia>3MB via URL, markRead explícito, retry/backoff | Spec atual do serviço | Evolution Go v2.3.7; commits `1d8e74a`, `fd563a0` |
| 13 | Removida menção a "testes automatizados/teste de integração" como tasks; validação é manual | Política do projeto | CLAUDE.md / instrução |
| 14 | SSE documentado como sync-stub + delegação async sob flag (WSGI trava worker; ASGI/UvicornWorker para SSE real) | Comportamento real e limitação WSGI | `views_sse.py`; Django 5.2.7 streaming |
| 15 | Estrutura PREVC (E/V) por fase com agente especialista | Mapeabilidade a agentes | Instrução de estruturação |

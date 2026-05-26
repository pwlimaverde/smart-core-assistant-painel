# Plano de Refatoração Modular — Atendimento Unificado

> **Versão 4.0 (2026-05-22)** — Consolidação dos planos v3.0/v3.1 com estado real de implementação e fases de execução detalhadas.

---

## 1. Contexto e Motivação

O app monolítico `atendimento_unificado` acumulou responsabilidades que pertencem a domínios distintos:

- **Bugs de estado**: SSE do chat (mensagens, composer, leitura) conflitava com SSE do kanban (drag-drop, movimentação, `tipo_etapa`).
- **UX degradada**: tudo numa view única gerou latência e complexidade visual desnecessária.
- **Frontend intratável**: `workspace_alpine.js` e `workspace.css` misturam lógicas de chat, kanban e layout em arquivos massivos.
- **Acoplamento visual**: ausência de um local central para componentes reutilizáveis forçou duplicação.

**Objetivo**: separar em **quatro pilares independentes**, transição não-destrutiva (sem quebrar o fluxo principal de atendimento durante a migração).

---

## 2. Arquitetura Alvo

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       atendimento_unificado                              │
│               (UI Shell puro — orquestra layout e eventos globais)       │
│  workspace.html  →  workspace_coordinator.js                             │
│                                                                          │
│  ┌───────────────────────────────┐  ┌──────────────────────────────────┐  │
│  │         chat_evolution        │  │         gestao_kanban            │  │
│  │  • Mensagens / Evolution API  │  │  • Quadros / Cards / Campos      │  │
│  │  • SSE: /chat/events/         │  │  • SSE: /kanban/events/          │  │
│  │  • API: /chat/api/            │  │  • API: /kanban/api/             │  │
│  │  • static/chat_evolution/     │  │  • static/gestao_kanban/         │  │
│  │  • templates/chat_evolution/  │  │  • templates/gestao_kanban/      │  │
│  └──────────────┬────────────────┘  └──────────────────┬───────────────┘  │
│                 │                                      │                  │
│  ┌──────────────▼──────────────────────────────────────▼───────────────┐  │
│  │                          design_system                              │  │
│  │                   (módulo agnóstico — modules/)                     │  │
│  │  core.css (Tailwind + tokens)  •  core_alpine.js (helpers globais)  │  │
│  │  templates/components/ (Button, Modal, Badge, Input, Drawer...)     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Localização dos pilares

| Pilar | Localização | Tipo |
|-------|-------------|------|
| `design_system` | `src/.../modules/design_system/` | Módulo Python simples (sem `apps.py`) |
| `chat_evolution` | `src/.../app/chat_evolution/` | App Django |
| `gestao_kanban` | `src/.../app/gestao_kanban/` | App Django |
| `atendimento_unificado` | `src/.../app/atendimento_unificado/` | App Django (UI Shell residual) |

### Princípios inegociáveis

1. **Design System agnóstico**: vive em `modules/`, não é app Django, não entra em `INSTALLED_APPS`. Django enxerga seus `static/` e `templates/` via `settings.py` (STATICFILES_DIRS e TEMPLATES[0]['DIRS']).
2. **Rotas limpas**: APIs do chat em `/chat/api/` e `/chat/events/`; do kanban em `/kanban/api/` e `/kanban/events/`. Fim do roteamento aninhado sob `/workspace/api/`.
3. **Zero acoplamento cross-app**: `chat_evolution` e `gestao_kanban` não se importam. Comunicação exclusivamente via Django signals (backend) e eventos Alpine (frontend).
4. **Zero alteração em banco legado**: novos apps usam models proxy com `managed = False` e `db_table = "atu_*"` apontando para as tabelas criadas pelas migrations do `atendimento_unificado`.

---

## 3. Estado Atual da Implementação

Esta seção descreve o que **já existe** no código antes de qualquer tarefa nova.

### `atendimento_unificado` — Completo (monolito funcional)

| Categoria | Arquivos existentes |
|-----------|---------------------|
| Backend | `models.py`, `views.py`, `views_api.py`, `views_sse.py`, `selectors.py`, `api_urls.py`, `urls.py`, `services/realtime_publisher.py`, `feature_flags.py`, `admin.py`, `tenant_admin.py`, migrations (4 arquivos) |
| Frontend CSS | `static/atendimento_unificado/css/workspace.css`, `workspace-tokens.css` |
| Frontend JS | `static/atendimento_unificado/js/workspace_alpine.js` |
| Templates | `templates/atendimento_unificado/workspace.html`, `base_workspace.html`, `workspace_disabled.html`, `partials/chat_drawer.html`, `partials/conversation_item.html`, `partials/focus_segmented.html` |

### `chat_evolution` — Backend parcial, frontend presente mas incompleto

| Categoria | Status | Detalhe |
|-----------|--------|---------|
| `models.py` | ✅ Existe | Proxy models com `managed=False` |
| `services/` | ✅ Existe | `message_dispatch_service.py`, `media_dispatch_service.py` |
| `api_urls.py`, `apps.py` | ✅ Existe | Estrutura básica criada |
| `static/.../js/chat_alpine.js` | ✅ Existe | Lógica Alpine presente |
| `views.py` / `views_api.py` | ❌ Falta | Views não criadas |
| `selectors.py` | ❌ Falta | Queries não isoladas |
| `signals.py` | ❌ Falta | Sem publicação SSE própria |
| Templates HTML | ❌ Falta | Nenhum partial migrado |
| `static/.../css/chat.css` | ❌ Falta | Sem CSS próprio |
| Registro em `urls.py` principal | ❌ Falta | Rotas `/chat/` não expostas |

### `gestao_kanban` — Backend parcial, frontend presente mas incompleto

| Categoria | Status | Detalhe |
|-----------|--------|---------|
| `models.py` | ✅ Existe | Proxy models com `managed=False` |
| `services/` | ✅ Existe | `board_service.py`, `card_renderer.py`, `etiquetas_service.py`, `notas_service.py`, `transfer_fluxo_service.py` |
| `api_urls.py`, `apps.py` | ✅ Existe | Estrutura básica criada |
| `static/.../js/kanban_alpine.js` | ✅ Existe | Lógica Alpine presente |
| `views.py` / `views_api.py` | ❌ Falta | Views não criadas |
| `selectors.py` | ❌ Falta | Queries não isoladas |
| `signals.py` | ❌ Falta | Sem publicação SSE própria |
| Templates HTML | ❌ Falta | Nenhum partial migrado |
| `static/.../css/kanban.css` | ❌ Falta | Sem CSS próprio |
| Registro em `urls.py` principal | ❌ Falta | Rotas `/kanban/` não expostas |

### `modules/design_system` — Esqueleto mínimo

| Categoria | Status | Detalhe |
|-----------|--------|---------|
| `static/css/core.css` | ✅ Existe | CSS base presente |
| Configuração no `settings.py` | ✅ Existe | TEMPLATES e STATICFILES mapeados |
| Templates de componentes | ⚠️ Mínimo | Apenas `README.html`, sem componentes reais |
| `static/js/core_alpine.js` | ❌ Falta | Helpers/stores Alpine globais não criados |

---

## 4. Fases de Desenvolvimento

> **Estratégia**: cada fase entrega valor isoladamente e não quebra o fluxo atual. O `atendimento_unificado` fica funcional até a Fase 5.

---

### FASE 1 — Design System: Componentes Visuais Base

**Objetivo**: criar os componentes HTML genéricos reutilizáveis e os helpers Alpine globais, consolidando os tokens CSS já existentes.

**Pré-requisito**: nenhum.  
**Responsável**: `frontend-specialist`.

#### Tarefas

**1.1 — Consolidar tokens CSS em `core.css`**

- Arquivo: `modules/design_system/static/css/core.css`
- Mover variáveis CSS de `workspace-tokens.css` para `core.css` (paleta de cores, fontes, sombras).
- Incluir Tailwind `@tailwind base`, `@tailwind components`, `@tailwind utilities`.
- Remover duplicatas entre os dois arquivos de tokens.
- Validar que o `workspace.css` ainda importa corretamente via `@import` ou referência Django.

**1.2 — Criar componentes HTML genéricos em `templates/components/`**

Criar os seguintes partials em `modules/design_system/templates/components/`:

| Arquivo | Conteúdo |
|---------|---------|
| `button.html` | Botão base com variantes (primary, secondary, danger, ghost). Parâmetros via `with`. |
| `badge.html` | Badge de status com variantes de cor e tamanho. |
| `modal_base.html` | Estrutura base de modal Alpine (backdrop, container, slot de conteúdo). |
| `input_text.html` | Input de texto com label flutuante e estado de erro. |
| `avatar.html` | Avatar de contato com fallback de iniciais. |
| `spinner.html` | Indicador de carregamento. |
| `toast.html` | Notificação temporária (sucesso/erro/info). |
| `drawer_base.html` | Container base para painéis laterais deslizantes. |
| `empty_state.html` | Estado vazio com ícone, título e descrição. |

**1.3 — Criar `core_alpine.js` com helpers globais**

- Arquivo: `modules/design_system/static/js/core_alpine.js`
- Conteúdo obrigatório:
  - Store `Alpine.store('notifications', ...)` — fila de toasts globais.
  - Store `Alpine.store('modal', ...)` — controle de modal global (open/close/payload).
  - Diretiva `x-format-date` — formata datas relativas (ex: "há 5 min").
  - Função utilitária `formatPhone(number)` — formata número de telefone BR.
  - Função `debounce(fn, delay)` — utilitário de debounce.

**1.4 — Validar integração sem regressão**

- Garantir que o `base_workspace.html` do `atendimento_unificado` carrega `core.css` e `core_alpine.js`.
- Navegar no workspace atual e confirmar que nenhum estilo foi quebrado.

**Entregável**: Design System com componentes funcionais e testáveis de forma isolada.  
**Commit**: `chore(ui): expand design system with base components and alpine helpers`

---

### FASE 2 — chat_evolution: Views, APIs e Frontend

**Objetivo**: tornar `chat_evolution` um app Django completo e autossuficiente, expondo suas próprias rotas e servindo seus próprios templates.

**Pré-requisito**: Fase 1 concluída.  
**Responsável**: `backend-specialist` (views/API) + `frontend-specialist` (templates/CSS).

#### Tarefas

**2.1 — Criar `selectors.py`**

- Arquivo: `app/chat_evolution/selectors.py`
- Isolar todas as queries de leitura do chat (atualmente espalhadas em `views.py` do monolito):
  - `get_conversas_ativas(tenant, fluxo_id, filtros)` — lista de conversas com status e última mensagem.
  - `get_historico_mensagens(atendimento_id, cursor, limit)` — histórico paginado com cursor.
  - `get_contato_detalhes(contato_id)` — dados do contato com custom fields.
  - `get_nao_lidos_por_conversa(tenant)` — contagem de não-lidos por atendimento.

**2.2 — Criar `signals.py`**

- Arquivo: `app/chat_evolution/signals.py`
- Signal `nova_mensagem_recebida` — dispara publicação SSE no canal `sse:{tenant}:chat`.
- Signal `mensagem_lida` — atualiza contadores e publica evento de leitura.
- Registrar no `apps.py` via `ready()`.

**2.3 — Criar `views_api.py`**

- Arquivo: `app/chat_evolution/views_api.py`
- Endpoints que serão expostos em `/chat/api/`:

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `conversas/` | GET | Lista conversas ativas com filtros |
| `conversas/<id>/mensagens/` | GET | Histórico paginado (cursor-based) |
| `conversas/<id>/enviar/` | POST | Envia mensagem de texto |
| `conversas/<id>/lido/` | POST | Marca conversa como lida |
| `conversas/<id>/presenca/` | POST | Atualiza indicador de presença (digitando) |
| `conversas/<id>/midia/` | POST | Upload e envio de mídia |
| `conversas/<id>/midias/` | GET | Lista mídias da conversa |
| `contatos/<id>/` | GET | Detalhes do contato |

**2.4 — Criar `views_sse.py`**

- Arquivo: `app/chat_evolution/views_sse.py`
- View SSE que faz streaming do canal `sse:{tenant}:chat` usando o mecanismo existente de `realtime_publisher`.
- Rota: `/chat/events/`

**2.5 — Completar `api_urls.py`**

- Arquivo: `app/chat_evolution/api_urls.py`
- Mapear todos os endpoints de `views_api.py` e `views_sse.py`.
- Usar `app_name = 'chat_evolution'` para namespacing.

**2.6 — Registrar rotas no `urls.py` principal**

- No arquivo de URLs raiz do projeto, adicionar:
  ```python
  path("chat/", include("app.chat_evolution.api_urls", namespace="chat_evolution")),
  ```

**2.7 — Criar templates HTML do chat**

Criar em `app/chat_evolution/templates/chat_evolution/`:

| Arquivo | Conteúdo |
|---------|---------|
| `components/chat_bubble.html` | Balão de mensagem (texto, mídia, áudio) com alinhamento esq/dir conforme remetente. |
| `components/composer.html` | Área de composição com botões de emoji, anexo e gravação de áudio. |
| `components/conversation_item.html` | Item de lista de conversas com avatar, nome, última mensagem e badge de não-lidos. |
| `components/media_viewer.html` | Visualizador de mídias (imagem, vídeo, áudio, documento). |
| `components/contact_info_panel.html` | Painel lateral com dados do contato. |
| `components/typing_indicator.html` | Indicador "digitando..." animado. |

**2.8 — Criar `static/chat_evolution/css/chat.css`**

- Arquivo: `app/chat_evolution/static/chat_evolution/css/chat.css`
- Estilos exclusivos do chat: bolhas de mensagem, composer, scroll do histórico, layout do drawer.
- Não duplicar variáveis CSS — importar tokens do `design_system/core.css`.

**2.9 — Verificar `chat_alpine.js` e conectar aos novos endpoints**

- Arquivo: `app/chat_evolution/static/chat_evolution/js/chat_alpine.js`
- Atualizar todas as chamadas `fetch` para os novos prefixos `/chat/api/`.
- Verificar se a conexão SSE aponta para `/chat/events/`.
- Garantir que os `x-data` components correspondem aos templates criados em 2.7.

**Entregável**: `chat_evolution` completamente funcional em suas próprias rotas, sem depender das views do monolito para o chat.  
**Commit**: `refactor(chat): complete chat_evolution app with views, templates and routes`

---

### FASE 3 — gestao_kanban: Views, APIs e Frontend

**Objetivo**: tornar `gestao_kanban` um app Django completo e autossuficiente.

**Pré-requisito**: Fase 1 concluída (Fase 2 pode rodar em paralelo).  
**Responsável**: `backend-specialist` (views/API) + `frontend-specialist` (templates/CSS).

#### Tarefas

**3.1 — Criar `selectors.py`**

- Arquivo: `app/gestao_kanban/selectors.py`
- Queries de leitura do kanban:
  - `get_snapshot_board(fluxo_id, tenant)` — todos os cards por coluna, otimizado com `select_related`.
  - `get_card_detalhes(atendimento_id)` — card completo com custom fields, etiquetas e notas.
  - `get_fluxos_por_tenant(tenant)` — lista de quadros do tenant.
  - `get_timeline_card(atendimento_id)` — histórico de movimentações do card.

**3.2 — Criar `signals.py`**

- Arquivo: `app/gestao_kanban/signals.py`
- Signal `card_movido` — publica evento SSE no canal `sse:{tenant}:kanban`.
- Signal `card_atribuido` — publica evento de atribuição.
- Signal `campo_custom_atualizado` — publica atualização de campo.
- Registrar no `apps.py` via `ready()`.

**3.3 — Criar `views_api.py`**

- Arquivo: `app/gestao_kanban/views_api.py`
- Endpoints expostos em `/kanban/api/`:

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `fluxos/` | GET | Lista quadros do tenant |
| `fluxos/<id>/board/` | GET | Snapshot completo do quadro |
| `cards/<id>/mover/` | POST | Move card entre colunas (com lógica `tipo_etapa`) |
| `cards/<id>/atribuir/` | POST | Atribui atendente ao card |
| `cards/<id>/transferir/` | POST | Move card para outro quadro (cross-board) |
| `cards/<id>/campos/` | GET/POST | Leitura e escrita de campos personalizados |
| `cards/<id>/etiquetas/` | GET/POST/DELETE | CRUD de etiquetas |
| `cards/<id>/notas/` | GET/POST/DELETE | CRUD de notas |
| `cards/<id>/timeline/` | GET | Histórico de movimentações |
| `cards/exportar/` | GET | Exportação CSV do quadro |

**3.4 — Criar `views_sse.py`**

- Arquivo: `app/gestao_kanban/views_sse.py`
- View SSE que faz streaming do canal `sse:{tenant}:kanban`.
- Rota: `/kanban/events/`

**3.5 — Completar `api_urls.py`**

- Arquivo: `app/gestao_kanban/api_urls.py`
- Mapear todos os endpoints de `views_api.py` e `views_sse.py`.
- Usar `app_name = 'gestao_kanban'` para namespacing.

**3.6 — Registrar rotas no `urls.py` principal**

- Adicionar:
  ```python
  path("kanban/", include("app.gestao_kanban.api_urls", namespace="gestao_kanban")),
  ```

**3.7 — Criar templates HTML do kanban**

Criar em `app/gestao_kanban/templates/gestao_kanban/`:

| Arquivo | Conteúdo |
|---------|---------|
| `components/kanban_board.html` | Container do quadro com colunas side-by-side. |
| `components/kanban_column.html` | Coluna com header (nome, count) e zona de drop. |
| `components/kanban_card.html` | Card com avatar, nome, etiquetas, campos preview, indicador de não-lidos. |
| `components/card_detail_panel.html` | Painel lateral de detalhes do card (notas, campos custom, histórico). |
| `components/custom_fields_panel.html` | Formulário de campos personalizados por tipo (text, select, date, number). |
| `components/etiquetas_panel.html` | Seletor de etiquetas com criação inline. |
| `components/notas_panel.html` | Lista de notas com editor inline. |
| `components/transfer_modal.html` | Modal de transferência de card para outro quadro/atendente. |

**3.8 — Criar `static/gestao_kanban/css/kanban.css`**

- Arquivo: `app/gestao_kanban/static/gestao_kanban/css/kanban.css`
- Estilos do kanban: layout de colunas, cards, estados de drag-over, handles de drag.
- Integração com SortableJS via classes CSS.
- Não duplicar tokens — importar do `design_system/core.css`.

**3.9 — Verificar `kanban_alpine.js` e conectar aos novos endpoints**

- Arquivo: `app/gestao_kanban/static/gestao_kanban/js/kanban_alpine.js`
- Atualizar todas as chamadas `fetch` para os novos prefixos `/kanban/api/`.
- Verificar se a conexão SSE aponta para `/kanban/events/`.
- Garantir inicialização correta do SortableJS com callbacks de atualização de ordem.

**Entregável**: `gestao_kanban` completamente funcional em suas próprias rotas, sem depender das views do monolito para o kanban.  
**Commit**: `refactor(kanban): complete gestao_kanban app with views, templates and routes`

---

### FASE 4 — Integração no UI Shell

**Objetivo**: refatorar o `atendimento_unificado` para orquestrar os dois apps via `{% include %}` e criar o `workspace_coordinator.js` para comunicação cross-app.

**Pré-requisito**: Fases 2 e 3 completamente funcionais em rotas independentes.  
**Responsável**: `frontend-specialist`.

#### Tarefas

**4.1 — Refatorar `workspace.html`**

- Arquivo: `app/atendimento_unificado/templates/atendimento_unificado/workspace.html`
- Substituir os blocos inline de chat e kanban por includes:
  ```django
  {% include "chat_evolution/components/chat_drawer.html" %}
  {% include "gestao_kanban/components/kanban_board.html" %}
  ```
- O arquivo deve definir apenas o layout macro (sidebar, header, área de conteúdo) e incluir os componentes dos apps filhos.

**4.2 — Criar `workspace_coordinator.js`**

- Arquivo: `app/atendimento_unificado/static/atendimento_unificado/js/workspace_coordinator.js`
- Responsabilidades exclusivas do coordinator:
  - Capturar evento `card:clicked` (disparado pelo kanban Alpine) e abrir o chat correspondente.
  - Capturar evento `chat:closed` e atualizar o estado de seleção do kanban.
  - Gerenciar o estado da sidebar (colapsada/expandida).
  - Inicializar os stores globais do `design_system` (`notifications`, `modal`).
- **Não deve** conter nenhuma lógica de chat ou kanban — apenas roteamento de eventos via `$dispatch` e `window.dispatchEvent`.

**4.3 — Reduzir `workspace_alpine.js`**

- Remover toda a lógica de chat (deve ter sido migrada para `chat_alpine.js` na Fase 2).
- Remover toda a lógica de kanban (deve ter sido migrada para `kanban_alpine.js` na Fase 3).
- O arquivo deve ficar com no máximo 80 linhas: inicialização do layout e bridge para o coordinator.

**4.4 — Atualizar `base_workspace.html` para carregar assets na ordem correta**

- Ordem de carregamento obrigatória:
  1. `design_system/css/core.css`
  2. `design_system/js/core_alpine.js`
  3. `chat_evolution/css/chat.css`
  4. `chat_evolution/js/chat_alpine.js`
  5. `gestao_kanban/css/kanban.css`
  6. `gestao_kanban/js/kanban_alpine.js`
  7. `atendimento_unificado/js/workspace_coordinator.js`
- Alpine.js deve ser carregado com `defer` após todos os stores e componentes registrados.

**4.5 — Teste de integração manual**

- Abrir workspace e validar fluxo: lista de conversas → clicar em conversa → chat abre → fechar chat → kanban responsivo.
- Mover card no kanban → evento SSE dispara → card atualiza sem reload.
- Enviar mensagem no chat → evento SSE dispara → badge de não-lidos atualiza no kanban.

**Entregável**: workspace funcionando com arquitetura modular completa, ainda com código legado presente (remoção na Fase 5).  
**Commit**: `refactor(shell): integrate modular apps into workspace coordinator`

---

### FASE 5 — Limpeza do Monolito

**Objetivo**: remover do `atendimento_unificado` toda a lógica que foi migrada para os apps filhos.

**Pré-requisito**: Fase 4 validada em homologação. **Não executar antes de confirmar que as rotas novas estão funcionais.**  
**Responsável**: `backend-specialist` + `code-reviewer`.

#### Tarefas

**5.1 — Remover endpoints migrados de `views_api.py` do monolito**

- Deletar do `app/atendimento_unificado/views_api.py` todos os endpoints que foram recriados em `chat_evolution` e `gestao_kanban`.
- Manter apenas endpoints que são genuinamente do shell (ex: dados do usuário logado, configurações de workspace).

**5.2 — Remover `views_sse.py` do monolito**

- Deletar `app/atendimento_unificado/views_sse.py` (SSE migrado para os apps filhos).
- Remover rotas SSE de `api_urls.py` do monolito.

**5.3 — Limpar `selectors.py` do monolito**

- Remover queries de chat e kanban (migradas nas Fases 2 e 3).
- Manter apenas queries de workspace (ex: lista de fluxos para sidebar, dados do usuário).

**5.4 — Remover partials HTML migrados**

- Deletar de `templates/atendimento_unificado/partials/` os arquivos que foram recriados nos apps filhos (`chat_drawer.html`, `conversation_item.html`, etc.).

**5.5 — Remover CSS e JS migrados de `workspace.css` e `workspace_alpine.js`**

- Remover de `workspace.css` todos os estilos de chat e kanban (migrados para `chat.css` e `kanban.css`).
- Confirmar que `workspace_alpine.js` está com menos de 80 linhas após a limpeza da Fase 4.

**5.6 — Atualizar `api_urls.py` do monolito**

- Remover rotas antigas de chat e kanban.
- Garantir que não há conflito de URL com as novas rotas `/chat/` e `/kanban/`.

**Entregável**: `atendimento_unificado` enxuto, contendo apenas lógica de shell.  
**Commit**: `chore(cleanup): remove migrated chat and kanban logic from atendimento_unificado`

---

### FASE 6 — Validação Final e Deploy

**Objetivo**: homologação completa do sistema refatorado antes do deploy em produção.

**Pré-requisito**: Fase 5 concluída.  
**Responsável**: `code-reviewer` + time de atendimento.

#### Checklist de Validação

**Backend**
- [ ] Nenhuma rota do chat aponta para views do `atendimento_unificado`.
- [ ] Nenhuma rota do kanban aponta para views do `atendimento_unificado`.
- [ ] SSE do chat (`/chat/events/`) funcional — mensagens chegam em tempo real.
- [ ] SSE do kanban (`/kanban/events/`) funcional — movimentações refletem em tempo real.
- [ ] Nenhuma migration pendente (`manage.py migrate --check`).
- [ ] Pyright sem erros de tipo nos novos apps.

**Frontend**
- [ ] Design System: componentes HTML renderizam sem erros.
- [ ] Chat: envio de texto, mídia, áudio funcionais.
- [ ] Chat: marcação de lido funcionando (sem ticks azuis automáticos — `readMessages=false`).
- [ ] Kanban: drag-and-drop entre colunas funcionando.
- [ ] Kanban: campos custom sendo lidos e atualizados.
- [ ] Kanban: etiquetas e notas funcionais.
- [ ] Cross-board: transferência de card para outro quadro.
- [ ] Workspace coordinator: evento de clique em card abre chat correto.

**Multi-Tenant**
- [ ] Troca de tenant não vaza dados entre workspaces.
- [ ] SSE de um tenant não aparece no workspace de outro.

**Performance**
- [ ] `workspace.html` carrega em menos de 3s (medir com DevTools).
- [ ] Sem JavaScript errors no console.
- [ ] Sem requests duplicados para os mesmos endpoints.

**Commit**: `chore(validation): post-refactor integration test results`  
**Deploy**: via `uv run task server-deploy` com feature flag habilitada.

---

## 5. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Regressão visual (CSS ao dividir workspace.css) | Média | Média | Migrar CSS em paralelo ao legado; não deletar até validar Fase 4 |
| Proxy model com `managed=False` gerando migration indesejada | Baixa | Alta | Confirmar `managed=False` em todos os models proxy; verificar `manage.py makemigrations --check` |
| Conflito de namespace de URL (`/chat/` sobrepondo rota existente) | Baixa | Alta | Auditar `urls.py` principal antes de registrar novas rotas |
| Alpine.js stores carregados fora de ordem (coordinator vs módulos) | Média | Média | Garantir ordem de carregamento definida em 4.4; testar com console aberto |
| SSE de chat e kanban conflitando no mesmo EventSource | Baixa | Alta | Canais separados (`sse:{tenant}:chat` vs `sse:{tenant}:kanban`) já resolvem isso |
| `workspace_alpine.js` sendo usado por código não mapeado | Média | Baixa | Busca global por `workspace_alpine` antes de reduzir na Fase 5 |

---

## 6. Resumo de Dependências entre Fases

```
FASE 1 (Design System)
    ↓
FASE 2 (chat_evolution completo) ──┐
FASE 3 (gestao_kanban completo) ───┤  (podem rodar em paralelo)
                                   ↓
                           FASE 4 (UI Shell)
                                   ↓
                           FASE 5 (Limpeza)
                                   ↓
                           FASE 6 (Validação + Deploy)
```

**Fases 2 e 3 podem ser executadas em paralelo** após a conclusão da Fase 1.

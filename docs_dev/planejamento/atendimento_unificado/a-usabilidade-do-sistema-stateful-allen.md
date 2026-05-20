# Plano Modular — Chat Evolution + Gestão Kanban + Atendimento Unificado

> **Versão 2.0 (2026-05-20)** — Reestruturação arquitetural: separação em 3 apps especializados com processamento independente e integração apenas na camada visual.
>
> Substitui o plano monolítico v1 (2026-05-14) que centralizava tudo em `atendimento_unificado`.

---

## Contexto e Motivação

A abordagem anterior de centralizar chat + kanban + campos custom em um único app (`atendimento_unificado`) gerou:

- **Bugs de estado** — estado do chat (SSE de mensagens, composer, leitura) conflitava com estado do kanban (drag-drop, movimentação de etapas, regras `tipo_etapa`).
- **UX degradada** — a tentativa de renderizar tudo em uma view única criou latência e complexidade visual desnecessária.
- **Manutenção difícil** — um único `views_api.py` com 938 linhas, `selectors.py` com 953 linhas e `models.py` com 382 linhas misturando domínios distintos.

**Novo Objetivo**: Separar as responsabilidades em **três apps Django independentes**, cada um fazendo uma coisa muito bem, e depois uni-los **apenas visualmente** num quarto passo.

### Os Três Pilares

| # | App | Responsabilidade | Analogia |
|---|-----|-----------------|----------|
| 1 | **`chat_evolution`** | Chat completo estilo WhatsApp Web, usando todos os recursos da Evolution API (texto, mídia, áudio, reações, presença, reply) | WhatsApp Web |
| 2 | **`gestao_kanban`** | Kanban avançado com paridade Trello, campos personalizados por tenant/fluxo, extração IA, drag-and-drop, SLA | Trello personalizado |
| 3 | **`atendimento_unificado`** | **UI Shell puro** — monta o layout integrando as telas dos dois apps acima. Zero lógica de negócio. | Container/Orquestrador |

### Decisões já tomadas pelo usuário (preservadas)

1. Trello permanece sincronizado bidirecionalmente (Kanban interno é principal, Trello é espelho).
2. Real-time via **SSE** (Server-Sent Events) — não WebSocket, não polling.
3. Campos personalizados **híbridos**: globais por tenant + por fluxo.
4. **Kanban interno espelha 100% da lógica do Trello** — operador pode trabalhar inteiramente no painel.
5. Clicar em qualquer card abre a conversa completa (drawer/modal sobre o kanban).

---

## 1. Decisões Arquiteturais Consolidadas

### 1.1 Separação por Domínio

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       atendimento_unificado                              │
│                    (UI Shell — apenas layout)                             │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────┐  │
│  │       chat_evolution          │  │        gestao_kanban             │  │
│  │  • Mensagens                  │  │  • Quadros / Colunas / Cards     │  │
│  │  • Contatos                   │  │  • Movimentação + tipo_etapa     │  │
│  │  • Evolution API              │  │  • Campos Personalizados         │  │
│  │  • Presença (digitando)       │  │  • Extração IA                   │  │
│  │  • Mídia in/out               │  │  • Etiquetas                     │  │
│  │  • Reply / Quote              │  │  • Notas internas                │  │
│  │  • SSE: sse:{tenant}:chat     │  │  • SLA / Timeline                │  │
│  │                                │  │  • SSE: sse:{tenant}:kanban      │  │
│  └──────────────────────────────┘  └──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
     ▲                                        ▲
     │  Signal: post_save Mensagem            │  Signal: post_save Atendimento
     │  (propaga para kanban via SSE)         │  (propaga para chat via SSE)
     └────────────────────────────────────────┘
          Comunicação cross-app: APENAS via Django Signals
```

### 1.2 Princípios Inegociáveis

1. **Independência cross-app**: `chat_evolution` e `gestao_kanban` não importam código um do outro. Comunicação **apenas via Django signals + Redis pub/sub**.
2. **Zero alteração em apps legados**: `atendimentos`, `operacional`, `trello_sync`, `evolution_sync`, `ai_engine` permanecem intocados. Leitura direta é permitida; escrita via métodos públicos existentes.
3. **FKs lógicas**: Referências cross-app usam `BigIntegerField` (sem FK constraint) — padrão já adotado no código atual (`atu_*` tables).
4. **Multi-tenant SSE**: Canal Redis nomeado por tenant e domínio (`sse:{tenant_slug}:chat`, `sse:{tenant_slug}:kanban`) para evitar vazamento cross-tenant.
5. **Reuso radical de models**: `FluxoAtendimento` já é "quadro", `EtapaFluxo` já é "coluna", `Atendimento.etapa_atual` já é "card". Não criar entidades duplicadas.

### 1.3 Reuso de Models Existentes

| Conceito | Modelo Existente | App que Consome |
|----------|-----------------|-----------------|
| Conversa / Mensagem | `atendimentos.Mensagem` | `chat_evolution` |
| Contato | `clientes.Contato` | `chat_evolution` |
| Envio WhatsApp | Signal `_on_message_saved` em `evolution_sync/signals.py:216` | `chat_evolution` |
| Quadro Kanban | `operacional.FluxoAtendimento` (1:1 com `TrelloBoard`) | `gestao_kanban` |
| Coluna Kanban | `operacional.EtapaFluxo` (tem `cor`, `ordem`, `tipo_etapa`) | `gestao_kanban` |
| Card Kanban | `atendimentos.Atendimento` (via `etapa_atual`) | `gestao_kanban` |
| Mover Card | `operacional.MovimentoFluxo.criar_movimento(...)` | `gestao_kanban` |
| Atendente | `operacional.Atendente` | ambos |

---

## 2. Inventário do Código Existente (migração para os novos apps)

O app `atendimento_unificado` atual já tem implementação substancial que deve ser **redistribuída**:

### 2.1 Código que migra para `chat_evolution`

| Arquivo Atual | Destino | O que contém |
|--------------|---------|-------------|
| `models.py` → `LeituraAtendimento` | `chat_evolution/models.py` | Controle de não-lidos por atendente |
| `services/message_dispatch_service.py` | `chat_evolution/services/` | Envio de texto via `Mensagem(ATENDENTE_HUMANO)` |
| `services/media_dispatch_service.py` | `chat_evolution/services/` | Upload e envio de mídia outbound |
| `views_api.py` → `ConversationsListView` | `chat_evolution/views_api.py` | Listagem de conversas sidebar |
| `views_api.py` → `ConversationMessagesView` | `chat_evolution/views_api.py` | Histórico paginado |
| `views_api.py` → `ConversationSendView` | `chat_evolution/views_api.py` | Enviar mensagem texto |
| `views_api.py` → `ConversationMarkReadView` | `chat_evolution/views_api.py` | Marcar como lido |
| `views_api.py` → `ConversationPresenceView` | `chat_evolution/views_api.py` | Indicador de presença (digitando/gravando) |
| `views_api.py` → `ConversationUploadView` | `chat_evolution/views_api.py` | Upload de mídia |
| `views_api.py` → `ConversationMediasView` | `chat_evolution/views_api.py` | Listagem de mídias |
| `selectors.py` → `list_conversations`, `get_messages`, `_serialize_mensagem`, `_extract_media`, `list_medias` | `chat_evolution/selectors.py` | Queries de leitura do chat |
| `views_sse.py` (parte de chat) | `chat_evolution/views_sse.py` | SSE para mensagens |

### 2.2 Código que migra para `gestao_kanban`

| Arquivo Atual | Destino | O que contém |
|--------------|---------|-------------|
| `models.py` → `CampoPersonalizado`, `ValorCampoAtendimento` | `gestao_kanban/models.py` | Campos custom por tenant/fluxo |
| `models.py` → `Etiqueta`, `EtiquetaAtendimento` | `gestao_kanban/models.py` | Sistema de etiquetas |
| `models.py` → `Nota` | `gestao_kanban/models.py` | Notas internas do atendente |
| `services/board_service.py` | `gestao_kanban/services/` | Movimentação com regras `tipo_etapa` |
| `services/card_renderer.py` | `gestao_kanban/services/` | Payload visual do card |
| `services/etiquetas_service.py` | `gestao_kanban/services/` | Toggle de etiquetas |
| `services/notas_service.py` | `gestao_kanban/services/` | CRUD de notas |
| `services/transfer_fluxo_service.py` | `gestao_kanban/services/` | Cross-board move |
| `views_api.py` → `BoardSnapshotView`, `BoardMoveView`, `BoardAssignView`, `BoardTransferFluxoView` | `gestao_kanban/views_api.py` | Endpoints de quadro |
| `views_api.py` → `CustomFieldPatchView` | `gestao_kanban/views_api.py` | Edição de campos custom |
| `views_api.py` → `EtiquetasListView`, `ConversationEtiquetaToggleView` | `gestao_kanban/views_api.py` | Etiquetas |
| `views_api.py` → `ConversationNotasView`, `ConversationNotaDeleteView` | `gestao_kanban/views_api.py` | Notas |
| `views_api.py` → `ConversationTimelineView` | `gestao_kanban/views_api.py` | Timeline |
| `views_api.py` → `ExportView` | `gestao_kanban/views_api.py` | Export CSV |
| `selectors.py` → `board_snapshot_by_fluxo`, `list_fluxos_acessiveis`, `get_atendimento_detail`, `get_campos_for_prompt`, `list_etiquetas`, `list_notas`, `build_timeline` | `gestao_kanban/selectors.py` | Queries do kanban |
| `tasks.py` | `gestao_kanban/tasks.py` | Extração de campos IA |
| `tenant_admin.py` | `gestao_kanban/tenant_admin.py` | Admin de CampoPersonalizado |
| `views_sse.py` (parte de kanban) | `gestao_kanban/views_sse.py` | SSE para board |

### 2.3 Código que permanece em `atendimento_unificado`

| Arquivo | Propósito |
|---------|----------|
| `views.py` → `WorkspaceView` | View HTML principal (UI Shell) |
| `feature_flags.py` | Feature flag do workspace |
| `urls.py` | Rota `/workspace/` |
| `templates/` | Template `workspace.html` |
| `static/js/workspace_coordinator.js` | Alpine.js orquestrando eventos cross-app |

### 2.4 Código compartilhado (extrair para utilitário)

| Item | Destino |
|------|---------|
| `realtime_publisher.py` | `core/services/realtime_publisher.py` (ou módulo compartilhado) |
| `_require_workspace` decorator | Cada app terá seu próprio decorator de permissão |
| `_resolve_atendente`, `_allowed_flow_ids` | `core/utils/` ou mixin compartilhado |
| `NotificationsUnreadCountView` | `chat_evolution` (pertence ao domínio de leitura) |

---

## 3. Paridade Funcional Trello ↔ Kanban Interno

> Extraído de `trello_sync/signals.py` e `trello_sync/services/ticket_sync_service.py` — **toda regra abaixo deve funcionar igual no `gestao_kanban`**.

### 3.1 Estrutura de Etapas (regras fixas por `tipo_etapa`)

| `TipoEtapa` | Comportamento ao mover card | Status resultante |
|-------------|----------------------------|-------------------|
| `FILA` | Atendimento entra em fila, sem atendente atribuído | `FILA` |
| `TRABALHO` | **Assumir atendimento**: atribui `atendente_humano` ao usuário que moveu + dispara saudação automática via `transferir_para_humano_com_saudacao(atendente_id=...)` | `EM_ATENDIMENTO` |
| `ESPERA` | Atendimento aguardando (cliente, pagamento, etc.) | `PENDENCIA` |
| `FINALIZACAO` | **Encerra atendimento**: chama `finalizar_atendimento(...)`. Se nome contém "cancel" → `CANCELADO`, senão → `RESOLVIDO` | `RESOLVIDO` / `CANCELADO` |

### 3.2 `board_service.move_atendimento` (já implementado — migrar para `gestao_kanban`)

```python
def move_atendimento(
    atendimento_id: int,
    etapa_destino_id: int,
    atendente_actor: Atendente | None,
    motivo: str | None = None,
) -> MoveResult:
    with transaction.atomic(using=router.db_for_write(Atendimento)):
        atendimento = Atendimento.objects.select_for_update().get(id=atendimento_id)
        nova_etapa = EtapaFluxo.objects.select_related('fluxo__departamento').get(id=etapa_destino_id)

        if atendimento.etapa_atual_id == nova_etapa.id:
            return  # idempotente

        # 1. Cross-board: atualizar fluxo + departamento
        # 2. Criar MovimentoFluxo (atualiza etapa_atual + histórico)
        # 3. Aplicar regras tipo_etapa (FILA→TRABALHO, FINALIZACAO, ESPERA)

    realtime_publisher.publish(tenant_slug, "board.moved", payload)
```

### 3.3 Comportamentos Especiais a Replicar

1. **Reordenação automática de colunas** — `EtapaFluxo.ordem` reflete na ordem visual.
2. **Atribuição automática FILA→TRABALHO** — atendente que move vira `atendente_humano` + saudação.
3. **Finalização automática** — mover para FINALIZACAO dispara `finalizar_atendimento`. Nome com "cancel" → CANCELADO.
4. **Status muda etapa automaticamente** — signal `post_save` de `Atendimento.status` move o card. Signal já existe em `trello_sync`.
5. **Sincronização de membro** — card mostra avatar/nome do atendente atribuído.
6. **Re-render do card a cada nova `Mensagem`** — preview reflete última mensagem.
7. **Loop prevention** — flag `_syncing_from_trello` evita recursão Trello↔Workspace.
8. **Concorrência** — `select_for_update` (padrão já em `TicketSyncService`).

### 3.4 Cross-Board Move (mover entre quadros = mudar fluxo)

Já implementado em `transfer_fluxo_service.py`:
1. Atualizar `atendimento.fluxo_atendimento_id` para o fluxo de destino.
2. Atualizar `atendimento.departamento_id` para `novo_fluxo.departamento_id`.
3. Criar `MovimentoFluxo.criar_movimento(...)` com a nova etapa.
4. Aplicar regras `tipo_etapa` da nova coluna.

### 3.5 Conteúdo Visual do Card

**Título composto** (espelhando `_build_card_name`):
```
{nome_contato} - {nome_fantasia_cliente} - {assunto} - {intents[0..3]}
```

**Componentes visuais do card** (já em `card_renderer.py`):
- Label de **prioridade** com cor (baixa→verde, normal→azul, alta→laranja, urgente→vermelho)
- **Status** com emoji: ⏳ fila, 💬 em atendimento, ⏸️ pendência, ✅ resolvido, ❌ cancelado
- **Atendente atribuído** (avatar + nome, ou "⏳ Não atribuído")
- **Preview da última mensagem** (1 linha truncada + ícone do remetente: 👤/🤖/👨‍💻)
- **Tempo desde última msg** humanizado ("há 8 minutos", "há 2 horas")
- **Canal** (emoji): 📱 whatsapp
- **Etiquetas** (chips coloridos)
- **Campos personalizados** com `mostrar_no_card=True` (mini-chips)
- **Badge de não-lidos** (contador)

---

## 4. Faseamento do Projeto

### FASE 1 — App `chat_evolution` (Experiência WhatsApp Web)

**Objetivo**: Chat isolado, completo e fluido, sem dependência do kanban.

#### 4.1.1 Estrutura do App

```
chat_evolution/
  __init__.py
  apps.py                          # ChatEvolutionConfig
  models.py                        # LeituraAtendimento (migrado de atendimento_unificado)
  urls.py                          # Rotas HTML
  api_urls.py                      # Rotas JSON + SSE
  views.py                         # ChatView (HTML shell standalone)
  views_api.py                     # Endpoints JSON do chat
  views_sse.py                     # Async SSE para mensagens
  selectors.py                     # Queries de leitura (conversas, mensagens, mídias)
  signals.py                       # Receivers: post_save Mensagem → publish SSE
  services/
    message_dispatch_service.py    # Criar Mensagem(ATENDENTE_HUMANO)
    media_dispatch_service.py      # Upload + envio de mídia outbound
    realtime_publisher.py          # Publica em sse:{tenant}:chat
  templates/chat_evolution/
    chat.html                      # Layout standalone (para uso independente)
    partials/
      conversation_item.html       # Item da sidebar
      chat_message.html            # Bolha de mensagem (variantes por tipo)
      chat_composer.html           # Área de digitação + anexos + gravação
      media_viewer.html            # Viewer de mídia inline
  static/chat_evolution/
    js/chat_alpine.js              # Store Alpine + EventSource
    css/chat.css                   # Estilos específicos do chat
  migrations/
    0001_initial.py                # atu_leitura_atendimento (prefixo mantido para evitar conflito)
```

#### 4.1.2 Endpoints da API

| Rota | Verbo | Função |
|------|-------|--------|
| `/chat/api/conversations/` | GET | Sidebar (cursor por `data_ultima_mensagem`, filtros: fluxo, q, prioridade, atendente, etiqueta, não-lidos) |
| `/chat/api/conversations/<id>/messages/` | GET | Histórico paginado (`before_id` para scroll infinito) |
| `/chat/api/conversations/<id>/send/` | POST | Cria `Mensagem(ATENDENTE_HUMANO)` — signal envia via Evolution |
| `/chat/api/conversations/<id>/upload/` | POST | Multipart → `Mensagem` com mídia (≤10 MB) |
| `/chat/api/conversations/<id>/mark-read/` | POST | Upsert em `LeituraAtendimento` + marcar `Mensagem.lido=True` |
| `/chat/api/conversations/<id>/presence/` | POST | Envia indicador de presença (composing/recording) via Evolution Go |
| `/chat/api/conversations/<id>/detail/` | GET | Dados do contato + métricas do atendimento |
| `/chat/api/conversations/<id>/medias/` | GET | Lista de mídias/documentos do atendimento |
| `/chat/api/notifications/unread-count/` | GET | Total de não-lidos para sino da topbar |

#### 4.1.3 SSE Chat

- **Canal Redis**: `sse:{tenant_slug}:chat`
- **Eventos**: `message.new`, `message.sent`, `message.status_update`, `heartbeat` (25s)
- **Formato**: `event: <tipo>\ndata: <json>\n\n`
- **Implementação**: Django async view nativa com `StreamingHttpResponse` (Django 4.1+)
- **Reconexão**: `EventSource` nativa reconecta automaticamente

#### 4.1.4 Funcionalidades do Chat (paridade WhatsApp Web)

- [x] Envio/recebimento de texto (já implementado)
- [x] Envio/recebimento de mídia: imagem, áudio, vídeo, documento (já implementado)
- [x] Reply/Quote de mensagens (já implementado — `quoted_message_id`)
- [x] Status de envio: sent, delivered, read (já implementado — `status_envio`, `data_entregue`, `data_lida`)
- [x] Presença: composing, recording (já implementado — `ConversationPresenceView`)
- [x] Não-lidos com badge (já implementado)
- [ ] Gravação de áudio inline (frontend — novo)
- [ ] Busca dentro da conversa (novo)
- [ ] Reações a mensagens (novo — requer endpoint Evolution)

#### 4.1.5 Envio de Mensagem pelo Atendente

`message_dispatch_service.send_text(atendimento_id, texto, atendente)`:
1. `Mensagem.objects.create(atendimento=..., remetente=TipoRemetente.ATENDENTE_HUMANO, conteudo="", resposta_bot=texto, metadados={"evolution": {"api_key": <api_key>}})` — segue padrão de `transferir_para_humano_com_saudacao`.
2. Signal `_on_message_saved` em `evolution_sync` detecta e envia via `EvolutionWhatsAppService.send_message(...)`.

---

### FASE 2 — App `gestao_kanban` (Trello Avançado + IA)

**Objetivo**: Motor de kanban focado no tenant, com personalização e IA.

#### 4.2.1 Estrutura do App

```
gestao_kanban/
  __init__.py
  apps.py                          # GestaoKanbanConfig
  models.py                        # CampoPersonalizado, ValorCampoAtendimento, Etiqueta, EtiquetaAtendimento, Nota
  urls.py                          # Rotas HTML
  api_urls.py                      # Rotas JSON + SSE
  views.py                         # KanbanView (HTML shell standalone)
  views_api.py                     # Endpoints JSON do kanban
  views_sse.py                     # Async SSE para board
  selectors.py                     # Queries de leitura (board, fluxos, campos, etiquetas, notas, timeline)
  signals.py                       # Receivers: post_save Atendimento/MovimentoFluxo → publish SSE
  tasks.py                         # Celery: extract_custom_fields_async
  tenant_admin.py                  # Admin de CampoPersonalizado por tenant
  services/
    board_service.py               # Movimentação com regras tipo_etapa + assign
    card_renderer.py               # Payload visual do card (espelha _build_card_name)
    etiquetas_service.py           # Toggle de etiquetas
    notas_service.py               # CRUD de notas internas
    transfer_fluxo_service.py      # Cross-board move
    realtime_publisher.py          # Publica em sse:{tenant}:kanban
  templates/gestao_kanban/
    kanban.html                    # Layout standalone
    partials/
      kanban_column.html           # Coluna com header colorido
      kanban_card.html             # Card visualmente equivalente ao Trello
      detail_panel.html            # Painel direito (dados, intents, campos)
      custom_fields_panel.html     # Formulário de campos custom
      etiquetas_popover.html       # Popover para gerenciar etiquetas
      notas_panel.html             # Lista de notas internas
      timeline_panel.html          # Linha do tempo
  static/gestao_kanban/
    js/kanban_alpine.js            # Store Alpine + SortableJS + EventSource
    css/kanban.css                 # Estilos do kanban
  migrations/
    0001_initial.py                # atu_campo_personalizado, atu_valor_campo, atu_etiqueta, atu_etiqueta_atendimento, atu_nota
```

#### 4.2.2 Models (já implementados — migrar de `atendimento_unificado`)

**`CampoPersonalizado`** (definição por tenant/fluxo):
- `slug`, `nome`, `descricao` (hint de extração)
- `escopo`: GLOBAL / FLUXO
- `fluxo_id`: FK lógica (null se GLOBAL)
- `tipo`: texto, numero, data, escolha, multipla_escolha, booleano
- `opcoes`: JSONField (lista para escolha/multipla)
- `obrigatorio`, `extrair_automaticamente`, `extrair_hint`
- `mostrar_no_card`: boolean — exibe como mini-chip no card
- `ordem`, `ativo`
- DB: `atu_campo_personalizado`, unique `(slug, escopo, fluxo_id)`

**`ValorCampoAtendimento`** (valor por atendimento):
- `atendimento_id`: FK lógica
- `campo`: FK → CampoPersonalizado
- `valor`: JSONField
- `origem`: MANUAL / BOT / IMPORT
- `confianca`: FloatField (score quando BOT)
- `mensagem_origem_id`: FK lógica (rastreia extração)
- `editado_por_id`: FK lógica
- DB: `atu_valor_campo`, unique `(atendimento_id, campo)`

**`Etiqueta`** (catálogo de tags coloridas):
- `nome`, `cor` (hex), `descricao`, `ativo`
- DB: `atu_etiqueta`

**`EtiquetaAtendimento`** (M2M manual):
- `atendimento_id`: FK lógica
- `etiqueta`: FK → Etiqueta
- `aplicada_por_id`: FK lógica
- DB: `atu_etiqueta_atendimento`

**`Nota`** (notas internas do atendente):
- `atendimento_id`: FK lógica
- `texto`, `criado_por_id`, `criado_em`
- DB: `atu_nota`

#### 4.2.3 Endpoints da API

| Rota | Verbo | Função |
|------|-------|--------|
| `/kanban/api/fluxos/` | GET | Lista `FluxoAtendimento` acessíveis ao atendente |
| `/kanban/api/board/?fluxo=<id>` | GET | Snapshot Kanban (etapas + cards com payload de render) |
| `/kanban/api/board/move/` | POST | `{atendimento_id, etapa_destino_id}` → `board_service.move_atendimento` |
| `/kanban/api/board/assign/` | POST | `{atendimento_id, atendente_id}` (override manual) |
| `/kanban/api/board/transfer-fluxo/` | POST | `{atendimento_id, fluxo_destino_id}` (cross-board) |
| `/kanban/api/cards/<id>/custom-fields/<slug>/` | PATCH | Cria/atualiza ValorCampoAtendimento (origem=MANUAL) |
| `/kanban/api/etiquetas/` | GET | Catálogo de etiquetas ativas |
| `/kanban/api/cards/<id>/etiquetas/` | GET | Etiquetas aplicadas ao atendimento |
| `/kanban/api/cards/<id>/etiquetas/<etiqueta_id>/toggle/` | POST | Aplica/remove etiqueta |
| `/kanban/api/cards/<id>/notas/` | GET/POST | Lista e cria notas internas |
| `/kanban/api/cards/<id>/notas/<nota_id>/` | DELETE | Remove nota (apenas o autor) |
| `/kanban/api/cards/<id>/timeline/` | GET | Linha do tempo agregada |
| `/kanban/api/export/` | GET | CSV streaming |

#### 4.2.4 Payload do Snapshot Kanban

```json
{
  "etapas": [
    {"id": 12, "nome": "Em Trabalho", "cor": "#3B82F6", "dot_color": "#d97706", "tipo_etapa": "trabalho", "ordem": 2, "count": 5}
  ],
  "cards": {
    "12": [
      {
        "atendimento_id": 88,
        "titulo": "João Silva - Acme Comércio - Orçamento - solicitar_orcamento",
        "status": "em_atendimento",
        "status_emoji": "💬",
        "prioridade": "alta",
        "prioridade_label_class": "bg-orange-100 text-orange-800",
        "atendente": {"id": 4, "nome": "Maria", "inicial": "MA"},
        "preview_msg": "Pode confirmar o endereço de entrega?",
        "preview_remetente": "CONTATO",
        "preview_remetente_icon": "👤",
        "tempo_ultima_msg": "há 8 minutos",
        "data_ultima_mensagem": "2026-05-14T15:32:11Z",
        "canal_emoji": "📱",
        "etiquetas": [{"nome": "VIP", "cor": "#dc2626"}],
        "campos_custom_card": [{"label": "CNPJ", "valor": "12.345.678/0001-99"}],
        "nao_lidos": 3
      }
    ]
  }
}
```

#### 4.2.5 SSE Kanban

- **Canal Redis**: `sse:{tenant_slug}:kanban`
- **Eventos**: `board.moved`, `card.updated`, `atendimento.assigned`, `atendimento.status_changed`, `custom_field.updated`, `etiqueta.toggled`, `heartbeat` (25s)

#### 4.2.6 Extração de Campos por IA

**Feature LLM** em `modules/ai_engine/features/extracao_campos/`:

```
extracao_campos/
  datasource/extracao_campos_datasource.py
  domain/usecase/extracao_campos_usecase.py
  domain/model/campo_extraido.py    # @dataclass CampoExtraido(slug, valor, confianca)
```

- **Trigger**: Signal `post_save Mensagem` em `gestao_kanban/signals.py` dispara task Celery `extract_custom_fields_async(tenant_slug, atendimento_id, mensagem_id)` quando `remetente=ASSISTENTE_VIRTUAL`.
- **Schema dinâmico**: `pydantic.create_model` a partir de `campos_definidos` (apenas campos sem valor ou com `confianca < 0.9`).
- **Threshold**: ≥ 0.6 para gravar.
- **Idempotência**: `select_for_update`; só sobrescreve `origem=BOT` se `confianca_nova > confianca_atual`. **Nunca sobrescreve `origem=MANUAL`**.

#### 4.2.7 Injeção no System Prompt do Bot

Modificar `analise_mensage_datasource.py` (revalidar offsets no momento da implementação):

1. Adicionar em `AnaliseMensageParameters`:
   ```python
   campos_coletados: dict[str, Any]   # {slug: valor}
   campos_pendentes: list[dict]       # [{slug, nome, descricao, obrigatorio}]
   ```
2. Nova seção no prompt entre "DADOS DA EMPRESA" e "DADOS DO TREINAMENTO":
   ```
   ### CAMPOS COLETADOS DO ATENDIMENTO:
   - cnpj: 12.345.678/0001-99
   - nome_fantasia: Acme Comércio

   ### CAMPOS PENDENTES (solicite ao usuário se vier ao caso, sem insistir):
   - tipo_produto (Tipo de produto desejado): obrigatório
   - medidas (Largura x altura em cm): opcional
   ```
3. Helper `get_campos_for_prompt(atendimento_id, fluxo_id)` já implementado em `selectors.py`.

#### 4.2.8 Drag-and-Drop

- **SortableJS** via CDN, integrado com Alpine via `x-init`.
- `dragend` → `POST /kanban/api/board/move/`.
- Em erro, reverter DOM via snapshot do store Alpine.
- Flag `isDragging` ignora updates SSE da etapa em movimento por 2s.

---

### FASE 3 — App `atendimento_unificado` (União de Layout)

**Objetivo**: UI Shell que integra Chat + Kanban na mesma tela.

#### 4.3.1 Estrutura do App (magro)

```
atendimento_unificado/
  __init__.py
  apps.py                          # AtendimentoUnificadoConfig
  urls.py                          # /workspace/ → WorkspaceView
  views.py                         # WorkspaceView (HTML shell)
  feature_flags.py                 # ATENDIMENTO_UNIFICADO_ENABLED
  templates/atendimento_unificado/
    workspace.html                 # estende base_dashboard.html
  static/atendimento_unificado/
    js/workspace_coordinator.js    # Alpine.js orquestrando cross-app
    css/workspace.css              # Ajustes de layout integrado
```

#### 4.3.2 Layout Integrado

```
┌──────────────────────────────────────────────────────────────────────┐
│ Topbar: [Conversas | Kanban]  Fluxo: [Vendas ▾]  🔔 Busca            │
├─────────────┬──────────────────────────────┬──────────────────────────┤
│ Sidebar     │ Centro                       │ Painel direito           │
│ Conversas   │ Modo CONVERSAS:              │ - Dados do contato       │
│ (do chat_   │   chat ativo + composer      │ - Atendimento (status,   │
│  evolution) │ Modo KANBAN:                 │   etapa, prioridade)     │
│ Ordenada    │   colunas EtapaFluxo + cards │ - Etiquetas              │
│ por data    │   (do gestao_kanban)         │ - Campos custom          │
│ última msg  │   Clicar abre drawer chat    │ - Notas internas         │
│             │                              │ - Timeline               │
└─────────────┴──────────────────────────────┴──────────────────────────┘
```

**Modos de exibição**:
- **Modo 1 — Kanban principal**: Kanban full-width. Clicar no card abre drawer lateral de chat (`fixed inset-y-0 right-0 w-full md:w-[600px] bg-white shadow-2xl z-40`).
- **Modo 2 — Chat principal**: Layout 3 colunas (sidebar | chat | detalhes).
- **Toggle**: Topbar com botões [Conversas | Kanban].

#### 4.3.3 Orquestração Frontend

O `workspace_coordinator.js` usa Alpine.js para:
1. **`onCardClick(atendimentoId)`**: Dispara `$dispatch('open-chat', {id})` → componente de chat abre drawer/carrega conversa.
2. **`onConversationSelect(atendimentoId)`**: Dispara `$dispatch('highlight-card', {id})` → kanban scrolla até o card e destaca.
3. **SSE multiplexado**: Escuta ambos canais (`sse:{tenant}:chat` + `sse:{tenant}:kanban`) e roteia eventos para o store correto.

#### 4.3.4 Drawer de Chat (sobre Kanban)

```html
<div class="fixed inset-y-0 right-0 w-full md:w-[600px] bg-white shadow-2xl z-40
            transform transition-transform"
     :class="chatDrawerOpen ? 'translate-x-0' : 'translate-x-full'">
    <!-- Header: info contato + botão fechar -->
    <!-- Área de mensagens (scroll) -->
    <!-- Composer fixo no rodapé -->
</div>
```

---

## 5. Design System

Referência: `base_dashboard.html`.

### 5.1 Paleta de Cores

| Token | Valor | Uso |
|-------|-------|-----|
| `--color-gold-primary` | `#a98f71` | Acento principal (estados ativos, hover, foco) |
| `--color-gold-dark` | `#8b7355` | Acento secundário |
| `bg-[#1c1917]` | stone-900 | Sidebar fundo |
| `bg-stone-50` | — | Fundo geral da página |
| `bg-white` | — | Cards e painéis |
| `bg-green-50 text-green-600` | — | Status conectado / WhatsApp |
| `bg-amber-50 border-amber-200` | — | Banners de aviso |
| `bg-red-50 text-red-700` | — | Erros, ações destrutivas |

### 5.2 Tipografia

- Fonte primária: **Outfit** (Google Fonts), pesos 300-700.
- Tamanhos: `text-xs` para labels, `text-sm` para corpo, `text-xl font-bold` para títulos.

### 5.3 Componentes por App

**Chat** (`chat_evolution`):
- Bolha recebida: `bg-stone-100 text-stone-800 rounded-2xl rounded-tl-sm` (esquerda)
- Bolha enviada: `bg-[#a98f71]/10 text-stone-800 rounded-2xl rounded-tr-sm` (direita)
- Composer: `border-t border-stone-200`, textarea com `focus:ring-2 focus:ring-[#a98f71]/30`, botão envio `bg-green-600`
- Sidebar item: hover suave, `divide-y divide-stone-100`, avatar `bg-[#a98f71] text-white`

**Kanban** (`gestao_kanban`):
- Coluna: `bg-stone-100 rounded-xl p-3`, header com barra de 3px usando `cor` da `EtapaFluxo`
- Card: `bg-white rounded-lg shadow-sm border border-stone-200 p-3 hover:shadow transition-shadow cursor-pointer`
- Painel campos custom: badges de origem (`BOT` em `bg-blue-50 text-blue-700`, `MANUAL` em `bg-stone-100`)
- Barra de confiança: `bg-green-500` ≥0.9, `bg-amber-500` 0.6-0.9, `bg-red-500` <0.6

### 5.4 Entrada no Sidebar Global

Adicionar ao `base_dashboard.html`:

```html
{% can_view_module "atendimento" as can_atendimento %}
{% if is_owner or can_atendimento %}
<div class="pt-4 pb-2 px-3">
    <p class="text-xs font-semibold text-stone-500 uppercase tracking-wider">Atendimento</p>
</div>
<a href="{% url 'atendimento_unificado:workspace' %}"
   class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg
          {% if 'workspace' in request.path %}bg-[#a98f71]/10 text-[#a98f71]
          {% else %}text-stone-400 hover:text-stone-100 hover:bg-stone-800{% endif %}
          group transition-colors">
    <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
    Workspace
</a>
{% endif %}
```

---

## 6. Registros e Configuração

### 6.1 Registrar os Novos Apps

- `core/settings.py` → `INSTALLED_APPS`: adicionar `chat_evolution` e `gestao_kanban`
- `tenants/db_router.py` → `TENANT_APPS`: adicionar ambos
- Criar permissão de módulo `atendimento` (ou separar em `chat` e `kanban` se necessário)

### 6.2 Infraestrutura SSE

- **Gunicorn worker**: `uvicorn.workers.UvicornWorker` (ou processo Uvicorn dedicado para rotas SSE).
- **Redis pub/sub** (broker Celery já presente): `aioredis.from_url(...).pubsub().subscribe(...)`.
- **Nginx**: `proxy_buffering off` e `proxy_read_timeout 1h` na rota SSE.

### 6.3 Feature Flag e Rollout

1. **Feature flag** `ATENDIMENTO_UNIFICADO_ENABLED` em `TenantConfig` (default `False`).
2. **Smoke test** em 1 tenant piloto (24h mínimas).
3. **Rollout gradual**: 1 tenant por vez, intervalo 4h, monitorando logs.

### 6.4 Rollback

| Cenário | Ação | Tempo |
|---------|------|-------|
| Erro fatal no boot | Flag OFF global | ~5min |
| Bug em 1 tenant | `TenantConfig.update_config(<slug>, ..., False)` | ~30s |
| Migration falha | Workflow aborta; containers antigos seguem ativos | Imediato |
| Performance ruim | Flag OFF em todos; investigar offline | ~2min |

### 6.5 Migrations Seguras

TODAS as migrations criam apenas tabelas novas com prefixo `atu_`:
- `atu_leitura_atendimento` (chat_evolution)
- `atu_campo_personalizado` (gestao_kanban)
- `atu_valor_campo` (gestao_kanban)
- `atu_etiqueta` (gestao_kanban)
- `atu_etiqueta_atendimento` (gestao_kanban)
- `atu_nota` (gestao_kanban)

Nenhuma `ALTER`/`DROP` em tabelas legadas. Migration reversa simplesmente dropa essas tabelas.

---

## 7. Riscos e Mitigações

### Fase 1 — Chat

| Risco | Mitigação |
|-------|-----------|
| Gunicorn sync worker trava em SSE | Usar `uvicorn.workers.UvicornWorker` ou Uvicorn dedicado |
| Evolution API não tem `send_media` implementado | Já implementado em `media_dispatch_service.py` (validado) |
| Race condition na marcação de lido | `update_or_create` atômico em `LeituraAtendimento` |
| Reconexão SSE causa duplicação de mensagens | EventSource reconecta com `Last-Event-Id`; backend filtra |

### Fase 2 — Kanban

| Risco | Mitigação |
|-------|-----------|
| Loop signal Workspace↔Trello (recursão) | Flag `_syncing_from_trello` + dedup em `TrelloWebhookEvent.action_id` |
| Drag-drop muda etapa → regras `tipo_etapa` mudam status → move card | `move_atendimento` aplica em ordem controlada com `update_fields` |
| Falta de saudação ao assumir da fila via Workspace | Roteiro de validação testa explicitamente |
| Atendente sem cadastro tenta mover para TRABALHO | API retorna 400; UI mostra modal claro |
| Concorrência mover-card | `select_for_update` (padrão já em TicketSyncService) |
| Schema Pydantic dinâmico da IA | Validar com structured output do LangChain |
| Custo LLM extra por mensagem | Modelo barato; pular se nada a extrair; pular se todos ≥0.9 |
| Race bot vs atendente em campos | `select_for_update` + regra "nunca sobrescrever MANUAL" |

### Fase 3 — Integração

| Risco | Mitigação |
|-------|-----------|
| SortableJS + SSE conflito | Flag `isDragging` ignora updates SSE por 2s |
| Drawer de chat sobre kanban causa jank | `transform: translateX` com `will-change: transform` |
| Dois EventSource simultâneos | Browser suporta 6 conexões por domínio; 2 SSE é seguro |
| Multi-tenant SSE vazamento | Canal Redis nomeado por tenant; teste com 2 tenants simultâneos |

---

## 8. Estratégia de Migração (do monolito para os 3 apps)

A migração deve ser **gradual e não-destrutiva**:

1. **Criar os novos apps** (`chat_evolution`, `gestao_kanban`) com código copiado (não movido) do `atendimento_unificado`.
2. **Registrar os apps** em `INSTALLED_APPS` e `TENANT_APPS`.
3. **Reutilizar as tabelas `atu_*` existentes** — os novos apps apontam para as mesmas tabelas via `db_table` nos models. **Sem nova migration de dados**.
4. **Criar rotas nos novos apps** (`/chat/api/...`, `/kanban/api/...`).
5. **Atualizar o frontend** (`workspace.html`) para consumir as novas rotas.
6. **Deprecar as rotas antigas** (`/workspace/api/...`) — manter como proxy temporário.
7. **Remover o código migrado** do `atendimento_unificado` após validação.

---

## 9. Plano de Ação (PREVC)

| Etapa | Ação | Entregável |
|-------|------|-----------|
| **P (Planning)** | Este documento | Plano revisado e aprovado |
| **E (Execution) - Fase 1** | Criar `chat_evolution`, migrar código de chat, validar standalone | App de chat funcional independente |
| **E (Execution) - Fase 2** | Criar `gestao_kanban`, migrar código de kanban + campos + etiquetas + notas | App de kanban funcional independente |
| **E (Execution) - Fase 3** | Reestruturar `atendimento_unificado` como UI Shell, integrar os dois apps | Layout unificado funcionando |
| **V (Validation)** | Testar SSE independente, drag-drop, extração IA, paridade Trello, cross-board, presença | Relatório de validação |
| **C (Confirmation)** | Remover código duplicado do monolito, atualizar docs, deploy com feature flag | Release em produção |

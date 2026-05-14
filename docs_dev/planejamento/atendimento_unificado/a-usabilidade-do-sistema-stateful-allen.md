# Plano — Módulo `atendimento_unificado` (Chat WhatsApp + Kanban + Campos Custom)

> **Versão consolidada (2026-05-14)** — inclui paridade funcional total com Trello, Design System mapeado e ajustes técnicos validados contra o código atual.

## Contexto

Hoje o operador alterna entre **Trello** (gestão Kanban) e **WhatsApp Web** (responder mensagens). Isso fragmenta o contexto e atrasa o atendimento — Trello não tem chat, WhatsApp não tem fluxo. Além disso, dados estruturados (tipo de produto, medidas, CNPJ) ficam soltos na conversa em vez de organizados em campos consultáveis.

**Objetivo**: Construir uma única tela onde o atendente vê suas conversas (estilo WhatsApp Web), pode responder dali, e ao mesmo tempo gerencia o pipeline em modo Kanban — com **campos personalizados** que o bot extrai automaticamente das mensagens e que são reinjetados no system prompt para enriquecer respostas futuras. **O Kanban interno deve ser um Trello completo** dentro do painel, com paridade funcional total (assumir atendimento, finalização, cross-board, status auto por `tipo_etapa`).

**Decisões já tomadas pelo usuário**:
1. Trello permanece sincronizado bidirecionalmente (UI nativa principal, Trello como espelho).
2. Real-time via **SSE** (Server-Sent Events) — não WebSocket, não polling.
3. Entrega **faseada em 3 fases** (MVP primeiro).
4. Campos personalizados **híbridos**: globais por tenant + por fluxo.
5. **Kanban interno espelha 100% da lógica do Trello** — usuário pode trabalhar inteiramente no painel sem perder funcionalidade.
6. Clicar em qualquer card abre a conversa completa (drawer/modal sobre o kanban) com mesma experiência do WhatsApp Web.

---

## Decisões arquiteturais consolidadas

1. **Reuso radical**: `EtapaFluxo` já é "coluna kanban", `Atendimento.etapa_atual` já é "card". Não criar `Coluna`/`Card` novos.
2. **App novo `atendimento_unificado`** é camada fina de UI + orquestração; lógica de negócio fica nos models/services existentes.
3. **DDD/Result Pattern só onde toca IA**: feature de extração vai em `modules/ai_engine/features/extracao_campos/`.
4. **SSE via Django async views** (Django 4.1+ suporta `StreamingHttpResponse` async nativo) — **não precisa Channels**, **não precisa rota ASGI dedicada**. `core/asgi.py` permanece intacto. Usar `uvicorn.workers.UvicornWorker` no Gunicorn ou processo Uvicorn paralelo.
5. **Atendente envia mensagem criando `Mensagem(remetente=ATENDENTE_HUMANO)`** — o signal já existente em [evolution_sync/signals.py:216](../../src/smart_core_assistant_painel/app/evolution_sync/signals.py#L216) cuida do envio via Evolution API.
6. **Trello é espelho passivo** mas com **paridade funcional total entre Kanban interno e Trello**: toda escrita nasce no painel e propaga via signals/tasks já existentes — nenhuma mudança de fluxo no `trello_sync`. Mudanças no Trello refletem no Workspace via SSE.
7. **Extração de campos é assíncrona pós-resposta** — não atrasa a UX do contato.
8. **Multi-tenant SSE**: canal Redis nomeado por tenant (`sse:{tenant_slug}:events`) para evitar vazamento cross-tenant.

---

## Ajustes ao planejamento (após análise do código atual)

| # | Ponto Original | Ajuste / Confirmação | Motivo |
|---|---|---|---|
| 1 | "Roteamento ASGI dedicado, resto continua WSGI/Gunicorn" | **Usar Django async views nativas com `StreamingHttpResponse`** — não precisa de ASGI dedicado. | Django 4.1+ suporta async views diretamente. Reduz complexidade operacional; basta Gunicorn com worker async (`uvicorn.workers.UvicornWorker`) ou Uvicorn dedicado. |
| 2 | "Mídia outbound — se Evolution não tem `send_media`, adiar para Fase 3" | **Confirmado: [`EvolutionWhatsAppService.send_message`](../../src/smart_core_assistant_painel/app/evolution_sync/services/evolution_api.py#L94) tem APENAS texto (`/message/sendText`).** Mídia outbound fica formalmente na Fase 3 e requer implementar `send_media` chamando `/message/sendMedia`. | Validado no código — não há método de mídia outbound hoje. |
| 3 | "Não-lido usa `mensagens.filter(remetente=CONTATO, respondida=False).count()`" | **Adicionar `Atendimento.data_ultima_leitura_atendente DateTimeField(null=True, db_index=True)` JÁ NA FASE 1.** | `respondida` muda quando bot/atendente responde, não reflete "atendente leu". Migration na Fase 1 evita refactor na Fase 3. Custo desprezível. |
| 4 | "Fase 2 modifica linhas 241-250 de `analise_mensage_datasource.py`" | Revalidar offsets durante a Fase 2 — arquivo pode ter mudado após `feature-interpret-media`. | Plano original é de 2026-04. Code review da Fase 2 revalida. |
| 5 | Sem menção a Design System | **Seção dedicada adicionada** (abaixo) seguindo padrões de `base_dashboard.html`. | Consistência visual com resto do painel. |
| 6 | Sem menção a permissões | **Toda rota verifica permissões via `permission_tags`**. Criar módulo `atendimento` na permissão. | Padrão multi-tenant do projeto. |
| 7 | "Quadro por departamento" implícito | **Quadro por `FluxoAtendimento`** (1:1 com `TrelloBoard`). Seletor no topbar é por fluxo. | Modelo de dados existente — cada fluxo é um board independente. |
| 8 | Não detalhava regras `tipo_etapa` | **Espelhar TODAS as regras do `ticket_sync_service.process_webhook_card_move`** ao mover card no Workspace. Ver seção "Paridade Funcional Trello". | Sem isso, perde-se "assumir atendimento" + "finalização auto" ao usar painel. |

---

## Paridade Funcional Trello ↔ Kanban Interno

> Esta seção foi extraída de [trello_sync/signals.py](../../src/smart_core_assistant_painel/app/trello_sync/signals.py) e [trello_sync/services/ticket_sync_service.py](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py) — **toda regra abaixo precisa funcionar igual no Workspace**.

### Mapeamento de Entidades

| Conceito Trello | Modelo Trello | Conceito Painel | Modelo Painel |
|---|---|---|---|
| Board | `TrelloBoard` | **Quadro** | `FluxoAtendimento` (1:1 com `TrelloBoard`) |
| List/Column | `TrelloList` | **Coluna** | `EtapaFluxo` (1:1 com `TrelloList`) |
| Card | `TrelloCard` | **Card** | `Atendimento` (1:1 com `TrelloCard`) |
| Member | `TrelloMember` | **Atendente** | `Atendente` (1:1 com `TrelloMember`) |

**Implicação crítica**: cada `FluxoAtendimento` é um quadro independente (não cada departamento). Um departamento pode ter múltiplos fluxos = múltiplos quadros. O seletor do Workspace é **por `FluxoAtendimento`**, não por departamento.

### Estrutura de Etapas (regras fixas por `tipo_etapa`)

| `TipoEtapa` | Comportamento ao mover card pra cá | Status resultante |
|---|---|---|
| `FILA` | Atendimento entra em fila, sem atendente atribuído | `StatusAtendimento.FILA` |
| `TRABALHO` | **Assumir atendimento**: atribui `atendente_humano` ao usuário que moveu + dispara saudação automática via `Atendimento.transferir_para_humano_com_saudacao(atendente_id=request.user.atendente.id)` | `StatusAtendimento.EM_ATENDIMENTO` |
| `ESPERA` | Atendimento aguardando algo (cliente, pagamento, etc.) | `StatusAtendimento.PENDENCIA` |
| `FINALIZACAO` | **Encerra atendimento**: chama `Atendimento.finalizar_atendimento(novo_status, solicitar_feedback=False)`. Se nome contém "cancel" → `CANCELADO`, senão → `RESOLVIDO` | `RESOLVIDO` ou `CANCELADO` |

### Conteúdo Visual do Card (espelhar `_build_card_name` + dados de preview)

**Título do card** ([ticket_sync_service.py:245-327](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L245)):
```
{nome_contato} - {nome_fantasia_cliente} - {assunto} - {intents[0..3]}
```
Cada parte é omitida se vazia. Nome do contato limitado a 40 chars.

**Componentes visuais do card no Kanban interno**:
- Label de **prioridade** (cor seguindo Tailwind):
  - `baixa` → `bg-green-100 text-green-800`
  - `normal` → `bg-blue-100 text-blue-800`
  - `alta` → `bg-orange-100 text-orange-800`
  - `urgente` → `bg-red-100 text-red-800`
- **Status** com emoji: `⏳` fila, `💬` em atendimento, `⏸️` pendência, `✅` resolvido, `❌` cancelado
- **Atendente atribuído** (avatar + nome, ou "⏳ Não atribuído")
- **Preview da última mensagem** (1 linha truncada + ícone do remetente: 👤/🤖/👨‍💻)
- **Tempo desde última msg** humanizado ("há 8 minutos", "há 2 horas", "há 3 dias")
- **Tags** (chips compactos)
- **Canal** (emoji): 📱 whatsapp, ✈️ telegram, 📧 email, 🌐 web
- **Campos personalizados marcados** (Fase 2) — badges adicionais

**Card detalhado (painel direito ou drawer)** espelha `_build_rich_description`:
- Métricas: tempo total, última interação, atendente
- Análise IA: intents detectadas + entidades extraídas (top 5 cada)
- Histórico das últimas 10 mensagens com ícone por remetente e mídia

### Cross-Board Move (mover entre quadros = mudar fluxo)

Quando o usuário arrasta um card para uma coluna de **outro quadro** ([ticket_sync_service.py:794-833](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L794)):
1. Atualizar `atendimento.fluxo_atendimento_id` para o fluxo de destino.
2. Atualizar `atendimento.departamento_id` para `novo_fluxo.departamento_id`.
3. Criar `MovimentoFluxo.criar_movimento(...)` com a nova etapa.
4. Aplicar regras `tipo_etapa` da nova coluna.

**MVP**: pode restringir cross-board ao mesmo departamento; API `/board/move/` aceita `etapa_destino_id` de qualquer fluxo desde a Fase 1.

### Comportamentos Especiais a Replicar

1. **Reordenação automática de colunas** ([signals.py:78-81](../../src/smart_core_assistant_painel/app/trello_sync/signals.py#L78)) — `EtapaFluxo.ordem` reflete na ordem das colunas.
2. **Atribuição automática FILA→TRABALHO** ([ticket_sync_service.py:1046-1076](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L1046)) — atendente que move vira `atendente_humano` + saudação automática.
3. **Finalização automática** ([ticket_sync_service.py:1079-1107](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L1079)) — move para FINALIZACAO dispara `finalizar_atendimento`. Nome com "cancel" → CANCELADO; senão → RESOLVIDO.
4. **Status muda etapa automaticamente** ([trello_sync/signals.py:325-581](../../src/smart_core_assistant_painel/app/trello_sync/signals.py#L325)) — mudar `Atendimento.status` move o card para etapa correspondente. **Signal já existe** — Workspace reflete via SSE.
5. **Sincronização de membro com `atendente_humano`** ([signals.py:173-197](../../src/smart_core_assistant_painel/app/trello_sync/signals.py#L173)) — card mostra avatar/nome do atendente.
6. **Re-render do card a cada nova `Mensagem`** ([signals.py:644-680](../../src/smart_core_assistant_painel/app/trello_sync/signals.py#L644)) — preview reflete última mensagem com tempo humanizado.
7. **Loop prevention** — flag `_syncing_from_trello` evita recursão Trello↔Workspace.

### Acesso à Conversa Completa a Partir do Card

**Requisito**: clicar em qualquer card abre a conversa completa, com possibilidade de enviar mensagens — mesma experiência do WhatsApp Web.

- **Modo Conversas**: layout 3 colunas (sidebar conversas | chat | painel detalhes)
- **Modo Kanban**: layout horizontal full-width
- **Clicar em card no Kanban** (decisão registrada — opção A): abre **drawer/modal de chat** sobreposto sem sair do kanban, com mesmo composer e histórico do Modo Conversas. Fechar volta para o kanban.

### Personalização do Card

Requisito: "será um Trello personalizável".

- **Fase 1 (MVP)**: card exibe `título composto`, `label de prioridade`, `atendente`, `preview última msg`, `tempo`, `canal emoji`, `status emoji`, `tags`.
- **Fase 2**: estender com `CampoPersonalizado.mostrar_no_card` (boolean) — campos marcados aparecem como mini-chips abaixo do preview.
- **Fase 3**: configuração visual por usuário (quais campos exibir/ocultar).

---

## Design System (referência: [base_dashboard.html](../../src/smart_core_assistant_painel/app/core/templates/base_dashboard.html))

### Paleta de Cores

| Token | Valor | Uso |
|---|---|---|
| `--color-gold-primary` | `#a98f71` | Acento principal (estados ativos, hover, foco) |
| `--color-gold-dark` | `#8b7355` | Acento secundário |
| `bg-[#1c1917]` | stone-900 | Sidebar fundo |
| `border-stone-800` | — | Sidebar bordas |
| `text-stone-400` / `text-stone-200` | — | Sidebar inativo / ativo |
| `bg-stone-50` | — | Fundo geral da página |
| `bg-white` | — | Cards e painéis principais |
| `border-stone-200` | — | Bordas suaves |
| `bg-green-50 text-green-600` | — | Ícone WhatsApp / status conectado |
| `bg-amber-50 border-amber-200` | — | Banners de aviso |
| `bg-red-50 text-red-700` | — | Erros, ações destrutivas |
| `bg-[#a98f71]/10 text-[#a98f71]` | — | Item de sidebar ativo |

### Tipografia
- Fonte primária: **Outfit** (Google Fonts), pesos 300-700, carregada em `base.html` via classe `font-outfit`.
- Tamanhos: `text-xs` (uppercase tracking-wider para labels), `text-sm` (corpo), `text-xl font-bold` (títulos de card).

### Componentes Reutilizáveis

**Card padrão**:
```html
<div class="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden">
    <div class="px-6 py-4 border-b border-stone-100 bg-stone-50/50">
        <h2 class="text-xl font-bold text-stone-800 flex items-center">
            <span class="p-2 bg-{COLOR}-50 rounded-lg mr-3 text-{COLOR}-600"><svg .../></span>
            Título
        </h2>
    </div>
    <div class="p-6"> <!-- conteúdo --> </div>
</div>
```

**Botão primário (verde WhatsApp)**:
```html
<button class="px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center">
```

**Botão secundário**:
```html
<button class="px-3 py-2 text-sm border border-stone-300 text-stone-700 rounded-lg hover:bg-stone-50 transition-colors">
```

**Badge de status conectado**:
```html
<div class="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 font-medium">
    <span class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span> Conectado
</div>
```

### Padrões Específicos do Workspace Unificado

1. **Sidebar de conversas**: cards com hover suave, `divide-y divide-stone-100`, avatar circular `bg-[#a98f71] text-white`.
2. **Composer de mensagem**: `border-t border-stone-200`, textarea `border-stone-300 rounded-lg focus:ring-2 focus:ring-[#a98f71]/30`, botão envio `bg-green-600`.
3. **Bolhas de chat**:
   - Recebida (contato): `bg-stone-100 text-stone-800 rounded-2xl rounded-tl-sm`, alinhada à esquerda
   - Enviada (atendente/bot): `bg-[#a98f71]/10 text-stone-800 rounded-2xl rounded-tr-sm`, alinhada à direita
   - Metadata: `text-xs text-stone-400`
4. **Coluna Kanban**: `bg-stone-100 rounded-xl p-3`, header com barra superior de 3px com `cor` da `EtapaFluxo`, cards = `bg-white rounded-lg shadow-sm border border-stone-200 p-3 hover:shadow transition-shadow cursor-pointer`.
5. **Card Kanban (interno)**: estrutura espelhando preview do Trello:
   ```html
   <div class="bg-white rounded-lg shadow-sm border border-stone-200 p-3 hover:shadow cursor-pointer" @click="openChat(card.atendimento_id)">
       <div class="flex items-start justify-between mb-2">
           <span class="text-xs font-semibold {{ prioridade_class }} px-2 py-0.5 rounded-full">{{ prioridade }}</span>
           <span class="text-xs">{{ status_emoji }} {{ canal_emoji }}</span>
       </div>
       <p class="text-sm font-medium text-stone-800 line-clamp-2">{{ titulo }}</p>
       <p class="text-xs text-stone-500 mt-1 line-clamp-1">{{ preview_remetente_icon }} {{ preview_msg }}</p>
       <div class="flex items-center justify-between mt-2 pt-2 border-t border-stone-100">
           <div class="flex items-center text-xs text-stone-500">
               <div class="w-5 h-5 rounded-full bg-[#a98f71] text-white text-[10px] font-bold flex items-center justify-center mr-1">{{ atendente_inicial }}</div>
               <span>{{ atendente_nome|default:"⏳ Não atribuído" }}</span>
           </div>
           <span class="text-xs text-stone-400">{{ tempo_ultima_msg }}</span>
       </div>
       <!-- Campos custom Fase 2 -->
       <div class="flex flex-wrap gap-1 mt-2">
           {% for campo in campos_custom %}
           <span class="text-[10px] bg-stone-100 text-stone-700 px-1.5 py-0.5 rounded">{{ campo.label }}: {{ campo.valor }}</span>
           {% endfor %}
       </div>
   </div>
   ```
6. **Painel direito (detalhes)**: empilhamento de mini-cards (`bg-white rounded-xl shadow-sm border border-stone-200`), headers compactos `px-4 py-3`, corpo `p-4`.
7. **Painel de campos personalizados (Fase 2)**: badges de origem (`BOT` em `bg-blue-50 text-blue-700`, `MANUAL` em `bg-stone-100 text-stone-700`), confiança como barra (`bg-green-500` ≥0.9, `bg-amber-500` 0.6-0.9, `bg-red-500` <0.6).
8. **Drawer de chat (sobre kanban)**: `fixed inset-y-0 right-0 w-full md:w-[600px] bg-white shadow-2xl z-40 transform transition-transform`, com botão fechar no topo, header com info do contato, área de mensagens, composer fixo no rodapé.

### Entrada no Sidebar Global

Adicionar item ao [base_dashboard.html](../../src/smart_core_assistant_painel/app/core/templates/base_dashboard.html) entre "Treinamento IA" e "Gestão":

```html
{% can_view_module "atendimento" as can_atendimento %}
{% if is_owner or can_atendimento %}
<div class="pt-4 pb-2 px-3">
    <p class="text-xs font-semibold text-stone-500 uppercase tracking-wider">Atendimento</p>
</div>
<a href="{% url 'atendimento_unificado:workspace' %}"
    class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg {% if 'workspace' in request.path %}bg-[#a98f71]/10 text-[#a98f71]{% else %}text-stone-400 hover:text-stone-100 hover:bg-stone-800{% endif %} group transition-colors">
    <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
    Workspace
</a>
{% endif %}
```

---

## FASE 1 — MVP: Chat Unificado + Kanban com Paridade Trello (esforço **G+**)

### Estrutura do app novo

Criar [atendimento_unificado/](../../src/smart_core_assistant_painel/app/atendimento_unificado/):

```
atendimento_unificado/
  apps.py                            # AppConfig
  urls.py                            # rotas HTML
  api_urls.py                        # rotas JSON + SSE
  views.py                           # WorkspaceView (HTML shell)
  views_api.py                       # endpoints JSON
  views_sse.py                       # async view → StreamingHttpResponse
  selectors.py                       # queries (lista conversas, kanban por fluxo, fluxos acessíveis)
  services/
    board_service.py                 # mover atendimento entre etapas (com regras tipo_etapa)
    message_dispatch_service.py      # criar Mensagem do atendente
    realtime_publisher.py            # publica eventos no Redis pub/sub
    card_renderer.py                 # payload visual do card (espelha _build_card_name + preview)
  signals.py                         # post_save Mensagem/MovimentoFluxo/Atendimento → publish
  templates/atendimento_unificado/
    workspace.html                   # estende core/templates/base_dashboard.html
    partials/conversation_item.html
    partials/chat_message.html       # variantes por TipoMensagem
    partials/kanban_column.html
    partials/kanban_card.html        # card visualmente equivalente ao Trello
    partials/detail_panel.html
    partials/chat_drawer.html        # drawer/modal acionado ao clicar em card
    partials/custom_fields_panel.html  # placeholder fase 1
  static/atendimento_unificado/
    js/workspace_alpine.js           # store Alpine + EventSource
    css/workspace.css
  migrations/
    0001_initial.py                  # add Atendimento.data_ultima_leitura_atendente
```

Registrar em:
- [core/settings.py](../../src/smart_core_assistant_painel/app/core/settings.py) `INSTALLED_APPS`
- [tenants/db_router.py](../../src/smart_core_assistant_painel/app/tenants/db_router.py) — adicionar `"atendimento_unificado"` ao `TENANT_APPS`
- Criar permissão de módulo `atendimento` (similar a `treinamento`, `configuracoes`)

### Models — alterações mínimas em models existentes

Tudo principal é reaproveitado. Única alteração: adicionar campo a `Atendimento`:

- `data_ultima_leitura_atendente = DateTimeField(null=True, blank=True, db_index=True)` — usado para badge de não-lidos na Fase 1 (evita refactor na Fase 3).

| Necessidade | Reuso |
|---|---|
| Quadro kanban | [`FluxoAtendimento`](../../src/smart_core_assistant_painel/app/operacional/models.py#L498) (1:1 com `TrelloBoard`) |
| Coluna kanban | [`EtapaFluxo`](../../src/smart_core_assistant_painel/app/operacional/models.py#L562) (já tem `cor`, `ordem`, `tipo_etapa`) |
| Card kanban | [`Atendimento.etapa_atual`](../../src/smart_core_assistant_painel/app/atendimentos/models.py#L142) |
| Mover card | `MovimentoFluxo.criar_movimento(...)` (atualiza `etapa_atual` + histórico) |
| Mensagens chat | [`Mensagem`](../../src/smart_core_assistant_painel/app/atendimentos/models.py#L1003) |
| Envio WhatsApp | Signal `_on_message_saved` em [evolution_sync/signals.py:216](../../src/smart_core_assistant_painel/app/evolution_sync/signals.py#L216) |
| Lista conversas | `Atendimento` ordenado por `data_ultima_mensagem` (já indexado) |
| Não-lido | `mensagens.filter(remetente=CONTATO, timestamp__gt=atendimento.data_ultima_leitura_atendente).count()` |

### Layout (3 colunas Conversas, full-width Kanban, drawer ao clicar em card)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Topbar: [Conversas | Kanban]  Fluxo: [Vendas ▾]  Busca               │
├─────────────┬──────────────────────────────┬──────────────────────────┤
│ Sidebar     │ Centro                       │ Painel direito           │
│ Conversas   │ Modo CONVERSAS:              │ - Dados do contato       │
│ (ordenada   │   chat ativo + composer      │ - Atendimento (status,   │
│ por data    │ Modo KANBAN:                 │   etapa, prioridade)     │
│ última msg) │   colunas EtapaFluxo + cards │ - Tags                   │
│             │   (clicar abre drawer)       │ - Custom fields panel    │
└─────────────┴──────────────────────────────┴──────────────────────────┘
```

A coluna direita é **a mesma nos dois modos**.

### Endpoints

**HTML** (`atendimento_unificado/urls.py`):
- `GET /workspace/` → `WorkspaceView` (aceita `?fluxo=<id>`, padrão = último usado salvo em session)

**JSON** (`/workspace/api/`):
| Rota | Verbo | Função |
|---|---|---|
| `/fluxos/` | GET | Lista `FluxoAtendimento` acessíveis ao atendente (popula seletor) |
| `/conversations/` | GET | Sidebar (cursor por `data_ultima_mensagem`, filtro `?fluxo=<id>` opcional) |
| `/conversations/<id>/messages/` | GET | Histórico paginado |
| `/conversations/<id>/send/` | POST | Cria `Mensagem(ATENDENTE_HUMANO)` — signal envia via Evolution |
| `/conversations/<id>/upload/` | POST | Multipart → `Mensagem` com mídia (Fase 3 se Evolution não suportar) |
| `/conversations/<id>/mark-read/` | POST | Atualiza `data_ultima_leitura_atendente=now()` |
| `/conversations/<id>/detail/` | GET | Bloco rico (intents, entidades, métricas, tags) |
| `/board/?fluxo=<id>` | GET | Snapshot Kanban (etapas + cards com payload de render) |
| `/board/move/` | POST | `{atendimento_id, etapa_destino_id}` → `board_service.move_atendimento` |
| `/board/assign/` | POST | `{atendimento_id, atendente_id}` (override manual) |

**SSE** (`/workspace/events/?topics=conversations,board`):
- Eventos: `message.new`, `message.sent`, `board.moved`, `atendimento.assigned`, `atendimento.status_changed`, `heartbeat` (25s)
- Formato: `event: <tipo>\ndata: <json>\n\n`

### Payload do snapshot Kanban `/board/`

```json
{
  "etapas": [
    {"id": 12, "nome": "Em Trabalho", "cor": "#3B82F6", "tipo_etapa": "trabalho", "ordem": 2, "count": 5}
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
        "tags": ["vip"],
        "campos_custom_card": []
      }
    ]
  }
}
```

### Atendente envia mensagem

`message_dispatch_service.send_text(atendimento_id, texto, atendente)`:
1. `Mensagem.objects.create(atendimento=..., remetente=TipoRemetente.ATENDENTE_HUMANO, conteudo="", resposta_bot=texto, metadados={"evolution":{"api_key": <api_key>}})` — segue padrão de [`Atendimento.transferir_para_humano_com_saudacao`](../../src/smart_core_assistant_painel/app/atendimentos/models.py#L762).
2. Signal `_on_message_saved` detecta e envia via `EvolutionWhatsAppService.send_message(...)`.

### Mover atendimento entre etapas — `board_service.move_atendimento`

Espelha exatamente [ticket_sync_service.process_webhook_card_move](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L945):

```python
def move_atendimento(
    atendimento_id: int,
    etapa_destino_id: int,
    atendente_request: Atendente,  # quem fez a ação
) -> None:
    with transaction.atomic(using=router.db_for_write(Atendimento)):
        atendimento = Atendimento.objects.select_for_update().get(id=atendimento_id)
        nova_etapa = EtapaFluxo.objects.select_related('fluxo__departamento').get(id=etapa_destino_id)
        etapa_anterior = atendimento.etapa_atual

        if atendimento.etapa_atual_id == nova_etapa.id:
            return  # idempotente

        # 1. Cross-board: atualizar fluxo + departamento
        novo_fluxo = nova_etapa.fluxo
        novo_dept = novo_fluxo.departamento
        if (atendimento.fluxo_atendimento_id != novo_fluxo.id
            or atendimento.departamento_id != novo_dept.id):
            atendimento.fluxo_atendimento_id = novo_fluxo.id
            atendimento.departamento_id = novo_dept.id

        # 2. Criar MovimentoFluxo (atualiza etapa_atual + histórico)
        MovimentoFluxo.criar_movimento(
            atendimento=atendimento,
            etapa_destino=nova_etapa,
            atendente_destino=None,
            motivo="Movimentação via Workspace",
            automatico=False,
        )

        # 3. Aplicar regras tipo_etapa
        if (etapa_anterior
            and etapa_anterior.tipo_etapa == TipoEtapa.FILA.value
            and nova_etapa.tipo_etapa == TipoEtapa.TRABALHO.value):
            # Assumir atendimento + saudação
            atendimento.transferir_para_humano_com_saudacao(
                atendente_id=atendente_request.id,
            )
        elif nova_etapa.tipo_etapa == TipoEtapa.FINALIZACAO.value:
            # Finalização automática
            nome_lower = nova_etapa.nome.lower()
            novo_status = (
                StatusAtendimento.CANCELADO
                if "cancel" in nome_lower
                else StatusAtendimento.RESOLVIDO
            )
            if atendimento.status != novo_status:
                atendimento.finalizar_atendimento(
                    novo_status=novo_status,
                    solicitar_feedback=False,
                )
        elif nova_etapa.tipo_etapa == TipoEtapa.ESPERA.value:
            atendimento.change_status(
                novo_status=StatusAtendimento.PENDENCIA,
                observacao="Movimentação via Workspace",
            )

    # Trello sync acontece automaticamente via signal post_save em trello_sync/signals.py
    realtime_publisher.publish(tenant_slug, "board.moved", payload)
```

### SSE: implementação

- **Django async view nativa** (Django 4.1+): `views_sse.py` retorna `StreamingHttpResponse(async_generator())`. **Não precisa Channels nem rota ASGI separada.**
- **Gunicorn worker**: `uvicorn.workers.UvicornWorker` (ou processo Uvicorn dedicado). Atualizar `Dockerfile` + `docker-compose.yml`.
- **Redis pub/sub** (broker Celery já presente): `aioredis.from_url(...).pubsub().subscribe(f"sse:{tenant_slug}:events")`.
- **`realtime_publisher.publish(tenant_slug, event_type, payload)`** = wrapper sobre `redis.publish(channel, json.dumps(...))`.
- Signals em `atendimento_unificado/signals.py` ouvem `post_save` de `Mensagem`, `MovimentoFluxo` e `Atendimento` (campos `status`, `atendente_humano`, `etapa_atual`) e chamam `publish(...)`. Tenant via `get_current_tenant_slug()`.
- **Heartbeat**: timer 25s emitindo `: ping\n\n`.
- **Reconexão**: `EventSource` nativa reconecta automaticamente.
- **Nginx**: `proxy_buffering off` e `proxy_read_timeout 1h` na rota SSE — documentar em `.context/docs/`.

### Riscos Fase 1

1. **Gunicorn sync worker trava em SSE** → usar `uvicorn.workers.UvicornWorker` ou Uvicorn dedicado para `/workspace/events/`.
2. **Loop signal Workspace↔Trello** (recursão) → `_syncing_from_trello` flag + dedup em `TrelloWebhookEvent.action_id` + early-return em tasks. Validar manualmente.
3. **Drag-drop muda etapa, regras `tipo_etapa` mexem no status que volta a mover card** → `move_atendimento` aplica em ordem controlada com `update_fields`, reusa lógica testada de `process_webhook_card_move`.
4. **Falta de saudação ao assumir da fila via Workspace** (regressão funcional vs Trello) → roteiro V valida explicitamente.
5. **Atendente sem `Atendente` cadastrado tenta mover para TRABALHO** → API retorna 400; UI mostra modal claro.
6. **Concorrência mover-card** → `select_for_update` (padrão já em `TicketSyncService`).
7. **Multi-tenant SSE** → canal Redis nomeado por tenant; teste com 2 tenants simultâneos.

---

## FASE 2 — Campos personalizados + Extração pelo bot (esforço **G**)

### Models novos (2 tabelas) — em `atendimento_unificado/models.py`

#### `CampoPersonalizado` (definição)
- `slug` SlugField(64)
- `nome` CharField(120)
- `descricao` TextField — também é hint de extração
- `escopo` CharField choices `GLOBAL`/`FLUXO`
- `fluxo` FK → `operacional.FluxoAtendimento` (null se GLOBAL)
- `tipo` choices: `texto`, `numero`, `data`, `escolha`, `multipla_escolha`, `booleano`
- `opcoes` JSONField (lista — para escolha/multipla)
- `obrigatorio` BooleanField
- `extrair_automaticamente` BooleanField(default=True)
- `extrair_hint` CharField(500, blank=True)
- `mostrar_no_card` BooleanField(default=True) — mostra como mini-chip no card do Workspace
- `mostrar_no_card_trello` BooleanField(default=True) — mostra na descrição do card Trello
- `ordem`, `ativo`, `data_criacao`, `data_atualizacao`
- Meta: `unique_together = [("slug","escopo","fluxo")]`, indexes `(escopo, fluxo, ativo)` e `(extrair_automaticamente,)`
- `db_table = "atu_campo_personalizado"`

#### `ValorCampoAtendimento` (valor por atendimento)
- `atendimento` FK → `Atendimento` (related=`valores_campos`)
- `campo` FK → `CampoPersonalizado`
- `valor` JSONField
- `origem` choices `MANUAL`/`BOT`/`IMPORT`
- `confianca` FloatField (null) — populado quando `BOT`
- `mensagem_origem` FK → `Mensagem` (null) — rastreia extração
- `editado_por` FK → `Atendente` (null)
- `data_atualizacao` DateTime
- Meta: `unique_together = [("atendimento","campo")]`, indexes `(atendimento, campo)`, `(campo, valor)` (GIN em PG para busca)
- `db_table = "atu_valor_campo"`

**Nota**: `Atendimento.contexto_conversa` permanece como rascunho livre do bot — não é fonte de verdade dos campos personalizados.

### Feature LLM nova — extração de campos

Caminho: [modules/ai_engine/features/extracao_campos/](../../src/smart_core_assistant_painel/modules/ai_engine/features/extracao_campos/)

Estrutura espelhada de [interpret_media/](../../src/smart_core_assistant_painel/modules/ai_engine/features/interpret_media/) (já implementada):
```
extracao_campos/
  datasource/extracao_campos_datasource.py
  domain/usecase/extracao_campos_usecase.py
  domain/model/campo_extraido.py    # @dataclass CampoExtraido(slug, valor, confianca)
```

- **Parameters** (em `modules/ai_engine/utils/parameters.py`): `ExtracaoCamposParameters(campos_definidos, valores_atuais, chat_history, ultima_mensagem_contato, llm_parameters, error)`.
- **Erro novo**: `ExtracaoCamposError` em `modules/ai_engine/utils/erros.py`.
- **Datasource** usa `with_structured_output` com **schema Pydantic dinâmico** construído via `pydantic.create_model` a partir de `campos_definidos` (apenas campos sem valor ou com `confianca<0.9`).
- **Prompt**: "Analise a conversa e extraia APENAS os campos abaixo cujos valores aparecem explicitamente. Não invente. Retorne `null` se ausente."
- **Threshold de confiança**: ≥0.6 para gravar.
- **Quando rodar**: integrar em [`AttendanceOrchestrator._process_message_and_respond`](../../src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py) **após** resposta gravada. Disparar via Celery task `extract_custom_fields_async(tenant_slug, atendimento_id, mensagem_id)`.
- **Idempotência**: `select_for_update` no atendimento; só sobrescreve `origem=BOT` se `confianca_nova > confianca_atual`. **Nunca sobrescreve `origem=MANUAL`**.
- **Exposição**: adicionar `FeaturesCompose.extracao_campos(parameters)` em [features_compose.py](../../src/smart_core_assistant_painel/modules/ai_engine/features/features_compose.py).

### Injeção no system prompt

Modificar [analise_mensage_datasource.py](../../src/smart_core_assistant_painel/modules/ai_engine/features/analise_mensage/datasource/analise_mensage_datasource.py) (revalidar offsets — plano original cita linhas 241-250, mas pode ter mudado após `feature-interpret-media`):

1. Adicionar em `AnaliseMensageParameters`:
   ```
   campos_coletados: dict[str, Any]   # {slug: valor}
   campos_pendentes: list[dict]       # [{slug, nome, descricao, obrigatorio}]
   ```

2. Inserir nova seção entre "DADOS DA EMPRESA" e "DADOS DO TREINAMENTO":
   ```
   ### CAMPOS COLETADOS DO ATENDIMENTO:
   - cnpj: 12.345.678/0001-99
   - nome_fantasia: Acme Comércio

   ### CAMPOS PENDENTES (solicite ao usuário se vier ao caso, sem insistir):
   - tipo_produto (Tipo de produto desejado): obrigatório
   - medidas (Largura x altura em cm): opcional
   ```

3. Helper `_formatar_campos_coletados(coletados, pendentes) -> str`.

4. Construção dos `parameters` (em `bot_rules_engine` ou onde aplicável) busca `ValorCampoAtendimento.objects.filter(atendimento=...)` + definições aplicáveis (globais ∪ do fluxo).

### Sincronização Trello (estender)

Em [`ticket_sync_service.py`](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py), estender `_build_rich_description` para appendar:

```
---
**Campos coletados:**
- CNPJ: 12.345.678/0001-99
- Tipo de produto: Banner
```

Trigger: signal `post_save` de `ValorCampoAtendimento` → task Celery `trello_sync.tasks.update_card_description(atendimento_id)` com **debounce 5s** (key Redis `update_card:<id>`) para evitar spam quando o bot extrai vários campos seguidos.

### UI Fase 2

- **Admin de definição**: `tenant_admin.py` com `CampoPersonalizadoAdmin` (filtros: escopo, fluxo, ativo).
- **Painel lateral no chat**: template `partials/custom_fields_panel.html` com form Alpine de auto-save por campo.
- **Mini-chips no card kanban**: campos com `mostrar_no_card=True` aparecem como badges abaixo do preview.
- **Endpoints**:
  - `GET /workspace/api/custom-fields/definitions/?fluxo=<id>` → definições aplicáveis.
  - `GET /workspace/api/conversations/<id>/custom-fields/` → valores atuais.
  - `PATCH /workspace/api/conversations/<id>/custom-fields/<slug>/` body `{valor}` → cria/atualiza `ValorCampoAtendimento(origem=MANUAL, editado_por=<request.atendente>)`.
- **Evento SSE novo**: `custom_field.updated` — `{atendimento_id, slug, valor, origem, confianca}`.

### Riscos Fase 2
1. **Schema Pydantic dinâmico** com `create_model` — validar com structured output do LangChain (já usado para `RespostaBot`).
2. **Custo LLM extra por mensagem** → usar modelo barato; pular se nada a extrair; pular se todos têm `confianca>=0.9`.
3. **Race bot vs atendente** → `select_for_update` + regra "nunca sobrescrever MANUAL".
4. **Tenant na task Celery** → ativar tenant via `tenant_context` (padrão já visto em outras tasks).

---

## FASE 3 — Refinamentos (esforço **M**)

### 3.1 Drag-and-drop
- **SortableJS** via CDN, integrado com Alpine via `x-init`. `dragend` → `POST /board/move/`. Em erro, reverter DOM via snapshot do store Alpine.
- Flag `isDragging` no store ignora updates SSE da etapa em movimento por 2s.

### 3.2 Filtros e busca
- Endpoint composto: `/conversations/?q=<txt>&depto=<id>&atendente=<id>&tag=<t>&campo_<slug>=<v>`.
- MVP: `Mensagem.conteudo__icontains` + `Contato.nome_contato__icontains`. PG full-text (`SearchVector`) como débito futuro.
- Filtro por valor de campo: GIN index em `valor`.

### 3.3 SLA e badges avançados
- Badge SLA estourado usando `MovimentoFluxo.duracao_segundos`.
- Badge não-lido (já usa `data_ultima_leitura_atendente` adicionado na Fase 1).

### 3.4 Mídia outbound
- Implementar `EvolutionWhatsAppService.send_media(...)` chamando `/message/sendMedia` da Evolution API.
- Signal Evolution detecta `Mensagem.tipo in (IMAGEM,AUDIO,DOCUMENTO)` e usa `send_media`.
- Endpoint `POST /conversations/<id>/upload/` (multipart) cria `Mensagem` com mídia.

### 3.5 Exportação
- `GET /workspace/api/export/?formato=csv&...` → CSV streaming (Celery task se grande).
- Colunas: atendimento, contato, status, etapa, atendente, **uma coluna por slug de campo**.

### 3.6 Personalização visual do card por usuário
- Atendente pode escolher quais campos exibir/ocultar no card kanban (preferência por usuário, salva em `UserPreference` ou `localStorage`).

### Riscos Fase 3
1. **SortableJS + SSE conflito**: store Alpine guarda flag `isDragging` que ignora updates SSE da etapa em movimento por 2s.
2. **Filtros por campo**: queries com JOINs em `valores_campos` exigem index parcial PG.
3. **Export grande**: `StreamingHttpResponse` + `.iterator(chunk_size=500)`.

---

## Critical Files

**Fase 1** (criar):
- [atendimento_unificado/views_sse.py](../../src/smart_core_assistant_painel/app/atendimento_unificado/views_sse.py)
- [atendimento_unificado/services/board_service.py](../../src/smart_core_assistant_painel/app/atendimento_unificado/services/board_service.py) — **lógica de paridade Trello**
- [atendimento_unificado/services/card_renderer.py](../../src/smart_core_assistant_painel/app/atendimento_unificado/services/card_renderer.py) — **espelha `_build_card_name`**
- [atendimento_unificado/services/realtime_publisher.py](../../src/smart_core_assistant_painel/app/atendimento_unificado/services/realtime_publisher.py)
- [atendimento_unificado/templates/atendimento_unificado/workspace.html](../../src/smart_core_assistant_painel/app/atendimento_unificado/templates/atendimento_unificado/workspace.html)
- [atendimento_unificado/templates/atendimento_unificado/partials/kanban_card.html](../../src/smart_core_assistant_painel/app/atendimento_unificado/templates/atendimento_unificado/partials/kanban_card.html)
- [atendimento_unificado/templates/atendimento_unificado/partials/chat_drawer.html](../../src/smart_core_assistant_painel/app/atendimento_unificado/templates/atendimento_unificado/partials/chat_drawer.html)

**Fase 1** (editar):
- [core/settings.py](../../src/smart_core_assistant_painel/app/core/settings.py) — INSTALLED_APPS
- [tenants/db_router.py](../../src/smart_core_assistant_painel/app/tenants/db_router.py) — TENANT_APPS
- [core/templates/base_dashboard.html](../../src/smart_core_assistant_painel/app/core/templates/base_dashboard.html) — entrada "Atendimento → Workspace" no sidebar
- `Dockerfile` + `docker-compose.yml` — Gunicorn com `UvicornWorker`
- Configuração Nginx/deploy (documentar `proxy_buffering off`)

**Fase 2** (criar):
- [atendimento_unificado/models.py](../../src/smart_core_assistant_painel/app/atendimento_unificado/models.py) — `CampoPersonalizado`, `ValorCampoAtendimento`
- [modules/ai_engine/features/extracao_campos/](../../src/smart_core_assistant_painel/modules/ai_engine/features/extracao_campos/) — feature DDD completa
- Migration `atendimento_unificado/migrations/0002_campos_personalizados.py`

**Fase 2** (editar):
- [analise_mensage_datasource.py](../../src/smart_core_assistant_painel/modules/ai_engine/features/analise_mensage/datasource/analise_mensage_datasource.py) — injeção dos campos (revalidar offsets)
- [modules/ai_engine/utils/parameters.py](../../src/smart_core_assistant_painel/modules/ai_engine/utils/parameters.py) — `campos_coletados` em `AnaliseMensageParameters`
- [modules/ai_engine/utils/erros.py](../../src/smart_core_assistant_painel/modules/ai_engine/utils/erros.py) — `ExtracaoCamposError`
- [modules/ai_engine/features/features_compose.py](../../src/smart_core_assistant_painel/modules/ai_engine/features/features_compose.py) — método `extracao_campos`
- [atendimentos/services/attendance_orchestrator.py](../../src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py) — disparar Celery task pós-resposta
- [trello_sync/services/ticket_sync_service.py](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py) — `_build_rich_description` estendido com campos coletados

---

## Verificação ponta a ponta

### Fase 1 — MVP + Paridade Trello

**Chat (V.1.a)**:
1. Acessar `/workspace/`, ver lista de conversas (sidebar) e chat ativo ao clicar.
2. Enviar mensagem pelo composer → confirmar que chega no WhatsApp do contato (testar com instância real).
3. `mark-read` decrementa badge de não-lidos.
4. Abrir 2 abas com `/workspace/` → enviar/mover em uma → ver atualização ao vivo na outra (validação SSE).

**Paridade Trello (V.1.b) — crítico**:
1. Topbar tem seletor de **Fluxo** mostrando todos os fluxos do departamento.
2. Cards no kanban renderizam visual equivalente ao Trello (título composto, label de prioridade, atendente, preview, tempo).
3. **Clicar em card abre chat drawer** sobre o kanban (não muda de tela).
4. Mover card **FILA → TRABALHO** atribui atendente E envia saudação automática (verificar `Mensagem` criada via `transferir_para_humano_com_saudacao`).
5. Mover para etapa **FINALIZACAO** com nome "Resolvido" encerra atendimento com status `RESOLVIDO`.
6. Mover para etapa com nome "Cancelado" encerra com `CANCELADO`.
7. Mover para etapa **ESPERA** muda status para `PENDENCIA`.
8. Mover card para coluna de **OUTRO fluxo** (cross-board) atualiza `atendimento.fluxo_atendimento_id` e `departamento_id`.
9. Mudar `Atendimento.status` via outra origem (ex: bot) move card no Workspace e no Trello.

**Trello sincronizado (V.1.c)**:
1. Mover card FILA → TRABALHO no Workspace → reflete no Trello em ≤5s.
2. Mover card no Trello → reflete no Workspace em ≤5s (webhook → signal → SSE).
3. Verificar logs: nenhum signal duplicado, sem erro `_syncing_from_trello`.

**Carga + qualidade**:
1. Carga: 50 conversas + 1000 mensagens → tempo de carregar sidebar < 500ms.
2. Board com 30 cards × 6 colunas < 800ms.
3. `ruff format` + `ruff check` + `pyright --strict` sem erros.
4. Auditoria de segurança: autorização por rota, isolamento tenant SSE, atendente só vê fluxos permitidos.

### Fase 2 — Campos personalizados

1. Criar definição global "CNPJ" e definição por fluxo "tipo_produto" no admin.
2. Em uma conversa nova, contato envia "Meu CNPJ é 12.345.678/0001-99 e quero um banner".
3. Após resposta do bot, abrir o painel direito → ver `cnpj` e `tipo_produto` preenchidos com `origem=BOT` + ícone de confiança.
4. Editar manualmente um campo no painel → próxima extração do bot **não deve sobrescrever**.
5. Verificar no Trello: descrição do card mostra "Campos coletados: CNPJ: ..." (após debounce de 5s).
6. Próxima mensagem do contato: verificar log do prompt — seção `### CAMPOS COLETADOS DO ATENDIMENTO:` presente com os valores.
7. Cards do Kanban no Workspace mostram chips dos campos marcados com `mostrar_no_card=True`.

### Fase 3 — Refinamentos

1. Drag-drop de card no kanban — sem flicker, com rollback se erro.
2. Filtro por campo personalizado: `?campo_tipo_produto=banner` retorna apenas atendimentos com esse valor.
3. Badge não-lido decrementa ao abrir conversa.
4. Badge SLA estourado destacado.
5. Atendente envia imagem via composer — chega no WhatsApp do contato.
6. Export CSV com 5000 linhas — completo em < 30s, sem timeout.
7. Atendente personaliza quais campos aparecem no card kanban.

---

## Métricas de Sucesso

- Sidebar de conversas carrega em <500ms com 50 conversas + 1000 mensagens
- Snapshot Kanban com 30 cards × 6 colunas em <800ms
- Movimentação de card no Workspace reflete no Trello em <5s (signal + task existentes)
- Movimentação de card no Trello reflete no Workspace em <5s (webhook + signal SSE)
- **Paridade Trello 100%**: todos os comportamentos do roteiro V.1.b passam (assumir, finalização auto, cross-board, status sync, saudação)
- Extração de campo do bot tem `confianca≥0.6` em ≥80% dos casos de teste manual
- Nenhum vazamento cross-tenant em teste com 2 tenants simultâneos

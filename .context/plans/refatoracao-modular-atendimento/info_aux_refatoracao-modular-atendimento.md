# Documentação Auxiliar — Refatoração Modular do Atendimento Unificado

> Gerado em: 2026-05-22
> Plano canônico: `.context/plans/refatoracao-modular-atendimento.md`
> Plano completo: `.context/plans/refatoracao-modular-atendimento/plano_completo_refatoracao-modular-atendimento.md`

Coletado via MCP context7 (libs) + WebSearch/WebFetch (serviços externos), por subagentes `haiku`.

---

## Libs Python / Frontend

### Django (5.2.7) — `library ID: /websites/djangoproject_en_5_2`

#### 1. Proxy models / `managed=False` / `db_table`
- **Proxy model** (`proxy=True`): herda a tabela do model pai, não cria tabela nova, não gera migration. Para estender comportamento Python.
- **`managed=False`**: Django não cria/altera/deleta a tabela. Para apontar para tabela criada por outro app/banco legado.
- **Recomendação oficial 5.2**: para compartilhar models entre apps, **importe o model canônico** do app dono em vez de duplicar com `managed=False`. Duplicar definição com mesma `db_table` faz o Django detectar inconsistência e quebrar `makemigrations`. Use `managed=False` apenas para integração com banco legado / views de banco.
- ✅ **Aplicação no plano:** `chat_evolution/models.py` e `gestao_kanban/models.py` contêm APENAS docstring instruindo importar de `atendimento_unificado.models`. A abordagem `managed=False`/`db_table="atu_*"` do plano original foi **abandonada** (commit `db787ca`).

```python
# Consumo direto do model canônico
from smart_core_assistant_painel.app.atendimento_unificado.models import (
    CampoPersonalizado, Etiqueta, EtiquetaAtendimento, Nota, ValorCampoAtendimento,
)
```

#### 2. Signals
- Registrar SEMPRE em `AppConfig.ready()` (importando o módulo `signals`), nunca em import de módulo de topo.

```python
class ChatEvolutionConfig(AppConfig):
    name = "smart_core_assistant_painel.app.chat_evolution"
    def ready(self):
        from . import signals  # noqa: F401

@receiver(post_save, sender=Mensagem)
def publica_sse(sender, instance, **kwargs): ...
```

#### 3. StreamingHttpResponse / SSE
- `StreamingHttpResponse(generator, content_type="text/event-stream")`. Sem `content`/`Content-Length`/`ETag` automáticos; muitos middlewares não funcionam com streaming.
- **WSGI bloqueia o worker durante o streaming** (cada conexão SSE prende um worker) — preferir **ASGI** com generator `async` para SSE/long-polling. Tratar `asyncio.CancelledError` para cleanup ao desconectar.

```python
async def stream(request):
    async def gen():
        async for chunk in canal_async():
            yield f"data: {chunk}\n\n".encode()
    return StreamingHttpResponse(gen(), content_type="text/event-stream")
```

#### 4. URLconf — `include`, `namespace`, `app_name`
- App define `app_name = "chat_evolution"` no seu `api_urls.py`; o projeto inclui via `path("chat/", include("...chat_evolution.api_urls"))`. Namespace resolvido automaticamente pelo `app_name`. Pode-se passar tupla `([...], "app_name")` para namespace explícito.

#### 5. STATICFILES_DIRS e TEMPLATES['DIRS']
- Diretórios fora dos apps (módulo agnóstico `modules/design_system`) entram em `STATICFILES_DIRS` e em `TEMPLATES[0]["DIRS"]`. Suporta tuplas `(prefix, path)` para prefixar staticfiles.

**Breaking changes 5.2:** nada crítico para esses recursos. `managed=False` e signals em `ready()` seguem suportados; SSE com ASGI é o caminho recomendado.

---

### Alpine.js (v3) — `library ID: /websites/alpinejs_dev`

#### `Alpine.data(name, cb)` e `Alpine.store(name, obj)`
- Registrar SEMPRE dentro de `document.addEventListener('alpine:init', ...)`. Componentes via `Alpine.data('chat', () => ({...}))` usados com `x-data="chat"`; estado global via `Alpine.store('workspace', {...})` acessado por `$store.workspace`.

#### Ciclo de vida — armadilha crítica de ordem
| Evento | Quando | Uso |
|--------|--------|-----|
| `alpine:init` | ANTES do Alpine percorrer o DOM | Registrar `data`/`store`/`directive` |
| `alpine:initialized` | DEPOIS de tudo inicializado | Código pós-init (ex.: instanciar SortableJS) |

- **Gotcha de `defer`:** se TODOS os scripts usam `defer`, eles executam em ordem de aparição. Os módulos (`chat_alpine.js`, `kanban_alpine.js`, `workspace_store.js`) devem ser carregados ANTES (ou junto) do core do Alpine, para que o listener `alpine:init` deles já esteja registrado quando o Alpine disparar `alpine:init`. Registrar `Alpine.data` fora de `alpine:init` falha silenciosamente.

#### `Alpine.directive` e `$dispatch`
- Diretivas customizadas registradas em `alpine:init`: `Alpine.directive('format-date', (el, {expression}, {evaluate}) => {...})`.
- Comunicação entre componentes: `$dispatch('evento', {detalhe})`. Para componentes distantes no DOM use `.window`: `@card-clicked.window="..."` + `$dispatch('card-clicked', {id})`.

---

### Tailwind CSS (v4) — `library ID: /tailwindlabs/tailwindcss.com`

#### CSS-first (`@theme`) — sem `tailwind.config.js`
```css
@import "tailwindcss";

@theme {
  --color-workspace-accent: #2563eb;
  --spacing-panel: 24rem;
  --font-workspace: "Inter", sans-serif;
}
```
- v4 abandonou `tailwind.config.js`; tokens viram **variáveis CSS** (`var(--color-workspace-accent)`) E utilities (`.bg-workspace-accent`) automaticamente. `@theme` sempre no topo, nunca aninhado.

#### `@utility` e `@layer components`
- `@layer utilities`/`@layer components` (modo plugin v3) substituídos por `@utility nome { ... }` para utilities. `@layer components { .classe {...} }` ainda é válido para classes de componente com pseudo-elementos/media queries.

#### Diretivas legadas e build de produção
- `@tailwind base/components/utilities` ainda funcionam, mas o preferido é só `@import "tailwindcss"`.
- **Build de produção (CRÍTICO):** `@tailwindcss/browser` (CDN, usado em `core/templates/base.html`) é **dev-only** — compila no navegador em runtime, sem purge, ruim em produção. Para produção usar `@tailwindcss/postcss` (PostCSS) ou `@tailwindcss/cli`, gerando CSS estático servido via `staticfiles`. Em v4 `postcss-import` e `autoprefixer` não são mais necessários.

---

### SortableJS — fontes: github.com/SortableJS/Sortable, sortablejs.github.io/Sortable

- Init: `new Sortable(el, options)`. Opções p/ kanban: `group: { name, pull, put }` (listas conectadas), `animation`, `handle`, `ghostClass`, `dragClass`, `filter`.
- Callbacks: `onEnd(evt)`, `onAdd`, `onUpdate` com `evt.item`, `evt.from`, `evt.to`, `evt.oldIndex`, `evt.newIndex` → persistir via `fetch`.
- **Gotcha com Alpine `x-for`:** quando o Sortable reordena o DOM, o array reativo do Alpine fica dessincronizado. Após `onEnd`, sincronizar o array (`splice` old/new index) OU re-render a partir do estado. Instanciar o Sortable em `alpine:initialized`/`init()` do componente, sobre `$refs`.

```javascript
new Sortable(this.$refs.list, {
  group: { name: 'kanban', pull: true, put: true },
  animation: 150,
  onEnd: (evt) => {
    fetch('/workspace/kanban/api/cards/' + evt.item.id + '/mover/', { method: 'POST', /* ... */ })
  }
})
```

---

## Serviços Externos

### Evolution API "Evolution Go" (v2.3.7, whatsmeow) — server `http://76.13.229.210:8080`, instância `atendimento`

#### Autenticação
- Header `apikey` em todos os endpoints. Endpoints de mensagem (`/message/*`, `/chat/*`) usam o **token da instância**; gerenciamento (`/instance/*`) usa o **token global**. `Content-Type: application/json`.

#### `POST /message/sendText/{instance}`
```json
{ "number": "553198296801", "text": "Olá!", "delay": 1000, "quoted": { "key": {...} } }
```
Resposta 201 com `key.id`, `status: "PENDING"`. Erros: 400 (número/texto inválido), 401 (token), 404 (instância), 500 (payload grande).

#### `POST /message/sendMedia/{instance}`
```json
{ "number": "...", "mediatype": "image|video|document|audio", "mimetype": "image/jpeg",
  "media": "<base64-puro-ou-URL>", "fileName": "foto.jpg", "caption": "..." }
```
- **CRÍTICO:** vídeos/arquivos > 3MB → SEMPRE URL (base64 causa `500 Maximum call stack`). Base64 SEM prefixo `data:`. Rate prático ~10-20 msg/min/instância.

#### `POST /message/sendWhatsAppAudio/{instance}` (PTT)
```json
{ "number": "...", "audio": "<base64-ou-URL>", "encoding": true }
```
`encoding:true` = base64; `false` = URL. Marca `ptt:true`.

#### `PUT /chat/markMessageAsRead/{instance}`
```json
{ "read_messages": [ { "remoteJid": "...@s.whatsapp.net", "fromMe": false, "id": "<key.id>" } ] }
```
Marca leitura EXPLÍCITA (ticks azuis) — chamar só após resposta do bot/atendente ou abertura da conversa.

#### `POST /chat/sendPresence/{instance}`
```json
{ "number": "...", "delay": 3000, "presence": "composing" }
```
`composing` = "digitando…", `recording` = "gravando…". `delay` em ms.

#### `PUT /instance/{instance_id}/advanced-settings`
```json
{ "readMessages": false }
```
- **CRÍTICO:** `readMessages` DEVE ser `false`. Com `true`, o whatsmeow envia recibo de leitura automático no protocolo para TODA mensagem recebida (ticks azuis), independente do app. Instância `atendimento` UUID `3bb88a86-b965-4a30-8164-91d47877aad4`. `server_url` em `tenants_tenantevolution.server_url` (db `smart_core_db`).

#### Webhook `messages.upsert` (recebimento)
- `webhookBase64: false` (true gera payloads > 50MB que crasham Gunicorn). Payload traz `data.key.id` (usar em markAsRead), `data.key.remoteJid`, `data.key.fromMe`, `data.pushName`, `data.message.{conversation|imageMessage|audioMessage}`, `data.messageTimestamp`.

#### Limitações / problemas conhecidos
- Rate ~10-20 msg/min (anti-spam) → fila com delay 3s+. Base64 máx ~3MB. WhatsApp stream pode morrer (503) com container "Up" → healthcheck via `/instance/fetchInstances` (`connectionStatus:"open"`).

---

## Notas Gerais (gotchas que afetam o plano)
1. **Models cross-app:** import canônico, não `managed=False` (Django 5.2 + commit `db787ca`).
2. **SSE:** preferir ASGI/async generator; em WSGI cada conexão prende um worker.
3. **Alpine:** registrar `data`/`store` em `alpine:init`; cuidado com ordem de `defer`; instanciar SortableJS em `init()`/`alpine:initialized`.
4. **Tailwind v4:** CSS-first (`@theme`/`@utility`); CDN browser é dev-only → produção exige build PostCSS/CLI.
5. **SortableJS + Alpine:** sincronizar array reativo após `onEnd`.
6. **Evolution:** `readMessages=false`; mídia grande via URL; `webhookBase64=false`; markAsRead explícito.

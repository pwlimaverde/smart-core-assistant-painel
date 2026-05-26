# Chat Integrado estilo WhatsApp Web — Plano de Melhorias Completo

> **Status atual**: A branch `feature/chat-whatsapp-redesign` já entrega o piso da experiência (mídia inline visível, lightbox, toggle de análise IA, card com nome+assunto separados, normalização de push_name). Este documento mapeia o **caminho restante** para que o atendente nunca mais precise abrir o WhatsApp Web em paralelo.
>
> **Objetivo**: Concentrar 100% da operação WhatsApp do operador dentro do kanban + chat do painel.
>
> **Premissa**: O servidor de WhatsApp vai migrar para **Evolution Go**, então as melhorias aproveitam endpoints novos quando aplicável.

---

## 1. Mapa do gap atual vs. WhatsApp Web

| Capacidade WhatsApp Web | Status no painel hoje | Necessário? |
|---|---|---|
| Bolhas de envio/recebimento diferenciadas | ✅ Pronto (.ws-bub--in/out) | — |
| Mídia visível inline + click abre maior | ✅ Pronto na branch atual | — |
| Áudio reproduzível | ✅ Player nativo | — |
| Documento baixável / PDF previewable | ✅ Pronto na branch atual | — |
| Análise IA discreta (toggle) | ✅ Pronto na branch atual | — |
| ✓ enviado / ✓✓ entregue / ✓✓ azul lido | ⚠️ Parcial (só ✓ vs ✓✓ binário) | **Crítico** |
| "Está digitando..." (presença do contato) | ❌ Ausente | **Crítico** |
| Enviar "digitando..." para o cliente quando o atendente está compondo | ❌ Ausente | Importante |
| Marcar como lido (✓✓ azul) quando o atendente abre a conversa | ❌ Ausente | **Crítico** |
| Resposta citada (reply em mensagem específica) | ❌ Ausente | **Crítico** |
| Reações emoji (👍 ❤️ 😂...) | ❌ Ausente | Importante |
| Encaminhar mensagem | ❌ Ausente | Médio |
| Excluir para todos | ❌ Ausente | Médio |
| Edição de mensagem enviada | ❌ Ausente | Baixo |
| Mensagem de voz (gravar áudio no painel) | ❌ Ausente | **Crítico** |
| Anexar arquivo via clip ou drag&drop | ⚠️ Botão existe, mas falta drag&drop | Importante |
| Preview de link/URL (unfurl) | ❌ Ausente | Baixo |
| Stickers | ❌ Ausente | Baixo |
| Localização (mapa) | ❌ Ausente | Baixo |
| Contato compartilhado (vCard) | ❌ Ausente | Baixo |
| Separadores de data ("Hoje", "Ontem") | ❌ Ausente | Importante |
| Agrupamento visual de mensagens consecutivas | ❌ Ausente | Médio |
| Avatar real do contato (foto WhatsApp) | ❌ Ausente (só iniciais) | Importante |
| Status online / last seen no header | ❌ Ausente | Importante |
| Scroll-to-bottom button quando rolado pra cima | ❌ Ausente | Importante |
| Lazy load de mensagens antigas | ⚠️ Há paginação API mas falta scroll trigger | Médio |
| Busca dentro da conversa | ❌ Ausente | Médio |
| Notificação sonora/toast de nova mensagem | ❌ Ausente | Importante |
| Indicador de mensagens não lidas + jump | ⚠️ Badge no card existe; falta divisor "novas mensagens" no chat | Médio |
| Atalhos de teclado (Ctrl+F, setas...) | ⚠️ Tem Alt+1/2/3; falta foco em mensagens | Baixo |
| Notificações desktop (Web Push) | ❌ Ausente | Baixo |
| Tema escuro | ⚠️ Token `[data-theme="dark"]` existe; falta switch UI | Baixo |

---

## 2. Capacidades Evolution Go que estamos subaproveitando

Estes endpoints já existem na Evolution Go e podem alimentar funcionalidades grandes do chat:

### 2.1. Storage S3/MinIO nativo (substitui `_fetch_media_base64_from_evolution`)

**Hoje:** o webhook chega só com URL encriptada do CDN do WhatsApp; nosso código faz `getBase64FromMediaMessage` e decodifica para `FileField` local.

**Com Evolution Go + MinIO/S3 configurado:** o payload já chega com `data.message.mediaUrl` apontando para o arquivo decodificado no nosso bucket. Sem decodificação no Django.

**Impacto:** elimina o pico de CPU do worker no recebimento de mídia; reduz código.

```json
{
  "event": "MESSAGE",
  "data": {
    "message": {
      "mediaUrl": "https://files.minha-empresa.com/evolution/abc.jpg",
      "imageMessage": { "caption": "..." }
    }
  }
}
```

### 2.2. `POST /message/presence` — mostrar "digitando…" no WhatsApp do cliente

Quando o atendente começa a digitar no painel, podemos avisar o cliente do outro lado. Estado `composing` (texto) ou `composing + isAudio=true` (áudio).

```bash
POST /message/presence
{
  "number": "5511999999999",
  "state": "composing",
  "isAudio": false
}
```

**UX:** o cliente vê "digitando..." abaixo do nome no WhatsApp dele — humaniza o atendimento.

### 2.3. `POST /message/markread` — marcar como lido (✓✓ azul)

```bash
POST /message/markread
{
  "number": "5511999999999",
  "id": ["3EB0C5A277F7F9B6C599", "..."]
}
```

**UX:** quando o atendente abre a conversa no painel, o cliente vê o ✓✓ azul no WhatsApp dele — feedback essencial.

### 2.4. `POST /message/react` — reações emoji

```bash
POST /message/react
{ "number": "...", "reaction": "👍", "id": "3EB0C5A...", "fromMe": false }
```

**UX:** atendente confirma recebimento de informação com 👍 sem precisar digitar resposta.

### 2.5. Eventos webhook valiosos que provavelmente não tratamos

Pelos eventos suportados (Evolution v2 / Go):

- **`MESSAGES_UPDATE`** — atualização de status (delivered/read). Permite `respondida` evoluir para ✓✓ azul de fato em vez de bool.
- **`CONTACTS_UPDATE`** — foto de perfil / nome / status do contato mudou. Permite manter foto/nome sincronizados.
- **`PRESENCE_UPDATE`** *(Baileys)* — o contato está online / digitando / gravando áudio. Alimentaria o "Maria está digitando..." abaixo do nome.
- **`CALL`** — chamada recebida no número. Mostra notificação no painel.
- **`GROUPS_UPSERT` / `GROUP_PARTICIPANTS_UPDATE`** — relevante se um dia atender grupos.

### 2.6. WebSocket nativo (alternativa ao webhook)

Evolution Go suporta WebSocket para eventos em tempo real. Combinado com o SSE atual do painel, dá pra reduzir latência percebida das atualizações de mensagem/presença.

---

## 3. Roadmap proposto, organizado por fase

Priorização por **impacto na sensação de WhatsApp Web** × **esforço**:

### 🟢 Fase 1 — Quick wins de UX (3-5 dias)

1. **Read receipts bidirecionais (✓✓ azul)**
   - Frontend: marcar `mensagem.respondida` granular — `enviada | entregue | lida` em vez de bool.
   - Tratar evento `MESSAGES_UPDATE` no webhook para atualizar status real.
   - Ao abrir conversa no painel, disparar `POST /message/markread` para Evolution → cliente vê ✓✓ azul.
   - Visual: ✓ cinza (enviada), ✓✓ cinza (entregue), ✓✓ azul (#34b7f1) lida — já temos token CSS pronto.

2. **Separadores de data + agrupamento visual**
   - Inserir `<div class="ws-chat__day-sep">Hoje / Ontem / DD/MM/AAAA</div>` entre mensagens de dias diferentes.
   - Bolhas consecutivas do mesmo remetente em janela curta (~2min): suprimir avatar/border-top-radius para visual "stacked".

3. **Scroll-to-bottom + divisor "novas mensagens"**
   - Botão flutuante no canto inferior direito do chat quando o usuário rolou >300px pra cima.
   - Linha "▼ N novas mensagens" inserida no ponto onde a leitura parou (idem WhatsApp Web).

4. **Drag & drop de arquivo no chat**
   - Listener `drop` no `.ws-chat__body` → injeta arquivo no composer / envia direto. Reaproveita endpoint de upload existente.

5. **Avatar real do contato (foto WhatsApp)**
   - Tratar evento `CONTACTS_UPDATE` para baixar `profilePictureUrl` e salvar em `Contato.foto_perfil` (novo FileField). Fallback para iniciais quando ausente.

6. **Auto-marcar como lido ao abrir conversa**
   - No `_doOpenChat` (workspace_alpine.js), após `messages` carregar, chamar endpoint local que: (a) marca `Mensagem.lido=True` no banco; (b) dispara `markread` na Evolution.

### 🟡 Fase 2 — Funcionalidades core que faltam (5-8 dias)

7. **Resposta citada (reply)**
   - Backend: tratar `contextInfo.quotedMessage` no payload do webhook → guardar em `Mensagem.respondendo_a` (FK self).
   - Endpoint POST `/send/text` aceita `quoted` com a key da mensagem original.
   - UI: hover na bolha mostra menu (▼); item "Responder" gera preview no composer.
   - Balão renderiza tira lateral colorida com preview da mensagem citada (.ws-bub__reply).

8. **Reações emoji**
   - Modelo `MensagemReacao(mensagem, emoji, remetente, timestamp)`.
   - Tratar payload com `reactionMessage` no webhook.
   - UI: bolha pequena colada na parte inferior do balão (`.ws-bub__reactions`).
   - Hover → mini-picker com 6 emojis comuns; aciona `POST /message/react`.

9. **"Atendente está digitando..." OUT**
   - Composer dispara debounce 400ms → `POST /message/presence state=composing` na Evolution.
   - Stop typing após 5s sem alteração ou ao enviar.

10. **"Cliente está digitando..." IN**
    - Tratar evento `PRESENCE_UPDATE` no webhook → broadcast via SSE/WebSocket.
    - Mostrar linha "digitando..." abaixo do nome do contato no header do chat.

11. **Gravação de mensagem de voz no painel**
    - Componente Alpine usa `MediaRecorder API` (browser nativo) → captura WebM/OGG.
    - Endpoint POST `/api/atendimento/{id}/send_audio` faz upload e envia via `/send/media type=audio`.
    - UI: botão de microfone no composer; durante gravação mostra waveform fake + duração + cancelar/enviar.

12. **Notificação toast + som de mensagem nova**
    - Toast canto inferior direito quando chega mensagem em conversa não-ativa.
    - Som curto (WhatsApp original tem signature sound) — `<audio>` cacheável.
    - Respeitar setting `silencio` por atendente (opt-out).

### 🟡 Fase 3 — Storage e infra (paralelo, 2-3 dias)

13. **Migrar mídia para S3/MinIO via Evolution Go**
    - Configurar bucket S3/MinIO no Evolution Go (`MEDIA_STORAGE`).
    - No webhook receiver, detectar `data.message.mediaUrl` no novo formato; salvar URL direto em `Mensagem.metadados['media_url']` e pular o `_fetch_media_base64_from_evolution`.
    - Backwards-compat: manter caminho legado durante migração.
    - Adicionar campo `Mensagem.midia_url_remota: URLField` para evitar `FileField` quando o arquivo já está em CDN.

14. **WebSocket Evolution Go → painel**
    - Conexão persistente Django ↔ Evolution Go via WS para receber eventos com latência baixa (~50ms vs ~200ms do webhook HTTP).
    - Mantém webhook como fallback.

### 🔴 Fase 4 — Recursos avançados (sob demanda)

15. **Encaminhar mensagem entre atendimentos**
    - Modal de seleção de contato/atendimento; reusa `/send/media` ou `/send/text` com flag `forwarded:true`.
    - Mostra badge "↪ Encaminhada" no balão.

16. **Excluir para todos / editar mensagem**
    - Evolution Go endpoints `revoke` / `edit`.
    - Confirmação modal; UI marca como "Esta mensagem foi apagada".

17. **Preview de URL (link unfurl)**
    - Worker assíncrono: ao receber mensagem com URL, baixa `<meta og:*>` da página e injeta `Mensagem.metadados['url_preview']`.
    - UI mostra card horizontal com imagem + título + descrição abaixo do texto.

18. **Busca dentro da conversa**
    - Input search no header do chat → highlight de matches + jump entre eles (n/N).

19. **Status online / last seen do contato**
    - `PRESENCE_UPDATE` traz `unavailable` + timestamp.
    - Mostrar "online" ou "visto por último às 14:32" abaixo do nome no header.

20. **Notificações desktop (Web Push)**
    - Service Worker + Permission API; manda push quando há nova mensagem e a aba não está visível.

21. **Stickers / localização / contato compartilhado**
    - Tratar `stickerMessage`, `locationMessage`, `contactMessage` no webhook.
    - Renderização específica no template.

22. **Tema escuro com switch UI**
    - Já temos tokens `[data-theme="dark"]`. Falta toggle no header + persistência.

---

## 4. Mudanças de modelo recomendadas (em camadas)

```python
# atendimentos/models.py — Mensagem (adições)
status_envio = CharField(choices=[("pendente","Pendente"),("enviada","Enviada"),
                                  ("entregue","Entregue"),("lida","Lida"),
                                  ("falhou","Falhou")], default="pendente")
data_entregue = DateTimeField(null=True, blank=True)
data_lida = DateTimeField(null=True, blank=True)
respondendo_a = ForeignKey("self", null=True, blank=True, on_delete=SET_NULL,
                           related_name="respostas")
encaminhada = BooleanField(default=False)
editada_em = DateTimeField(null=True, blank=True)
apagada = BooleanField(default=False)
midia_url_remota = URLField(blank=True, null=True, max_length=500)  # S3/MinIO

# atendimentos/models.py — novo modelo
class MensagemReacao(models.Model):
    mensagem = ForeignKey(Mensagem, related_name="reacoes", on_delete=CASCADE)
    emoji = CharField(max_length=8)  # emoji unicode
    remetente = CharField(choices=TipoRemetente.choices, max_length=20)
    timestamp = DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = [("mensagem","emoji","remetente")]

# clientes/models.py — Contato (adições)
foto_perfil = FileField(upload_to="contatos/fotos/%Y/%m/", null=True, blank=True)
foto_perfil_url_remota = URLField(blank=True, null=True, max_length=500)
ultimo_visto = DateTimeField(null=True, blank=True)
online = BooleanField(default=False)
status_whatsapp = CharField(max_length=139, blank=True, default="")  # recado/about
```

---

## 5. Novos endpoints Django sugeridos

| Método | URL | Função |
|---|---|---|
| POST | `/api/atendimento/{id}/mark-read` | Marca todas as mensagens do contato como lidas + dispara `markread` na Evolution |
| POST | `/api/atendimento/{id}/typing` | Body `{state: composing\|paused, audio: bool}` → propaga para `/message/presence` |
| POST | `/api/atendimento/{id}/react` | Body `{mensagem_id, emoji}` → grava reação e propaga via `/message/react` |
| POST | `/api/atendimento/{id}/send-audio` | Multipart com blob WebM/OGG → envia áudio gravado no browser |
| POST | `/api/atendimento/{id}/send-reply` | Body `{texto, respondendo_a_id}` → envia reply com `contextInfo` |
| GET | `/api/atendimento/{id}/messages/search?q=…` | Busca textual dentro da conversa |
| POST | `/api/atendimento/{id}/forward` | Encaminha mensagem para outro destinatário |

---

## 6. Mudanças na UI / Alpine store

```js
// workspace_alpine.js — additions
contactPresence: { state: 'unavailable', updatedAt: null },  // 'available'|'composing'|'recording'|'unavailable'
typingTimer: null,
replyTo: null,   // { id, conteudo_preview, remetente }
recording: { active: false, since: null, audioBlob: null },
notifications: { sound: true, desktop: false },
unreadDivider: { atendimento_id: null, msg_id: null },  // marca onde "novas mensagens" aparece
scrollAnchorBottom: true,  // false quando usuário rolou pra cima
```

Novas classes CSS (continuando o design system `.ws-*`):

```css
.ws-chat__day-sep      /* "Hoje" / "Ontem" / data */
.ws-chat__unread-div   /* linha "▼ N novas mensagens" */
.ws-chat__scroll-btn   /* botão flutuante voltar pro fim */
.ws-bub--stacked       /* segunda+ bolha consecutiva do mesmo remetente */
.ws-bub__reply         /* tira lateral colorida com preview da citada */
.ws-bub__reactions     /* container de emoji reactions abaixo do balão */
.ws-bub__menu          /* menu de contexto (responder, encaminhar, etc) */
.ws-typing-dots        /* "•••" animado no header */
.ws-record             /* UI de gravação de áudio no composer */
.ws-toast              /* notificação canto inferior direito */
```

---

## 7. Priorização sugerida (sequência de PRs)

Recomendo entregar em **5 PRs pequenos e independentes** (cada um mergável sozinho):

| PR | Escopo | Esforço | Impacto |
|---|---|---|---|
| 1 | Read receipts granulares (✓✓ azul) + auto-mark-read ao abrir + tratamento `MESSAGES_UPDATE` | 2 dias | Alto |
| 2 | Separadores de data + agrupamento visual + scroll-to-bottom + divisor "novas mensagens" + drag&drop | 2 dias | Alto |
| 3 | Reply (citar mensagem) — modelo + endpoint + UI | 3 dias | Alto |
| 4 | Presença bidirecional ("digitando…") OUT + IN | 2 dias | Médio-Alto |
| 5 | Gravação de mensagem de voz no painel | 2 dias | Alto |

Reações, encaminhar, busca, online/last seen e foto de perfil ficam em PRs subsequentes conforme prioridade.

---

## 8. Considerações de migração Evolution v2 → Evolution Go

- **Quebra de payload**: Evolution Go usa `event: "MESSAGE"` (singular, uppercase) em vez de `messages.upsert`. Precisa adapter no `WebhookProcessor` que normalize ambos os formatos durante a transição.
- **`subscribe`** explicitamente: Evolution Go exige lista de eventos no `/instance/connect`. Garantir que assinamos pelo menos: `MESSAGE`, `MESSAGE_UPDATE`, `PRESENCE`, `CALL`, `CONTACTS`, `CONNECTION`.
- **MinIO / S3**: configurar bucket dedicado no servidor para que o Evolution Go faça storage e nosso Django só consuma URLs (reduz CPU/disco do Django).
- **WebSocket opcional**: Evolution Go oferece WS persistente — útil pra presença, que via webhook HTTP gera ruído.
- **Healthcheck**: o monitor atual checa Evolution v2 `connectionStatus`. Adaptar para `/instance/info` ou equivalente da Go.

---

## 9. Métricas para validar a melhoria

Após cada fase, medir:

- **Tempo médio de resposta** do atendente (esperado: cair com gravação de áudio e reply).
- **% de mensagens com ✓✓ azul disparado** (deve aproximar de 100% das abertas).
- **Frequência de "abrir WhatsApp Web em paralelo"** — perguntar aos atendentes em 1-on-1.
- **CPU do worker Celery** durante recebimento de mídia (esperado: queda significativa após migrar para S3/MinIO).
- **Latência percebida** (typing → ver "digitando" no cliente): meta <500ms.

---

## 10. Riscos e cuidados

- **Rate limit do WhatsApp**: presença/markread em alto volume pode ser flag de spam. Throttle por instância (ex: max 1 presence por número a cada 3s).
- **Tamanho de mídia**: Evolution Go com MinIO precisa CORS bem configurado pra servir mídia direto no `<img>` / `<audio>` do browser.
- **Auth da mídia**: se MinIO ficar público, qualquer um com URL acessa. Usar URLs pré-assinadas (signed URLs) com TTL ou proxy via Django.
- **Sincronização de `respondida` vs `status_envio`**: durante migração, manter ambos por 2 semanas e auditar consistência.
- **Drag & drop de PDFs grandes**: validar tamanho client-side antes de upload para evitar OOM no Gunicorn.

---

## 11. Referências

### Documentação Evolution
- [Evolution Go — repositório oficial](https://github.com/evolution-foundation/evolution-go)
- [Evolution API — docs.evoapicloud.com](https://docs.evoapicloud.com/get-started/introduction)
- [Evolution v2 — webhooks](https://github.com/evolution-foundation/docs-evolution/blob/main/v2/en/configuration/webhooks.mdx)
- [Evolution Go vs Evolution API — comparativo (YouTube)](https://www.youtube.com/watch?v=Q9ntiwwLZCI)
- [Evolution Go + N8N — tutorial 2026 (YouTube)](https://www.youtube.com/watch?v=2LEQaWmhlpA)

### Inspiração de UX
- [I built a WhatsApp Web UI Clone — DEV Community](https://dev.to/soorajsnblaze333/i-built-a-whatsapp-web-ui-clone-2723)
- [How to Build a Chat App Like WhatsApp — Contus 2026](https://www.contus.com/blog/how-whatsapp-works-technically-and-how-to-build-an-app-similar-to-it/)
- [WhatsApp Clone App Features — Primocys 2026](https://primocys.com/blog/whatsapp-clone-app-features-to-build-2026/)

---

**Próximo passo sugerido**: revisar este documento e marcar quais itens entram nos próximos PRs. Posso começar pela Fase 1 (PRs 1 e 2) ou por qualquer item específico que você priorize.

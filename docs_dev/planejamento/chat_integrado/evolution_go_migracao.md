# Migração `evolution_sync`: Evolution v2 → Evolution Go

> Companion técnico ao plano principal em [`chat_whatsapp_experiencia_completa.md`](./chat_whatsapp_experiencia_completa.md).
> Aqui ficam **apenas as mudanças de baixo nível** no app `evolution_sync` (endpoints REST, payloads, eventos, configuração). Para decisões de UX/produto e roadmap por fase, consulte o plano principal.

---

## 1. Premissa

- **Escopo deste plano = apenas o cliente Django.** O servidor Evolution Go já roda no container do tenant (Hostinger, ex.: `paulo-ecoprint-evolution`) — sua configuração, deploy e infra **não estão neste escopo**. O `evolution_sync` é o **consumidor** desse servidor.
- O app Django `evolution_sync` ainda fala endpoints/payloads da Evolution v2. Precisa ser **completamente adaptado** para falar com o Evolution Go já em produção.
- A migração precisa ser **backwards-compatível** durante a janela de cutover (outros tenants podem ainda apontar para uma instância v2). Estratégia: feature flag `EVOLUTION_API_VERSION` em `EvolutionInstance`.

---

## 2. Inventário do código atual

| Arquivo | Linhas | O que faz | Status migração |
|---|---|---|---|
| [`services/evolution_api.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/services/evolution_api.py) | 489 | Wrapper REST: `send_message`, `_typing`, `fetch_instances`, `create_instance`, `delete_instance`, `connect_instance`, `get_connection_state`, `set_webhook`, `get_base64_from_media`, `logout_instance` | **Reescrita necessária** |
| [`services/webhook.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/services/webhook.py) | 577 | Recebe webhook, normaliza, buffer, dispatch | **Adapter de evento** |
| [`services/message_buffer.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/services/message_buffer.py) | 79 | Buffer Redis para agrupar mensagens | Sem mudança |
| [`domain/schemas.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/domain/schemas.py) | 426 | `EvolutionWebhookEnvelope`, parsers | **Estender para Go payload** |
| [`models.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/models.py) | 169 | `EvolutionInstance`, `EvolutionContact` | **Campo `api_version` + `s3_enabled`** |
| [`views.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/views.py) | 128 | Endpoint `/webhook/` | Sem mudança (delega ao service) |
| [`views_instances.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/views_instances.py) | 804 | UI tenant: criar/conectar/QR/excluir/listar | **Endpoints novos** |
| [`signals.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/signals.py) | 246 | Sincroniza estado | Revisar |
| [`normalizers.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/normalizers.py) | 37 | Normalização de telefones | Sem mudança |
| [`tenant_admin.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/tenant_admin.py) | 113 | Admin do tenant | Adicionar campo `api_version` |

**Total:** ~3377 linhas. Esperamos diff de ~600-900 linhas.

---

## 3. Mapeamento endpoint a endpoint

### 3.1. Conexão & autenticação (validado contra logs Gin do servidor)

Headers em ambas as versões: `apikey: <token>`. Em Go o token é **da instância** para endpoints de mensagem, e **Global API Key** para criar/listar/deletar.

| Função no painel | v2 (atual) | Go (real) | Mudança |
|---|---|---|---|
| Listar instâncias | `GET /instance/fetchInstances` | `GET /instance/all` (Global API Key) | URL |
| Info da instância | `GET /instance/fetchInstance/{name}` | `GET /instance/info/:instanceId` | URL + path param |
| Criar instância | `POST /instance/create` body com `instanceName`+`integration`+`qrcode`+webhook | `POST /instance/create` body `{name, token}` apenas | **Body simplificado** |
| Conectar (gerar QR) | `GET /instance/connect/{name}` | `POST /instance/connect` body `{instanceName, webhookUrl, subscribe[]}` | **Método+body diferentes** |
| Buscar QR Code | (retornado no `connect`) | `GET /instance/qr` (header `apikey: <token-instância>`) | **Endpoint dedicado** |
| Parear por código | (não disponível) | `POST /instance/pair` | **NOVO** (alternativa ao QR) |
| Status da conexão | `GET /instance/connectionState/{name}` | `GET /instance/status` (header `apikey: <token-instância>`) | **URL diferente — chamar v2 em Go retorna 503** |
| Desconectar (manter sessão) | (não usado) | `POST /instance/disconnect` | **NOVO** |
| Reconectar | (não usado) | `POST /instance/reconnect` | **NOVO** |
| Forçar reconexão | (não usado) | `POST /instance/forcereconnect/:instanceId` | **NOVO** |
| Logout (limpar sessão) | `DELETE /instance/logout/{name}` | `DELETE /instance/logout` (header da instância) | URL |
| Deletar instância | `DELETE /instance/delete/{name}` | `DELETE /instance/delete/:instanceId` (Global API Key) | URL com `:instanceId` |
| Proxy da instância | (não usado) | `POST /instance/proxy/:instanceId` / `DELETE /instance/proxy/:instanceId` | **NOVO** |
| Logs da instância | (não usado) | `GET /instance/logs/:instanceId` | **NOVO** (debug) |
| Advanced settings | (não usado) | `GET/PUT /instance/:instanceId/advanced-settings` | **NOVO** |
| Set webhook | `POST /webhook/set/{name}` separado | **Não existe em Go** — webhook configurado no body do `/instance/connect` | **Endpoint extinto** |

> ⚠️ **Importante:** No servidor real **não há endpoint `/webhook/*`** — qualquer chamada a `/webhook/set/...` ou `/webhook/find/...` retornará 404. O SETUP_INFO do servidor tem essa parte desatualizada (ver §8). Configure webhook sempre via `subscribe[]` no `/instance/connect`.

### 3.2. Mensageria (validado contra logs Gin do servidor `paulo-ecoprint-evolution`)

> ⚠️ **Crítico:** o endpoint de envio em Evolution Go é `/send/*`, **não** `/message/sendText` ou `/message/sendMedia`. O SETUP_INFO do servidor tem essa parte desatualizada — ver §8.

| Função | v2 | Go (real) | Mudança |
|---|---|---|---|
| Enviar texto | `POST /message/sendText/{instance}` body `{number, text}` | `POST /send/text` body `{number, text}` | URL completamente nova; instância vem do header `apikey` |
| Enviar mídia (img/vid/aud/doc) | `POST /message/sendMedia/{instance}` | `POST /send/media` body `{number, mediatype, media, caption}` | URL nova |
| Enviar link com preview | (não usado) | `POST /send/link` | **NOVO** |
| Enviar localização | `POST /message/sendLocation/{instance}` | `POST /send/location` | URL |
| Enviar contato (vCard) | (não usado) | `POST /send/contact` | **NOVO** |
| Enviar sticker | (não usado) | `POST /send/sticker` | **NOVO** |
| Enviar enquete | (não usado) | `POST /send/poll` | **NOVO** |
| Enviar botões interativos | (não usado) | `POST /send/button` | **NOVO** |
| Enviar lista interativa | (não usado) | `POST /send/list` | **NOVO** |
| Enviar carrossel | (não usado) | `POST /send/carousel` | **NOVO** |
| Publicar Status (texto) | (não usado) | `POST /send/status/text` | **NOVO** |
| Publicar Status (mídia) | (não usado) | `POST /send/status/media` | **NOVO** |
| Reagir a mensagem | (não usado) | `POST /message/react` body `{number, reaction, id, fromMe}` | **NOVO** |
| Marcar como lida | (não usado) | `POST /message/markread` body `{number, id: []}` | **NOVO** |
| Presença ("digitando…") | `POST /chat/sendPresence/{instance}` body `{number, presence, delay}` | `POST /message/presence` body `{number, state, isAudio}` | URL + estados (`composing`/`paused`/`recording`) |
| Editar mensagem enviada | (não usado) | `POST /message/edit` | **NOVO** |
| Excluir para todos | (não usado) | `POST /message/delete` | **NOVO** |
| Status de mensagem (lookup) | (não usado) | `POST /message/status` | **NOVO** |
| Mensagem citada (reply) | usado via body extra do `sendText` | `POST /send/text` com `quoted` no body | Campo `quoted` |

### 3.2.1. Gestão de chats (recursos novos em Go que não existiam em v2)

| Função | Endpoint Go | Quando usar |
|---|---|---|
| Fixar chat no topo | `POST /chat/pin` | Marcar atendimento prioritário |
| Arquivar/desarquivar | `POST /chat/archive` / `/chat/unarchive` | Auto-arquivar após resolução |
| Silenciar/dessilenciar | `POST /chat/mute` / `/chat/unmute` | Reduzir ruído |
| **Sincronização de histórico** | `POST /chat/history-sync` | Trazer histórico antigo do WhatsApp ao conectar nova instância |
| Etiquetar chat | `POST /label/chat` / `/unlabel/chat` | Usar etiquetas nativas do WhatsApp Business |

`history-sync` é especialmente útil porque permite popular o painel com mensagens antigas quando uma instância nova é conectada — antes a única opção era v2 com workaround.

### 3.3. Mídia recebida

| Operação | v2 | Go |
|---|---|---|
| Decodificar mídia (legado) | `POST /chat/getBase64FromMediaMessage/{name}` (CPU-intensivo, base64 inflado) | **Substituído** por `POST /message/downloadmedia` (mais leve) ou `mediaUrl` direto no payload quando S3/MinIO está habilitado no servidor |
| Storage de mídia | base64 inline ou nada | S3/MinIO configurado **no container Evolution Go** (env do servidor, fora do escopo deste plano) — quando ligado, payload já traz `mediaUrl` |

**Estratégia do cliente (nosso lado):**
1. Se `data.message.mediaUrl` vier no webhook → usar direto, salvar URL em `Mensagem.midia_url_remota`.
2. Se não vier (S3 não configurado no servidor) → chamar `POST /message/downloadmedia` (endpoint novo do Go) — mais eficiente que o `getBase64FromMediaMessage` do v2.
3. `_fetch_media_base64_from_evolution` em [`attendance_orchestrator.py`](../../../src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py) torna-se fallback de legado v2.

### 3.4. Contatos

| Função | v2 | Go |
|---|---|---|
| Avatar do contato | `POST /chat/fetchProfilePictureUrl/{instance}` | `POST /user/avatar` body `{number, preview}` |
| Info do contato | `POST /chat/findContacts/{instance}` | `POST /user/info` body `{number: []}` |
| Atualizar perfil | (não usado) | `POST /user/profilePicture` / `/user/profileName` / `/user/profileStatus` |

---

## 4. Mudanças no payload do webhook

### 4.1. Estrutura geral

**v2:**
```json
{
  "event": "messages.upsert",
  "instance": "atendimento",
  "data": {
    "key": { "remoteJid": "...", "fromMe": false, "id": "..." },
    "message": { "conversation": "..." },
    "messageTimestamp": 1699999999,
    "pushName": "João"
  }
}
```

**Go:**
```json
{
  "event": "MESSAGE",
  "instance": "atendimento",
  "data": {
    "key": { "remoteJid": "...", "fromMe": false, "id": "..." },
    "message": {
      "conversation": "...",
      "mediaUrl": "https://files.empresa.com/path/file.jpg"
    },
    "messageTimestamp": "1699999999",
    "pushName": "João"
  }
}
```

**Diferenças chave:**
1. `event` em `UPPERCASE` (não `dot.case`).
2. Campo `mediaUrl` aparece quando S3/MinIO está configurado — substitui a necessidade de chamar `getBase64FromMediaMessage`.
3. `messageTimestamp` pode vir como string (era number em v2).

### 4.2. Eventos a tratar

Evolution Go publica os seguintes eventos (`subscribe` no `/instance/connect`):

| Evento (Go) | Equivalente v2 | Tratado hoje? | Necessário? |
|---|---|---|---|
| `MESSAGE` | `messages.upsert` | ✅ | Sim |
| `MESSAGE_UPDATE` | `messages.update` | ❌ | **Sim** (read receipts) |
| `MESSAGE_DELETE` | `messages.delete` | ❌ | Médio |
| `SEND_MESSAGE` | `send.message` | ❌ | Baixo |
| `PRESENCE` | `presence.update` | ❌ | **Sim** ("digitando…" do contato) |
| `CONNECTION` | `connection.update` | ⚠️ via polling | **Sim** (estado da instância em tempo real) |
| `QRCODE` | `qrcode.updated` | ⚠️ via polling | **Sim** (atualiza QR no admin) |
| `CONTACTS` | `contacts.update` | ❌ | **Sim** (avatar/nome) |
| `GROUP` | `groups.upsert` | ❌ | Não (grupos descartados) |
| `CALL` | `call` | ❌ | Médio (notificação) |

### 4.3. Adapter de evento — implementação sugerida

Em `domain/schemas.py`, novo enum:

```python
class EvolutionEventName(str, Enum):
    # Go
    MESSAGE = "MESSAGE"
    MESSAGE_UPDATE = "MESSAGE_UPDATE"
    MESSAGE_DELETE = "MESSAGE_DELETE"
    PRESENCE = "PRESENCE"
    CONNECTION = "CONNECTION"
    QRCODE = "QRCODE"
    CONTACTS = "CONTACTS"
    CALL = "CALL"

    @classmethod
    def from_raw(cls, raw: str) -> "EvolutionEventName | None":
        """Aceita v2 ('messages.upsert') OU Go ('MESSAGE')."""
        normalized = raw.upper().replace(".", "_").rstrip("S")
        # Tabela de aliases v2 → Go
        ALIASES = {
            "MESSAGES_UPSERT": cls.MESSAGE,
            "MESSAGES_UPDATE": cls.MESSAGE_UPDATE,
            "MESSAGES_DELETE": cls.MESSAGE_DELETE,
            "PRESENCE_UPDATE": cls.PRESENCE,
            "CONNECTION_UPDATE": cls.CONNECTION,
            "QRCODE_UPDATED": cls.QRCODE,
            "CONTACTS_UPDATE": cls.CONTACTS,
        }
        return ALIASES.get(normalized) or cls._value2member_map_.get(raw)
```

Em `services/webhook.py`, o `WebhookProcessor.handle()` continua entrando pelo mesmo endpoint HTTP, mas o switch interno passa a usar `EvolutionEventName.from_raw(event)` para acomodar ambos.

---

## 5. Mudanças nos modelos

Em [`evolution_sync/models.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/models.py) (`EvolutionInstance`):

```python
class APIVersion(models.TextChoices):
    V2 = "v2", "Evolution API v2"
    GO = "go", "Evolution Go"

api_version = CharField(choices=APIVersion.choices, default=APIVersion.GO, max_length=5)
media_storage_backend = CharField(
    choices=[("none","Sem storage"),("s3","S3/MinIO no Evolution")],
    default="s3", max_length=10,
)
subscribed_events = JSONField(default=list, blank=True,
    help_text="Lista de eventos assinados no /instance/connect (ex: [MESSAGE, PRESENCE])")
```

Em [`tenants/models.py`](../../../src/smart_core_assistant_painel/app/tenants/models.py) (`TenantEvolution`, se existir):

```python
default_api_version = CharField(choices=APIVersion.choices, default=APIVersion.GO, max_length=5)
```

Migration `evolution_sync/migrations/0XXX_api_version_e_storage.py`.

---

## 6. Reescrita do `EvolutionWhatsAppService`

Estratégia: criar **dois adapters** com a mesma interface e escolher por `api_version`:

```
services/
├── evolution_api.py            # Interface abstrata (ABC) + factory
├── evolution_v2_adapter.py     # Implementação v2 (código atual)
└── evolution_go_adapter.py     # Implementação Go (nova)
```

Interface mínima:

```python
class EvolutionAPIInterface(Protocol):
    def send_text(self, *, instance, api_key, base_url, number, text, quoted=None) -> dict: ...
    def send_media(self, *, instance, api_key, base_url, number, file_url, kind, caption="", filename="") -> dict: ...
    def send_audio(self, *, instance, api_key, base_url, number, audio_url, ptt=True) -> dict: ...
    def send_reaction(self, *, instance, api_key, base_url, number, message_id, emoji, from_me=False) -> dict: ...
    def mark_read(self, *, instance, api_key, base_url, number, message_ids: list[str]) -> dict: ...
    def set_presence(self, *, instance, api_key, base_url, number, state, is_audio=False) -> dict: ...
    def get_profile_picture(self, *, instance, api_key, base_url, number) -> str: ...

    def create_instance(self, *, base_url, api_key, name, token=None) -> dict: ...
    def connect_instance(self, *, base_url, api_key, name, webhook_url, subscribe: list[str]) -> dict: ...
    def get_status(self, *, base_url, api_key, name) -> dict: ...
    def delete_instance(self, *, base_url, api_key, name) -> dict: ...
    def logout_instance(self, *, base_url, api_key, name) -> dict: ...

    # Legado v2 — não implementado em Go
    def get_base64_from_media(self, **kw) -> str: ...
```

Factory:

```python
def get_evolution_adapter(api_version: str) -> EvolutionAPIInterface:
    if api_version == "go":
        return EvolutionGoAdapter()
    return EvolutionV2Adapter()
```

Chamadores (orchestrator, message_dispatch, etc.) passam a usar `get_evolution_adapter(instance.api_version)`.

---

## 7. Reescrita da UI de instâncias

Em [`views_instances.py`](../../../src/smart_core_assistant_painel/app/evolution_sync/views_instances.py) (804 linhas), três grupos de mudança:

1. **Criar instância**: o form passa a aceitar `subscribed_events` (multi-select) e `media_storage_backend`. Por default já vem com `[MESSAGE, MESSAGE_UPDATE, PRESENCE, CONNECTION, CONTACTS]` marcados.
2. **Connect**: o body do POST muda — não passa mais por `set_webhook` separado; webhook URL + eventos vão no payload do `/instance/connect`.
3. **QR Code**: continua igual (retorno do `connect_instance`).
4. **Status**: passa a consumir o evento `CONNECTION` via banco em vez de polling — `EvolutionInstance.last_connection_state` atualizado pelo webhook.

---

## 8. Status do servidor (validado em 2026-05-19) e pendências com o devops

> ⚠️ O deploy e a operação dos servidores Evolution Go são de responsabilidade do devops/tenant. Esta seção registra o que foi **validado contra o servidor real `paulo-ecoprint-evolution`** (Hostinger, container `evoapicloud/evolution-go:latest`) e **inconsistências encontradas** que precisam ser tratadas.

### 8.1. O que está OK no servidor

- ✅ 4 containers rodando (`postgres_cliente`, `redis_cliente`, `postgres_evolution`, `evolution`).
- ✅ Imagem Go correta: `evoapicloud/evolution-go:latest` (não mais Baileys/v2).
- ✅ Dois bancos PostgreSQL Evolution (`evogo_auth` + `evogo_users`) ativos.
- ✅ Servidor responde na porta 8080 e expõe todos os endpoints listados nas §3.1–§3.3.
- ✅ Manager UI acessível em `http://76.13.229.210:8080/manager/login`.

### 8.2. Status dos bloqueadores

#### 8.2.1. Licença ✅ ATIVADA em 2026-05-19 10:27 UTC

```
✓ License activated! Key: f65f53d0...4072 (_9dg: evolution-go)
GET /instance/all → 200 OK {"data":[],"message":"success"}
```

Servidor totalmente operacional. `/instance/all` responde com lista (vazia até a primeira instância ser criada via fluxo de provisioning).

#### 8.2.2. Cliente Django ainda chama endpoint v2 inexistente (⚠ Phase 1 deste plano resolve)

Os logs do servidor mostraram nosso próprio cliente Django chamando:
```
GET /instance/connectionState/atendimento → 503
```

Esse endpoint **não existe em Go** — é resquício do `evolution_v2` do nosso cliente. O substituto correto é `GET /instance/status` (header `apikey: <token-instância>`). Será corrigido pelo `EvolutionGoAdapter` na **Phase 1.3** do plano canônico.

### 8.3. ❗ Inconsistências no SETUP_INFO do servidor (`paulo-ecoprint-server/SETUP_INFO.md`)

O documento foi atualizado para Evolution Go, mas três pontos saíram incorretos. Sugerir correção ao devops do servidor:

| Item no SETUP_INFO | Correção real (validada contra logs Gin) |
|---|---|
| `POST /message/sendText` | É **`POST /send/text`** |
| `POST /message/sendMedia` | É **`POST /send/media`** |
| `POST /webhook/set/<instancia>` e `GET /webhook/find/<instancia>` | **Não existem em Go**. Webhook é configurado via `subscribe[]` no body do `POST /instance/connect`. |
| Exemplo de payload com `"event": "messages.upsert"` (dot.lowercase) | Precisa ser confirmado contra um webhook real recebido — versões recentes do Evolution Go enviam `"MESSAGE"` (UPPERCASE). Nossa estratégia: `EvolutionEventName.from_raw()` aceita ambos formatos (§4.3). |

### 8.4. Pressupostos a confirmar antes de cada cutover de instância

Mesmo após o devops resolver §8.2, validar para cada instância migrada:

| Item | Como verificar |
|---|---|
| Servidor acessível a partir do app Django | Smoke test do `EvolutionGoAdapter` |
| Webhook do painel alcançável a partir do servidor | Logs do servidor mostram POST 200/201 ao webhook do Django |
| Eventos assinados na conexão | Mínimo: `MESSAGE, MESSAGE_UPDATE, PRESENCE, CONNECTION, CONTACTS, QRCODE` |
| S3/MinIO configurado no servidor (opcional) | Webhook traz `data.message.mediaUrl` populado em mensagens com mídia. Se não tiver S3, cliente cai em `POST /message/downloadmedia` |
| URLs de mídia acessíveis pelo browser do operador | Abrir `mediaUrl` direto no navegador retorna o arquivo |

**Caso algum item não esteja pronto, NÃO ativar `api_version="go"` na `EvolutionInstance`** — manter em `v2` até o devops resolver. O adapter v2 continua funcional como fallback.

---

## 9. Plano de cutover

1. **Branch isolada**: `feature/evolution-go-migration`.
2. **Coexistência**: durante o desenvolvimento, manter `EvolutionV2Adapter` e `EvolutionGoAdapter` lado a lado. Toggle via `EvolutionInstance.api_version`.
3. **Testes em paralelo**: nova instância de QA aponta para Go; instância produção fica em v2 até pronto.
4. **Cutover**: alterar `default_api_version` para `"go"`, executar migration, atualizar instâncias existentes para `"go"`, recriar webhooks via `/instance/connect`.
5. **Cleanup**: após 2 semanas estável, remover `EvolutionV2Adapter` e `get_base64_from_media`.

---

## 10. Critérios de aceitação

- [ ] Toda chamada do app ao Evolution roteia via `get_evolution_adapter(...)`.
- [ ] Mensagens novas chegam com `mediaUrl` populado (não precisa decodificar base64).
- [ ] Eventos `MESSAGE_UPDATE`, `PRESENCE`, `CONNECTION`, `CONTACTS` são processados sem erro 500 no webhook receiver.
- [ ] UI de instâncias cria/conecta/QR/exclui sem regressão funcional.
- [ ] Healthcheck do servidor passa contra Evolution Go.
- [ ] Testes de regressão do `evolution_sync` passam com `api_version="go"`.
- [ ] `pyright` zero erros novos nos arquivos tocados.

---

## 11. Endpoints novos que abrem caminho para o plano principal

A migração também desbloqueia diretamente os recursos da Fase 1-2 do plano principal:

| Capability do plano principal | Endpoint Go que viabiliza |
|---|---|
| ✓✓ azul (read receipts) | `POST /message/markread` + evento `MESSAGE_UPDATE` |
| "Atendente digitando…" para o cliente | `POST /message/presence` |
| "Cliente digitando…" no painel | Evento `PRESENCE` (subscribe) |
| Reply citada | `POST /message/sendText` com `quoted` |
| Reações emoji | `POST /message/react` |
| Avatar real do contato | `POST /user/avatar` + evento `CONTACTS` |
| Mídia sem CPU spike | `mediaUrl` direto via MinIO/S3 |
| Encaminhar mensagem | `POST /message/sendText/sendMedia` com flag `forwarded` |

---

## 12. Referências

- [Evolution Go — repositório](https://github.com/evolution-foundation/evolution-go)
- [Evolution Go — wiki authentication](https://github.com/evolutionapi/evolution-go/blob/main/docs/wiki/conceitos-core/authentication.md)
- [Evolution Go — wiki events system](https://github.com/evolutionapi/evolution-go/blob/main/docs/wiki/recursos-avancados/events-system.md)
- [Evolution Go — wiki instances](https://github.com/evolutionapi/evolution-go/blob/main/docs/wiki/conceitos-core/instances.md)
- [Plano principal de chat](./chat_whatsapp_experiencia_completa.md)

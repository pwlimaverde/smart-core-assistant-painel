# Plano — Módulo `atendimento_unificado` (Chat WhatsApp + Kanban + Campos Custom)

## Contexto

Hoje o operador alterna entre **Trello** (gestão Kanban) e **WhatsApp Web** (responder mensagens). Isso fragmenta o contexto e atrasa o atendimento — Trello não tem chat, WhatsApp não tem fluxo. Além disso, dados estruturados (tipo de produto, medidas, CNPJ) ficam soltos na conversa em vez de organizados em campos consultáveis.

**Objetivo**: Construir uma única tela onde o atendente vê suas conversas (estilo WhatsApp Web), pode responder dali, e ao mesmo tempo gerencia o pipeline em modo Kanban — com **campos personalizados** que o bot extrai automaticamente das mensagens e que são reinjetados no system prompt para enriquecer respostas futuras.

**Decisões já tomadas pelo usuário**:
1. Trello permanece sincronizado bidirecionalmente (UI nativa principal, Trello como espelho).
2. Real-time via **SSE** (Server-Sent Events) — não WebSocket, não polling.
3. Entrega **faseada em 3 fases** (MVP primeiro).
4. Campos personalizados **híbridos**: globais por tenant + por fluxo.

---

## Decisões arquiteturais consolidadas

1. **Reuso radical**: `EtapaFluxo` já é "coluna kanban", `Atendimento.etapa_atual` já é "card". Não criar `Coluna`/`Card` novos.
2. **App novo `atendimento_unificado`** é camada fina de UI + orquestração; lógica de negócio fica nos models/services existentes.
3. **DDD/Result Pattern só onde toca IA**: feature de extração vai em `modules/ai_engine/features/extracao_campos/`.
4. **SSE sobre Redis pub/sub**, servida via ASGI (apenas a rota SSE) enquanto resto continua em WSGI/Gunicorn — minimiza impacto operacional.
5. **Atendente envia mensagem criando `Mensagem(remetente=ATENDENTE_HUMANO)`** — o signal já existente em [evolution_sync/signals.py](src/smart_core_assistant_painel/app/evolution_sync/signals.py#L216) cuida do envio via Evolution API.
6. **Trello é espelho passivo**: toda escrita nasce no painel e propaga via signals/tasks já existentes — nenhuma mudança de fluxo no `trello_sync`.
7. **Extração de campos é assíncrona pós-resposta** — não atrasa a UX do contato.

---

## FASE 1 — MVP: Chat unificado + Kanban básico (esforço **G**)

### Estrutura do app novo

Criar [atendimento_unificado/](src/smart_core_assistant_painel/app/atendimento_unificado/):

```
atendimento_unificado/
  apps.py                            # AppConfig
  urls.py                            # rotas HTML
  api_urls.py                        # rotas JSON + SSE
  views.py                           # WorkspaceView (HTML shell)
  views_api.py                       # endpoints JSON
  views_sse.py                       # StreamingHttpResponse via ASGI
  selectors.py                       # queries (lista conversas, kanban snapshot)
  services/
    board_service.py                 # mover atendimento entre etapas
    message_dispatch_service.py      # criar Mensagem do atendente
    realtime_publisher.py            # publica eventos no Redis pub/sub
  signals.py                         # post_save Mensagem/MovimentoFluxo → publish
  templates/atendimento_unificado/
    workspace.html                   # estende core/templates/base_dashboard.html
    partials/conversation_item.html
    partials/chat_message.html       # variantes por TipoMensagem
    partials/kanban_column.html
    partials/kanban_card.html
    partials/detail_panel.html
    partials/custom_fields_panel.html  # placeholder fase 1
  static/atendimento_unificado/
    js/workspace_alpine.js           # store Alpine + EventSource
    css/workspace.css
```

Registrar em:
- [core/settings.py](src/smart_core_assistant_painel/app/core/settings.py) `INSTALLED_APPS`
- [tenants/db_router.py](src/smart_core_assistant_painel/app/tenants/db_router.py) — adicionar `"atendimento_unificado"` ao `TENANT_APPS`

### Models — **NENHUM novo na Fase 1**

Tudo já existe e é reaproveitado:

| Necessidade | Reuso |
|---|---|
| Coluna kanban | [`EtapaFluxo`](src/smart_core_assistant_painel/app/operacional/models.py#L562) (já tem `cor`, `ordem`, `tipo_etapa`) |
| Card kanban | [`Atendimento.etapa_atual`](src/smart_core_assistant_painel/app/atendimentos/models.py#L142) |
| Mover card | `MovimentoFluxo.criar_movimento(...)` (já existe, atualiza `etapa_atual` + histórico) |
| Mensagens chat | [`Mensagem`](src/smart_core_assistant_painel/app/atendimentos/models.py#L1003) |
| Envio WhatsApp | Signal `_on_message_saved` em [evolution_sync/signals.py](src/smart_core_assistant_painel/app/evolution_sync/signals.py#L216) |
| Lista conversas | `Atendimento` ordenado por `data_ultima_mensagem` (já indexado) |
| Não-lido (MVP) | `mensagens.filter(remetente=CONTATO, respondida=False).count()` |

### Layout (3 colunas, modo via tab Alpine)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Topbar: tabs [Conversas | Kanban]   Filtros (depto/atendente/busca)  │
├─────────────┬──────────────────────────────┬──────────────────────────┤
│ Sidebar     │ Centro                       │ Painel direito           │
│ Conversas   │ Modo CONVERSAS:              │ - Dados do contato       │
│ (ordenada   │   chat ativo + composer      │ - Atendimento (status,   │
│ por data    │ Modo KANBAN:                 │   etapa, prioridade)     │
│ última msg) │   colunas EtapaFluxo + cards │ - Tags                   │
│             │   (clicar abre chat à dir.)  │ - Custom fields panel    │
└─────────────┴──────────────────────────────┴──────────────────────────┘
```

A coluna direita é **a mesma nos dois modos** — facilita drilldown e prepara terreno para Fase 2.

### Endpoints

**HTML** (`atendimento_unificado/urls.py`):
- `GET /workspace/` → `WorkspaceView`

**JSON** (`/workspace/api/`):
| Rota | Verbo | Função |
|---|---|---|
| `/conversations/` | GET | Sidebar (cursor por `data_ultima_mensagem`) |
| `/conversations/<id>/messages/` | GET | Histórico paginado |
| `/conversations/<id>/send/` | POST | Cria `Mensagem(ATENDENTE_HUMANO)` — signal envia |
| `/conversations/<id>/upload/` | POST | Multipart → `Mensagem` com mídia (Fase 3 se Evolution não suportar) |
| `/conversations/<id>/mark-read/` | POST | Marcar lido |
| `/board/?departamento=<id>` | GET | Snapshot Kanban (etapas + cards) |
| `/board/move/` | POST | `{atendimento_id, etapa_destino_id}` → `board_service.move_atendimento` |
| `/board/assign/` | POST | `{atendimento_id, atendente_id}` |

**SSE** (`/workspace/events/?topics=conversations,board`):
- Eventos: `message.new`, `message.sent`, `board.moved`, `atendimento.assigned`, `heartbeat` (25s)
- Formato: `event: <tipo>\ndata: <json>\n\n`

### Atendente envia mensagem

`message_dispatch_service.send_text(atendimento_id, texto, atendente)`:
1. `Mensagem.objects.create(atendimento=..., remetente=TipoRemetente.ATENDENTE_HUMANO, conteudo="", resposta_bot=texto, metadados={"evolution":{"api_key": <api_key>}})` — segue padrão de [`Atendimento.transferir_para_humano_com_saudacao`](src/smart_core_assistant_painel/app/atendimentos/models.py#L867).
2. Signal `_on_message_saved` detecta e envia via `EvolutionWhatsAppService.send_message(...)`.

### Mover atendimento entre etapas

`board_service.move_atendimento(atendimento_id, etapa_destino_id, atendente=None)`:
1. Validar `etapa_destino.fluxo.departamento_id == atendimento.departamento_id` (regra já em `Atendimento.clean()`).
2. `MovimentoFluxo.criar_movimento(...)` — atualiza `etapa_atual`, registra duração, histórico.
3. Trello sync acontece automaticamente via signal já existente em [trello_sync/signals.py](src/smart_core_assistant_painel/app/trello_sync/signals.py).
4. `realtime_publisher.publish(tenant_slug, "board.moved", payload)`.

### SSE: implementação

- **Roteamento ASGI dedicado**: rota `/workspace/events/` servida por ASGI (Daphne/Uvicorn), resto continua WSGI/Gunicorn. `app/core/asgi.py` já existe.
- **Redis pub/sub** (broker Celery já presente): cada conexão `redis.pubsub().subscribe(f"sse:{tenant_slug}:events")`.
- **`realtime_publisher.publish(tenant_slug, event_type, payload)`** = wrapper sobre `redis.publish(channel, json.dumps(...))`.
- Signals em `atendimento_unificado/signals.py` ouvem `post_save` de `Mensagem` e `MovimentoFluxo` e chamam `publish(...)`. Tenant via `get_current_tenant_slug()` em `tenants/tenant_context.py`.
- **Heartbeat**: timer 25s emitindo `: ping\n\n`.
- **Reconexão**: `EventSource` nativa reconecta automaticamente.
- **Nginx**: `proxy_buffering off` e `proxy_read_timeout` alto na rota SSE — documentar.

### Riscos Fase 1
1. **SSE com Gunicorn sync prende worker** → mitigação: rota SSE em ASGI.
2. **"Não-lido" sem campo dedicado** → MVP usa `respondida=False` como aproximação; campo dedicado vem na Fase 3.
3. **Mídia outbound** → Evolution `send_message` é só texto. Se não houver `send_media`, **adiar mídia para Fase 3**.
4. **Concorrência mover-card** → usar `select_for_update` (padrão já em `TicketSyncService`).
5. **Multi-tenant SSE** → canal Redis nomeado por tenant para evitar vazamento.

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
- `mostrar_no_card_trello` BooleanField(default=True)
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

Caminho: [modules/ai_engine/features/extracao_campos/](src/smart_core_assistant_painel/modules/ai_engine/features/extracao_campos/)

Estrutura espelhada de [analise_mensage/](src/smart_core_assistant_painel/modules/ai_engine/features/analise_mensage/):
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
- **Quando rodar**: integrar em [`AttendanceOrchestrator._process_message_and_respond`](src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py) **após** resposta gravada. Disparar via Celery task `extract_custom_fields_async(tenant_slug, atendimento_id, mensagem_id)`.
- **Idempotência**: `select_for_update` no atendimento; só sobrescreve `origem=BOT` se `confianca_nova > confianca_atual`. **Nunca sobrescreve `origem=MANUAL`**.
- **Exposição**: adicionar `FeaturesCompose.extracao_campos(parameters)` em [features_compose.py](src/smart_core_assistant_painel/modules/ai_engine/features/features_compose.py).

### Injeção no system prompt

Modificar [analise_mensage_datasource.py:241-250](src/smart_core_assistant_painel/modules/ai_engine/features/analise_mensage/datasource/analise_mensage_datasource.py#L241-L250):

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

Em [`ticket_sync_service.py`](src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py), estender `_build_card_description` para appendar:

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

### 3.2 Filtros e busca
- Endpoint composto: `/conversations/?q=<txt>&depto=<id>&atendente=<id>&tag=<t>&campo_<slug>=<v>`.
- MVP: `Mensagem.conteudo__icontains` + `Contato.nome_contato__icontains`. PG full-text (`SearchVector`) como débito futuro.
- Filtro por valor de campo: GIN index em `valor`.

### 3.3 Não-lidos / SLA
- Migration: adicionar `Atendimento.data_ultima_leitura_atendente DateTimeField(null=True)`.
- Contador = mensagens do contato após esse timestamp.
- Badge SLA estourado usando `MovimentoFluxo.duracao_segundos`.

### 3.4 Mídia outbound (se não entrou na Fase 1)
- Estender `EvolutionWhatsAppService.send_media(...)`.
- Signal Evolution detecta `Mensagem.tipo in (IMAGEM,AUDIO,DOCUMENTO)` e usa `send_media`.

### 3.5 Exportação
- `GET /workspace/api/export/?formato=csv&...` → CSV streaming (Celery task se grande).
- Colunas: atendimento, contato, status, etapa, atendente, **uma coluna por slug de campo**.

### Riscos Fase 3
1. **SortableJS + SSE conflito**: store Alpine guarda flag `isDragging` que ignora updates SSE da etapa em movimento por 2s.
2. **Filtros por campo**: queries com JOINs em `valores_campos` exigem index parcial PG.
3. **Export grande**: `StreamingHttpResponse` + `.iterator(chunk_size=500)`.

---

## Critical Files

**Fase 1** (criar):
- [atendimento_unificado/views_sse.py](src/smart_core_assistant_painel/app/atendimento_unificado/views_sse.py)
- [atendimento_unificado/services/board_service.py](src/smart_core_assistant_painel/app/atendimento_unificado/services/board_service.py)
- [atendimento_unificado/services/realtime_publisher.py](src/smart_core_assistant_painel/app/atendimento_unificado/services/realtime_publisher.py)
- [atendimento_unificado/templates/atendimento_unificado/workspace.html](src/smart_core_assistant_painel/app/atendimento_unificado/templates/atendimento_unificado/workspace.html)

**Fase 1** (editar):
- [core/settings.py](src/smart_core_assistant_painel/app/core/settings.py) — INSTALLED_APPS
- [tenants/db_router.py](src/smart_core_assistant_painel/app/tenants/db_router.py) — TENANT_APPS
- [core/asgi.py](src/smart_core_assistant_painel/app/core/asgi.py) — rota SSE
- Configuração Nginx/deploy (documentar `proxy_buffering off`)

**Fase 2** (criar):
- [atendimento_unificado/models.py](src/smart_core_assistant_painel/app/atendimento_unificado/models.py) — `CampoPersonalizado`, `ValorCampoAtendimento`
- [modules/ai_engine/features/extracao_campos/](src/smart_core_assistant_painel/modules/ai_engine/features/extracao_campos/) — feature DDD completa
- Migration `atendimento_unificado/migrations/0001_initial.py`

**Fase 2** (editar):
- [analise_mensage_datasource.py:241-250](src/smart_core_assistant_painel/modules/ai_engine/features/analise_mensage/datasource/analise_mensage_datasource.py#L241-L250) — injeção dos campos
- [modules/ai_engine/utils/parameters.py](src/smart_core_assistant_painel/modules/ai_engine/utils/parameters.py) — `campos_coletados` em `AnaliseMensageParameters`
- [modules/ai_engine/utils/erros.py](src/smart_core_assistant_painel/modules/ai_engine/utils/erros.py) — `ExtracaoCamposError`
- [modules/ai_engine/features/features_compose.py](src/smart_core_assistant_painel/modules/ai_engine/features/features_compose.py) — método `extracao_campos`
- [atendimentos/services/attendance_orchestrator.py](src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py) — disparar Celery task pós-resposta
- [trello_sync/services/ticket_sync_service.py](src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py) — `_build_card_description` estendido

---

## Verificação ponta a ponta

**Fase 1**:
1. Acessar `/workspace/`, ver lista de conversas (sidebar) e chat ativo ao clicar.
2. Enviar mensagem pelo composer → confirmar que chega no WhatsApp do contato (testar com instância real).
3. Trocar para tab Kanban → ver colunas (etapas) com cards (atendimentos) do departamento.
4. Mover card para outra coluna via endpoint → confirmar mudança no Trello (sincronização preservada).
5. Abrir 2 abas com `/workspace/` → enviar/mover em uma → ver atualização ao vivo na outra (validação SSE).
6. Verificar logs: nenhum signal duplicado, sem erro `_syncing_from_trello`.
7. Carga: 50 conversas + 1000 mensagens → tempo de carregar sidebar < 500ms.

**Fase 2**:
1. Criar definição global "CNPJ" e definição por fluxo "tipo_produto" no admin.
2. Em uma conversa nova, contato envia "Meu CNPJ é 12.345.678/0001-99 e quero um banner".
3. Após resposta do bot, abrir o painel direito → ver `cnpj` e `tipo_produto` preenchidos com `origem=BOT` + ícone de confiança.
4. Editar manualmente um campo no painel → próximo extração do bot **não deve sobrescrever**.
5. Verificar no Trello: descrição do card mostra "Campos coletados: CNPJ: ..." (após debounce de 5s).
6. Próxima mensagem do contato: verificar log do prompt — seção `### CAMPOS COLETADOS DO ATENDIMENTO:` presente com os valores.

**Fase 3**:
1. Drag-drop de card no kanban — sem flicker, com rollback se erro.
2. Filtro por campo personalizado: `?campo_tipo_produto=banner` retorna apenas atendimentos com esse valor.
3. Badge não-lido decrementa ao abrir conversa.
4. Export CSV com 5000 linhas — completo em < 30s, sem timeout.

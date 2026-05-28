<!--
Builds manuais sobre a release 1.2.2 (fase de estruturação/testes).
Sufixo `+NNN` = build local sequencial, SEM git tag e SEM deploy automático.
A próxima PATCH oficial (1.2.3) só será cortada/tag quando a fase fechar.
-->

## 1.2.3+003 - 2026-05-28 (build manual, sem tag)

### Fixed
- **`context_processors.project_version`**: removido hack que concatenava
  `+001` no final da string mesmo quando a versão real era outra (resultado:
  `1.2.3+2` aparecia como `1.2.3+2+001` no rodapé). Agora retorna
  `__version__` direto.

## 1.2.3+002 - 2026-05-28 (build manual, sem tag)

### Performance
- **`jinja2_env.py` — cache de `static_versioned`**: memoiza via
  `lru_cache(512)` em produção (DEBUG=False). Cada render do dashboard fazia
  ~30 chamadas que executavam `finders.find()` + `os.path.getmtime()` em disco
  por request; agora viram lookup em dict após o primeiro hit. Em DEBUG o
  comportamento original é mantido para refletir mudanças em dev.
- **`jinja2_env.py` — cache de `_resolve_tenant_context` por request**: os
  helpers de permissão (`can_view_module`, `is_owner_user`, etc.) são chamados
  ~8 vezes no `base_dashboard.html` e cada um disparava
  `TenantUser.objects.get(...)` idêntico. Resultado agora é armazenado em
  `request._tenant_ctx_cache`, reduzindo 8 queries SQL → 1 por render.
- **`jinja2_env.py` — `FileSystemBytecodeCache`**: workers Gunicorn em
  cold-start carregam `.html` direto do bytecode persistido em
  `/tmp/jinja2-cache` (configurável via `JINJA2_BYTECODE_CACHE_DIR`),
  eliminando o re-parse de Python source nos primeiros requests.

### Changed
- **`docker/compose/workers.yml`**: `init: true` (tini como PID 1, reapa
  zombies do `celery inspect ping`) e healthcheck mais espaçado
  (interval 60s→180s, timeout 15s→45s, start_period 60s→120s) para não
  saturar VM de 2 vCPUs onde o healthcheck sobe um Django+Celery completo a
  cada execução.

## 1.2.2+016 - 2026-05-21 (build manual, sem tag)

### Fixed
- **Mensagem recebida marcada como "visualizada" (ticks azuis) no ato do
  recebimento**: a instância do Evolution Go estava com `readMessages: true`,
  fazendo o whatsmeow enviar recibo de leitura automático para toda mensagem
  recebida — independente do app. Setting corrigido para `false` na instância
  de produção. Recibo de leitura agora é **explícito** (após resposta do
  bot/atendente ou abertura do atendimento via `POST /message/markread`).
- **Frontend marcava conversa ativa como lida ao receber mensagem via SSE**:
  removida a chamada `markRead` do handler `message.new` em `workspace_alpine.js`.

### Changed
- **`set_advanced_settings` (evolution_go_adapter)**: default de `read_messages`
  alterado de `True` → `False` para evitar reintrodução do recibo automático em
  chamadas futuras.

## 1.2.2+015 - 2026-05-21 (build manual, sem tag)

### Changed
- **Formatação automática (ruff)**: normalização de comprimento de linha (`E501`)
  e estilo de aspas em migrations e demais módulos — sem alteração funcional.

## 1.2.2+014 - 2026-05-21 (build manual, sem tag)

### Fixed
- **Imagens (e outras mídias) sem base64 inline não eram analisadas pela IA**:
  o Evolution Go (whatsmeow) retorna 403/500 **transitório** no
  `POST /message/downloadmedia` logo após o recebimento, durante a rajada de
  mensagens (race/throttle). Confirmado em produção que o mesmo download passa
  a funcionar segundos depois. Adicionado retry com backoff (3s/8s/15s) em
  `_fetch_media_base64_from_evolution` antes de cair no placeholder — mídias
  que antes falhavam por timing agora são baixadas, persistidas e analisadas.

## 1.2.2+013 - 2026-05-21 (build manual, sem tag)

### Fixed
- **Mídia sem base64 inline (forwarded/grande) causava `InterpretMediaError`**:
  quando o fallback `POST /message/downloadmedia` falha (CDN do WhatsApp → 403,
  encapsulado em 500 pelo Evolution Go), a IA era chamada com `base64_len=0`.
  Adicionado guard em `_convert_media_context`: sem base64 após fallback, registra
  placeholder em `analise_midia` e retorna sem chamar `converter_contexto`.
- **Logs `[MIDIA-CTX]` multiline sumiam de filtros por keyword**: texto interpretado
  ficava em linhas sem o prefixo; separado em `logger.info` (cabeçalho) +
  `logger.debug` (texto completo), com placeholders `{}` (padrão loguru recomendado).

### Added
- **Suporte a `stickerMessage`**: adicionado a `_MEDIA_TYPES` em
  `attendance_orchestrator.py` e branch dedicado em `EvolutionMessageData.from_dict`
  (`schemas.py`). Stickers chegam sem base64 inline e requerem download via
  `/message/downloadmedia`; os campos de encriptação (`mediaKey`, `directPath`,
  `fileSha256`, `fileEncSha256`) são extraídos para viabilizar o fallback.
  Persistência `.webp` já existia em `_persist_media_file`.

## 1.2.2+012 - 2026-05-20 (build manual, sem tag)

### Fixed
- **Endpoint de download era `/message/downloadimage` (404)**: o swagger lista
  esse path mas a rota real do servidor é `/message/downloadmedia` (confirmado
  ao vivo: `downloadimage`→404, `downloadmedia`→500 "invalid media type" com body
  vazio). Corrigido o path mantendo o body `{message: <obj>}`.

## 1.2.2+011 - 2026-05-20 (build manual, sem tag)

### Fixed
- **Download de mídia retorna data URL, não base64 cru** (confirmado na doc do
  Evolution Go): o `/message/downloadimage` devolve `data:<mime>;base64,<payload>`.
  Removido o prefixo antes de decodificar (no fetch e, defensivamente, no
  `_persist_media_file`) — sem isso o `/` do prefixo corromperia o arquivo.

## 1.2.2+010 - 2026-05-20 (build manual, sem tag)

### Fixed
- **Fallback de download de mídia sem base64 inline** (ex.: imagens grandes): o
  `download_media` agora usa o endpoint correto `POST /message/downloadimage`
  com o objeto `Message` (whatsmeow) reconstruído da metadata (`URL`,
  `directPath`, `mediaKey`, `fileEncSHA256`, `fileSHA256`, `mediaKeyTimestamp`,
  `mimetype`), em vez do inexistente `/message/downloadmedia`. Extração de
  base64 robusta (aceita `{base64}` ou `{data:{base64}}`).

## 1.2.2+009 - 2026-05-20 (build manual, sem tag)

### Fixed
- **Múltiplas mídias em rajada eram mescladas numa só mensagem** (metadados
  contaminados, só um arquivo salvo): o buffer (`process_contact_response`) fazia
  `metadados.update()` de todos os envelopes. Agora **cada mídia vira sua própria
  `Mensagem`** (com arquivo + análise individual) e apenas os textos rápidos são
  concatenados. A mensagem primária (texto, ou a última mídia) dirige a resposta
  do bot.

## 1.2.2+008 - 2026-05-20 (build manual, sem tag)

### Added
- **Recebimento de mídia (formato whatsmeow do Go)**: `translate_go_payload`
  agora trata `Info.MediaType` (image/video/audio/document), monta o
  `data.Message.<tipo>Message` normalizando o casing do whatsmeow
  (`URL`→`url`, `fileEncSHA256`→`fileEncSha256`) e embute o `base64` inline
  (que o Go entrega no irmão `data.Message.base64`). `EvolutionMessageData`
  passa a extrair `base64` também para imagem/vídeo/documento (antes só áudio).
  Resultado: mídia recebida é decodificada e persistida em `Mensagem.arquivo_midia`
  pelo pipeline existente. Removido o diagnóstico temporário de mídia.

## 1.2.2+007 - 2026-05-20 (build manual, sem tag)

### Changed
- **Correções conforme o spec oficial do Evolution GO** (swagger `EvolutionAPI/
  evolution-go`):
  - `connect_instance`: volta a usar o campo **`subscribe`** (array de nomes
    UPPERCASE válidos `MESSAGE,CONNECTION,PRESENCE,QRCODE`) + `immediate:true`.
    O `events` do +004 era hack; o que zerava a assinatura antes eram nomes
    PascalCase inválidos.
  - **`alwaysOnline=true`** agora é o mecanismo primário de persistência da
    sessão (novo `set_advanced_settings`, chamado na criação da instância via
    `PUT /instance/{id}/advanced-settings`). O keep-alive vira fallback.
  - **Envio de mídia** (`send_media`/`send_audio`): campos corretos
    `{number, type, url, caption, filename}` (eram `mediatype`/`media`/`fileName`).

## 1.2.2+006 - 2026-05-20 (build manual, sem tag)

### Fixed
- **Keep-alive quebrava com `FieldError`**: `TenantEvolution.api_key` é property
  (decripta `_api_key`), não filtrável no ORM. A task agora filtra por
  `server_url` e valida a chave no loop.

## 1.2.2+005 - 2026-05-20 (build manual, sem tag)

### Added
- **Keep-alive da sessão Evolution Go**: task Celery `keepalive_evolution_instances`
  (beat a cada 60s) verifica `connected` via `/instance/all` e dispara
  `/instance/reconnect` quando a sessão whatsmeow cai por ociosidade — evita que o
  atendimento pare silenciosamente de receber webhooks. Registrada em
  `CELERY_BEAT_SCHEDULE` (sincronizada pelo DatabaseScheduler).

### Diagnostics (temporário)
- Log `[DIAG-TEMP-MEDIA]` na view do webhook captura o payload bruto de mensagens
  de mídia do Go para ajustar o normalizer/download (será removido após o fix).

## 1.2.2+004 - 2026-05-20 (build manual, sem tag)

### Fixed
- **Mensagens recebidas não eram processadas (formato whatsmeow do Go)**: o
  Evolution Go entrega o payload no formato do whatsmeow (`data.Info.Chat/Sender/
  ID/IsFromMe/PushName` + `data.Message.<tipo>` + `instanceName`/`instanceToken`),
  totalmente diferente do Node v2 (`data.key.remoteJid`/`data.message`). O
  normalizer extraía `data.key.remoteJid` → sempre vazio → "missing contact JID"
  → mensagem descartada. Novo `translate_go_payload()` converte o envelope Go
  para o formato Node-like (as sub-chaves de `data.Message` já são idênticas) e
  reaproveita os factories. Acoplado em `from_dict_single`/`from_dict_batch`.
- **Entrega de webhooks parava após reconectar**: o `connect_instance` enviava o
  campo `subscribe`, que o servidor Go interpreta como "zerar" a assinatura
  (`events=""`) → nenhum webhook entregue. Corrigido para enviar `events`
  (array). Eventos default ajustados para os suportados pelo Go
  (`MESSAGE,CONNECTION,PRESENCE,QRCODE`).

## 1.2.2+003 - 2026-05-20 (build manual, sem tag)

### Fixed
- **Eventos do Go em PascalCase eram descartados (mensagens inbound!)**: o Go
  emite `Message`, `QRCode`, `Connected`, `Presence`, etc. (não UPPERCASE).
  `EvolutionEventName.from_raw()` não reverificava o value map após normalizar,
  então `from_raw("Message")` → `None` e o filtro global do webhook ignorava as
  mensagens recebidas. Agora reverifica o value map normalizado e mapeia
  `Connected`/`Disconnected`/`LoggedOut` → `CONNECTION`.
- **Sem feedback visual ao conectar o WhatsApp**: (a) novo handler `_handle_connection`
  persiste `connection_state` na instância via evento `Connected` (fonte da
  verdade, independente do polling); (b) o polling de status do detalhe agora
  **retoma** quando a aba volta a ficar visível (antes morria ao trocar de aba
  para escanear o QR); (c) banner "WhatsApp conectado com sucesso!" antes do reload.

## 1.2.2+002 - 2026-05-20 (build manual, sem tag)

### Fixed
- **Status "Desconhecido" mesmo conectado**: o `GET /instance/status` do Go
  retorna `{"data": {"Connected": ..., "LoggedIn": ...}}`, não `{"state": ...}`.
  `_parse_state` agora mapeia `LoggedIn=True → "open"`, senão `"close"`.
- **QR Code não aparecia**: o QR vem do `GET /instance/qr` em `data.Qrcode`
  (data URI), não na resposta do `/instance/connect`. `InstanceQRCodeView` agora
  chama connect (configura webhook) + `get_qr_code` e parseia `data.Qrcode`/
  `data.PairingCode`.

## 1.2.2+001 - 2026-05-20 (build manual, sem tag)

### Fixed
- **`401 "not authorized"` ao conectar instância / gerar QR**: o `/instance/connect`
  do Evolution Go autentica com o **token da instância**, não com a Global API
  Key. `InstanceQRCodeView` e `InstanceWebhookView` passavam `evo_config.api_key`
  (global). Trocado para `instance.api_key` (token da instância).

## 1.2.2 - 2026-05-20

### Fixed
- **Criação de instância falhava com `400 "token is required"`**: o servidor
  Evolution Go exige um `token` no `POST /instance/create`. A view passava só
  `name`. Agora o painel gera um `token` (UUID hex) e o envia — esse token vira
  o `api_key` da instância (header `apikey` nas operações de qr/status/send),
  com fallback caso o Go não o devolva na resposta.

## 1.2.1 - 2026-05-20

### Fixed
- **500 ao gerenciar instâncias / migrations travadas no tenant**: a migration
  `0006` (Evolution Go) fazia `EvolutionInstance.objects.update(api_version=...)`
  sem `.using()`. Em multi-tenant o ORM roteava o UPDATE por uma conexão
  separada onde a coluna recém-criada (ainda não commitada na transação da
  migration) não era visível → `column api_version does not exist` e rollback de
  toda a `0006`. Resultado: as colunas `media_storage_backend`/`subscribed_events`/
  `last_connection_state` nunca eram criadas no banco do tenant e
  `/evolution/instances/` retornava 500. Corrigido fixando
  `schema_editor.connection.alias` no `RunPython`.
- **Testar Conexão com Evolution API**: `ConnectionTester` usava o endpoint v2
  `/instance/fetchInstances` (404 no Go). Trocado para `/instance/all`.

## 1.2.0 - 2026-05-20

### Changed
- **`evolution_sync` agora é exclusivo do Evolution Go**: removida toda a camada
  de coexistência v2/Go. O cliente Django fala apenas com o Evolution Go, sem
  feature flag nem código morto. Removidos `EvolutionV2Adapter`, o Protocol
  `EvolutionAPIInterface`, a factory `get_evolution_adapter`, o alias
  `EvolutionWhatsAppService`, o management command `migrate_to_evolution_go` e o
  campo `EvolutionInstance.api_version` (migration 0008). `EvolutionGoAdapter`
  passa a ser o serviço único, instanciado diretamente.
- **`views_instances` corrigido para a API do Go**: `get_status` (com token da
  instância) no lugar de `connectionState`; webhook reconfigurado via
  `/instance/connect` (não há `/webhook/set` no Go); logout usa o token da
  instância; parsing do `create_instance` tolerante ao formato do Go.

### Added
- **Avatar real do contato** (chat Phase 3.6/3.7): novo `Contato.foto_perfil`
  (+`foto_perfil_url_origem` como cache-key). O webhook trata o evento
  `CONTACTS`/`CONTACTS_UPDATE` e baixa `profilePictureUrl` para o `FileField`.
  Cards do Kanban, header do chat e mini-bar renderizam a foto com fallback de
  iniciais.

### Fixed
- **Migrations pendentes pós Phase 1/4** geradas (`Mensagem.quoted_preview`,
  `EvolutionInstance.api_key`/`media_storage_backend`).

## 1.1.1 - 2026-05-17

### Fixed
- **SSL renewal cron quebrado**: scripts em `docker/scripts/*.sh` estavam
  commitados sem bit de execução (`100644`), fazendo o cron de renovação
  diária falhar silenciosamente com `Permission denied`. Resultado: o
  certificado Let's Encrypt expirou em 15 May 2026 e o site retornou
  `NET::ERR_CERT_DATE_INVALID`. Permissões corrigidas para `100755` no
  Git (`renew-ssl.sh`, `init-ssl.sh`, `health-monitor.sh`,
  `resolve-image-tag.sh`). Cert renovado manualmente — válido até
  15 Aug 2026.

## 1.1.0 - 2026-05-16

### Added
- **Workspace de Atendimento Unificado** (`atendimento_unificado`): tela única com
  chat estilo WhatsApp Web e Kanban sobre `EtapaFluxo`/`Atendimento`. Acessível em
  `/workspace/` (feature flag `ATENDIMENTO_UNIFICADO_ENABLED` por tenant).
- **Chat em tempo real via SSE**: updates de mensagens, board e campos chegam sem
  polling. Reconexão automática com backoff exponencial.
- **Kanban drag-drop** (SortableJS): mover cards entre colunas chama `POST /board/move/`
  com rollback automático; flag `isDragging` bloqueia updates SSE durante o arrastar.
- **Campos Personalizados** (`CampoPersonalizado` / `ValorCampoAtendimento`): campos
  globais ou por fluxo, extraídos automaticamente pelo LLM via `ExtracaoCamposDatasource`
  (Pydantic `create_model` + `with_structured_output`). Badge de confiança no painel.
- **Badge SLA**: card do Kanban exibe ⚠️ SLA quando atendimento passa >8h na etapa atual
  (baseado em `MovimentoFluxo.data_movimento`).
- **Mídia outbound**: endpoint `POST /conversations/<id>/upload/` aceita multipart ≤10 MB
  e envia via Evolution API `/message/sendMedia` (serviço `media_dispatch_service`).
- **Export CSV**: `GET /workspace/api/export/?fluxo=<id>` retorna `StreamingHttpResponse`
  com `csv.writer` e `iterator(chunk_size=500)` para grandes volumes.
- **Filtro por tag**: `GET /conversations/?tag=<tag>` filtra conversas ativas.
- **GIN index** em `atu_valor_campo.valor` (jsonb_path_ops) para queries de filtro por campo.
- Helpers `get_campos_for_prompt(atendimento_id, fluxo_id)` em `selectors.py` para
  integração futura com o pipeline do bot (E.2.9b).

### Changed
- `card_renderer.render_card` inclui `tempo_na_etapa_segundos` e `sla_estourado`.
- `list_conversations` aceita parâmetro `tag` para filtragem adicional.
- `workspace_alpine.js` expandido com `initSortable`, `uploadMedia`, `filterTag` e
  handler SSE `custom_field.updated`.

### Technical
- Tabelas novas: `atu_leitura_atendimento`, `atu_campo_personalizado`, `atu_valor_campo`.
- Zero alterações em tabelas legadas (princípio de independência).
- Migrations: 0001 (LeituraAtendimento), 0002 (CampoPersonalizado/ValorCampoAtendimento),
  0003 (GIN index em valor).
- Bug corrigido: `_formatar_historico` em `extracao_campos_datasource` usava prefixos
  uppercase (`CONTATO`) mas `TipoRemetente` é lowercase (`contato`).

## 1.0.3 - 2026-02-12

### Added
- Feature `transcribe_audio` no AI Engine para transcrição de mensagens de áudio.
- Configuração de transcrição por provider/model no runtime com override por tenant.
- Integração da transcrição no orquestrador de atendimento antes da análise da mensagem.

### Changed
- Pipeline de atendimento atualizado para preservar metadados de áudio e usar texto transcrito no fluxo de análise.

### Fixed
- Correção do descarte silencioso de `audioMessage` no fluxo webhook -> buffer -> processamento.

## 1.0.2 - 2026-02-08

### Added
- Treinamentos RAG para o piloto Ecoprint (documentos e intents).
- Interface para testar queries e registrar feedback no app de treinamento.
- Bootstrap de `CoreSettings` via management command (`bootstrap_core_settings`).

### Changed
- Refactor: apps Django movidos de `src/smart_core_assistant_painel/app/ui/` para `src/smart_core_assistant_painel/app/`.
- Deploy/Docker: `DJANGO_SETTINGS_MODULE` e entrypoints atualizados para `smart_core_assistant_painel.app.core.settings` e `smart_core_assistant_painel.app.manage`.

### Notes
- Antes do deploy: rodar `migrate` (inclui migrações iniciais dos apps movidos) e executar `bootstrap_core_settings` quando aplicável.

## 0.9.0

### Added
- **Suporte Multi-Turn**: Reestruturação completa do prompt para suportar `chat_history` e contexto dinâmico, permitindo diálogos contínuos.
- **Externalização de Prompts**: Templates de prompt movidos para configuração externa, facilitando ajustes sem deploy.
- **Feedback Loop**: Sistema de coleta de avaliação de atendimento com agradecimento automático e normalização de notas.
- **Task Master 2.0**: Melhorias na geração de tasks e planejamento via AI.

### Changed
- **Melhoria no RAG**: Ajuste na recuperação de documentos para garantir carregamento completo do contexto de treinamento.

## 0.8.5

### Fixed
- **Sync Trello**: Resolução de erro `member already on card` e falhas na transferência/arquivamento de cards.
- **Mensagens Curtas**: Correção para que a IA processe mensagens como "sim" ou "não" mantendo o contexto.
- **Fluxo de Saudação**: Separação entre saudação e inquérito de necessidades para maior naturalidade.
- **UI Admin**: Correção no reset de formulários na tela de Query Compose.

## 0.8.4

### Added
- Script `migrar_remoto.py` para migração de dados remotos.
- Campo `treinamento_vetorizado` no modelo Treinamento para controle de vetorização.
- View para verificar treinamentos vetorizados.
- Configuração do Qoder para análise de código.

### Changed
- **Refatoração completa dos modelos Treinamento e Documento**: Reestruturação dos modelos para melhor organização e performance.
- **Melhoria significativa na tipagem**: Adicionadas anotações de tipo completas em models.py e correção de erros de tipo.
- **Atualização de dependências**: Atualização das bibliotecas do projeto para versões mais recentes.
- **Reorganização do ambiente Docker**: Melhorias na configuração e estrutura do ambiente de desenvolvimento.

### Fixed
- Correção de bug na avaliação de atendimento.
- Resolução do erro `redis.typing` no comando migrate-remoto.
- Ajuste no campo `models.JSONField` para aceitar `models.JSONField[dict[str, Any] | None]`.
- Correção de erros de tipo em models.py, incluindo valores de enum e anotações.
- Correção no salvamento e criação de documentos.
- Correção no admin do treinamento vetorizado.
- Correção na funcionalidade de editar treinamento.
- Correção no carregamento das variáveis de ambiente.

### Tests
- **Aumento significativo da cobertura de testes**: Cobertura aumentou de 47% para 66% com a adição de testes abrangentes em múltiplos módulos.
- Remoção da feature WAHA e melhoria na cobertura de testes.
- Correção de problemas nos testes e execução bem-sucedida da suíte completa.
- Resolução de problema com fixture `django_db_setup` vazio.

### Refactor
- **Refatoração da feature de busca similar**: Melhorias na funcionalidade de busca.
- **Refatoração da feature de chunks**: Otimização do processamento de chunks de texto.
- **Refatoração do treinamento**: Melhorias no processo de treinamento e geração de embeddings.
- Organização de imports e limpeza de código.
- Desmembramento do modelo Document para melhor estruturação.

### Chore
- Remoção do arquivo `uv.lock` do controle de versão.
- Adição do `uv.lock` ao `.gitignore`.
- Configuração de script para criação de novas features.
- Limpeza de imports e organização do código.

## 0.8.3

### Fixed
- Resolvidos conflitos de merge priorizando a branch `bugfix/fix-apps-django` nos arquivos:
  - `src/smart_core_assistant_painel/app/oraculo/admin.py`
  - `src/smart_core_assistant_painel/app/oraculo/signals.py`

### Tests
- Removido o teste obsoleto `test_vetor_storage_not_set`, que referenciava a
  propriedade descontinuada `vetor_storage`.
- Suíte de testes executada localmente com `uv run task test-all`: 295 testes
  aprovados; relatório de cobertura HTML gerado em `tests/htmlcov`.

### Chore
- Limpeza de referências a `vetor_storage` em testes e código legado.

## 0.8.2
### Added
- Nova documentação de setup completa e unificada no `README.md`.
- Scripts de setup (`ambiente_docker/`) atualizados e corrigidos para uma instalação mais fluida.
- Guia de validação para garantir que o setup funcione em um ambiente limpo do zero.

### Changed
- Refatorado e simplificado todo o processo de instalação via Docker.
- Unificados múltiplos arquivos de documentação em um `README.md` centralizado para facilitar a consulta.

### Fixed
- Corrigidos bugs no `Dockerfile` que causavam loops e falhas durante a construção da imagem.
- Resolvido problema na geração automática do arquivo `firebase_key.json`.

## 0.8.1
- **fix**: Adição do campo email ao modelo Contato (migração 0003_add_email_to_contato)
- **fix**: Correção dos testes que utilizavam o campo email no modelo Contato
- **docs**: Atualização do README-Docker.md com instruções sobre migrações
- **test**: Execução bem-sucedida da suíte de testes no Docker (305 testes passados)
- **fix**: Resolução do problema de contêineres Docker reiniciando, incluindo:
  - Correção do erro `uv: 1: [/usr/local/bin/docker-entrypoint.sh]: not found` no `smart-core-qcluster-dev`.
  - Resolução da incompatibilidade de versão do PostgreSQL (`database files are incompatible with server`) no `postgres-dev` e `evolution-api-dev` através da remoção dos volumes de dados e reinicialização dos contêineres.
- **test**: Verificação de que todos os contêineres Docker (`smart-core-qcluster-dev`, `evolution-api-dev`, `smart-core-assistant-dev`, `postgres-dev`, `redis-dev`, `postgres-django-dev`) estão em estado `running`.

## 0.8.0
- **fix**: Correção do problema "Nenhum chunk válido encontrado" no Ollama, incluindo:
  - Bug no loop de iteração em `faiss_vetor_storage.py`.
  - Valor padrão para `EMBEDDINGS_MODEL` em `service_hub.py`.
  - Configuração dinâmica da URL do Ollama em `faiss_vetor_storage.py`.
  - Integração da configuração do Ollama com Firebase Remote Config em `features_compose.py`.
  - Configuração local da `OLLAMA_BASE_URL` no arquivo `.env`.
- **docs**: Atualização da documentação `CORREÇÕES_OLLAMA.md` para refletir que o Ollama roda localmente e é acessado via `host.docker.internal` por containers Docker.
- **fix**: Ajuste da configuração de coverage para ignorar pastas de testes de apps Django, via `.coveragerc` e `pytest.ini`.
- Migração do processamento das mensagens para o cluster

## 0.7.0
- **feat**: Configuração completa do ambiente Docker com PostgreSQL e Redis
- **fix**: Correção do problema de geração de QR code na Evolution API
- **fix**: Implementação de tratamento robusto de encoding UTF-8 no webhook WhatsApp
- **fix**: Correção de caminhos Docker e configuração do ambiente de desenvolvimento
- **docs**: Atualização completa da documentação Docker (README-Docker.md)
- **docs**: Documentação para arquitetura PostgreSQL+Redis
- **feat**: Configuração otimizada do QR Code da Evolution API (30s limite, cor personalizada)
- **feat**: Implementação de cache Redis para Evolution API
- **feat**: Configuração de webhook global para Evolution API
- **feat**: Bypass do Firebase Remote Config em modo DEBUG
- **refactor**: Ajustes nas variáveis de ambiente e finalização da configuração Docker
- **refactor**: Revisão do fluxo de recebimento de mensagens
- **refactor**: Atualização do diagrama webhook_whatsapp

## 0.6.0
- **feat**: Adicionada a chave "historico_atendimentos" na função `carregar_historico_mensagens` em `src/smart_core_assistant_painel/app/models.py`.
- **fix**: Removido o campo `Data fim` da lista `readonly_fields` da classe `AtendimentoAdmin` para permitir edição.
- **fix**: Resolvidas falhas nos testes, incluindo a atualização do teste `test_call_non_str`.
- **refactor**: Ajustes gerais de tipo e formatação de código.
- **test**: Ajustados testes para refletir o novo formato de histórico de atendimento.
- **test**: Adicionados testes para cobertura das linhas 138 e 150 do método `_formatar_historico_atendimento`.

## 0.5.0
1 - Correções gerais no dicionario
2 - Simplificação da feature analise_previa_mensagem para rodar em llms menores

## 0.4.0
1 - Refatoração do model treinamento para setar e carregar os documentos do langchain
2 - Criação de modelos para controle de atendimento em Oraculo
3 - Criação de diagrama de relacionamento Oraculo
4 - Criação de diagrama de fluxo de atendimento Oraculo
5 - Feature analise_previa_mensagem para extração dos intents e entity das mensagens 

## 0.3.0
1 - Migração dos metodos em signals para features em ai_engine
2 - Refatoração e melhoria dos códigos para treinamento

## 0.2.0
1 - Services configurado
2 - Features ai_engine implantado

## 0.1.0
Configuração inicial do projeto.
1 - Start e configuração do Django.
2 - Initial load configurado

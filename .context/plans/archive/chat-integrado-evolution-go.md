---
status: archived
archived: 2026-05-20
archived_reason: "PREVC concluído (P→R→E→V→C). Phases 1-6 entregues; evolution_sync agora exclusivo Evolution Go (v2 removido); avatar real do contato; release 1.2.0."
generated: 2026-05-19
agents:
  - type: "backend-specialist"
    role: "Reescrever evolution_sync para Evolution Go e novos endpoints"
  - type: "frontend-specialist"
    role: "Refatorar UI do chat (Alpine, CSS .ws-*) para WhatsApp Web parity"
  - type: "feature-developer"
    role: "Implementar read receipts, reply, presence, voice recording, reações"
  - type: "database-specialist"
    role: "Migrations para Mensagem, MensagemReacao, Contato (avatar/presence)"
  - type: "code-reviewer"
    role: "Revisar PRs garantindo aderência ao design system e padrões"
  - type: "test-writer"
    role: "Testes de regressão do evolution_sync e dos novos endpoints"
docs:
  - "../../docs_dev/planejamento/chat_integrado/README.md"
  - "../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md"
  - "../../docs_dev/planejamento/chat_integrado/evolution_go_migracao.md"
phases:
  - id: "phase-1"
    name: "Migração Evolution Go (foundation)"
    prevc: "P"
    agent: "backend-specialist"
  - id: "phase-2"
    name: "Read Receipts + Auto-mark-read"
    prevc: "E"
    agent: "feature-developer"
  - id: "phase-3"
    name: "UX Quick Wins (date sep, scroll, drag&drop, avatar)"
    prevc: "E"
    agent: "frontend-specialist"
  - id: "phase-4"
    name: "Reply (mensagem citada)"
    prevc: "E"
    agent: "feature-developer"
  - id: "phase-5"
    name: "Presence bidirecional + Voice recording"
    prevc: "E"
    agent: "feature-developer"
  - id: "phase-6"
    name: "Validação e cutover"
    prevc: "V"
    agent: "test-writer"
---

# Chat Integrado WhatsApp + Migração Evolution Go

> **Não duplica conteúdo.** Este plano é o **mapa de execução** que referencia os dois documentos de planejamento:
> - 📄 [Plano principal de UX/produto](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md)
> - 📄 [Companion técnico de migração Evolution Go](../../docs_dev/planejamento/chat_integrado/evolution_go_migracao.md)
> - 📄 [Índice da pasta](../../docs_dev/planejamento/chat_integrado/README.md)

## Task Snapshot

- **Primary goal:** Tornar o painel um substituto fluido do WhatsApp Web (chat + kanban integrados) **e adaptar o cliente Django (`evolution_sync`) para consumir o Evolution Go já em produção** nos servidores dos tenants.
- **Success signal:** Atendentes operam 100% no painel, sem precisar abrir WhatsApp Web em paralelo; o tenant **não toca no servidor** — só preenche `server_url` + `api_key` em `tenants/config/evolution/` e o sistema cuida de criar instâncias, configurar webhooks, baixar QR e baixar mídia automaticamente; `evolution_sync` falando 100% Evolution Go nas instâncias migradas, com `EvolutionV2Adapter` removido após período de coexistência.
- **Branch base:** `feature/chat-whatsapp-redesign` (já contém o piso da experiência).
- **Fora do escopo:** deploy, configuração ou manutenção dos containers Evolution Go nos VPS dos tenants (responsabilidade do devops do servidor — Hostinger, ex.: `paulo-ecoprint-evolution`, repo `paulo-ecoprint-server`). Este plano adapta o **cliente** para falar com o servidor existente, e a interface do tenant nunca exige acesso SSH/Docker.
- **✅ Blocker de licença resolvido em 2026-05-19 10:27 UTC:** servidor `paulo-ecoprint-evolution` agora retorna `200 OK` em `/instance/all`. Pronto para Phase 1.11 (smoke test) assim que o `EvolutionGoAdapter` estiver pronto. Inconsistências do SETUP_INFO (Task 1.10) seguem pendentes do devops do servidor — não bloqueiam o desenvolvimento. Detalhes na [§8.2 do companion](../../docs_dev/planejamento/chat_integrado/evolution_go_migracao.md).

## Escopo

| Camada | Mudanças | Documento de referência |
|---|---|---|
| `evolution_sync` (backend WhatsApp) | Reescrita do `EvolutionWhatsAppService` em dois adapters (v2/Go), adapter de eventos, novo modelo `api_version`, novos endpoints `markread/react/presence/avatar` | [`evolution_go_migracao.md`](../../docs_dev/planejamento/chat_integrado/evolution_go_migracao.md) §3, §6, §7 |
| `atendimentos` (modelos) | `Mensagem.status_envio`, `Mensagem.respondendo_a`, `Mensagem.encaminhada`, `Mensagem.midia_url_remota`; novo `MensagemReacao`; campos novos em `Contato` (avatar, presence) | [`chat_whatsapp_experiencia_completa.md`](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md) §4 |
| `atendimento_unificado` (UI chat) | Lightbox (✅ já feito), date separators, scroll-to-bottom, divisor "novas mensagens", reply UI, reactions UI, recording UI, drag&drop | [`chat_whatsapp_experiencia_completa.md`](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md) §3 fases 1-2 + §6 |
| `tenants/views/config_evolution` | Fluxo onde o tenant fornece **apenas `server_url` + Global API Key**; o sistema provisiona tudo (create/connect/qr/status/webhook automáticos) | [`evolution_go_migracao.md`](../../docs_dev/planejamento/chat_integrado/evolution_go_migracao.md) §3.1 |
| Endpoints Django | 7 novos: `mark-read`, `typing`, `react`, `send-audio`, `send-reply`, `messages/search`, `forward` | [`chat_whatsapp_experiencia_completa.md`](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md) §5 |
| Pendências com devops do servidor | Ativar licença Go; corrigir `paulo-ecoprint-server/SETUP_INFO.md` (3 inconsistências detectadas) — sem alterar o servidor | [`evolution_go_migracao.md`](../../docs_dev/planejamento/chat_integrado/evolution_go_migracao.md) §8.2-§8.3 |

## Estado de partida

Branch `feature/chat-whatsapp-redesign` já entregou (já commitado/em PR):
- Mídia visível inline (img/áudio/vídeo/PDF)
- Lightbox + iframe PDF
- Toggle "Ver análise IA"
- Card kanban com `contato_nome`/`assunto` separados
- Normalização de `push_name`
- Campos `Mensagem.arquivo_midia` (FileField) + `Mensagem.analise_midia` (TextField)

Resto deste plano ataca tudo que falta para fechar a experiência.

## Riscos & Dependências

| Risco | Probabilidade | Impacto | Mitigação | Owner |
|---|---|---|---|---|
| Cutover Evolution Go quebrar tenants ativos | Média | Alto | Feature flag `api_version` por instância; rollback alterando o campo no admin; v2 adapter coexiste 2 semanas | `backend-specialist` |
| `mediaUrl` do servidor Evolution Go vir sem CORS configurado | Média | Médio | Proxy via Django como fallback (não dependemos do servidor para resolver) + escalonar com devops do tenant | `backend-specialist` |
| Rate limit do WhatsApp por excesso de `markread`/`presence` | Baixa | Médio | Throttle no service (1 markread por conversa por abertura; 1 presence a cada 3s) | `backend-specialist` |
| `MediaRecorder API` indisponível em navegador antigo | Baixa | Baixo | Fallback gracioso: esconde botão de áudio se API ausente | `frontend-specialist` |
| Servidor do tenant ainda não suporta algum endpoint Go esperado | Baixa | Alto | Checklist em 1.9 valida antes de migrar; se faltar, mantém em v2 até devops resolver | `backend-specialist` |

### Dependências
- **Externa (fora do escopo deste plano):** Evolution Go rodando e operacional no servidor do tenant (ex.: container `paulo-ecoprint-evolution` no Hostinger). Configuração do servidor, S3/MinIO e healthcheck são responsabilidade do devops/tenant.
- **Interna:** Branch `feature/chat-whatsapp-redesign` precisa ser mergeada antes de iniciar Fase 2.
- **Confirmação prévia ao cutover:** seguir o checklist da §8 do companion antes de mudar uma instância para `api_version="go"`. Se algo não estiver pronto no servidor, a instância fica em `v2` até o devops resolver.

### Pressupostos
- O servidor Evolution Go já está estável e respondendo no endpoint atual.
- Os tenants existentes podem ser migrados um a um (não há big-bang obrigatório).
- O painel pode ficar com janela curta (<5min) de manutenção durante o cutover.

## Working Phases

### Phase 1 — Migração Evolution Go (PREVC: P→E→V)
> **Primary Agent:** `backend-specialist`
> **Detalhe técnico:** [`evolution_go_migracao.md`](../../docs_dev/planejamento/chat_integrado/evolution_go_migracao.md)

**Objective:** Substituir todas as chamadas v2 do `evolution_sync` por chamadas Evolution Go, mantendo coexistência via feature flag.

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 1.1 | Criar `EvolutionAPIInterface` (Protocol) com todos os métodos esperados | backend-specialist | pending | `services/evolution_api.py` refatorado em interface |
| 1.2 | Mover impl atual para `EvolutionV2Adapter` | backend-specialist | pending | `services/evolution_v2_adapter.py` |
| 1.3 | Implementar `EvolutionGoAdapter` com 12 métodos Go | backend-specialist | pending | `services/evolution_go_adapter.py` |
| 1.4 | Factory `get_evolution_adapter(api_version)` | backend-specialist | pending | `services/__init__.py` |
| 1.5 | Estender `EvolutionEventName.from_raw()` para aceitar UPPERCASE + lowercase dot | backend-specialist | pending | `domain/schemas.py` |
| 1.6 | Migration: `EvolutionInstance.api_version`, `media_storage_backend`, `subscribed_events`, `last_connection_state` | database-specialist | pending | nova migration |
| 1.7 | Atualizar callers do orchestrator/message_dispatch para usar factory | backend-specialist | pending | diff cross-app |
| 1.8 | Adaptar `views_instances.py` E `tenants/views/config_evolution`: o tenant preenche `server_url` + Global API Key apenas → sistema dispara `POST /instance/create`, `POST /instance/connect` (com webhook + subscribe), `GET /instance/qr`, `GET /instance/status` automaticamente. Sem chamadas manuais ao servidor pelo operador. | backend-specialist | pending | UI tenant fluxo end-to-end |
| 1.9 | Substituir `_fetch_media_base64_from_evolution` (v2) por: (a) usar `data.message.mediaUrl` se vier; (b) fallback `POST /message/downloadmedia` (Go) ou `POST /chat/getBase64FromMediaMessage` (v2) | backend-specialist | pending | `attendance_orchestrator.py` |
| 1.10 | Reportar ao devops do servidor (via README do paulo-ecoprint-server): (1) ativar licença; (2) corrigir SETUP_INFO §"Endpoints" com `/send/text` `/send/media` (não `/message/sendText/sendMedia`); (3) remover seção `/webhook/set` `/webhook/find` que não existe em Go; (4) confirmar formato real do payload do webhook (`MESSAGE` vs `messages.upsert`) | documentation-writer | pending | issue/PR no repo do servidor |
| 1.11 | Smoke test manual no painel (Django): criar instância de QA contra Go, gerar QR, conectar, enviar texto, receber mensagem, validar `mediaUrl` no payload | test-writer | pending | checklist preenchido |

**Commit checkpoint:** `feat(evolution_sync): migrate to Evolution Go with v2 backwards-compat`

---

### Phase 2 — Read Receipts + Auto-mark-read (PR 1 do plano principal)
> **Primary Agent:** `feature-developer`
> **Detalhe UX:** [`chat_whatsapp_experiencia_completa.md`](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md) §3 Fase 1, item 1; §3 Fase 1, item 6

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 2.1 | Modelo: adicionar `Mensagem.status_envio` (choices) + `data_entregue` + `data_lida`; deprecar `respondida` (manter por compat) | database-specialist | pending | migration |
| 2.2 | Tratar evento `MESSAGE_UPDATE` no webhook → atualiza `status_envio` da Mensagem correspondente por `message_id_whatsapp` | feature-developer | pending | `services/webhook.py` |
| 2.3 | Endpoint `POST /api/atendimento/{id}/mark-read` → marca `Mensagem.lido=True` no banco + dispara `markread` no adapter Go | feature-developer | pending | `views_api.py` |
| 2.4 | Hook no `_doOpenChat` (Alpine) → chama `/mark-read` quando conversa abre | frontend-specialist | pending | `workspace_alpine.js` |
| 2.5 | UI: ✓ (pendente) → ✓ (enviada) → ✓✓ (entregue) → ✓✓ azul (lida) — derivado de `status_envio` | frontend-specialist | pending | `chat_message.html` + CSS |
| 2.6 | Throttle no `mark-read`: 1 chamada por abertura de conversa (não a cada nova mensagem) | feature-developer | pending | service guard |

**Commit checkpoint:** `feat(chat): read receipts (✓ → ✓✓ → ✓✓ azul) com auto-mark-read`

---

### Phase 3 — UX Quick Wins (PR 2 do plano principal)
> **Primary Agent:** `frontend-specialist`
> **Detalhe UX:** [`chat_whatsapp_experiencia_completa.md`](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md) §3 Fase 1, itens 2-5

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 3.1 | Date separators (`Hoje` / `Ontem` / `DD/MM/AAAA`) entre mensagens | frontend-specialist | pending | template + CSS `.ws-chat__day-sep` |
| 3.2 | Agrupamento visual de bolhas consecutivas (<2min, mesmo remetente) → classe `.ws-bub--stacked` | frontend-specialist | pending | `chat_message.html` + CSS |
| 3.3 | Scroll-to-bottom button quando rolagem >300px (estado `scrollAnchorBottom` no store) | frontend-specialist | pending | `workspace_alpine.js` + `.ws-chat__scroll-btn` |
| 3.4 | Divisor "▼ N novas mensagens" no ponto de leitura anterior | frontend-specialist | pending | store + CSS `.ws-chat__unread-div` |
| 3.5 | Drag & drop de arquivos no `.ws-chat__body` → injeta no composer | frontend-specialist | pending | `workspace_alpine.js` |
| 3.6 | Tratar evento `CONTACTS_UPDATE` no webhook → baixar `profilePictureUrl` para `Contato.foto_perfil` (novo FileField) | backend-specialist | pending | `services/webhook.py` + migration |
| 3.7 | Avatar real renderizado nos cards/header quando `Contato.foto_perfil` existe; fallback iniciais | frontend-specialist | pending | templates |

**Commit checkpoint:** `feat(chat): date separators, scroll-to-bottom, drag&drop, avatar real`

---

### Phase 4 — Reply / Mensagem citada (PR 3 do plano principal)
> **Primary Agent:** `feature-developer`
> **Detalhe UX:** [`chat_whatsapp_experiencia_completa.md`](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md) §3 Fase 2, item 7

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 4.1 | Modelo: `Mensagem.respondendo_a` (FK self) | database-specialist | pending | migration |
| 4.2 | Webhook: tratar `contextInfo.quotedMessage` → grava `respondendo_a` na mensagem inbound | feature-developer | pending | `services/webhook.py` |
| 4.3 | Endpoint `POST /api/atendimento/{id}/send-reply` body `{texto, respondendo_a_id}` → envia via adapter Go com `quoted` no payload | feature-developer | pending | `views_api.py` |
| 4.4 | UI: hover na bolha mostra ▼ → menu de contexto → item "Responder" preenche `replyTo` no store | frontend-specialist | pending | `workspace_alpine.js` + `.ws-bub__menu` |
| 4.5 | Composer mostra preview da mensagem citada acima do textarea; X cancela | frontend-specialist | pending | `workspace.html` |
| 4.6 | Balão renderiza tira lateral colorida com preview da mensagem citada | frontend-specialist | pending | `chat_message.html` + `.ws-bub__reply` |

**Commit checkpoint:** `feat(chat): reply (mensagem citada) entrada e saída`

---

### Phase 5 — Presence bidirecional + Voice recording (PRs 4 e 5 do plano principal)
> **Primary Agent:** `feature-developer`
> **Detalhe UX:** [`chat_whatsapp_experiencia_completa.md`](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md) §3 Fase 2, itens 9-11

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 5.1 | Endpoint `POST /api/atendimento/{id}/typing` → propaga para `/message/presence` (Go) com throttle 3s | feature-developer | pending | `views_api.py` |
| 5.2 | Composer Alpine: debounce 400ms → dispara typing OUT; stop após 5s ou no send | frontend-specialist | pending | `workspace_alpine.js` |
| 5.3 | Webhook: tratar evento `PRESENCE` → broadcast via SSE/WebSocket → store `contactPresence` | feature-developer | pending | `services/webhook.py` + SSE channel |
| 5.4 | Header do chat: mostra "digitando..." (texto) ou "gravando áudio..." (com indicador animado) | frontend-specialist | pending | `workspace.html` + `.ws-typing-dots` |
| 5.5 | Botão de microfone no composer (`MediaRecorder API`) → grava WebM/OGG | frontend-specialist | pending | `workspace_alpine.js` |
| 5.6 | UI de gravação: waveform fake animado + duração + cancelar/enviar | frontend-specialist | pending | `.ws-record` CSS |
| 5.7 | Endpoint `POST /api/atendimento/{id}/send-audio` (multipart) → upload via adapter Go `/send/media type=audio` | feature-developer | pending | `views_api.py` |
| 5.8 | Durante gravação: dispara `typing` com `isAudio=true` para o cliente ver "gravando áudio..." no WhatsApp | feature-developer | pending | `workspace_alpine.js` integração |

**Commit checkpoint:** `feat(chat): presence bidirecional + gravação de áudio no painel`

---

### Phase 6 — Validação e cutover (PREVC: V→C)
> **Primary Agent:** `test-writer`

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| 6.1 | Smoke test full-flow: receber imagem→áudio→PDF→vídeo→reply→reaction, validar UI e read receipts | test-writer | pending | checklist + screenshots |
| 6.2 | Teste de regressão do `evolution_sync` com `api_version="go"` em tenant de QA | test-writer | pending | doc test run |
| 6.3 | Migração de instâncias produção no painel: `api_version="v2"` → `"go"` (management command idempotente, alterando apenas o registro Django — o servidor já está em Go) | backend-specialist | pending | management command |
| 6.4 | Confirmar com o devops que o healthcheck do servidor está saudável após cutover (acompanhar, não configurar) | backend-specialist | pending | print/relato no checklist |
| 6.5 | Após 2 semanas estável: remover `EvolutionV2Adapter` e `get_base64_from_media` | refactoring-specialist | pending | PR de cleanup |
| 6.6 | Atualizar `README.md` da pasta `chat_integrado` marcando itens entregues ✅ | documentation-writer | pending | doc atualizado |

**Commit checkpoint:** `chore(evolution_sync): cleanup v2 adapter após cutover Go estável`

## Rollback Plan

### Triggers
- Mensagens em produção começam a falhar (erro 5xx no `/send/text`).
- `mediaUrl` retornando 403 (CORS / signed URL quebrada).
- Spike de erros 500 no webhook receiver após mudança do adapter de evento.

### Rollback por fase

| Phase | Ação de rollback | Tempo |
|---|---|---|
| 1 (Migração Go) | Atualizar `EvolutionInstance.api_version="v2"` no admin do tenant; webhook continua funcionando porque o adapter aceita ambos formatos | <5min |
| 2-5 (Features) | Revert do PR específico; o restante do sistema continua operando | <30min cada |
| Cutover (6.3) | Re-executar management command com `--rollback`; instâncias voltam para v2 | <15min |

## Métricas de sucesso

Conforme [`chat_whatsapp_experiencia_completa.md`](../../docs_dev/planejamento/chat_integrado/chat_whatsapp_experiencia_completa.md) §9:

- **% mensagens com ✓✓ azul disparado**: meta 95%+.
- **Tempo médio de resposta do atendente**: redução de 20-30% após PR 5 (áudio).
- **CPU do worker Celery durante recebimento de mídia**: redução >50% após cutover Go (sem `getBase64FromMediaMessage`).
- **Frequência de "abrir WhatsApp Web em paralelo"**: zero relatos após 4 semanas em produção.
- **Latência typing → "digitando" no cliente**: <500ms.

## Evidence & Follow-up

### Artefatos a coletar por phase
- Phase 1: diff do `evolution_sync`, screenshots de QR/conexão na nova UI, log do health-monitor.
- Phase 2: screenshot dos 4 estados de ✓, log do webhook `MESSAGE_UPDATE`.
- Phase 3: screenshots before/after dos cards e do chat com date separators.
- Phase 4: vídeo curto de fluxo de reply ponta a ponta.
- Phase 5: vídeo do typing bidirecional e do envio de áudio.
- Phase 6: dashboard de métricas + checklist preenchido + atas de QA.

### Follow-up
| Ação | Owner | Quando |
|---|---|---|
| Atualizar `docs_dev/planejamento/chat_integrado/README.md` marcando ✅ | documentation-writer | A cada PR mergeado |
| Atualizar `MEMORY.md` com aprendizados específicos do Evolution Go | solo-dev | Após Phase 1 |
| Considerar Phase 7+ (encaminhar, busca, online/last seen) | planner | Após Phase 6 entregue |

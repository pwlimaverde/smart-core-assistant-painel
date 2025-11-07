# Kanban Dinâmico — Guia de Seleção de Provedor e Especificação Agnóstica

## Objetivo
- Estabelecer requisitos funcionais e técnicos para implementar um Kanban dinâmico (criação de boards/colunas/cards via API), independentemente do provedor.
- Facilitar a análise e a escolha de um novo serviço que atenda ao fluxo operacional da Central de Atendimento.
- Nota: Notion não será utilizado para criação dinâmica de quadros, por limitação da API quanto a “views”.

## Escopo Funcional
- Criar automaticamente “boards” por par `Departamento+Fluxo` com nome dinâmico `departamento-fluxo` (ex.: `comercial-orcamento`).
- Criar automaticamente “colunas/listas” por `EtapaFluxo` (ex.: `fila`, `trabalho`, `espera`, `finalizacao`).
- Gerenciar “cards” que representam `Atendimentos`, permitindo mover entre colunas com refletência de regras de negócio.
- Filtrar e visualizar cards por `departamento`, `fluxo`, `etapa`, `atendente`, `prioridade` e `tags`.
- Registrar histórico completo de movimentos (origem/destino, atendente, tempo, motivo) para auditoria e métricas.
- Atualizações em tempo real no painel (WebSockets), refletindo alterações de estado e movimentos.

## Requisitos Técnicos Essenciais (Provedor)
- API para CRUD de `board`, `list/column` e `card` (criação/movimentação).
- Webhooks para eventos críticos (ex.: `card_moved`, `card_created`, `list_created`).
- Autenticação segura (API Key, OAuth 2.0) e suporte a escopos/ACL.
- Rate limits previsíveis e documentação clara de erros.
- Suporte a campos customizados (ex.: prioridade, tags, relação externa `external_id`).
- Pesquisa e filtros via API (para sincronização e reconciliação).
- Anexos e comentários em cards (para contexto operacional, opcional).
- Logs de auditoria e metadados de mudanças.
- SDKs oficiais ou documentação REST estável.
- Compatibilidade com execução em Docker (testes) e Windows (desenvolvimento).

## Critérios de Seleção (Matriz de Avaliação)
- Funcionalidade:
  - Criação dinâmica de board/colunas/cards via API.
  - Webhooks ricos (mover, criar, atualizar, excluir).
  - Campos customizados e filtros avançados.
- Técnicos:
  - Autenticação/segurança, rate limits, SLA.
  - SDKs, documentação e exemplos.
  - Performance e limites de payload.
- Operacionais:
  - Custo/licenciamento, governança de acesso.
  - Opções SaaS vs On-prem; facilidade de operação.
  - Conformidade (LGPD/GDPR) e residência de dados.
- Integração:
  - Webhook inbound confiável (assinatura/verificação).
  - Idempotência e reconciliação.
  - Facilidade de modelar mapeamentos (`external_id`).

## Modelo de Dados Canônico (Agnóstico)
- `Board` (Departamento+Fluxo):
  - `board_id`: identificador do provedor.
  - `name`: `departamento-fluxo`.
  - `columns`: coleção de colunas/listas.
  - `metadata`: configurações e flags.
- `Column` (EtapaFluxo):
  - `column_id`: identificador da coluna/lista no board.
  - `name`: `etapa_slug`.
  - `order`: posição.
  - `type`: FILA | TRABALHO | ESPERA | FINALIZACAO.
- `Card` (Atendimento):
  - `card_id`: identificador do provedor.
  - `external_id`: ID local do atendimento.
  - `title`, `description`.
  - `department`, `flow`, `stage`, `assignee`, `priority`, `tags`.
  - `attachments`, `comments` (opcional).
- `Movement` (histórico):
  - `card_id`, `from_column_id`, `to_column_id`.
  - `actor` (atendente), `reason`, `timestamp`, `duration_seconds`.

## Fluxos Operacionais
- Cadastro de Etapa:
  - Resolver `departamento_slug` e `fluxo_slug`.
  - Verificar existência do `board (departamento-fluxo)`; criar se necessário.
  - Criar “coluna/lista” para a nova etapa; atualizar mapa `stage → column_id`.
- Movimentação de Card:
  - Ao mover `FILA → TRABALHO`: atribuir card ao `actor` (quem moveu).
  - Ao mover `TRABALHO/ESPERA → FILA`: remover atribuição.
  - Movimentos entre etapas de trabalho/espera: manter atribuição.
- Sincronização:
  - Atualizar `Atendimento` local em cada movimento; persistir `Movement`.
  - Em caso de webhook, refletir movimento no banco; em caso de API outbound, enviar mudança ao provedor.

## Integração e Sincronização
- Adapter `BoardClient` (Provider-agnóstico):
  - `create_board(name)`, `create_column(board_id, name, order)`, `create_card(...)`, `move_card(card_id, column_id)`.
  - `get_board(board_id)`, `get_columns(board_id)`, `find_card_by_external_id(external_id)`.
  - `register_webhook(callback_url)`, `verify_webhook_signature(headers, body)`.
- Mapeamentos persistentes:
  - `ExternalBoardConfig`: `slug`, `service_type`, `board_id`, `columns_map`.
  - `BoardObjectMapping`: `local_model`, `local_id`, `card_id`, `board_id`, `column_id`.
- Reconciliação e Idempotência:
  - Antes de criar, procurar por `external_id`; se existir, reusar e atualizar.
  - Operações com “chave de deduplicação” e retries exponenciais.

## Segurança e Conformidade
- Segredos em `.env` (API keys, tokens, callback URLs) com `python-decouple`.
- Assinatura/verificação de webhooks; rejeitar requests sem assinatura válida.
- Rate limiting e proteção contra replay.
- Auditoria: logs estruturados (`loguru`) e trilha de mudanças.
- Conformidade com LGPD/GDPR; retenção de dados e escopo mínimo.

## Observabilidade
- Logs: criação, movimentação, falhas, retries.
- Métricas: tempo em etapa, produtividade, taxa de devolução, throughput.
- Alertas: erros de sincronização, falhas de webhook, rate limit excedido.

## Testes e Validação
- Executar em Docker: `uv run task test-docker`.
- Testes de unidade: adapter e serviços (mock HTTP, idempotência, reconciliação).
- Testes de integração: criação de board, colunas, cards, movimentação, webhook.
- Cobertura mínima: 80%.

## Critérios de Aceitação
- Cadastro de nova `EtapaFluxo` cria/valida board e coluna correspondentes.
- Cards de `Atendimento` aparecem no board correto e movem entre colunas com regras de atribuição aplicadas.
- Webhooks (quando habilitados) atualizam estado local em tempo real.
- Métricas e auditoria disponíveis; erros tratados com retries e logs claros.

## Plano de POC (Prova de Conceito)
- Semana 1:
  - Implementar adapter genérico `BoardClient` e `ExternalBoardConfig`.
  - Sinal `post_save(EtapaFluxo)` chamando `ensure_board_and_stage(...)`.
- Semana 2:
  - `BoardSyncService` (criar/mover cards, mapear external_id).
  - Endpoint webhook com verificação de assinatura; atualização de `MovimentoFluxo`.
- Semana 3:
  - Painel Kanban consumindo API e WebSockets (Django Channels).
  - Testes e métricas; documentação de `.env.example`.

## Checklist de Avaliação de Provedor
- API de criação dinâmica (board/list/card) e webhooks robustos.
- Campos customizados, filtros e buscas.
- Autenticação, ACL e auditoria.
- Rate limits e SLAs aceitáveis.
- SDKs e documentação madura.
- Custo/licenciamento e governança.
- Opções SaaS vs On-prem e adequação ao seu ambiente.

## Roadmap de Implementação (Agnóstico)
- Definir provedor alvo e credenciais em `.env`.
- Implementar adapter específico herdando de `BoardClient`.
- Migrar sinais e serviços para utilizar o adapter ao cadastrar etapas e movimentar atendimentos.
- Configurar webhook receptor (Docker, Windows compatível) e canais WebSocket.
- Publicar documentação e exemplos de uso; validar com `uv run task test-docker`.

---

Este guia estabelece uma base neutra para seleção e integração de um provedor de Kanban dinâmico, mantendo o projeto disciplinado (segurança, testes, observabilidade) e aderente aos requisitos operacionais da Central de Atendimento.
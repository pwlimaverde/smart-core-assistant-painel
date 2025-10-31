# Checklist — Integração AppFlowy

## Status Geral

- Fase 1 concluída (modelos e sinais). Fase 2 em execução.
- Demais fases planejadas com escopo e critérios de aceite definidos.

## Entregas Concluídas (v)

- v Isolar Notion para não interferir na integração AppFlowy.
- v Remover `notion_sync` de `INSTALLED_APPS` e documentar flag
  `NOTION_SYNC_ENABLED: False`.
- v Ignorar suíte de testes do Notion em `pytest.ini`.
- v Comentar task `init-sync-records` em `pyproject.toml`.
- v Criar app Django `appflowy_adapter` e registrar URLs sob
  `/api/appflowy_adapter/`.
- v Adicionar endpoint de saúde e testes básicos do adapter.
- v Iniciar crate Rust `django_sync_provider` com trait `RemoteSync` e
  métodos stub.
- v Modelos do `appflowy_adapter` para workspace/grid/columns/rows e
  valores de célula (`RowValue`) e estado de sincronização (`SyncState`).
- v Sinais `post_save`/`post_delete` de `Atendimento` espelhando linhas
  no Grid, com `version` e idempotência por `ticket_id`.
- v `AppFlowyAdapterConfig.ready()` importando `signals` para registro
  automático na inicialização do app.

## Em Execução

- Implementar autenticação JWT (login/refresh) no `appflowy_adapter`.
- Migrar endpoints para DRF com serializers e validação.
- Expor CRUD real de `rows` e `grid_schema` usando os modelos do adapter.
- Adicionar checagem de `version` com `If-Match` na atualização.
- Atualizar `.env.example` com variáveis do adapter (sem valores).
- Testes para sinais, modelos e endpoints; cobertura ≥ 80%.

## Próximas Etapas Detalhadas

- Backend (Django):
  - Converter views para DRF e criar serializers de `Row` e `Column`.
  - Implementar `GET /workspaces`, `GET /grids/{grid_id}` (`grid_schema`).
  - Implementar `GET/POST /grids/{grid_id}/rows` e
    `PUT/DELETE /grids/{grid_id}/rows/{row_id}` com `If-Match`.
  - Autenticação JWT (login/refresh) e permissões mínimas.

- Provider (Rust):
  - Implementar `pull_rows`/`push_rows` com `reqwest` e JWT.
  - Persistir `sync_state` (último `since`, `version`) e backoff.

- Frontend (Flutter):
  - Tela de configurações para `server_url` e credenciais.
  - Indicadores de status de sincronização e conflitos.

- Infra/Observabilidade:
  - Logs estruturados (`loguru`) e CLI de diagnóstico (`rich`).
  - SSE/WebSocket (opcional) para eventos de mudança.
  - Testes ponta-a-ponta e cobertura ≥ 80% via `uv run task test-docker`.

## Critérios de Aceite (MVP)

- CRUD funcional do Grid Atendimentos sincronizando com Django.
- Offline-first com persistência em SQLite e sincronização posterior.
- JWT curto + refresh funcionando no Desktop.
- Logs estruturados e correlação por `ticket_id` no backend.
- Cobertura de testes ≥ 80% e CI verde.

## Observações

- Manter escopo focado no Grid de Atendimentos (MVI).
- Evoluir de LWW para CRDT apenas se necessário.
- Evitar segredos em código e documentar variáveis em `.env.example`.

## Critérios de Aceite (MVP)

- CRUD funcional do Grid Atendimentos sincronizando com Django.
- Offline-first com persistência em SQLite e sincronização posterior.
- JWT curto + refresh funcionando no Desktop.
- Logs estruturados e correlação por `ticket_id` no backend.
- Cobertura de testes ≥ 80% e CI verde.

## Observações

- Manter escopo focado no Grid de Atendimentos (MVI).
- Evoluir de LWW para CRDT apenas se necessário.
- Evitar segredos em código e documentar variáveis em `.env.example`.
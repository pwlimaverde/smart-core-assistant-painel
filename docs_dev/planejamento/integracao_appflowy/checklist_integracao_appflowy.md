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

### Backend (Django)

- Migrar para DRF e criar serializers mínimos:
  - `RowSerializer` (id, ticket_id, name, status, priority, assigned_to, tags, version, updated_at, received_at, channel, sla_due, last_message).
  - `ColumnSerializer` (id, name, type, options).
- Autenticação JWT:
  - Endpoints: `POST /auth/login`, `POST /auth/refresh` (usar `djangorestframework-simplejwt`).
  - Permissões: requer JWT para todas as rotas do adapter.
- Metadados:
  - `GET /workspaces` → lista id/nome.
  - `GET /grids/{grid_id}` → esquema e colunas.
- Dados do Grid (Atendimentos):
  - `GET /grids/{grid_id}/rows?since=<ISO8601>` → delta incremental.
  - `POST /grids/{grid_id}/rows` → criação idempotente por `ticket_id`.
  - `PUT /grids/{grid_id}/rows/{row_id}` com `If-Match: <version>` → 200 quando ok; 412 em conflito.
  - `DELETE /grids/{grid_id}/rows/{row_id}` → 204; respeitar integridade dos sinais.
- Observabilidade:
  - Logs estruturados com `loguru` (campos: `row_id`, `ticket_id`, `version`).
  - CLI de manutenção com `rich` (opcional).
- Testes (≥ 80%):
  - Unit: serializers, normalização, sinais.
  - Integração: autenticação, CRUD e controle de versão.

### Provider (Rust)

- `DjangoSyncProvider` com `reqwest` + JWT:
  - `login/refresh` (persistir tokens seguros).
  - `pull_rows(since)` e `push_rows(batch)` com tratamento de 412 (LWW).
  - Backoff exponencial com jitter; tempo máximo configurável.
- Estado de sincronização:
  - Persistir `sync_state` por `grid_id` (último `since`, `version`).
  - Estratégia de reprocessamento em falhas de rede.
- Testes:
  - Mocks de HTTP e validação de mapeamento JSON ↔ modelos locais.

### Frontend (Flutter)

- Tela de Configurações:
  - `server_url`, `email`, `password`, botão “Testar Conexão”.
  - Armazenar tokens de forma segura (keychain/arquivo protegido).
- Indicadores de Sync:
  - Última sincronização, contador de conflitos (412), ação “Sincronizar agora”.

### Infra/Observabilidade

- Logs e diagnóstico:
  - `loguru` no backend; `tracing`/`env_logger` no provider Rust.
  - Comandos `uv run task logs-docker` (ambiente Docker) e scripts locais.
- Real-time (opcional pós-MVP):
  - SSE/WebSocket para mudanças de `rows` por `grid_id`.
- Testes ponta-a-ponta:
  - Preferir `uv run task test-docker` para a suíte completa.
  - Fallback local quando necessário com filtros de coleta.

## Sequência Recomendada (Execução)

1) Backend DRF + JWT → endpoints `auth`, `workspaces`, `grids`, `rows` com `If-Match`.
2) Provider Rust → `login/refresh`, `pull_rows/push_rows`, persistir `sync_state`.
3) Flutter UI → tela de configurações + indicadores de sincronização.
4) Observabilidade + testes E2E → logs, métricas básicas e cobertura.

## Definition of Done por Etapa

- Backend: todos endpoints ativos com testes de integração; conflito retorna 412; cobertura ≥ 80%.
- Provider: sincronização pull/push funcionando contra backend; tratamento de erro confiável.
- Flutter: configuração persistida e conexão testável; feedback claro ao usuário.
- Observabilidade: logs úteis e comandos de diagnóstico; documentação atualizada.

## Comandos de Validação

- Local (rápido, sem Docker):
  - `uv run pytest -v -o addopts='' --ignore=tests/app/notion_sync tests src/smart_core_assistant_painel/app/ui`
- Preferencial (padrão do projeto):
  - `uv run task test-docker`
- Migrações:
  - `uv run task makemigrations` e `uv run task migrate`

## Variáveis de Ambiente (Adapter)

- `APPFLOWY_ADAPTER_BASE_URL`, `APPFLOWY_ADAPTER_WORKSPACE_ID`, `APPFLOWY_ADAPTER_GRID_ID`
- `JWT_ACCESS_EXPIRES_MIN`, `JWT_REFRESH_EXPIRES_MIN`
- Documentar em `.env.example` (sem valores).

## Critérios de Aceite (MVP)

- CRUD do Grid Atendimentos sincronizando com Django.
- Offline-first (SQLite) e sincronização posterior sem perda.
- JWT curto + refresh funcional no Desktop.
- Logs estruturados com correlação por `ticket_id`.
- Cobertura ≥ 80% e CI verde.

## Observações

- Escopo MVI: focar no Grid de Atendimentos.
- Evolução para CRDT apenas se necessário.
- Zero segredos em código; `.env.example` atualizado.
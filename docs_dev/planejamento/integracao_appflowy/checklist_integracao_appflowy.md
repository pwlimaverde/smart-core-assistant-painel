# Checklist — Integração AppFlowy

## Status Geral

- Fase 1 concluída (modelos e sinais).
- Fase 2 concluída (DRF + JWT + CRUD + If-Match).
- Fase 3 em execução (Provider Rust: login/refresh, pull/push, sync).
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

- v DRF + SimpleJWT adicionados ao projeto e configurados em `settings`.
- v Endpoints de autenticação:
  - `POST /api/appflowy_adapter/auth/login/`
  - `POST /api/appflowy_adapter/auth/refresh/`
- v Endpoints do adapter ativos:
  - `GET /workspaces/`, `GET /grids/{grid_id}/schema/`
  - `GET/POST /grids/{grid_id}/rows/`
  - `PUT/DELETE /grids/{grid_id}/rows/{row_id}/`
- v Controle de versão com `If-Match` e retorno `412` em conflito.
- v `.env.example` atualizado com variáveis do adapter e JWT.
- v `.env` local (ignorado pelo Git) com base URL e credenciais dev.
- v Provider Rust (`django_sync_provider`):
  - Dependências: `reqwest`, `directories`, `chrono`, `dotenvy`.
  - Autenticação JWT: `login_from_env` e `auth_refresh`.
  - `pull_rows(since)` e `push_rows` com `If-Match`.
  - Persistência de `sync_state` por `grid_id` em arquivo no SO.
  - Credenciais lidas via `.env`; tokens mantidos apenas em memória.
  - README atualizado com seção de Segurança e variáveis esperadas.
\
## Entregas Concluídas (Frontend Flutter)
\
- v Tela de Configurações (Django Adapter): `server_url`, `username`,
  `password` e botão “Testar Conexão”.
- v Internacionalização da UI com `LocaleKeys.tr()` e assets de
  traduções adicionados: `assets/translations/en-US.json` e
  `assets/translations/pt-BR.json`.
- v Ajuste de assets: criação dos diretórios `assets/flowy_icons/*`
  para eliminar erros de build.

## Em Execução

- Testes de integração e cobertura ≥ 80% (adapter e sinais).
- Robustez do provider Rust (backoff/jitter, tratamento de 4xx/5xx).
- Resolução automática de `workspace/grid` por nome (ex.: "Atendimentos").
- Planejamento de SSE/WebSocket para mudanças (pós-MVP).

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
  - `login/refresh` com tokens apenas em memória (MVP).
  - Persistência de tokens opcional via armazenamento seguro do SO
    (ex.: DPAPI no Windows) — futura tarefa.
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
\
## Bloqueios e Mitigações (conhecidos)
\
- Build Web (Chrome): erro “Only JS interop members may be 'external'”
  por dependências que usam `win32`. Mitigação: executar no Windows
  desktop ou isolar APIs de desktop via imports condicionais/stubs.
\
## Validação Flutter
\
- Windows desktop:
  - Pré-requisitos: Visual Studio Build Tools (C++), MSVC, CMake,
    Windows SDK. Validar `flutter doctor -v`.
  - Executar: `flutter run -d windows`.
- Web (opcional): somente após isolar `win32` com stubs; `flutter run -d chrome`.
\
## Definition of Done (Flutter UI)
\
- Configurações persistem e teste de conexão retorna sucesso/erros
  com mensagens localizadas.
- Indicadores básicos de sincronização exibidos.
- Sem erros de assets; i18n funcional para `pt-BR` e `en-US`.

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
- `APPFLOWY_ADAPTER_USERNAME`, `APPFLOWY_ADAPTER_PASSWORD`
- `JWT_ACCESS_EXPIRES_MIN`, `JWT_REFRESH_EXPIRES_MIN`
- Documentar em `.env.example` (sem valores).

## Critérios de Aceite (MVP)

- CRUD do Grid Atendimentos sincronizando com Django.
- Offline-first (SQLite) e sincronização posterior sem perda.
- JWT curto + refresh funcional no Desktop.
- Logs estruturados com correlação por `ticket_id`.
- Cobertura ≥ 80% e CI verde.

## Cronograma Detalhado (Próximas Etapas)

- Dia 1–2 (Backend/Tests):
  - Escrever testes de integração para `auth`, `workspaces`, `grids`,
    `rows` (CRUD) e conflitos `If-Match`.
  - Validar cobertura ≥ 80% via `uv run task test-docker`.
  - Ajustes finos nos serializers e validações de payload.

- Dia 3 (Provider Rust — Robustez):
  - Implementar backoff exponencial com jitter nas chamadas HTTP.
  - Tratamento de erros para 401 (refresh) e 412 (re-pull e merge LWW).
  - Resolver `workspace/grid` automaticamente por nome quando IDs
    não estiverem definidos no `.env`.

- Dia 4 (Provider Rust — Segurança opcional):
  - Prototipar módulo de persistência segura de tokens usando DPAPI
    (Windows) e chave do usuário.
  - Feature flag para ativar/desativar persistência.

- Dia 5–6 (Flutter UI — Configurações):
  - Tela de configurações (`server_url`, `email`, `password`).
  - Botão “Testar Conexão” e indicadores de sincronização básica.
  - Integração com provider via FFI ou ponte existente.

- Dia 7 (E2E e Observabilidade):
  - Cenários ponta-a-ponta: criação/edição/remoção e conflitos.
  - Logs estruturados com correlação por `ticket_id`.
  - Ajustes finais de desempenho e paginação, se necessário.

- Dia 8–9 (Estabilização/Docs):
  - Revisar documentação (`README`, `integracao_appflowy.md`).
  - Scripts de diagnóstico e checklist de release.
  - Preparar pacote/artefatos para teste interno em Windows.

- Dia 10 (Piloto):
  - Teste com usuários internos, coleta de feedback.
  - Correções rápidas e planejamento do próximo ciclo.

## Observações

- Escopo MVI: focar no Grid de Atendimentos.
- Evolução para CRDT apenas se necessário.
- Zero segredos em código; `.env.example` atualizado.
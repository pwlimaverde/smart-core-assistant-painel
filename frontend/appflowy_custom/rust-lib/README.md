# Rust Lib — Custom Provider

Este diretório abrigará crates Rust próprios para integrar o AppFlowy
com o servidor Django como fonte de verdade.

## Planejado

- `django_sync_provider/` — Implementa um provider de sincronização
  remoto (HTTP/JSON via `reqwest`) com suporte a JWT, backoff e
  idempotência.
- `ffi_adapter/` (opcional) — Camada FFI para expor funções ao Flutter,
  caso necessário.

## Contratos (resumo)

- Trait `RemoteSync` com métodos:
  - `push_rows(rows: Vec<RowPatch>) -> Result<()>`
  - `pull_rows(since: DateTime) -> Result<Vec<RowDelta>>`
  - `subscribe_changes(grid_id: Uuid) -> Stream<RowDelta>`

## Observações

- Reutilizar padrões e tipos de `flowy-sqlite` quando possível.
- Respeitar versionamento (`version`) e idempotência (`ticket_id`).
- Logs estruturados com `log`/`tracing` (compatível com `loguru` no
  Django para correlação de `ticket_id`).
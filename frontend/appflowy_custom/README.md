# AppFlowy Custom (Vendor) — Monorepo

Este diretório contém o código do App Windows (Flutter) e o backend
local (Rust) do AppFlowy, incluído como vendor para permitir
customizações profundas e integração direta com o servidor Django.

## Estrutura

- `vendor/AppFlowy/` — Repositório vendor do AppFlowy
  (`https://github.com/pwlimaverde/AppFlowy`) clonado com `--depth 1`.
- `rust-lib/` — Espaço para crates Rust próprios (ex.:
  `django_sync_provider`) que implementarão o provedor de sincronização
  com o Django.

Rationale: manter controle total sobre UI/fluxos (Flutter) e backend
local (Rust), sem depender do AppFlowy Cloud, seguindo o plano em
`docs_dev/planejamento/integracao_appflowy/integracao_appflowy.md`.

## Build (Windows — orientação geral)

Pré-requisitos:
- Flutter (stable), SDK configurado para Windows Desktop.
- Rust (stable) toolchain MSVC e Visual Studio Build Tools (C++).

Passos (referência rápida):
1. `cd vendor/AppFlowy/frontend/appflowy_flutter`
2. `flutter config --enable-windows-desktop`
3. `flutter pub get`
4. `flutter build windows`

Notas:
- O AppFlowy utiliza crates Rust em `vendor/AppFlowy/frontend/rust-lib`.
  A integração com crates custom será feita em `rust-lib/` deste
  monorepo, conectando via FFI e/ou implementando o trait de sync.
- Ajustes de build podem exigir configuração adicional (PATH do Rust,
  toolchain, etc.). Consulte o `README.md` do vendor.

## Customização e Sincronização

- O objetivo é implementar um `DjangoSyncProvider` em Rust para
  sincronizar o Grid de Atendimentos com o servidor Django local.
- UI de configurações (Flutter) permitirá definir `server_url` e
  credenciais (JWT), conforme o plano.
- Offline-first permanece via `SQLite` local (Diesel), com política LWW
  inicial e evolução futura para CRDT, se necessário.

## Licença

O AppFlowy é distribuído sob **AGPLv3**. Qualquer modificação e
redistribuição deve respeitar essa licença. Consulte `vendor/AppFlowy/
LICENSE` para detalhes.
# Integração AppFlowy — Estudo de Viabilidade e Plano

## Objetivo desta versão

Detalhar como integrar o AppFlowy Desktop (Windows) diretamente com um
servidor Django local, sem depender do AppFlowy Cloud, utilizando um
adaptador de sincronização customizado no AppFlowy e uma API dedicada no
servidor Django.

## Contexto e Viabilidade

- AppFlowy Desktop usa `Rust` no backend e `Flutter` no frontend, com
  armazenamento local em `SQLite` via `Diesel` (crate `flowy-sqlite`).
  Referência: Docs de banco (SQLite/Diesel).
- O AppFlowy Cloud provê backend oficial com `Postgres/Redis/Minio` e
  autenticação `GoTrue`, além de endpoints e eventos de sincronização.
- Para sincronizar diretamente com Django, é necessário criar um
  "provedor de sincronização" alternativo no AppFlowy Desktop que se
  comunique com a API do Django em vez do Cloud.

Conclusão: Tecnicamente viável, porém envolve customização do AppFlowy
Desktop (Rust/Flutter) e a construção de uma API estável e segura em
Django. Recomenda-se começar com um escopo limitado (apenas Grid de
Atendimentos).

## Arquitetura Proposta

- AppFlowy Desktop (Windows):
  - Backend Rust continua usando `SQLite` local para offline-first.
  - Novo `DjangoSyncProvider` (Rust) implementa chamadas HTTP/JSON a
    um servidor Django.
  - UI adiciona configurações de servidor e credenciais.

- Servidor Django (local):
  - App `appflowy_adapter` com API REST (DRF) para operações do Grid:
    listar/criar/atualizar/excluir linhas e metadados.
  - Autenticação JWT (ex.: `djangorestframework-simplejwt`).
  - Logs estruturados com `loguru` e ferramentas de console com `rich`.
  - Banco Postgres (opcional) como fonte de verdade para Atendimentos.

- Sincronização (pull/push):
  - Desktop cria/edita em `SQLite` e envia `patches` para Django.
  - Desktop puxa atualizações do servidor por intervalos, ou via
    SSE/WebSocket para near real-time.
  - Versão/ETag por linha para resolver conflitos (last-write-wins
    inicialmente; evoluir para CRDT conforme necessidade).

## Estrutura de Pastas (Monorepo com Vendor)

- `src/smart_core_assistant_painel/` — Django (fonte de verdade, APIs, sinais, serviços).
- `frontend/appflowy_custom/` — App Windows (Flutter) e backend local (Rust/FFI) do AppFlowy adaptado.
- `frontend/appflowy_custom/rust-lib/` — crates Rust (FFI, sync provider, sqlite).
- `docker/` — compose e configs de desenvolvimento (Django + Postgres/Redis, se necessário).
- `docs_dev/` — documentação técnica, planos e decisões.

Rationale: evita dependência do AppFlowy Cloud, dá controle total do ciclo de sincronização e permite evoluir UI/fluxos sob demanda.

## Endpoints Django (mínimo viável)

- Autenticação:
  - `POST /auth/login` → retorna JWT.
  - `POST /auth/refresh` → renova JWT.

- Metadados de workspace/grid:
  - `GET /workspaces` → lista.
  - `GET /grids/{grid_id}` → esquema e colunas.

- Dados (Grid "Atendimentos"):
  - `GET /grids/{grid_id}/rows?since={timestamp}` → delta incremental.
  - `POST /grids/{grid_id}/rows` → criar linha.
  - `PUT /grids/{grid_id}/rows/{row_id}` → atualizar linha (If-Match:
    `version`).
  - `DELETE /grids/{grid_id}/rows/{row_id}` → remover linha.

- Eventos (opcional para real-time):
  - `GET /grids/{grid_id}/events` (SSE/WebSocket) → mudanças.

## Modelo de Dados (sugerido)

- Linha do atendimento:
  - `row_id: UUID`
  - `ticket_id: str` (chave idempotente)
  - `received_at: datetime`
  - `name: str`
  - `channel: str` (ex.: whatsapp)
  - `status: str` (ex.: open, pending, closed)
  - `priority: str` (ex.: low, medium, high)
  - `assigned_to: str`
  - `tags: list[str]`
  - `last_message: str`
  - `sla_due: datetime | null`
  - `version: int` (incremental)
  - `updated_at: datetime`

## Alterações no AppFlowy Desktop

- Crate de sincronização (Rust):
  - Definir trait `RemoteSync` com métodos: `push_rows`, `pull_rows`,
    `subscribe_changes`.
  - Implementar `DjangoSyncProvider` usando `reqwest` (HTTP/JSON) e
    suporte a JWT.

- Injeção de dependência:
  - Onde hoje existe client para Cloud, registrar o provider `Django`.
  - Configurar via UI (Flutter): `server_url`, `email`, `password`.

- Persistência local:
  - Manter `flowy-sqlite` para offline-first.
  - Guardar `sync_state` por grid (último `since`, `version`).

## Implementação no Django

- App `appflowy_adapter`:
  - Serializers e viewsets para `Row` e metadados.
  - Autenticação JWT e permissões mínimas.
  - Idempotência por `ticket_id` na criação.
  - Conflito: checar `version` em atualização (`If-Match`).
  - Logs com `loguru` e comandos de manutenção com `rich`.

- Sinais do Django (existentes do seu domínio):
  - `post_save`/`post_delete` dos modelos de Atendimento atualizam a
    tabela do Grid (fonte de verdade no servidor), sem necessidade de
    chamar a API (mesmo processo).

## Segurança

- Segredos apenas em `.env` e documentados em `.env.example`.
- JWT com expiração curta e `refresh` seguro.
  - Rate-limit básico e verificação de payloads.

## Testes

- Testes unitários e de integração para o `appflowy_adapter` (DRF).
- Testes de cliente (mockando endpoints) para o provider Django.
  - Cobertura mínima 80%. Rodar via `uv run task test-docker`.

## Docker e Execução Local

- `docker-compose` para Django + Postgres + Redis (se necessário).
- AppFlowy Desktop configurado para `server_url` local (ex.: `http://localhost:8000`).
- Opcional: Nginx reverso e certificados.

## Riscos e Mitigações

- Manutenção do fork do AppFlowy: acompanhar upstream e isolar mudanças
  por feature flags.
- Conflitos de sincronização: iniciar com last-write-wins, evoluir para
  CRDT conforme necessidade.
  - Performance: implementar `bulk` operations e paginação.

## Roadmap (Estimativa)

- Fork + Provider Django no AppFlowy: 2–4 dias.
- API Django (MVP Grid Atendimentos): 1–2 dias.
- Autenticação e UI de configurações: 1 dia.
- Testes e observabilidade: 1–2 dias.
  - Piloto e ajustes: 1–2 semanas.

## Próximos Passos

1. Criar o app `appflowy_adapter` no Django com endpoints mínimos.
2. Forcar o AppFlowy Desktop e adicionar o `DjangoSyncProvider`.
3. Construir a tela de configurações (URL/credenciais) no AppFlowy.
  4. Validar ponta-a-ponta com um grid real de Atendimentos.

### Fase 0.1 — Bootstrap do appflowy_adapter (executado)

- Estrutura inicial criada para o app Django `appflowy_adapter` com:
  - Endpoints mínimos sob `GET /api/appflowy_adapter/health/` (saúde),
    `GET /api/appflowy_adapter/workspaces/`, `GET /api/appflowy_adapter/grids/{grid_id}/`,
    e rotas básicas de `rows` (list/create/update/delete) retornando JSON estático.
  - Tipos/DTOs em `types.py` com `Row`, `RowPatch` e `RowDelta`.
  - Logs com `loguru` nos endpoints (placeholders).
  - Registro de URLs em `ui.core.urls` sob o prefixo `/api/appflowy_adapter/`.

- Crate Rust `django_sync_provider` iniciado em `frontend/appflowy_custom/rust-lib/` com:
  - Trait `RemoteSync` (push/pull/subscribe) e struct `DjangoSyncProvider` com métodos stub.
  - Dependências base (serde/serde_json) e estrutura pronta para evoluir com `reqwest`.

Próximos incrementos:
- Implementar autenticação JWT real e validação de payloads nos endpoints.
- Persistir dados em modelos do Django e sinais para o Grid.
- Conectar o provider Rust ao AppFlowy (vendor) e construir tela de configurações.

## Referências

- AppFlowy Desktop — Database (SQLite/Diesel):
  https://docs.appflowy.io/docs/documentation/software-contributions/architecture/backend/database
- AppFlowy Cloud — Arquitetura:
  https://docs.appflowy.io/docs/documentation/appflowy-cloud/architecture

---

## Plano de Execução — MVI (Versão Inicial Mínima)

- Objetivo: entregar um App Windows custom que sincroniza um Grid de Atendimentos com o Django local, com operações básicas (listar, criar, editar, excluir), offline-first, LWW.

- Escopo MVI:
  - UI: Grid de Atendimentos, filtros simples e edição inline.
  - Sync: pull delta (`since`), push patch batch; LWW com `version`.
  - Segurança: JWT curto + refresh; sem multi-tenant no MVI.
  - Observabilidade: logs correlacionados por `ticket_id` em Django.

- Critérios de Aceite:
  - App Windows conecta ao Django com credenciais e sincroniza corretamente.
  - CRUD no App Windows reflete no Django e vice-versa.
  - Offline: edições locais são persistidas em SQLite e sincronizam quando há rede (sem perda de dados).
  - Testes backend com cobertura ≥ 80% (`uv run task test-docker`).
  - Sem segredos em código; `.env.example` atualizado.

## Pré-requisitos (Windows/Docker)

- Windows 10/11 com PowerShell e WSL2 (opcional para Docker).
- Docker Desktop com suporte a Windows containers (ou Linux via WSL2).
- Flutter (stable), Android SDK opcional (apenas Windows Desktop alvo).
- Rust (stable), toolchain MSVC, Visual Studio Build Tools (C++), `cargo`.
- Python 3.11+ e `uv` instalado; `uv sync --dev` para deps de dev.

## Variáveis de Ambiente (.env.example)

- Servidor Django:
  - `APPFLOWY_ADAPTER_BASE_URL`
  - `APPFLOWY_ADAPTER_JWT_AUD`
  - `APPFLOWY_ADAPTER_WORKSPACE_ID`
  - `APPFLOWY_ADAPTER_GRID_ID`
  - `APPFLOWY_ADAPTER_CLIENT_ID` (se necessário)

- Segurança:
  - `DJANGO_SECRET_KEY`
  - `JWT_ACCESS_EXPIRES_MIN`
  - `JWT_REFRESH_EXPIRES_MIN`

- Banco:
  - `DATABASE_URL` (Postgres ou SQLite conforme ambiente)

Documentar no `.env.example` sem valores, seguindo “Zero Secrets”.

## Backlog Inicial (tarefas)

- Django
  - Criar app `appflowy_adapter` (DRF + JWT + endpoints mínimos).
  - Modelos/serializers com `version` e idempotência por `ticket_id`.
  - Sinais dos modelos de Atendimento alimentando a tabela do Grid.
  - Testes unitários e de integração (≥ 80%).

- App Windows
  - Vendor do AppFlowy em `frontend/appflowy_custom`.
  - Implementar `DjangoSyncProvider` (Rust, `reqwest`, JWT, backoff).
  - Tela de configurações (Flutter) e Grid básico.
  - Persistência local (SQLite) e estado de sync por grid.

- Infra/DevEx
  - `docker-compose` para Django + banco.
  - Scripts de build (PowerShell) para Flutter e Rust.
  - Linter/type-check (`ruff`, `mypy`) e tasks (`uv run task`).

## Entregáveis

- App Windows executável para ambiente interno (dev/teste).
- API Django funcional com documentação e testes.
- Documentação de uso e configuração (README, `.env.example`).

## Cronograma Sugerido (10 dias úteis)

- Dia 1–2: API Django (MVP) + testes + compose.
- Dia 3–5: Vendor AppFlowy + `DjangoSyncProvider` base + UI de configurações.
- Dia 6–7: Grid CRUD + sincronização pull/push + LWW.
- Dia 8: Testes e observabilidade.
- Dia 9–10: Piloto, ajustes e estabilização.



## Visão Geral

Você utiliza hoje o `notion_sync` para integrar os atendimentos
ao Notion (API) e usá-lo como frontend de gestão. A proposta é
substituir o Notion pelo AppFlowy, rodando os dois sistemas no
mesmo servidor (Docker) e enviar os dados diretamente para o
backend do AppFlowy, de preferência via banco de dados, usando
os sinais do Django no fluxo do webhook do WhatsApp.

Este documento avalia a viabilidade técnica e propõe um plano de
implementação.

## Arquitetura AppFlowy (resumo)

- AppFlowy Desktop (native):
  - Usa `Rust` no backend e `Flutter` no frontend.
  - Armazena dados localmente com `SQLite` e `Diesel` como ORM
    (crate `flowy-sqlite`).
    Referência: [Docs — Database (SQLite/Diesel)][ref1].

- AppFlowy Cloud (self-host):
  - Serviços core em `Rust` (AppFlowy Cloud).
  - Dependências: `Postgres` (banco principal), `Redis` (cache),
    `Minio/S3` (arquivos) e `GoTrue` (autenticação). O cliente
    nativo se comunica com esses serviços.
    Referência: [Docs — Cloud Architecture][ref2].

Conclusão: Escrever diretamente em `Postgres` só é aplicável ao
AppFlowy Cloud. O AppFlowy Desktop usa `SQLite` local via FFI e
não refletirá gravações em `Postgres`.

## Hipóteses de Integração

1. Escrita direta no Postgres do AppFlowy Cloud:
   - Possível, mas exige seguir o esquema e invariantes de dados
     do Cloud, além de considerar cache (`Redis`) e arquivos
     (`Minio/S3`). Mudanças diretas podem não disparar eventos
     esperados para atualização em tempo real no cliente.

2. Uso de API/serviço do AppFlowy Cloud:
   - Preferível, se disponível, pois preserva regras de negócio,
     cache e consistência. Autenticação via `GoTrue` com JWT.

3. Conector dedicado usando crates internos (Rust):
   - Construir um microserviço que utilize as mesmas crates do
     Cloud para inserir registros de forma segura.
   - Mais complexo, porém robusto e evolutivo.

## Estudo de Viabilidade

### Técnica

- Desktop local (SQLite): gravação direta em Postgres não se
  aplica. O cliente nativo conversa com o backend via FFI usando
  o banco local.
- Cloud (Postgres): viável. Contudo, escrever diretamente no
  banco pode burlar validações, índices e eventos em memória.
- Real-time: atualizações podem depender de canais internos ou
  re-sync periódico. Sem garantir eventos, o cliente pode não
  refletir imediatamente as mudanças.

### Operacional

- É possível rodar AppFlowy Cloud e o painel Django no mesmo
  host com Docker (Windows compatível). O AppFlowy Cloud depende
  de `Postgres`, `Redis`, `Minio` e `GoTrue` devidamente
  configurados.

### Segurança

- Autenticação de usuários do AppFlowy via `GoTrue` (JWT).
- Evitar escrever diretamente com credenciais privilegiadas sem
  camadas de validação. Preferir integração pelo serviço quando
  possível.

### Conclusão de Viabilidade

- Sim, é possível integrar gravando diretamente no Postgres do
  AppFlowy Cloud, mas é **não recomendado** como caminho padrão,
  devido ao risco de inconsistência e quebra de contratos
  internos. O caminho recomendado é **via serviço/API do Cloud**
  (quando disponível) ou via **conector dedicado** que reutilize
  as crates internas do AppFlowy.

## Estratégia Recomendada

1. Adotar AppFlowy Cloud self-host para fornecer o backend
   oficial (Postgres/Redis/Minio/GoTrue).
2. Configurar o AppFlowy Desktop para autenticar no Cloud.
3. Implementar um adaptador de sincronização no painel (Django)
   que, acionado por sinais (`post_save`/`post_delete`), envia os
   dados ao AppFlowy Cloud:
   - Preferência: chamadas ao serviço do Cloud (HTTP/gRPC), com
     JWT do `GoTrue`.
   - Alternativa controlada: escrita direta no Postgres + rotina
     de invalidação/refresh, ciente de riscos.

## Plano de Implementação

### Fase 0 — Preparação

- Definir quais entidades dos atendimentos serão exibidas no
  AppFlowy (Grid/Tabela principal) e o mapeamento de colunas.
- Atualizar `.env.example` do painel com variáveis do Cloud
  (sem segredos), documentando chaves requeridas:
  - `APPFLOWY_CLOUD_URL`
  - `APPFLOWY_GOTRUE_URL`
  - `APPFLOWY_GOTRUE_JWT_AUD`
  - `APPFLOWY_GOTRUE_SERVICE_ROLE` (se aplicável)
  - `APPFLOWY_CLOUD_WORKSPACE_ID`

### Fase 1 — Infraestrutura Docker

- Criar um `docker-compose` com os serviços:
  - `postgres` (persistência)
  - `redis` (cache/sessões)
  - `minio` (arquivos)
  - `gotrue` (autenticação)
  - `appflowy-cloud` (serviço principal)
- Expor `web` do Cloud e realizar `health-check`.
  Referência de dependências: [Docs — Cloud Architecture][ref2].

### Fase 2 — Modelagem de Dados (Grid)

- Definir a "Tabela de Atendimentos" no AppFlowy como um Grid:
  - Colunas sugeridas: `ticket_id`, `received_at`, `name`,
    `channel`, `status`, `priority`, `assigned_to`, `tags`,
    `last_message`, `sla_due`.
- Criar workspace/page e o Grid inicial via UI/Cloud.
- Obter IDs (workspace/page/grid) necessários na integração.

### Fase 3 — Sincronização via Sinais do Django

- Criar módulo `appflowy_sync` no painel com:
  - `AppFlowySyncService` (camada de aplicação) com `loguru` e
    `rich` para logs/saídas estruturadas.
  - Funções:
    - `create_or_update_row(atendimento: Atendimento) -> None`
    - `delete_row(atendimento_id: UUID) -> None`
- Estratégia Preferencial (Serviço Cloud):
  - Autenticar via `GoTrue` e enviar operações ao Cloud.
  - Garantir consistência e eventos para o cliente.
- Alternativa (Escrita Postgres Direta):
  - Usar `psycopg` para gravar nas tabelas do Grid.
  - Implementar transações e checagens de integridade.
  - Forçar revalidação/refresh no cliente (quando aplicável).
  - Documentar que futuras migrações do Cloud podem quebrar a
    integração.

### Fase 4 — Observabilidade e Testes

- Logs detalhados com `loguru` (correlações por `ticket_id`).
- CLI de diagnóstico com `rich` para inspeção de filas/erros.
- Tests (`pytest`) cobrindo:
  - Mapeamento de campos e transformação.
  - Envio ao Cloud (mock/stub) e/ou escrita no Postgres.
  - Tratamento de falhas e reprocessamento.
- Executar testes sempre via `uv run task test-docker`.

### Fase 5 — Segurança e Hardening

- Segredos exclusivamente em `.env` (nunca em código).
- Políticas de permissões mínimas no `GoTrue`/Cloud.
- Criptografia em repouso para `Postgres` e `Minio` (se possível).
- Auditoria de alterações e fallback seguro.

### Fase 6 — Rollout e Fallback

- Habilitar o AppFlowy para um conjunto piloto de usuários.
- Monitorar performance e consistência por 2 semanas.
- Ter plano de rollback para Notion caso necessário.

## Cronograma & Esforço (Estimativa)

- Infra Cloud (Docker + Config): 1–2 dias.
- Modelagem Grid e mapeamento: 0,5 dia.
- Serviço de sincronização (API Cloud): 1–2 dias.
- Alternativa Postgres direto (se necessário): +1 dia.
- Testes, observabilidade e ajustes: 1–2 dias.

## Riscos e Mitigações

- Mudanças de esquema do AppFlowy Cloud: monitorar releases e
  preferir a integração via serviço/API.
- Inconsistência de cache/eventos: evitar escrita direta; se
  usada, agendar "refresh" no cliente e validar leitura.
- Autenticação/Autorização: centralizar no `GoTrue` e rotacionar
  segredos.
- Performance: usar `bulk` inserts e filas assíncronas quando
  necessário.

## Decisão Recomendada

1) Self-host do AppFlowy Cloud é o caminho correto para
   integração server-side e visualização no AppFlowy Desktop.
2) Implementar integração via serviço/API do Cloud e usar JWT
   do `GoTrue`. Manter escrita direta em Postgres apenas como
   fallback controlado e documentado.

## Referências

- [ref1] AppFlowy Docs — Database (SQLite/Diesel):
  https://docs.appflowy.io/docs/documentation/software-contributions/architecture/backend/database
- [ref2] AppFlowy Docs — Cloud Architecture:
  https://docs.appflowy.io/docs/documentation/appflowy-cloud/architecture
- Postgres em Cloud (exemplos e discussões):
  https://github.com/AppFlowy-IO/AppFlowy-Cloud/issues/198
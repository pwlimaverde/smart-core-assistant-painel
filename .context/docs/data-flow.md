---
status: unfilled
generated: 2026-01-15
---

# Data Flow & Integrations

Explain how data enters, moves through, and exits the system, including interactions with external services.

## Module Dependencies
- **src\smart_core_assistant_painel\app\trello_sync\api_urls.py/** → `src\smart_core_assistant_painel\app\trello_sync`
- **src\smart_core_assistant_painel\app\ui\usuarios\urls.py/** → `src\smart_core_assistant_painel\app\ui\usuarios`
- **src\smart_core_assistant_painel\app\ui\treinamento\urls.py/** → `src\smart_core_assistant_painel\app\ui\treinamento`
- **src\smart_core_assistant_painel\app\ui\core\urls.py/** → `src\smart_core_assistant_painel\app\ui\core`

## Service Layer
- [`TreinamentoService`](src\smart_core_assistant_painel\app\ui\treinamento\services.py#L13)
- [`WebhookProcessingService`](src\smart_core_assistant_painel\app\trello_sync\services\webhook_processing_service.py#L8)
- [`TicketSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\ticket_sync_service.py#L34)
- [`MemberSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\member_sync_service.py#L25)
- [`FlowSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\flow_sync_service.py#L24)
- [`TenantProvisioningService`](src\smart_core_assistant_painel\app\tenants\services\provisioning.py#L9)
- [`EvolutionWhatsAppService`](src\smart_core_assistant_painel\app\evolution_sync\services\evolution_api.py#L7)
- [`TestInMemoryUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_unifield_data_services_datasource.py#L65)
- [`TestTrelloUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_trello_adapter.py#L16)
- [`TestClicupUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_clicup_adapter.py#L16)
- [`TrelloUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\trello_adapter.py#L24)
- [`NotionUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\notion_adapter.py#L30)
- [`ClicupUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\clicup_adapter.py#L25)
- [`UnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\interface\unified_data_service.py#L14)

## High-level Flow

Summarize the primary pipeline from input to output. Reference diagrams or embed Mermaid definitions when available.

## Internal Movement

Describe how modules within `AGENTS.md`, `ambiente_cliente`, `ambiente_cliente_teste`, `bugs.txt`, `CHANGELOG.md`, `cspell.json`, `diagnostico_output.txt`, `diagnostico_result.txt`, `docker`, `docs`, `docs_dev`, `GEMINI.md`, `log_cluster.txt`, `log_langsmith.txt`, `log_ngrok.txt`, `log_servidor.txt`, `mkdocs.yml`, `openspec`, `pyproject.toml`, `pytest.ini`, `README.md`, `scripts`, `smartcore-landing`, `src`, `teste_debug`, `tests`, `trace.txt`, `uv.lock`, `verify_fix.py`, `WARP.md` collaborate (queues, events, RPC calls, shared databases).

## External Integrations

Document each integration with purpose, authentication, payload shapes, and retry strategy.

## Observability & Failure Modes

Describe metrics, traces, or logs that monitor the flow. Note backoff, dead-letter, or compensating actions when downstream systems fail.

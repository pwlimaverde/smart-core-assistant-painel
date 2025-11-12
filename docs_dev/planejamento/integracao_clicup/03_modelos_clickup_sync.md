# Modelos e Adapter `clickup_sync`

## Conceitos e Interfaces
- Adapter `ClickUpUnifiedDataService` com responsabilidades:
  - `create_folder(department)`: cria Folder no Space.
  - `create_list(flow, folder_id)`: cria List para fluxo.
  - `set_list_statuses(list_id, statuses)`: configura etapas do fluxo.
  - `ensure_custom_fields(list_id, fields)`: garante CF na List.
  - `create_task(list_id, payload)`: cria Atendimento.
  - `update_task(task_id, payload)`: atualiza Atendimento (inclui `status`).
  - `set_task_field(task_id, field_id, value)`: define CF.
  - `assign_member(task_id, member_id)`: gerencia responsáveis.
  - `register_webhook(team_id, url, events)`: registra Webhook.

## Mapeamento
- Departamento → Folder
- FluxoAtendimento → List
- EtapaFluxo → Status (por List)
- Atendimento → Task
- Atributos do Atendimento → Custom Fields

## Eventos (Webhooks)
- Receber e tratar: `taskCreated`, `taskUpdated`, `taskMoved`, mudanças de `status`.
- Persistir correlações (IDs locais ↔ IDs ClickUp).

## Observações de Implementação
- Reutilizar CF do Workspace quando cabível para economizar usos.
- Validar rate limit com retries exponenciais.
- Logar com `loguru` e saídas ricas com `rich` em scripts.
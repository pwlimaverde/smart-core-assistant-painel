# Modelos e Adapter `clickup_sync`

## Conceitos e Interfaces
- Adapter `ClickUpUnifiedDataService` com responsabilidades:
  - `create_folder(department)`: cria Folder no Space.
- `create_list(flow, folder_id)`: cria List para fluxo.
  (preferir incluir `statuses` na criação para personalizar por fluxo)
  - `set_list_statuses(list_id, statuses)`: configura etapas do fluxo
    (List statuses com tipo `open`/`done`/`closed`).
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

### Modelo `ClickupStatus`
- Persiste a correlação entre `EtapaFluxo` e o status da `List`.
- Campos principais:
  - `etapa_fluxo_id`: ID local da etapa.
  - `list_external_id`: ID externo da List (ClickUp).
  - `status_name`: nome do status na List.
  - `status_type`: `open`, `done` ou `closed`.
  - `color`: cor hex do status.
  - `order_index`: ordem do status na List.
- Chave única composta: (`etapa_fluxo_id`, `list_external_id`).

### Dinâmica de Mudança de Etapa
- Ao mudar a etapa do atendimento, o sistema consulta `ClickupStatus`
  usando (`etapa_fluxo_id`, `list_external_id`) para obter `status_name`.
- O `TicketSyncService` usa `status_name` ao montar o corpo de
  atualização/criação da Task para refletir o novo status.
- Caso não exista mapeamento, o sistema faz fallback para o nome
  da etapa, evitando bloqueios e permitindo continuidade.
- O `FlowSyncService` atualiza/persiste o mapeamento após definir
  os `statuses` na List e confirmar via `GET /list/{id}`.

### Remoção de Etapas
- Ao excluir uma `EtapaFluxo`, os mapeamentos `ClickupStatus` da etapa
  são removidos imediatamente.
- Em seguida, o sistema reconfigura os `statuses` da List do fluxo,
  removendo o status correspondente no ClickUp (via `PUT /list/{id}`)
  com a nova lista de statuses sem a etapa excluída.
- O mapeamento é limpo de órfãos após cada reconfiguração, garantindo
  consistência da base local.

## Eventos (Webhooks)
- Receber e tratar: `taskCreated`, `taskUpdated`, `taskMoved`, mudanças de `status`.
- Persistir correlações (IDs locais ↔ IDs ClickUp).

## Observações de Implementação
- Reutilizar CF do Workspace quando cabível para economizar usos.
- Validar rate limit com retries exponenciais.
- Logar com `loguru` e saídas ricas com `rich` em scripts.

## Exemplo de Payload de Statuses da List

```json
{
  "override_statuses": true,
  "statuses": [
    { "status": "Fila", "type": "open", "color": "#6B7280" },
    { "status": "Em Trabalho", "type": "done", "color": "#0EA5E9" },
    { "status": "Finalizado", "type": "closed", "color": "#22C55E" }
  ]
}
```

Notas:
- `type` deve ser um dentre `open`, `done` ou `closed`.
- Apenas um status `open` e um `closed` são permitidos.
- Use `done` para etapas intermediárias que permanecem abertas.
- A ordem da lista define a ordem visual no Board.
- `color` deve ser uma cor hex válida (ex.: `#6B7280`).
- Alguns workspaces exigem definir os `statuses` na criação da List
  para que a personalização seja aplicada. O `PUT /list/{id}` funciona
  como ajuste posterior idempotente.
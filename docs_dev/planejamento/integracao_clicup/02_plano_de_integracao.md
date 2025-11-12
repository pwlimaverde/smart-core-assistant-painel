# Plano de Integração com ClickUp

## Passos de Implementação
- Autenticação:
  - Usar `Authorization: Bearer <token>` em todas as requisições.
- Descoberta de Workspace e Space:
  - `GET /api/v2/team` para obter `team_id`.
  - (Opcional) `POST /api/v2/team/{team_id}/space` para criar o Space "ServiceDesk".
- Criação de Departamentos (Folder):
  - `POST /api/v2/space/{space_id}/folder` para cada Departamento.
- Criação de Fluxos (Lists):
  - `POST /api/v2/folder/{folder_id}/list` por FluxoAtendimento.
- Configuração de Etapas (Statuses):
  - `PUT /api/v2/list/{list_id}` incluindo `statuses` personalizados.
- Campos Personalizados (CF):
  - Workspace: `GET /api/v2/team/{team_id}/field` (listar) e reutilizar quando possível.
  - List: `GET/POST /api/v2/list/{list_id}/field` para anexar CF ao fluxo.
  - Task: `POST /api/v2/task/{task_id}/field/{field_id}` para definir valores.
- CRUD de Atendimentos:
  - `POST /api/v2/list/{list_id}/task`, `PUT /api/v2/task/{task_id}` (inclui `status`).
  - Anexos: `POST /api/v2/task/{task_id}/attachment`.
- Webhooks:
  - `POST /api/v2/team/{team_id}/webhook` (events: task create/update/move/status change).
  - Endpoint Django para processamento.

## Exemplo de Requisições
- Criar Folder (Departamento):
```
POST https://api.clickup.com/api/v2/space/{space_id}/folder
Content-Type: application/json
Authorization: Bearer <token>
{
  "name": "Atendimento Comercial"
}
```

- Criar List (FluxoAtendimento):
```
POST https://api.clickup.com/api/v2/folder/{folder_id}/list
Content-Type: application/json
Authorization: Bearer <token>
{
  "name": "Fluxo Atendimento WhatsApp"
}
```

- Configurar Status da List:
```
PUT https://api.clickup.com/api/v2/list/{list_id}
Content-Type: application/json
Authorization: Bearer <token>
{
  "statuses": [
    {"status": "Novo", "type": "open"},
    {"status": "Em atendimento", "type": "open"},
    {"status": "Aguardando cliente", "type": "open"},
    {"status": "Resolvido", "type": "closed"}
  ]
}
```

- Criar Task (Atendimento):
```
POST https://api.clickup.com/api/v2/list/{list_id}/task
Content-Type: application/json
Authorization: Bearer <token>
{
  "name": "Atendimento #1234",
  "status": "Novo",
  "assignees": [123456]
}
```

- Definir Custom Field na Task:
```
POST https://api.clickup.com/api/v2/task/{task_id}/field/{field_id}
Content-Type: application/json
Authorization: Bearer <token>
{
  "value": "Maria Silva"
}
```

## Testes e Qualidade
- Escrever testes `pytest` com tipagem completa e cobertura ≥80%.
- Rodar sempre em Docker: `uv run task test-docker`.
- Validar: criação de Folder/List/Task, atualização de status, CF set/get, webhook.
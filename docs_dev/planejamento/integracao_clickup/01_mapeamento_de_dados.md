# Mapeamento de Dados: Domínio → ClickUp

## Objetos de Domínio
- Departamento → Folder (em um Space específico do Workspace).
- FluxoAtendimento → List (dentro do Folder do Departamento).
- EtapaFluxo → Status da List (colunas no Board view).
- Atendimento → Task (pertence a uma List e possui `status`).

## Campos do Atendimento (Task)
- Principais atributos como Custom Fields:
  - `contact_name` (Text)
  - `contact_number` (Text)
  - `company` (Text)
  - `channel` (Dropdown; ex.: WhatsApp, Email, Phone)
  - `priority` (Dropdown; ex.: Low, Medium, High)
  - `sla_due` (Date)
  - `last_message_at` (Date)
  - `messages_summary` (Rich Text) — resumo das últimas mensagens
  - `has_attachments` (Checkbox)

## Hierarquia e Identificadores
- Workspace (`team_id`) → Space (`space_id`) → Folder (`folder_id`) → List (`list_id`) → Task (`task_id`).
- CF referenciados por `field_id` (escopo Workspace/List).

## Exemplo de Payload de Criação de Task
```json
{
  "name": "Atendimento #1234",
  "status": "Em atendimento",
  "assignees": [123456],
  "priority": 3,
  "due_date": 1734567890000,
  "custom_fields": [
    { "id": "field_contact_name", "value": "Maria Silva" },
    { "id": "field_contact_number", "value": "+55 11 99999-8888" },
    { "id": "field_company", "value": "Acme Ltda" },
    { "id": "field_channel", "value": "WhatsApp" },
    { "id": "field_messages_summary", "value": "Resumo das últimas mensagens..." }
  ]
}
```

## Regras de Negócio
- Cada Atendimento pertence a um Departamento (Folder), a um FluxoAtendimento (List) e a uma EtapaFluxo (Status).
- Mudança de EtapaFluxo = atualização do `status` da Task.
- CF devem ser anexados às Lists corretas para aparecerem nos Atendimentos.
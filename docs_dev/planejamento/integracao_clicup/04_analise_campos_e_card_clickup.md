# Análise de Campos e Card (Task) no ClickUp

## Conjunto de Campos Personalizados
- Essenciais:
  - `contact_name` (Text)
  - `contact_number` (Text)
  - `company` (Text)
  - `channel` (Dropdown: WhatsApp, Email, Phone, Web)
  - `priority` (Dropdown)
  - `sla_due` (Date)
  - `last_message_at` (Date)
  - `messages_summary` (Rich Text)
  - `has_attachments` (Checkbox)

## Boas Práticas
- Resumo de mensagens em `messages_summary` (Rich Text) e anexos na Task para históricos.
- Evitar CF redundantes; preferir CF globais (Workspace) quando aplicáveis.
- Padronizar nomes e tipos por fluxo.

## Limitações (Free Plan)
- ~60 usos de Custom Fields por Workspace (conta anexos de CF em listas).
- Monitorar consumo e consolidar CF.

## Exemplo de Definição de Valor
```
POST /api/v2/task/{task_id}/field/{field_id}
{
  "value": "Resumo das mensagens: ..."
}
```
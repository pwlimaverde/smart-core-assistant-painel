# Limitações de Statuses no ClickUp via API

Este documento descreve limitações observadas ao tentar definir
statuses personalizados em Lists do ClickUp usando a API v2.

## Resumo

- A criação de Lists (`POST /folder/{folder_id}/list`) não aceita
  definir statuses de tarefas no corpo da requisição.
- A atualização de uma List (`PUT /list/{list_id}`) aceita campos
  como `name`, `description`, `archived` e cor de `status`, mas
  nem sempre aplica um conjunto de `statuses` customizados.
- Por padrão, o ClickUp mantém "To do" e "Complete" para consistência
  do Workspace.

## Abordagem no Projeto

- Implementamos tentativa de atualização com `override_statuses: true`
  e `statuses: [...]` no serviço `FlowSyncService`.
- Após atualizar, validamos via `GET` os `statuses` da List.
- Se o servidor retornar apenas os padrões (2 itens), registramos
  um aviso nos logs indicando que a personalização pode não ter sido
  aplicada pela API.
- Persistimos o mapeamento Etapa ↔ Status no banco para manter
  consistência de nomes na atualização de tarefas.

## Recomendações

- Configure statuses personalizados diretamente no Space/Folder via UI
  do ClickUp quando desejar garantir aplicação global.
- Mantenha os nomes das Etapas coerentes com os nomes dos statuses
  no ClickUp para simplificar integrações.
- Use o comando de testes preferencial:
  `uv run task test-docker`.

## Observações

- Estas limitações foram verificadas na prática e podem variar com
  mudanças de API. Revise periodicamente a documentação oficial do
  ClickUp.
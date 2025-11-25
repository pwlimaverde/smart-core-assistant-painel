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

## Sincronização de Responsáveis (Assignees)

- Preferir o endpoint dedicado de assignees:
  - `POST /task/{task_id}/assignee` com corpo
    `{ "assignee": <user_id>, "unassign": <bool> }`.
- Em alguns ambientes, pode ocorrer `404 (Cannot POST ...)` ao
  chamar o endpoint acima, apesar de documentado. Nestes casos,
  aplicar fallback via:
  - `PUT /task/{task_id}` com corpo `{ "assignees": [<user_id>, ...] }`,
    que substitui a lista inteira de responsáveis.
- Tipagem: para `PUT`, alguns ambientes exigem IDs inteiros (não strings).
  Utilize sempre `user_id` como inteiro quando possível.
- Requisitos: o usuário deve ser membro da List onde a task reside.
  Membro apenas do Workspace pode não ser suficiente para receber
  atribuição.
- Boas práticas no projeto:
  - Após aplicar a alteração, consultar `GET /task/{task_id}` e
    comparar os IDs de `assignees` com o alvo desejado.
  - Padronizar um único `user_id`/e-mail por atendente nas automações
    para evitar ambiguidade de mapeamento.

### Comportamento implementado

- O adapter tenta primeiro `POST /task/{task_id}/assignee` para
  adicionar/remover individualmente.
- Se ocorrer `404`, aplica fallback único com `PUT /task/{task_id}`
  definindo a lista final.
- O método só é considerado bem-sucedido quando o `GET /task/{task_id}`
  retorna a lista aplicada igual ao alvo.

### Referência

- Endpoint de assignee (requer cabeçalho `Authorization`):
  - https://api.clickup.com/api/v2/task/86ad86g4a/assignee
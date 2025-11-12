# Relatório Final: Estratégia de Integração com ClickUp via `clickup_sync`

## Contexto e Objetivo
- Substituir o Trello por ClickUp mantendo automações, webhooks e campos personalizados.
- Modelo proposto: Workspace único → Space → Folder (Departamento) → List (FluxoAtendimento) → Status (EtapaFluxo) → Task (Atendimento).
- Cada Task representa um atendimento e armazena atributos principais em Custom Fields (mensagens, nome, número, empresa, etc.).

## Conclusão de Viabilidade
- Viável e recomendado. O modelo aproveita a hierarquia nativa do ClickUp:
  - Workspace (time) para a organização.
  - Space para agrupar operações (pode ser único, ex.: "ServiceDesk").
  - Folder por Departamento.
  - List por FluxoAtendimento dentro do Folder.
  - Status da List como EtapaFluxo (colunas no Board view).
  - Task como Atendimento com Custom Fields.
- A API `ClickUpV2Api` suporta criação/gestão de Folder, List, Task, status e Custom Fields, além de webhooks e anexos.
- Benefício: mais organizado que Trello, pois o Board é uma visualização da List, e os Status são controlados por List (por fluxo), com CF flexíveis por nível.

## Suporte da API (ClickUpV2Api) aos Requisitos
- Autenticação:
  - `Authorization: Bearer <token>` (Personal token ou OAuth).
- Descoberta de Workspaces (times):
  - `GET /api/v2/team` → listar Workspaces disponíveis.
  - `GET /api/v2/team/{team_id}/plan` → consultar plano (Free/paid).
- Space (se necessário programaticamente):
  - `POST /api/v2/team/{team_id}/space` → criar Space (opcional; pode ser criado via UI).
- Folder (Departamento):
  - `POST /api/v2/space/{space_id}/folder` → criar Folder no Space.
  - `GET /api/v2/space/{space_id}/folder` → listar Folders do Space.
- List (FluxoAtendimento):
  - `POST /api/v2/folder/{folder_id}/list` → criar List dentro do Folder.
  - `GET /api/v2/folder/{folder_id}/list` → listar Lists do Folder.
- Status (EtapaFluxo) por List:
  - `PUT /api/v2/list/{list_id}` → atualizar propriedades da List (inclui configuração de statuses personalizados).
  - Task muda de etapa via `status` no update da Task.
- Task (Atendimento):
  - `POST /api/v2/list/{list_id}/task` → criar Task.
  - `GET /api/v2/task/{task_id}` → obter Task.
  - `PUT /api/v2/task/{task_id}` → atualizar Task (inclui `status`).
  - Anexos: `POST /api/v2/task/{task_id}/attachment`.
- Custom Fields (campos personalizados):
  - Workspace-level: `GET /api/v2/team/{team_id}/field` → listar CF disponíveis no Workspace.
  - List-level: `GET /api/v2/list/{list_id}/field` / `POST /api/v2/list/{list_id}/field` → listar/adicionar CF à List.
  - Valor em Task: `POST /api/v2/task/{task_id}/field/{field_id}` → definir valor.
- Webhooks:
  - `POST /api/v2/team/{team_id}/webhook` → criar Webhook para eventos (task created/updated/moved, etc.).
  - Receberemos JSON via POST e processaremos no backend Django.

Observação: endpoints podem variar conforme plano/organização, mas a documentação pública atual suporta os fluxos acima. A abordagem é compatível com Windows e execução em Docker.

## Riscos e Mitigações
- Limite de Custom Fields (Free): até ~60 usos por Workspace (contagem por uso em listas). Mitigar padronizando CF essenciais e reutilizando CF no Workspace quando possível.
- Rate limit: ~100 req/min. Mitigar com filas e backoff.
- Status por List: precisa de padronização de nomes por fluxo. Mitigar com catálogo de etapas e automação de criação.
- Gestão de membros: permissões por Space/Folder/List. Mitigar com rotina de provisionamento e validação.

## Plano de POC (Windows/Docker)
- Preparação:
  - Obter `team_id` via `GET /api/v2/team`.
  - Criar Space "ServiceDesk" (UI ou `POST /team/{team_id}/space`).
  - Criar Folders por Departamento via `POST /space/{space_id}/folder`.
  - Criar Lists por FluxoAtendimento via `POST /folder/{folder_id}/list`.
  - Configurar Status por List via `PUT /list/{list_id}`.
- Campos Personalizados:
  - Definir CF no Workspace/List (nome, tipo: Text, Rich Text, Number, Date, Dropdown).
  - Anexar CF às Lists e validar via `GET /list/{list_id}/field`.
- CRUD de Atendimentos:
  - `POST /list/{list_id}/task` e atualização de `status` com `PUT /task/{task_id}`.
  - Definir CF da Task com `POST /task/{task_id}/field/{field_id}`.
  - Anexos e comentários quando necessário.
- Webhooks:
  - `POST /team/{team_id}/webhook` → eventos de criação/movimento/alteração de Task.
  - Endpoint Django para receber/processar.
- Testes (sempre em Docker):
  - `uv run task test-docker` com cenários: criação de Folder/List/Task, mudança de status, CF set/get, webhook end-to-end.

## Próximos Passos
- Confirmar conjunto de CF e nomenclatura de Status por fluxo.
- Implementar adapter `ClickUpUnifiedDataService` conforme modelos.
- Rodar POC end-to-end e documentar resultados.
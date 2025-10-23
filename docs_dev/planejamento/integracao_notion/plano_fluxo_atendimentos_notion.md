# Plano de Integração Bidirecional: Django ↔ Notion (Gestão de Atendimentos)

Este documento consolida a análise técnica e o plano de implementação para integrar os modelos Django com o Notion, cobrindo carga inicial de estrutura e dados, além de sincronização contínua e bidirecional. Referências consideradas: Notion API (versão 2025-09-03), boas práticas de clientes (`NotionClient`), camada de serviço/SDK (`NotionApi`) e guias de uso (`NotionGuides`).

## 1. Objetivos e Escopo
- Unificar dados de atendimento entre Django e Notion, mantendo consistência.
- Carga inicial: criar bases no Notion e carregar dados existentes do Django.
- Sincronização contínua: sinais do Django → Notion e polling do Notion → Django.
- Modelos alvo (inicial): `Attendance`, `Contact`, `Message`, `Department`.

## 2. Análise: NotionClient, NotionApi, NotionGuides
- `NotionClient` (wrapper HTTP):
  - Autenticação via `Bearer NOTION_API_KEY` (env var).
  - Endpoints principais: `databases`, `pages`, `blocks`, `search`.
  - Rate limit: projetar para ~3 req/s por integração; aplicar retry exponencial e backoff.
  - Erros: tratar 4xx/5xx com reclassificação (ex.: 409 conflito, 429 throttling).
- `NotionApi` (camada de serviço/SDK):
  - Métodos de alto nível com tipos e validações: `create_database`, `upsert_page`, `query_database`, `archive_page`.
  - Conversões de tipos entre Django ↔ Notion (Title, Rich Text, Select, Multi-Select, Date, Relation, Status, Checkbox, etc.).
  - Política de idempotência: `upsert_page` usando `notion_page_id` ou chaves naturais.
- `NotionGuides` (guias e melhores práticas):
  - Propriedade `Title` única por DB; usar campo de negócio (ex.: `protocol_number`).
  - Relacionamentos: `Relation` para FK/M2M; `Rollup` para agregações.
  - Controle de versão: manter `last_edited_time` do Notion e `updated_at` do Django.
  - Conflitos: decidir `last-writer-wins` com exceções de status críticos.

## 3. Arquitetura
- Camadas:
  - Cliente HTTP (`NotionClient`) com retry/backoff e logs (`loguru`).
  - Serviços (`NotionApi`): orquestram operações do Notion e mapeamento.
  - Mapeadores: funções de transformação entre modelos Django e propriedades Notion.
  - Sincronização (`SyncService`): coordena sinais (Django → Notion) e polling (Notion → Django).
- Config:
  - `configs/notion_schema.json`: definição de DBs e propriedades.
  - `configs/notion_objects_map.json`: relação modelo ↔ database e campos.
- Execução assíncrona: recomendar `Celery` + `celery beat` para jobs de polling.

## 4. Mapeamento de Modelos
- Chave técnica: adicionar `notion_page_id: CharField(null=True, unique=True)` em cada modelo sincronizado.
- Exemplos:
  - `Attendance` ↔ DB "Atendimentos":
    - `protocol_number` → `Title`
    - `status` → `Select`
    - `contact (FK)` → `Relation` (DB "Contatos")
    - `department (FK)` → `Relation` (DB "Departamentos")
    - `created_at/updated_at` → `Date`/metadados
  - `Contact` ↔ DB "Contatos": nome/telefone/email como `Rich Text`/`Phone`/`Email`.
  - `Message` ↔ DB "Mensagens": conteúdo `Rich Text`, data `Date`, relação com `Attendance`.

## 5. Carga Inicial (Estrutura e Dados)
- Estrutura (idempotente):
  - Ler `configs/notion_schema.json` e criar/atualizar DBs no Notion.
  - Persistir `database_id` por tipo (em cache/arquivo de config).
- Dados:
  - Percorrer registros Django e criar `pages` correspondentes no Notion.
  - Salvar `notion_page_id` no Django após criação.
- Comando sugerido: `uv run task setup_notion_databases` e `uv run task sync_all_to_notion`.

## 6. Sincronização Bidirecional
- Django → Notion (tempo real):
  - `post_save` e `post_delete` em modelos: acionar `SyncService`.
  - `upsert_page` com mapeamento; criar se `notion_page_id` ausente, senão atualizar.
- Notion → Django (polling):
  - Job periódico (ex.: 5 min): `query_database` por `last_edited_time` > `cursor`.
  - Aplicar transformações e atualizar/arquivar objetos Django conforme necessário.
- Conflitos e regras:
  - Estratégia padrão: `last-writer-wins` com resolução por timestamps.
  - Campos sensíveis (ex.: `status`): regras de prioridade configuráveis.

## 7. Observabilidade, Erros e Segurança
- Logs estruturados: `loguru` com contexto (modelo, `database_id`, `page_id`).
- Saída de terminal: `rich` para comandos de gestão.
- Alertas: contagem de falhas e circuito aberto para throttling.
- Segredos: `NOTION_API_KEY` via `python-decouple` e `.env`.

## 8. Testes e Qualidade
- Testes unitários dos mapeadores e `SyncService` (mocks HTTP).
- Testes de integração: cenários de carga inicial e conflitos.
- Cobertura mínima: 80%. Executar com `uv run task test-docker`.
- Lint/format/type-check: `uv run task format`, `lint`, `type-check`.

## 9. Cronograma e Entregáveis
- Semana 1: schema, mapeadores, comandos de estrutura, carga inicial.
- Semana 2: sinais Django, upsert, política de conflitos, logging.
- Semana 3: polling Notion → Django, testes integração, ajustes finais.

## 10. Próximos Passos
- Criar app `integrations.notion` com `NotionClient`, `NotionApi`, mapeadores e `SyncService`.
- Adicionar campo `notion_page_id` aos modelos-alvo e migrar.
- Implementar comandos: `setup_notion_databases`, `sync_all_to_notion`, `sync_from_notion`.
- Configurar `Celery` (opcional) para tarefas assíncronas.

# Plano de Reorganização do Fluxo de Atendimentos com Notion (API 2025-09-03)

## Objetivo
- Migrar o fluxo de atendimentos para ser gerenciado diretamente em um Data Source (antigo “database”) do Notion.
- Ao receber uma nova mensagem, criar automaticamente um atendimento (página) no Notion conectado.
- Configurar um webhook para receber atualizações do “quadro” (board) e sincronizar estados no painel.

## Visão Geral da Arquitetura
- Origem de mensagens (WhatsApp/Email/Chat) → Backend/Painel → `POST /v1/pages` (Notion) → Data Source (board)
- Notion Webhooks (`page.created`, `page.content_updated`) → Endpoint `POST /webhooks/notion` → Atualizações no painel/sistema interno

## Mudanças de Modelo (2025-09-03)
- `database_id` foi substituído por `data_source_id` em diversas operações.
- Criação de página sob um data source exige `parent[type] = "data_source_id"` e `parent[data_source_id]`.
- Templates do data source podem ser aplicados via `template[type] = "default"` ou `template[type] = "template_id"` + `template[template_id]`.

Referências:
- NotionGuides: Working with databases / Creating pages from templates
- NotionGuides: Upgrading to Version 2025-09-03
- NotionApi: Webhooks (eventos, entrega)

## Descoberta e Configuração Inicial
- Variáveis de ambiente:
  - `NOTION_API_KEY`: token da integração (Bearer).
  - `NOTION_DATA_SOURCE_ID`: ID do data source (board de atendimentos).
  - `NOTION_VERSION`: `2025-09-03`.
  - `NOTION_WEBHOOK_URL`: URL pública do endpoint receptor.
  - `NOTION_WEBHOOK_SECRET`: segredo para validar assinaturas do webhook.

- Obter `data_source_id`:
  - Pelo app do Notion: abrir o board e copiar o ID da URL.
  - Ou via API de busca/lista, ajustando o fluxo para considerar objetos de data source conforme o guia de migração.

## Modelagem de Propriedades no Notion
- Propriedades sugeridas para o data source de atendimentos (ajuste conforme necessidade):
  - `Name` (title) → título do atendimento.
  - `Status` (status) → ex.: "Novo", "Em atendimento", "Aguardando", "Resolvido".
  - `Prioridade` (select) → ex.: "Baixa", "Média", "Alta".
  - `Cliente` (rich_text ou relation) → identificação do cliente.
  - `Canal` (select) → ex.: "WhatsApp", "Email", "Chat".
  - `ID Externo` (rich_text) → ID da mensagem/sessão no sistema.
  - `Responsável` (people) → agente.
  - `SLA` (date) → prazos.
  - `Tags` (multi_select).

> Observação: valide os nomes/tipos exatamente como definidos no seu data source para evitar erros de schema.

## Fluxo: Nova Mensagem → Criação de Página no Notion
1. Receber a mensagem no backend e normalizar campos (cliente, canal, texto, ID externo, prioridade sugerida).
2. Enviar `POST /v1/pages` com headers:
   - `Authorization: Bearer <NOTION_API_KEY>`
   - `Notion-Version: 2025-09-03`
3. Body mínimo (exemplo):

```json
{
  "parent": {
    "type": "data_source_id",
    "data_source_id": "<NOTION_DATA_SOURCE_ID>"
  },
  "properties": {
    "Name": {
      "title": [
        { "type": "text", "text": { "content": "Atendimento #123" } }
      ]
    },
    "Status": { "status": { "name": "Novo" } },
    "Canal": { "select": { "name": "WhatsApp" } },
    "ID Externo": {
      "rich_text": [
        { "type": "text", "text": { "content": "msg-abc-123" } }
      ]
    }
  },
  "template": { "type": "default" }
}
```

- Se não quiser aplicar o template padrão, use `"template": { "type": "none" }`.
- Armazene o `page.id` retornado para correlacionar com a conversa interna.

### Nota sobre processamento de templates
- A criação retorna imediatamente com uma página quase vazia.
- O Notion aplica o template em background. O evento `page.created` pode ser deferido até a página estar pronta, ou vir seguido de `page.content_updated`.
- Confirme prontidão com `Retrieve block children` se sua integração precisar agir apenas após conteúdo estar populado.

## Webhooks: Eventos e Sincronização
### Assinatura e Versão
- No painel da integração do Notion, crie/edite a assinatura de webhook:
  - Selecione `API version`: `2025-09-03`.
  - Inscreva-se em `page.created` e `page.content_updated`.
  - Configure a URL do endpoint: `POST <NOTION_WEBHOOK_URL>`.

### Comportamento dos eventos
- `page.created`: página de atendimento criada (pode já incluir conteúdo se template foi aplicado rápido).
- `page.content_updated`: página atualizada (conteúdo/propriedades), tipicamente após duplicação do template.

> Os eventos não carregam conteúdo completo; use o `page_id` para consultar a API e obter propriedades e blocos.

### Handler do webhook (alto nível)
1. Validar assinatura e versão do evento.
2. Para cada evento:
   - `page.created`:
     - `GET /v1/pages/{page_id}` para propriedades.
     - Opcional: `GET /v1/blocks/{page_id}/children` para conteúdo.
     - Atualizar estado interno (ex.: marcar atendimento como "criado").
   - `page.content_updated`:
     - Reconsultar propriedades/conteúdo.
     - Sincronizar mudanças (status, responsável, tags) com o painel.
3. Garantir idempotência (deduplicar pelo `event_id`/`page_id` + `timestamp`).

### Paginação
- Endpoints de lista/blocos usam paginação baseada em cursor.
- Utilize `start_cursor` e trate `has_more` para obter todos os blocos.

## Exemplos de Requisições
### Listar templates de um Data Source
```bash
curl --request GET \
     --url "https://api.notion.com/v1/data_sources/<DATA_SOURCE_ID>/templates" \
     -H "Notion-Version: 2025-09-03" \
     -H "Authorization: Bearer $NOTION_API_KEY"
```

### Criar página (aplicando template padrão)
```bash
curl --request POST \
     --url "https://api.notion.com/v1/pages" \
     -H "Content-Type: application/json" \
     -H "Notion-Version: 2025-09-03" \
     -H "Authorization: Bearer $NOTION_API_KEY" \
     --data '{
       "parent": {"type": "data_source_id", "data_source_id": "<NOTION_DATA_SOURCE_ID>"},
       "properties": {"Name": {"title": [{"type": "text", "text": {"content": "Atendimento #123"}}]}},
       "template": {"type": "default"}
     }'
```

### Consultar conteúdo (blocos) após atualização
```bash
curl --request GET \
     --url "https://api.notion.com/v1/blocks/<PAGE_ID>/children" \
     -H "Notion-Version: 2025-09-03" \
     -H "Authorization: Bearer $NOTION_API_KEY"
```

## Checklist de Migração (2025-09-03)
- Adicionar etapa de descoberta e armazenamento do `data_source_id`.
- Enviar `data_source_id` ao criar páginas e definir relações.
- Migrar endpoints antigos de database para data source.
- Se usar Search API, adaptar parsing para objetos de data source e possíveis múltiplos resultados por database.
- Fixar `Notion-Version` para `2025-09-03` em todas as chamadas.
- Se usar SDK TypeScript, atualizar para v5 e migrar para métodos `notion.dataSources.*`/`notion.databases.*` (no nosso caso Python, usar HTTP direto).

## Segurança, Resiliência e Observabilidade
- Validar assinaturas do webhook e timestamps.
- Tratar rate limits (retry com backoff exponencial e `Retry-After`).
- Idempotência: armazenar `last_event` por `page_id`.
- Timeouts e circuit breakers nas chamadas HTTP.
- Logging estruturado para eventos e erros.

## Plano de Implementação
1. Configurar variáveis e conexão com Notion (API key, versão, data source).
2. Mapear propriedades do board de atendimentos e ajustar o payload de criação.
3. Implementar serviço de criação de página ao receber nova mensagem.
4. Criar endpoint `POST /webhooks/notion` e validar assinatura.
5. Processar `page.created`/`page.content_updated` e sincronizar com o painel.
6. Testes E2E: criar mensagem simulada → verificar página no Notion → validar eventos → checar atualização interna.
7. Observabilidade: logs, métricas e alertas em falhas de webhook ou rate limit.

## Riscos e Mitigações
- Diferenças de schema entre ambiente e plano: mitigar com validação automática dos nomes/tipos de propriedades.
- Atrasos na aplicação de template: usar webhook e verificação de blocos antes de ações dependentes.
- Rate limits: implementar retries e filas assíncronas para criação/atualização.

## Próximos Passos
- Confirmar `NOTION_DATA_SOURCE_ID` do board.
- Ajustar nomes/tipos das propriedades do payload.
- Implementar o endpoint do webhook e registrar assinatura no Notion.
- Rodar testes de ponta a ponta e ajustar fluxos conforme resultados.
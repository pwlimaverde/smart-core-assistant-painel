# Kanban Dinâmico por Fluxo — Especificação Funcional e Técnica

## 📌 Contexto e Objetivo

Este documento estrutura a proposta de visualização em Kanban para gestão de atendimentos, alinhada ao planejamento da Central de Atendimento e ao padrão de integração existente no projeto (Django + Notion + serviços de sincronização). O objetivo é garantir que, ao cadastrar uma nova etapa de fluxo, o sistema crie/organize automaticamente os “quadros” de trabalho por departamento+fluxo, com rastreio completo de movimentações e métricas.

## 🧭 Terminologia e Convenções

- Departamento: área funcional (ex.: Comercial, Financeiro, Suporte).
- Fluxo: conjunto de etapas de trabalho de um departamento (ex.: “Orçamento”).
- Etapa: coluna/estado do processo (ex.: FILA, TRABALHO, ESPERA, FINALIZAÇÃO).
- Quadro (Board): visualização Kanban associada a um fluxo/etapa.
- Página: entidade organizacional no Notion onde ficam databases/visualizações.
- Nome dinâmico (Página): `"{departamento_slug}-{fluxo_slug}"` (ex.: `comercial-orcamento`).
- Slug de configuração: `"ui_operacional_board_{departamento_slug}-{fluxo_slug}"`.

## 🎯 Escopo Funcional

### 1. Criação/Verificação de Página por Departamento+Fluxo
- Ao cadastrar uma nova etapa de um fluxo, o sistema resolve:
  - `departamento_slug` e `fluxo_slug`;
  - `page_name = "{departamento_slug}-{fluxo_slug}"` (ex.: `comercial-orcamento`).
- Procura em `NotionDatabaseConfig` por registro com `name == page_name` ou `slug == ui_operacional_board_{page_name}`.
- Caso não exista:
  - Cria uma nova Página no Notion com `title = page_name`;
  - Registra a Página/Database em `NotionDatabaseConfig` (IDs, schema, mapeamentos);
  - Prepara estrutura para visualização Kanban dos atendimentos vinculados ao fluxo.
- Caso já exista:
  - Recupera os IDs (página/database) da configuração;
  - Prossegue para criar o novo “quadro” (visualização) referente à etapa cadastrada.

### 2. Quadros (Boards) por Etapa de Fluxo
- Para cada etapa criada, deve existir um “quadro” específico dentro da Página `departamento-fluxo`.
- Nome do quadro: `"{etapa_slug}"` (ex.: `fila`, `trabalho`, `espera`, `finalizacao`).
- Conteúdo do quadro:
  - Cards representam `Atendimentos` vinculados ao fluxo;
  - Filtro mínimo: `fluxo == fluxo_atual` e (opcional) `etapa_atual == etapa_do_quadro`;
  - Campos visíveis: cliente, assunto, etapa atual, atendente, prioridade, tags, tempo na etapa.

### 3. Movimentações e Atribuição Manual
- Ao mover um card de `FILA → TRABALHO`:
  - Atribuição automática ao atendente que moveu; registro em `MovimentoFluxo`.
- Ao mover `TRABALHO/ESPERA → FILA`:
  - Remove atribuição (atendimento volta a ficar disponível); registra movimento.
- Movimentos entre etapas de trabalho mantêm a atribuição ao mesmo atendente.
- Todos os movimentos geram histórico (`MovimentoFluxo`) e métricas de duração.

### 4. Atualizações em Tempo Real
- Painel Kanban recebe atualizações via WebSockets (Django Channels).
- Cada ação de movimentação dispara eventos para atualizar a UI dos participantes.

### 5. Métricas e Auditoria
- Tempo em FILA, tempo em TRABALHO, tempo em ESPERA;
- Taxa de devolução à FILA; produtividade por atendente; tempo total de atendimento;
- Registro completo: quem moveu, quando, motivo, origem/destino, duração.

## ⚙️ Fluxo Operacional — Cadastro de Nova Etapa

1. Entrada: `fluxo_id`, `nome_etapa`, `tipo_etapa`, `ordem`, `cor`, `regras_transicao`.
2. Resolver `departamento_slug` e `fluxo_slug` a partir do `fluxo_id`.
3. Montar `page_name = "{departamento_slug}-{fluxo_slug}"`.
4. Consultar `NotionDatabaseConfig` por `name == page_name` (ou `slug == ui_operacional_board_{page_name}`).
5. Se não existir configuração:
   - Criar Página no Notion com título `page_name`;
   - (Estrutura recomendada) Criar uma Database de “Atendimentos do Fluxo”, com propriedades para:
     - `Título` (title), `Etapa (Status/Select)`, `Departamento`, `Fluxo`, `Atendente`, `Prioridade`, `Tags`, `Data Criação`;
   - Persistir a configuração em `NotionDatabaseConfig` com `notion_database_id`, `data_source_id` (se aplicável), `notion_page_id` (se houver), `notion_schema` e `field_mappings`;
   - Criar o “quadro” (visualização Kanban) para a `etapa` (ver limitações Notion abaixo).
6. Se existir configuração:
   - Reutilizar IDs existentes;
   - Criar o novo “quadro” para a `etapa` dentro da Página `page_name`.
7. Atualizar a UI do painel e sincronizar atendimentos que pertencem ao fluxo para aparecerem no novo quadro (segundo o filtro estabelecido).
8. Persistir logs e métricas; validar consistência de mapeamento `Atendimento ↔ Card`.

## 🔗 Integração Técnica e Limitações do Notion

### Limitação Importante (API Notion)
- A API oficial do Notion **não suporta** criação/gestão de “views” (incluindo Kanban) programaticamente. É possível criar databases e propriedades, mas a **configuração da visualização** deve ser feita manualmente na UI.

### Modos de Execução
**Modo A — Notion (com complemento manual na UI):**
- Automação cria/ajusta a Página e a Database do fluxo;
- Um operador configura manualmente a visualização Kanban na Página para cada etapa;
- O projeto mantém sincronização de dados (paginação, propriedades, relação com Atendimentos), usando `NotionAsyncClient` e `NotionDatabaseConfig`.

**Modo B — Provedor de Board (dinâmico), com Notion como espelho:**
- Adotar um serviço com API que cria boards/listas/colunas e cards via código (ex.: Trello ou WeKan);
- Mapear `Departamento+Fluxo` para um “board” e as “etapas” para listas/colunas;
- Sincronizar `Atendimento ↔ Card` e movimentos via webhooks/serviço;
- Manter o Notion como espelho de dados e relatórios (opcional), preservando `NotionDatabaseConfig` para consultas/integrações.

Recomendação: para **criação dinâmica de quadros** ao cadastrar etapas, usar o **Modo B** (Trello/WeKan) e manter o Notion como camada de documentação/relatórios.

## 🗂️ Modelos e Configurações

### NotionDatabaseConfig (existente)
- Campos chave: `slug`, `name`, `notion_database_id`, `data_source_id`, `notion_page_id`, `django_model`, `django_app_label`, `notion_schema`, `field_mappings`, `sync_enabled`.
- Convenção de `slug` sugerida: `ui_operacional_board_{departamento_slug}-{fluxo_slug}`.

### (Sugerido) ExternalBoardConfig
- Finalidade: parametrizar o provedor de board (Trello/WeKan/Kanboard) para criação dinâmica de “quadros/colunas”.
- Campos:
  - `slug`: `ui_operacional_board_{departamento_slug}-{fluxo_slug}`;
  - `service_type`: `"trello" | "wekan" | "kanboard"`;
  - `workspace_id/team_id`, `board_id`;
  - `columns_map`: `{ etapa_slug: list_id }`;
  - `sync_enabled`, `sync_direction`, `sync_priority`.

### (Sugerido) BoardObjectMapping
- Finalidade: mapear `Atendimento.id ↔ card_id` (e outros relacionamentos necessários).
- Índices para reconciliação rápida e consistência.

## 🧠 Regras de Negócio (resumo)

- `FILA → TRABALHO`: atribuir atendimento ao atendente que moveu.
- `TRABALHO/ESPERA → FILA`: remover atribuição.
- `TRABALHO ↔ TRABALHO` / `TRABALHO ↔ ESPERA`: manter atribuição.
- Toda mudança gera `MovimentoFluxo` com origem, destino, atendente, motivo e duração estimada.

## 🔄 Sincronização e Eventos

- Painel SPA atualizado por `Django Channels` (grupos por departamento/fluxo).
- Webhooks (no Modo B) para eventos de `card moved`/`card created`;
- Pull/poll para Notion caso necessário (não há webhooks oficiais); respeitar rate limits.
- Estratégia de conflitos: “last write wins” com logs e reconciliação periódica.

## 🔐 Segurança e Ambiente

- Segredos em `.env` (ex.: `TRELLO_KEY`, `TRELLO_TOKEN`, `WEKAN_API_URL`, etc.).
- Expor `.env.example` documentando variáveis exigidas (sem valores).
- Compatibilidade com Windows e execução em Docker (ambiente padronizado).

## ✅ Testes e Qualidade

- Testes automatizados em Docker: `uv run task test-docker`.
- Cobrir cenários: criação de Página/Database, criação de board/lista/coluna, criação/movimento de card, idempotência, falhas de rede, reconciliação.
- Lint/format/type-check: `uv run task format`, `uv run task lint`, `uv run task type-check`.

## 📏 Critérios de Aceitação

1. Ao cadastrar nova `EtapaFluxo`, o sistema:
   - Resolve `page_name` e verifica `NotionDatabaseConfig`;
   - Cria Página/Database (se necessário) e registra configuração;
   - Cria “quadro” correspondente à etapa (Modo B: automático; Modo A: instrução/manual);
   - Exibe no quadro os Atendimentos do fluxo (com filtro correto).
2. Movimentações geram `MovimentoFluxo` com dados completos e atualizam a UI em tempo real.
3. Métricas básicas disponíveis: tempos por etapa, produtividade, taxa de devolução.

## 🚀 Próximos Passos

- Decidir o provedor de board para criação dinâmica (Trello/WeKan/Kanboard).
- Implementar `ExternalBoardConfig` e adapter do provedor escolhido.
- Implementar sinal `post_save(EtapaFluxo)` que chama `ensure_board_and_stage`.
- Integrar WebSockets e (se Modo B) webhooks do provedor.
- Documentar `.env.example` e atualizar `CENTRAL_DE_ATENDIMENTO.md` com referências.

---

Observação: Esta especificação está alinhada à arquitetura atual e às limitações da API do Notion quanto à gestão de “views”. Para atender ao requisito de criação dinâmica de quadros Kanban ao cadastrar etapas, recomenda-se Modo B (provedor de board com API rica), mantendo o Notion como espelho e repositório estruturado.
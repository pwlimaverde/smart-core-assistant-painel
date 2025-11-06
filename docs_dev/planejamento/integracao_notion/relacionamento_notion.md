# Relacionamentos Notion (CRM)

Este documento mapeia os relacionamentos entre os modelos do sistema e as
bases do Notion utilizadas na integração CRM. Também registra a correção
do espelhamento entre `FluxoAtendimento` ↔ `Departamento` na construção
das tabelas.

## Escopo

- Modelos sincronizados: `Cliente`, `Contato`, `Departamento`, `Atendente`,
  `Atendimento`, `Mensagem`.
- Modelos operacionais adicionais (não sincronizados por mappers, porém
  agora com base e relação): `FluxoAtendimento`.

## Bases Notion e Slugs

- `🏢 Clientes CRM` — slug: `ui_clientes_cliente` — Django: `clientes.Cliente`.
- `👥 Contatos CRM` — slug: `ui_clientes_contato` — Django: `clientes.Contato`.
- `🏛️ Departamentos CRM` — slug: `ui_operacional_departamento` — Django:
  `ui.operacional.Departamento`.
- `👨‍💼 Atendentes CRM` — slug: `ui_operacional_atendente` — Django:
  `ui.operacional.Atendente`.
- `🎯 Atendimentos CRM` — slug: `ui_atendimentos_atendimento` — Django:
  `ui.atendimentos.Atendimento`.
- `💬 Mensagens CRM` — slug: `ui_atendimentos_mensagem` — Django:
  `ui.atendimentos.Mensagem`.
- `📋 Fluxos de Atendimento CRM` — slug: `ui_operacional_fluxo_atendimento`
  — Django: `ui.operacional.FluxoAtendimento`.
- `🧱 Etapas do Fluxo CRM` — slug: `ui_operacional_etapa_fluxo` — Django:
  `ui.operacional.EtapaFluxo`.
- `🔀 Movimentos do Fluxo CRM` — slug: `ui_operacional_movimento_fluxo` —
  Django: `ui.operacional.MovimentoFluxo`.

## Relacionamentos por Modelo

### Cliente ↔ Contato (bidirecional)

- Em `Contatos`:
  - Propriedade: `Clientes Relacionados` (`relation`) → aponta para
    `🏢 Clientes CRM` via `data_source_id`.
  - Espelho bidirecional: `dual_property.synced_property_name =
    "Contatos Relacionados"`.
- Em `Clientes`:
  - Propriedade: `Contatos Relacionados` (`relation`) → espelhada via
    `data_sources` com `dual_property`.

### Departamento ↔ Atendente (bidirecional)

- Em `Atendentes`:
  - Propriedade: `Departamentos Relacionados` (`relation`) → aponta para
    `🏛️ Departamentos CRM` via `data_source_id`.
  - Espelho bidirecional: `dual_property.synced_property_name =
    "Atendentes Relacionados"`.
- Em `Departamentos`:
  - Propriedade: `Atendentes Relacionados` (`relation`) → espelhada via
    `data_sources` com `dual_property`.
  - Observação: mapeamento envia sempre a relação (inclusive vazio),
    refletindo remoções imediatas.

### Atendimento → Contato / Departamento / Atendente / Mensagens

- Em `Atendimentos`:
  - Propriedades padrão (podem ser renomeadas via `field_mappings`):
    - `Assunto` (`title`)
    - `Status` (`select`)
    - `Prioridade` (`select`)
    - `Canal` (`select`)
    - `Contexto Conversa` (`rich_text`)
    - `Tags` (`multi_select`)
    - `Data Início` (`date`)
    - `Data Última Mensagem` (`date`)
    - `Data Fim` (`date`)
    - `Avaliação` (`number`)
    - `Feedback` (`rich_text`)
  - Relacionamentos:
    - `Contato` (`relation`) → `👥 Contatos CRM` (via `external_id` de
      `ContatoSync`).
    - `Departamento` (`relation`) → `🏛️ Departamentos CRM` (via
      `external_id` de `DepartamentoSync`).
    - `Atendente` (`relation`) → `👨‍💼 Atendentes CRM` (via `external_id`
      de `AtendenteSync`).
    - `Mensagens Relacionadas` (`relation`) → `💬 Mensagens CRM` (array
      de `external_id` de `MensagemSync`).

### Mensagem → Atendimento

- Em `Mensagens`:
  - Propriedade: `Atendimento Relacionado` (`relation`) → `🎯 Atendimentos CRM`.
  - Demais propriedades: `Conteúdo` (`title`), `Tipo` (`select`),
    `Remetente` (`select`), `Timestamp` (`date`), `Message ID WhatsApp`
    (`rich_text`).

### FluxoAtendimento ↔ Departamento (bidirecional; correção aplicada)

- Em `📋 Fluxos de Atendimento CRM`:
  - Propriedade: `Departamento Relacionado` (`relation`) → aponta para
    `🏛️ Departamentos CRM` via `data_source_id`.
  - Espelho bidirecional: `dual_property.synced_property_name =
    "Fluxo de Atendimento"`.
- Em `🏛️ Departamentos CRM`:
  - Propriedade: `Fluxo de Atendimento` (`relation`) → espelhada via
    `data_sources` com `dual_property`.
  - Observação: relação 1:1 por regra de negócio (um fluxo por
    departamento).

### EtapaFluxo → FluxoAtendimento

- Em `🧱 Etapas do Fluxo CRM`:
  - Propriedade: `Fluxo Relacionado` (`relation`) → aponta para
    `📋 Fluxos de Atendimento CRM` via `data_source_id`.
  - Observação: relação 1:N (um fluxo possui várias etapas) com ordem
    controlada por propriedade `Ordem`.

### MovimentoFluxo → Atendimento / Etapas / Atendentes

- Em `🔀 Movimentos do Fluxo CRM`:
  - Propriedade: `Atendimento` (`relation`) → `🎯 Atendimentos CRM`.
  - Propriedade: `Etapa Origem` (`relation`) → `🧱 Etapas do Fluxo CRM`.
  - Propriedade: `Etapa Destino` (`relation`) → `🧱 Etapas do Fluxo CRM`.
  - Propriedade: `Atendente Origem` (`relation`) → `👨‍💼 Atendentes CRM`.
  - Propriedade: `Atendente Destino` (`relation`) → `👨‍💼 Atendentes CRM`.
  - Observação: campos adicionais como `Motivo`, `Dados Complementares`,
    `Automático`, `Data do Movimento` e `Duração (s)` compõem o schema.

## Especificações Técnicas

- Todas as relações utilizam Notion `relation` com `data_source_id` para
  garantir o vínculo por fonte de dados.
- Propriedades espelhadas são garantidas via `dual_property` com
  `synced_property_id` quando disponível ou `synced_property_name`.
- Mappers principais (Django → Notion):
  - `DepartamentoMapper`: usa `Atendentes Relacionados` e envia sempre a
    relação, inclusive vazia.
  - `AtendenteMapper`: `Departamentos Relacionados` (1..1 no sistema,
    representado como `relation` no Notion).
  - `AtendimentoMapper`: propriedades padrão e relações listadas acima;
    suporta `field_mappings` via `NotionDatabaseConfig` para renomear
    campos no Notion.
  - `MensagemMapper`: `Atendimento Relacionado` e blocos de conteúdo.

### Schemas mínimos operacionais

- `📋 Fluxos de Atendimento CRM`:
  - Propriedades: `Nome` (`title`), `Descrição` (`rich_text`), `Ativo`
    (`checkbox`), `Data Criação` (`date`), `Departamento Relacionado`
    (`relation`).
- `🧱 Etapas do Fluxo CRM`:
  - Propriedades: `Nome` (`title`), `Descrição` (`rich_text`), `Ordem`
    (`number`), `Cor` (`select`), `Tipo de Etapa` (`select`),
    `Permite Atribuição` (`checkbox`), `Fluxo Relacionado` (`relation`),
    `Data Criação` (`date`).
- `🔀 Movimentos do Fluxo CRM`:
  - Propriedades: `Título` (`title`), `Motivo` (`rich_text`), `Dados
    Complementares` (`rich_text`), `Automático` (`checkbox`), `Data do
    Movimento` (`date`), `Duração (s)` (`number`), `Atendimento`
    (`relation`), `Etapa Origem` (`relation`), `Etapa Destino`
    (`relation`), `Atendente Origem` (`relation`), `Atendente Destino`
    (`relation`).

## Decisões de Sincronização

- IDs externos (`external_id`) são usados para montar relações no Notion.
- O agendamento de sincronização (Django Q) garante que páginas pais
  existam antes de relacionamentos filhos (ex.: Mensagem → Atendimento).
- Para `Etapas do Fluxo`, a relação com `Fluxo` só é enviada quando o
  `FluxoAtendimentoSync` possuir `external_id` (senão é omitida).
- Para `Movimentos do Fluxo`, as relações com `Atendimento`, `Etapas` e
  `Atendentes` são adicionadas apenas quando seus respectivos `*Sync`
  possuem `external_id`.
- Para `Departamentos`, a relação com `Atendentes` é enviada sempre para
  refletir remoções e manter visualização consistente.

## Plano de Correção: Fluxo ↔ Departamento

Para corrigir o problema de não espelhamento na construção:

1. Criada a base `📋 Fluxos de Atendimento CRM` com propriedade
   `Departamento Relacionado` apontando para `🏛️ Departamentos CRM`.
2. Adicionada a propriedade inversa `Fluxo de Atendimento` em
   `🏛️ Departamentos CRM` via atualização em `data_sources` com
   `dual_property`.
3. Persistida configuração `ui_operacional_fluxo_atendimento` em
   `NotionDatabaseConfig` (mapeando `ui.operacional.FluxoAtendimento`).

Observação: embora não exista mapper dedicado para `FluxoAtendimento`,
o espelhamento estrutural no Notion fica garantido para futuras
evoluções de sincronização.

## Comandos Recomendados

- Para testar em ambiente Docker: `uv run task test-docker`.
- Para lint/format: `uv run task lint` e `uv run task format`.

---

Documento mantido em conformidade com os padrões do projeto (PEP8 para
código, comentários em Português, e integração compatível com Windows).
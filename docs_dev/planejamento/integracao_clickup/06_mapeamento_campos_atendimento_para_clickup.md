# Mapeamento de Campos do Atendimento para Custom Fields no ClickUp

## Visão Geral

Este documento propõe um mapeamento detalhado dos campos do model
`Atendimento` (app `atendimentos`) para campos personalizados (Custom
Fields) em cards do ClickUp, com foco em enriquecer o contexto para os
atendentes na Central de Atendimento. A proposta considera a arquitetura
por Departamentos (Folder), Fluxos por departamento (List) e Etapas
(`EtapaFluxo`) mapeadas para Status da List.

- Base técnica: Django + PostgreSQL, UI Kanban por departamento.
- Integração: ClickUp API v2 (`Authorization: Bearer <token>`).
- Referências: `CENTRAL_DE_ATENDIMENTO.md` e `02_plano_de_integracao.md`.

## Campos do Model `Atendimento`

Campos principais identificados no model (`src/.../atendimentos/models.py`):

- `id` (AutoField)
- `contato` (FK `clientes.Contato`)
- `departamento` (FK `operacional.Departamento`)
- `fluxo_atendimento` (FK `operacional.FluxoAtendimento`)
- `status` (Enum `StatusAtendimento` – legado)
- `etapa_atual` (FK `operacional.EtapaFluxo` – etapa no fluxo)
- `data_inicio` (DateTime)
- `data_fim` (DateTime | null)
- `data_ultima_mensagem` (DateTime | null)
- `assunto` (Char | null)
- `prioridade` (Char; baixa/normal/alta/urgente)
- `atendente_humano` (FK `operacional.Atendente` | null)
- `contexto_conversa` (JSON)
- `historico_status` (JSON list)
- `tags` (JSON list)
- `avaliacao` (Integer 1–5 | null)
- `feedback` (Text | null)
- `data_primeira_resposta` (DateTime | null)
- `canal` (Char; whatsapp/email/telefone/web)

## Mapeamento para Custom Fields no ClickUp

Princípios:

- Campos que melhoram a leitura rápida do card, contexto do cliente,
  SLAs e próximos passos.
- Reuso preferencial em **Workspace** para padrões (Canal, Avaliação),
  e **List** para campos específicos de fluxos (Ex.: Resumo).
- Onde houver equivalentes nativos do ClickUp (Assignees, Priority,
  Status), usar nativos e complementar com CF apenas se necessário.

| Campo (Model)             | CF no ClickUp (nome)         | Tipo CF       | Nível        | Por que é importante |
|---------------------------|-------------------------------|---------------|--------------|----------------------|
| `departamento`            | `Department`                  | Dropdown      | Workspace    | Filtro e agregação cross-list; visível mesmo fora da pasta. |
| `fluxo_atendimento`       | `Flow`                        | Text          | List         | Ajuda a identificar o fluxo quando há múltiplos por pasta. |
| `etapa_atual` → Status    | — (usar Status da List)       | —             | List         | Alinha com Kanban nativo; evita duplicação de status. |
| `status` (legado)         | —                             | —             | —            | Não criar CF; manter compatibilidade interna apenas. |
| `assunto`                 | `Subject (Summary)`           | Short Text    | List         | Resumo legível no card, além do título quando necessário. |
| `data_inicio`             | `Service Start`               | DateTime      | Workspace    | Ponto inicial para SLA e métricas operacionais. |
| `data_fim`                | `Service End`                 | DateTime      | Workspace    | Cálculo de tempo total de atendimento. |
| `data_ultima_mensagem`    | `Last Message At`             | DateTime      | Workspace    | Ajuda no ordenamento e triagem por recência. |
| `prioridade`              | `Priority (Local)`            | Dropdown      | List         | Alternativa ao nativo; útil se granularidade difere do padrão. |
| `atendente_humano`        | — (usar `assignees`)          | —             | —            | Usa campo nativo (People) do card; evita redundância. |
| `contexto_conversa`       | `Conversation Context`        | Long Text     | List         | Pontos-chave da conversa; evita sobrecarregar a descrição. |
| `historico_status`        | `Status History URL`          | URL           | Workspace    | Linka rastro detalhado (interno); CF armazena referência. |
| `tags`                    | — (usar `tags` nativo)        | —             | —            | Tags nativas do ClickUp para categorização. |
| `avaliacao`               | `Customer Rating (1–5)`       | Number        | Workspace    | NPS por atendimento; identifica satisfação por card. |
| `feedback`                | `Customer Feedback`           | Long Text     | Workspace    | Registro textual do cliente para contexto futuro. |
| `data_primeira_resposta`  | `First Response At`           | DateTime      | Workspace    | SLA de 1ª resposta, crítico em operações. |
| `canal`                   | `Channel`                     | Dropdown      | Workspace    | Estratégia e métricas por canal (WhatsApp, e-mail etc.). |

### Campos derivados recomendados (do relacionamento `contato`)

Para enriquecer o entendimento, é valioso expor dados-chave do contato:

| Origem                 | CF no ClickUp (nome) | Tipo CF   | Nível     | Benefício |
|------------------------|-----------------------|-----------|-----------|-----------|
| `contato.nome`         | `Contact Name`        | Short Text| Workspace | Atendimento humanizado e melhor triagem. |
| `contato.telefone`     | `Contact Phone`       | Phone     | Workspace | Contato rápido; integrações de discagem. |
| `contato.email`        | `Contact Email`       | Email     | Workspace | Escalonamento e follow-up por e-mail. |
| `contato.id`           | `Contact ID`          | Text      | Workspace | Correlação e auditoria com o sistema interno. |

> Observação: estes campos são populados a partir da FK `contato`. Caso o
> model não exponha todos os atributos, usar services para leitura
> agregada no momento da sincronização com ClickUp.

## Status e Fluxo: Diretrizes de Mapeamento

- `EtapaFluxo` deve ser mapeada para o **Status** da List correspondente.
- Sugestão de correspondência (ajustável por fluxo):
  - `FILA` → `Novo` (type: `open`)
  - `EM_ATENDIMENTO` → `Em atendimento` (type: `open`)
  - `PENDENCIA` → `Aguardando cliente` (type: `open`)
  - `TRANSFERIDO` → `Transferido` (type: `open` ou mover para a fila do
    novo departamento)
  - `RESOLVIDO` → `Resolvido` (type: `closed`)
  - `CANCELADO` → `Cancelado` (type: `closed`)

- Manter a coerência entre `departamento`, `fluxo_atendimento` e
  `etapa_atual` (já validado em `clean()` no Django).

## Plano de Implementação via ClickUp API

1. Descoberta de IDs
   - `GET /api/v2/team` → `team_id`.
   - Criar/obter `space_id` e `folder_id` conforme planejamento.
   - `POST /api/v2/space/{space_id}/folder` (Departamento).
   - `POST /api/v2/folder/{folder_id}/list` (Fluxo do Departamento).

2. Configuração de Status (List)
   - Enviar `statuses` já na criação da List.
   - Fallback/idempotência: `PUT /api/v2/list/{list_id}` com `statuses`.
   - Persistir correlação `EtapaFluxo.nome` ↔ `status` para sincronização.

3. Custom Fields (CF)
   - Descoberta e reuso: `GET /api/v2/team/{team_id}/field` (Workspace).
   - Anexar CF à List: `GET/POST /api/v2/list/{list_id}/field`.
   - Setar valor no card: `POST /api/v2/task/{task_id}/field/{field_id}`.
   - Estratégia: campos **Workspace** para reuso (Channel, Rating, datas),
     campos **List** para contexto específico (Subject, Conversation Context).

4. Criação e Atualização de Cards (Tasks)
   - Criar: `POST /api/v2/list/{list_id}/task` com `name`, `status`,
     `assignees` (usar nativo para `atendente_humano`).
   - Atualizar Status: `PUT /api/v2/task/{task_id}`.
   - Setar CFs: `POST /api/v2/task/{task_id}/field/{field_id}` por campo.

5. Webhooks
   - `POST /api/v2/team/{team_id}/webhook` (events: task create/update/move/status change).
   - Consumir no Django e refletir mudanças ao sistema interno.

6. Persistência de Mapeamento
   - Manter tabela/local store com `field_id` por CF, por List/Workspace.
   - Validar compatibilidade de tipos antes de setar valores.

### Exemplos de Requisição (resumo)

- Criar List com Status personalizados:

```
POST https://api.clickup.com/api/v2/folder/{folder_id}/list
Authorization: Bearer <token>
{
  "name": "Fluxo Atendimento WhatsApp",
  "statuses": [
    {"status": "Novo", "type": "open"},
    {"status": "Em atendimento", "type": "open"},
    {"status": "Aguardando cliente", "type": "open"},
    {"status": "Resolvido", "type": "closed"}
  ]
}
```

- Definir CF em uma Task (ex.: `Customer Rating`):

```
POST https://api.clickup.com/api/v2/task/{task_id}/field/{field_id}
Authorization: Bearer <token>
{
  "value": 5
}
```

## Justificativas por Campo (Resumo)

- `Channel`: imediatamente destaca o canal de origem, melhorando priorização
  e roteamento.
- `First Response At` e `Service Start/End`: possibilitam SLAs confiáveis
  e auditoria.
- `Last Message At`: ordena por recência e evita estagnação de casos.
- `Customer Rating` e `Customer Feedback`: insights de satisfação e motivos
  para melhoria contínua.
- `Department` e `Flow`: reforçam contexto quando cards são vistos fora
  da pasta/list.
- `Subject (Summary)` e `Conversation Context`: balanceiam legibilidade e
  detalhamento sem poluir a descrição.
- `Contact Name/Phone/Email/ID` (derivados): acessibilidade e correlação
  rápida com o CRM interno.

## Segurança e Operação

- Autenticação: `Authorization: Bearer <token>` via variável de ambiente
  (ex.: `CLICKUP_TOKEN`), sem segredos em código.
- Logs estruturados: usar `loguru` e saídas mais ricas com `rich` em scripts.
- Testes: rodar sempre em Docker com `uv run task test-docker` e cobertura
  ≥80% para integrações críticas (CF set/get, status, webhooks).

## Checklist de Sincronização

- [ ] Lists têm `statuses` coerentes com `EtapaFluxo`.
- [ ] CFs de Workspace anexados às Lists de todos os Departamentos.
- [ ] `field_id` persistidos e versionados.
- [ ] Criação de Task popula: `Channel`, `Contact Name/Phone/Email/ID`.
- [ ] Movimentos atualizam `status` e CFs de datas (Start/End/First Response/Last Message).
- [ ] Webhooks refletem mudanças de ClickUp para o sistema interno.

---

### Observações Finais

- Priorizar o uso de campos nativos de ClickUp (Status, Assignees, Tags,
  Priority) e suplementar com CFs apenas para contexto adicional.
- Campos derivados do `contato` são críticos para visão 360º do cliente
  no card e devem ser priorizados.
- Onde o `status` legado ainda for necessário, manter conversão interna
  para os `statuses` da List, sem criar CF redundante.
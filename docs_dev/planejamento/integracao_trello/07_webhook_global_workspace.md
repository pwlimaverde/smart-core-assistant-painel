# Webhooks Dinâmicos do Trello — Cobertura de Quadros Atuais e Futuros

Este documento descreve, em detalhe, como implementar um **webhook global** em nível de **Área de Trabalho (Workspace)** do Trello para registrar, de forma permanente, as movimentações dos cards dos quadros atuais e futuros. O objetivo é que **cada atendimento** lançado no Trello tenha sua movimentação entre os **fluxos** refletida corretamente no sistema.

---

## 1. Visão Geral

- **Escopo**: Webhooks **dinâmicos por Board** (modelo `board`) registrados automaticamente na criação de cada quadro do Workspace; complementados por um job de reconciliação que garante cobertura para quadros existentes e futuros.
- **Resultado**: Sempre que um card for movido de lista (etapa), o endpoint recebe o evento (`moveCardToList`, `updateCard`, etc.) e o sistema pode atualizar a **etapa atual** do atendimento correspondente (quando o processamento estiver habilitado). Quadros e listas criados dinamicamente ficam cobertos sem ação manual.
- **Princípios**:
  - Segurança (callback verificado e protegido por segredo)
  - Idempotência (não processar o mesmo evento duas vezes)
  - Resiliência (respeito a rate limits, retentativas e monitoramento)
  - Compatibilidade com a **versão gratuita** do Trello (sem Custom Fields)

---

## 2. Fundamentos dos Webhooks (TrelloWebhook)

Os pontos abaixo derivam diretamente da documentação oficial “Webhooks” do Trello.

- **Pertencem ao Token**:
  - Webhooks pertencem a tokens e somente monitoram objetos que o token pode acessar.
  - A implementação deve usar a **Key** e o **Token** do Trello obtidos via app-key.

- **callbackURL válido e verificação HEAD**:
  - No momento da criação, o Trello faz uma requisição **HEAD** para `callbackURL` e exige **200 OK**.
  - Se o `callbackURL` não retornar 200, ou tiver **SSL inválido**, o webhook **não será criado**.
  - O endpoint deve responder **HEAD 200** e, opcionalmente, **GET 200** para testes.

- **idModel (Modelo Observado)**:
  - O webhook precisa de um `idModel` (`member`, `card`, `list`, `board`, `organization/workspace`).
  - **Importante**: eventos de **movimentação de cards/listas** são disparados pelos **Boards** (modelo `board`). Um webhook no **Workspace** (`organization`) **não recebe** eventos de card/lista; ele cobre eventos do próprio Workspace (ex.: mudanças de membros/admins).
  - Portanto, para captar movimentações de cards de quadros atuais e futuros, a solução viável é **registrar webhooks por Board** de forma **dinâmica** no momento da criação de cada quadro.

- **Métodos Importantes da API**:
  - `POST /1/webhooks` — criar webhook.
  - `GET /1/tokens/{token}/webhooks` — listar webhooks do token (gestão/inspeção).
  - `DELETE /1/webhooks/{idWebhook}` — apagar webhook.

- **Tipos de Ações e Cobertura**:
  - Ações em **cards** e **listas** são emitidas aos webhooks do **Board** correspondente (ex.: `moveCardToList`, `updateCard`, `createList`).
  - Ações do Workspace (ex.: `makeNormalMemberOfOrganization`, `removeMemberFromOrganization`) são emitidas ao webhook de **Organization** quando configurado.
  - Implementar um **roteador de ações** (quando processamento estiver ativo) mapeando `action.type` → handler.

- **Rate Limits e Retentativas (Outbound)**:
  - A API do Trello retorna cabeçalhos de **rate limit** contendo intervalo, limite máximo e restante.
  - O sistema deve usar essa informação para evitar estouros (backoff exponencial nas requisições ao Trello).

- **Retentativas de Webhook (Inbound)**:
  - Se o callback falhar, o Trello **reitenta 3 vezes**: após **30s**, **60s** e **120s**.

- **Desativação Automática**:
  - Webhooks podem ser **desativados automaticamente** se houver **falhas consecutivas** por **30 dias** ou se o token perder acesso ao modelo.
  - Um **único sucesso** reseta contadores. Monitorar o estado e revalidar proativamente.

---

## 3. Arquitetura Proposta

- **Assinatura Dinâmica por Board (Viável e Requerida)**:
  - Registrar **automaticamente** um webhook com `idModel = {idBoard}` **imediatamente após a criação** de cada `Board` do fluxo.
  - Motivação: somente o **Board webhook** recebe eventos de card/lista.

- **Sentinela por Workspace (Opcional)**:
  - Manter um webhook em `idOrganization` para receber eventos administrativos (ex.: perda de privilégio admin), conforme “Webhooks and Admins”. Não substitui o board webhook.

- **Endpoint Público Unificado**:
  - `POST /api/trello_sync/webhook/`: recebe o **payload JSON**.
  - Deve suportar `HEAD 200` e **validar um segredo** (`secret`) no querystring.

- **Roteador de Ações**:
  - `moveCardToList` / `updateCard`: atualizar mapeamento de **lista→etapa** e refletir no **atendimento**.
  - `createBoard`: detectar criação de quadros e **sincronizar** com fluxos.
  - `createList` / `updateList`: reconciliar listas com etapas (nome/ordem/posição).
  - `moveCardToBoard`: remapear card entre boards do Workspace ou sinalizar transferência.
  - `deleteCard`: ajustar estado do atendimento (ex.: arquivado/cancelado) conforme política.

- **Mapeamentos de Domínio**:
  - `Board` ↔ `FluxoAtendimento`
  - `List` ↔ `EtapaFluxo`
  - `Card` ↔ `Atendimento`
  - Mantêm a relação necessária para atualizar a **etapa atual** quando o card muda de lista.

- **Idempotência**:
  - Basear-se em `action.id` para evitar reprocessamento.
  - Persistir o evento e **ignorar** se `action.id` já foi processado.

- **Segurança**:
  - Incluir `secret` no `callbackURL` (ex.: `...?secret=<TOKEN>`).
  - Validar `secret` antes de processar.

- **Observabilidade**:
  - Logs estruturados com `action.type`, `card.id`, `listBefore.id`, `listAfter.id`, `board.id`.
  - Painel de auditoria com eventos persistidos.

---

## 4. Variáveis de Ambiente

- `TRELLO_API_KEY` — Chave de API do Trello.
- `TRELLO_TOKEN` — Token do Trello associado ao webhook.
- `TRELLO_WORKSPACE_ID` — `idOrganization` do Workspace.
- `TRELLO_WEBHOOK_CALLBACK_URL` — URL pública do endpoint.
- `TRELLO_WEBHOOK_SECRET` — segredo para validar o callback.
- `TRELLO_ENABLE_WEBHOOKS` — `true|false|auto` para controlar registro automático.
 - `X_TRELLO_CLIENT_IDENTIFIER` — identificador opcional para evitar loops de automação (enviado em requisições à API; o valor é retornado aos webhooks).

> Boas práticas: **não** versionar segredos. Usar `.env` e fornecer `.env.example` com chaves sem valores.

---

## 5. Descoberta de `idOrganization` (Workspace)

- Abrir qualquer **board** da organização e adicionar `.json` ao final da URL.
- No JSON, localizar `"idOrganization"` e copiar o valor.
- Usar esse valor como `idModel` na criação do webhook.

---

## 6. Registro de Webhooks — Organização e Board

- **Criação (Workspace)** (`POST /1/webhooks`):

```bash
curl -X POST "https://api.trello.com/1/webhooks" \
  -d key="${TRELLO_API_KEY}" \
  -d token="${TRELLO_TOKEN}" \
  -d callbackURL="${TRELLO_WEBHOOK_CALLBACK_URL}?secret=${TRELLO_WEBHOOK_SECRET}" \
  -d idModel="${TRELLO_WORKSPACE_ID}" \
  -d description="Webhook Global do Workspace Trello"
```

- **Criação (Board dinâmico)** (`POST /1/webhooks`):

```bash
curl -X POST "https://api.trello.com/1/webhooks" \
  -d key="${TRELLO_API_KEY}" \
  -d token="${TRELLO_TOKEN}" \
  -d callbackURL="${TRELLO_WEBHOOK_CALLBACK_URL}?secret=${TRELLO_WEBHOOK_SECRET}" \
  -d idModel="{ID_DO_BOARD}" \
  -d description="Webhook por Board: {nome-do-board}"
```

- **Listagem** (`GET /1/tokens/{token}/webhooks`):

```bash
curl "https://api.trello.com/1/tokens/${TRELLO_TOKEN}/webhooks?key=${TRELLO_API_KEY}&token=${TRELLO_TOKEN}"
```

- **Remoção** (`DELETE /1/webhooks/{idWebhook}`):

```bash
curl -X DELETE "https://api.trello.com/1/webhooks/${WEBHOOK_ID}?key=${TRELLO_API_KEY}&token=${TRELLO_TOKEN}"
```

> Exigido: `callbackURL` acessível publicamente retornando **HEAD 200**.

---

## 7. Design do Endpoint (`callbackURL`)

- **HEAD**: responder `200 OK` para o handshake do Trello.
- **GET**: responder `200 OK` para teste de conectividade.
- **POST**:
  - Validar `secret` do querystring.
  - Parsear JSON do corpo.
  - Persistir o evento com `action.id`, `action.type` e payload completo.
  - Checar **idempotência** por `action.id` antes do processamento.
  - Despachar para o **roteador de ações**.
  - Retornar `200 OK` com JSON `{"status": "processed"}`.

---

## 8. Roteador de Ações (Action Router)

- **moveCardToList / updateCard**:
  - Extrair `data.card.id`, `data.listAfter.id`.
  - Resolver `card.id` para atendimento via `Card ↔ Atendimento`.
  - Resolver `listAfter.id` para etapa via `List ↔ EtapaFluxo`.
  - Atualizar `etapa_atual` do atendimento, registrar movimento.

- **createBoard**:
  - Detectar novo board no Workspace.
  - Criar/associar `FluxoAtendimento` correspondente.
  - (Opcional) Registrar webhook por board como redundância.

- **createList / updateList**:
  - Associar/atualizar `EtapaFluxo` ao `List` (nome e ordem).
  - Reordenar listas conforme `etapa.ordem` (posições).

- **moveCardToBoard**:
  - Se destino pertence ao mesmo Workspace e está mapeado, remapear `Card ↔ Atendimento` para o novo board/etapa.
  - Caso contrário, marcar transferência no domínio (ex.: `MovimentoFluxo` de saída).

- **deleteCard**:
  - Atualizar estado do atendimento conforme política (ex.: cancelado/arquivado).

> Implementar **logs** de cada etapa e garantir **idempotência** usando `action.id`.

---

## 9. Idempotência e Persistência

- Criar uma tabela de **eventos** com índice/constraint único em `action_id`.
- Ao receber um evento, verificar se `action_id` já existe; se sim, **ignorar**.
- Armazenar payload bruto para auditoria e reprocessamento manual.

---

## 10. Segurança

- **Segredo no callback**: exigir `TRELLO_WEBHOOK_SECRET` no querystring.
- **Validação**: comparar com o valor esperado; se inválido, retornar `401`.
- **Entrada**: validar/normalizar campos do payload antes de usar.
- **Segredos**: nunca registrar Key/Token em logs.
 - **Assinaturas**: opcionalmente verificar `X-Trello-Webhook` (HMAC-SHA1 com app secret) concatenando `body + callbackURL`, para garantir origem Trello.

---

## 11. Rate Limits e Resiliência

- **Outbound** (chamadas à API do Trello):
  - Ler cabeçalhos de rate limit e aplicar **backoff exponencial**.
  - Implementar retentativas com limites seguros.

- **Inbound** (webhook do Trello):
  - O Trello reenvia **3 vezes** com backoff em caso de falha.
  - Evitar janelas de indisponibilidade; manter o endpoint estável.

- **Desativação Automática**:
  - Monitorar falhas e saúde do webhook para evitar desativação por 30 dias de erros consecutivos.

---

## 12. Operação e Provisionamento

- **Exposição pública**: usar túnel (ex.: ngrok) ou publicar via HTTPS.
- **Automação (Dinâmica por Board)**:
  - Hook no **fluxo de criação de Board**: após o `POST /1/boards` que cria o quadro, chamar **imediatamente** `POST /1/webhooks` com `idModel = idBoard`.
  - Job de **reconciliação periódico**: listar boards do Workspace (`GET /1/members/me/boards?fields=id,idOrganization,closed`), filtrar pelo Workspace e estado `closed=false`, e **criar webhooks ausentes**.
  - (Opcional) Sentinela do Workspace: registrar `idOrganization` apenas para monitorar mudanças administrativas.
  - Variáveis de ambiente: manter `.env` e atualizar `.env.example`.

---

## 13. Testes e Validação

- **Handshake**: teste `HEAD` e `GET` no `callbackURL`.
- **Fluxo principal**: enviar payload de exemplo de `moveCardToList` e verificar atualização de `etapa_atual` do atendimento.
- **Idempotência**: reenviar o mesmo evento e verificar que é ignorado.
- **Resiliência**: simular falha temporária e observar retentativas.
- **Cobertura mínima**: testes automatizados com `pytest` e execução via `uv run task test-docker`.

---

## 14. Exemplos de cURL

- **Criação de Webhook (Workspace)**:

```bash
curl -X POST "https://api.trello.com/1/webhooks" \
  -d key="${TRELLO_API_KEY}" \
  -d token="${TRELLO_TOKEN}" \
  -d callbackURL="${TRELLO_WEBHOOK_CALLBACK_URL}?secret=${TRELLO_WEBHOOK_SECRET}" \
  -d idModel="${TRELLO_WORKSPACE_ID}" \
  -d description="Webhook Global do Workspace Trello"
```

- **Criação de Webhook (Board)**:

```bash
curl -X POST "https://api.trello.com/1/webhooks" \
  -d key="${TRELLO_API_KEY}" \
  -d token="${TRELLO_TOKEN}" \
  -d callbackURL="${TRELLO_WEBHOOK_CALLBACK_URL}" \
  -d idModel="{ID_DO_BOARD}" \
  -d description="Webhook por Board"
```

- **Listar Webhooks do Token**:

```bash
curl "https://api.trello.com/1/tokens/${TRELLO_TOKEN}/webhooks?key=${TRELLO_API_KEY}&token=${TRELLO_TOKEN}"
```

- **Excluir Webhook**:

```bash
curl -X DELETE "https://api.trello.com/1/webhooks/${WEBHOOK_ID}?key=${TRELLO_API_KEY}&token=${TRELLO_TOKEN}"
```

---

## 15. Estratégia Dinâmica Recomendada (Resumo)

- **Use webhooks por Board** e registre-os **automaticamente** na criação de cada quadro do fluxo.
- **Mantenha um job de reconciliação** para garantir que nenhum quadro ativo do Workspace fique sem webhook.
- **Opcional**: mantenha um webhook de Workspace apenas como sentinela administrativa — não substitui o board webhook.
- Com isso, quadros criados dinamicamente e suas listas (etapas) ficam cobertos e os eventos de cards são entregues ao seu endpoint, sem necessidade de intervenção manual.

---

## 16. Considerações Finais

- Com **registro dinâmico por Board**, **roteador de ações**, **idempotência**, **segurança** e **resiliência**, o sistema mantém a sincronização correta das **etapas de atendimento**.
- A solução independe de **Custom Fields** e funciona integralmente no **plano gratuito** do Trello.


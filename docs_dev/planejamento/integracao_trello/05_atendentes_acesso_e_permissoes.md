# Atendentes: Acesso e Permissões no Trello

Este documento define a estratégia para controlar o acesso de atendentes
aos quadros (boards) do Trello via convites por e-mail, mapeando perfis
do sistema para permissões do Trello e descrevendo os endpoints oficiais
da API a serem utilizados.

## Objetivos

- Garantir acesso controlado dos atendentes somente aos quadros relevantes.
- Automatizar convites por e-mail e atualização de permissões.
- Manter rastreabilidade (log/auditoria) do ciclo de vida do acesso.

## Regras de cadastro (sistema → Trello)

- `Atendente` deve informar obrigatoriamente:
  - `email` (corporativo) e
  - `fluxo` (`FluxoAtendimento`, que mapeia o quadro Trello).
- O `departamento` deve ser coerente com o `fluxo` selecionado.
- No ato do cadastramento, o sistema dispara o convite para o quadro do fluxo
  com tipo de membro `normal`.

## Princípios de desenho

- Controle no nível de quadro (board), por fluxo de atendimento.
- Convite via e-mail do atendente (não armazenar senhas, somente e-mail).
- Mapeamento claro de papéis do sistema para tipos de membro do Trello.
- Remoção automática de acesso quando o atendente for desvinculado.

## Mapeamento de perfis → Trello

- Supervisor de Fluxo → `admin` no quadro (acesso total via conta institucional).
- Atendente (operacional) → `normal` no quadro.

Observação: não haverá perfil de observador no escopo atual.

## Fluxo de acesso (alto nível)

 1. Cadastro do atendente com `fluxo` obrigatório:
   - Se o fluxo já possuir quadro Trello, convidar o atendente por e-mail (guest `normal`).
   - Após aceite, ajustar o `member type` conforme perfil (admin/normal).
2. Desvincular atendente do fluxo:
   - Remover a associação do quadro no Trello.
3. Inativar atendente no sistema:
   - Remover associação dos quadros de todos os fluxos ativos.

## Endpoints oficiais (Boards → Membros)

- Convidar membro por e-mail para o quadro:
  - `PUT /1/boards/{id}/members?email={email}&key={key}&token={token}`
  - Body (JSON): `{ "fullName": "Nome Completo" }`
  - Referência: API de Boards. [1]

- Definir tipo de membro (por id do membro):
  - `PUT /1/boards/{id}/members/{idMember}?type={admin|normal|observer}`
  - Referência: API de Boards. [1]

- Listar membros do quadro:
  - `GET /1/boards/{id}/members`
  - Referência: API de Boards. [1]

- Listar memberships (inclui estado e tipo):
  - `GET /1/boards/{id}/memberships`
  - Referência: API de Boards. [1]

- Remover membro do quadro:
  - `DELETE /1/boards/{id}/members/{idMember}`
  - Referência: API de Boards. [1]

> Observações importantes:
> - Convite por e-mail não recebe `type` diretamente em todos os cenários;
>   após aceite, use o endpoint de `members/{idMember}` para ajustar tipo.
> - Recursos de `observer` exigem Trello Premium e podem ter limitações.
> - Apps com Forge/OAuth2 possuem restrições em alguns endpoints. [1]

## Modelo de dados sugerido (persistência interna)

- `TrelloMember` (por fluxo/quadro):
  - `id` (interno)
  - `id_board` (str)
  - `id_member` (str, Trello)
  - `email` (str)
  - `full_name` (str)
  - `member_type` (enum: admin|normal|observer)
  - `status` (enum: invited|accepted|removed)
  - `created_at` / `updated_at`

> Comentário: `status` pode ser inferido consultando `memberships`. Em
> convites pendentes, `members` pode não listar o usuário imediatamente; use
> `memberships` para verificar estado e tipo.

## Serviços e integração (proposta)

- Interface `UnifiedDataService` (métodos opcionais):
  - `invite_member_to_container_email(container_id, email, full_name)`
  - `set_container_member_type(container_id, member_id, member_type)`
  - `remove_container_member(container_id, member_id)`

- Adapter Trello:
  - Mapeia os métodos acima para os endpoints descritos.
  - Implementa verificação prévia (`GET /members`) para evitar duplicidades.
  - Após convite e aceite, ajusta `member_type` conforme perfil.

- `FlowSyncService`:
  - Na vinculação de atendente ao fluxo: chama `invite_*` e depois `set_*`.
  - Na desvinculação: chama `remove_*`.
  - Em inativação global: remove de todos os quadros ativos do atendente.

## Segurança e conformidade

- Nunca armazenar tokens em código; usar variáveis de ambiente.
- Registrar logs (com contexto: quadro, atendente, operação, resultado).
- Em erros de API (rate limits), aplicar fallback:
  - Convite duplicado → idempotência por checagem prévia de membros.
  - Re‑tentar com backoff exponencial quando aplicável.

Sem `observer`: todos os atendentes serão `normal` e supervisores `admin`.

## Endpoints Relevantes

- Convidar por e‑mail para um quadro: `PUT /1/boards/{id}/members?email={email}&key={key}&token={token}` com body `{ "fullName": "Nome Completo" }` [1].
- Definir tipo de membro (apenas `admin` e `normal`): `PUT /1/boards/{id}/members/{idMember}?type={admin|normal}` [1].
- Listar membros do quadro: `GET /1/boards/{id}/members` [1].
- Listar memberships (estado/tipo, útil para convite pendente): `GET /1/boards/{id}/memberships` [1].
- Remover membro: `DELETE /1/boards/{id}/members/{idMember}` [1].

Notas de viabilidade:
- Os convites por e‑mail são suportados e retornam memberships; pendências aparecem em `memberships`.
- O tipo `observer` depende de Trello Premium e está fora de escopo atual.
- Limites de taxa podem exigir backoff e registro de erros.

## Checklist de implementação

- [ ] Adicionar métodos opcionais de convite/remoção na interface de serviço.
- [ ] Implementar endpoints no adapter Trello.
- [ ] Integrar com `FlowSyncService` nas operações de cadastro (convite imediato)
      e vincular/desvincular.
- [ ] Persistir `TrelloMember` por fluxo/quadro e manter `member_type`.
- [ ] Logs e auditoria de convites, aceitações e remoções.

## Referências

- [1] Trello REST API – Boards (membros e convites)
  https://developer.atlassian.com/cloud/trello/rest/api-group-boards/

- [2] Observers (permissão de membro em Workspace Premium)
  https://support.atlassian.com/trello/docs/adding-observers-to-boards/
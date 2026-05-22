# Final Review — refatoracao-modular-atendimento
Data: 2026-05-22 · Modelo: Opus · Escopo: 4 módulos da refatoração

## Veredito: CORRIGIDO (qualidade) — porém ciclo INCOMPLETO → NÃO ARQUIVAR
A implementação avançou além do snapshot de 60% do plano (F2/F3 backend essencialmente
movidos, design system criado, coordinator criado). Foram encontrados e corrigidos
desvios reais: import cruzado proibido `chat_evolution → gestao_kanban`, função de chat
mal posicionada num service do kanban, `export` ES em script clássico (quebraria os
stores Alpine) e um bloco de comentário-monólogo (código morto). Lint e type-check ficam
limpos no escopo após as correções.

**Decisão de arquivamento:** as fases F4V, F5 e F6 (+ validações F1V/F2V/F3V) seguem
`pending`. Pela pré-condição de completude do gate, o plano **não é arquivado** — este
relatório é um checkpoint de qualidade do trabalho parcial. O ciclo só fecha após F4–F6.

## 1. Plano vs. Implementado

| Fase | Status | Observação |
|------|--------|------------|
| F1 — Design System (componentes + core_alpine.js + tokens v4) | ✅ feito conforme | `core.css` consolidado; 9 componentes em `templates/components/`; `core_alpine.js` com stores `notifications`/`modal` e diretiva `format-date` em `alpine:init`. (Bug de `export` corrigido — ver §2.) |
| F1V — Validação Design System | ❌ pendente | Validação manual de render não executada (fase V do plano). |
| F2 — chat_evolution (views/selectors/signals + front) | ⚠️ feito com desvio | `views_api.py`, `selectors.py`, `signals.py` movidos; `apps.ready()` carrega signals; `api_urls.py` usa `from . import views_api`. Desvios corrigidos: import cruzado e código morto (§2). `chat_alpine.js` ainda é mixin (`window.workspaceChatMixin`) e não `Alpine.data('chat')` — aceitável pois F4 (integração) está pendente. |
| F2V — Validação chat_evolution + Evolution Go | ❌ pendente | Validação manual de endpoints/envio/markRead não executada. |
| F3 — gestao_kanban (views/selectors/signals + SortableJS) | ✅ feito conforme | `views_api.py`/`selectors.py`/`signals.py` movidos; `apps.ready()` OK; SortableJS instanciado e sincroniza via recarga (`loadBoard()` no `onEnd`), alternativa válida ao `splice`. |
| F3V — Validação gestao_kanban + drag-drop | ❌ pendente | Validação manual não executada. |
| F4 — Integração UI Shell (coordinator + ordem de assets) | ⚠️ parcial / pendente | `workspace_coordinator.js` criado e correto (registra em `alpine:init`, escuta `card:clicked`/`chat:closed` com `.window`). Ordem de assets em `workspace.html` carrega módulos antes do Alpine core (`base.html` defer) — ordem correta. Redução do `workspace_alpine.js` ainda não concluída. Marcado pending no plano. |
| F4V — Validação integração + SSE único | ❌ pendente | — |
| F5 — Limpeza do monolito | ➕/⚠️ parcialmente antecipado | `selectors.py`, `signals.py`, `views_api.py` JÁ removidos do monolito (status git `D`), antecipando F5 antes de F4V. Risco baixo (imports repontados), mas fora da ordem PREVC planejada. |
| F6 — Build produção Tailwind v4 + deploy | ❌ pendente | CDN `@tailwindcss/browser` ainda em `core/templates/base.html` (dev-only); build CLI/PostCSS não feito. |

Notas de conformidade verificadas (OK):
- Import canônico de `atendimentos.models` em selectors/signals/services; `models.py` dos apps permanecem docstring-only. Nenhum `managed=False`/proxy/`db_table="atu_*"` reintroduzido.
- SSE único respeitado: nenhum app criou `views_sse.py`; signals publicam `type` `chat.*`/`kanban.*` via `realtime_publisher.publish_event`.
- Multi-tenant: filtros por atendente/fluxo/owner; `get_current_tenant_slug()` no signal de chat.
- Sem secrets hardcoded; `csrf_protect` nas views de escrita; validação de input nas views.
- `select_related`/`prefetch_related` presentes nas queries de listagem.

## 2. Correções Aplicadas

| Arquivo:linha | Problema | Correção |
|---------------|----------|----------|
| `chat_evolution/views_api.py:27-32` (orig.) | **Import cruzado proibido** `chat_evolution → gestao_kanban` (`list_fluxos_acessiveis` de `gestao_kanban.selectors` e `mark_read` de `gestao_kanban.services.board_service`). Viola §2.4 do plano ("zero import entre chat_evolution e gestao_kanban"). | `mark_read` movido para `chat_evolution/services/message_dispatch_service.py`; `list_fluxos_acessiveis` adicionado a `chat_evolution/selectors.py` (usa `operacional.models`, app neutro). Imports do views_api repontados para locais. **Zero import cruzado restante** (verificado por grep nos dois sentidos). |
| `gestao_kanban/services/board_service.py:172-303` | `mark_read` + `_dispatch_evolution_markread` (lógica 100% de chat: `Mensagem`, Evolution markread) residiam num service do kanban — feature envy / responsabilidade trocada. | Removidos do board_service e movidos para `message_dispatch_service.py` (domínio chat). Import `Any` (agora não usado) removido. |
| `evolution_sync/signals.py:262` | Import de `_dispatch_evolution_markread` apontava para `gestao_kanban.services.board_service` (quebraria após a movimentação acima). Arquivo fora do escopo, mas a quebra é consequência da correção. | Repontado para `chat_evolution.services.message_dispatch_service`. Validado com `django.setup()` + import (IMPORTS_OK, sem ciclo). |
| `chat_evolution/views_api.py` (ConversationMediasView, ~451-468) | **Código morto**: bloco de ~18 linhas de comentário-monólogo de desenvolvimento ("Vamos ver se...", "Espera, vamos..."). | Removido; mantida apenas a linha funcional `from .selectors import list_medias`. |
| `modules/design_system/static/js/core_alpine.js:53,62` | **Bug**: `export function formatPhone/debounce` em arquivo carregado como script CLÁSSICO (`<script src=...>` sem `type="module"` em workspace.html:416). `export` em script clássico = SyntaxError que aborta o arquivo inteiro → `Alpine.store('notifications'/'modal')` e a diretiva `format-date` NUNCA registrariam. Helpers não são importados por ninguém. | Envolvido em IIFE; `export` removido; helpers expostos em `window.DesignSystem`. Comentário de aviso adicionado. |

Revalidação intermediária: `ruff check` limpo nos arquivos tocados; `task type-check` sem `error:` no escopo.

## 3. Decisões Autônomas (revisar depois)

1. **`list_fluxos_acessiveis` duplicado em chat_evolution.** Para eliminar o import cruzado, a função foi recriada em `chat_evolution/selectors.py` (cópia da de `gestao_kanban/selectors.py`, que continua servindo kanban e o shell). Há leve duplicação de uma query de leitura de fluxos. Alternativa futura mais limpa: mover esse helper de acesso a um módulo neutro (ex.: shell `atendimento_unificado` ou `operacional`) consumido pelos três (shell + chat + kanban). Não feito agora para não tocar a fiação do shell fora do ciclo.
2. **`mark_read` realocado para `message_dispatch_service`** (e não para um novo `read_service`). Mantém o número de arquivos baixo e fica no domínio chat. Revisar se preferirem um service dedicado de leitura.
3. **Repontamento em `evolution_sync/signals.py`** (fora dos 4 diretórios) foi feito por ser consequência direta da movimentação de `_dispatch_evolution_markread` — sem ele o app quebraria em runtime.

## 4. Revalidação

- lint (`uv run task lint`): ✅ no escopo. `ruff check` dos 4 diretórios = "All checks passed!". Run completo termina exit 0; as **25 errors** remanescentes são todas fora de escopo (`modules/services/.../notion_adapter.py`, `trello_adapter.py` — F841 unused var), pré-existentes e não tocadas.
- type-check (`uv run task type-check`): ✅ no escopo. Zero linhas `error:` nos arquivos dos 4 diretórios (apenas warnings de atributo dinâmico do Django, suprimidos pelos cabeçalhos `# pyright:` dos arquivos). Os ~1947 errors do run completo são todos em `tests/...` e no `core/urls.py` (unused-import pré-existente) — fora de escopo. Sanidade de import sob `django.setup()`: `IMPORTS_OK`.

## 5. Pendências (fases não concluídas + itens fora de escopo)

Fases pendentes (esperado, ~60% → agora um pouco além):
- F1V, F2V, F3V, F4V: validações manuais não executadas.
- F4: reduzir `workspace_alpine.js` (remover lógica de chat/kanban migrada) e finalizar o split dos mixins para `Alpine.data` dedicados.
- F5: limpeza completa do monolito (CSS de chat/kanban em `workspace.css`, partials legados). Parcialmente antecipada (selectors/signals/views já removidos).
- F6: build de produção Tailwind v4 (remover CDN `@tailwindcss/browser` de `core/templates/base.html`, gerar CSS estático via CLI/PostCSS) + deploy.

Itens fora de escopo (NÃO corrigidos — apenas registrados):
- 25 erros de lint (F841 unused var) em `modules/services/features/unifield_data_services/datasource/notion_adapter.py` e `trello_adapter.py`.
- `core/urls.py:23` — `reportUnusedImport` de `tenant_admin` (type-check).
- Grande volume de erros de type-check em `tests/**` (fora do escopo de produção e da diretriz "não criar testes").

## 6. Contradição de estado (status.yaml vs plano)

- `.context/plans/refatoracao-modular-atendimento.md` (frontmatter): `status: in_progress`, `progress: 60`, com F4/F5/F6 e todas as validações `pending`.
- `.context/workflow/status.yaml`: P, R, E = `completed`; **V = `in_progress`**; C = `pending`. (Observação: a instrução da tarefa afirmava que "todas as fases PREVC estão completed" — isso NÃO corresponde ao arquivo lido: V está in_progress e C pending.)

Contradição real: o `status.yaml` marca a fase **E (Execução) como `completed`** em 2026-05-22T13:07, enquanto o plano declara F2/F3/F4/F5/F6 ainda parcial/`pending` e progresso 60%. Ou seja, o workflow considera a Execução encerrada e está na Validação (V), mas o plano de fases mostra execução incompleta. Recomenda-se reconciliar: ou reabrir E até F4/F5/F6 fecharem, ou redefinir o escopo de E para "backend movido" e tratar F4–F6 como um ciclo PREVC subsequente. O gate C não deve fechar enquanto F4V/F5/F6 não forem concluídas e validadas.

---

Veredito: CORRIGIDO

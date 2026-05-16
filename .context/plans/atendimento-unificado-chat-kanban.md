---
status: ready
progress: 0
generated: 2026-05-14
source: "docs_dev/planejamento/atendimento_unificado/a-usabilidade-do-sistema-stateful-allen.md"
workflow: "atendimento-unificado-chat-kanban"
scale: "Large"
agents:
  - type: "architect-specialist"
    role: "Validar decisões arquiteturais (SSE/ASGI, multi-tenant, reuso radical de EtapaFluxo/Atendimento)"
  - type: "backend-specialist"
    role: "Implementar app atendimento_unificado, services, endpoints JSON e signals"
  - type: "database-specialist"
    role: "Modelar CampoPersonalizado e ValorCampoAtendimento, migrations e índices GIN"
  - type: "frontend-specialist"
    role: "Construir templates Tailwind+Alpine seguindo o Design System estabelecido"
  - type: "feature-developer"
    role: "Implementar feature LLM extracao_campos (DDD/Result Pattern) e integração com analise_mensage"
  - type: "code-reviewer"
    role: "Revisar aderência ao padrão arquitetural, type hints e segurança multi-tenant"
  - type: "security-auditor"
    role: "Auditar autorização nas rotas, isolamento tenant em SSE e tratamento de uploads"
  - type: "devops-specialist"
    role: "Configurar Uvicorn worker, criar tag/release e acompanhar deploy automático via GitHub Actions"
docs:
  - "architecture.md"
  - "data-flow.md"
  - "security.md"
  - "development-workflow.md"
  - "glossary.md"
phases:
  - id: "phase-P"
    name: "Planejamento e Decisões Arquiteturais"
    prevc: "P"
    agent: "architect-specialist"
    steps:
      - "Consolidar decisões arquiteturais (SSE via async views, reuso de models, Trello como espelho)"
      - "Mapear Design System (cores, tipografia, padrões de cards/forms/badges)"
      - "Definir contratos de endpoints JSON e formato de eventos SSE"
      - "Identificar ajustes ao planejamento original (não-lidos, send_media, ASGI)"
  - id: "phase-R"
    name: "Revisão e Aprovação do Plano"
    prevc: "R"
    agent: "code-reviewer"
    steps:
      - "Revisar plano com architect-specialist, frontend-specialist e database-specialist"
      - "Confirmar reuso de EtapaFluxo/Atendimento sem criar Coluna/Card novos"
      - "Validar canal Redis por tenant e formato de eventos SSE"
      - "Aprovar Design System mapeado a partir de base_dashboard.html"
  - id: "phase-E"
    name: "Execução (3 sub-fases sequenciais)"
    prevc: "E"
    agent: "backend-specialist"
    steps:
      - "E.1 — MVP Chat + Kanban (esforço G): app novo, models reutilizados, endpoints, SSE, templates"
      - "E.2 — Campos Personalizados + Extração IA (esforço G): models novos, feature extracao_campos, injeção no prompt, sync Trello"
      - "E.3 — Refinamentos (esforço M): drag-drop, filtros, não-lidos dedicado, mídia outbound, export CSV"
  - id: "phase-V"
    name: "Validação Ponta a Ponta"
    prevc: "V"
    agent: "code-reviewer"
    steps:
      - "Verificação manual conforme roteiro de validação (3 sub-roteiros, um por sub-fase)"
      - "Rodar ruff format + ruff check + pyright em modo strict"
      - "Validar isolamento multi-tenant em SSE (2 tenants simultâneos)"
      - "Testar carga: 50 conversas + 1000 mensagens < 500ms"
  - id: "phase-C"
    name: "Encerramento, Release e Deploy em Produção"
    prevc: "C"
    agent: "documentation-writer"
    steps:
      - "Atualizar architecture.md, data-flow.md, glossary.md e Nginx (proxy_buffering off)"
      - "Merge feature branch em master + bump semver MINOR + CHANGELOG"
      - "Criar tag v<X.Y.Z> e push para disparar .github/workflows/deploy.yml automaticamente"
      - "Healthcheck pós-deploy: containers Up, logs limpos no GHA"
      - "Habilitar feature flag ATENDIMENTO_UNIFICADO_ENABLED em 1 tenant piloto, observar 24h"
      - "Rollout gradual nos demais tenants (1 a 1, intervalo 4h)"
      - "Arquivar plano e registrar lessons learned"
lastUpdated: "2026-05-15T14:07:00.417Z"
---

# Atendimento Unificado — Chat WhatsApp + Kanban + Campos Personalizados

> Construir o módulo `atendimento_unificado`: tela única com chat estilo WhatsApp Web e modo Kanban sobre `EtapaFluxo`/`Atendimento`, com campos personalizados híbridos (globais por tenant + por fluxo) extraídos automaticamente pela IA e reinjetados no system prompt do bot. Real-time via SSE sobre Redis pub/sub. Trello permanece como espelho passivo. Entrega faseada em 3 sub-fases de execução (MVP → Campos+IA → Refinamentos).

## Task Snapshot

- **Primary goal:** Eliminar o cenário "tela do Trello + WhatsApp Web em abas separadas" — operadores trabalham em **uma única tela** que combina pipeline Kanban e atendimento via chat, com dados estruturados extraídos pelo bot e enriquecendo respostas futuras.
- **Success signal:** Operador acessa `/workspace/`, vê suas conversas e o kanban do seu departamento. Envia mensagem pelo composer e ela chega no WhatsApp do contato. Move card no kanban e a etapa é atualizada no Atendimento. Bot extrai CNPJ/tipo de produto da conversa e essas informações aparecem como campos no painel direito e como contexto no próximo prompt do bot. Tudo isso sem polling — atualizações em tempo real via SSE.
- **Key references:**
  - [Planejamento Original](../../docs_dev/planejamento/atendimento_unificado/a-usabilidade-do-sistema-stateful-allen.md)
  - [Arquitetura](../docs/architecture.md)
  - [Fluxo de Dados](../docs/data-flow.md)
  - [Segurança](../docs/security.md)
  - [Glossário](../docs/glossary.md)

## Codebase Context

### Modelos Existentes Reutilizados (Fase E.1 — NENHUM model novo)

| Necessidade | Reuso |
|---|---|
| Coluna kanban | [`EtapaFluxo`](../../src/smart_core_assistant_painel/app/operacional/models.py) (já tem `cor`, `ordem`, `tipo_etapa`) |
| Card kanban | [`Atendimento.etapa_atual`](../../src/smart_core_assistant_painel/app/atendimentos/models.py) |
| Mover card | `MovimentoFluxo.criar_movimento(...)` (atualiza `etapa_atual` + histórico) |
| Mensagens chat | [`Mensagem`](../../src/smart_core_assistant_painel/app/atendimentos/models.py) |
| Envio WhatsApp | Signal `_on_message_saved` em [evolution_sync/signals.py:216](../../src/smart_core_assistant_painel/app/evolution_sync/signals.py#L216) |
| Lista conversas | `Atendimento` ordenado por `data_ultima_mensagem` (já indexado) |

### Arquivos Centrais (a criar e editar)

**Criar (E.1)**:
- `src/smart_core_assistant_painel/app/atendimento_unificado/` (app novo completo)

**Editar (E.1)**:
- [core/settings.py](../../src/smart_core_assistant_painel/app/core/settings.py) — `INSTALLED_APPS`
- [tenants/db_router.py](../../src/smart_core_assistant_painel/app/tenants/db_router.py) — `TENANT_APPS`
- [core/asgi.py](../../src/smart_core_assistant_painel/app/core/asgi.py) — sem mudança (Django async view nativa)

**Criar (E.2)**:
- `atendimento_unificado/models.py` — `CampoPersonalizado`, `ValorCampoAtendimento`
- `src/smart_core_assistant_painel/modules/ai_engine/features/extracao_campos/` (feature DDD)

**Editar (E.2)** — APENAS no `modules/ai_engine` (infra compartilhada de IA, fora dos `app/`):
- [analise_mensage_datasource.py](../../src/smart_core_assistant_painel/modules/ai_engine/features/analise_mensage/datasource/analise_mensage_datasource.py) — injetar campos no system prompt **lendo de `AnaliseMensageParameters.campos_coletados`** (sem que `analise_mensage` saiba sobre `CampoPersonalizado`)
- [ai_engine/utils/parameters.py](../../src/smart_core_assistant_painel/modules/ai_engine/utils/parameters.py) — adicionar `campos_coletados`/`campos_pendentes` em `AnaliseMensageParameters` e criar `ExtracaoCamposParameters`
- [ai_engine/utils/erros.py](../../src/smart_core_assistant_painel/modules/ai_engine/utils/erros.py) — `ExtracaoCamposError`
- [ai_engine/features/features_compose.py](../../src/smart_core_assistant_painel/modules/ai_engine/features/features_compose.py) — método `extracao_campos`

**NÃO editar nenhum app de produção em `app/`** (substituído por signals/tasks em `atendimento_unificado/`):
- ~~[atendimentos/services/attendance_orchestrator.py](../../src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py)~~ — disparo da task de extração vem de signal `post_save Mensagem` em `atendimento_unificado/signals.py` (E.2.7).
- ~~[trello_sync/services/ticket_sync_service.py](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py)~~ — espelhamento de campos no Trello foi **DROPADO** (decisão D5). Workspace é a única fonte de visualização de campos personalizados.
- ~~[atendimentos/models.py](../../src/smart_core_assistant_painel/app/atendimentos/models.py)~~ — não-lidos via model próprio `LeituraAtendimento` em `atendimento_unificado/models.py` (decisão D4). Zero alteração em `Atendimento`.

## Decisões Arquiteturais Consolidadas

1. **Reuso radical**: `EtapaFluxo` JÁ É "coluna kanban", `Atendimento.etapa_atual` JÁ É "card". Não criar `Coluna`/`Card` novos.
2. **App novo `atendimento_unificado`** é camada fina de UI + orquestração; lógica de negócio fica nos models/services existentes.
3. **DDD/Result Pattern só onde toca IA**: feature de extração em `modules/ai_engine/features/extracao_campos/` segue o padrão de `analise_mensage`/`transcribe_audio`/`interpret_media`.
4. **SSE via Django async views** (Django 4.1+ suporta `StreamingHttpResponse` async nativo) — **não precisa Channels**, **não precisa rota ASGI separada**. `core/asgi.py` permanece intacto.
5. **Atendente envia mensagem criando `Mensagem(remetente=ATENDENTE_HUMANO)`** — o signal existente em [evolution_sync/signals.py:216](../../src/smart_core_assistant_painel/app/evolution_sync/signals.py#L216) cuida do envio via `EvolutionWhatsAppService.send_message(...)`.
6. **Trello é espelho passivo** mas **paridade funcional total entre Kanban interno e Trello**: o Kanban interno precisa reproduzir TODA a lógica que hoje só existe no Trello (board por fluxo, status auto por tipo de etapa, assumir atendimento, finalização, cross-board move). Toda escrita nasce no painel e propaga via signals/tasks já existentes; nenhuma mudança de fluxo no `trello_sync`.
7. **Extração de campos é assíncrona pós-resposta** — não atrasa a UX do contato. Disparada via Celery task no `attendance_orchestrator`.
8. **Multi-tenant SSE**: canal Redis nomeado por tenant (`sse:{tenant_slug}:events`) para evitar vazamento cross-tenant.

---

## Lógica do Trello a Espelhar no Kanban Interno (Paridade Funcional)

> Esta seção foi extraída de [trello_sync/signals.py](../../src/smart_core_assistant_painel/app/trello_sync/signals.py) e [trello_sync/services/ticket_sync_service.py](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py) — **toda regra abaixo precisa funcionar igual no Workspace**.

### Mapeamento de Entidades

| Conceito Trello | Modelo Trello | Conceito Painel | Modelo Painel |
|---|---|---|---|
| Board | `TrelloBoard` | **Quadro** (board interno) | `FluxoAtendimento` (1:1 com `TrelloBoard`) |
| List/Column | `TrelloList` | **Coluna** | `EtapaFluxo` (1:1 com `TrelloList`) |
| Card | `TrelloCard` | **Card** | `Atendimento` (1:1 com `TrelloCard`) |
| Member | `TrelloMember` | **Atendente** | `Atendente` (1:1 com `TrelloMember`) |

**Implicação crítica**: **cada `FluxoAtendimento` é um quadro independente** (não cada departamento). Um departamento pode ter múltiplos fluxos = múltiplos quadros. O seletor do Workspace deve ser **por `FluxoAtendimento`**, não por departamento.

### Estrutura de Etapas (regras fixas)

Cada coluna (`EtapaFluxo`) tem um `tipo_etapa` que dispara comportamento automático:

| `TipoEtapa` | Comportamento ao mover card pra cá | Status Atendimento resultante |
|---|---|---|
| `FILA` | Atendimento entra em fila, sem atendente atribuído | `StatusAtendimento.FILA` |
| `TRABALHO` | **Assumir atendimento**: atribui `atendente_humano` ao usuário que moveu + dispara saudação automática via `Atendimento.transferir_para_humano_com_saudacao` | `StatusAtendimento.EM_ATENDIMENTO` |
| `ESPERA` | Atendimento aguardando algo (cliente, pagamento, etc.) | `StatusAtendimento.PENDENCIA` |
| `FINALIZACAO` | **Encerra atendimento**: chama `Atendimento.finalizar_atendimento(novo_status, solicitar_feedback=False)`. Se nome da etapa contém "cancel" → `CANCELADO`, senão → `RESOLVIDO` | `StatusAtendimento.RESOLVIDO` ou `CANCELADO` |

### Conteúdo Visual do Card (espelhar `_build_card_name` + `_build_rich_description`)

**Título do card** ([ticket_sync_service.py:245-327](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L245)):
```
{nome_contato} - {nome_fantasia_cliente} - {assunto} - {intents[0..3]}
```
Cada parte é omitida se vazia. Nome do contato limitado a 40 chars.

**Conteúdo rico do card** ([ticket_sync_service.py:329-573](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L329)):
- Header: `{emoji_status} Atendimento #{pk}` + assunto + canal (emoji)
- **Info do contato**: nome, telefone, e-mail
- **Métricas**: tempo total (humanizado: "há X dias/horas/min"), última interação, atendente atribuído
- **Tags** (se houver)
- **Análise IA**: intents detectados + entidades extraídas (top 5 cada)
- **Mensagens recentes**: últimas 10, com ícone por remetente (👤 cliente / 🤖 bot / 👨‍💻 atendente), ícone por mídia (🎤🖼️🎬📄), tempo humanizado, conteúdo + resposta_bot

**Labels (prioridade)**:
| Prioridade | Cor | Tailwind sugerido |
|---|---|---|
| `baixa` | green | `bg-green-100 text-green-800` |
| `normal` | blue | `bg-blue-100 text-blue-800` |
| `alta` | orange | `bg-orange-100 text-orange-800` |
| `urgente` | red | `bg-red-100 text-red-800` |

**Datas**: `start = data_inicio`, `due = data_inicio + 1 dia` (fallback `data_ultima_mensagem + 1 dia`).

### Cross-Board Move (mover entre quadros = mudar fluxo)

Quando o usuário arrasta um card para uma coluna de **outro quadro** ([ticket_sync_service.py:794-833](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L794)):
1. Atualizar `atendimento.fluxo_atendimento_id` para o fluxo de destino.
2. Atualizar `atendimento.departamento_id` para `novo_fluxo.departamento_id`.
3. Criar `MovimentoFluxo.criar_movimento(...)` com a nova etapa.
4. Aplicar regras de `tipo_etapa` da nova coluna (FILA/TRABALHO/ESPERA/FINALIZACAO).

**No Workspace**: a UI deve permitir mover card entre quadros (multi-board view ou modal de movimentação). MVP pode restringir à mesma "área" inicialmente, mas a API `/board/move/` precisa aceitar `etapa_destino_id` de qualquer fluxo.

### Comportamentos Especiais a Replicar

1. **Reordenação automática de listas** ([signals.py:78-81](../../src/smart_core_assistant_painel/app/trello_sync/signals.py#L78)) — `EtapaFluxo.ordem` deve refletir na ordem das colunas. Mudou `ordem` → reordena.
2. **Atribuição automática FILA→TRABALHO** ([ticket_sync_service.py:1046-1076](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L1046)) — quando o atendente move o card da fila para "Em Trabalho", o **atendente que moveu** vira `atendente_humano` E é enviada saudação automática via `transferir_para_humano_com_saudacao`.
3. **Finalização automática** ([ticket_sync_service.py:1079-1107](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L1079)) — qualquer move para etapa do tipo FINALIZACAO dispara `finalizar_atendimento`. Nome com "cancel" → CANCELADO; senão → RESOLVIDO.
4. **Status muda etapa automaticamente** ([trello_sync/signals.py:325-581](../../src/smart_core_assistant_painel/app/trello_sync/signals.py#L325)) — mudar `Atendimento.status` para RESOLVIDO/PENDENCIA/CANCELADO move o card para a etapa correspondente do fluxo (busca por `nome__iexact` ou `tipo_etapa`). **Este signal já existe** e funciona; o Workspace só precisa refletir via SSE.
5. **Sincronização de membro do card com `atendente_humano`** ([signals.py:173-197](../../src/smart_core_assistant_painel/app/trello_sync/signals.py#L173)) — mudou `atendente_humano` → card mostra o avatar do atendente. No Workspace: o card kanban mostra avatar/nome.
6. **Re-render do card a cada nova `Mensagem`** ([signals.py:644-680](../../src/smart_core_assistant_painel/app/trello_sync/signals.py#L644)) — preview no card precisa refletir última mensagem. No Workspace: card mostra preview da última mensagem (com tempo humanizado).
7. **Loop prevention** — flag `_syncing_from_trello` evita que signals do Trello disparem novos signals do Trello. Para o Workspace, não há esse problema (mesma origem), mas precisa atentar para evitar que mover via Workspace dispare task Trello que dispara novamente o Workspace.

### Acesso à Conversa Completa a Partir do Card

**Requisito do usuário**: clicar em qualquer card no Kanban abre a conversa completa, com possibilidade de enviar mensagens — mesma experiência do WhatsApp Web.

**Implementação**:
- **Modo Conversas**: layout 3 colunas (sidebar de conversas | chat | painel detalhes).
- **Modo Kanban**: layout 1 ou 2 colunas (kanban full-width OU kanban + painel detalhes).
- **Clicar em card no Kanban**: 2 opções (decidir na E.1):
  - **Opção A** (recomendada): abre **drawer/modal de chat** sobreposto sem sair do kanban, com mesmo composer e histórico do Modo Conversas. Fechar volta para o kanban.
  - **Opção B**: muda para Modo Conversas com aquela conversa selecionada. Mais simples mas perde contexto visual do kanban.

### Personalização do Card

Requisito do usuário: "será um Trello personalizável". Decisões sobre quais campos exibir no card:

- **Fase E.1 (MVP)**: card sempre exibe `título composto`, `prioridade (label)`, `atendente`, `preview última msg`, `tempo desde última msg`.
- **Fase E.2**: estender com `CampoPersonalizado.mostrar_no_card` (boolean já previsto no plano) — campos marcados aparecem no card como mini-chips/badges abaixo do preview.

---

## Ajustes ao Planejamento Original (identificados na fase P)

| # | Ponto Original | Ajuste / Confirmação | Motivo |
|---|---|---|---|
| 1 | "Roteamento ASGI dedicado, resto continua WSGI/Gunicorn" | **Usar Django async views nativas com `StreamingHttpResponse`** — não precisa de ASGI dedicado. | Django 4.1+ suporta async views diretamente. Reduz complexidade operacional; um único servidor pode atender SSE se rodar via Uvicorn/Daphne, ou Gunicorn com worker async (`uvicorn.workers.UvicornWorker`). |
| 2 | "Mídia outbound — se Evolution não tem `send_media`, adiar para Fase 3" | **Confirmado: `EvolutionWhatsAppService` em [evolution_api.py:94](../../src/smart_core_assistant_painel/app/evolution_sync/services/evolution_api.py#L94) tem APENAS `send_message` (texto via `/message/sendText`).** Mídia outbound **fica formalmente na E.3** e requer implementar `send_media` chamando `/message/sendMedia` da Evolution API. | Já validado — não há método de mídia outbound hoje. |
| 3 | "Não-lido (MVP) usa `mensagens.filter(remetente=CONTATO, respondida=False).count()`" | **Adicionar `Atendimento.data_ultima_leitura_atendente DateTimeField(null=True)` JÁ NA E.1** (não esperar E.3). | Campo `respondida` muda quando o bot/atendente responde, mas não reflete "atendente leu". Migration na E.1 evita refactor posterior. Custo desprezível (1 campo). |
| 4 | "Fase 2 modifica linhas 241-250 de `analise_mensage_datasource.py`" | Confirmar offset durante a E.2 — arquivo pode ter mudado após `feature-interpret-media`. | Plano original é de 2026-04. Code review da E.2 deve revalidar offsets. |
| 5 | Sem menção a Design System | **Adicionar seção dedicada (abaixo)** seguindo padrões de `base_dashboard.html` e `evolution_sync/templates/`. | Garante consistência visual com resto do painel. |
| 6 | Sem menção a permissões | **Toda rota deve verificar permissões via tags existentes** (`permission_tags.has_any_module_permission`, `can_view_module "atendimento"` — criar módulo se não existir). | Padrão multi-tenant do projeto. |

---

## Design System (referência: [base_dashboard.html](../../src/smart_core_assistant_painel/app/core/templates/base_dashboard.html))

### Paleta de Cores

| Token | Valor | Uso |
|---|---|---|
| `--color-gold-primary` | `#a98f71` | Acento principal (estados ativos, hover, foco) |
| `--color-gold-dark` | `#8b7355` | Acento secundário/hover do gold |
| `bg-[#1c1917]` | stone-900 | Sidebar fundo |
| `border-stone-800` | — | Sidebar bordas |
| `text-stone-400` / `text-stone-200` | — | Sidebar texto inativo / ativo |
| `bg-stone-50` | — | Fundo geral da página |
| `bg-white` | — | Cards e painéis principais |
| `border-stone-200` | — | Bordas suaves entre seções |
| `bg-green-50` + `text-green-600` | — | Ícone WhatsApp / status conectado |
| `bg-amber-50` + `border-amber-200` | — | Banners de aviso/configuração pendente |
| `bg-red-50` + `text-red-700` | — | Erros, ações destrutivas |
| `bg-[#a98f71]/10` + `text-[#a98f71]` | — | Item de sidebar ativo |

### Tipografia
- Fonte primária: **Outfit** (Google Fonts), pesos 300-700, carregada em `base.html`.
- `font-outfit` é a classe padrão no `<body>`.
- Tamanhos: `text-xs` (uppercase tracking-wider para labels), `text-sm` (corpo padrão), `text-xl font-bold` (títulos de card).

### Componentes Reutilizáveis (já em uso)

**Card padrão**:
```html
<div class="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden">
    <div class="px-6 py-4 border-b border-stone-100 bg-stone-50/50">
        <h2 class="text-xl font-bold text-stone-800 flex items-center">
            <span class="p-2 bg-{COLOR}-50 rounded-lg mr-3 text-{COLOR}-600">
                <svg class="w-6 h-6" .../>
            </span>
            Título
        </h2>
        <p class="mt-1 text-stone-500 text-sm ml-11">Subtítulo</p>
    </div>
    <div class="p-6"> <!-- conteúdo --> </div>
</div>
```

**Botão primário (WhatsApp green)**:
```html
<button class="px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center">
```

**Botão secundário**:
```html
<button class="px-3 py-2 text-sm border border-stone-300 text-stone-700 rounded-lg hover:bg-stone-50 transition-colors">
```

**Badge status conectado**:
```html
<div class="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 font-medium">
    <span class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span> Conectado
</div>
```

**Tabela**:
```html
<thead>
    <tr class="border-b border-stone-200">
        <th class="text-left py-3 px-4 text-xs font-semibold text-stone-500 uppercase tracking-wide">…</th>
    </tr>
</thead>
<tbody class="divide-y divide-stone-100">
    <tr class="hover:bg-stone-50/50 transition-colors">…</tr>
</tbody>
```

### Padrões Específicos do Workspace Unificado

1. **Sidebar de conversas** (col-1): inspirar-se na estrutura de [evolution_sync/templates/instance_list.html](../../src/smart_core_assistant_painel/app/evolution_sync/templates/evolution_sync/instance_list.html) — cards com hover suave, `divide-y divide-stone-100`, avatar circular `bg-[#a98f71] text-white` (mesmo padrão do bloco user-profile do sidebar global).
2. **Composer de mensagem** (col-2 base): borda superior `border-t border-stone-200`, fundo `bg-white`, textarea `border-stone-300 rounded-lg focus:ring-2 focus:ring-[#a98f71]/30`, botão envio `bg-green-600`.
3. **Bolhas de chat**:
   - Recebida (contato): `bg-stone-100 text-stone-800 rounded-2xl rounded-tl-sm`, alinhada à esquerda
   - Enviada (atendente/bot): `bg-[#a98f71]/10 text-stone-800 rounded-2xl rounded-tr-sm`, alinhada à direita
   - Metadata abaixo: `text-xs text-stone-400`
4. **Coluna Kanban**: container `bg-stone-100 rounded-xl p-3`, header da coluna com `cor` da `EtapaFluxo` em uma barra superior de 3px, cards = `bg-white rounded-lg shadow-sm border border-stone-200 p-3 hover:shadow transition-shadow`.
5. **Painel direito (detalhes)**: empilhamento de mini-cards com mesmo padrão (`bg-white rounded-xl shadow-sm border border-stone-200`), cada um com header compacto `px-4 py-3` e corpo `p-4`.
6. **Painel de campos personalizados (E.2)**: lista de pares label/valor com badge de origem (`BOT` em `bg-blue-50 text-blue-700`, `MANUAL` em `bg-stone-100 text-stone-700`), confiança como mini-barra `bg-green-500` (≥0.9), `bg-amber-500` (0.6-0.9), `bg-red-500` (<0.6).

### Entrada no Sidebar Global

Adicionar item ao [base_dashboard.html](../../src/smart_core_assistant_painel/app/core/templates/base_dashboard.html) entre "Treinamento IA" e "Gestão":

```html
{% can_view_module "atendimento" as can_atendimento %}
{% if is_owner or can_atendimento %}
<div class="pt-4 pb-2 px-3">
    <p class="text-xs font-semibold text-stone-500 uppercase tracking-wider">Atendimento</p>
</div>
<a href="{% url 'atendimento_unificado:workspace' %}"
    class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg {% if 'workspace' in request.path %}bg-[#a98f71]/10 text-[#a98f71]{% else %}text-stone-400 hover:text-stone-100 hover:bg-stone-800{% endif %} group transition-colors">
    <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
    Workspace
</a>
{% endif %}
```

---

## Working Phases

### Phase P — Planejamento e Decisões Arquiteturais
> **Primary Agent:** `architect-specialist` — [Playbook](../agents/architect-specialist.md)

**Objective:** Consolidar todas as decisões arquiteturais, ajustes ao planejamento original e o Design System em um documento aprovável.

**Tasks**

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| P.1 | Mapear decisões arquiteturais (SSE via async, reuso, Trello passivo) | `architect-specialist` | completed | Seção "Decisões Arquiteturais Consolidadas" neste plano |
| P.2 | Validar disponibilidade de ASGI e `send_media` | `architect-specialist` | completed | Tabela "Ajustes ao Planejamento Original" |
| P.3 | Extrair Design System de templates existentes | `frontend-specialist` | completed | Seção "Design System" neste plano |
| P.4 | Definir contratos de endpoints e formato de eventos SSE | `backend-specialist` | completed | Tabelas "Endpoints" e "SSE: Implementação" (em E.1) |

**Commit Checkpoint**: `chore(plan): consolidar plano atendimento_unificado e design system`

---

### Phase R — Revisão e Aprovação do Plano
> **Primary Agent:** `code-reviewer` — [Playbook](../agents/code-reviewer.md)

**Objective:** Revisão multi-disciplinar do plano antes de qualquer escrita de código.

**Tasks**

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| R.1 | Confirmar reuso de `EtapaFluxo`/`Atendimento` sem criar models novos na E.1 | `database-specialist` | pending | Aprovação registrada via `plan recordDecision` |
| R.2 | Aprovar formato dos eventos SSE e canal Redis por tenant | `architect-specialist` | pending | Aprovação registrada |
| R.3 | Aprovar Design System mapeado (cores, componentes, padrões de chat/kanban) | `frontend-specialist` | pending | Aprovação registrada |
| R.4 | Aprovar disparo Celery pós-resposta para extração + idempotência `select_for_update` | `feature-developer` | pending | Aprovação registrada |
| R.5 | Aprovar isolamento multi-tenant em SSE (`sse:{tenant_slug}:events`) e autorização por rota | `security-auditor` | pending | Aprovação registrada |
| R.6 | **Aprovar paridade funcional Trello ↔ Kanban interno**: regras `tipo_etapa`, cross-board, "assumir atendimento" com saudação automática, finalização automática, conteúdo visual do card | `architect-specialist` | pending | Aprovação registrada |
| R.7 | Aprovar opção A (drawer/modal de chat sobre o kanban) vs opção B (mudar para modo Conversas) ao clicar em card | `frontend-specialist` | pending | Decisão registrada via `plan recordDecision` |
| R.8 | Aprovar seletor por `FluxoAtendimento` (não departamento) no topbar do Workspace | `architect-specialist` | pending | Decisão registrada |

**Gate**: aprovação do usuário antes de E.1 (workflow LARGE requer `require_approval`).

**Commit Checkpoint**: `chore(plan): aprovar plano atendimento_unificado para execução`

---

### Phase E — Execução (3 sub-fases sequenciais)
> **Primary Agent:** `backend-specialist` — [Playbook](../agents/backend-specialist.md)

#### E.1 — MVP: Chat Unificado + Kanban com Paridade Trello (esforço **G+**)

**Objective:** Tela única onde o atendente atende conversas estilo WhatsApp Web E gerencia o pipeline em modo Kanban com **paridade funcional completa com o Trello**: board por `FluxoAtendimento`, status automático por `tipo_etapa`, assumir atendimento (FILA→TRABALHO + saudação), finalização (→FINALIZACAO), cross-board move, card visualmente equivalente ao card do Trello. Clicar em qualquer card abre o chat completo sem sair do kanban.

**Estrutura do app novo** (espelha layout de [trello_sync/](../../src/smart_core_assistant_painel/app/trello_sync/))
```
src/smart_core_assistant_painel/app/atendimento_unificado/
  __init__.py
  apps.py                            # AtendimentoUnificadoConfig com ready() que importa signals (padrão TrelloSyncConfig)
  admin.py                           # admin global (placeholder na E.1)
  tenant_admin.py                    # admin por tenant (E.2: CampoPersonalizadoAdmin)
  urls.py                            # rotas HTML
  api_urls.py                        # rotas JSON + SSE
  views.py                           # WorkspaceView (HTML shell)
  views_api.py                       # endpoints JSON
  views_sse.py                       # async view → StreamingHttpResponse
  selectors.py                       # queries (lista conversas, kanban snapshot)
  models.py                          # E.1 vazio; E.2 CampoPersonalizado + ValorCampoAtendimento
  signals.py                         # TODOS os receivers do app (publish SSE + orquestração cross-app)
  tasks.py                           # Celery tasks do app (E.2: extract_custom_fields_async)
  services/
    board_service.py                 # mover atendimento entre etapas
    message_dispatch_service.py      # criar Mensagem do atendente
    realtime_publisher.py            # publica eventos no Redis pub/sub
    card_renderer.py                 # payload visual do card (E.1.11)
  templates/atendimento_unificado/
    workspace.html                   # estende base_dashboard.html
    partials/conversation_item.html
    partials/chat_message.html       # variantes por TipoMensagem
    partials/kanban_column.html
    partials/kanban_card.html
    partials/detail_panel.html
    partials/chat_drawer.html        # drawer de chat sobre o kanban
    partials/custom_fields_panel.html  # placeholder na E.1
  static/atendimento_unificado/
    js/workspace_alpine.js           # store Alpine + EventSource
    css/workspace.css
  migrations/
    0001_initial.py                  # migration vazia + add data_ultima_leitura_atendente
```

**Convenção de `apps.py`** (espelha [trello_sync/apps.py](../../src/smart_core_assistant_painel/app/trello_sync/apps.py)):
```python
from django.apps import AppConfig


class AtendimentoUnificadoConfig(AppConfig):
    name: str = "smart_core_assistant_painel.app.atendimento_unificado"
    label: str = "atendimento_unificado"
    verbose_name: str = "Atendimento Unificado"

    def ready(self) -> None:
        # Comentário (PT-BR): Carrega sinais ao iniciar a app
        try:
            from . import signals as _signals  # noqa: F401
        except Exception as exc:
            # Evita falha de inicialização caso models ainda não migrados
            from loguru import logger

            logger.warning("Falha ao carregar sinais do atendimento_unificado: {}", exc)
```

**Princípio de independência total (não-negociável)** — refinado conforme decisão D4/D5/D6:

> **Nenhum app de produção em `src/smart_core_assistant_painel/app/` pode ser editado.** Toda integração acontece via signals e Celery tasks dentro de `atendimento_unificado/`.

**Exceções autorizadas (integrações inevitáveis, NÃO são lógica de negócio):**

| Arquivo | Motivo |
|---|---|
| [core/settings.py](../../src/smart_core_assistant_painel/app/core/settings.py) | Registro do app em `INSTALLED_APPS` (Django requer). |
| [tenants/db_router.py](../../src/smart_core_assistant_painel/app/tenants/db_router.py) | Registro do app em `TENANT_APPS` (multi-tenant requer). |
| [core/templates/base_dashboard.html](../../src/smart_core_assistant_painel/app/core/templates/base_dashboard.html) | Adicionar item de menu "Atendimento → Workspace" no sidebar global. É template compartilhado, não lógica. Explicitamente pedido pelo usuário. |
| [core/urls.py](../../src/smart_core_assistant_painel/app/core/urls.py) (ou raiz equivalente) | Incluir `path("workspace/", include("...atendimento_unificado.urls"))`. Registro de rotas. |

**Módulos fora de `app/` (autorizados a editar):**

| Módulo | Motivo |
|---|---|
| [modules/ai_engine/](../../src/smart_core_assistant_painel/modules/ai_engine/) | Infraestrutura compartilhada de IA, não é "app em produção" no sentido da regra. Edições controladas e isoladas em `parameters.py`, `erros.py`, `features_compose.py` e nova feature `extracao_campos/`. |

**Modelagem de dados que afeta tabelas legadas: PROIBIDA.** O que precisaria de campo em `Atendimento` (não-lidos) virou model próprio `LeituraAtendimento` em `atendimento_unificado/models.py` (decisão D4). O que precisaria de append no card Trello foi dropado (decisão D5). Todas as migrations do app criam apenas tabelas `atu_*` novas — nenhum `ALTER`/`DROP` em tabelas legadas.

Mesma direção de acoplamento adotada pelo `trello_sync` hoje (escuta signals de `Atendimento`/`Mensagem` sem que `atendimentos` saiba da existência do Trello). Decisões registradas via `plan recordDecision` na fase P.

**Models — ZERO alteração em apps de produção**

Em vez de adicionar campo a `Atendimento`, criar model próprio em [`atendimento_unificado/models.py`](../../src/smart_core_assistant_painel/app/atendimento_unificado/models.py) já na E.1:

```python
class LeituraAtendimento(models.Model):
    atendimento_id = models.BigIntegerField()  # FK lógica para Atendimento, sem constraint cross-app
    atendente_id = models.BigIntegerField()    # FK lógica para Atendente, sem constraint cross-app
    ultima_leitura_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "atu_leitura_atendimento"
        unique_together = [("atendimento_id", "atendente_id")]
        indexes = [
            models.Index(fields=["atendimento_id", "ultima_leitura_at"]),
        ]
```

Cálculo de não-lidos em `selectors.py`: para cada atendimento, conta `Mensagem.objects.filter(atendimento_id=..., remetente=CONTATO, timestamp__gt=LeituraAtendimento.ultima_leitura_at).count()`. O app `atendimentos` permanece 100% intocado.

**Tasks**

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| E.1.1 | Criar app `atendimento_unificado` (apps.py com `ready()` carregando signals, registrar em INSTALLED_APPS e TENANT_APPS) + permissão de módulo `atendimento` + **feature flag `ATENDIMENTO_UNIFICADO_ENABLED`** em `TenantConfig`/`RuntimeConfig` (default OFF). Sidebar e rotas `/workspace/*` só renderizam/respondem se flag True para o tenant. | `backend-specialist` | pending | App registrado, Django check passa, feature flag desligada por padrão |
| E.1.2 | Implementar `selectors.py`: `list_conversations`, `get_messages`, `board_snapshot_by_fluxo(fluxo_id)`, `list_fluxos_acessiveis(atendente)` | `backend-specialist` | pending | Funções tipadas com `pyright --strict` |
| E.1.3 | Implementar `services/message_dispatch_service.py` (cria Mensagem ATENDENTE_HUMANO seguindo padrão de `transferir_para_humano_com_saudacao`) | `backend-specialist` | pending | Service + teste manual: msg chega no WhatsApp |
| E.1.4 | Implementar `services/board_service.py::move_atendimento` espelhando lógica do Trello: `select_for_update`, `MovimentoFluxo.criar_movimento`, detectar cross-board (atualizar `fluxo_atendimento_id` + `departamento_id`), aplicar regra `tipo_etapa` (FILA→nada, TRABALHO→`transferir_para_humano_com_saudacao(atendente_id=request.user.atendente.id)`, ESPERA→nada, FINALIZACAO→`finalizar_atendimento`) | `backend-specialist` | pending | Mover entre quadros funciona; assumir da fila dispara saudação; finalização encerra |
| E.1.5 | Implementar `services/realtime_publisher.py` (wrapper Redis pub/sub, canal `sse:{tenant_slug}:events`) | `backend-specialist` | pending | Publish testado via redis-cli SUBSCRIBE |
| E.1.6 | Implementar `signals.py`: `post_save Mensagem` → `message.new`/`message.sent`; `MovimentoFluxo` post_save → `board.moved`; `Atendimento` post_save (status/atendente_humano/etapa) → `board.moved` (cobre o caso do signal Trello-existente alterar etapa quando status muda — Workspace precisa refletir) | `backend-specialist` | pending | Eventos saem para o canal do tenant em todas as mudanças relevantes |
| E.1.7 | Implementar `views_api.py` (endpoints JSON da tabela abaixo) com autorização por `LoginRequiredMixin` + `permission_tags` por rota | `backend-specialist` | pending | Endpoints retornam 200 com payload esperado; 403 sem permissão |
| E.1.8 | Implementar `views_sse.py` async view (`StreamingHttpResponse` async + heartbeat 25s + Redis `aioredis` subscribe), filtrando eventos por `tenant_slug` da request | `backend-specialist` | pending | EventSource conecta e recebe eventos do tenant correto |
| E.1.9 | Configurar Gunicorn com `uvicorn.workers.UvicornWorker` (ou processo Uvicorn dedicado) para suportar async views — atualizar Dockerfile/compose | `devops-specialist` | pending | Worker não trava em conexões longas; smoke test em prod |
| E.1.10 | **Criar model `LeituraAtendimento` em `atendimento_unificado/models.py` + migration `0001_initial.py`** (tabela própria `atu_leitura_atendimento` com `atendimento_id`/`atendente_id` BigIntegerField sem FK cross-app). ZERO alteração em `atendimentos`. | `database-specialist` | pending | Migration aplicada em produção; tabela `atu_leitura_atendimento` criada |
| E.1.11 | Implementar `services/card_renderer.py` que produz o **payload visual do card kanban** espelhando `_build_card_name` + dados de preview (título composto, prioridade, atendente, última msg preview, tempo humanizado, métricas, status emoji). Reutilizar helpers de [ticket_sync_service.py:180-244](../../src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py#L180) (`_get_status_emoji`, `_get_prioridade_emoji`, `_get_canal_emoji`, `_format_time_delta`) — mover para módulo compartilhado em `app/core/utils/` ou duplicar em `card_renderer.py` | `backend-specialist` | pending | Renderer testado com 3 cenários (sem atendente, com mídia, com intents) |
| E.1.12 | Implementar `WorkspaceView` + template `workspace.html` com **seletor de Fluxo** (combo no topbar) + tabs Alpine `Conversas`/`Kanban`. Layout: Conversas = 3 colunas (sidebar/chat/detalhes); Kanban = colunas horizontais full-width | `frontend-specialist` | pending | Layout renderiza dentro de base_dashboard, seletor de fluxo popula colunas |
| E.1.13 | Implementar partials seguindo Design System: `conversation_item.html`, `chat_message.html` (variantes contato/bot/atendente, mídia), `kanban_column.html` (barra de cor da etapa, contador, header com nome), `kanban_card.html` (espelha visual do card Trello: título, label de prioridade, avatar atendente, preview msg, tempo, badges custom da E.2), `detail_panel.html`, `chat_drawer.html` (drawer/modal de chat acionado ao clicar em card no Kanban) | `frontend-specialist` | pending | Partials seguem Design System; comparar visual com card Trello |
| E.1.14 | Implementar `workspace_alpine.js`: store global (`fluxoSelecionado`, `mode`, `conversations`, `activeConv`, `kanban` por etapa, `chatDrawerOpen`); handler `EventSource` que dispatch eventos para o store; método `openChat(atendimento_id)` que abre drawer | `frontend-specialist` | pending | Atualização ao vivo em 2 abas; clicar em card abre chat |
| E.1.15 | Adicionar entrada "Atendimento → Workspace" no sidebar global de `base_dashboard.html` (com permission tag `can_view_module "atendimento"`) | `frontend-specialist` | pending | Link visível conforme permissão, marca ativo |
| E.1.16 | Documentar configuração Nginx (`proxy_buffering off`, `proxy_read_timeout 1h` na rota `/workspace/events/`) + Dockerfile/compose com Uvicorn worker | `devops-specialist` | pending | Trecho nginx + compose em `.context/docs/` |
| E.1.17 | Testes manuais de paridade Trello (roteiro detalhado na fase V): assumir da fila, finalização, cross-board, mudança de status, etc. | `code-reviewer` | pending | Checklist marcado |

**Endpoints E.1**

| Rota | Verbo | Função |
|---|---|---|
| `/workspace/` | GET | `WorkspaceView` (HTML shell) — query `?fluxo=<id>` ou padrão (último usado, salvo em session) |
| `/workspace/api/fluxos/` | GET | Lista `FluxoAtendimento` acessíveis ao atendente (para o seletor) |
| `/workspace/api/conversations/` | GET | Sidebar (cursor por `data_ultima_mensagem`, filtro `?fluxo=<id>` opcional) |
| `/workspace/api/conversations/<id>/messages/` | GET | Histórico paginado |
| `/workspace/api/conversations/<id>/send/` | POST | Cria `Mensagem(ATENDENTE_HUMANO)` |
| `/workspace/api/conversations/<id>/mark-read/` | POST | Atualiza `data_ultima_leitura_atendente=now()` |
| `/workspace/api/conversations/<id>/detail/` | GET | Bloco rico (intents, entidades, métricas, tags) — payload do "card kanban" + extras |
| `/workspace/api/board/?fluxo=<id>` | GET | Snapshot Kanban: `[{etapa: {...}, cards: [{atendimento_id, render: {...}}]}]` |
| `/workspace/api/board/move/` | POST | `{atendimento_id, etapa_destino_id}` — service aplica regras `tipo_etapa` (FILA/TRABALHO/ESPERA/FINALIZACAO) e cross-board automaticamente |
| `/workspace/api/board/assign/` | POST | `{atendimento_id, atendente_id}` (override manual; FILA→TRABALHO via drag-drop usa o atendente do request) |
| `/workspace/events/` | GET (SSE) | Stream eventos do tenant atual |

**Formato dos cards no payload `/board/`**:
```json
{
  "etapas": [
    {"id": 12, "nome": "Em Trabalho", "cor": "#3B82F6", "tipo_etapa": "trabalho", "ordem": 2, "count": 5}
  ],
  "cards": {
    "12": [
      {
        "atendimento_id": 88,
        "titulo": "João Silva - Acme Comércio - Orçamento - solicitar_orcamento",
        "status": "em_atendimento",
        "status_emoji": "💬",
        "prioridade": "alta",
        "prioridade_label_class": "bg-orange-100 text-orange-800",
        "atendente": {"id": 4, "nome": "Maria"},
        "preview_msg": "Pode confirmar o endereço de entrega?",
        "preview_remetente": "CONTATO",
        "tempo_ultima_msg": "há 8 minutos",
        "data_ultima_mensagem": "2026-05-14T15:32:11Z",
        "canal_emoji": "📱",
        "tags": ["vip"],
        "campos_custom_card": []
      }
    ]
  }
}
```

**Formato SSE**:
```
event: message.new
data: {"atendimento_id": 42, "mensagem_id": 123, "remetente": "CONTATO", "preview": "Olá"}

: ping (heartbeat a cada 25s)
```

**Riscos E.1 e mitigações**
1. **Gunicorn sync worker trava em SSE** → usar `uvicorn.workers.UvicornWorker` ou rodar Uvicorn dedicado para `/workspace/events/`.
2. **Concorrência mover-card** → `select_for_update` no `Atendimento` durante `move_atendimento`.
3. **Multi-tenant SSE vazamento** → canal Redis nomeado por tenant; teste com 2 tenants simultâneos na V.

---

#### E.2 — Campos Personalizados + Extração pelo Bot (esforço **G**)

**Objective:** Bot extrai automaticamente dados estruturados das mensagens, persiste como `ValorCampoAtendimento`, e os reinjeta no system prompt das próximas respostas. Atendente pode editar manualmente no painel direito.

**Models novos em `atendimento_unificado/models.py`**

`CampoPersonalizado`:
- `slug` SlugField(64)
- `nome` CharField(120)
- `descricao` TextField — também é hint de extração
- `escopo` CharField choices `GLOBAL`/`FLUXO`
- `fluxo` FK → `operacional.FluxoAtendimento` (null se GLOBAL)
- `tipo` choices: `texto`, `numero`, `data`, `escolha`, `multipla_escolha`, `booleano`
- `opcoes` JSONField (lista — para escolha/multipla)
- `obrigatorio` BooleanField
- `extrair_automaticamente` BooleanField(default=True)
- `extrair_hint` CharField(500, blank=True)
- `mostrar_no_card_trello` BooleanField(default=True)
- `ordem`, `ativo`, `data_criacao`, `data_atualizacao`
- Meta: `unique_together=[("slug","escopo","fluxo")]`, indexes `(escopo, fluxo, ativo)` e `(extrair_automaticamente,)`
- `db_table = "atu_campo_personalizado"`

`ValorCampoAtendimento`:
- `atendimento` FK → `Atendimento` (related=`valores_campos`)
- `campo` FK → `CampoPersonalizado`
- `valor` JSONField
- `origem` choices `MANUAL`/`BOT`/`IMPORT`
- `confianca` FloatField (null) — populado quando `BOT`
- `mensagem_origem` FK → `Mensagem` (null)
- `editado_por` FK → `Atendente` (null)
- `data_atualizacao` DateTime
- Meta: `unique_together=[("atendimento","campo")]`, indexes `(atendimento, campo)`, GIN em `valor` (PG)
- `db_table = "atu_valor_campo"`

**Feature LLM `extracao_campos`** em [modules/ai_engine/features/extracao_campos/](../../src/smart_core_assistant_painel/modules/ai_engine/features/extracao_campos/) (espelhar `interpret_media`):
```
extracao_campos/
  datasource/extracao_campos_datasource.py
  domain/usecase/extracao_campos_usecase.py
  domain/model/campo_extraido.py
```
- **Schema Pydantic dinâmico** via `pydantic.create_model` a partir de `campos_definidos` (apenas campos sem valor ou `confianca<0.9`).
- **Prompt**: "Analise a conversa e extraia APENAS os campos abaixo cujos valores aparecem explicitamente. Não invente. Retorne `null` se ausente."
- **Threshold**: ≥0.6 para gravar; **nunca sobrescreve `origem=MANUAL`**; só sobrescreve `BOT` se `confianca_nova > confianca_atual`.
- **Quando rodar**: Celery task `extract_custom_fields_async(tenant_slug, atendimento_id, mensagem_id)` disparada em [`AttendanceOrchestrator._process_message_and_respond`](../../src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py) **após** resposta gravada.

**Tasks**

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| E.2.1 | Criar models `CampoPersonalizado` + `ValorCampoAtendimento` + migration | `database-specialist` | ✅ done | Migration `0002_campos_personalizados` aplicada |
| E.2.2 | Criar `CampoPersonalizadoAdmin` em `tenant_admin.py` | `backend-specialist` | ✅ done | `CampoPersonalizadoAdmin` + `ValorCampoAtendimentoAdmin` |
| E.2.3 | Criar `ExtracaoCamposError` e `ExtracaoCamposParameters` | `feature-developer` | ✅ done | `erros.py` + `parameters.py` + `CampoDefinicao` |
| E.2.4 | Implementar `extracao_campos_datasource.py` com `with_structured_output` + schema dinâmico | `feature-developer` | ✅ done | `pydantic.create_model` dinâmico; threshold 0.6; bug do prefixo de remetente corrigido em `b3686f0` |
| E.2.5 | Adicionar `FeaturesCompose.extracao_campos(parameters)` | `feature-developer` | ✅ done | `temperature=0.0`; retorna `list[CampoExtraido]` |
| E.2.6 | Criar Celery task `extract_custom_fields_async` com `select_for_update` e regra de idempotência | `feature-developer` | ✅ done | Task idempotente; usa `time.sleep(1)` (não `countdown` — bug Celery+Redis); skip BOT≥0.9 |
| E.2.7 | **Disparar `extract_custom_fields_async` via signal próprio** | `feature-developer` | ✅ done | `_on_mensagem_bot_extrair_campos` em `signals.py` — usa `TipoRemetente.BOT` |
| E.2.8 | Adicionar `campos_coletados`/`campos_pendentes` em `AnaliseMensageParameters` | `feature-developer` | ✅ done | Campos opcionais via `field(default_factory=list)` |
| E.2.9 | Modificar `analise_mensage_datasource` para injetar seção no system prompt | `feature-developer` | ✅ done | `_formatar_campos_personalizados` integrado entre `contexto_adicional` e `dados_empresa` |
| E.2.9b | **NOVO** — Ponte real: `attendance_orchestrator.py` (no app `atendimentos`) passar `campos_coletados`/`campos_pendentes` para `AnaliseMensageParameters` usando `selectors.get_campos_for_prompt(atendimento_id, fluxo_id)` | `backend-specialist` | ⏳ pending (E.3) | A integração end-to-end exige tocar `attendance_orchestrator.py` — fora do princípio E.2. Helper `get_campos_for_prompt` já pronto em `atendimento_unificado/selectors.py` |
| ~~E.2.10~~ | **DROPADA** | — | dropped | — |
| E.2.11 | Implementar painel `partials/custom_fields_panel.html` com form Alpine auto-save por campo | `frontend-specialist` | ✅ done | Edição inline; barra de confiança colorida (verde/âmbar/vermelho); badges BOT/IMPORT/MANUAL |
| E.2.12 | Endpoints API (definitions/values/PATCH) | `backend-specialist` | ✅ done | `CustomFieldPatchView` em `views_api.py`; valores expostos via `get_atendimento_detail.campos` |
| E.2.13 | Evento SSE `custom_field.updated` | `backend-specialist` | ✅ done | Publicado em `tasks.py` após persistência; handler em `workspace_alpine.js` |

**Riscos E.2 e mitigações**
1. **Custo LLM extra por mensagem** → modelo barato; skip se todos campos têm `confianca≥0.9`; skip se não há campo `extrair_automaticamente=True` aplicável.
2. **Race bot vs atendente** → `select_for_update` no atendimento + regra "nunca sobrescrever MANUAL".
3. **Tenant na task Celery** → ativar via `tenant_context` (padrão já usado em outras tasks — ver memória do projeto).

---

#### E.3 — Refinamentos (esforço **M**)

**Objective:** Polir UX (drag-drop, filtros), implementar mídia outbound e exportação.

**Tasks**

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| E.3.1 | Integrar **SortableJS** via CDN com Alpine; `dragend → POST /board/move/`; rollback em erro via snapshot do store | `frontend-specialist` | pending | Drag-drop suave sem flicker |
| E.3.2 | Flag `isDragging` no store Alpine ignora updates SSE da etapa em movimento por 2s | `frontend-specialist` | pending | Sem conflito SortableJS+SSE |
| E.3.3 | Filtros: `/conversations/?q=&depto=&atendente=&tag=&campo_<slug>=` | `backend-specialist` | pending | Filtros funcionam |
| E.3.4 | Index GIN em `ValorCampoAtendimento.valor` para filtro por campo | `database-specialist` | pending | Query plan usa index |
| E.3.5 | Badge não-lido baseado em `LeituraAtendimento.ultima_leitura_at` (model criado na E.1.10). Endpoint `mark-read` faz upsert em `LeituraAtendimento` | `frontend-specialist` | pending | Badge decrementa ao abrir |
| E.3.6 | Badge SLA estourado usando `MovimentoFluxo.duracao_segundos` | `frontend-specialist` | pending | Visualização clara de SLA |
| E.3.7 | Implementar `EvolutionWhatsAppService.send_media(...)` chamando `/message/sendMedia` da Evolution API | `backend-specialist` | pending | Mídia outbound funcional |
| E.3.8 | Signal Evolution detecta `Mensagem.tipo in (IMAGEM,AUDIO,DOCUMENTO)` e usa `send_media` | `backend-specialist` | pending | Atendente envia mídia |
| E.3.9 | Endpoint `POST /conversations/<id>/upload/` (multipart) cria `Mensagem` com mídia | `backend-specialist` | pending | Upload funcional |
| E.3.10 | `GET /workspace/api/export/?formato=csv&...` → `StreamingHttpResponse` + `.iterator(chunk_size=500)`; Celery se grande | `backend-specialist` | pending | Export 5000 linhas < 30s |

**Riscos E.3 e mitigações**
1. **SortableJS+SSE conflito** → flag `isDragging` no store (E.3.2).
2. **Export grande** → streaming + Celery para >10k linhas.

---

### Phase V — Validação Ponta a Ponta
> **Primary Agent:** `code-reviewer` — [Playbook](../agents/code-reviewer.md)

**Objective:** Validação manual (3 roteiros, um por sub-fase) + lint + type-check + carga.

**Tasks**

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| V.1.a | Roteiro E.1 — Chat: envio msg via composer chega no WhatsApp; histórico carrega; mark-read decrementa badge; 2 abas refletem novas msgs ao vivo (SSE) | `code-reviewer` | pending | Checklist marcado |
| V.1.b | **Roteiro E.1 — Paridade Trello (crítico)**: (a) seletor de Fluxo mostra todos os fluxos do dept; (b) cards no kanban renderizam visual equivalente ao Trello (título, label prioridade, atendente, preview, tempo); (c) clicar em card abre chat drawer; (d) mover card FILA→TRABALHO atribui atendente E envia saudação automática (verificar Mensagem criada com `transferir_para_humano_com_saudacao`); (e) mover para etapa FINALIZACAO (nome "Resolvido") encerra atendimento com status RESOLVIDO; (f) mover para etapa "Cancelado" encerra com CANCELADO; (g) mover para etapa ESPERA muda status para PENDENCIA; (h) mover card para coluna de OUTRO fluxo atualiza `atendimento.fluxo_atendimento_id` e `departamento_id`; (i) mudança de `Atendimento.status` (via outra origem) move card e card no Trello | `code-reviewer` | pending | Checklist marcado, evidências em screenshots |
| V.1.c | Roteiro E.1 — Trello permanece sincronizado: mudanças no Workspace refletem no Trello em ≤5s; mudanças no Trello refletem no Workspace em ≤5s (via SSE após signal interno) | `code-reviewer` | pending | Checklist marcado |
| V.2 | Roteiro E.2: definir campo, contato envia "CNPJ X", ver extração, editar manual, validar não-sobrescrita, ver no Trello, ver no próximo prompt | `code-reviewer` | pending | Checklist marcado |
| V.3 | Roteiro E.3: drag-drop, filtros por campo, badge não-lido, export CSV | `code-reviewer` | pending | Checklist marcado |
| V.4 | `ruff format` + `ruff check` + `pyright --strict` sem erros | `code-reviewer` | pending | Saída limpa |
| V.5 | Carga: 50 conversas + 1000 mensagens → sidebar < 500ms; board com 30 cards × 6 colunas < 800ms | `performance-optimizer` | pending | Métrica registrada |
| V.6 | Auditoria de segurança: autorização por rota, isolamento tenant SSE, validação upload, atendente só vê fluxos permitidos | `security-auditor` | pending | Relatório aprovado |

**Commit Checkpoint**: `chore(plan): validar atendimento_unificado fases E.1-E.3`

---

### Phase C — Encerramento, Release e Deploy em Produção
> **Primary Agent:** `documentation-writer` — [Playbook](../agents/documentation-writer.md)

**Objective:** Documentação final + release versionada + deploy automático via tag git + rollout controlado em produção (sem ambiente de teste, conforme decisão D6).

**Tasks**

| # | Task | Agent | Status | Deliverable |
|---|------|-------|--------|-------------|
| C.1 | Atualizar [architecture.md](../docs/architecture.md) com novo app, SSE e princípio de independência cross-app | `documentation-writer` | pending | Seção adicionada |
| C.2 | Atualizar [data-flow.md](../docs/data-flow.md) com fluxo de extração e SSE | `documentation-writer` | pending | Diagrama atualizado |
| C.3 | Atualizar [glossary.md](../docs/glossary.md) (Workspace, Campo Personalizado, `LeituraAtendimento`, feature flag, etc.) | `documentation-writer` | pending | Termos novos |
| C.4 | Documentar configuração Nginx (`proxy_buffering off`, `proxy_read_timeout 1h` em `/workspace/events/`) em [security.md](../docs/security.md) ou doc dedicado | `documentation-writer` | pending | Config Nginx publicada |
| C.5 | **Merge da branch `feature/new-front-user` em `master`** após todas E.1–E.3 verdes. PR review obrigatório. | `backend-specialist` | pending | Merge concluído em master |
| C.6 | **Bump de versão semver MINOR** (feature nova) em `pyproject.toml` + `CHANGELOG.md` resumindo entregas E.1, E.2, E.3 | `backend-specialist` | pending | Versão bumpada, CHANGELOG atualizado |
| C.7 | **Criar tag e disparar deploy automático**: `git tag -a v<MAJOR>.<MINOR>.<PATCH> -m "Release atendimento_unificado v..."` + `git push origin v<MAJOR>.<MINOR>.<PATCH>`. O [.github/workflows/deploy.yml](../../.github/workflows/deploy.yml) dispara em `push: tags: v*` — build Docker, push GHCR, SSH no servidor, `docker compose pull`, `migrate`, `bootstrap_core_settings`, `migrate_all_tenants`, `collectstatic`, healthcheck. | `devops-specialist` | pending | Tag criada; workflow GitHub Actions verde; containers `Up (healthy)` |
| C.8 | **Verificar healthcheck pós-deploy**: logs do GHA, `docker compose ps` no servidor, acesso a `/healthz` (se existir) ou raiz autenticada | `devops-specialist` | pending | Containers healthy, sem `Restarting` |
| C.9 | **Habilitar feature flag em 1 tenant piloto**: `TenantConfig.update_config(slug, key="ATENDIMENTO_UNIFICADO_ENABLED", value=True)` no shell Django. Smoke test manual (V.1.a, V.1.b crítico, V.1.c) com esse tenant — duração mínima 24h observando logs Loguru. | `backend-specialist` | pending | 1 tenant rodando 24h sem erros |
| C.10 | **Rollout gradual**: habilitar feature flag nos demais tenants, 1 por vez, intervalo mínimo de 4h entre cada. Monitorar `/var/log/smartcore-health.log` e logs do GHA. | `backend-specialist` | pending | Todos os tenants ligados, sem incidentes |
| C.11 | Arquivar plano em `.context/plans/archive/` e atualizar README | `documentation-writer` | pending | Plano arquivado |
| C.12 | Registrar lessons learned (SSE async views, princípio de independência cross-app, deploy direto em prod com feature flag) | `documentation-writer` | pending | Lessons no plano arquivado |

**Commit Checkpoint**: `chore(plan): encerrar plano atendimento_unificado v<MAJOR>.<MINOR>.<PATCH>`

---

#### Estratégia de Teste em Produção (sem ambiente de teste — decisão D6)

**Risco fundamental**: validações V.1–V.6 rodam em produção. Mitigações obrigatórias antes do tag push (C.7):

1. **Feature flag global por tenant** (`ATENDIMENTO_UNIFICADO_ENABLED`) — default OFF. Sidebar não mostra item; rotas `/workspace/*` retornam 404. Liga manualmente por tenant após smoke test.
2. **Migrations seguras**: TODAS as migrations do `atendimento_unificado` criam apenas tabelas novas (`atu_leitura_atendimento`, `atu_campo_personalizado`, `atu_valor_campo`). Nenhuma `ALTER`/`DROP` em tabelas legadas. Migration reversa simplesmente drop dessas tabelas, sem perda de dados de produção.
3. **Loguru level INFO em produção** no primeiro mês — visibilidade dos receivers de signals, disparos de Celery tasks, eventos SSE publicados.
4. **Health monitoring existente**: `/opt/smartcore/scripts/health-monitor.sh` (cron 5min) + `/var/log/smartcore-health.log` (logrotate semanal) cobrem reinício de containers.
5. **Smoke test em 1 tenant piloto antes de rollout** (C.9) — 24h mínimas de observação.

#### Rollback Plan (release em produção)

| Cenário | Ação | Reversibilidade |
|---|---|---|
| Erro fatal no boot do app | (a) `TenantConfig` global OFF da feature flag via shell; (b) revert imediato: `git push --delete origin <tag>` + `git tag -d <tag>` + `git push origin <tag-anterior>` redispara workflow com versão anterior. | Total, ~5min |
| Bug funcional em 1 tenant | Desligar feature flag só nesse tenant. App continua rodando para os demais. | Total, ~30s |
| Migration falha | Workflow `deploy.yml` aborta em `migrate` (`set -e` no script SSH). Containers antigos seguem ativos. Investigar e corrigir antes de retentar push da tag. | Total, sem impacto |
| Performance ruim de SSE | Desligar feature flag em todos os tenants; investigar offline. App segue Up. | Total, ~2min |

#### Como o usuário cria a release

```bash
# em master, após merge da feature branch e bump de versão
git checkout master
git pull
git tag -a v1.4.0 -m "Release atendimento_unificado: chat + kanban + campos personalizados"
git push origin v1.4.0
# acompanhar workflow em https://github.com/<owner>/<repo>/actions
```

---

## Risk Assessment

| Risco | Probabilidade | Impacto | Mitigação | Owner |
|---|---|---|---|---|
| Gunicorn sync worker travado por SSE | Alta | Alto | Usar `UvicornWorker` ou Uvicorn dedicado para `/events/` | `devops-specialist` |
| Vazamento cross-tenant em SSE | Média | Crítico | Canal Redis por tenant + teste com 2 tenants na V | `security-auditor` |
| **Loop signal Workspace↔Trello** (mover via Workspace → signal Trello → task → webhook reverso) | **Alta** | **Alto** | (a) `board_service.move_atendimento` define `_syncing_from_trello=False` (não impede). (b) `webhook_processing_service` já tem dedup via `TrelloWebhookEvent.action_id`. (c) Tasks Trello fazem early-return se etapa não mudou. Verificar com teste manual. | `architect-specialist` |
| **Drag-drop Workspace muda etapa, mas regras `tipo_etapa` mexem no status** que volta a mover o card (recursão) | Média | Alto | `board_service.move_atendimento` deve aplicar regras em ordem: (1) `MovimentoFluxo.criar_movimento` (define `etapa_atual`), (2) lógica `tipo_etapa` (define status SEM disparar signal de etapa novamente — usar `update_fields=["status","data_fim"]`). Reusar exatamente o que `ticket_sync_service.process_webhook_card_move` faz. | `backend-specialist` |
| **Falta de saudação ao assumir da fila via Workspace** (regressão funcional vs Trello) | Média | Alto | E.1.4 obriga chamada a `transferir_para_humano_com_saudacao` ao mover para etapa `TRABALHO`. Roteiro V.1.b item (d) valida explicitamente. | `backend-specialist` |
| **Atendente sem `Atendente` cadastrado tenta mover card para TRABALHO** | Média | Médio | API retorna 400 com mensagem clara; UI exibe modal "Você não está cadastrado como atendente neste departamento" | `backend-specialist` |
| Custo LLM extra por mensagem | Média | Médio | Skip campos com `confianca≥0.9`; modelo barato; skip se nada a extrair | `feature-developer` |
| Race bot vs atendente em campo | Média | Médio | `select_for_update` + nunca sobrescrever MANUAL | `feature-developer` |
| Schema Pydantic dinâmico falha | Baixa | Médio | Validar com `with_structured_output` (já usado em `RespostaBot`) | `feature-developer` |
| ~~Trello reflete antes de campos estarem prontos~~ | — | — | **DROPADO** — espelhamento de campos no Trello removido (D5). Workspace é a única fonte. | — |
| Mídia outbound não suportada hoje | **Confirmado** | Médio | E.3 implementa `send_media` (endpoint Evolution `/message/sendMedia`) | `backend-specialist` |

## Dependencies

- **Internal**: `operacional` (FluxoAtendimento, EtapaFluxo), `atendimentos` (Atendimento, Mensagem, MovimentoFluxo), `evolution_sync` (EvolutionWhatsAppService + signal), `trello_sync` (TicketSyncService + signals), `tenants` (TenantConfig, get_current_tenant_slug)
- **External**: Redis (já presente como broker Celery), Evolution API (já configurada por tenant), Gemini (para extração — já configurado na feature anterior)
- **Técnico**: Tailwind CSS via CDN, Alpine.js 3 via CDN, SortableJS via CDN (E.3), Uvicorn worker async (E.1)

## Assumptions

- `core/asgi.py` permanece como Django ASGI padrão; rota SSE é async view nativa (Django 4.1+).
- A integração Trello continua bidirecional, mas painel é a UI principal e Trello passa a ser espelho de leitura.
- Bot LLM já configurado por tenant (modelo, API key) — extração reusa o mesmo provider/modelo.
- Permissão de módulo `atendimento` será criada (similar a `treinamento`, `configuracoes`).

## Rollback Plan

| Sub-fase | Ação | Impacto em dados | Tempo |
|---|---|---|---|
| E.1 | Reverter PRs, remover app de `INSTALLED_APPS`. Migration `data_ultima_leitura_atendente` permanece (campo opcional). | Nenhum | <1h |
| E.2 | Reverter PRs, manter tabelas `atu_*` no banco (ou rodar migration reversa). Desativar Celery task. | Campos extraídos pelo bot persistem mas não são exibidos. Não afeta WhatsApp/Trello. | <2h |
| E.3 | Reverter PRs. Mídia outbound desabilitada (volta a só texto). | Nenhum | <1h |

## Execution History

> Last updated: 2026-05-15T14:07:00.417Z | Progress: 0%

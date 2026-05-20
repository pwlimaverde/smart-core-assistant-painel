# Plano Modular — Chat Evolution + Gestão Kanban + Atendimento Unificado + Design System

> **Versão 3.1 (2026-05-20)** — Reestruturação arquitetural: separação em 4 pilares especializados, incluindo um Design System em módulo independente, rotas de API limpas e divisão total do frontend por domínio.
>
> Substitui o plano v3.0 para consolidar o Design System como módulo agnóstico ao Django.

---

## Contexto e Motivação

A abordagem anterior de centralizar chat + kanban + campos custom em um único app (`atendimento_unificado`) gerou:

- **Bugs de estado** — estado do chat (SSE de mensagens, composer, leitura) conflitava com estado do kanban (drag-drop, movimentação de etapas, regras `tipo_etapa`).
- **UX degradada** — a tentativa de renderizar tudo em uma view única criou latência e complexidade visual desnecessária.
- **Manutenção difícil no Frontend** — arquivos JS e CSS massivos misturando lógicas distintas.
- **Acoplamento Visual** — falta de um local central para componentes reaproveitáveis.

**Novo Objetivo**: Separar as responsabilidades em **quatro pilares independentes**, com foco inicial na criação de um **Design System** agnóstico e isolado, permitindo que cada app cuide de sua lógica e assets específicos, unidos apenas num UI Shell.

### Os Quatro Pilares

| # | Pilar | Responsabilidade | Localização |
|---|-------|-----------------|-------------|
| 1 | **`design_system`** | Central de componentes visuais, CSS base (Tailwind), JS utilitário e partials genéricos (botões, modais). Totalmente desvinculado do Django. | `modules/design_system` |
| 2 | **`chat_evolution`** | Chat completo estilo WhatsApp Web, usando todos os recursos da Evolution API. | `app/chat_evolution` |
| 3 | **`gestao_kanban`** | Kanban avançado com paridade Trello, campos personalizados, IA, drag-and-drop. | `app/gestao_kanban` |
| 4 | **`atendimento_unificado`** | **UI Shell puro** — monta o layout integrando as telas dos apps acima como "módulos". | `app/atendimento_unificado` |

---

## 1. Decisões Arquiteturais Consolidadas

### 1.1 Separação por Domínio e UI

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                       atendimento_unificado                              │
│         (UI Shell — Orquestra Layout e amarra eventos globais)           │
│                                                                          │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────┐  │
│  │       chat_evolution          │  │        gestao_kanban             │  │
│  │  • Mensagens / Evolution      │  │  • Quadros / Cards / Custom FI.  │  │
│  │  • SSE: /chat/events/         │  │  • SSE: /kanban/events/          │  │
│  │  • API: /chat/api/            │  │  • API: /kanban/api/             │  │
│  │  • static/chat_evolution/     │  │  • static/gestao_kanban/         │  │
│  │  • templates/.../components/  │  │  • templates/.../components/     │  │
│  └─────────────┬────────────────┘  └────────────────┬─────────────────┘  │
│                │                                    │                    │
│  ┌─────────────▼────────────────────────────────────▼─────────────────┐  │
│  │                        design_system                               │  │
│  │                  (Módulo Agnóstico - modules/)                     │  │
│  │  • core.css (Tailwind Base)  • core_alpine.js (Helpers globais)    │  │
│  │  • templates/ (Button, Modal, Input)                               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Princípios Inegociáveis

1. **Design System Agnóstico**: O módulo `design_system` vive em `modules/` (mesmo nível do `ai_engine`). Ele **não é um app Django** (sem `apps.py`, fora de `INSTALLED_APPS`). O Django mapeará seus diretórios estáticos e de templates via `settings.py`. Nenhum app de negócio deve reescrever CSS genérico.
2. **Rotas Limpas**: Cada app terá seu namespace de URL. Fim do roteamento aninhado sob `/workspace/api/`. As APIs do chat viverão em `/chat/api/` e do kanban em `/kanban/api/`.
3. **Independência cross-app**: `chat_evolution` e `gestao_kanban` não importam código um do outro. Comunicação **apenas via Django signals + eventos Alpine no frontend**.
4. **Zero alteração em banco legado**: Leitura direta das tabelas atuais é permitida; escrita via métodos públicos. Novos apps usarão models proxy (`managed = False`) apontando para as tabelas criadas pelo `atendimento_unificado`.

---

## 2. Estruturação do Frontend (CSS/JS/HTML)

### 2.1 Módulo `design_system` (Agnóstico)
- **Local**: `src/smart_core_assistant_painel/modules/design_system/`
- **Configuração no Django**:
  ```python
  # settings.py
  TEMPLATES[0]['DIRS'].append(BASE_DIR / 'src/smart_core_assistant_painel/modules/design_system/templates')
  STATICFILES_DIRS.append(BASE_DIR / 'src/smart_core_assistant_painel/modules/design_system/static')
  ```
- **Templates**: `templates/components/` (ex: `button.html`, `badge.html`, `modal_base.html`).
- **Static**:
  - `static/css/core.css`: Imports do Tailwind (`@tailwind base`), variáveis de cores (`--color-gold-primary`), e classes utilitárias.
  - `static/js/core_alpine.js`: Stores Alpine genéricas, diretivas reutilizáveis e utilitários de formatação.

### 2.2 Frontend Específico: `chat_evolution`
- **Templates**: `templates/chat_evolution/components/` (ex: `chat_bubble.html`, `composer.html`, `media_viewer.html`).
- **Static**:
  - `static/chat_evolution/css/chat.css`: Estilos puramente do chat.
  - `static/chat_evolution/js/chat_alpine.js`: Controle SSE de mensagens, gravação de áudio, envio. Consome endpoints `/chat/api/`.

### 2.3 Frontend Específico: `gestao_kanban`
- **Templates**: `templates/gestao_kanban/components/` (ex: `kanban_card.html`, `kanban_column.html`, `custom_fields_panel.html`).
- **Static**:
  - `static/gestao_kanban/css/kanban.css`: Estilos de drag-and-drop, layout do board.
  - `static/gestao_kanban/js/kanban_alpine.js`: Integração SortableJS, SSE de board. Consome endpoints `/kanban/api/`.

### 2.4 UI Shell Orquestrador (`atendimento_unificado`)
- **Templates**: `templates/atendimento_unificado/workspace.html`. Atua como arquivo base, incluindo os componentes via `{% include %}`.
- **Static**:
  - `static/atendimento_unificado/js/workspace_coordinator.js`: Roteia eventos entre os submódulos (ex: abre o chat quando clica num card do kanban).

---

## 3. Inventário de Migração do Backend

As migrations (tabelas `atu_*`) ficam no app original. Os novos apps farão proxy.

### 3.1 Backend `chat_evolution`
- **Models**: `LeituraAtendimento` (`managed = False`).
- **Views**: Listagem de conversas, Histórico de mensagens, Envio de texto, Marcação de lido, Presença, Upload de mídia, Lista de mídias, Detalhes do contato, Sinalização de não-lidos.
- **Rotas (Novas)**: Inicia em `/chat/api/` e `/chat/events/`.
- **Services**: `message_dispatch_service.py`, `media_dispatch_service.py`.
- **Selectors**: Queries de leitura do chat.
- **Signals**: Publica SSE em `sse:{tenant}:chat`.

### 3.2 Backend `gestao_kanban`
- **Models**: `CampoPersonalizado`, `ValorCampoAtendimento`, `Etiqueta`, `EtiquetaAtendimento`, `Nota`. Enums. Todos `managed = False`.
- **Views**: Lista de fluxos, Snapshot do board, Movimentação de card, Atribuição, Cross-board move, Edição de campos custom, CRUD de etiquetas e notas, Timeline, Exportação CSV.
- **Rotas (Novas)**: Inicia em `/kanban/api/` e `/kanban/events/`.
- **Services**: `board_service.py`, `card_renderer.py`, `etiquetas_service.py`, `notas_service.py`, `transfer_fluxo_service.py`.
- **IA**: Celery task `extract_custom_fields_async` disparada após resposta do bot.
- **Selectors**: Queries de renderização do quadro.
- **Signals**: Publica SSE em `sse:{tenant}:kanban`.

### 3.3 Paridade Funcional (Trello ↔ Kanban)
Garantido via `board_service`:
1. Reordenação automática por `ordem`.
2. FILA → TRABALHO: atribui atendente e dispara saudação.
3. FINALIZACAO: encerra (RESOLVIDO/CANCELADO).
4. ESPERA: PENDENCIA.
5. Cross-Board move altera `fluxo_atendimento_id` e `departamento_id`.

---

## 4. Estratégia de Transição e Faseamento

O projeto adota uma transição gradual (Não-Destrutiva):

### FASE 1: Fundação UI e Design System Agnóstico
1. Criar pasta `src/smart_core_assistant_painel/modules/design_system/`.
2. Mapear `templates` e `static` no `settings.py`.
3. Isolar classes CSS globais do `workspace.css` em `core.css`.
4. Mover partials HTML genéricos para a nova estrutura.
5. Testar e garantir que o monolito atual importa do novo módulo sem quebrar.

### FASE 2: Backend e Proxies de Banco
1. Criar apps Django `chat_evolution` e `gestao_kanban` na pasta `app/`.
2. Registrar apps e implementar models proxy.
3. Copiar os serializers, selectors, services, tasks e signals.

### FASE 3: Rotas Limpas e Desacoplamento JS
1. Expor as novas rotas em `/chat/` e `/kanban/` no `urls.py` principal.
2. Quebrar o `workspace_alpine.js` em módulos específicos.
3. Atualizar chamadas AJAX (`fetch`) no frontend para as novas APIs.
4. Mover partials HTML de domínio para os seus respectivos apps.

### FASE 4: Limpeza do Shell
1. Validar funcionalidade integrada.
2. Deletar views, endpoints antigos, js massivo e lógica de negócio de dentro do `atendimento_unificado`.
3. Deixar `atendimento_unificado` puramente como roteador visual.

---

## 5. Plano de Ação (PREVC)

| Etapa | Ação | Entregável |
|-------|------|-----------|
| **P (Planning)** | Este documento | Plano revisado com Design System em módulo agnóstico. |
| **E (Execution) - Fase 1** | Criar `modules/design_system`, migrar CSS e HTML genéricos, mapear no settings. | Foundation agnóstica estabelecida. |
| **E (Execution) - Fase 2** | Criar `app/chat_evolution` e `app/gestao_kanban`, migrar models e endpoints. | Rotas limpas ativas. |
| **E (Execution) - Fase 3** | Separar JS/CSS em arquivos por app, refatorar chamadas REST/SSE. | Frontend desacoplado. |
| **E (Execution) - Fase 4** | Integrar e Limpar. | Código legado removido. |
| **V (Validation)** | Homologação final. | Relatório de testes. |
| **C (Confirmation)** | Deploy via Feature Flag. | Funcionalidade no ar. |

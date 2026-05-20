# Plano Modular — Chat Evolution + Gestão Kanban + Atendimento Unificado + Design System

> **Versão 3.0 (2026-05-20)** — Reestruturação arquitetural: separação em 4 apps especializados, incluindo um Design System centralizado, rotas de API limpas e divisão total do frontend por domínio.
>
> Substitui o plano v2.0 para incorporar as diretrizes de design system e independência visual.

---

## Contexto e Motivação

A abordagem anterior de centralizar chat + kanban + campos custom em um único app (`atendimento_unificado`) gerou:

- **Bugs de estado** — estado do chat (SSE de mensagens, composer, leitura) conflitava com estado do kanban (drag-drop, movimentação de etapas, regras `tipo_etapa`).
- **UX degradada** — a tentativa de renderizar tudo em uma view única criou latência e complexidade visual desnecessária.
- **Manutenção difícil no Frontend** — arquivos JS e CSS massivos misturando lógicas distintas.
- **Acoplamento Visual** — falta de um local central para componentes reaproveitáveis.

**Novo Objetivo**: Separar as responsabilidades em **quatro pilares independentes**, com foco inicial na criação de um **Design System** que padronize a UI, permitindo que cada app cuide de sua lógica e assets específicos, unidos apenas num UI Shell.

### Os Quatro Pilares

| # | Pilar | Responsabilidade | Analogia |
|---|-------|-----------------|----------|
| 1 | **`design_system`** | Central de componentes visuais, CSS base (Tailwind), JS utilitário e partials genéricos (botões, modais). | Foundation/Bootstrap interno |
| 2 | **`chat_evolution`** | Chat completo estilo WhatsApp Web, usando todos os recursos da Evolution API. | WhatsApp Web |
| 3 | **`gestao_kanban`** | Kanban avançado com paridade Trello, campos personalizados, IA, drag-and-drop. | Trello personalizado |
| 4 | **`atendimento_unificado`** | **UI Shell puro** — monta o layout integrando as telas dos apps acima como "módulos". | Container/Orquestrador |

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
│  │  • core.css (Tailwind Base)  • core_alpine.js (Helpers globais)    │  │
│  │  • templates/design_system/components/ (Button, Modal, Input)      │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Princípios Inegociáveis

1. **Design System First**: O app `design_system` centraliza a base. Nenhum app deve reescrever CSS genérico. Componentes específicos de app vivem dentro do seu respectivo app.
2. **Rotas Limpas**: Cada app terá seu namespace de URL. Fim do roteamento aninhado e confuso sob `/workspace/api/`. As APIs do chat viverão em `/chat/api/` e do kanban em `/kanban/api/`.
3. **Independência cross-app**: `chat_evolution` e `gestao_kanban` não importam código um do outro. Comunicação **apenas via Django signals + eventos Alpine no frontend**.
4. **Zero alteração em banco legado**: Leitura direta das tabelas atuais é permitida; escrita via métodos públicos. Novos apps usarão models proxy (`managed = False`) apontando para as tabelas criadas pelo `atendimento_unificado`.

---

## 2. Estruturação do Frontend (CSS/JS/HTML)

Esta é a prioridade técnica antes de mover a lógica de backend.

### 2.1 Módulo `design_system`
- **Responsabilidade**: Fornecer a fundação UI para o resto do sistema.
- **Templates**: `templates/design_system/components/` (ex: `button.html`, `badge.html`, `input.html`, `modal_base.html`).
- **Static**:
  - `static/design_system/css/core.css`: Onde ficam os imports do Tailwind (`@tailwind base`), variáveis de cores (`--color-gold-primary`), e classes utilitárias não vinculadas a um domínio.
  - `static/design_system/js/core_alpine.js`: Armazena stores Alpine genéricas, diretivas reutilizáveis e utilitários de formatação.

### 2.2 Frontend Específico: `chat_evolution`
- **Templates**: `templates/chat_evolution/components/` (ex: `chat_bubble.html`, `composer.html`, `media_viewer.html`).
- **Static**:
  - `static/chat_evolution/css/chat.css`: Estilos puramente do chat (balões, layout de conversa).
  - `static/chat_evolution/js/chat_alpine.js`: Controle SSE de mensagens, gravação de áudio, envio. Consome endpoints `/chat/api/`.

### 2.3 Frontend Específico: `gestao_kanban`
- **Templates**: `templates/gestao_kanban/components/` (ex: `kanban_card.html`, `kanban_column.html`, `custom_fields_panel.html`).
- **Static**:
  - `static/gestao_kanban/css/kanban.css`: Estilos do layout horizontal, drag states, modais do kanban.
  - `static/gestao_kanban/js/kanban_alpine.js`: Integração com SortableJS, SSE de board, manipulação de cards. Consome endpoints `/kanban/api/`.

### 2.4 UI Shell Orquestrador (`atendimento_unificado`)
- **Templates**: `templates/atendimento_unificado/workspace.html`. Atua como arquivo base da página, incluindo `{% include %}` os componentes dos apps.
- **Static**:
  - `static/atendimento_unificado/js/workspace_coordinator.js`: Ouve os eventos disparados pelos submódulos. Ex:
    ```javascript
    window.addEventListener('kanban:card-clicked', (e) => {
        Alpine.store('chat').loadConversation(e.detail.id);
        Alpine.store('shell').openDrawer();
    });
    ```

---

## 3. Inventário de Migração do Backend

O app `atendimento_unificado` atual tem suas responsabilidades desmembradas. As migrations (tabelas `atu_*`) ficam no app original. Os novos apps farão proxy.

### 3.1 Backend `chat_evolution`
- **Models**: `LeituraAtendimento` (`managed = False`).
- **Views**: Listagem de conversas, Histórico de mensagens, Envio de texto, Marcação de lido, Presença, Upload de mídia, Lista de mídias, Detalhes do contato, Sinalização global de não-lidos.
- **Rotas (Novas)**: Inicia em `/chat/api/` e `/chat/events/`.
- **Services**: `message_dispatch_service.py`, `media_dispatch_service.py`.
- **Selectors**: Queries exclusivas de leitura do chat.
- **Signals**: Envio de mensagem → publica SSE em `sse:{tenant}:chat`.

### 3.2 Backend `gestao_kanban`
- **Models**: `CampoPersonalizado`, `ValorCampoAtendimento`, `Etiqueta`, `EtiquetaAtendimento`, `Nota`. Enums. Todos `managed = False`.
- **Views**: Lista de fluxos, Snapshot do board, Movimentação de card, Atribuição, Cross-board move, Edição de campos custom, CRUD de etiquetas e notas, Timeline, Exportação CSV.
- **Rotas (Novas)**: Inicia em `/kanban/api/` e `/kanban/events/`.
- **Services**: `board_service.py`, `card_renderer.py`, `etiquetas_service.py`, `notas_service.py`, `transfer_fluxo_service.py`.
- **IA**: Celery task `extract_custom_fields_async` disparada após resposta do bot.
- **Selectors**: Queries de renderização do quadro e painéis laterais.
- **Signals**: Movimentação/Update → publica SSE em `sse:{tenant}:kanban`.

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

### FASE 1: Fundação UI e Design System
1. Criar app `design_system`.
2. Isolar as classes CSS globais do `workspace.css` em `design_system/core.css`.
3. Criar os diretórios e migrar partials genéricos para os `components/` globais.
4. Testar para garantir que o layout monolítico atual sobrevive à extração das fundações.

### FASE 2: Backend e Proxies de Banco
1. Criar `chat_evolution` e `gestao_kanban`.
2. Registrar apps.
3. Implementar os models proxy apontando para as tabelas `atu_*`.
4. Copiar (sem deletar a fonte) os serializers, selectors, services, tasks e signals.

### FASE 3: Rotas Limpas e Desacoplamento JS
1. Expor as novas rotas em `/chat/` e `/kanban/` no `urls.py` principal.
2. Quebrar o `workspace_alpine.js` em seus respectivos módulos.
3. Atualizar as chamadas AJAX (`fetch`) no frontend para apontar para as APIs e SSE específicos de cada módulo.
4. Mover templates partials de domínio para dentro de seus apps.

### FASE 4: Limpeza do Shell
1. Validar funcionalidade integrada (SSE, Drag-drop, Envio WhatsApp, IA).
2. Deletar as views, endpoints antigos, js massivo e lógica de negócio de dentro do `atendimento_unificado`.
3. O `atendimento_unificado` deve ficar reduzido a ser o "roteador" visual da feature.

---

## 5. Rollout e Riscos

| Risco | Mitigação |
|-------|-----------|
| Gunicorn sync worker trava em SSE | Manter Uvicorn dedicado ou configuração assíncrona. Os canais agora são `/chat/events/` e `/kanban/events/`. |
| Concorrência SortableJS + SSE | Flag Alpine `isDragging` ignora updates via SSE por 2s para aquele card específico. |
| Model Proxy falha no makemigrations | Usar estritamente `managed = False` e `db_table` com a string exata do banco legado. A migration permanece de posse do app original. |
| Quebra de CSS ao separar em arquivos | Importar CSS na ordem correta: Tailwind Base -> Componentes globais -> Chat.css / Kanban.css -> Utilitários locais. |
| Múltiplos EventSource sobrecarregam | Browsers suportam ~6 conexões HTTP/1.1 por host. Com 2 (chat e kanban), estamos seguros. HTTP/2 faz multiplexing transparente. |

---

## 6. Plano de Ação (PREVC)

| Etapa | Ação | Entregável |
|-------|------|-----------|
| **P (Planning)** | Este documento | Plano revisado arquitetural com Design System. |
| **E (Execution) - Fase 1** | Criar `design_system`, migrar CSS e HTML genéricos. | Foundation estabelecido. |
| **E (Execution) - Fase 2** | Criar `chat_evolution` e `gestao_kanban`, migrar models e endpoints. | Rotas limpas ativas. |
| **E (Execution) - Fase 3** | Separar JS/CSS em arquivos por app, refatorar chamadas REST/SSE. | Frontend desacoplado. |
| **E (Execution) - Fase 4** | Integrar e Limpar. | Código legado removido. |
| **V (Validation)** | Homologação final. | Relatório de testes. |
| **C (Confirmation)** | Deploy via Feature Flag. | Funcionalidade no ar. |

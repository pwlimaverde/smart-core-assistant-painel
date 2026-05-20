# Plano Modular — Chat Evolution, Gestão Kanban e Atendimento Unificado

> **Versão revisada (2026-05-20)** — Evolução da arquitetura original para separar responsabilidades. Foco em estabilidade, melhor UX e processamento desacoplado.

## Contexto e Motivação

A abordagem anterior de centralizar todo o chat e kanban em um único app (`atendimento_unificado`) gerou complexidade, bugs e uma experiência de usuário (UX) degradada. Misturar a orquestração de mensagens em tempo real com a lógica de movimentação de cards e extração de campos tornou o sistema monolítico e difícil de manter.

**Novo Objetivo**: Separar as responsabilidades em três apps distintos, garantindo que cada um faça uma única coisa muito bem, para depois unificá-los visualmente.

1.  **App de Chat (`chat_app` / `chat_evolution`)**: Focado 100% em proporcionar uma experiência similar ao WhatsApp Web. Deve usar todos os recursos da Evolution API (texto, mídia, reações, etc.).
2.  **App de Kanban (`gestao_kanban`)**: Focado em ser um clone aprimorado do Trello, mas direcionado à personalização para cada tenant. Inclui campos personalizados extraídos pela IA e um controle de fluxo de atendimento eficiente.
3.  **App de Atendimento Unificado (`atendimento_unificado`)**: Servirá apenas como um **container de interface (UI Shell)**. Ele unirá as duas telas (Chat + Kanban) mantendo o processamento no backend estritamente separado, lidando apenas com o layout integrado.

## 1. Decisões Arquiteturais

1.  **Separação por Domínio (Micro-apps Django)**:
    *   `chat_app`: Lida com `Mensagem`, `Contato`, webhooks da Evolution API, SSE para mensagens e composer de chat.
    *   `gestao_kanban`: Lida com `FluxoAtendimento`, `EtapaFluxo`, `Atendimento` (como card), movimentações (`MovimentoFluxo`), campos personalizados e tarefas de IA.
    *   `atendimento_unificado`: Lida apenas com views e templates HTML que montam o layout consumindo os componentes/HTMX/APIs dos dois apps acima.
2.  **Processamento Desacoplado**:
    *   O `chat_app` não sabe sobre etapas de funil.
    *   O `gestao_kanban` não envia mensagens, apenas observa (via signals) se o atendimento recebeu interação para fins de SLAs.
    *   Eventos SSE (Server-Sent Events) serão separados ou tipados claramente em canais distintos (`sse:{tenant}:chat` e `sse:{tenant}:kanban`).
3.  **Integração Visual no Frontend**:
    *   O clique em um card no Kanban dispara um evento global (ex: via Alpine.js `$dispatch` ou CustomEvents).
    *   O componente de Chat escuta esse evento e carrega a conversa do contato correspondente.
4.  **Campos Personalizados (IA)**:
    *   A extração de campos pertence ao domínio do Kanban (contexto do lead/atendimento). A IA analisará o histórico de mensagens de forma assíncrona para extrair dados estruturados, sem impactar a performance do chat.

---

## 2. Faseamento do Projeto

A entrega será dividida para garantir que cada módulo seja maduro e funcional independentemente antes de serem fundidos.

### Fase 1: App `chat_app` (Experiência WhatsApp Web)
**Objetivo**: Construir um chat completo e fluido, sem dependência do kanban.

*   **Responsabilidades**:
    *   Listagem de conversas (contatos recentes).
    *   Janela de chat completa com histórico paginado.
    *   Envio e recebimento de texto e mídias via Evolution API.
    *   Real-time via SSE exclusivo para chat (`message.new`, `message.sent`).
    *   Leitura de mensagens (marcar como lido).
*   **Design**: Sidebar esquerdo com lista de contatos, área central com chat completo.
*   **Integração Evolution API**: Garantir suporte a envio de arquivos (`sendMedia`), áudios e mensagens de texto de forma otimizada.

### Fase 2: App `gestao_kanban` (Trello Avançado + IA)
**Objetivo**: Construir o motor de kanban focado no tenant.

*   **Responsabilidades**:
    *   Visualização de quadros por `FluxoAtendimento` e colunas por `EtapaFluxo`.
    *   Movimentação de cards (drag-and-drop) aplicando regras automáticas de `tipo_etapa` (assumir atendimento, pendência, finalização).
    *   Campos Personalizados: Definição por tenant/fluxo.
    *   Extração por IA: Task assíncrona que lê as mensagens do atendimento e extrai valores para os campos personalizados.
    *   SSE exclusivo para kanban (`board.moved`, `card.updated`).
*   **Design**: Quadro Kanban em tela cheia (full-width), cartões ricos com badges de tags, status, prioridade e mini-chips de campos customizados. Clicar no cartão abre um modal/painel com os detalhes do atendimento (ainda sem o chat interativo, apenas dados do lead).

### Fase 3: App `atendimento_unificado` (União de Layout)
**Objetivo**: A "casca" que integra os dois.

*   **Responsabilidades**:
    *   Fornecer a view principal `/workspace/`.
    *   Carregar o componente de colunas do `gestao_kanban` na área central.
    *   Carregar o drawer/painel lateral do `chat_app`.
    *   Orquestrar a interação no frontend: `onCardClick` no kanban -> `openChat(atendimentoId)` no componente de chat.
*   **Design**: Mantém o layout 3 colunas ou Kanban + Drawer Lateral.
    *   Modo 1: Kanban principal. Ao clicar no card, o Chat abre em um Drawer flutuante.
    *   Modo 2: Split-screen (Kanban ocupando 60% e Chat ocupando 40% da tela).

---

## 3. Detalhamento Técnico das Aplicações

### 3.1. `chat_app`
*   **APIs**:
    *   `GET /chat/conversations/`
    *   `GET /chat/conversations/<id>/messages/`
    *   `POST /chat/conversations/<id>/send/` (Texto e Mídia)
    *   `POST /chat/conversations/<id>/mark-read/`
*   **SSE**: Retorna atualizações puras de troca de mensagens.
*   **Modelos Próprios**: `LeituraAtendimento` (para gerenciar não-lidos sem poluir tabelas globais).

### 3.2. `gestao_kanban`
*   **APIs**:
    *   `GET /kanban/boards/`
    *   `GET /kanban/boards/<id>/cards/`
    *   `POST /kanban/cards/<id>/move/`
    *   `PATCH /kanban/cards/<id>/custom-fields/`
*   **Feature IA**:
    *   Módulo `extracao_campos` engatilhado via signal quando há nova mensagem.
    *   Uso de schema Pydantic dinâmico no LangChain para buscar os campos pendentes definidos no `CampoPersonalizado`.
*   **Modelos Próprios**: `CampoPersonalizado` (definição) e `ValorCampoAtendimento` (valor extraído ou preenchido manualmente).

### 3.3. `atendimento_unificado`
*   **Estrutura de Arquivos Fina**:
    ```text
    atendimento_unificado/
      urls.py
      views.py
      templates/atendimento_unificado/
        workspace.html (O layout integrado)
      static/atendimento_unificado/
        js/workspace_coordinator.js (Alpine.js orquestrando eventos cross-app)
    ```

---

## 4. Design System e UX

O design manterá a paleta definida no `base_dashboard.html`, mas a componentização será estrita por app:
*   **Chat UI**: Componentes de bolhas de chat, composer, gravação de áudio, anexos, renderizados nativamente pelo `chat_app`.
*   **Kanban UI**: Componentes de colunas, cards arrastáveis (`SortableJS`), badges de SLA, renderizados pelo `gestao_kanban`.
*   **Orquestrador UI**: O `atendimento_unificado` se encarrega de transições suaves e estados de loading durante a montagem das duas interfaces na mesma tela.

## 5. Próximos Passos (Plano de Ação PREVC)

1.  **P (Planning)**: Este documento serve como plano base atualizado.
2.  **E (Execution) - Fase 1**: Criar o app `chat_app` ou adaptar o existente para operar isoladamente focado 100% no Evolution API.
3.  **E (Execution) - Fase 2**: Criar o app `gestao_kanban` implementando a lógica de Trello e as tabelas de Campos Personalizados.
4.  **E (Execution) - Fase 3**: Desenvolver o template unificador no app `atendimento_unificado`.
5.  **V (Validation)**: Testar SSE independente, arrasto de cards e extração de IA sem gargalos de performance.
6.  **C (Confirmation)**: Limpeza do código monolítico anterior.

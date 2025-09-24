# Arquitetura da Central de Atendimento

## 1. Visão Geral

O objetivo é criar uma central de atendimento multicanal e multidepartamental, onde um chatbot realiza a triagem inicial e, quando necessário, transfere o atendimento para um agente humano do departamento apropriado.

A arquitetura será baseada em microsserviços e eventos para garantir escalabilidade, resiliência e manutenibilidade.

## 2. Componentes Principais

1.  **Gateway de Mensagens (Webhook)**: Ponto de entrada para todas as mensagens recebidas (WhatsApp, etc.). Responsável por receber o evento, normalizá-lo e publicá-lo em um tópico específico no broker de mensagens.

2.  **Broker de Mensagens (Redis Pub/Sub ou RabbitMQ)**: Fila central que desacopla os serviços. O Gateway publica as mensagens aqui, e os outros serviços (Chatbot, Roteador) consomem essas mensagens.

3.  **Serviço do Chatbot**: Consome as mensagens do broker, processa o diálogo com o usuário usando o `AI Engine` já existente e, se a transferência for necessária, publica um evento de "solicitação de transferência" no broker.

4.  **Serviço de Roteamento de Atendimento**:
    *   Consome os eventos de "solicitação de transferência".
    *   Contém a lógica para determinar para qual departamento e, em seguida, para qual atendente disponível o chat deve ser direcionado.
    *   Critérios de roteamento: departamento solicitado, disponibilidade do atendente, carga de trabalho atual, etc.
    *   Após decidir o destino, publica um evento de "atendimento atribuído".

5.  **Serviço de Atendimento Humano**:
    *   Cada atendente terá uma interface (UI) para visualizar e responder aos chats atribuídos.
    *   Este serviço consome os eventos de "atendimento atribuído".
    *   Gerencia o estado da conversa entre o cliente e o atendente.
    *   Envia as respostas do atendente para o Gateway de Mensagens, que as encaminhará para o cliente final via WhatsApp.

6.  **Banco de Dados**:
    *   **PostgreSQL**: Para dados relacionais e estruturados (Departamentos, Atendentes, Clientes, Histórico de Atendimentos).
    *   **PGVector**: Para armazenar e consultar embeddings vetoriais, se necessário para buscas semânticas em conversas futuras.
    *   **Redis**: Para cache e gerenciamento de estado em tempo real (ex: status de disponibilidade dos atendentes, sessões de chat ativas).

7.  **Painel de Administração (UI)**: Interface onde os administradores poderão:
    *   Cadastrar/Gerenciar Departamentos.
    *   Cadastrar/Gerenciar Atendentes e associá-los a departamentos.
    *   Visualizar métricas e relatórios de atendimento.

## 3. Fluxo de Atendimento

1.  **Cliente Inicia Conversa**: O cliente envia uma mensagem para o número de WhatsApp da empresa.
2.  **Webhook Recebe**: A instância da Evolution API (ou similar) associada a esse número dispara um evento para o nosso Gateway de Mensagens.
3.  **Gateway Publica**: O Gateway normaliza a mensagem e a publica no tópico `mensagens_recebidas`.
4.  **Chatbot Processa**: O Serviço do Chatbot consome a mensagem, identifica o cliente (ou o cadastra) e inicia o diálogo. O contexto da conversa é mantido em Redis.
5.  **Transferência Solicitada**: O chatbot identifica a necessidade de transferir. Ele publica um evento no tópico `solicitacoes_transferencia` com informações como `cliente_id` e `departamento_destino`.
6.  **Roteamento Decide**: O Serviço de Roteamento consome o evento, consulta o banco de dados para encontrar um atendente disponível no departamento solicitado e publica um evento no tópico `atendimentos_atribuidos` com `atendimento_id`, `cliente_id` e `atendente_id`.
7.  **Atendente Notificado**: O Serviço de Atendimento Humano (via WebSocket, talvez) notifica a UI do atendente sobre o novo chat.
8.  **Conversa Humana**:
    *   O atendente aceita o chat. A UI exibe o histórico da conversa com o bot.
    *   As mensagens do atendente são enviadas para o Gateway (via API REST ou outro evento).
    *   As mensagens do cliente continuam chegando pelo fluxo normal, mas o Roteador agora as direciona para o tópico do atendente específico.
9.  **Finalização**: O atendente finaliza o atendimento. O sistema registra o histórico completo no PostgreSQL.

## 4. Modelagem de Dados Inicial

Precisaremos das seguintes entidades no banco de dados:

*   `Departamento`
*   `Atendente` (com relacionamento para `Departamento`)
*   `Cliente`
*   `Atendimento` (registra todo o ciclo, desde o bot até a finalização, com status, timestamps, etc.)
*   `Mensagem` (armazena cada mensagem trocada, com referência ao `Atendimento`)

Este plano será detalhado nos próximos documentos.
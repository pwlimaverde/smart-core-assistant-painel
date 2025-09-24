# Roteiro de Implementação - Central de Atendimento

Este documento descreve o plano passo a passo para implementar a funcionalidade da central de atendimento.

## Fase 1: Estrutura Fundamental e Modelos

**Objetivo:** Criar a base de dados e os modelos Django que darão suporte a toda a funcionalidade.

1.  **Criar a App Django `atendimentos`**:
    *   Executar `uv run task startapp-docker atendimentos`.
    *   Adicionar a nova app em `INSTALLED_APPS`.

2.  **Implementar os Modelos (em `atendimentos/models.py`)**:
    *   `Departamento`: Modelo para os setores da empresa.
    *   `Atendente`: Modelo para os usuários que atenderão os clientes, com FK para `User` e `Departamento`.
    *   `Cliente`: Modelo para armazenar os contatos.
    *   `Atendimento`: Modelo central para registrar cada sessão de chat.
    *   `Mensagem`: Modelo para armazenar cada mensagem trocada.
    *   Seguir a estrutura definida em `modelagem_dados.md`.

3.  **Gerar e Aplicar as Migrações**:
    *   `uv run task makemigrations-docker atendimentos`
    *   `uv run task migrate-docker`

4.  **Criar Painéis no Django Admin**:
    *   Registrar todos os novos modelos em `atendimentos/admin.py` para permitir o gerenciamento inicial dos dados.

## Fase 2: Lógica de Roteamento e Atribuição

**Objetivo:** Implementar o serviço que decide para qual atendente um chat deve ser enviado.

1.  **Criar o Serviço de Roteamento (`RoutingService`)**:
    *   Local: `src/smart_core_assistant_painel/modules/services/features/routing_service.py`.
    *   Responsabilidade: Conter a lógica para selecionar o melhor atendente para um novo chat.
    *   Método principal: `get_available_agent(department_id: UUID) -> Atendente | None`.
    *   Critérios iniciais: Buscar um atendente online no departamento solicitado que tenha o menor número de atendimentos ativos.

2.  **Integrar com o Broker de Mensagens**:
    *   Criar um consumidor (listener) para o tópico `solicitacoes_transferencia`.
    *   Quando uma mensagem for recebida, este consumidor chamará o `RoutingService`.
    *   Após o serviço encontrar um atendente, o consumidor publicará uma nova mensagem no tópico `atendimentos_atribuidos`.

3.  **Modificar o Chatbot (`AI Engine`)**:
    *   Ajustar a lógica do chatbot para, em vez de apenas responder, poder publicar um evento de `solicitacoes_transferencia` quando a intenção de falar com um humano for detectada.

## Fase 3: Interface do Atendente (UI)

**Objetivo:** Desenvolver a tela onde o atendente irá gerenciar e responder às conversas.

1.  **Criar as Views Django**:
    *   `PainelAtendenteView`: View principal que listará os atendimentos em andamento e aguardando.
    *   `DetalheAtendimentoView`: View que mostrará o histórico de uma conversa específica e permitirá o envio de novas mensagens.

2.  **Desenvolver os Templates HTML**:
    *   Usar o sistema de templates do Django para criar a interface.
    *   A interface deve ser reativa, atualizando em tempo real (ver próximo item).

3.  **Implementar Comunicação em Tempo Real (WebSockets)**:
    *   Usar `Django Channels` ou uma solução similar para notificar a UI do atendente sobre:
        *   Novos atendimentos atribuídos.
        *   Novas mensagens recebidas do cliente.
    *   O frontend (JavaScript) estabelecerá uma conexão WebSocket para receber essas atualizações e atualizar a página dinamicamente.

4.  **Criar o Endpoint para Envio de Mensagem**:
    *   Criar uma API (ex: com Django Rest Framework) para que o frontend possa enviar as respostas do atendente.
    *   Este endpoint receberá a mensagem, salvará no banco de dados e a publicará no broker para ser enviada ao cliente final pelo Gateway.

## Fase 4: Integração e Testes End-to-End

**Objetivo:** Garantir que todos os componentes funcionem juntos de forma harmoniosa.

1.  **Ajustar o Gateway de Mensagens**:
    *   Modificar o webhook para que, ao receber uma mensagem, ele verifique se o chat correspondente já está com um atendente humano.
    *   Se estiver, a mensagem deve ser roteada diretamente para o tópico/fila daquele atendimento/atendente, em vez de ir para o chatbot.

2.  **Criar Testes Automatizados**:
    *   **Testes Unitários**: Para os modelos, serviços (como o `RoutingService`) e views.
    *   **Testes de Integração**: Para simular o fluxo completo: mensagem chega -> chatbot processa -> transfere -> atendente responde.
    *   Garantir que a cobertura de testes atinja o mínimo de 80% estipulado pelo projeto.

3.  **Documentação Final**:
    *   Atualizar o `README.md` e a documentação em `docs/` com as novas funcionalidades e como configurá-las.
    *   Descrever as novas variáveis de ambiente necessárias no `.env.example`.
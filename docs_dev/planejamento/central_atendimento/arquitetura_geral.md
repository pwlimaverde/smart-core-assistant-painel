# Arquitetura da Central de Atendimento: Abordagem Monolítica com Django

## 1. Visão Geral

O objetivo é criar uma central de atendimento multicanal e multidepartamental, onde um chatbot realiza a triagem inicial e transfere o atendimento para um agente humano quando necessário.

Para acelerar o desenvolvimento e aproveitar a estrutura existente, a implementação será feita dentro da **aplicação monolítica Django** atual. A arquitetura utilizará os recursos robustos do ecossistema Django para garantir escalabilidade e manutenibilidade.

## 2. Componentes Principais (Arquitetura Monolítica Django)

1.  **Aplicação Django Principal**: O coração do sistema, orquestrando todas as funcionalidades. A lógica da central de atendimento será modularizada em apps Django específicos.
    *   **App `atendimentos`**: Conterá os modelos (`Atendimento`, `StatusAtendimento`), a lógica de negócio (`services.py`), os endpoints da API (`views.py`, `serializers.py`) e a comunicação em tempo real (`consumers.py`).
    *   **App `clientes`**: Gerencia os dados dos clientes (`Cliente`, `Contato`).
    *   **App `operacional`**: Gerencia a estrutura interna da empresa (`Departamento`, `AtendenteHumano`).

2.  **Django REST Framework (DRF)**: Será utilizado para construir a API RESTful que servirá como ponte entre o backend e a interface do usuário (frontend).

3.  **Django Channels**: Para a comunicação em tempo real. Permitirá que o servidor envie atualizações automáticas para a interface do Kanban via WebSockets sempre que um atendimento mudar de estado (novo, atribuído, transferido, etc.).

4.  **Django Signals**: Atuarão como um mecanismo de eventos interno. Por exemplo, um sinal `post_save` no modelo `Atendimento` será usado para disparar uma notificação via WebSocket após qualquer alteração, garantindo que a UI esteja sempre sincronizada.

5.  **Banco de Dados (PostgreSQL)**: O banco de dados relacional existente, gerenciado inteiramente pelo ORM do Django.

6.  **Frontend (SPA)**: Uma aplicação de página única (desenvolvida em React, Vue.js, ou similar) que consumirá a API DRF para buscar dados e se conectará via WebSocket para receber atualizações em tempo real.

## 3. Fluxo de Atendimento (Integrado ao Django)

1.  **Entrada de Mensagens**: Um serviço externo (ex: webhook de um provedor de WhatsApp) interage com um endpoint específico da nossa API, criado com DRF.

2.  **Processamento na API View**: A `APIView` correspondente recebe a requisição, identifica o cliente (ou o cadastra), e cria ou atualiza um registro do modelo `Atendimento`.

3.  **Lógica de Roteamento**: Se o atendimento precisar de intervenção humana, a `APIView` invoca uma função de serviço (ex: `atribuir_proximo_atendimento` do `atendimentos/services.py`). Esta função contém a lógica de negócio para encontrar o atendente mais adequado.

4.  **Disparo do Sinal `post_save`**: Ao salvar o modelo `Atendimento` com seu novo status ou atendente, o Django dispara automaticamente um sinal `post_save`.

5.  **Notificação via WebSocket**: Um *handler* conectado a esse sinal executa a lógica para enviar uma mensagem através do Django Channels para um grupo específico (ex: `kanban_departamento_{id_do_departamento}`).

6.  **Atualização da UI em Tempo Real**: O frontend, que está inscrito nesse grupo de WebSocket, recebe a mensagem e atualiza o estado do painel Kanban, movendo, adicionando ou atualizando o card do atendimento sem a necessidade de recarregar a página.

7.  **Interação do Atendente na UI**: Quando um atendente realiza uma ação (ex: arrasta um card para uma nova coluna, clica em "transferir"), o frontend envia uma requisição para o endpoint DRF correspondente (ex: `POST /api/atendimentos/{id}/atualizar-status/`).

8.  **Ciclo de Atualização**: A `APIView` processa a requisição, atualiza o modelo no banco de dados, o que novamente dispara o sinal `post_save`, e a mudança é transmitida em tempo real para todos os clientes conectados.

## 4. Modelagem de Dados

A estrutura detalhada das tabelas e campos, perfeitamente alinhada com os modelos Django já implementados, está documentada no arquivo [modelagem_dados.md](./modelagem_dados.md).
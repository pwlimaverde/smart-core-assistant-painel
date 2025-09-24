# Checklist de Desenvolvimento: Central de Atendimento Kanban

Este documento detalha as tarefas técnicas necessárias para implementar a Central de Atendimento com a interface Kanban, alinhado aos modelos Django existentes e ao planejamento de UI.

---

## Fase 1: Backend - Lógica de Negócio e Serviços

Implementação das regras de negócio que governam o fluxo de atendimento, utilizando os modelos já existentes.

- **Tarefa 1.1: Implementar Lógica de Roteamento e Atribuição**
  - **Local Sugerido:** `src/smart_core_assistant_painel/app/ui/atendimentos/services.py` (criar se não existir).
  - **Ações:**
    - [ ] **Função `atribuir_proximo_atendimento(departamento_id)`:**
      - [ ] Implementar a lógica "Round Robin com Nivelamento":
        1. Buscar atendentes com `disponivel=True` no departamento especificado.
        2. Filtrar atendentes que ainda não atingiram `max_atendimentos_simultaneos` (contando seus atendimentos `ativos`).
        3. Ordenar os atendentes elegíveis pela `data_ultima_atribuicao` (do mais antigo para o mais novo).
        4. Buscar o atendimento mais antigo na fila (ex: `status__nome='Pendente'`) para aquele departamento.
        5. Atribuir o atendimento ao atendente selecionado, atualizando `atendimento.atendente`.
        6. Atualizar o status do atendimento para `Em Andamento` (`status__nome='Em Andamento'`).
        7. Atualizar a `data_ultima_atribuicao` do atendente.

- **Tarefa 1.2: Implementar Lógica de Transferência**
  - **Local Sugerido:** `src/smart_core_assistant_painel/app/ui/atendimentos/services.py`.
  - **Ações:**
    - [ ] **Função `transferir_atendimento_para_departamento(atendimento_id, novo_departamento_id, nota_interna)`:**
      - [ ] Desvincular o `atendente` do atendimento (`atendimento.atendente = None`).
      - [ ] Atualizar o `departamento` do atendimento para o `novo_departamento_id`.
      - [ ] Mudar o `status` do atendimento para `Pendente`.
      - [ ] (Opcional) Adicionar a `nota_interna` a um futuro modelo de histórico/log.
      - [ ] Disparar a lógica de `atribuir_proximo_atendimento` para o novo departamento.
    - [ ] **Função `transferir_atendimento_para_atendente(atendimento_id, novo_atendente_id, nota_interna)`:**
      - [ ] Validar se o `novo_atendente_id` pertence a um departamento e está `disponivel`.
      - [ ] Atribuir o atendimento ao `novo_atendente_id`.
      - [ ] Atualizar o `departamento` do atendimento para o departamento do novo atendente.
      - [ ] Manter o `status` como `Em Andamento`.
      - [ ] (Opcional) Adicionar a `nota_interna` ao histórico.

---

## Fase 2: Backend - API e Comunicação em Tempo Real

Exposição dos dados e eventos para o frontend consumir.

- **Tarefa 2.1: Criar/Ajustar Endpoints da API (Django REST Framework)**
  - **Local:** `src/smart_core_assistant_painel/app/ui/atendimentos/views.py` e `serializers.py`.
  - **Ações:**
    - [ ] **Endpoint `GET /api/departamentos/`:**
      - [ ] Listar todos os departamentos `ativos`.
    - [ ] **Endpoint `GET /api/departamentos/{id}/atendimentos/`:**
      - [ ] Retornar os atendimentos `ativos` de um departamento, serializados com informações do cliente e status.
      - [ ] O frontend será responsável por agrupar em colunas (Fila, Em Atendimento, etc.) com base no campo `status.nome`.
    - [ ] **Endpoint `POST /api/atendimentos/{id}/transferir-departamento/`:**
      - [ ] Body: `{ "novo_departamento_id": "ID" }`.
      - [ ] Chama o serviço `transferir_atendimento_para_departamento`.
    - [ ] **Endpoint `POST /api/atendimentos/{id}/transferir-atendente/`:**
      - [ ] Body: `{ "novo_atendente_id": "ID", "nota_interna": "texto" }`.
      - [ ] Chama o serviço `transferir_atendimento_para_atendente`.
    - [ ] **Endpoint `POST /api/atendimentos/{id}/atualizar-status/`:**
      - [ ] Body: `{ "novo_status_id": "ID" }`.
      - [ ] Implementar a lógica para alterar o status de um atendimento (ex: de `Em Andamento` para `Aguardando Cliente`).

- **Tarefa 2.2: Configurar Comunicação via WebSocket (Django Channels)**
  - **Local:** `src/smart_core_assistant_painel/app/ui/atendimentos/consumers.py` (criar se não existir).
  - **Ações:**
    - [ ] **Consumer `KanbanConsumer`:**
      - [ ] Permitir que o frontend se inscreva em "grupos" baseados no departamento (ex: `kanban_departamento_{id}`).
      - [ ] Transmitir eventos quando um atendimento for alterado (criado, atribuído, transferido, status modificado).
        - Exemplo de evento: `evento: 'ATENDIMENTO_ATUALIZADO', dados: { ...serialização completa do atendimento... }`

- **Tarefa 2.3: Integrar Sinais do Django com Channels**
  - **Local:** `src/smart_core_assistant_painel/app/ui/atendimentos/signals.py`.
  - **Ação:**
    - [ ] Usar o sinal `post_save` no modelo `Atendimento` para detectar alterações.
    - [ ] No handler do sinal, obter o `departamento` do atendimento e disparar o evento WebSocket para o grupo correspondente (`kanban_departamento_{atendimento.departamento.id}`).

---

## Fase 3: Frontend - Implementação da UI Kanban

Construção da interface visual da central de atendimento.

- **Tarefa 3.1: Estrutura do Painel (React/Vue/etc.)**
  - **Ações:**
    - [ ] Criar um componente `PainelKanban` que recebe um `departamentoId`.
    - [ ] Ao montar, buscar os dados iniciais via API (`GET /api/departamentos/{id}/atendimentos/`).
    - [ ] Renderizar as colunas com base nos `StatusAtendimento` possíveis (ex: "Pendente", "Em Andamento", "Aguardando Cliente").
    - [ ] Renderizar os `CardsAtendimento` dentro das colunas apropriadas, com base no `atendimento.status.nome`.

- **Tarefa 3.2: Componente `CardAtendimento`**
  - **Ações:**
    - [ ] Exibir informações: `cliente.nome_social`, tempo desde `data_ultima_mensagem`.
    - [ ] Implementar drag-and-drop entre as colunas.
      - Ao soltar, chamar o endpoint `POST /api/atendimentos/{id}/atualizar-status/` com o ID do novo status.

- **Tarefa 3.3: Funcionalidade de Transferência na UI**
  - **Ações:**
    - [ ] Adicionar um menu de opções no `CardAtendimento`.
    - [ ] Criar um modal de transferência que permita selecionar um novo departamento ou um atendente específico.
    - [ ] Ao confirmar, chamar o endpoint de transferência correspondente na API.

- **Tarefa 3.4: Integração com WebSocket no Frontend**
  - **Ações:**
    - [ ] Conectar ao WebSocket e se inscrever no grupo do departamento (`kanban_departamento_{id}`).
    - [ ] Implementar a lógica para atualizar o estado da UI em tempo real quando o evento `ATENDIMENTO_ATUALIZADO` for recebido, movendo, adicionando ou atualizando os cards sem recarregar a página.

---

## Fase 4: Testes e Validação

Garantir a robustez e o funcionamento correto da implementação.

- **Tarefa 4.1: Testes de Backend**
  - **Ações:**
    - [ ] Criar testes unitários para os serviços em `atendimentos/services.py`.
    - [ ] Criar testes de integração para os endpoints da API, validando as respostas e os dados.
    - [ ] **Comando:** `uv run task test-docker`

- **Tarefa 4.2: Testes de Frontend**
  - **Ações:**
    - [ ] Criar testes de componentes para `PainelKanban` e `CardAtendimento`.
    - [ ] Simular interações do usuário, como drag-and-drop e transferência.

- **Tarefa 4.3: Testes End-to-End (E2E)**
  - **Ação:**
    - [ ] Criar um cenário de teste completo simulando o fluxo de um atendimento, desde a chegada na fila até a transferência e finalização, validando as atualizações na UI em tempo real.
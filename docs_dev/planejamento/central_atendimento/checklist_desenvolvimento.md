# Checklist de Desenvolvimento da Central de Atendimento

Este checklist detalha as tarefas técnicas necessárias para implementar a central de atendimento humano, com base no planejamento definido nos documentos de arquitetura e lógica de roteamento.

## Fase 1: Estrutura e Modelos de Dados

- [ ] **1.1. Modificar o modelo `Atendimento`:**
    - [ ] Adicionar o campo `departamento` (`ForeignKey` para `operacional.Departamento`).
    - [ ] Alterar o campo `atendente_humano` para permitir valores nulos (`null=True`).
    - [ ] Gerar e aplicar a migração do banco de dados (`uv run task makemigrations` e `uv run task migrate`).

- [ ] **1.2. Modificar o modelo `AtendenteHumano`:**
    - [ ] Adicionar o campo `data_ultima_atribuicao` (`DateTimeField`, `null=True`, `blank=True`).
    - [ ] Gerar e aplicar a migração correspondente.

- [ ] **1.3. Atualizar os Testes dos Modelos:**
    - [ ] Adaptar os testes existentes em `atendimentos/tests/test_models.py` para refletir as mudanças.
    - [ ] Criar novos testes para garantir que a relação com `Departamento` funciona e que `atendente_humano` pode ser nulo.
    - [ ] Adaptar os testes em `operacional/tests/test_models.py` para o novo campo em `AtendenteHumano`.

## Fase 2: Lógica de Roteamento e Atribuição

- [ ] **2.1. Criar o Serviço de Roteamento (`RoutingService`):**
    - [ ] Criar um novo módulo de serviço, por exemplo, `src/smart_core_assistant_painel/app/atendimento_humano/services.py`.
    - [ ] Implementar a função `transferir_para_departamento(atendimento_id, departamento_id)`:
        - [ ] Altera o status do atendimento para `AGUARDANDO_ATENDENTE`.
        - [ ] Associa o `departamento` ao atendimento.
        - [ ] Garante que `atendente_humano` seja `None`.
        - [ ] Adiciona um registro ao histórico da conversa.

- [ ] **2.2. Criar o Serviço de Atribuição (`AssignmentService`):**
    - [ ] No mesmo módulo de serviço, implementar a função `atribuir_proximo_atendimento(departamento_id)`.
    - [ ] Implementar a lógica de seleção do atendente ideal, seguindo os critérios:
        1.  Filtros essenciais (ativo, disponível, no departamento, horário de trabalho).
        2.  Menor número de atendimentos ativos (`get_atendimentos_ativos() < max_atendimentos_simultaneos`).
        3.  Round-robin (ordenar por `data_ultima_atribuicao` ascendente).
    - [ ] Implementar a lógica de atribuição (vincular atendente, atualizar status, atualizar `data_ultima_atribuicao`).
    - [ ] Adicionar tratamento para o caso de nenhum atendente estar disponível.

- [ ] **2.3. Criar Tarefa Assíncrona (Celery/RQ):**
    - [ ] Criar uma tarefa que chama `AssignmentService.atribuir_proximo_atendimento` para um departamento.
    - [ ] Esta tarefa será acionada quando um novo atendimento entrar na fila ou quando um atendente ficar disponível.

- [ ] **2.4. Implementar Testes para os Serviços:**
    - [ ] Criar testes unitários e de integração para `RoutingService` e `AssignmentService`.
    - [ ] Simular diferentes cenários: atendente disponível, múltiplos atendentes com cargas diferentes, nenhum atendente disponível, etc.

## Fase 3: Integração e API

- [ ] **3.1. Adaptar o Webhook de Mensagens:**
    - [ ] Modificar a view que recebe os webhooks do chatbot/Evolution API.
    - [ ] Quando o chatbot decidir pela transferência, a view deve chamar o `RoutingService.transferir_para_departamento`.

- [ ] **3.2. Criar Endpoints de API (DRF):**
    - [ ] Criar um endpoint para que um atendente possa se marcar como `disponivel` / `indisponivel`.
    - [ ] Criar um endpoint para listar os atendimentos na fila de um departamento.
    - [ ] Criar um endpoint para um atendente "pegar" um atendimento manualmente (opcional, mas útil).

- [ ] **3.3. Integração com WebSocket (Django Channels):**
    - [ ] Configurar um consumidor WebSocket para o painel dos atendentes.
    - [ ] Enviar notificações em tempo real quando:
        - [ ] Um novo atendimento entra na fila do departamento.
        - [ ] Um atendimento é atribuído a um atendente específico.
        - [ ] O status de um atendimento muda.

## Fase 4: Interface do Atendente (UI)

- [ ] **4.1. Criar a Visualização da Fila de Atendimento:**
    - [ ] Desenvolver um componente de UI que exiba a lista de atendimentos no status `AGUARDANDO_ATENDENTE` para o departamento do atendente logado.
    - [ ] A lista deve ser atualizada em tempo real via WebSocket.

- [ ] **4.2. Adaptar a Tela de Atendimento:**
    - [ ] A UI deve exibir claramente a qual atendente um atendimento está atribuído.
    - [ ] Implementar a funcionalidade para o atendente enviar e receber mensagens no contexto do atendimento.

- [ ] **4.3. Adicionar Controles de Disponibilidade:**
    - [ ] Implementar um botão/toggle na UI para que o atendente possa alterar seu status de `disponivel` para `indisponivel` (e vice-versa), chamando a API correspondente.

## Fase 5: Testes End-to-End e Validação

- [ ] **5.1. Criar Cenários de Teste E2E:**
    - [ ] Simular um fluxo completo: cliente inicia conversa -> chatbot transfere -> atendimento cai na fila -> sistema atribui ao atendente A -> atendente A resolve.
    - [ ] Testar o cenário com múltiplos atendentes para validar o balanceamento de carga.
    - [ ] Testar o cenário sem atendentes disponíveis e a posterior atribuição quando um se torna disponível.

- [ ] **5.2. Validação Funcional:**
    - [ ] Realizar testes manuais no painel para garantir que a UI se comporta como esperado.
    - [ ] Validar que as notificações e atualizações em tempo real estão funcionando corretamente.
# Planejamento de Lógica e Modelos para a Central de Atendimento

Este documento detalha as modificações necessárias nos modelos de dados e a lógica de negócio para roteamento, transferência e atribuição de atendimentos na nova central de atendimento humano.

## 1. Análise e Modificações nos Modelos

A análise dos modelos `Atendimento`, `AtendenteHumano` e `Departamento` revela uma base sólida. No entanto, para suportar uma fila de atendimento por departamento, são necessárias algumas adaptações.

### 1.1. Modelo `Atendimento` (`atendimentos/models.py`)

**Necessidade:** Um atendimento transferido pelo chatbot precisa entrar em uma "fila" de um departamento antes de ser atribuído a um atendente específico.

**Modificações Propostas:**

1.  **Adicionar `ForeignKey` para `Departamento`:**
    *   Criar um campo `departamento` que estabelece um vínculo direto com o modelo `Departamento`.
    *   Este campo será preenchido no momento da transferência.

    ```python
    # Em Atendimento
    departamento: models.ForeignKey[Optional["Departamento"]] = models.ForeignKey(
        "operacional.Departamento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atendimentos",
        help_text="Departamento para o qual o atendimento foi direcionado.",
    )
    ```

2.  **Tornar `atendente_humano` opcional:**
    *   O campo `atendente_humano` deve permitir valores nulos (`null=True`), pois um atendimento na fila do departamento ainda não tem um atendente designado.

    ```python
    # Em Atendimento
    atendente_humano: models.ForeignKey[Optional["AtendenteHumano"]] = models.ForeignKey(
        "operacional.AtendenteHumano",
        on_delete=models.SET_NULL,
        null=True,  # Alterar para True
        blank=True,
        related_name="atendimentos",
        help_text="Atendente humano responsável pelo atendimento.",
    )
    ```

### 1.2. Modelo `AtendenteHumano` (`operacional/models.py`)

**Necessidade:** Para implementar um sistema de distribuição mais justo (como round-robin), é útil saber quando um atendente recebeu seu último atendimento.

**Modificação Proposta:**

1.  **Adicionar `data_ultima_atribuicao`:**
    *   Este campo registrará o timestamp exato de quando um atendimento foi atribuído ao atendente.

    ```python
    # Em AtendenteHumano
    data_ultima_atribuicao: models.DateTimeField[datetime | None] = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e hora da última atribuição de um novo atendimento.",
    )
    ```

## 2. Lógica de Transferência e Atribuição

A eficiência da central de atendimento depende de uma lógica de roteamento e atribuição bem definida, garantindo que o cliente seja direcionado corretamente e que a carga de trabalho seja distribuída de forma justa entre os atendentes.

### 2.1. Lógica de Transferência: Chatbot para Departamento (Baseada em Intenção)

O ponto central da automação é a capacidade do chatbot de realizar uma triagem inteligente e transferir o atendimento para o departamento correto.

**Fluxo de Transferência:**

1.  **Análise de Intenção:** Durante a conversa, o chatbot (integrado ao `AIEngine`) analisa continuamente a mensagem do cliente para identificar a **intenção** principal.
    *   **Exemplo:** Uma mensagem como "não consigo pagar minha fatura" seria classificada com a intenção `PAGAMENTOS_ERRO`.

2.  **Mapeamento de Intenção para Departamento:** O sistema terá uma configuração (seja em um arquivo de configuração, ou em um modelo no banco de dados) que mapeia cada intenção a um departamento específico.
    *   `PAGAMENTOS_ERRO` -> Departamento "Financeiro"
    *   `PRODUTO_DUVIDA` -> Departamento "Vendas"
    *   `SUPORTE_TECNICO` -> Departamento "Suporte"

3.  **Decisão de Transferência:** Quando o chatbot determina que a solicitação ultrapassa sua capacidade de resolução ou que a intenção claramente pertence a um time humano, ele inicia o processo de transferência.

4.  **Execução da Transferência:**
    *   O chatbot chama uma função interna, como `atendimento.transferir_para_departamento(departamento_id)`.
    *   O status do atendimento é alterado para `AGUARDANDO_ATENDENTE`.
    *   O campo `atendimento.departamento` é preenchido com o ID do departamento mapeado.
    *   O card de atendimento, que estava na coluna "Em Atendimento (Chatbot)", é movido para a coluna "Fila Humano" no painel Kanban do departamento correspondente.
    *   O chatbot envia uma mensagem de confirmação ao cliente, como: "Entendi. Estou transferindo seu atendimento para nossa equipe do setor Financeiro. Em breve, um de nossos especialistas irá atendê-lo."

**Exceção - Intenção Não Mapeada:**
*   Se a intenção não for claramente identificada ou não tiver um mapeamento, o atendimento pode ser direcionado a um departamento "Geral" ou "Triagem", onde um atendente humano fará a classificação manual.

### 2.2. Lógica de Atribuição: Departamento para Atendente

Este fluxo descreve o ciclo de vida de um atendimento desde o chatbot até a resolução por um atendente humano.

### Fase 1: Transferência (Chatbot -> Departamento)

1.  **Gatilho de Transferência:** O chatbot, com base no fluxo da conversa e na intenção do usuário (ex: "falar com um especialista", "problema complexo", ou seleção em um menu), decide que a intervenção humana é necessária.
2.  **Identificação do Departamento:** O chatbot determina o departamento de destino. Isso pode ocorrer de várias formas:
    *   **Seleção Explícita:** O usuário escolhe o departamento em um menu ("Vendas", "Suporte", "Financeiro").
    *   **Inferência por IA:** O modelo de linguagem do chatbot analisa a conversa e infere o departamento mais apropriado com base no assunto.
3.  **Atualização do Objeto `Atendimento`:**
    *   O status do atendimento é alterado para `StatusAtendimento.AGUARDANDO_ATENDENTE`.
    *   O campo `atendimento.departamento` é preenchido com o `Departamento` identificado.
    *   O campo `atendimento.atendente_humano` permanece `NULL`.
    *   Uma mensagem interna é registrada no histórico, informando que o atendimento foi transferido para a fila do departamento X.
4.  **Notificação (Webhook/WebSocket):** O sistema dispara um evento para o frontend (painel dos atendentes), sinalizando que um novo atendimento entrou na fila do departamento.

### Fase 2: Atribuição (Departamento -> Atendente)

Esta é a lógica central para decidir qual atendente disponível receberá o próximo atendimento da fila.

1.  **Gatilho de Atribuição:** A atribuição pode ser acionada de duas formas:
    *   **Automática (Push):** Assim que um atendimento entra na fila, o sistema tenta imediatamente atribuí-lo a um atendente.
    *   **Manual (Pull):** Um atendente clica em "Pegar próximo atendimento" em seu painel. (Menos ideal para distribuição balanceada).

2.  **Lógica de Seleção do Atendente (Ordem de Prioridade):**

    Para um dado `departamento`, o sistema deve buscar o melhor `AtendenteHumano` com base nos seguintes critérios, em ordem:

    a. **Filtros Essenciais (Regras de Exclusão):**
        *   `departamento` = Departamento do atendimento em questão.
        *   `ativo` = `True`.
        *   `disponivel` = `True`.
        *   O atendente não pode estar fora do seu `horario_trabalho` (se definido).

    b. **Critério 1: Carga de Trabalho (Menos Atendimentos Ativos)**
        *   O sistema calcula o número de atendimentos ativos para cada atendente elegível usando o método `get_atendimentos_ativos()`.
        *   A prioridade é dada aos atendentes com o menor número de atendimentos ativos.
        *   **Regra:** `atendimentos_ativos < max_atendimentos_simultaneos`.

    c. **Critério 2: Round-Robin (Distribuição Justa)**
        *   Dentre os atendentes que atendem aos critérios anteriores e têm a menor carga de trabalho, o sistema seleciona aquele que está há mais tempo sem receber um novo atendimento.
        *   **Regra:** Ordenar os atendentes elegíveis por `data_ultima_atribuicao` em ordem ascendente (do mais antigo para o mais recente). O primeiro da lista é o escolhido.

    d. **(Opcional) Critério 3: Especialidade**
        *   Se o `atendimento` tiver `tags` ou um `contexto` que possa ser mapeado para as `especialidades` do atendente, esse critério pode ser usado para refinar a seleção.

3.  **Processo de Atribuição:**
    *   Uma vez que o atendente ideal é selecionado, o sistema executa as seguintes ações em uma transação de banco de dados:
        1.  **Vincular Atendente:** O campo `atendimento.atendente_humano` é preenchido com o `AtendenteHumano` selecionado.
        2.  **Atualizar Status:** O status do atendimento muda de `AGUARDANDO_ATENDENTE` para `EM_ANDAMENTO`.
        3.  **Atualizar Timestamp:** O campo `atendente.data_ultima_atribuicao` é atualizado com o `datetime.now()`.
    *   **Notificação:** O sistema notifica o atendente selecionado (via WebSocket para o painel) que um novo atendimento foi atribuído a ele, e a UI é atualizada em tempo real.
    *   **Mensagem ao Cliente:** Uma mensagem automática é enviada ao cliente, informando: "Olá! Você está sendo atendido por {atendente.nome}."

## 3. Fluxo de Exceção

*   **Nenhum Atendente Disponível:** Se a lógica de atribuição não encontrar nenhum atendente que satisfaça os critérios, o atendimento permanece na fila (`atendente_humano` = `NULL`, `status` = `AGUARDANDO_ATENDENTE`). O sistema pode:
    *   Enviar uma mensagem ao cliente: "Todos os nossos atendentes estão ocupados no momento. Por favor, aguarde um instante."
    *   Re-tentar a lógica de atribuição periodicamente (ex: a cada 30 segundos) ou quando o status de um atendente do departamento mudar para `disponivel`.

### 2.3. Lógica de Transferência: Humano para Humano (Entre Departamentos ou Atendentes)

Este fluxo permite que um atendente redirecione um caso para outro departamento ou para um colega mais qualificado, garantindo que o cliente seja sempre atendido pelo especialista certo.

1.  **Gatilho da Transferência:**
    *   O atendente, a partir de um atendimento que está sob sua responsabilidade (status `EM_ANDAMENTO`), clica no botão "Transferir" na interface do Kanban.

2.  **Seleção do Destino (Via Modal na UI):**
    *   O atendente escolhe o destino:
        *   **Transferir para Departamento:** Seleciona um novo departamento da lista (ex: "Financeiro"). O atendimento entrará na fila geral deste departamento.
        *   **Transferir para Atendente:** Seleciona um departamento e, em seguida, um atendente específico dentro daquele departamento.
    *   O atendente pode (e deve ser encorajado a) adicionar uma **nota interna** explicando o motivo da transferência. Essa nota fica registrada no histórico do atendimento.

3.  **Execução da Transferência (Ações do Sistema):**
    *   O sistema executa as seguintes ações em uma transação:
        1.  **Registrar Nota:** A nota interna da transferência é salva no histórico do atendimento.
        2.  **Desvincular Atendente Atual:** O campo `atendimento.atendente_humano` é definido como `NULL`.
        3.  **Atualizar Departamento:** O campo `atendimento.departamento` é atualizado para o novo departamento de destino.
        4.  **Atualizar Status:** O status do atendimento volta a ser `AGUARDANDO_ATENDENTE`.

4.  **Chegada no Destino e Notificação:**
    *   **Caso 1 (Transferência para Departamento):**
        *   O atendimento aparece na coluna "Fila de Atendimento" do painel do novo departamento.
        *   O sistema dispara a lógica de atribuição automática (descrita na seção 2.2) para encontrar um novo atendente nesse departamento.
    *   **Caso 2 (Transferência para Atendente Específico):**
        *   O sistema tenta atribuir diretamente ao atendente escolhido. Se ele estiver disponível (`disponivel=True` e com carga de trabalho permissível), o atendimento é imediatamente vinculado a ele, e o status muda para `EM_ANDAMENTO`.
        *   Se o atendente específico não estiver disponível, o atendimento entra na fila do departamento dele (como no Caso 1), aguardando que ele ou outro colega o assuma.
    *   **Notificações (WebSocket):** O sistema envia eventos para atualizar em tempo real os painéis do atendente de origem (removendo o card), do departamento de destino (adicionando o card) e, se for o caso, do atendente de destino.
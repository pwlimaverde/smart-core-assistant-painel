# Plano de Investigação: Latência no Processamento de Mensagens

## 1. Contexto
Atualmente, o tempo de processamento das mensagens e resposta ao cliente está excedendo o limite aceitável. O objetivo é reduzir esse tempo para **no máximo 20 segundos** entre o envio da mensagem pelo cliente e a resposta do bot.

## 2. Objetivo
Identificar os gargalos no fluxo de processamento de mensagens e implementar otimizações para garantir que a resposta seja entregue dentro do SLA de 20 segundos.

## 3. Estrutura da Task

### Etapa 1: Diagnóstico e Mapeamento de Tempos (Profiling)
**Objetivo:** Quantificar o tempo gasto em cada etapa do pipeline de processamento.

1.  **Análise de Logs Existentes:**
    *   Examinar `log_servidor.txt` e `log_cluster.txt` para identificar timestamps de entrada e saída de mensagens.
    *   Calcular o tempo médio atual de processamento.
2.  **Instrumentação de Logs (Temporária):**
    *   Adicionar logs com timestamps precisos (milissegundos) nos pontos críticos do fluxo:
        *   Recebimento do Webhook (`evolution_sync`).
        *   Disparo de Signals (`post_save` de Mensagem).
        *   Entrada na Fila do Django Q.
        *   Início da execução no `attendance_orchestrator`.
        *   Chamada ao LLM (início e fim).
        *   Processamento de ferramentas/RAG.
        *   Envio da resposta para a API de envio (Evolution API).
3.  **Identificação do "Caminho Crítico":**
    *   Determinar qual componente consome a maior parte do tempo (ex: latência do LLM, fila congestionada, queries lentas no banco, overhead de conexões HTTP).

### Etapa 2: Análise de Código e Infraestrutura
**Objetivo:** Revisar a implementação dos componentes identificados como lentos.

1.  **Revisão do `attendance_orchestrator.py`:**
    *   Verificar se há operações bloqueantes ou síncronas que deveriam ser assíncronas.
    *   Analisar a lógica de construção do contexto (RAG) – está buscando dados demais ou de forma ineficiente?
2.  **Análise de Integrações Externas:**
    *   **LLM:** Verificar o modelo utilizado e seus parâmetros (temperatura, max_tokens). Modelos maiores são mais lentos.
    *   **Evolution API:** Verificar latência de rede e tempo de resposta da API de envio.
    *   **Trello/Outros:** Verificar se integrações secundárias (ex: sync com Trello) estão bloqueando o fluxo principal de resposta.
3.  **Banco de Dados:**
    *   Verificar se há queries pesadas sendo executadas durante o processamento da mensagem (N+1, falta de índices).

### Etapa 3: Proposta de Otimização
**Objetivo:** Definir ações concretas para redução de tempo.

*   *Possíveis ações (a serem confirmadas pelo diagnóstico):*
    *   Uso de `async/await` para I/O bound tasks.
    *   Otimização de prompts para reduzir tokens de entrada/saída (menor custo e tempo).
    *   Paralelização de tarefas independentes (ex: salvar no banco enquanto envia para o LLM).
    *   Cache de contextos frequentes.
    *   Ajuste de prioridade na fila do Django Q.

### Etapa 4: Implementação e Validação
**Objetivo:** Aplicar as correções e medir o resultado.

1.  Implementar as otimizações aprovadas.
2.  Realizar testes de carga simulados.
3.  Monitorar os logs novamente para confirmar se o tempo total baixou para < 20s.

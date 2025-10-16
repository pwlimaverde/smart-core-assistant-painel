# Planejamento de Utilização e Interface (UI/UX) - Painel Kanban

Este documento descreve a visão e o funcionamento do painel da central de atendimento, que será estruturado no formato de um quadro Kanban para proporcionar uma experiência de usuário intuitiva, visual e eficiente para os atendentes e gestores.

## 1. Visão Geral do Painel Kanban

O objetivo é centralizar o fluxo de trabalho em telas distintas e otimizadas para cada perfil. Teremos dois tipos principais de painéis:

1.  **Painel Operacional (Departamentos Humanos):** A interface diária dos atendentes para gerenciar conversas.
2.  **Painel de Monitoramento (Departamento do Chatbot):** Uma visão para gestores acompanharem a performance e as interações do bot.

Cada departamento terá seu próprio quadro, e os atendentes só verão os quadros aos quais pertencem.

### Estrutura do Painel - Departamento de Atendimento Humano

Este é o painel principal para os colaboradores. Ele é projetado para gerenciar o ciclo de vida de um atendimento que requer intervenção humana.

1.  **Fila de Atendimento (Aguardando Atribuição):**
    *   **Conteúdo:** Atendimentos que foram transferidos pelo chatbot e aguardam um atendente. Esta é a caixa de entrada da equipe.
    *   **Status do Atendimento:** `AGUARDANDO_ATENDENTE`.
    *   **Ações:** Um atendente pode se atribuir a um atendimento (ação de "puxar") ou o sistema pode atribuir automaticamente (ação de "empurrar").

2.  **Meus Atendimentos (Ativo):**
    *   **Conteúdo:** Atendimentos sob a responsabilidade direta do atendente logado.
    *   **Status do Atendimento:** `EM_ANDAMENTO` (com `atendente_humano` preenchido).
    *   **Ações:** Interagir com o cliente, mover para "Aguardando Cliente", "Finalizados" ou **iniciar uma transferência**.

3.  **Aguardando Cliente:**
    *   **Conteúdo:** Conversas onde o atendente respondeu e espera um retorno do cliente.
    *   **Status do Atendimento:** `AGUARDANDO_CONTATO`.
    *   **Ações:** Quando o cliente responder, o card retorna automaticamente para "Meus Atendimentos (Ativo)".

4.  **Finalizados:**
    *   **Conteúdo:** Atendimentos resolvidos pelo atendente no dia corrente.
    *   **Status do Atendimento:** `RESOLVIDO`.
    *   **Ações:** O atendente move o card para esta coluna ao finalizar a conversa.

### Estrutura do Painel - Monitoramento do Chatbot

Este painel é exclusivo para o departamento do chatbot e serve como uma ferramenta de monitoramento para gestores. Ele não envolve interação humana direta no atendimento.

1.  **Atendimentos Ativos (Bot):**
    *   **Conteúdo:** Exibe **todos os atendimentos em andamento** que estão sendo tratados exclusivamente pela inteligência artificial.
    *   **Status do Atendimento:** `EM_ANDAMENTO` (com `departamento` sendo o do bot).
    *   **Fluxo:**
        *   Se o bot **resolve** o atendimento, o card move-se para a coluna "Finalizados (Bot)".
        *   Se o bot **transfere** o atendimento, o card **desaparece** deste painel e é movido para a "Fila de Atendimento" do departamento humano correspondente.

2.  **Finalizados (Bot):**
    *   **Conteúdo:** Atendimentos que foram concluídos com sucesso pelo chatbot.
    *   **Status do Atendimento:** `RESOLVIDO` (concluído pelo bot).
    *   **Ações:** Apenas visualização e análise de métricas.

### Estrutura do Card de Atendimento

Cada card no quadro Kanban representará um único atendimento e exibirá informações essenciais de forma concisa:

*   **Nome do Cliente:** Identificação clara do contato.
*   **Protocolo/ID do Atendimento:** Para referência rápida.
*   **Assunto/Última Mensagem:** Um trecho da última interação para dar contexto.
*   **Tempo na Fila/Status:** Há quanto tempo o atendimento está na coluna atual.
*   **Tags de Prioridade/Assunto:** Indicadores visuais (ex: "Urgente", "Vendas", "Problema Técnico").
*   **Atendente Atual:** (Quando aplicável) Nome do atendente responsável.

## 2. Fluxo de Utilização e Transição

O fluxo de trabalho é desenhado para ser contínuo e claro, desde o bot até o humano e entre humanos.

### Fluxo 1: Chatbot para Humano

1.  **Início (Painel do Chatbot):** Todo novo atendimento começa na coluna "Atendimentos Ativos (Bot)".
2.  **Transferência pelo Bot:**
    *   O chatbot, com base na intenção, decide transferir.
    *   O sistema atualiza o `departamento` do atendimento, muda o status para `AGUARDANDO_ATENDENTE` e desvincula o bot.
    *   O card é removido do painel do chatbot.
3.  **Chegada (Painel Humano):**
    *   O card aparece automaticamente na coluna "Fila de Atendimento" do departamento de destino.

### Fluxo 2: Atribuição e Atendimento Humano

1.  **Atribuição de Atendimento:**
    *   **Automática (Push):** O sistema move o card da "Fila" para "Meus Atendimentos" de um atendente disponível.
    *   **Manual (Pull):** O atendente arrasta o card da "Fila" para "Meus Atendimentos".
2.  **Interação e Finalização:**
    *   O atendente assume, interage e move o card entre "Meus Atendimentos", "Aguardando Cliente" e, finalmente, "Finalizados".

### Fluxo 3: Transferência entre Departamentos/Atendentes (Humano para Humano)

Este fluxo ocorre quando um atendente precisa escalar ou redirecionar um atendimento.

1.  **Início da Transferência:**
    *   No card do atendimento ativo (em "Meus Atendimentos"), o atendente clica na opção "Transferir".
2.  **Seleção de Destino:**
    *   Uma janela (modal) é aberta, permitindo ao atendente selecionar:
        *   **Um novo Departamento** (ex: de "Suporte" para "Financeiro").
        *   Opcionalmente, **um Atendente específico** dentro do novo departamento.
    *   O atendente pode adicionar uma nota interna explicando o motivo da transferência.
3.  **Execução da Transferência:**
    *   O sistema desvincula o atendente atual (`atendente_humano` vira `NULL`).
    *   O `departamento` do atendimento é atualizado para o novo destino.
    *   O status volta para `AGUARDANDO_ATENDENTE`.
    *   O card **desaparece** do painel do atendente de origem.
4.  **Chegada no Novo Destino:**
    *   O card **aparece** na coluna "Fila de Atendimento" do novo departamento, pronto para ser atribuído.
    *   Se um atendente específico foi escolhido, o card pode ir diretamente para a coluna "Meus Atendimentos" dele (a ser definido).

## 3. Vantagens desta Abordagem

*   **Interfaces Limpas:** Cada perfil (atendente e gestor) tem uma visão focada em suas responsabilidades.
*   **Clareza no Fluxo:** A transição entre o bot e o humano (e entre humanos) é clara e rastreável.
*   **Foco do Atendente:** O atendente humano lida apenas com o que é relevante para ele, sem a distração dos atendimentos automatizados.
*   **Colaboração Eficiente:** Facilita a escalada e o redirecionamento de casos complexos para o especialista ou departamento correto.
*   **Monitoramento Centralizado do Bot:** Gestores têm uma visão consolidada e em tempo real da performance e carga de trabalho do chatbot.
*   **Simplicidade:** O mecanismo de "arrastar e soltar" é mantido para o fluxo humano, garantindo facilidade de uso.
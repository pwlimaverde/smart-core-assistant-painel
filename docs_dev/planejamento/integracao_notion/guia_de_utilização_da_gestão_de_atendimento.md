# Guia de utilização da Gestão de Atendimento

Este guia orienta usuários na operação do sistema de Gestão de Atendimento. Foca em utilização, boas práticas e entendimento do fluxo, sem detalhes técnicos de implementação.

## Objetivo do Sistema
- Centralizar e organizar atendimentos de clientes.
- Acompanhar o ciclo completo: recepção de mensagens, pré-atendimento do bot, roteamento, atendimento humano e encerramento.
- Oferecer visões (Kanban, listas, filtros) para gestão eficiente por agente, status e prioridade.

## Público-Alvo
- Agentes de atendimento
- Supervisores e coordenadores
- Administradores operacionais

## Conceitos-Chave
- Atendimento: registro principal que representa uma conversa/solicitação do cliente.
- Mensagem: cada interação enviada/recebida (cliente, bot ou agente).
- Status: estado do atendimento (Fila, Em Atendimento, Aguardando Cliente, Encerrado).
- Agente: responsável atual pelo atendimento.
- Departamento: área relacionada ao atendimento (quando aplicável).

## Visão Geral de Uso
- Acesse a página de gestão e utilize as visões predefinidas (Kanban por Status, lista por Agente, etc.).
- Use filtros para focar em sua fila ou prioridade.
- Abra um atendimento para ver detalhes, histórico de mensagens e campos importantes.

## Fluxo de Criação de Novos Atendimentos
Abaixo está o fluxo padronizado desde a chegada de uma nova mensagem até o atendimento humano.

### 1) Recepção da mensagem
- Uma mensagem enviada pelo cliente (ex.: WhatsApp) é recebida pelo sistema.
- A mensagem é registrada e fica disponível para processamento.

### 2) Pré-atendimento do bot
- O bot faz triagem inicial: cumprimenta, coleta informações básicas e identifica intenção.
- Se possível, oferece respostas automáticas (FAQ, instruções simples, confirmação de dados).
- Caso precise de humano, encaminha para a fila adequada.

### 3) Identificação do cliente e vínculo
- O sistema tenta reconhecer o cliente por telefone/ID.
- Se não existir cadastro, cria-se um registro básico do cliente.
- O atendimento referencia o cliente identificado para continuidade.

### 4) Criação do atendimento
- Ao confirmar necessidade de acompanhamento, um “Atendimento” é criado com campos iniciais (cliente, origem, título/resumo, status).
- O status inicial é normalmente “Fila”, aguardando agente.

### 5) Roteamento e prioridade
- Regras operacionais definem o departamento (quando aplicável) e prioridade.
- Supervisores podem ajustar manualmente prioridade ou fila.

### 6) Atribuição ao agente
- Um agente assume o atendimento (manual ou conforme regras internas).
- O status passa para “Em Atendimento”.

### 7) Conversa e registro de mensagens
- O agente responde ao cliente; novas mensagens são registradas no histórico do atendimento.
- Se aguardar retorno do cliente, atualize para “Aguardando Cliente”.
- Mantenha o histórico claro; evite trocas fora do registro.

### 8) Atualizações de status e campos
- Atualize o status conforme avanço: “Em Atendimento”, “Aguardando Cliente”, “Encerrado”.
- Ajuste os campos relevantes (responsável, departamento, prioridade, tags) para facilitar gestão.

### 9) Encerramento
- Quando a demanda é resolvida, mude para “Encerrado”.
- Registre brevemente a solução ou motivo do fechamento.

## Orientações de Uso Diário
- Utilize o Kanban para organizar atendimentos por status.
- Filtre por “Agente” para ver sua fila rapidamente.
- Atenda em ordem de prioridade e tempo de espera.
- Mantenha campos atualizados para melhor visibilidade do time.

## Boas Práticas
- Seja claro e objetivo nas respostas.
- Atualize o status sempre que houver mudança de contexto.
- Documente brevemente decisões importantes no atendimento.
- Evite duplicidade: uma conversa = um atendimento, salvo exceções.

## Perguntas Frequentes
- Como vejo meus atendimentos? Use filtro por “Agente” na visão lista/kanban.
- Como acompanho pendências? Filtre “Aguardando Cliente” e revise itens mais antigos.
- Posso reatribuir atendimentos? Supervisores podem reatribuir conforme necessidade.

## Glossário Rápido
- Fila: aguardando agente.
- Em Atendimento: em progresso com agente.
- Aguardando Cliente: aguardando resposta do cliente.
- Encerrado: finalizado.

---

Para dúvidas operacionais, contate a coordenação de atendimento.
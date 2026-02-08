# Visão Geral e Regras de Transferência de Atendimentos

Este documento detalha a arquitetura, regras de negócio, lógica de automação e validações técnicas que regem a transferência de atendimentos no Smart Core Assistant Painel.

## 1. Entidades e Relacionamentos

A transferência envolve a interação entre as seguintes entidades do sistema:

*   **Atendimento** (`src/smart_core_assistant_painel/app/atendimentos/models.py`): A entidade central.
    *   Mantém ponteiros para `Departamento`, `FluxoAtendimento`, `EtapaFluxo` e `Atendente`.
    *   Estado gerido por campo `status` (enum) e `etapa_atual` (fk).
*   **Departamento** (`src/smart_core_assistant_painel/app/operacional/models.py`): Unidade lógica (ex: Comercial). Possui configurações de API e instâncias.
*   **FluxoAtendimento**: Quadro Kanban que pertence a um Departamento. Define a sequência de Etapas.
*   **EtapaFluxo**: Estado granular dentro de um Fluxo (ex: "Aguardando Pagamento"). Possui um `tipo_etapa` (FILA, TRABALHO, etc.).
*   **MovimentoFluxo**: Log de auditoria que registra cada transição de etapa, calculando tempos de permanência.

## 2. Máquina de Estados (Status vs. Etapa)

O sistema opera com um modelo híbrido de estados:

1.  **Status Global** (`Atendimento.status`):
    *   `fila`: Aguardando triagem ou distribuição.
    *   `em_atendimento`: Sob responsabilidade de um humano ou bot ativo.
    *   `pendencia`: Aguardando ação externa (cliente).
    *   `resolvido` / `cancelado`: Estados terminais.
    *   `transferido`: Estado transitório (legado, hoje mapeado para FILA no novo setor).

2.  **Estado no Fluxo** (`Atendimento.etapa_atual`):
    *   Define a posição visual no Kanban.
    *   Deve ser consistente com o `status` global (ex: uma etapa do tipo `FINALIZACAO` geralmente implica status `RESOLVIDO`).

## 3. Lógica de Comunicação Humano-Agente

A comunicação entre atendente humano e contato segue regras específicas para garantir registro e controle:

1.  **Registro de Mensagens**:
    *   Toda interação gera um novo objeto `Mensagem`.
    *   Mensagens enviadas pelo atendente (via painel ou celular) são registradas com `remetente=ATENDENTE_HUMANO` e vinculadas ao `Atendente` específico.

2.  **Análise em Tempo Real (Human Loop)**:
    *   Mesmo quando um humano está atendendo (`bot_pode_atender=False`), as mensagens do contato **continuam passando pela análise de IA** (NLP).
    *   **Objetivo**: Extrair entidades, detectar intenções e atualizar o contexto do atendimento silenciosamente.
    *   **Regra de Ouro**: O Bot analisa, salva os metadados, mas **NÃO gera resposta** (silenciado pelo `BotRulesEngine`).

## 4. Mecanismos de Transferência (Lógica Atual)

Existem três vetores principais que disparam transferências:

### 3.1. Transferência Automática via IA (Bot)

A `FeaturesCompose` (`src/smart_core_assistant_painel/modules/ai_engine/features/features_compose.py`) é o cérebro que decide quando transferir.

**Algoritmo de Decisão:**
1.  **Análise de Conteúdo**: A mensagem do usuário é comparada (embedding) com a base de conhecimento e intenções.
2.  **Cálculo de Score**: Um score "triádico" é calculado comparando (Pergunta vs Resposta Bot), (Pergunta vs Treinamento) e (Resposta Bot vs Treinamento).
3.  **Gatilhos de Transferência (`transferir_atendimento = True`)**:
    *   **Baixa Confiança**: Se `final_score < 0.6`.
    *   **Frases Chave**: Se a resposta do bot contém "Desculpe, não encontrei informações" ou "Estarei transferindo seu atendimento".
    *   **Intenção Explícita**: Se o usuário pede explicitamente (detectado via tags como `transferir_humano` no `QueryCompose`).

**Roteamento de Destino:**
*   O sistema tenta extrair o destino da resposta do bot usando Regex:
    `Estarei transferindo seu atendimento para ([^.]+)`
*   O valor extraído é comparado com as chaves de `fluxos_disponiveis` (formato "Nome Fluxo - Nome Depto").
*   **Fallback**: Se não encontrar correspondência exata, transfere para o **primeiro fluxo disponível** na lista.

### 3.2. Transferência Manual (Interface/API)

Operadores podem mover atendimentos manualmente.

*   **Movimentação Kanban**:
    *   Atualiza apenas `etapa_atual`.
    *   Gera registro em `MovimentoFluxo`.
*   **Transferência de Departamento**:
    *   Limpa `atendente_humano`.
    *   Define novo `departamento`.
    *   Opcionalmente define novo `fluxo` e `etapa_inicial`.
    *   Reseta status para `FILA`.

### 3.3. Orquestração (`AttendanceOrchestrator`)

O `AttendanceOrchestrator` coordena a execução da decisão da IA:
1.  Recebe `result.transferir_atendimento` e `result.fluxo_transferencia`.
2.  Invoca `atendimento.apply_flow_by_description(fluxo_nome)`.
3.  O método `apply_flow_by_description`:
    *   Localiza o objeto `FluxoAtendimento`.
    *   Atualiza `departamento` e `fluxo`.
    *   Define `etapa_atual` para a primeira etapa do fluxo (priorizando tipo `FILA`).
    *   Se a nova etapa for tipo `FILA`, força `status = 'fila'`.

## 4. Regras de Validação e Consistência

O modelo `Atendimento` implementa validações rígidas no método `clean()` para evitar inconsistências de dados:

1.  **Consistência Hierárquica**:
    *   `etapa_atual` DEVE pertencer ao `fluxo_atendimento`.
    *   `fluxo_atendimento` DEVE pertencer ao `departamento`.
    *   Logo, `etapa_atual` DEVE pertencer ao `departamento`.
2.  **Erro de Validação**:
    *   Tentar salvar um atendimento com Etapa X (do Depto A) e Departamento B levanta `ValidationError`.

## 6. Limitações Técnicas Atuais

1.  **Dependência de Strings Mágicas**: A IA depende que a resposta gerada contenha exatamente a frase "Estarei transferindo..." para extrair o destino. Se o prompt do sistema mudar, a extração quebra.
2.  **Roteamento "Cego"**: No fallback, o sistema joga para o primeiro fluxo encontrado, o que pode ser incorreto em ambientes com múltiplos departamentos.
3.  **Sessão de WhatsApp**: A transferência entre departamentos não altera a sessão do WhatsApp. Se os departamentos usam instâncias (números) diferentes, o histórico não é migrado transparentemente para o novo número (limitação da plataforma WhatsApp).

## 6. Planejamento de Melhorias (Roadmap)

Para mitigar as limitações acima, propõe-se a seguinte reestruturação (detalhada em documentos complementares):

1.  **Service de Transferência Centralizado**:
    *   Remover lógica de regex da camada de View/Compose.
    *   Implementar `TransferService.execute(atendimento, destino_intencao)`.
2.  **Tabela de Roteamento de Intenções**:
    *   Mapear `Tag de Intenção` -> `Fluxo ID` no banco de dados, eliminando a adivinhação por nome.
3.  **Handover Contextual**:
    *   Ao transferir, gerar uma "Nota Interna" automática resumindo o motivo da transferência e o resumo da conversa até o momento.

## 8. Exemplos Práticos de Fluxo

Para ilustrar como as regras acima se aplicam na prática, considere os seguintes cenários:

### Cenário A: Triagem Automática (IA -> Departamento)
1.  **Entrada**: Cliente envia mensagem: "Gostaria de receber um orçamento para consultoria".
2.  **Processamento (IA)**:
    *   `AnaliseMensage` detecta intenção `solicitacao_orcamento`.
    *   Base de Conhecimento indica que isso pertence ao Comercial.
    *   IA gera resposta: "Entendi, estarei transferindo seu atendimento para o setor Comercial".
    *   Regex extrai: "Comercial".
3.  **Ação (Orchestrator)**:
    *   Identifica fluxo "Vendas - Comercial".
    *   Define `atendimento.departamento = Comercial`.
    *   Define `atendimento.fluxo = Vendas`.
    *   Define `atendimento.etapa_atual = Fila de Entrada` (Primeira etapa do fluxo).
    *   Define `atendimento.status = fila`.
4.  **Resultado**: O atendimento aparece na coluna "Fila" do quadro Kanban do time Comercial.

### Cenário B: Evolução no Kanban (Manual)
1.  **Contexto**: Atendente "João" do Comercial pega o atendimento da fila.
2.  **Ação**: João arrasta o card de "Fila de Entrada" para "Em Negociação".
3.  **Sistema**:
    *   Valida se "Em Negociação" pertence ao fluxo "Vendas".
    *   Atualiza `atendimento.etapa_atual`.
    *   Cria registro em `MovimentoFluxo` (Origem: Fila, Destino: Em Negociação, Atendente: João).
    *   Mantém `atendimento.status = em_atendimento`.

### Cenário C: Transbordo entre Departamentos (Comercial -> Financeiro)
1.  **Contexto**: Durante a negociação, o cliente pede a segunda via de um boleto antigo.
2.  **Ação**: João clica em "Transferir Departamento" e seleciona "Financeiro".
3.  **Sistema**:
    *   Limpa `atendimento.atendente_humano` (João perde a posse).
    *   Define `atendimento.departamento = Financeiro`.
    *   Define `atendimento.fluxo = Atendimento Geral` (Fluxo padrão do Financeiro).
    *   Define `atendimento.etapa_atual = Fila` (Etapa inicial do fluxo Financeiro).
    *   Define `atendimento.status = fila`.
4.  **Resultado**: O atendimento sai da tela do João e aparece na Fila do time Financeiro.

# Mapeamento de Campos do Sistema de Atendimento para Campos Personalizados do ClickUp

## Introdução

Este documento detalha o mapeamento dos campos do modelo de Atendimentos do sistema para campos personalizados do ClickUp, visando enriquecer o entendimento dos atendentes sobre cada atendimento sincronizado. A análise considera a importância estratégica de cada informação e o tipo mais adequado de campo personalizado no ClickUp.

## Principais Objetivos da Integração

1. **Contexto Rápido**: Permitir que atendentes compreendam rapidamente a situação do atendimento
2. **Priorização Eficiente**: Facilitar a identificação de atendimentos críticos
3. **Histórico Completo**: Disponibilizar informações relevantes sobre a jornada do cliente
4. **Insights de Negócio**: Possibilitar análises e melhorias nos processos de atendimento

## Mapeamento Detalhado de Campos

### 1. Informações de Identificação

#### Campo do Modelo: `contato`
- **Tipo de Campo ClickUp**: Campo de Relacionamento (Task Relationship)
- **Configuração**: Campo que permite vincular a uma tarefa representando o contato
- **Importância**: Essencial para identificar quem está sendo atendido
- **Justificativa**: Permite visualizar rapidamente informações detalhadas sobre o contato, incluindo histórico completo de interações anteriores

#### Campo do Modelo: `departamento`
- **Tipo de Campo ClickUp**: Dropdown
- **Configuração**: 
  ```json
  {
    "name": "Departamento",
    "type": "drop_down",
    "type_config": {
      "sorting": "manual",
      "placeholder": "Selecione o departamento",
      "options": [
        {"id": "dept_vendas", "name": "Vendas", "color": "#00BCD4"},
        {"id": "dept_suporte", "name": "Suporte Técnico", "color": "#FF9800"},
        {"id": "dept_financeiro", "name": "Financeiro", "color": "#4CAF50"},
        {"id": "dept_outros", "name": "Outros", "color": "#9E9E9E"}
      ]
    }
  }
  ```
- **Importância**: Fundamental para roteamento e especialização do atendimento
- **Justificativa**: Permite filtrar e distribuir atendimentos equipes especializadas

#### Campo do Modelo: `canal`
- **Tipo de Campo ClickUp**: Labels
- **Configuração**:
  ```json
  {
    "name": "Canal de Origem",
    "type": "labels",
    "type_config": {
      "sorting": "manual",
      "options": [
        {"id": "canal_whatsapp", "label": "WhatsApp", "color": "#25D366"},
        {"id": "canal_email", "label": "E-mail", "color": "#7289DA"},
        {"id": "canal_telefone", "label": "Telefone", "color": "#37474F"},
        {"id": "canal_web", "label": "Website", "color": "#2196F3"}
      ]
    }
  }
  ```
- **Importância**: Define o meio de comunicação e suas particularidades
- **Justificativa**: Cada canal possui regras de resposta diferentes, sendo crucial para priorização

### 2. Informações de Status e Prioridade

#### Campo do Modelo: `prioridade`
- **Tipo de Campo ClickUp**: Dropdown
- **Configuração**:
  ```json
  {
    "name": "Prioridade",
    "type": "drop_down",
    "type_config": {
      "sorting": "manual",
      "default": 1,
      "placeholder": "Selecione a prioridade",
      "options": [
        {"id": "prio_baixa", "name": "Baixa", "color": "#4CAF50"},
        {"id": "prio_normal", "name": "Normal", "color": "#2196F3"},
        {"id": "prio_alta", "name": "Alta", "color": "#FF9800"},
        {"id": "prio_urgente", "name": "Urgente", "color": "#F44336"}
      ]
    }
  }
  ```
- **Importância**: Crítico para organização da fila de atendimentos
- **Justificativa**: Permite visualização imediata dos atendimentos que exigem atenção imediata

#### Campo do Modelo: `etapa_atual` (equivalente a status)
- **Tipo de Campo ClickUp**: Status (nativo do ClickUp)
- **Configuração**: Mapeamento para status da lista do ClickUp
- **Importância**: Essencial para acompanhamento do fluxo de trabalho
- **Justificativa**: O campo status nativo já representa colunas em visualizações Kanban

### 3. Informações Temporais

#### Campo do Modelo: `data_inicio`
- **Tipo de Campo ClickUp**: Date
- **Configuração**:
  ```json
  {
    "name": "Início do Atendimento",
    "type": "date",
    "type_config": {}
  }
  ```
- **Importância**: Base para cálculo de métricas de tempo de atendimento
- **Justificativa**: Permite análises de eficiência e cumprimento de SLAs

#### Campo do Modelo: `data_ultima_mensagem`
- **Tipo de Campo ClickUp**: Date (com opção de tempo)
- **Configuração**:
  ```json
  {
    "name": "Última Interação",
    "type": "date",
    "type_config": {}
  }
  ```
- **Importância**: Indicador de atendimentos parados ou esquecidos
- **Justificativa**: Permite identificar atendimentos estagnados que precisam de atenção

#### Campo do Modelo: `data_primeira_resposta`
- **Tipo de Campo ClickUp**: Date
- **Configuração**:
  ```json
  {
    "name": "Primeira Resposta",
    "type": "date",
    "type_config": {}
  }
  ```
- **Importância**: Métrica de qualidade do atendimento inicial
- **Justificativa**: Essencial para avaliar a agilidade da equipe no atendimento inicial

### 4. Informações de Atribuição

#### Campo do Modelo: `atendente_humano`
- **Tipo de Campo ClickUp**: User
- **Configuração**: Campo para atribuir usuários específicos
- **Importância**: Definição de responsabilidade pelo atendimento
- **Justificativa**: Permite saber quem está responsável pelo caso atualmente

### 5. Informações de Conteúdo

#### Campo do Modelo: `assunto`
- **Tipo de Campo ClickUp**: Text
- **Configuração**:
  ```json
  {
    "name": "Assunto/Resumo",
    "type": "text",
    "type_config": {}
  }
  ```
- **Importância**: Síntese do motivo do atendimento
- **Justificativa**: Permite compreensão rápida do contexto sem ler toda a conversa

#### Campo do Modelo: `tags`
- **Tipo de Campo ClickUp**: Labels
- **Configuração**: Campo de etiquetas múltiplas
- **Importância**: Categorização flexível dos atendimentos
- **Justificativa**: Facilita filtros e análises específicas (ex: "reclamação", "dúvida", "elogio")

### 6. Informações de Feedback

#### Campo do Modelo: `avaliacao`
- **Tipo de Campo ClickUp**: Emoji Rating
- **Configuração**:
  ```json
  {
    "name": "Avaliação do Cliente",
    "type": "emoji",
    "type_config": {
      "code_point": "2b50",
      "count": 5
    }
  }
  ```
- **Importância**: Indicador direto da satisfação do cliente
- **Justificativa**: Métrica crucial para avaliação da qualidade do atendimento

#### Campo do Modelo: `feedback`
- **Tipo de Campo ClickUp**: Text (multilinha)
- **Configuração**:
  ```json
  {
    "name": "Feedback Detalhado",
    "type": "text",
    "type_config": {}
  }
  ```
- **Importância**: Informações qualitativas sobre a experiência
- **Justificativa**: Fornece contexto para entender a avaliação numérica

### 7. Informações de Contexto Adicional

#### Campo do Modelo: `canal`
- **Tipo de Campo ClickUp**: Labels
- **Configuração**: Campo de etiquetas para canal de origem
- **Importância**: Define o meio de comunicação utilizado
- **Justificativa**: Cada canal possui particularidades no tratamento

#### Campo do Modelo: `historico_status`
- **Tipo de Campo ClickUp**: Text Area
- **Configuração**: Campo para registrar histórico de mudanças
- **Importância**: Rastreabilidade das mudanças de status
- **Justificativa**: Permite entender a jornada do atendimento

## Campos de Métricas e KPIs

### Tempo de Primeira Resposta
- **Tipo de Campo ClickUp**: Formula (calculado)
- **Configuração**: Campo que calcula diferença entre `data_inicio` e `data_primeira_resposta`
- **Importância**: Métrica de agilidade no atendimento inicial
- **Justificativa**: KPI essencial para avaliar eficiência da equipe

### Tempo de Atendimento
- **Tipo de Campo ClickUp**: Formula (calculado)
- **Configuração**: Campo que calcula diferença entre `data_inicio` e `data_fim`
- **Importância**: Métrica de duração total do atendimento
- **Justificativa**: Indica eficiência no processo de resolução

## Considerações de Implementação

### Hierarquia no ClickUp
1. **Space**: Central de Atendimento
2. **Folder**: Departamentos (Vendas, Suporte, Financeiro, etc.)
3. **List**: Fluxos de atendimento por tipo de solicitação
4. **Task**: Cada atendimento individual

### Sincronização Bidirecional
- **Do Sistema para ClickUp**: Novos atendimentos criam automaticamente tasks
- **Do ClickUp para Sistema**: Alterações em campos personalizados atualizam o modelo
- **Histórico de Mudanças**: Sincronização de comentários e alterações de status

### Automações Recomendadas
1. **Notificações**: Quando um atendimento é atribuído a um atendente
2. **SLAs**: Alertas quando atingidos limites de tempo
3. **Escalonamento**: Mudança automática de status após determinado tempo
4. **Relatórios**: Geração automática de relatórios de desempenho

## Fluxo de Trabalho Proposto

1. **Início**: Novo atendimento é criado no sistema e sincronizado como task no ClickUp
2. **Atribuição**: Atendente recebe notificação e visualiza todos os campos personalizados
3. **Andamento**: Atualizações no ClickUp ou no sistema refletem em ambos os lados
4. **Conclusão**: Finalização do atendimento registra feedback e métricas

## Conclusão

O mapeamento detalhado dos campos do sistema para campos personalizados do ClickUp permite uma visualização rica e contextualizada dos atendimentos, capacitando os atendentes com informações cruciais para oferecer um serviço mais eficiente e personalizado. A estratégia de integração deve focar não apenas na transferência de dados, mas na criação de um fluxo de trabalho que aproveite as funcionalidades visuais e de automação do ClickUp para enriquecer a experiência do atendente e, consequentemente, do cliente.
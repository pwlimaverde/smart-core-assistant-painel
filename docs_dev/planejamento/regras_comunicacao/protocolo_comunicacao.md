# Protocolo de Comunicação e Regras de Interação

Este documento define as regras de negócio implementadas para o processamento de mensagens no sistema Smart Core Assistant, focando na distinção entre interações automáticas (Bot), intervenções humanas e comunicações internas.

## 1. Visão Geral

O sistema atua como um hub de comunicação centralizado. Para garantir a integridade dos dados e evitar loops ou registros desnecessários, foram estabelecidas regras estritas de filtragem e categorização de mensagens recebidas via Webhook da Evolution API.

## 2. Atores Envolvidos

*   **Instância (Bot):** O número de WhatsApp conectado ao sistema via Evolution API.
*   **Contato (Cliente):** Usuário externo que interage com a instância.
*   **Atendente Humano:** Operador que utiliza a própria instância (celular físico ou WhatsApp Web) ou o painel para enviar mensagens.
*   **Whitelist (Gestão):** Números específicos (Diretoria, Supervisão) cujas interações não devem gerar atendimentos operacionais.

## 3. Regras de Filtragem (Ignorar Mensagem)

Antes de qualquer processamento, o sistema avalia se a mensagem deve ser ignorada. Se qualquer uma das condições abaixo for verdadeira, a mensagem é descartada silenciosamente (logada apenas como ignorada).

### 3.1. Comunicação entre Instâncias
*   **Regra:** Mensagens trocadas entre dois números que são ambos registrados como `EvolutionInstance` no sistema.
*   **Objetivo:** Evitar que um Bot "converse" com outro Bot, gerando loops infinitos ou atendimentos fantasmas.
*   **Mecanismo:** O sistema verifica se o `sender_jid` (remetente) corresponde ao `phone_number` de qualquer instância ativa.

### 3.2. Whitelist (Lista Branca)
*   **Regra:** Mensagens enviadas por números cadastrados na `WhiteList`.
*   **Objetivo:** Permitir que diretores e supervisores testem ou interajam com as instâncias sem poluir o painel de atendimentos e sem receber respostas automáticas.
*   **Mecanismo:** O sistema verifica se o `sender_jid` (remetente) está presente na tabela `WhiteList` com status `active=True`.

### 3.3. Mensagens de Sistema/Status
*   **Regra:** Mensagens sem JID válido ou atualizações de status (presença).
*   **Objetivo:** Processar apenas conteúdo relevante (texto, mídia).

## 4. Regras de Processamento e Registro

Se a mensagem passar pelos filtros acima, ela é categorizada e processada conforme sua origem.

### 4.1. Mensagem do Cliente (Entrada)
*   **Origem:** `fromMe = False` (Enviada pelo contato).
*   **Ação:**
    1.  Cria ou atualiza o `Atendimento`.
    2.  Registra a `Mensagem` com remetente `CONTATO`.
    3.  **Aciona o Bot:** O orquestrador analisa a mensagem e gera uma resposta automática (IA ou Fluxo), a menos que o atendimento esteja em pausa ou sob intervenção humana.

### 4.2. Mensagem do Atendente (Saída Direta)
*   **Origem:** `fromMe = True` (Enviada pelo próprio WhatsApp da instância).
*   **Cenário:** O atendente usa o celular físico ou WhatsApp Web para falar com o cliente (prospecção ou resposta manual).
*   **Ação:**
    1.  **Atualização Cadastral:** O sistema usa o remetente para atualizar/confirmar o `phone_number` da instância no banco de dados.
    2.  Cria ou atualiza o `Atendimento` (inicia um se não existir).
    3.  Registra a `Mensagem` com remetente `ATENDENTE_HUMANO`.
    4.  **NÃO Aciona o Bot:** A mensagem é apenas registrada. O sistema entende que o humano assumiu o controle ou está iniciando uma conversa, portanto, não deve haver interrupção automática imediata.

## 5. Fluxo de Decisão

```mermaid
flowchart TD
    A[Webhook Recebido] --> B{Tem JID Válido?}
    B -- Não --> Z[Ignorar]
    B -- Sim --> C{Remetente é Instância?}
    C -- Sim --> Z
    C -- Não --> D{Remetente na Whitelist?}
    D -- Sim --> Z
    D -- Não --> E{É fromMe?}
    
    E -- Sim (Atendente) --> F[Atualizar Phone Instância]
    F --> G[Registrar Mensagem (Atendente Humano)]
    G --> H[Criar/Atualizar Atendimento]
    H --> I[FIM (Sem Resposta Bot)]
    
    E -- Não (Cliente) --> J[Registrar Mensagem (Contato)]
    J --> K[Criar/Atualizar Atendimento]
    K --> L[Acionar Orquestrador (Bot)]
    L --> M[Gerar Resposta IA/Fluxo]
```

## 6. Implementação Técnica

*   **Local:** `src/smart_core_assistant_painel/app/evolution_sync/services/webhook.py`
*   **Classe:** `WebhookProcessor`
*   **Métodos Chave:**
    *   `process_webhook`: Aplica os filtros globais.
    *   `_handle_from_me_message`: Trata especificamente as mensagens enviadas pela instância.

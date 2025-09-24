# Modelagem de Dados - Central de Atendimento

Este documento detalha o esquema do banco de dados PostgreSQL para as novas entidades da central de atendimento.

## 1. Diagrama de Entidade e Relacionamento (DER)

(Será adicionado um diagrama aqui posteriormente, gerado a partir dos modelos Django)

## 2. Detalhamento das Tabelas

### Tabela: `atendimentos_departamento`

Armazena os departamentos da empresa.

| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `id` | `UUID` | PK | Identificador único do departamento. |
| `nome` | `VARCHAR(100)` | | Nome do departamento (ex: "Comercial", "Suporte"). |
| `descricao` | `TEXT` | | Descrição das responsabilidades do departamento. |
| `ativo` | `BOOLEAN` | | Indica se o departamento está ativo no sistema. |
| `created_at` | `TIMESTAMP` | | Data de criação do registro. |
| `updated_at` | `TIMESTAMP` | | Data da última atualização. |

### Tabela: `atendimentos_atendente`

Representa os agentes/atendentes humanos.

| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `id` | `UUID` | PK | Identificador único do atendente. |
| `user_id` | `INTEGER` | FK (`auth_user.id`) | Relacionamento com o modelo de usuário do Django. |
| `departamento_id` | `UUID` | FK (`atendimentos_departamento.id`) | Departamento ao qual o atendente pertence. |
| `nome_completo` | `VARCHAR(255)` | | Nome completo do atendente. |
| `status_disponibilidade` | `VARCHAR(50)` | | Status atual do atendente (ex: "Online", "Offline", "Ocupado"). |
| `whatsapp_instance_id` | `VARCHAR(255)` | | ID da instância do WhatsApp associada a este atendente (da Evolution API). |
| `ativo` | `BOOLEAN` | | Indica se o atendente está ativo no sistema. |
| `created_at` | `TIMESTAMP` | | Data de criação do registro. |
| `updated_at` | `TIMESTAMP` | | Data da última atualização. |

### Tabela: `atendimentos_cliente`

Dados dos clientes que entram em contato.

| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `id` | `UUID` | PK | Identificador único do cliente. |
| `nome` | `VARCHAR(255)` | | Nome do cliente. |
| `numero_whatsapp` | `VARCHAR(50)` | UNIQUE | Número do WhatsApp do cliente (usado como identificador principal). |
| `email` | `VARCHAR(254)` | | E-mail do cliente (opcional). |
| `created_at` | `TIMESTAMP` | | Data de criação do registro. |
| `updated_at` | `TIMESTAMP` | | Data da última atualização. |

### Tabela: `atendimentos_atendimento`

Coração do sistema, registra cada sessão de atendimento.

| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `id` | `UUID` | PK | Identificador único do atendimento. |
| `cliente_id` | `UUID` | FK (`atendimentos_cliente.id`) | Cliente que está sendo atendido. |
| `atendente_id` | `UUID` | FK (`atendimentos_atendente.id`) | Atendente humano que assumiu o chat (pode ser nulo no início). |
| `departamento_id` | `UUID` | FK (`atendimentos_departamento.id`) | Departamento para o qual o atendimento foi direcionado. |
| `status` | `VARCHAR(50)` | | Status do atendimento (ex: "Aguardando", "Com Chatbot", "Em Atendimento", "Finalizado", "Cancelado"). |
| `data_inicio` | `TIMESTAMP` | | Quando o atendimento começou. |
| `data_transferencia` | `TIMESTAMP` | | Quando foi transferido para um humano (se aplicável). |
| `data_finalizacao` | `TIMESTAMP` | | Quando o atendimento foi finalizado. |
| `contexto_chatbot` | `JSONB` | | Último estado/contexto da conversa com o chatbot antes da transferência. |

### Tabela: `atendimentos_mensagem`

Armazena cada mensagem trocada durante um atendimento.

| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `id` | `UUID` | PK | Identificador único da mensagem. |
| `atendimento_id` | `UUID` | FK (`atendimentos_atendimento.id`) | Atendimento ao qual a mensagem pertence. |
| `remetente_tipo` | `VARCHAR(20)` | | Tipo de remetente ("Cliente", "Atendente", "Chatbot"). |
| `remetente_id` | `VARCHAR(255)` | | ID do remetente (pode ser `cliente.id`, `atendente.id`, ou um ID fixo para o bot). |
| `conteudo` | `TEXT` | | O texto da mensagem. |
| `tipo_conteudo` | `VARCHAR(50)` | | Tipo de mensagem (texto, imagem, áudio, etc.). |
| `timestamp_envio` | `TIMESTAMP` | | Data e hora em que a mensagem foi enviada. |
| `metadata` | `JSONB` | | Metadados adicionais da mensagem (ex: ID da mensagem do WhatsApp). |
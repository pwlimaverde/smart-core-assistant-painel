# Modelagem de Dados da Central de Atendimento

Este documento detalha a estrutura de dados da Central de Atendimento, alinhada com os modelos Django existentes no projeto.

## 1. App `atendimentos`

Responsável por gerenciar todas as informações relacionadas aos atendimentos.

### 1.1. `StatusAtendimento`

Representa os diferentes status que um atendimento pode ter.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | `INTEGER` | Identificador único do status. |
| `nome` | `VARCHAR(100)` | Nome do status (ex: "Pendente", "Em Andamento", "Resolvido"). |

### 1.2. `TipoMensagem`

Define o tipo de uma mensagem (ex: texto, imagem).

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | `INTEGER` | Identificador único do tipo de mensagem. |
| `nome` | `VARCHAR(50)` | Nome do tipo de mensagem. |

### 1.3. `TipoRemetente`

Identifica quem enviou a mensagem (cliente, atendente ou sistema).

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | `INTEGER` | Identificador único do tipo de remetente. |
| `nome` | `VARCHAR(50)` | Nome do tipo de remetente. |

### 1.4. `Atendimento`

Modelo central que armazena as informações de cada atendimento.

| Campo | Tipo | Chave Estrangeira | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | | Identificador único do atendimento. |
| `cliente` | `INTEGER` | `clientes.Cliente` | Cliente associado ao atendimento. |
| `atendente` | `INTEGER` | `operacional.AtendenteHumano` | Atendente responsável pelo atendimento (pode ser nulo). |
| `departamento` | `INTEGER` | `operacional.Departamento` | Departamento atual do atendimento. |
| `status` | `INTEGER` | `atendimentos.StatusAtendimento` | Status atual do atendimento. |
| `data_inicio` | `DATETIME` | | Data e hora de início do atendimento. |
| `data_fim` | `DATETIME` | | Data e hora de finalização (pode ser nulo). |
| `resolucao` | `TEXT` | | Descrição da resolução do atendimento. |
| `nivel_satisfacao` | `INTEGER` | | Nível de satisfação do cliente (1 a 5). |
| `data_ultima_mensagem` | `DATETIME` | | Data da última mensagem trocada. |
| `ativo` | `BOOLEAN` | | Indica se o atendimento está ativo. |

## 2. App `clientes`

Gerencia as informações dos clientes e seus contatos.

### 2.1. `Contato`

Armazena os dados de contato de um cliente.

| Campo | Tipo | Chave Estrangeira | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | | Identificador único do contato. |
| `cliente` | `INTEGER` | `clientes.Cliente` | Cliente ao qual o contato pertence. |
| `whatsapp` | `VARCHAR(20)` | | Número do WhatsApp. |

### 2.2. `Cliente`

Modelo que representa um cliente.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | `UUID` | Identificador único do cliente. |
| `nome_social` | `VARCHAR(255)` | Nome social ou apelido do cliente. |
| `cpf` | `VARCHAR(11)` | CPF do cliente (único). |
| `data_nascimento` | `DATE` | Data de nascimento do cliente. |
| `ativo` | `BOOLEAN` | Indica se o cliente está ativo. |

## 3. App `operacional`

Responsável pela estrutura organizacional, como departamentos e atendentes.

### 3.1. `Departamento`

Representa um departamento da empresa.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | `INTEGER` | Identificador único do departamento. |
| `nome` | `VARCHAR(100)` | Nome do departamento. |
| `descricao` | `TEXT` | Descrição das responsabilidades do departamento. |
| `ativo` | `BOOLEAN` | Indica se o departamento está ativo. |

### 3.2. `AtendenteHumano`

Modelo que representa um atendente humano.

| Campo | Tipo | Chave Estrangeira | Descrição |
| --- | --- | --- | --- |
| `id` | `INTEGER` | | Identificador único do atendente. |
| `user` | `INTEGER` | `auth.User` | Usuário do sistema associado ao atendente. |
| `departamento` | `INTEGER` | `operacional.Departamento` | Departamento ao qual o atendente pertence. |
| `nome_completo` | `VARCHAR(255)` | | Nome completo do atendente. |
| `max_atendimentos_simultaneos` | `INTEGER` | | Número máximo de atendimentos simultâneos. |
| `horario_trabalho` | `VARCHAR(255)` | | Horário de trabalho do atendente. |
| `data_ultima_atribuicao` | `DATETIME` | | Data da última atribuição de atendimento. |
| `disponivel` | `BOOLEAN` | | Indica se o atendente está disponível. |
| `especialidades` | `TEXT` | | Especialidades ou habilidades do atendente. |
# Product Requirements Document (PRD) - Smart Core Assistant Painel

**Versão:** 1.0
**Data:** 27/11/2025
**Status:** Em Planejamento

---

## 1. Introdução

### 1.1. Propósito
Este documento define os requisitos funcionais e não funcionais, escopo e arquitetura do **Smart Core Assistant Painel**. Ele serve como a fonte única de verdade para o desenvolvimento, garantindo que todas as partes interessadas tenham um entendimento alinhado sobre o produto a ser entregue.

### 1.2. Escopo do Produto
O Smart Core Assistant Painel é uma plataforma centralizada de atendimento multicanal que integra inteligência artificial (chatbot) com atendimento humano. O sistema orquestra a comunicação via WhatsApp (Evolution API), gerencia fluxos de trabalho personalizados por departamento e utiliza o Trello como interface visual para gestão de tickets (Kanban).

### 1.3. Definições e Acrônimos
- **PRD:** Product Requirements Document
- **RAG:** Retrieval-Augmented Generation (Geração Aumentada por Recuperação)
- **LLM:** Large Language Model
- **CRM:** Customer Relationship Management
- **SLA:** Service Level Agreement

---

## 2. Visão Geral do Produto

### 2.1. Visão
Criar uma solução de atendimento que combine a eficiência da IA com a empatia do atendimento humano, oferecendo uma experiência fluida para o cliente e ferramentas poderosas de gestão para a equipe.

### 2.2. Objetivos Principais
1.  **Centralização:** Unificar o atendimento de múltiplos canais e departamentos em uma única plataforma.
2.  **Automação Inteligente:** Utilizar IA para triagem, respostas automáticas e suporte ao atendente.
3.  **Flexibilidade:** Permitir a criação de fluxos de trabalho personalizados para cada departamento.
4.  **Integração Transparente:** Sincronizar perfeitamente com o Trello para gestão visual de tarefas sem duplicidade de dados.

---

## 3. Requisitos Funcionais

### 3.1. Módulo: Configuração e Núcleo do Sistema `[SYS]`
Funcionalidades essenciais de infraestrutura e serviços base.

| ID | Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| **SYS-INI-001** | Inicialização do Firebase | Conexão com Firebase Admin SDK para serviços de autenticação e configuração. | Alta |
| **SYS-INI-002** | Remote Config | Gestão dinâmica de variáveis de ambiente via Firebase Remote Config. | Alta |
| **SYS-DAT-002** | Vector Storage | Gerenciamento de banco de dados vetorial para busca semântica e RAG. | Alta |

### 3.2. Módulo: Gestão Administrativa e Acesso `[ADM]`
Gestão de usuários, permissões e configurações globais.

| ID | Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| **ADM-USR-001** | Cadastro de Usuários | Registro de novos usuários com validação de credenciais. | Alta |
| **ADM-USR-002** | Autenticação e Login | Sistema de login seguro com redirecionamento baseado em perfil. | Alta |
| **ADM-CFG-001** | Configuração OAuth | Gestão de autenticação OAuth para integrações (Trello/ClickUp). | Média |

### 3.3. Módulo: Gestão Operacional `[OPS]`
Definição da estrutura organizacional e fluxos de trabalho.

| ID | Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| **OPS-ORG-001** | Gestão de Departamentos | Cadastro de departamentos com configurações específicas (API keys, instâncias). | Alta |
| **OPS-ORG-002** | Gestão de Atendentes | Cadastro de agentes, horários e limites de atendimento. | Alta |
| **OPS-FLW-001** | Fluxos Personalizados | Criação de fluxos de trabalho (Kanban) específicos por departamento. | Alta |
| **OPS-FLW-002** | Gestão de Etapas | Configuração de colunas/etapas com regras de automação e cores. | Alta |

### 3.4. Módulo: Treinamento e Conhecimento (RAG UI) `[TRN]`
Interface para gestão da base de conhecimento da IA.

| ID | Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| **TRN-CON-001** | Ingestão de Documentos | Upload de arquivos (PDF, DOCX) para treinamento da IA. | Alta |
| **TRN-CON-002** | Curadoria de Conteúdo | Fluxo de revisão e aprovação de conteúdo processado pela IA. | Média |
| **TRN-INT-001** | Query Compose | Cadastro de intenções e exemplos para treinamento supervisionado. | Média |

### 3.5. Módulo: Gestão de Clientes e Contatos `[CLI]`
CRM leve para gestão de dados de clientes.

| ID | Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| **CLI-CTT-001** | Gestão de Contatos | Cadastro de contatos WhatsApp com histórico de interações. | Alta |
| **CLI-CRM-001** | Gestão de Clientes | Cadastro de PF/PJ com dados fiscais e múltiplos contatos. | Alta |

### 3.6. Módulo: Gestão de Atendimentos `[ATD]`
Núcleo operacional do sistema.

| ID | Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| **ATD-LIF-001** | Orquestrador | Coordenação central de mensagens, intenções e respostas. | Crítica |
| **ATD-LIF-003** | Transferência | Mecanismo de transferência entre Bot/Humano e entre Departamentos. | Crítica |
| **ATD-CTX-001** | Histórico de Mensagens | Armazenamento detalhado de todas as interações e metadados. | Crítica |

### 3.7. Módulo: Integração Trello (Gestão Visual) `[TRL]`
Sincronização bidirecional para gestão visual.

| ID | Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| **TRL-FLW-001** | Sync de Boards | Criação automática de Quadros no Trello baseados em Fluxos. | Alta |
| **TRL-LST-001** | Sync de Listas | Espelhamento de Etapas do fluxo como Listas no Trello. | Alta |
| **TRL-CRD-001** | Sync de Cards | Criação e atualização de Cards para cada atendimento. | Alta |
| **TRL-WEB-002** | Webhooks Trello | Processamento de eventos do Trello (movimentação) para atualizar o sistema. | Alta |

### 3.8. Módulo: Integração Evolution API `[EVO]`
Gateway de comunicação WhatsApp.

| ID | Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| **EVO-MSG-001** | Multi-Instância | Suporte a múltiplos números de WhatsApp conectados. | Alta |
| **EVO-MSG-002** | Envio de Mídia | Suporte a texto, imagem, áudio, vídeo e documentos. | Alta |

---

## 4. Requisitos Não Funcionais

### 4.1. Desempenho
- **Tempo de Resposta:** As interações do bot devem ter latência < 3s.
- **Sincronização:** A atualização entre Trello e Sistema deve ocorrer em < 5s.

### 4.2. Segurança
- **Dados Sensíveis:** Senhas e tokens devem ser criptografados.
- **Autenticação:** Uso de JWT e OAuth para sessões seguras.
- **Isolamento:** Dados de diferentes departamentos devem ser logicamente isolados.

### 4.3. Confiabilidade
- **Disponibilidade:** SLA de 99.5% de uptime.
- **Recuperação:** Mecanismos de retry automático para falhas de webhook.

---

## 5. Arquitetura Técnica

### 5.1. Visão Geral
O sistema adota uma arquitetura monolítica modular baseada em **Django**, com serviços desacoplados para integrações específicas.

### 5.2. Componentes Chave
- **Backend:** Django + Django REST Framework.
- **Banco de Dados:** PostgreSQL (Relacional + JSON).
- **Mensageria:** Redis (Cache e Filas).
- **Integração Trello:** App dedicado `trello_sync` atuando como sidecar lógico.
- **WhatsApp:** Evolution API (Gateway externo).

### 5.3. Fluxo de Dados (Trello Sync)
1.  **Django → Trello:** Signals (`post_save`) disparam serviços que chamam a API do Trello.
2.  **Trello → Django:** Webhooks do Trello enviam eventos para endpoint Django, que processa e atualiza o banco local.

---

## 6. Métricas de Sucesso

- **Eficiência Operacional:** Redução de 30% no tempo de triagem com uso de IA.
- **Adoção:** 100% dos atendimentos registrados e sincronizados no Trello.
- **Estabilidade:** Zero perdas de mensagens ou dessincronização de status crítica.

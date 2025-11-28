# Product Requirements Document (PRD) - Smart Core Assistant Painel

**Versão:** 2.0
**Data:** 27/11/2025
**Status:** Em Desenvolvimento
**Responsável:** Arquiteto de Software

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
- **Evolution API:** Gateway de API para WhatsApp.

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

## 3. Stack Tecnológico

A arquitetura do projeto foi definida para garantir robustez, escalabilidade e manutenibilidade, seguindo práticas de Clean Code e arquitetura de serviços.

### 3.1. Backend e Core
-   **Linguagem:** Python 3.13+
-   **Framework Web:** Django 5.x + Django REST Framework (DRF)
-   **Gerenciamento de Dependências:** `uv` (Astral)
-   **Tasks Assíncronas:** Django-Q2 (Cluster Redis)
-   **Cache e Broker:** Redis
-   **Orquestração de IA:** LangChain (Integração com múltiplos modelos)

### 3.2. Banco de Dados e Armazenamento
-   **Relacional:** PostgreSQL 16+ (Dados de negócios, usuários, atendimentos)
-   **Vetorial:** PostgreSQL (`pgvector`) (para Embeddings/RAG)
-   **Configuração Remota:** Firebase Remote Config

### 3.3. Integrações e APIs Externas
-   **WhatsApp:** Evolution API (Multi-instância, v2)
-   **Gestão Visual:** Trello API (via Webhooks e API REST)
-   **Inteligência Artificial:**
    -   **LLMs:** OpenAI API, Groq, Ollama (Local/Híbrido)
    -   **Embeddings:** OpenAI, HuggingFace
-   **Autenticação Externa:** Firebase Auth / OAuth Providers

### 3.4. Infraestrutura e DevOps
-   **Containerização:** Docker e Docker Compose
-   **Testes:** Pytest (com cobertura mínima de 80%)
-   **Linting/Formatting:** Ruff, Pyright (Strict Mode)
-   **CI/CD:** GitHub Actions (Sugerido)

---

## 4. Recursos Definidos e Requisitos Funcionais

O sistema é modularizado para facilitar a manutenção e escalabilidade. Abaixo estão os módulos e recursos já definidos.

### 4.1. Módulo: Configuração e Núcleo do Sistema `[SYS]`
-   **SYS-INI-001:** Inicialização do Firebase Admin SDK.
-   **SYS-INI-002:** Gestão de variáveis via Remote Config e `.env`.
-   **SYS-INI-003:** Health Check e Monitoramento de sistema.
-   **SYS-DAT-001:** Serviços de dados unificados (Facade).
-   **SYS-DAT-002:** Gerenciamento de Vector Storage para RAG (`pgvector`).

### 4.2. Módulo: Gestão Administrativa e Acesso `[ADM]`
-   **ADM-USR-001/002:** Cadastro e Autenticação de usuários/atendentes.
-   **ADM-USR-003:** Gestão de Papéis e Permissões (RBAC com `django-role-permissions`).
-   **ADM-USR-004:** Dashboard Gerencial (KPIs).
-   **ADM-CFG-001:** Gestão de OAuth (Trello/ClickUp).

### 4.3. Módulo: Gestão Operacional `[OPS]`
-   **OPS-ORG-001:** Gestão de Departamentos (com isolamento de dados).
-   **OPS-ORG-002:** Gestão de Atendentes (Horários, Limites).
-   **OPS-FLW-001/002:** Configuração de Fluxos Kanban e Etapas personalizadas.
-   **OPS-FLW-003:** Registro de movimentação e cálculo de SLA.

### 4.4. Módulo: Treinamento e Conhecimento (RAG UI) `[TRN]`
-   **TRN-CON-001:** Ingestão de documentos (PDF, DOCX, TXT).
-   **TRN-CON-002:** Curadoria de conteúdo (Human-in-the-loop).
-   **TRN-INT-001:** Cadastro de Intenções e exemplos (Few-shot learning).
-   **TRN-CON-003:** Gestão de embeddings ativos.

### 4.5. Módulo: Gestão de Clientes e Contatos `[CLI]`
-   **CLI-CTT-001:** Gestão de contatos WhatsApp (JID/LID).
-   **CLI-CRM-001:** Mini-CRM para PF/PJ (Dados fiscais, múltiplos contatos).
-   **CLI-CRM-002:** Vinculação e unificação de histórico.

### 4.6. Módulo: Gestão de Atendimentos `[ATD]`
-   **ATD-LIF-001:** Orquestrador central de mensagens.
-   **ATD-LIF-003:** Mecanismo de Transferência (Bot ↔ Humano, Depto ↔ Depto).
-   **ATD-CTX-001:** Log completo de mensagens e metadados.
-   **ATD-CTX-002:** Manutenção de contexto conversacional (Memória).

### 4.7. Módulo: Integração Trello (Sidecar `trello_sync`) `[TRL]`
-   **TRL-FLW-001:** Sync de Boards (Fluxos).
-   **TRL-LST-001:** Sync de Listas (Etapas).
-   **TRL-CRD-001/002:** Sync de Cards (Atendimentos) com detalhes ricos.
-   **TRL-WEB-001/002:** Gestão automática de Webhooks para atualizações em tempo real (Bidirecional).
-   **Arquitetura:** App dedicado (`trello_sync`) usando Signals para desacoplamento.

### 4.8. Módulo: Integração Evolution API `[EVO]`
-   **EVO-MSG-001:** Suporte a múltiplas instâncias (Multitenancy) via `EvolutionInstance`.
-   **EVO-MSG-002:** Envio/Recebimento de Mídia (Áudio, Imagem, Docs).
-   **EVO-MSG-003:** Webhooks de status de entrega (Sent, Delivered, Read).
-   **EVO-MSG-004:** Mapeamento de contatos (`EvolutionContact`) para suporte a múltiplos números por cliente.
-   **EVO-MSG-005:** Whitelist para ignorar números específicos (ex: bots, testes).

---

## 5. Arquitetura Técnica Detalhada

### 5.1. Padrão de Projeto
-   **Services Pattern:** Lógica de negócios encapsulada em `services/`, nunca em Views ou Models.
-   **Fat Models Avoidance:** Models apenas para estrutura de dados.
-   **Facade:** Uso de `__init__.py` para expor APIs públicas dos módulos.
-   **Domain-Driven Design (DDD) Lite:** Separação clara entre Domínio, Serviços e Interface.

### 5.2. Fluxo de Integração Trello (Sidecar)
1.  **Django → Trello:** Alterações no modelo disparam `Signals`. O app `trello_sync` intercepta e ageda tasks no Django-Q2 para chamar a API do Trello.
2.  **Trello → Django:** Webhooks do Trello enviam eventos para endpoint Django, que processa e atualiza o banco local.
3.  **Isolamento:** O app `trello_sync` possui seus próprios modelos de mapeamento (`TrelloBoard`, `TrelloCard`), não alterando as tabelas core do sistema.

---

## 6. Métricas de Sucesso
-   **Eficiência Operacional:** Redução de 30% no tempo de triagem com uso de IA.
-   **Adoção:** 100% dos atendimentos registrados e sincronizados no Trello.
-   **Estabilidade:** Zero perdas de mensagens ou dessincronização de status crítica.
-   **Latência:** Resposta do Bot < 3s.

---

## 7. Roadmap Futuro e Sugestões de Melhoria

Baseado na análise da arquitetura atual, sugerem-se as seguintes funcionalidades para evoluir o produto:

### 7.1. Curto Prazo (Operacional)
1.  **Transcrição de Áudio (Speech-to-Text):**
    *   *Descrição:* Converter automaticamente áudios recebidos no WhatsApp em texto dentro do Card do Trello.
    *   *Valor:* Facilita a leitura rápida pelo atendente sem precisar ouvir o áudio.
2.  **Análise de Sentimento em Tempo Real:**
    *   *Descrição:* A IA analisa o tom da mensagem do cliente. Se detectar "Raiva" ou "Frustração", marca o ticket como "Urgente" e alerta o supervisor.
    *   *Valor:* Prevenção de churn e gestão de crises.
3.  **Gestão de Prompts (System Prompts):**
    *   *Descrição:* Interface administrativa para criar, versionar e testar prompts do sistema sem necessidade de deploy.
    *   *Valor:* Agilidade na evolução da "personalidade" e regras do bot.

### 7.2. Médio Prazo (Estratégico)
4.  **Sugestão de Resposta (Human-in-the-loop):**
    *   *Descrição:* O Bot gera um rascunho de resposta no Trello/Painel. O atendente apenas revisa e aprova.
    *   *Valor:* Aumenta a produtividade do atendente mantendo a supervisão humana.
5.  **Suporte Omnichannel Real:**
    *   *Descrição:* Integrar Instagram Direct e Telegram através da Evolution API, unificando tudo no mesmo fluxo Kanban.
    *   *Valor:* Centralização total do atendimento.
6.  **Observabilidade Avançada:**
    *   *Descrição:* Implementação de OpenTelemetry e Sentry para rastreamento distribuído de requisições e erros.
    *   *Valor:* Diagnóstico rápido de problemas em produção.

### 7.3. Longo Prazo (Governança)
7.  **Módulo LGPD/GDPR:**
    *   *Descrição:* Ferramentas para anonimização de dados de clientes e exportação de histórico mediante solicitação.
    *   *Valor:* Conformidade legal.
8.  **Analytics Preditivo:**
    *   *Descrição:* Previsão de volume de atendimento por dia/hora para auxiliar na escala de atendentes.
    *   *Valor:* Otimização de recursos humanos.
9.  **Testes de Carga:**
    *   *Descrição:* Implementação de scripts Locust para simular múltiplos atendimentos simultâneos e garantir estabilidade.
    *   *Valor:* Garantia de robustez em picos de acesso.

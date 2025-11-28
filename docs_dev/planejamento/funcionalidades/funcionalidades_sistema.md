# Registro de Funcionalidades do Sistema

**Data:** 27/11/2025
**Versão:** 1.0
**Status:** Em Planejamento

---

## 1. Introdução

Este documento tem como objetivo registrar, de forma estruturada, todas as funcionalidades do sistema **Smart Core Assistant Painel**. Ele serve como base para o contrato de fornecimento de serviço, garantindo transparência e alinhamento sobre o escopo do produto.

As funcionalidades estão organizadas por módulos e sub-módulos, permitindo uma visão clara da arquitetura e das capacidades do sistema.

## 2. Sistema de Codificação

Para garantir a organização e escalabilidade, cada funcionalidade recebe um código único no formato `[MOD]-[SUB]-[SEQ]`:

*   **[MOD]**: Código do Módulo (3 letras Maiúsculas). Identifica a grande área do sistema (ex: `BOT` para Chat Bot).
*   **[SUB]**: Código do Sub-módulo (3 letras Maiúsculas). Identifica um componente específico dentro do módulo (ex: `PRE` para Pré-análise).
*   **[SEQ]**: Sequencial Numérico (3 dígitos). Identificador único da funcionalidade dentro do sub-módulo (ex: `001`).

**Exemplo:** `BOT-PRE-001` refere-se à primeira funcionalidade de Pré-análise do Chat Bot.

---

## 3. Módulo: Configuração e Núcleo do Sistema `[SYS]`

Este módulo abrange as funcionalidades essenciais de inicialização, configuração e serviços base que sustentam toda a aplicação.

### 3.1. Inicialização e Configuração `[INI]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **SYS-INI-001** | **Inicialização do Firebase** | Inicializa a conexão com o Firebase Admin SDK, permitindo o acesso a serviços como Firestore, Auth e Remote Config. |
| **SYS-INI-002** | **Gestão de Variáveis de Ambiente (Remote Config)** | Carrega e gerencia as configurações do sistema a partir do Firebase Remote Config, permitindo ajustes dinâmicos de parâmetros (ex: chaves de API, prompts) sem necessidade de redeploy. |
| **SYS-INI-003** | **Health Check e Monitoramento** | Endpoint para verificação de saúde do sistema (Health Check), utilizado por orquestradores (Docker/K8s) para garantir a disponibilidade da aplicação. |

### 3.2. Serviços de Dados e Armazenamento `[DAT]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **SYS-DAT-001** | **Serviços de Dados Unificados** | Camada de abstração para acesso e manipulação de dados, garantindo consistência e centralização da lógica de persistência. |
| **SYS-DAT-002** | **Armazenamento Vetorial Nativo (pgvector)** | Gerencia o armazenamento e operações vetoriais diretamente no PostgreSQL através da extensão `pgvector`, eliminando a necessidade de serviços externos. |

---

## 4. Módulo: Gestão Administrativa e Acesso `[ADM]`

Este módulo centraliza as funcionalidades de interface administrativa, gestão de usuários e configurações gerais de acesso.

### 4.1. Gestão de Usuários e Autenticação `[USR]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **ADM-USR-001** | **Cadastro de Usuários** | Permite o registro de novos usuários no sistema, com validação de credenciais e unicidade de login. |
| **ADM-USR-002** | **Autenticação e Login** | Gerencia o acesso seguro ao sistema, autenticando credenciais e redirecionando o usuário para sua área de trabalho correta (Kanban de Departamento ou Treinamento) com base no perfil de atendente vinculado. |
| **ADM-USR-003** | **Gestão de Permissões e Papéis** | Interface para atribuição de papéis (ex: Gerente) e permissões específicas aos usuários, controlando o acesso a funcionalidades sensíveis. |
| **ADM-USR-004** | **Dashboard Gerencial** | Painel exclusivo para gerentes com métricas consolidadas de atendimentos por status e departamento, oferecendo visão macro da operação. |

### 4.2. Configurações e Integrações de UI `[CFG]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **ADM-CFG-001** | **Configuração OAuth (ClickUp/Trello)** | Gerencia o fluxo de autenticação OAuth para integrações externas (como ClickUp e Trello), trocando códigos de autorização por tokens de acesso e persistindo-os de forma segura. |

---

## 5. Módulo: Gestão Operacional `[OPS]`

Este módulo define a estrutura organizacional e as regras de negócio para o atendimento, incluindo departamentos, atendentes e fluxos de trabalho.

### 5.1. Estrutura Organizacional `[ORG]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **OPS-ORG-001** | **Gestão de Departamentos** | Cadastro e configuração de departamentos (ex: Comercial, Suporte), incluindo chaves de API e instâncias de comunicação específicas. |
| **OPS-ORG-002** | **Gestão de Atendentes** | Cadastro de agentes humanos, definição de horários de trabalho, especialidades e limites de atendimentos simultâneos. |
| **OPS-ORG-003** | **Gestão de Instâncias (AppInstance)** | Configuração das instâncias de conexão com canais de mensagem (WhatsApp), vinculando-as a departamentos ou atendentes específicos. |

### 5.2. Fluxos de Trabalho (Workflow) `[FLW]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **OPS-FLW-001** | **Configuração de Fluxos de Atendimento** | Definição de fluxos de trabalho personalizados por departamento, compostos por etapas sequenciais (Kanban). |
| **OPS-FLW-002** | **Gestão de Etapas do Fluxo** | Configuração das colunas/etapas do fluxo (ex: "Em Análise", "Aguardando Cliente"), definindo cores, ordenação e regras de automação. |
| **OPS-FLW-003** | **Registro de Movimentação** | O sistema registra todo o histórico de movimentação dos atendimentos entre etapas, calculando tempos de permanência (SLA) e responsáveis por cada ação. |

---

## 6. Módulo: Treinamento e Conhecimento (RAG UI) `[TRN]`

Este módulo oferece interfaces para que gestores alimentem e curem a base de conhecimento da Inteligência Artificial.

### 6.1. Gestão de Conteúdo e Treinamento `[CON]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **TRN-CON-001** | **Upload e Ingestão de Documentos** | Interface para envio de arquivos (PDF, DOCX, TXT) ou inserção de texto livre para treinamento da IA. |
| **TRN-CON-002** | **Pré-processamento e Curadoria** | Fluxo de revisão onde o conteúdo inserido é analisado, melhorado pela própria IA e apresentado ao gestor para aprovação, edição ou descarte antes da indexação final. |
| **TRN-CON-003** | **Gestão de Treinamentos Vetorizados** | Painel para visualizar, editar ou excluir treinamentos que já foram processados e estão ativos na base de conhecimento vetorial. |

### 6.2. Gestão de Intenções (Query Compose) `[INT]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **TRN-INT-001** | **Cadastro de Intenções (Query Compose)** | Interface para definir intenções específicas (ex: "Pedir Reembolso"), associando exemplos de perguntas e o comportamento (prompt) esperado da IA. |
| **TRN-INT-002** | **Verificação e Ajuste de Intenções** | Ferramenta para monitorar a saúde das intenções cadastradas (se possuem embeddings gerados corretamente) e realizar ajustes finos nas descrições e comportamentos. |

---

## 8. Módulo: Gestão de Clientes e Contatos `[CLI]`

Este módulo gerencia a base de dados de pessoas e empresas que interagem com o sistema, garantindo a integridade e unicidade dos dados.

### 8.1. Gestão de Contatos (WhatsApp) `[CTT]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **CLI-CTT-001** | **Gestão de Contatos** | Cadastro e manutenção de contatos identificados pelo número de telefone (WhatsApp), incluindo nome de perfil e histórico de interações. |
| **CLI-CTT-002** | **Validação de Telefone** | Validação rigorosa de formatos de telefone, garantindo a padronização (DDI+DDD+Número) para comunicação via API. |

### 8.2. Gestão de Clientes (CRM) `[CRM]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **CLI-CRM-001** | **Gestão de Clientes (PF/PJ)** | Cadastro completo de clientes (Pessoa Física ou Jurídica) com dados fiscais (CPF/CNPJ), endereço e múltiplos contatos vinculados. |
| **CLI-CRM-002** | **Vinculação Contato-Cliente** | Permite associar um ou mais contatos de WhatsApp a um cadastro de cliente, unificando o histórico de atendimento de diferentes números. |

---

## 9. Módulo: Gestão de Atendimentos `[ATD]`

Este é o módulo central de operação, orquestrando o ciclo de vida dos atendimentos desde a recepção da mensagem até a finalização.

### 9.1. Ciclo de Vida e Orquestração `[LIF]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **ATD-LIF-001** | **Orquestrador de Atendimentos** | Componente central que coordena o processamento de mensagens, análise de intenções, execução de regras de bot e geração de respostas. |
| **ATD-LIF-002** | **Gestão de Estrutura de Atendimento** | Garante a existência e configuração correta da estrutura base (Departamentos, Fluxos e Etapas) para novos atendimentos, aplicando regras de fallback quando necessário. |
| **ATD-LIF-003** | **Transferência e Atribuição** | Mecanismos para transferir atendimentos entre departamentos ou atribuir a atendentes humanos, gerenciando a transição de responsabilidade (Bot vs Humano). |

### 9.2. Histórico e Contexto `[CTX]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **ATD-CTX-001** | **Registro de Mensagens e Metadados** | Armazenamento detalhado de todas as mensagens trocadas, incluindo tipo (texto, áudio, imagem) e metadados técnicos (IDs da API, status de entrega). |
| **ATD-CTX-002** | **Manutenção de Contexto de Conversa** | O sistema mantém um contexto dinâmico para cada atendimento, armazenando variáveis de estado e chaves de API para garantir a continuidade da conversa. |

---

## 10. Módulo: Integrações (Evolution API & Trello) `[INT]`

Este módulo conecta o sistema ao mundo externo, gerenciando a comunicação via WhatsApp e a sincronização com ferramentas de gestão de tarefas.

### 10.1. Integração Evolution API (WhatsApp) `[EVO]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **INT-EVO-001** | **Gestão de Instâncias Evolution** | Configuração e monitoramento das instâncias da Evolution API, responsáveis por enviar e receber mensagens do WhatsApp. |
| **INT-EVO-002** | **Mapeamento de Contatos (Sync)** | Sincronização entre contatos do WhatsApp (JID/LID) e contatos do sistema, mantendo metadados técnicos atualizados. |
| **INT-EVO-003** | **Whitelist de Números** | Lista de permissão para números que podem interagir com o sistema, útil para ambientes de teste ou restritos. |

### 10.2. Sincronização Trello (Kanban) `[TRL]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **INT-TRL-001** | **Sincronização de Fluxos (Boards/Lists)** | Espelhamento automático da estrutura de departamentos e fluxos do sistema para Quadros e Listas no Trello. |
| **INT-TRL-002** | **Sincronização de Tickets (Cards)** | Criação e atualização automática de Cards no Trello para cada atendimento, mantendo status e informações sincronizadas bidirecionalmente. |
| **BOT-EMB-002** | **Chunking de Documentos** | Divide documentos longos em fragmentos menores e lógicos para otimizar a indexação e recuperação. |
| **BOT-EMB-003** | **Carregamento de Documento (Conteúdo)** | Processa e indexa conteúdo textual direto para a base de conhecimento. |
| **BOT-EMB-004** | **Carregamento de Documento (Arquivo)** | Processa arquivos (PDF, DOCX, TXT) carregados, extraindo texto e gerando embeddings para a base de conhecimento. |

### 4.4. Geração de Resposta (RAG) `[RAG]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **BOT-RAG-001** | **Montagem de Contexto** | O sistema recupera o histórico da conversa e as informações relevantes encontradas na busca vetorial para montar um contexto rico que será enviado ao modelo de linguagem (LLM). |
| **BOT-RAG-002** | **Geração de Resposta Contextual** | Utilizando o contexto montado, o sistema gera uma resposta natural e precisa para o usuário, seguindo as diretrizes de tom de voz e personalidade definidas para o assistente. |

---

## 4. Módulo: Integração Trello (Gestão de Atendimento) `[TRL]`

Este módulo gerencia a sincronização bidirecional entre o sistema e o Trello, utilizando-o como interface visual para a gestão dos atendimentos.

### 4.1. Gestão de Fluxos e Quadros `[FLW]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **TRL-FLW-001** | **Geração Automática de Quadros (Boards)** | Ao criar um novo "Fluxo de Atendimento" no sistema, é gerado automaticamente um Quadro correspondente na área de trabalho do Trello vinculada, servindo como o espaço de trabalho para aquele fluxo. |
| **TRL-FLW-002** | **Sincronização de Metadados do Quadro** | Alterações no nome ou descrição do Fluxo no sistema são refletidas automaticamente no Quadro do Trello, mantendo a consistência das informações. |

### 4.2. Gestão de Etapas e Listas `[LST]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **TRL-LST-001** | **Geração Automática de Listas** | O sistema gera automaticamente Listas dentro do Quadro do Trello correspondentes às etapas do fluxo. Por padrão, são criadas as listas: "Fila de Atendimento", "Em Atendimento", "Pendência", "Resolvido" e "Cancelado". |
| **TRL-LST-002** | **Ordenação de Listas** | O sistema garante que as listas no Trello sigam a ordem lógica definida no fluxo de atendimento, corrigindo a posição caso sejam movidas acidentalmente de forma incorreta. |

### 4.3. Gestão de Atendimentos e Cartões `[CRD]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **TRL-CRD-001** | **Criação Automática de Cartões (Cards)** | Quando um novo atendimento é iniciado, o sistema cria automaticamente um Cartão na lista "Fila de Atendimento" (ou etapa inicial configurada) do respectivo Quadro no Trello. |
| **TRL-CRD-002** | **Preenchimento de Detalhes do Cartão** | O cartão é criado contendo informações essenciais do atendimento: Título (Resumo), Descrição (com dados do cliente e contexto), Etiquetas (Prioridade, Departamento) e Data de Início. |
| **TRL-CRD-003** | **Sincronização de Movimentação (Bidirecional)** | Se o cartão for movido no Trello para outra lista, o sistema atualiza o status/etapa do atendimento no banco de dados. Se o status for alterado no sistema, o cartão é movido automaticamente no Trello. |
| **TRL-CRD-004** | **Arquivamento Automático** | Quando um atendimento é finalizado ou cancelado no sistema, o cartão correspondente no Trello pode ser movido para a lista "Resolvido"/"Cancelado" ou arquivado, conforme configuração. |

### 4.4. Gestão de Membros e Atendentes `[MEM]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **TRL-MEM-001** | **Sincronização de Atendentes** | Os usuários cadastrados como atendentes no sistema são mapeados para seus respectivos usuários no Trello (Membros). |
| **TRL-MEM-002** | **Atribuição Automática** | Quando um atendimento é atribuído a um atendente no sistema, o respectivo Membro é adicionado automaticamente ao Cartão no Trello. |

### 4.5. Webhooks e Eventos `[WEB]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **TRL-WEB-001** | **Registro Automático de Webhooks** | O sistema registra e gerencia automaticamente os Webhooks necessários em cada Quadro criado, garantindo que eventos externos (ações no Trello) sejam capturados. |
| **TRL-WEB-002** | **Processamento de Eventos em Tempo Real** | O sistema processa eventos recebidos do Trello (ex: movimentação de card, comentário) em tempo real para atualizar o estado do atendimento e disparar automações (ex: enviar mensagem ao cliente). |

---

## 5. Módulo: Integração Evolution API (WhatsApp) `[EVO]`

Este módulo gerencia a comunicação via WhatsApp utilizando a Evolution API.

### 5.1. Mensageria `[MSG]`

| Código | Funcionalidade | Descrição Detalhada |
| :--- | :--- | :--- |
| **EVO-MSG-001** | **Conexão Multi-Instância** | O sistema suporta a conexão e gerenciamento de múltiplas instâncias do WhatsApp (números diferentes), permitindo a segmentação por departamentos ou marcas. |
| **EVO-MSG-002** | **Envio de Mensagens de Texto e Mídia** | Capacidade de enviar mensagens de texto, imagens, áudios, vídeos e documentos para os usuários via WhatsApp. |
| **EVO-MSG-003** | **Recebimento de Status de Entrega** | O sistema monitora e registra o status das mensagens enviadas (enviado, entregue, lido), fornecendo feedback sobre a comunicação. |

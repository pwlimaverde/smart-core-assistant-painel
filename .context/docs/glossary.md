# Glossário

Este documento define os termos e conceitos de domínio utilizados no projeto Smart Core Assistant Painel.

---

## Termos de Negócio

### Atendimento
Ticket de suporte ou conversa com um cliente via WhatsApp. Um atendimento pode conter múltiplas mensagens e passar por diferentes status (aberto, em andamento, resolvido, encerrado).

### Cliente
Pessoa física ou jurídica que é atendida pelo sistema. Associado a um número de telefone WhatsApp.

### Contato
Informações de contato de um cliente, incluindo telefone, email e dados adicionais.

### Departamento
Área organizacional que recebe e processa atendimentos. Exemplos: Comercial, Suporte, Financeiro.

### Fluxo de Atendimento
Sequência de etapas e regras que definem como um atendimento deve ser processado. Pode incluir respostas automáticas, roteamento e escalação.

### Tenant
Cliente da plataforma SaaS. Cada tenant possui seu próprio banco de dados isolado e configurações independentes.

### Usuário
Pessoa que acessa o painel administrativo para gerenciar atendimentos, configurações e relatórios.

---

## Termos Técnicos

### Adapter
Padrão de design que permite que interfaces incompatíveis trabalhem juntas. No projeto, usado para integrar Trello, ClickUp e Notion via interface unificada.

### Celery Worker
Processo que executa tarefas assíncronas em background. Utilizado para processamento de webhooks, análise de IA e sincronização.

### Chunk
Fragmento de texto de um documento, dividido para processamento de embeddings. Tamanho típico: 500-1000 tokens.

### Embedding
Representação vetorial de texto em espaço de alta dimensão. Usado para busca semântica (RAG).

### Evolution API
API de terceiros para integração com WhatsApp Business. Permite enviar/receber mensagens e gerenciar instâncias.

### Feature
Módulo funcional com responsabilidade específica. Segue estrutura DDD com datasource, domain e usecase.

### LangChain
Framework para desenvolvimento de aplicações com LLMs. Orquestra chamadas para modelos de IA e processamento de documentos.

### Multi-Tenancy
Arquitetura que permite múltiplos clientes (tenants) compartilharem a mesma aplicação com dados isolados.

### pgvector
Extensão PostgreSQL para armazenamento e busca de vetores. Utilizada para embeddings de documentos.

### RAG (Retrieval-Augmented Generation)
Técnica que combina busca de documentos relevantes com geração de texto por LLM. Usado para respostas baseadas em conhecimento.

### Result Pattern
Padrão de tratamento de erros que encapsula sucesso ou falha em um tipo de retorno explícito (Success/Failure).

### Service Hub
Factory central que cria e disponibiliza instâncias de serviços. Ponto único de acesso a funcionalidades.

### Signal (Django)
Mecanismo de notificação que permite desacoplar ações. Quando um evento ocorre (ex: atendimento criado), signals disparam ações relacionadas.

### Usecase
Caso de uso que encapsula uma operação de negócio específica. Coordena datasources e regras de domínio.

### Webhook
Callback HTTP que permite receber notificações de eventos externos. Usado para receber mensagens do WhatsApp via Evolution API.

### Workspace (Atendimento Unificado)
Tela única do operador (`/workspace/`) que combina chat estilo WhatsApp
Web e Kanban sobre `EtapaFluxo`/`Atendimento`. Entregue pelo app
`atendimento_unificado` e disparada por um item dedicado no sidebar do
`base_dashboard.html`. Atualização em tempo real via Server-Sent Events
sobre Redis pub/sub. Trello permanece como espelho passivo.

### Campo Personalizado
Definição configurável por tenant (`CampoPersonalizado`) que descreve um
dado estruturado a ser coletado durante o atendimento — por exemplo
"CNPJ do cliente" ou "data preferida de visita". Cada campo tem escopo
`GLOBAL` (todos os fluxos) ou `FLUXO` (vinculado a um
`FluxoAtendimento`), tipo (`texto`/`numero`/`data`/`escolha`/`booleano`)
e flag `extrair_automaticamente` que indica se o bot deve tentar extrair
o valor da conversa via LLM.

### Valor de Campo (`ValorCampoAtendimento`)
Valor concreto de um `CampoPersonalizado` para um `Atendimento`
específico. Persiste origem (`MANUAL`/`BOT`/`IMPORT`), confiança
(quando origem é BOT) e o ID lógico da mensagem que originou a extração.
Garante idempotência: nunca sobrescreve `MANUAL` e só sobrescreve `BOT`
quando nova confiança é maior.

### LeituraAtendimento
Tabela própria do app `atendimento_unificado` (`atu_leitura_atendimento`)
que registra a última leitura de um atendimento por um atendente
específico. Substitui campo `data_ultima_leitura_atendente` em
`Atendimento` para preservar o princípio de independência cross-app.
Cálculo de não-lidos via JOIN com `Mensagem`.

### SSE (Server-Sent Events)
Mecanismo HTTP unidirecional usado para enviar atualizações em tempo
real do servidor para o navegador. O Workspace usa SSE no endpoint
`/workspace/events/` (async view) sobre canal Redis pub/sub
`sse:{tenant_slug}:events` — sem necessidade de Django Channels.

### Feature Flag `ATENDIMENTO_UNIFICADO_ENABLED`
Configuração global em `settings.py` (env vars) que habilita o Workspace.
Allowlist por tenant via `ATENDIMENTO_UNIFICADO_TENANT_SLUGS`. Default
`OFF` — rotas `/workspace/*` retornam 200 com tela "indisponível" e o
item de sidebar fica oculto. Permite rollout gradual por tenant sem
deploy.

### Princípio de Independência Cross-App
Diretriz arquitetural: todo app utilitário ou de visualização (como
`atendimento_unificado` e `trello_sync`) integra-se aos apps de produção
exclusivamente via Django signals e Celery tasks **dentro** do próprio
app. FKs cross-app são lógicas (`BigIntegerField`). Apps de produção
nunca são editados para servir consumidores. Permite rollback simples
(remover de `INSTALLED_APPS`) sem afetar dados existentes.

---

## Siglas

| Sigla | Significado |
|-------|-------------|
| API | Application Programming Interface |
| CRUD | Create, Read, Update, Delete |
| DDD | Domain-Driven Design |
| DRF | Django REST Framework |
| JWT | JSON Web Token |
| LLM | Large Language Model |
| NLP | Natural Language Processing |
| PK | Primary Key |
| RAG | Retrieval-Augmented Generation |
| REST | Representational State Transfer |
| SaaS | Software as a Service |
| SDK | Software Development Kit |
| SSE | Server-Sent Events |
| UI | User Interface |
| UX | User Experience |

---

## Status de Atendimento

| Status | Descrição |
|--------|-----------|
| `aberto` | Atendimento recém-criado, aguardando processamento |
| `em_andamento` | Atendimento sendo processado por agente humano ou IA |
| `aguardando_cliente` | Aguardando resposta do cliente |
| `resolvido` | Problema resolvido, pendente de fechamento |
| `encerrado` | Atendimento finalizado |
| `cancelado` | Atendimento cancelado pelo sistema ou usuário |

---

## Tipos de Mensagem

| Tipo | Descrição |
|------|-----------|
| `entrada` | Mensagem recebida do cliente |
| `saida` | Mensagem enviada para o cliente |
| `sistema` | Mensagem gerada automaticamente pelo sistema |
| `interna` | Nota interna visível apenas para atendentes |

---

## Roles de Usuário

| Role | Descrição | Permissões |
|------|-----------|------------|
| `admin` | Administrador do tenant | Acesso total ao tenant |
| `supervisor` | Supervisor de atendimentos | Gerencia atendentes e visualiza relatórios |
| `atendente` | Atendente de suporte | Processa atendimentos atribuídos |
| `viewer` | Visualizador | Apenas visualização de dados |

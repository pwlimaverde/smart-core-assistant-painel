# Glossário

## Termos Técnicos

### A

**ai_engine**
: Módulo central de processamento de linguagem natural. Contém os casos de uso para análise de mensagens, conteúdo e avaliações.

**Atendente**
: Usuário do sistema responsável por atender clientes via WhatsApp.

**Atendimento**
: Registro de uma interação/conversa entre atendente e cliente.

### C

**Celery**
: Framework para processamento de tarefas assíncronas. Usado para webhooks e IA.

**ClickUp**
: Plataforma de gestão de projetos integrada ao sistema.

**Clean Architecture**
: Padrão arquitetural aplicado nos módulos de negócio, separando domínio de infraestrutura.

### D

**Datasource**
: Camada de acesso a dados nos módulos. Implementa a interface de repository.

**Departamento**
: Unidade organizacional que agrupa atendentes e fluxos de atendimento.

### E

**Embeddings**
: Representações vetoriais de texto usadas para busca semântica.

**Evolution API**
: Serviço de API para WhatsApp Business usado nas integrações.

### F

**Feature (módulo)**
: Unidade de funcionalidade no ai_engine seguindo Clean Architecture.

**Fluxo de Atendimento**
: Sequência de etapas por onde um atendimento passa.

### L

**LangChain**
: Framework de IA usado para orquestrar LLMs e pipelines de processamento.

**LLM (Large Language Model)**
: Modelos de linguagem como GPT, Groq, Ollama.

### M

**MCP (Model Context Protocol)**
: Protocolo para extensão de capacidades de IA com ferramentas externas.

**Mensagem**
: Comunicação individual dentro de um atendimento.

**Multi-tenancy**
: Arquitetura que permite múltiplas organizações no mesmo sistema isoladamente.

### N

**Notion**
: Plataforma de documentação e bases de dados integrada ao sistema.

### O

**OpenSpec**
: Metodologia de especificação de mudanças usada no projeto.

### P

**pgvector**
: Extensão PostgreSQL para armazenamento e busca de vetores (embeddings).

**py-return-success-or-error**
: Biblioteca Python para retorno de sucesso ou erro de forma tipada.

**Pyright**
: Verificador de tipos estático para Python, usado em modo estrito.

### R

**Repository (pattern)**
: Padrão de abstração de acesso a dados.

**ReturnSuccessOrError**
: Tipo de retorno padrão do padrão py-return-success-or-error.

**Ruff**
: Linter e formatador Python extremamente rápido.

### S

**Signal (Django)**
: Mecanismo de eventos do Django usado para disparar sincronizações.

**ServiceHub**
: Singleton que centraliza acesso aos serviços do sistema.

### T

**Taskipy**
: Executor de tarefas definidas no pyproject.toml.

**Tenant**
: Organização/cliente isolado no sistema multi-tenant.

**Trello**
: Plataforma de kanban integrada para gestão de tickets.

### U

**Usecase**
: Caso de uso que encapsula regra de negócio específica.

**UV**
: Gerenciador de pacotes Python moderno e rápido.

### W

**Webhook**
: Endpoint HTTP que recebe notificações de sistemas externos (Trello, WhatsApp).

**Worker (Celery)**
: Processo que executa tarefas assíncronas da fila.

---

## Acrônimos

| Sigla | Significado                       |
| ----- | --------------------------------- |
| API   | Application Programming Interface |
| CRUD  | Create, Read, Update, Delete      |
| DRF   | Django REST Framework             |
| JWT   | JSON Web Token                    |
| LLM   | Large Language Model              |
| ORM   | Object-Relational Mapping         |
| REST  | Representational State Transfer   |
| UI    | User Interface                    |
| WA    | WhatsApp                          |

---

_Consulte a documentação específica de cada componente para mais detalhes._

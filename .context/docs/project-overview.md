# Visão Geral do Projeto

## Smart Core Assistant Painel

**Plataforma SaaS multi-tenant para atendimento inteligente ao cliente via WhatsApp.**

### Descrição

O Smart Core Assistant Painel é uma solução completa para gerenciamento de atendimentos automatizados e humanos via WhatsApp. A plataforma integra:

- **Motor de IA** com LangChain para análise e geração de respostas
- **Integração WhatsApp** via Evolution API
- **Sincronização de tarefas** com Trello, ClickUp e Notion
- **Multi-tenancy** com isolamento completo por cliente

### Stack Tecnológica

| Camada | Tecnologias |
|--------|-------------|
| Backend | Django 5.2, Django REST Framework, Celery |
| Banco de Dados | PostgreSQL 14 + pgvector |
| IA/NLP | LangChain, OpenAI, Groq, Ollama |
| Cache/Broker | Redis |
| WhatsApp | Evolution API |
| Admin UI | Django Jazzmin |

### Módulos Principais

```
src/smart_core_assistant_painel/
├── app/
│   ├── ui/                    # Apps Django (7 apps de interface)
│   │   ├── core/              # Configurações, middleware, views base
│   │   ├── atendimentos/      # Tickets e mensagens
│   │   ├── operacional/       # Departamentos, fluxos, atendentes
│   │   ├── clientes/          # Contatos e clientes
│   │   ├── usuarios/          # Gerenciamento de usuários
│   │   ├── treinamento/       # Treinamento IA e documentos
│   │   └── oraculo/           # Interface do motor de IA
│   ├── tenants/               # Multi-tenancy
│   ├── evolution_sync/        # Integração WhatsApp
│   ├── trello_sync/           # Sincronização Trello
│   └── settings_manager/      # Configurações remotas
│
└── modules/                   # Lógica de negócio reutilizável
    ├── ai_engine/             # Motor de IA (LangChain)
    ├── services/              # Serviços e adapters
    └── initial_loading/       # Inicialização Firebase
```

---

## Roadmap

### Fase Atual: MVP Consolidado

- [x] Multi-tenancy com isolamento de banco
- [x] Integração Evolution API (WhatsApp)
- [x] Motor de IA com LangChain
- [x] Sincronização Trello
- [x] Admin interface com Jazzmin
- [x] Sistema de permissões baseado em roles

### Próximas Fases

#### Q1 2026 - Expansão de Integrações
- [ ] Integração ClickUp completa
- [ ] Integração Notion completa
- [ ] API pública para integrações externas

#### Q2 2026 - Melhorias de IA
- [ ] RAG com pgvector otimizado
- [ ] Múltiplos modelos de IA simultâneos
- [ ] Dashboard de analytics de atendimentos

#### Q3 2026 - Escalabilidade
- [ ] Arquitetura de microserviços
- [ ] Kubernetes deployment
- [ ] Observabilidade avançada

---

## Stakeholders

### Equipe Técnica

| Papel | Responsabilidades |
|-------|-------------------|
| Backend Developer | Django, APIs, integrações |
| AI/ML Engineer | LangChain, embeddings, prompts |
| DevOps | Infraestrutura, CI/CD, Docker |
| QA | Testes, qualidade de código |

### Negócio

| Papel | Responsabilidades |
|-------|-------------------|
| Product Owner | Roadmap, priorização de features |
| Customer Success | Onboarding de clientes, feedback |
| Suporte | Atendimento a clientes |

---

## Notas de Release

### v0.1.0 (Atual)
- Sistema base de atendimentos
- Integração WhatsApp via Evolution API
- Motor de IA com LangChain
- Sincronização básica com Trello
- Admin interface customizada com Jazzmin

# Cursor Project Rules

## Smart Core Assistant Painel

Plataforma SaaS multi-tenant para atendimento inteligente via WhatsApp.

## Stack

- Django 5.2 + DRF + Celery
- PostgreSQL 14 + pgvector
- LangChain (OpenAI, Groq, Ollama)
- Evolution API (WhatsApp)

## Regras Essenciais

1. **Idioma**: Comunicação em PT-BR, código em inglês
2. **Type hints**: Obrigatórios em todas as funções
3. **Multi-tenancy**: SEMPRE filtrar por tenant
4. **Result pattern**: Usar Success/Failure
5. **Docstrings**: Google style
6. **Commits**: Conventional Commits
7. **Testes**: NÃO criar (agente dedicado)

## Estrutura

```
src/smart_core_assistant_painel/
├── app/ui/           # Apps Django
├── app/tenants/      # Multi-tenancy
├── app/*_sync/       # Integrações
└── modules/          # Lógica de negócio
```

## Comandos

```bash
uv run task start           # Servidor
uv run task lint            # Linting
uv run task type-check      # Types
uv run task test-docker     # Testes
```

## Contexto AI

- Docs: `.context/docs/`
- Agents: `.context/agents/`
- Skills: `.context/skills/`
- Workflow: `.context/workflow/`

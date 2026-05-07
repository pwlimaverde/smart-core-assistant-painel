import os
import re

AGENT_DIR = r"c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\.context\agents"

# Dictionary of specialized responsibilities and files by agent type
AGENT_DETAILS = {
    "ai-specialist": {
        "mission": "Gerenciar o motor de IA do Painel, incluindo LangChain, embeddings, RAG, prompts e a integração com LLMs.",
        "responsibilities": [
            "Configurar e orquestrar modelos utilizando LangChain.",
            "Criar e otimizar prompts com Firebase Remote Config.",
            "Implementar chunking e embeddings (OpenAI, pgvector).",
            "Manter pipelines de análise de mensagens e documentos.",
            "Monitorar custos e timeouts das APIs de LLM."
        ],
        "symbols": ["AnaliseMensageUsecase", "GenerateEmbeddingsUsecase", "Result", "PromptManager", "create_llm"]
    },
    "architect-specialist": {
        "mission": "Projetar a arquitetura macro, definindo padrões para escalabilidade, segurança (multi-tenant) e modularização do código.",
        "responsibilities": [
            "Definir e manter ADRs (Architecture Decision Records).",
            "Assegurar rigor no isolamento Multi-Tenant do Banco de Dados.",
            "Validar fluxos de dados e integrações.",
            "Monitorar a dívida técnica do repositório."
        ],
        "symbols": ["Tenant", "TenantMiddleware", "Result", "ServiceHub"]
    },
    "backend-specialist": {
        "mission": "Projetar e construir APIs no lado do servidor com Django/DRF, focando em performance, segurança e consistência.",
        "responsibilities": [
            "Construir views e controllers, respeitando camadas do Django.",
            "Implementar lógica de negócio separada de infraestrutura.",
            "Configurar rotas, serializers e validações estritas.",
            "Aplicar isolamento restrito de tenant (`user.tenant`)."
        ],
        "symbols": ["BaseTenantConfigView", "AdminStaffRequiredMiddleware"]
    },
    "bug-fixer": {
        "mission": "Sanar falhas em código de produção e ambiente de desenvolvimento utilizando um forte isolamento de causa raiz.",
        "responsibilities": [
            "Realizar análise de logs estruturados e depuração de stack traces.",
            "Formular hipóteses de causa, isolá-las e tratá-las.",
            "NUNCA criar testes durante este step, apenas garantir correção funcional e de arquitetura."
        ],
        "symbols": []
    },
    "code-reviewer": {
        "mission": "Revisar o código de peers visando qualidade do projeto, type hints estruturais, aderência ao DRY e a PEP8.",
        "responsibilities": [
            "Enforçar strict mode do Pyright e tipagem robusta.",
            "Auditar a não-existência de chaves de API secretas e vazamentos.",
            "Exigir conformidade com o padrão `Result` e Docstrings."
        ],
        "symbols": []
    },
    "database-specialist": {
        "mission": "Assegurar o gerenciamento robusto do PostgreSQL pgvector, queries, indexes e modelagem de banco de dados do Django.",
        "responsibilities": [
            "Atimização de ORM Queries, `select_related`, `prefetch_related`.",
            "Geração segura de Migrations e scripts customizados (loaddata).",
            "Proteção estrita dos dados via multi-tenancy."
        ],
        "symbols": ["Tenant", "DocumentoChunk", "Treinamento"]
    },
    "devops-specialist": {
        "mission": "Administrar containers Docker, automação CI/CD, execução de Celery, Redis e configuração do servidor de desenvolvimento.",
        "responsibilities": [
            "Gerenciar Docker Compose file, ambiente e builds.",
            "Orquestrar o setup de Celery workers, beat schedules e integrações Redis.",
            "Monitorar scripts operacionais e task runners (uv)."
        ],
        "symbols": []
    },
    "documentation-writer": {
        "mission": "Produzir, atualizar e padronizar documentação robusta, utilizando estrutura Markdown (MkDocs).",
        "responsibilities": [
            "Garantir a conformidade dos guias, referências Mkdocs, docstrings de função e arquivos README.",
            "Refletir mudanças drásticas de implementação."
        ],
        "symbols": []
    },
    "feature-developer": {
        "mission": "Desdobrar novos épicos e funcionalidades da estrutura, passando pelas camadas de View, Service e Domain.",
        "responsibilities": [
            "Fatiar componentes complexos em modulos e views separadas.",
            "Implementar novas features utilizando os frameworks definidos.",
            "Submeter ao linting (ruff format, check) após o desenvolvimento."
        ],
        "symbols": ["Success", "Failure"]
    },
    "frontend-specialist": {
        "mission": "Implementar templates Django limpos e estéticos, e prover as lógicas da interface e estilos aplicáveis no painel administrativo.",
        "responsibilities": [
            "Criar implementações UI voltadas a UX com Django Templates ou custom forms no Jazzmin.",
            "Gerenciar static assets (css, js) para o Backoffice dashboard."
        ],
        "symbols": ["BackofficeDashboardView"]
    },
    "mobile-specialist": {
        "mission": "Trabalhar em abstrações ou serviços e documentações focados no end-user ou aplicativos móveis periféricos.",
        "responsibilities": [
            "Prestar suporte para APIs compatíveis com Mobile/Webviews.",
            "Monitorar interações assíncronas do backend para UX Mobile."
        ],
        "symbols": []
    },
    "performance-optimizer": {
        "mission": "Atuar na identificação de gargalos de rede, concorrência ou custos de computação local vs remota.",
        "responsibilities": [
            "Refatorar processos síncronos para assíncronos (Celery) na fila de tarefas (ex: Evolution API, LLMs).",
            "Realizar profilling e tuning de performance em Views bloqueantes."
        ],
        "symbols": ["mock_django_q_async_task"]
    },
    "refactoring-specialist": {
        "mission": "Rearranjar sistemas desacoplados, promovendo reuso e isolamento de dependências nos componentes existentes.",
        "responsibilities": [
            "Elevar abstrações na pasta `/domain/` e interfaces.",
            "Otimizar arquivos grandes dividindo os responsabilidades SOLID.",
            "Implementar Factory patterns ou facades (`__init__.py`)."
        ],
        "symbols": []
    },
    "security-auditor": {
        "mission": "Rastrear vazamentos, problemas de autorização e injeções, atuando de fato como controle rígido do OWASP Top 10.",
        "responsibilities": [
            "Proibir vazamento de ENV ou strings expostas.",
            "Blindar endpoints restritos utilizando `AdminStaffRequiredMiddleware`, permissões Custom.",
            "Verificar validações de entradas por Pydantic."
        ],
        "symbols": ["AdminStaffRequiredMiddleware", "TenantMiddleware"]
    },
    "test-writer": {
        "mission": "Providenciar automação de código por meio do pytest ou Django Test Framework, focado em alta assertividade.",
        "responsibilities": [
            "Criar script / classes de Mocks de serviços externos (Firebase, Trello, LLMs).",
            "Escrever casos com `test-docker` para as lógicas de negócio e da suite de aplicações.",
            "A meta aqui exclui foco em mera 'cobertura de linhas', e abraça testes cruciais de segurança."
        ],
        "symbols": ["TestServiceHub"]
    }
}

TEMPLATE = """## Mission
{mission}

O objetivo deste agente é focar exclusivamente nos requisitos de sua especialização, usando Português para comunicação e Inglês para código, sempre se atendo às diretrizes do `AGENTS.md`.

## Responsibilities
{responsibilities}

## Best Practices
- **Clareza e Simplicidade:** Soluções diretas sempre.
- **Isolamento:** Multi-tenant (`user.tenant`) é sagrado.
- **Qualidade de Código:** Usar Type Hints (`pyright`), DOC strings, Padrões em Inglês, result pattern (`Success`/`Failure`).
- **Nenhum Hardcoded Secret:** Sempre referenciar `.env`. Configurações no decouple.

## Key Project Resources
- [Índice de Documentação](../docs/README.md)
- [Regras para Agentes](../../AGENTS.md)
- [Regras do Projeto](../../rules-smart-assistant.md)
- [Workflow PREVC](../workflow/status.yaml)

## Repository Starting Points
- `src/smart_core_assistant_painel/`: Código principal da aplicação.
- `src/smart_core_assistant_painel/app/`: Módulos de aplicação Django e regras.
- `scripts/`: Scripts e utilitários.
- `.context/`: Scaffold e agentes.

## Key Files
- `src/smart_core_assistant_painel/main.py`
- `pyproject.toml`
- `.env.example`

## Key Symbols for This Agent
{symbols}

## Documentation Touchpoints
- [`AGENTS.md`](../../AGENTS.md)
- [`project-overview.md`](../docs/project-overview.md)
- [`architecture.md`](../docs/architecture.md)

## Collaboration Checklist
1. Analisar os requisitos para ambiguidades e levantar perguntas.
2. Planejar execução.
3. Seguir regras em Português estrito nas tasks.
4. Executar garantindo o Linting (`uv run task lint`).
5. Realizar Hand-off para o fluxo seguinte do PREVC.
"""

def generate_agent_content(agent_type):
    data = AGENT_DETAILS.get(agent_type, {
        "mission": "Atuar na resolução e desenvolvimento das tarefas relacionadas a " + agent_type,
        "responsibilities": ["Participar ativamente da etapa associada ao seu profile.", "Seguir PR reviews com base de codebase e arquitetura."],
        "symbols": []
    })
    
    resps = "\n".join([f"- {r}" for r in data["responsibilities"]])
    
    symbs = "\n".join([f"- `{s}`" for s in data["symbols"]]) if data["symbols"] else "- N/A"
    
    return TEMPLATE.format(
        mission=data["mission"],
        responsibilities=resps,
        symbols=symbs
    )

for filename in os.listdir(AGENT_DIR):
    if not filename.endswith(".md"):
        continue
        
    filepath = os.path.join(AGENT_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check if already filled beyond just frontmatter
    # By seeing if there is a '## Mission' or something
    if "## Mission" in content or "## Contexto" in content:
        # ai-specialist might have ## Contexto, we skip if they are already heavily customized
        # but let's check if `status: unfilled` is in the file
        if "status: unfilled" not in content and "status: pending" not in content and "##" in content.split("---")[-1]:
             continue
             
    # Replace frontmatter status: unfilled -> status: active
    content = content.replace("status: unfilled", "status: active")
    content = content.replace("status: pending", "status: active")
    
    # Extract frontmatter
    parts = content.split("---")
    if len(parts) >= 3:
        frontmatter = "---" + parts[1] + "---\n\n"
    else:
        frontmatter = ""
        
    agent_type = filename.replace(".md", "")
    new_body = generate_agent_content(agent_type)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + new_body)

print("Agent files updated successfully.")

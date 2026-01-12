# Ferramentas e Tecnologias

## Stack Principal

### Backend

| Ferramenta            | Versão | Propósito                |
| --------------------- | ------ | ------------------------ |
| Python                | 3.13+  | Linguagem principal      |
| Django                | 5.2    | Framework web            |
| Django REST Framework | 3.15+  | APIs REST                |
| Celery                | latest | Processamento assíncrono |
| PostgreSQL            | 14+    | Banco de dados           |
| Redis                 | < 5.0  | Cache e broker Celery    |
| pgvector              | 0.3+   | Busca vetorial           |

### Inteligência Artificial

| Ferramenta      | Propósito                         |
| --------------- | --------------------------------- |
| LangChain       | Framework de IA                   |
| OpenAI          | LLM principal                     |
| Groq            | LLM alternativo (alta velocidade) |
| Ollama          | LLM local (privacidade)           |
| XAI             | LLM experimental                  |
| HuggingFace Hub | Embeddings e modelos              |
| TikToken        | Tokenização                       |

### Integrações Externas

| Serviço       | Propósito                         |
| ------------- | --------------------------------- |
| Evolution API | WhatsApp Business                 |
| Trello API    | Gestão de cards/boards            |
| ClickUp API   | Gestão de tasks/spaces            |
| Notion API    | Databases e documentação          |
| Firebase      | Autenticação e push notifications |

## Ferramentas de Desenvolvimento

### Gerenciamento de Dependências

```bash
# Instalar uv (gerenciador moderno de pacotes Python)
pip install uv

# Sincronizar dependências
uv sync       # Produção
uv sync --dev # Desenvolvimento
```

### Qualidade de Código

| Ferramenta | Comando                  | Propósito            |
| ---------- | ------------------------ | -------------------- |
| ruff       | `uv run task lint`       | Linting              |
| ruff       | `uv run task format`     | Formatação           |
| pyright    | `uv run task type-check` | Verificação de tipos |

### Configuração Pyright

```toml
# pyproject.toml
[tool.pyright]
typeCheckingMode = "strict"
include = ["src", "tests"]
exclude = ["**/migrations/**"]
```

### Configuração Ruff

```toml
# pyproject.toml
[tool.ruff]
line-length = 79
target-version = "py313"

[tool.ruff.lint]
extend-select = ["I"]  # Ordenação de imports
```

## Documentação

| Ferramenta      | Propósito               |
| --------------- | ----------------------- |
| mkdocs          | Geração de documentação |
| mkdocs-material | Tema moderno            |
| mkdocstrings    | Documentação de código  |

```bash
# Servir documentação localmente
uv run mkdocs serve

# Build para produção
uv run mkdocs build
```

## Logs e Monitoramento

### Loguru

```python
from loguru import logger

# Configuração automática via loguru
logger.add("logs/app.log", rotation="10 MB")
```

### Rich

```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Status")
table.add_column("Serviço")
table.add_column("Status")
console.print(table)
```

## Testes

### Pytest

```bash
# Rodar todos os testes
uv run task test-all

# Testes com cobertura
uv run task test-coverage

# Teste específico
uv run pytest tests/test_file.py -v
```

### Configuração pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = smart_core_assistant_painel.app.ui.core.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Docker

### Stacks de Produção

| Stack   | Serviços             |
| ------- | -------------------- |
| data    | PostgreSQL + Redis   |
| app     | Django + Migrate     |
| workers | Celery Worker + Beat |
| infra   | Cloudflared + Flower |

### Comandos

```bash
# Status remoto
uv run task remote-status

# Logs do app
uv run task remote-logs-app

# Restart workers
uv run task remote-restart-workers
```

---

_Todas as versões são gerenciadas via `pyproject.toml` e `uv.lock`._

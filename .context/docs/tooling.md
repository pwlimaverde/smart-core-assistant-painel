# Ferramentas e Configurações

Este documento descreve as ferramentas de desenvolvimento, scripts e configurações de IDE do projeto.

---

## Gerenciador de Pacotes: uv

O projeto utiliza **uv** como gerenciador de pacotes Python, oferecendo velocidade superior ao pip.

### Comandos Principais

```bash
# Instalar todas as dependências
uv sync

# Adicionar dependência
uv add <pacote>

# Adicionar dependência de desenvolvimento
uv add --dev <pacote>

# Atualizar dependências
uv lock --upgrade
uv sync
```

### Arquivo de Configuração

```toml
# pyproject.toml
[project]
name = "smart-core-assistant-painel"
version = "0.1.0"
requires-python = ">=3.13"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-django>=4.8",
    "ruff>=0.8",
    "pyright>=1.1",
]
```

---

## Automação de Tarefas: Taskipy

Taskipy gerencia scripts de execução via `uv run task <nome>`.

### Tarefas Disponíveis

```toml
# pyproject.toml
[tool.taskipy.tasks]
# Servidor
start = "python src/smart_core_assistant_painel/app/manage.py runserver 0.0.0.0:8000"
celery-worker = "celery -A app.core worker -l info"
celery-beat = "celery -A app.core beat -l info"

# Banco de dados
makemigrations = "python src/smart_core_assistant_painel/app/manage.py makemigrations"
migrate = "python src/smart_core_assistant_painel/app/manage.py migrate"

# Qualidade
lint = "ruff check src tests"
format = "ruff format src tests"
type-check = "pyright src"

# Testes
test-docker = "docker compose -f docker/compose/test/docker-compose.yml run --rm test"
test = "pytest tests/"
```

---

## Linting: Ruff

**Ruff** é utilizado para linting e formatação de código.

### Configuração

```toml
# pyproject.toml
[tool.ruff]
line-length = 79
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]
ignore = [
    "E501",   # line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Comandos

```bash
# Verificar erros
uv run task lint

# Corrigir automaticamente
uv run ruff check --fix src tests

# Formatar código
uv run task format
```

---

## Type Checking: Pyright

**Pyright** em modo estrito verifica type hints.

### Configuração

```toml
# pyproject.toml
[tool.pyright]
include = ["src"]
exclude = ["**/__pycache__", "**/migrations"]
pythonVersion = "3.13"
typeCheckingMode = "strict"
reportMissingTypeStubs = false
reportUnknownMemberType = false
```

### Comandos

```bash
# Verificar tipos
uv run task type-check

# Com output verboso
uv run pyright src --verbose
```

---

## Testes: Pytest

### Configuração

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = app.core.settings_test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### Plugins Instalados

| Plugin | Função |
|--------|--------|
| pytest-django | Integração Django |
| pytest-cov | Cobertura de código |
| pytest-asyncio | Testes assíncronos |
| pytest-mock | Mocking facilitado |

---

## Docker

### Estrutura

```
docker/
├── compose/
│   ├── data-stack/           # PostgreSQL + Redis
│   │   └── docker-compose.yml
│   ├── app-stack/            # Django app
│   │   └── docker-compose.yml
│   ├── test/                 # Ambiente de testes
│   │   └── docker-compose.yml
│   └── workers-stack/        # Celery workers
│       └── docker-compose.yml
│
└── Dockerfile                # Imagem principal
```

### Comandos Úteis

```bash
# Iniciar infraestrutura (PostgreSQL + Redis)
docker compose -f docker/compose/data-stack/docker-compose.yml up -d

# Executar testes
uv run task test-docker

# Parar todos os containers
docker compose -f docker/compose/data-stack/docker-compose.yml down
```

---

## IDEs Suportadas

### VS Code

Extensões recomendadas:

| Extensão | Função |
|----------|--------|
| Python | Suporte Python |
| Pylance | Language server |
| Ruff | Linting inline |
| Django | Syntax highlighting |
| GitLens | Git integrado |

Configurações (`.vscode/settings.json`):

```json
{
    "python.defaultInterpreterPath": ".venv/Scripts/python",
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "python.analysis.typeCheckingMode": "strict"
}
```

### Zed

Configurações (`.zed/settings.json`):

```json
{
    "languages": {
        "Python": {
            "language_servers": ["pyright", "ruff"]
        }
    }
}
```

### PyCharm

- Use o interpretador do `.venv`
- Configure Django support
- Enable type checking

---

## Scripts de Automação

### Diretório scripts/

```
scripts/
├── automacao/
│   └── new_feature_script.py     # Gera estrutura de nova feature
│
├── config_global/                # Configurações globais
│
├── docker_remoto/                # Gerenciamento Docker remoto
│   └── manager.py
│
└── temp/                         # Scripts temporários
```

### Gerador de Features

```bash
# Criar nova feature de AI Engine
python scripts/automacao/new_feature_script.py --name analise_sentimento --module ai_engine
```

Isso cria:
```
modules/ai_engine/features/analise_sentimento/
├── __init__.py
├── datasource/
│   └── __init__.py
└── domain/
    ├── __init__.py
    ├── model/
    │   └── __init__.py
    └── usecase/
        └── __init__.py
```

---

## Documentação: MkDocs

### Configuração

```yaml
# mkdocs.yml
site_name: Smart Core Assistant
theme:
  name: material

nav:
  - Home: index.md
  - API:
    - AI Engine: api/ai_engine.md
    - Services: api/services_facade.md
```

### Comandos

```bash
# Servir documentação localmente
mkdocs serve

# Build para produção
mkdocs build
```

---

## Git Hooks

### Pre-commit (Recomendado)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff-lint
        name: ruff lint
        entry: uv run ruff check
        language: system
        types: [python]

      - id: ruff-format
        name: ruff format
        entry: uv run ruff format --check
        language: system
        types: [python]

      - id: pyright
        name: pyright
        entry: uv run pyright
        language: system
        types: [python]
```

### Instalação

```bash
pip install pre-commit
pre-commit install
```

---

## Variáveis de Ambiente

### Template (.env.example)

```bash
# Django
SECRET_KEY=generate-a-secure-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:pass@localhost:5432/smartcore

# Redis
REDIS_URL=redis://localhost:6379/0

# Evolution API
EVOLUTION_API_URL=https://api.evolution.com
EVOLUTION_API_KEY=your-api-key

# LLM Providers
OPENAI_API_KEY=sk-xxx
GROQ_API_KEY=gsk_xxx

# Firebase
FIREBASE_CREDENTIALS_PATH=./firebase_key.json
```

---

## Debugging

### Scripts de Debug (teste_debug/)

```
teste_debug/
├── check_env.py              # Verifica variáveis de ambiente
├── reproduce_bug.py          # Reproduz bugs específicos
├── test_flow_simulation.py   # Simula fluxos
└── verify_*.py               # Scripts de verificação
```

### Uso

```bash
# Verificar ambiente
python teste_debug/check_env.py

# Simular fluxo de atendimento
python teste_debug/test_flow_simulation.py
```

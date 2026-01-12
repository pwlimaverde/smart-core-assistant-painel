# Fluxo de Desenvolvimento

## Visão Geral

Este documento descreve o processo de desenvolvimento do Smart Core Assistant Painel, incluindo configuração de ambiente, comandos disponíveis e boas práticas.

## Configuração do Ambiente

### Pré-requisitos

- Python 3.13+
- Docker e Docker Compose
- Git
- Windows (ambiente primário)

### Instalação Inicial

```bash
# 1. Clonar o repositório
git clone <repo-url>
cd smart-core-assistant-painel

# 2. Copiar configurações
cp .env.example .env
# Edite o .env com suas credenciais

# 3. Instalar dependências
uv sync --dev

# 4. Iniciar containers Docker (dados)
cd ambiente_base_dados
.\setup.bat  # Windows

# 5. Aplicar migrações
uv run task migrate

# 6. Criar superusuário
uv run task createsuperuser
```

## Comandos Taskipy

### Servidor e Desenvolvimento

| Comando                 | Descrição                                           |
| ----------------------- | --------------------------------------------------- |
| `uv run task start`     | Inicia o servidor Django (porta 8000)               |
| `uv run task start-all` | Inicia servidor + Celery + ngrok (Windows Terminal) |
| `uv run task shell`     | Abre o shell Django                                 |

### Celery (Processamento Assíncrono)

| Comando                     | Descrição               |
| --------------------------- | ----------------------- |
| `uv run task celery-worker` | Inicia worker Celery    |
| `uv run task celery-beat`   | Inicia scheduler Celery |

### Qualidade de Código

| Comando                  | Descrição                            |
| ------------------------ | ------------------------------------ |
| `uv run task lint`       | Verifica código com ruff             |
| `uv run task format`     | Formata código com ruff              |
| `uv run task type-check` | Verifica tipos com pyright (estrito) |

### Testes

| Comando                 | Descrição                        |
| ----------------------- | -------------------------------- |
| `uv run task test`      | Roda testes de lógica de negócio |
| `uv run task test-apps` | Roda testes das apps Django      |
| `uv run task test-all`  | Roda todos os testes             |

### Django Management

| Comando                      | Descrição                 |
| ---------------------------- | ------------------------- |
| `uv run task makemigrations` | Cria arquivos de migração |
| `uv run task migrate`        | Aplica migrações locais   |
| `uv run task collectstatic`  | Coleta arquivos estáticos |

### Docker Remoto (Produção)

| Comando                        | Descrição                     |
| ------------------------------ | ----------------------------- |
| `uv run task remote-status`    | Status de todos os containers |
| `uv run task remote-start-all` | Inicia todos os stacks        |
| `uv run task remote-stop-all`  | Para todos os stacks          |
| `uv run task remote-logs-app`  | Visualiza logs do Django      |

## Fluxo de Trabalho Git

### Branches (GitFlow)

| Prefixo    | Uso                            |
| ---------- | ------------------------------ |
| `feature/` | Novas funcionalidades          |
| `bugfix/`  | Correções no desenvolvimento   |
| `hotfix/`  | Correções urgentes em produção |
| `release/` | Preparação de nova versão      |

### Commits (Conventional Commits)

```
feat: adiciona integração com ClickUp
fix: corrige encoding UTF-8 no webhook
docs: atualiza README com instruções Docker
refactor: extrai lógica para serviço dedicado
chore: atualiza dependências
```

## Pre-Commit Hooks

O projeto utiliza pre-commit para garantir qualidade:

```bash
# Instalar hooks
pre-commit install

# Rodar manualmente
pre-commit run --all-files
```

## Ciclo de Desenvolvimento

```
1. Criar branch feature/xxx
        │
        ▼
2. Desenvolver funcionalidade
        │
        ▼
3. Rodar lint + format + type-check
        │
        ▼
4. Commit com Conventional Commits
        │
        ▼
5. Push e criar PR
        │
        ▼
6. Revisão + Merge para dev
        │
        ▼
7. Deploy em staging/produção
```

## Debugging

### Logs

```python
from loguru import logger

logger.info("Mensagem informativa")
logger.error("Erro: {}", exception)
logger.debug("Debug: {}", data)
```

### Scripts de Debug

Para testes pontuais, use o diretório `teste_debug/`:

```bash
# Exemplo: testar fluxo de simulação
python teste_debug/test_flow_simulation.py
```

---

_Siga sempre as convenções definidas em `.agent/rules/` para manter consistência._

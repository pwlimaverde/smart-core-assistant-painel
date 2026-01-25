# Workflow de Desenvolvimento

## Gerenciador de Pacotes

O projeto utiliza **uv** como gerenciador de pacotes e **taskipy** para automação de tarefas.

```bash
# Instalar dependências
uv sync

# Executar comandos via taskipy
uv run task <nome_do_task>
```

---

## Comandos Disponíveis

### Servidor e Serviços

| Comando | Descrição |
|---------|-----------|
| `uv run task start` | Inicia servidor Django (0.0.0.0:8000) |
| `uv run task celery-worker` | Inicia worker Celery |
| `uv run task celery-beat` | Inicia agendador Celery beat |
| `uv run task start-all` | Inicia todos os serviços |

### Banco de Dados

| Comando | Descrição |
|---------|-----------|
| `uv run task makemigrations` | Cria migrações Django |
| `uv run task migrate` | Aplica migrações locais |
| `uv run task migrate-remoto` | Aplica migrações no PostgreSQL remoto |
| `uv run task createsuperuser` | Cria superusuário Django |

### Qualidade de Código

| Comando | Descrição |
|---------|-----------|
| `uv run task lint` | Executa linter ruff |
| `uv run task format` | Formata código com ruff |
| `uv run task type-check` | Executa pyright (modo estrito) |

### Testes

| Comando | Descrição |
|---------|-----------|
| `uv run task test-docker` | **PREFERIDO** - Executa testes no Docker |
| `uv run task test` | Executa apenas diretório tests/ |
| `uv run task test-apps` | Executa apenas testes de apps Django |
| `uv run task test-all` | Executa todos os testes localmente |

Para executar um teste específico:
```bash
uv run task test-docker -- -k "nome_do_teste"
```

---

## Branching Strategy (GitFlow)

### Branches Principais

| Branch | Propósito |
|--------|-----------|
| `master` | Código em produção |
| `develop` | Integração de features (quando aplicável) |

### Branches de Trabalho

| Prefixo | Uso |
|---------|-----|
| `feature/` | Novas funcionalidades |
| `bugfix/` | Correções de bugs em desenvolvimento |
| `hotfix/` | Correções urgentes em produção |
| `release/` | Preparação de versão |
| `refactor/` | Refatorações de código |

### Exemplos

```bash
# Nova feature
git checkout -b feature/add-notion-sync

# Correção de bug
git checkout -b bugfix/fix-message-parsing

# Hotfix em produção
git checkout -b hotfix/critical-auth-issue

# Refatoração
git checkout -b refactor/ui-design-system
```

---

## Conventional Commits

Todos os commits devem seguir o padrão Conventional Commits:

### Tipos de Commit

| Tipo | Descrição |
|------|-----------|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `docs:` | Alterações em documentação |
| `style:` | Formatação (sem alteração de lógica) |
| `refactor:` | Refatoração de código |
| `test:` | Adição/modificação de testes |
| `chore:` | Tarefas de manutenção |
| `perf:` | Melhorias de performance |
| `ci:` | Alterações de CI/CD |

### Exemplos

```bash
# Feature
git commit -m "feat: add Notion integration adapter"

# Bug fix
git commit -m "fix: resolve message parsing error for media files"

# Documentation
git commit -m "docs: update API documentation for webhooks"

# Refactoring
git commit -m "refactor: extract message processing to service layer"
```

### Escopo (Opcional)

```bash
git commit -m "feat(evolution_sync): add support for audio messages"
git commit -m "fix(trello_sync): handle rate limiting errors"
```

---

## CI/CD Pipeline

### Verificações Automáticas

1. **Linting** (ruff)
   - Verifica estilo de código
   - Detecta problemas comuns

2. **Type Checking** (pyright)
   - Modo estrito habilitado
   - Todas as funções devem ter type hints

3. **Testes** (pytest)
   - Execução em container Docker
   - Cobertura de código reportada

### Comandos de Verificação Local

```bash
# Executar todas as verificações antes do commit
uv run task lint && uv run task type-check && uv run task test-docker
```

---

## Pull Request Guidelines

### Checklist

- [ ] Código segue padrões do projeto
- [ ] Type hints adicionados em todas as funções
- [ ] Linting passa sem erros
- [ ] Testes passam
- [ ] Documentação atualizada (se necessário)
- [ ] Commit messages seguem Conventional Commits

### Template de PR

```markdown
## Descrição
[Breve descrição das mudanças]

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova feature
- [ ] Breaking change
- [ ] Refatoração

## Como Testar
[Passos para testar as mudanças]

## Checklist
- [ ] Código revisado
- [ ] Testes passando
- [ ] Documentação atualizada
```

---

## Ambiente de Desenvolvimento

### Pré-requisitos

- Python 3.13+
- uv (gerenciador de pacotes)
- Docker e Docker Compose
- PostgreSQL 14+ (ou via Docker)
- Redis (ou via Docker)

### Setup Inicial

```bash
# 1. Clonar repositório
git clone <repo-url>
cd smart-core-assistant-painel

# 2. Instalar dependências
uv sync

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 4. Iniciar serviços de infraestrutura
docker-compose -f docker/compose/data-stack/docker-compose.yml up -d

# 5. Aplicar migrações
uv run task migrate

# 6. Criar superusuário
uv run task createsuperuser

# 7. Iniciar servidor
uv run task start
```

### IDEs Recomendadas

- **VS Code** com extensões:
  - Python
  - Pylance
  - Ruff

- **PyCharm Professional**
  - Suporte Django integrado

### Configuração de IDE

Configurações já incluídas:
- `.vscode/settings.json` (se existir)
- `.zed/settings.json`
- `pyrightconfig.json` (implícito no pyproject.toml)

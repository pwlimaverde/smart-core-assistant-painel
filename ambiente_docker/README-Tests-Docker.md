# Testes no Ambiente Docker

## Abordagem Simplificada

Este projeto utiliza uma abordagem simplificada para execução de testes no Docker, aproveitando o container `django-app` existente em vez de criar um container separado para testes.

## Comandos Disponíveis

### Executar Todos os Testes
```bash
# Via taskipy
uv run task test-docker

# Comando direto
docker compose exec django-app uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

### Executar Testes Específicos
```bash
# Via taskipy
uv run task test-docker-specific tests/modules/oraculo/

# Comando direto
docker compose exec django-app uv run pytest tests/modules/oraculo/ -v
```

### Executar com Relatório de Cobertura HTML
```bash
# Via taskipy
uv run task test-docker-coverage

# Comando direto
docker compose exec django-app uv run pytest tests/ -v --cov=src --cov-report=html
```

## Pré-requisitos

1. **Container Django em execução**:
   ```bash
   docker compose up -d django-app
   ```

2. **Banco de dados ativo**:
   ```bash
   docker compose up -d postgres-django
   ```

## Configuração de Teste

### Arquivo conftest.py
O arquivo `tests/conftest.py` contém as configurações necessárias para os testes, incluindo:
- Configuração do Django
- Configuração do banco de dados de teste
- Fixtures compartilhadas

### Estrutura de Testes
```
tests/
├── __init__.py
├── conftest.py
└── modules/
    ├── __init__.py
    └── oraculo/
        ├── __init__.py
        ├── test_models.py
        ├── test_views.py
        └── test_utils.py
```

## Vantagens da Abordagem Simplificada

1. **Menos Complexidade**: Usa o container existente em vez de criar um novo
2. **Configuração Única**: Não duplica configurações Docker
3. **Desenvolvimento Ágil**: Testes executam no mesmo ambiente da aplicação
4. **Menos Recursos**: Não consome recursos adicionais com containers separados
5. **Manutenção Simples**: Menos arquivos de configuração para manter

## Comandos de Qualidade de Código

### Linting
```bash
uv run task lint-docker
# ou
docker compose exec django-app uv run ruff check src/
```

### Formatação
```bash
uv run task format-docker
# ou
docker compose exec django-app uv run ruff format src/
```

### Verificação de Tipos
```bash
uv run task type-check-docker
# ou
docker compose exec django-app uv run mypy src/
```

## Solução de Problemas

### Container não está em execução
```bash
docker compose up -d django-app
```

### Problemas de banco de dados
```bash
# Reiniciar banco
docker compose restart postgres-django

# Executar migrações
docker compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate
```

### Limpar cache de testes
```bash
docker compose exec django-app find . -name "*.pyc" -delete
docker compose exec django-app find . -name "__pycache__" -type d -exec rm -rf {} +
```

## Boas Práticas

1. **Execute testes antes de commits**:
   ```bash
   uv run task test-docker
   ```

2. **Mantenha cobertura mínima de 80%**:
   ```bash
   uv run task test-docker-coverage
   ```

3. **Use testes específicos durante desenvolvimento**:
   ```bash
   docker compose exec django-app uv run pytest tests/modules/oraculo/test_models.py::TestTreinamentos::test_create -v
   ```

4. **Verifique qualidade do código**:
   ```bash
   uv run task lint-docker
   uv run task format-docker
   uv run task type-check-docker
   ```
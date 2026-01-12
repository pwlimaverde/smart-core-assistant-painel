# Estratégia de Testes

## Visão Geral

Este documento descreve a estratégia de testes do Smart Core Assistant Painel.

> [!IMPORTANT]
> A criação e manutenção de testes automatizados é **responsabilidade exclusiva de um agente dedicado a testes**. Desenvolvedores NÃO devem criar ou modificar testes de cobertura.

## Estrutura de Testes

```
tests/                              # Testes de lógica de negócio
├── modules/
│   └── services/
│       └── features/               # Testes por feature
│           ├── analise_avaliacao/
│           ├── analise_conteudo/
│           └── unified_data_services/
├── conftest.py                     # Fixtures globais
└── verify_payment_logic.py         # Scripts de verificação

src/.../app/.../tests/              # Testes de apps Django
```

## Comandos de Teste

| Comando                     | Descrição                            |
| --------------------------- | ------------------------------------ |
| `uv run task test`          | Testes de lógica de negócio (tests/) |
| `uv run task test-apps`     | Testes de apps Django (src/)         |
| `uv run task test-all`      | Todos os testes                      |
| `uv run task test-coverage` | Gera relatório HTML de cobertura     |

### Executar Teste Específico

```bash
# Por nome
uv run pytest tests/ -k "test_nome_especifico" -v

# Por arquivo
uv run pytest tests/modules/services/test_arquivo.py -v
```

## Framework e Configuração

### pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = smart_core_assistant_painel.app.ui.core.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Fixtures Principais

```python
# tests/conftest.py

@pytest.fixture
def mock_clickup_department_provision():
    """Mock para provisionamento ClickUp."""
    pass

@pytest.fixture
def mock_django_q_async_task():
    """Mock para tarefas assíncronas."""
    pass
```

## Padrões de Teste

### Nomenclatura

```python
class TestAnaliseMensageUsecase:
    def test_should_classify_greeting_message(self):
        """Deve classificar mensagem de saudação."""
        pass

    def test_should_return_error_for_empty_input(self):
        """Deve retornar erro para entrada vazia."""
        pass
```

### Estrutura AAA

```python
def test_example():
    # Arrange (Preparar)
    input_data = create_input()

    # Act (Agir)
    result = usecase.execute(input_data)

    # Assert (Verificar)
    assert result.is_success()
```

## Scripts de Debug

Para testes pontuais durante desenvolvimento, use `teste_debug/`:

```bash
# Testar fluxo específico
python teste_debug/test_flow_simulation.py

# Verificar conexões
python teste_debug/check_treinamento_celery.py
```

> [!WARNING]
> Scripts em `teste_debug/` são para investigação temporária e NÃO fazem parte da suite de testes automatizados.

## Ambiente de Testes

### Variáveis de Ambiente

```env
# pytest-env configura automaticamente:
DJANGO_SETTINGS_MODULE=smart_core_assistant_painel.app.ui.core.settings
DATABASE_URL=postgresql://test:test@localhost:5432/test_db
```

### Banco de Dados de Teste

O pytest-django cria automaticamente um banco de dados de teste isolado.

---

_A cobertura de código é monitorada automaticamente pelo CI/CD._

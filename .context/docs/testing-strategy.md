# Estratégia de Testes

## Visão Geral

O projeto utiliza **pytest** com **pytest-django** para testes. A execução preferencial é via Docker para garantir ambiente consistente.

---

## Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py                 # Fixtures globais
│
├── app/                        # Testes de apps Django
│   ├── ui/
│   │   ├── atendimentos/
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── services/
│   │   │       └── test_*.py
│   │   ├── clientes/
│   │   ├── operacional/
│   │   ├── treinamento/
│   │   └── usuarios/
│   │
│   └── evolution_sync/
│       ├── test_views.py
│       ├── test_signals.py
│       ├── domain/
│       └── services/
│
└── modules/                    # Testes de módulos
    ├── ai_engine/
    │   └── features/
    │       ├── analise_conteudo/
    │       ├── analise_previa_mensagem/
    │       ├── load_document_file/
    │       └── load_mensage_data/
    │
    └── services/
```

---

## Comandos de Teste

### Execução Principal (Recomendado)

```bash
# Executa todos os testes em Docker
uv run task test-docker
```

### Execução Local

```bash
# Apenas diretório tests/
uv run task test

# Apenas testes de apps Django
uv run task test-apps

# Todos os testes localmente
uv run task test-all
```

### Testes Específicos

```bash
# Por nome
uv run task test-docker -- -k "test_create_atendimento"

# Por arquivo
uv run task test-docker -- tests/app/ui/atendimentos/test_models.py

# Por diretório
uv run task test-docker -- tests/app/evolution_sync/
```

### Com Cobertura

```bash
# Gerar relatório de cobertura
uv run task test-docker -- --cov=src --cov-report=html
```

---

## Fixtures Principais

### conftest.py

```python
# tests/conftest.py

import pytest
from django.contrib.auth import get_user_model

@pytest.fixture
def user(db):
    """Cria usuário para testes."""
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )

@pytest.fixture
def authenticated_client(client, user):
    """Cliente Django autenticado."""
    client.force_login(user)
    return client

@pytest.fixture
def tenant(db):
    """Cria tenant para testes."""
    from app.tenants.models import Tenant
    return Tenant.objects.create(
        nome="Test Tenant",
        database="test_db"
    )
```

### Fixtures por App

Cada app pode ter seu próprio `conftest.py` com fixtures específicas:

```python
# tests/app/ui/atendimentos/conftest.py

@pytest.fixture
def atendimento(db, cliente, departamento):
    """Cria atendimento para testes."""
    from app.ui.atendimentos.models import Atendimento
    return Atendimento.objects.create(
        cliente=cliente,
        departamento=departamento,
        status="aberto"
    )
```

---

## Tipos de Teste

### 1. Testes Unitários

Testam funções/métodos isoladamente.

```python
# tests/modules/ai_engine/features/test_analise.py

def test_analise_mensagem_valida():
    """Testa análise de mensagem válida."""
    result = analise_mensagem("Olá, preciso de ajuda")
    assert result.is_success()
    assert result.value.intent is not None
```

### 2. Testes de Integração

Testam interação entre componentes.

```python
# tests/app/evolution_sync/test_webhook.py

@pytest.mark.django_db
def test_webhook_creates_atendimento(client, tenant):
    """Testa que webhook cria atendimento."""
    payload = {
        "event": "messages.upsert",
        "data": {...}
    }
    response = client.post("/webhook/evolution/", payload, format="json")
    assert response.status_code == 200
    assert Atendimento.objects.count() == 1
```

### 3. Testes de Model

Testam models Django.

```python
# tests/app/ui/atendimentos/test_models.py

@pytest.mark.django_db
class TestAtendimentoModel:
    def test_create_atendimento(self, cliente, departamento):
        """Testa criação de atendimento."""
        atendimento = Atendimento.objects.create(
            cliente=cliente,
            departamento=departamento
        )
        assert atendimento.status == "aberto"
        assert atendimento.pk is not None

    def test_atendimento_str(self, atendimento):
        """Testa representação string."""
        assert str(atendimento) == f"Atendimento #{atendimento.pk}"
```

### 4. Testes de View

Testam endpoints HTTP.

```python
# tests/app/ui/clientes/test_views.py

@pytest.mark.django_db
class TestClienteViews:
    def test_list_clientes(self, authenticated_client):
        """Testa listagem de clientes."""
        response = authenticated_client.get("/clientes/")
        assert response.status_code == 200

    def test_create_cliente(self, authenticated_client):
        """Testa criação de cliente."""
        data = {"nome": "Novo Cliente", "telefone": "11999999999"}
        response = authenticated_client.post("/clientes/", data)
        assert response.status_code == 302  # Redirect after create
```

---

## Configuração pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = app.ui.core.settings_test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks integration tests
```

---

## Mocks e Patches

### Mockando Serviços Externos

```python
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
@patch("app.evolution_sync.services.evolution_api.EvolutionAPI.send_message")
def test_send_message(mock_send, atendimento):
    """Testa envio de mensagem mockando API externa."""
    mock_send.return_value = {"status": "sent"}

    result = send_response_to_client(atendimento, "Olá!")

    mock_send.assert_called_once()
    assert result.is_success()
```

### Mockando LangChain

```python
@patch("modules.ai_engine.features.analise_mensage.domain.usecase.llm")
def test_analise_com_mock_llm(mock_llm):
    """Testa análise mockando LLM."""
    mock_llm.invoke.return_value = "Intent: saudacao"

    result = analise_mensagem("Olá")

    assert result.value.intent == "saudacao"
```

---

## Política de Testes

### O que Testar

- **Models**: Validações, métodos custom, signals
- **Views**: Endpoints críticos, permissões
- **Services**: Lógica de negócio principal
- **Usecases**: Casos de uso de módulos

### O que NÃO Testar

- Admin interface (testada indiretamente)
- Migrações Django
- Código de terceiros

### Cobertura Mínima

- **Crítico (>80%)**: Services, Usecases
- **Importante (>60%)**: Models, Views
- **Opcional**: Forms, Serializers

---

## Debug de Testes

### Scripts de Debug

Diretório `teste_debug/` contém scripts para reprodução manual:

```bash
# Reproduzir bug específico
python teste_debug/reproduce_bug.py

# Testar fluxo específico
python teste_debug/test_flow_simulation.py
```

### Logs em Testes

```python
import logging

logger = logging.getLogger(__name__)

def test_with_logging(caplog):
    with caplog.at_level(logging.DEBUG):
        result = some_function()
        assert "expected log" in caplog.text
```

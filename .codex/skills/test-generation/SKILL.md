---
name: test-generation
description: Gera casos de teste automatizados
phases: [E, V]
---

# Test Generation Skill

## Quando Usar

Use este skill quando:
- Criando testes para código novo
- Adicionando testes para código existente
- Melhorando cobertura de testes

## Instruções

### 1. Análise do Código

Antes de gerar testes, analise:
- Quais são os inputs possíveis?
- Quais são os outputs esperados?
- Quais são os casos de borda?
- Quais dependências precisam ser mockadas?

### 2. Estrutura de Teste

```python
# tests/app/<app>/test_<module>.py

import pytest
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestNomeDaClasse:
    """Testes para NomeDaClasse."""

    @pytest.fixture
    def setup_data(self, db):
        """Prepara dados para testes."""
        return create_test_data()

    def test_caso_sucesso(self, setup_data):
        """Deve [comportamento esperado] quando [condição]."""
        # Arrange
        input_data = {...}

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result.is_success()
        assert result.value == expected

    def test_caso_falha(self):
        """Deve [comportamento esperado] quando [condição de falha]."""
        # Arrange
        invalid_input = {...}

        # Act
        result = function_under_test(invalid_input)

        # Assert
        assert result.is_failure()
        assert "mensagem" in str(result.error)
```

### 3. Tipos de Teste

#### Teste de Model
```python
@pytest.mark.django_db
class TestAtendimentoModel:
    def test_create_atendimento(self, cliente, departamento):
        """Deve criar atendimento com status padrão."""
        atendimento = Atendimento.objects.create(
            cliente=cliente,
            departamento=departamento,
        )
        assert atendimento.pk is not None
        assert atendimento.status == "aberto"

    def test_str_representation(self, atendimento):
        """Deve retornar representação string correta."""
        assert str(atendimento) == f"Atendimento #{atendimento.pk}"
```

#### Teste de View
```python
@pytest.mark.django_db
class TestAtendimentoViews:
    def test_list_authenticated(self, authenticated_client):
        """Usuário autenticado deve ver lista."""
        response = authenticated_client.get("/atendimentos/")
        assert response.status_code == 200

    def test_list_unauthenticated(self, client):
        """Usuário não autenticado deve ser redirecionado."""
        response = client.get("/atendimentos/")
        assert response.status_code == 302
```

#### Teste de API
```python
@pytest.mark.django_db
class TestAtendimentoAPI:
    def test_create_via_api(self, api_client, cliente):
        """Deve criar atendimento via API."""
        response = api_client.post("/api/atendimentos/", {
            "cliente": cliente.pk,
        })
        assert response.status_code == 201
```

#### Teste de Usecase
```python
class TestAnaliseMensageUsecase:
    def test_execute_success(self, mock_llm):
        """Deve analisar mensagem com sucesso."""
        usecase = AnaliseMensageUsecase(mock_llm)
        result = usecase.execute("Olá")
        assert result.is_success()

    def test_execute_empty_message(self):
        """Deve falhar com mensagem vazia."""
        usecase = AnaliseMensageUsecase(Mock())
        result = usecase.execute("")
        assert result.is_failure()
```

### 4. Mocking

```python
from unittest.mock import Mock, patch

# Mock de serviço externo
@patch("app.evolution_sync.services.evolution_api.send_message")
def test_send_message(mock_send):
    mock_send.return_value = {"status": "sent"}
    result = send_to_client("Olá")
    mock_send.assert_called_once()

# Mock de LLM
def test_with_mock_llm():
    mock_llm = Mock()
    mock_llm.invoke.return_value = "Resposta"
    usecase = Usecase(mock_llm)
    result = usecase.execute("input")
```

### 5. Fixtures

```python
# conftest.py

@pytest.fixture
def user(db):
    return User.objects.create_user(username="test", password="test")

@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client
```

### 6. Casos a Cobrir

- [ ] Caso de sucesso (happy path)
- [ ] Inputs inválidos
- [ ] Inputs vazios/nulos
- [ ] Casos de borda
- [ ] Erros de dependências externas
- [ ] Permissões/autorização
- [ ] Multi-tenancy

## Comandos

```bash
# Executar todos os testes
uv run task test-docker

# Teste específico
uv run task test-docker -- -k "test_create"

# Com cobertura
uv run task test-docker -- --cov=src --cov-report=html
```
# Test Writer

## Contexto

O Test Writer é responsável por criar testes automatizados para o Smart Core Assistant Painel. Este agente desenvolve testes unitários, de integração e de comportamento seguindo as melhores práticas.

---

## Habilidades

- Pytest e pytest-django
- Testes unitários e de integração
- Mocking e patching
- Fixtures reutilizáveis
- Cobertura de código
- Test-Driven Development (TDD)

---

## Stack de Testes

| Ferramenta | Uso |
|------------|-----|
| pytest | Framework de testes |
| pytest-django | Integração Django |
| pytest-cov | Cobertura de código |
| pytest-mock | Mocking facilitado |
| factory_boy | Factories para models |

---

## Estrutura de Testes

```
tests/
├── conftest.py                 # Fixtures globais
├── factories.py                # Factories compartilhadas
│
├── app/
│   ├── ui/
│   │   ├── atendimentos/
│   │   │   ├── conftest.py     # Fixtures específicas
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── services/
│   │   │       └── test_orchestrator.py
│   │   └── ...
│   │
│   └── evolution_sync/
│       ├── test_views.py
│       └── test_signals.py
│
└── modules/
    └── ai_engine/
        └── features/
            └── analise_mensage/
                └── test_usecase.py
```

---

## Padrões de Teste

### Teste de Model

```python
# tests/app/atendimentos/test_models.py

import pytest
from django.utils import timezone

from app.atendimentos.models import Atendimento, Mensagem


@pytest.mark.django_db
class TestAtendimentoModel:
    """Testes para o model Atendimento."""

    def test_create_atendimento(self, cliente, departamento):
        """Deve criar atendimento com status padrão."""
        atendimento = Atendimento.objects.create(
            cliente=cliente,
            departamento=departamento,
        )

        assert atendimento.pk is not None
        assert atendimento.status == "aberto"
        assert atendimento.created_at is not None

    def test_atendimento_str(self, atendimento):
        """Deve retornar representação string correta."""
        expected = f"Atendimento #{atendimento.pk}"
        assert str(atendimento) == expected

    def test_atendimento_mensagens_count(self, atendimento):
        """Deve contar mensagens corretamente."""
        Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Mensagem 1",
            direcao="entrada",
        )
        Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Mensagem 2",
            direcao="saida",
        )

        assert atendimento.mensagens.count() == 2
```

### Teste de View

```python
# tests/app/atendimentos/test_views.py

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAtendimentoViews:
    """Testes para views de Atendimento."""

    def test_list_atendimentos_authenticated(self, authenticated_client):
        """Usuário autenticado deve ver lista."""
        url = reverse("atendimento_list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "atendimentos" in response.context

    def test_list_atendimentos_unauthenticated(self, client):
        """Usuário não autenticado deve ser redirecionado."""
        url = reverse("atendimento_list")
        response = client.get(url)

        assert response.status_code == 302
        assert "/login/" in response.url

    def test_create_atendimento(self, authenticated_client, cliente, departamento):
        """Deve criar atendimento via POST."""
        url = reverse("atendimento_create")
        data = {
            "cliente": cliente.pk,
            "departamento": departamento.pk,
            "assunto": "Teste",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert Atendimento.objects.filter(assunto="Teste").exists()

    def test_detail_atendimento(self, authenticated_client, atendimento):
        """Deve exibir detalhes do atendimento."""
        url = reverse("atendimento_detail", args=[atendimento.pk])
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context["atendimento"] == atendimento
```

### Teste de API

```python
# tests/app/atendimentos/test_api.py

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAtendimentoAPI:
    """Testes para API de Atendimentos."""

    @pytest.fixture
    def api_client(self, user):
        """Cliente API autenticado."""
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_atendimentos(self, api_client, atendimento):
        """Deve listar atendimentos via API."""
        response = api_client.get("/api/atendimentos/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_atendimento(self, api_client, cliente, departamento):
        """Deve criar atendimento via API."""
        data = {
            "cliente": cliente.pk,
            "departamento": departamento.pk,
        }

        response = api_client.post("/api/atendimentos/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["cliente"] == cliente.pk

    def test_encerrar_atendimento(self, api_client, atendimento):
        """Deve encerrar atendimento via action."""
        url = f"/api/atendimentos/{atendimento.pk}/encerrar/"

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        atendimento.refresh_from_db()
        assert atendimento.status == "encerrado"
```

### Teste de Usecase

```python
# tests/modules/ai_engine/features/analise_mensage/test_usecase.py

import pytest
from unittest.mock import Mock, patch

from modules.ai_engine.features.analise_mensage.domain.usecase import (
    AnaliseMensageUsecase,
    AnaliseResult,
)


class TestAnaliseMensageUsecase:
    """Testes para AnaliseMensageUsecase."""

    @pytest.fixture
    def mock_llm(self):
        """LLM mockado."""
        return Mock()

    @pytest.fixture
    def usecase(self, mock_llm):
        """Instância do usecase com LLM mockado."""
        return AnaliseMensageUsecase(llm=mock_llm)

    def test_execute_success(self, usecase, mock_llm):
        """Deve analisar mensagem com sucesso."""
        mock_llm.invoke.return_value = AnaliseResult(
            intent="saudacao",
            sentiment="positivo",
            entities=[],
            suggested_response="Olá!",
        )

        result = usecase.execute("Bom dia!")

        assert result.is_success()
        assert result.value.intent == "saudacao"

    def test_execute_empty_message(self, usecase):
        """Deve falhar com mensagem vazia."""
        result = usecase.execute("")

        assert result.is_failure()
        assert "vazia" in str(result.error).lower()

    def test_execute_llm_error(self, usecase, mock_llm):
        """Deve capturar erro do LLM."""
        mock_llm.invoke.side_effect = Exception("API Error")

        result = usecase.execute("Mensagem")

        assert result.is_failure()
        assert "API Error" in str(result.error)
```

---

## Fixtures

### conftest.py Global

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
        password="testpass123",
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
        database="test_db",
    )
```

### Fixtures Específicas

```python
# tests/app/atendimentos/conftest.py

import pytest


@pytest.fixture
def cliente(db, tenant):
    """Cria cliente para testes."""
    from app.clientes.models import Cliente
    return Cliente.objects.create(
        tenant=tenant,
        nome="Cliente Teste",
        telefone="11999999999",
    )


@pytest.fixture
def departamento(db, tenant):
    """Cria departamento para testes."""
    from app.operacional.models import Departamento
    return Departamento.objects.create(
        tenant=tenant,
        nome="Suporte",
    )


@pytest.fixture
def atendimento(db, cliente, departamento):
    """Cria atendimento para testes."""
    from app.atendimentos.models import Atendimento
    return Atendimento.objects.create(
        cliente=cliente,
        departamento=departamento,
    )
```

---

## Mocking

### Mock de Serviço Externo

```python
@pytest.mark.django_db
@patch("app.evolution_sync.services.evolution_api.EvolutionAPI.send_message")
def test_send_message(mock_send, atendimento):
    """Testa envio de mensagem mockando API externa."""
    mock_send.return_value = {"status": "sent", "id": "123"}

    from app.evolution_sync.services import send_message_to_client
    result = send_message_to_client(atendimento, "Olá!")

    mock_send.assert_called_once()
    assert result["status"] == "sent"
```

### Mock de Celery Task

```python
@patch("app.atendimentos.tasks.process_atendimento_async.delay")
def test_signal_triggers_task(mock_delay, cliente, departamento):
    """Testa que signal dispara task."""
    from app.atendimentos.models import Atendimento

    atendimento = Atendimento.objects.create(
        cliente=cliente,
        departamento=departamento,
    )

    mock_delay.assert_called_once_with(atendimento.pk)
```

---

## Comandos

```bash
# Executar todos os testes
uv run task test-docker

# Teste específico
uv run task test-docker -- -k "test_create_atendimento"

# Com cobertura
uv run task test-docker -- --cov=src --cov-report=html

# Modo verbose
uv run task test-docker -- -v
```

---

## Restrições

- **SEMPRE** usar `@pytest.mark.django_db` para testes de banco
- **SEMPRE** criar fixtures reutilizáveis
- **SEMPRE** testar casos de sucesso e falha
- **SEMPRE** mockar serviços externos
- **NUNCA** depender de dados de produção
- **NUNCA** criar testes flaky (não-determinísticos)
- **NUNCA** testar lógica de terceiros

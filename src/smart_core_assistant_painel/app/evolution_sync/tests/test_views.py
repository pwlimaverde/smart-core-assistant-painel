import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.test import RequestFactory

from smart_core_assistant_painel.app.evolution_sync.views import webhook


@pytest.fixture
def factory() -> RequestFactory:
    return RequestFactory()


@patch("smart_core_assistant_painel.app.evolution_sync.views.WebhookProcessor")
@patch(
    "smart_core_assistant_painel.app.evolution_sync.views.normalize_evolution_webhook_batch"
)
def test_webhook_view_success(
    mock_normalize: Mock, mock_processor_cls: Mock, factory: RequestFactory
) -> None:
    # Mock Processor
    mock_processor_instance = mock_processor_cls.return_value
    mock_processor_instance.process_webhook.return_value = {"status": "ok"}

    # Mock Normalizer
    mock_normalize.return_value = []

    # Create Request
    payload = {"data": []}
    request = factory.post(
        "/sync/evolution/webhook/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    response = webhook(request)

    assert response.status_code == 200
    assert json.loads(response.content) == {"status": "ok"}
    mock_processor_instance.process_webhook.assert_called_once()


def test_webhook_view_invalid_method(factory: RequestFactory) -> None:
    request = factory.get("/sync/evolution/webhook/")
    response = webhook(request)

    assert response.status_code == 405
    assert json.loads(response.content) == {"detail": "method not allowed"}


def test_webhook_view_invalid_json(factory: RequestFactory) -> None:
    request = factory.post(
        "/sync/evolution/webhook/",
        data="invalid-json",
        content_type="application/json",
    )
    response = webhook(request)

    assert response.status_code == 400
    assert json.loads(response.content) == {"detail": "invalid json"}

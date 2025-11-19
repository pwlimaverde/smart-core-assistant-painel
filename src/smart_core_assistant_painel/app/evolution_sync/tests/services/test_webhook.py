from unittest.mock import MagicMock, Mock, patch

import pytest

from smart_core_assistant_painel.app.evolution_sync.domain.schemas import (
    EvolutionContactData,
    EvolutionMessageData,
    EvolutionProfileData,
    EvolutionWebhookEnvelope,
)
from smart_core_assistant_painel.app.evolution_sync.services.webhook import (
    WebhookProcessor,
)


@pytest.fixture
def processor() -> WebhookProcessor:
    return WebhookProcessor()


@pytest.fixture
def mock_envelope() -> EvolutionWebhookEnvelope:
    return EvolutionWebhookEnvelope(
        instance="test-instance",
        instance_id="inst-123",
        apikey="secret",
        contact=EvolutionContactData(
            jid="5511999999999@s.whatsapp.net", phone="5511999999999"
        ),
        message=EvolutionMessageData(type="conversation", text="Hello"),
        profile=EvolutionProfileData(push_name="Test User"),
    )


@patch(
    "smart_core_assistant_painel.app.evolution_sync.services.webhook.EvolutionInstance.objects"
)
@patch(
    "smart_core_assistant_painel.app.evolution_sync.services.webhook.EvolutionContact.objects"
)
@patch(
    "smart_core_assistant_painel.app.evolution_sync.services.webhook.Contato.objects"
)
@patch(
    "smart_core_assistant_painel.app.evolution_sync.services.webhook.sched_response_contact"
)
def test_process_webhook_success(
    mock_sched: Mock,
    mock_contato_mgr: Mock,
    mock_evo_contact_mgr: Mock,
    mock_evo_instance_mgr: Mock,
    processor: WebhookProcessor,
    mock_envelope: EvolutionWebhookEnvelope,
) -> None:
    # Mock Instance
    mock_instance = MagicMock()
    mock_instance.name = "test-instance"
    mock_evo_instance_mgr.get_or_create.return_value = (mock_instance, False)

    # Mock EvolutionContact
    mock_evo_contact = MagicMock()
    mock_evo_contact.contact_id = None  # Initially not linked
    mock_evo_contact_mgr.filter.return_value.first.return_value = (
        mock_evo_contact
    )

    # Mock Contato (Internal)
    mock_contato = MagicMock()
    mock_contato.id = 100
    mock_contato_mgr.get_or_create.return_value = (mock_contato, False)

    # Execute
    result = processor.process_webhook(
        payload={"data": {}}, envelopes=[mock_envelope]
    )

    # Assertions
    assert result["status"] == "processed"
    assert result["processed_count"] == 1

    # Verify Instance creation/update
    mock_evo_instance_mgr.get_or_create.assert_called_once()

    # Verify Contact resolution
    mock_evo_contact_mgr.filter.assert_called()

    # Verify Linking
    assert mock_evo_contact.contact == mock_contato
    mock_evo_contact.save.assert_called()

    # Verify Scheduling
    mock_sched.assert_called_once()
    args, _ = mock_sched.call_args
    assert args[0] == 100  # contact_id
    assert args[1] == "Hello"  # message text


def test_process_webhook_ignored_from_me(processor: WebhookProcessor) -> None:
    envelope = EvolutionWebhookEnvelope(from_me=True)
    result = processor.process_webhook({}, [envelope])

    assert result["status"] == "ignored_from_me"
    assert result["processed_count"] == 0

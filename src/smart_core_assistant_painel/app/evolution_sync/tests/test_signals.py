from unittest.mock import MagicMock, Mock, patch

import pytest

from smart_core_assistant_painel.app.evolution_sync.signals import (
    _on_message_saved,
)


@patch(
    "smart_core_assistant_painel.app.evolution_sync.signals.EvolutionWhatsAppService"
)
@patch(
    "smart_core_assistant_painel.app.evolution_sync.signals.EvolutionContact.objects"
)
def test_on_message_saved_success(
    mock_evo_contact_mgr: Mock, mock_service_cls: Mock
) -> None:
    # Mock Service
    mock_service_instance = mock_service_cls.return_value

    # Mock Message Instance (Django Model)
    mock_message = MagicMock()
    mock_message.id = 123
    mock_message.respondida = False
    mock_message.mensagem = "Hello"
    mock_message.atendimento.contato.id = 456
    mock_message.atendimento.contato.telefone = "5511999999999"

    # Mock EvolutionContact
    mock_evo_contact = MagicMock()
    mock_evo_contact.instance.active = True
    mock_evo_contact.instance.name = "inst-1"
    mock_evo_contact.instance.api_key = "key"
    mock_evo_contact.instance.server_url = "http://api"
    mock_evo_contact_mgr.filter.return_value.first.return_value = (
        mock_evo_contact
    )

    # Execute Signal Handler
    _on_message_saved(sender=None, instance=mock_message, created=True)

    # Verify Service Call
    mock_service_instance.send_message.assert_called_once()
    args, kwargs = mock_service_instance.send_message.call_args
    assert kwargs["instance"] == "inst-1"
    assert kwargs["number"] == "5511999999999"
    assert kwargs["text"] == "Hello"


def test_on_message_saved_not_created() -> None:
    mock_message = MagicMock()

    # Execute with created=False
    _on_message_saved(sender=None, instance=mock_message, created=False)

    # Should do nothing (no mocks needed as it returns early)


def test_on_message_saved_already_responded() -> None:
    mock_message = MagicMock()
    mock_message.respondida = True

    _on_message_saved(sender=None, instance=mock_message, created=True)

    # Should do nothing

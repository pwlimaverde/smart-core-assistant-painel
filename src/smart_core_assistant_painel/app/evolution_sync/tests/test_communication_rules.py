import pytest
from unittest.mock import patch, MagicMock
from smart_core_assistant_painel.app.evolution_sync.services.webhook import (
    WebhookProcessor,
)
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionInstance,
    WhiteList,
)
from smart_core_assistant_painel.app.evolution_sync.domain.schemas import (
    EvolutionWebhookEnvelope,
)


@pytest.mark.django_db
class TestCommunicationRules:
    def setup_method(self):
        self.processor = WebhookProcessor()
        self.payload = {
            "instance": "TestInstance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG123",
                },
                "message": {"conversation": "Hello"},
                "pushName": "Test User",
            },
            "sender": "5511999999999@s.whatsapp.net",
        }

    def test_filter_inter_instance_communication(self):
        # Create an instance with the sender's phone number
        EvolutionInstance.objects.create(
            name="Instance B",
            instance_id="inst_b",
            api_key="key",
            phone_number="5511999999999",
        )

        envelopes = [EvolutionWebhookEnvelope.from_dict_single(self.payload)]

        with patch(
            "smart_core_assistant_painel.app.evolution_sync.services.webhook.logger"
        ) as mock_logger:
            result = self.processor.process_webhook(self.payload, envelopes)

            # Should be ignored (valid_envelopes empty)
            assert (
                result["status"] == "ignored_from_me"
            )  # Default return when empty

            # Verify log message
            mock_logger.info.assert_any_call(
                "Ignoring interaction with instance 5511999999999 (from_me=False)"
            )

    def test_filter_whitelist_communication(self):
        # Create a whitelist entry
        WhiteList.objects.create(
            name="Director", phone_number="5511999999999", active=True
        )

        envelopes = [EvolutionWebhookEnvelope.from_dict_single(self.payload)]

        with patch(
            "smart_core_assistant_painel.app.evolution_sync.services.webhook.logger"
        ) as mock_logger:
            result = self.processor.process_webhook(self.payload, envelopes)

            assert result["status"] == "ignored_from_me"
            mock_logger.info.assert_any_call(
                "Ignoring interaction with whitelist 5511999999999"
            )

    @patch(
        "smart_core_assistant_painel.app.evolution_sync.services.webhook.processar_mensagem_por_contato"
    )
    def test_handle_from_me_message(self, mock_processar):
        # Modify payload to be fromMe=True
        self.payload["data"]["key"]["fromMe"] = True
        # remoteJid is now the recipient
        self.payload["data"]["key"]["remoteJid"] = (
            "5511888888888@s.whatsapp.net"
        )

        envelopes = [EvolutionWebhookEnvelope.from_dict_single(self.payload)]

        # Mock internal methods to avoid DB complexity if possible, or let them run
        # We need an instance for _get_or_create_instance
        EvolutionInstance.objects.create(
            name="MyInstance",
            instance_id="my_inst",
            api_key="key",
            phone_number="5511777777777",
        )

        result = self.processor.process_webhook(self.payload, envelopes)

        # Should be ignored for BOT processing (valid_envelopes empty)
        assert result["status"] == "ignored_from_me"

        # But processar_mensagem_por_contato should have been called
        mock_processar.assert_called_once()
        call_kwargs = mock_processar.call_args[1]
        assert call_kwargs["from_me"] is True
        assert call_kwargs["conteudo"] == "Hello"
        assert call_kwargs["nome_perfil_whatsapp"] == "Test User"

    def test_filter_instance_by_name(self):
        """Test filtering when phone_number is missing but name matches."""
        EvolutionInstance.objects.create(
            name="5511999999999",  # Name is the phone number
            instance_id="inst_c",
            api_key="key",
            phone_number="",  # Empty phone number
        )

        envelopes = [EvolutionWebhookEnvelope.from_dict_single(self.payload)]

        with patch(
            "smart_core_assistant_painel.app.evolution_sync.services.webhook.logger"
        ) as mock_logger:
            result = self.processor.process_webhook(self.payload, envelopes)

            assert result["status"] == "ignored_from_me"
            # Should match by name
            mock_logger.info.assert_any_call(
                "Ignoring interaction with instance 5511999999999 (from_me=False)"
            )

    def test_filter_inter_instance_from_me(self):
        """Test filtering when one instance sends a message to another instance (from_me=True)."""
        # Sender Instance (A)
        EvolutionInstance.objects.create(
            name="Instance A",
            instance_id="inst_a",
            api_key="key_a",
            phone_number="5511888888888",
        )
        # Receiver Instance (B) - The destination of the message
        EvolutionInstance.objects.create(
            name="Instance B",
            instance_id="inst_b",
            api_key="key_b",
            phone_number="5511999999999",
        )

        # Payload: A sends to B (fromMe=True)
        self.payload["data"]["key"]["fromMe"] = True
        self.payload["data"]["key"]["remoteJid"] = (
            "5511999999999@s.whatsapp.net"  # To B
        )
        self.payload["sender"] = "5511888888888@s.whatsapp.net"  # From A

        envelopes = [EvolutionWebhookEnvelope.from_dict_single(self.payload)]

        with patch(
            "smart_core_assistant_painel.app.evolution_sync.services.webhook.logger"
        ) as mock_logger:
            result = self.processor.process_webhook(self.payload, envelopes)

            assert result["status"] == "ignored_from_me"
            # Should be ignored because destination (B) is an instance
            mock_logger.info.assert_any_call(
                "Ignoring interaction with instance 5511999999999 (from_me=True)"
            )

    def test_filter_whitelist_communication_normalization(self):
        """Test filtering when Whitelist number format differs from payload (12 vs 13 digits)."""
        # Whitelist entry has 13 digits (with 9)
        WhiteList.objects.create(
            name="Director", phone_number="5511999999999", active=True
        )

        # Payload has 12 digits (without 9)
        self.payload["sender"] = "551199999999@s.whatsapp.net"
        self.payload["data"]["key"]["remoteJid"] = (
            "551199999999@s.whatsapp.net"
        )

        envelopes = [EvolutionWebhookEnvelope.from_dict_single(self.payload)]

        with patch(
            "smart_core_assistant_painel.app.evolution_sync.services.webhook.logger"
        ) as mock_logger:
            result = self.processor.process_webhook(self.payload, envelopes)

            assert result["status"] == "ignored_from_me"
            # Should match despite formatting difference
            mock_logger.info.assert_any_call(
                "Ignoring interaction with whitelist 551199999999"
            )

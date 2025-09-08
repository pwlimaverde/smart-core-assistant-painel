"""Tests for the Atendimentos app views."""

from unittest.mock import patch, MagicMock
import json

from django.test import TestCase, Client
from django.urls import reverse
from django.http import JsonResponse

from smart_core_assistant_painel.app.ui.operacional.models import Departamento
from smart_core_assistant_painel.modules.ai_engine import MessageData


class TestAtendimentosViews(TestCase):
    """Tests for the Atendimentos app views."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.client = Client()
        self.valid_webhook_data = {
            "instance": "test_instance",
            "apikey": "test_api_key",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "test_message_id"
                },
                "message": {
                    "conversation": "Test message"
                }
            }
        }

    @patch('smart_core_assistant_painel.app.ui.operacional.models.Departamento.validar_api_key')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.views.FeaturesCompose.load_message_data')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.views.set_wa_buffer')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.views.sched_message_response')
    def test_webhook_whatsapp_post_success(
        self,
        mock_sched_message_response: MagicMock,
        mock_set_wa_buffer: MagicMock,
        mock_load_message_data: MagicMock,
        mock_validar_api_key: MagicMock
    ) -> None:
        """Test successful WhatsApp webhook POST request."""
        # Arrange
        departamento_mock = MagicMock()
        mock_validar_api_key.return_value = departamento_mock
        
        message_data_mock = MessageData(
            instance="test_instance",
            api_key="test_api_key",
            numero_telefone="5511999999999",
            from_me=False,
            conteudo="Test message",
            message_type="text",
            message_id="test_message_id",
            metadados={},
            nome_perfil_whatsapp="Test User"
        )
        mock_load_message_data.return_value = message_data_mock

        # Act
        response = self.client.post(
            reverse('atendimentos:webhook_whatsapp'),
            data=json.dumps(self.valid_webhook_data),
            content_type='application/json'
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        mock_validar_api_key.assert_called_once_with(self.valid_webhook_data)
        mock_load_message_data.assert_called_once_with(self.valid_webhook_data)
        # Check that set_wa_buffer was called with a MessageData object containing the expected data
        mock_set_wa_buffer.assert_called_once()
        called_message_data = mock_set_wa_buffer.call_args[0][0]
        self.assertEqual(called_message_data.instance, "test_instance")
        self.assertEqual(called_message_data.api_key, "test_api_key")
        self.assertEqual(called_message_data.numero_telefone, "5511999999999")
        self.assertEqual(called_message_data.conteudo, "Test message")
        mock_sched_message_response.assert_called_once_with("5511999999999")

    @patch('smart_core_assistant_painel.app.ui.operacional.models.Departamento.validar_api_key')
    def test_webhook_whatsapp_post_invalid_api_key(
        self,
        mock_validar_api_key: MagicMock
    ) -> None:
        """Test WhatsApp webhook with invalid API key."""
        # Arrange
        mock_validar_api_key.return_value = None

        # Act
        response = self.client.post(
            reverse('atendimentos:webhook_whatsapp'),
            data=json.dumps(self.valid_webhook_data),
            content_type='application/json'
        )

        # Assert
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Invalid or inactive API key')

    def test_webhook_whatsapp_get_method_not_allowed(self) -> None:
        """Test WhatsApp webhook with GET method (should return 405)."""
        # Act
        response = self.client.get(reverse('atendimentos:webhook_whatsapp'))

        # Assert
        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Method not allowed')

    def test_webhook_whatsapp_post_empty_body(self) -> None:
        """Test WhatsApp webhook with empty POST body."""
        # Act
        response = self.client.post(
            reverse('atendimentos:webhook_whatsapp'),
            data='',
            content_type='application/json'
        )

        # Assert
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Empty request body')

    @patch('smart_core_assistant_painel.app.ui.operacional.models.Departamento.validar_api_key')
    @patch('smart_core_assistant_painel.modules.ai_engine.FeaturesCompose.load_message_data')
    def test_webhook_whatsapp_post_exception_handling(
        self,
        mock_load_message_data: MagicMock,
        mock_validar_api_key: MagicMock
    ) -> None:
        """Test WhatsApp webhook exception handling."""
        # Arrange
        departamento_mock = MagicMock()
        mock_validar_api_key.return_value = departamento_mock
        mock_load_message_data.side_effect = Exception("Test exception")

        # Act
        response = self.client.post(
            reverse('atendimentos:webhook_whatsapp'),
            data=json.dumps(self.valid_webhook_data),
            content_type='application/json'
        )

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Internal server error')
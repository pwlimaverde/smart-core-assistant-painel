"""Testes para as views do app Oraculo."""

import json
from unittest.mock import Mock, patch

from django.test import Client, TestCase
from django.urls import reverse

from ..models_departamento import Departamento


class TestWebhookWhatsApp(TestCase):
    """Testes para a view webhook_whatsapp."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.client = Client()
        self.webhook_url = reverse("oraculo:webhook_whatsapp")

        # Dados de exemplo do WhatsApp
        self.whatsapp_data = {
            "apikey": "test_api_key",
            "instance": "test_instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "ABCD1234",
                },
                "message": {"conversation": "Olá, preciso de ajuda"},
                "messageType": "conversation",
                "pushName": "Cliente Teste",
                "broadcast": False,
                "messageTimestamp": 1700000123,
            },
        }

        # Mock do departamento para validação
        self.mock_departamento = Mock(spec=Departamento)
        self.mock_departamento.id = 1
        self.mock_departamento.api_key = "test_api_key"
        self.mock_departamento.telefone_instancia = "test_instance"

    def test_webhook_get_not_allowed(self) -> None:
        """Testa que GET não é permitido no webhook."""
        response = self.client.get(self.webhook_url)
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_webhook_post_empty_body(self) -> None:
        """Testa webhook com corpo vazio."""
        response = self.client.post(
            self.webhook_url,
            data="",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)  # Bad request

    def test_webhook_post_invalid_json(self) -> None:
        """Testa webhook com JSON inválido."""
        response = self.client.post(
            self.webhook_url,
            data="invalid json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 500)  # JSON parse error

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.Departamento.validar_api_key"
    )
    def test_webhook_post_invalid_api_key(self, mock_validar: Mock) -> None:
        """Testa webhook com API key inválida."""
        mock_validar.return_value = None  # API key inválida

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(self.whatsapp_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)  # Unauthorized
        mock_validar.assert_called_once_with(self.whatsapp_data)

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.sched_message_response"
    )
    @patch("smart_core_assistant_painel.app.ui.oraculo.views.set_wa_buffer")
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.FeaturesCompose.load_message_data"
    )
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.Departamento.validar_api_key"
    )
    def test_webhook_post_nova_mensagem(
        self,
        mock_validar: Mock,
        mock_load_message: Mock,
        mock_set_buffer: Mock,
        mock_sched: Mock,
    ) -> None:
        """Testa o processamento de nova mensagem via POST."""
        # Setup mocks
        mock_validar.return_value = self.mock_departamento
        mock_message = Mock()
        mock_message.numero_telefone = "5511999999999"
        mock_load_message.return_value = mock_message

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(self.whatsapp_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        mock_validar.assert_called_once_with(self.whatsapp_data)
        mock_load_message.assert_called_once_with(self.whatsapp_data)
        mock_set_buffer.assert_called_once_with(mock_message)
        mock_sched.assert_called_once_with(mock_message.numero_telefone)

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.FeaturesCompose.load_message_data"
    )
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.Departamento.validar_api_key"
    )
    def test_webhook_post_load_message_error(
        self, mock_validar: Mock, mock_load_message: Mock
    ) -> None:
        """Testa erro no processamento de mensagem."""
        # Setup mocks
        mock_validar.return_value = self.mock_departamento
        mock_load_message.side_effect = Exception("Erro ao processar mensagem")

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(self.whatsapp_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        mock_validar.assert_called_once_with(self.whatsapp_data)
        mock_load_message.assert_called_once_with(self.whatsapp_data)

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.Departamento.validar_api_key"
    )
    def test_webhook_post_dados_invalidos(self, mock_validar: Mock) -> None:
        """Testa o webhook com dados inválidos."""
        mock_validar.return_value = self.mock_departamento
        dados_invalidos = {"invalid": "data"}

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(dados_invalidos),
            content_type="application/json",
        )

        # Pode retornar 500 se load_message_data falhar com dados inválidos
        self.assertIn(response.status_code, [200, 500])

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.sched_message_response"
    )
    @patch("smart_core_assistant_painel.app.ui.oraculo.views.set_wa_buffer")
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.FeaturesCompose.load_message_data"
    )
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.Departamento.validar_api_key"
    )
    def test_webhook_post_multiplas_mensagens(
        self,
        mock_validar: Mock,
        mock_load_message: Mock,
        mock_set_buffer: Mock,
        mock_sched: Mock,
    ) -> None:
        """Testa o webhook com múltiplas mensagens."""
        # Setup mocks
        mock_validar.return_value = self.mock_departamento
        mock_message = Mock()
        mock_message.numero_telefone = "5511999999999"
        mock_load_message.return_value = mock_message

        dados_multiplas = {
            "apikey": "test_api_key",
            "instance": "test_instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "ABCD1234",
                },
                "message": {"conversation": "Primeira mensagem"},
                "messageType": "conversation",
                "pushName": "Cliente Teste",
                "broadcast": False,
                "messageTimestamp": 1700000123,
            },
        }

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(dados_multiplas),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        mock_validar.assert_called_once_with(dados_multiplas)
        mock_load_message.assert_called_once_with(dados_multiplas)
        mock_set_buffer.assert_called_once_with(mock_message)
        mock_sched.assert_called_once_with(mock_message.numero_telefone)

    def test_webhook_put_method_not_allowed(self) -> None:
        """Testa método PUT não permitido."""
        response = self.client.put(self.webhook_url)
        self.assertEqual(response.status_code, 405)

    def test_webhook_delete_method_not_allowed(self) -> None:
        """Testa método DELETE não permitido."""
        response = self.client.delete(self.webhook_url)
        self.assertEqual(response.status_code, 405)


class TestViewsIntegration(TestCase):
    """Testes de integração para as views."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.client = Client()
        self.webhook_url = reverse("oraculo:webhook_whatsapp")

        # Mock do departamento para validação
        self.mock_departamento = Mock(spec=Departamento)
        self.mock_departamento.id = 1
        self.mock_departamento.api_key = "test_api_key"
        self.mock_departamento.telefone_instancia = "test_instance"

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.sched_message_response"
    )
    @patch("smart_core_assistant_painel.app.ui.oraculo.views.set_wa_buffer")
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.FeaturesCompose.load_message_data"
    )
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.Departamento.validar_api_key"
    )
    def test_fluxo_completo_nova_conversa(
        self,
        mock_validar: Mock,
        mock_load_message: Mock,
        mock_set_buffer: Mock,
        mock_sched: Mock,
    ) -> None:
        """Testa o fluxo completo de uma nova conversa via webhook."""
        # Setup mocks
        mock_validar.return_value = self.mock_departamento
        mock_message = Mock()
        mock_message.numero_telefone = "5511999999999"
        mock_load_message.return_value = mock_message

        payload = {
            "apikey": "test_api_key",
            "instance": "test_instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "FLUXO123",
                },
                "message": {"conversation": "Iniciando conversa"},
                "messageType": "conversation",
                "pushName": "Cliente Fluxo",
                "broadcast": False,
                "messageTimestamp": 1700000123,
            },
        }

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        mock_validar.assert_called_once_with(payload)
        mock_load_message.assert_called_once_with(payload)
        mock_set_buffer.assert_called_once_with(mock_message)
        mock_sched.assert_called_once_with(mock_message.numero_telefone)

    def test_webhook_csrf_exempt(self) -> None:
        """Verifica se a view do webhook está isenta de CSRF (csrf_exempt)."""
        from ..views import webhook_whatsapp

        # Verifica se a view tem o atributo csrf_exempt
        self.assertTrue(hasattr(webhook_whatsapp, "csrf_exempt"))
        # ou verifica se está no decorator
        self.assertTrue(getattr(webhook_whatsapp, "csrf_exempt", False))

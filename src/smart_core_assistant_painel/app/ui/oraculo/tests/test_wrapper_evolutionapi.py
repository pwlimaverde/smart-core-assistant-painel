"""Testes para o wrapper da Evolution API."""

import pytest
import requests
from unittest.mock import patch, MagicMock

from smart_core_assistant_painel.app.ui.oraculo.wrapper_evolutionapi import (
    BaseEvolutionAPI,
    SendMessage,
)


class TestBaseEvolutionAPI:
    """Testes para a classe BaseEvolutionAPI."""

    def setup_method(self):
        """Configuração inicial para cada teste."""
        self.base_api = BaseEvolutionAPI()
        self.base_api._API_KEY = {"test_instance": "test_key"}

    def test_mount_url_without_params(self):
        """Testa se a URL é montada corretamente sem parâmetros."""
        path = "/test/path"
        expected_url = "http://evolution-api:8080/test/path"
        assert self.base_api._mount_url(path, {}) == expected_url

    def test_mount_url_with_params(self):
        """Testa se a URL é montada corretamente com parâmetros."""
        path = "/test/path"
        params = {"param1": "value1", "param2": "value2"}
        expected_url = "http://evolution-api:8080/test/path?param1=value1&param2=value2"
        assert self.base_api._mount_url(path, params) == expected_url

    def test_get_instance(self):
        """Testa se a instância é extraída corretamente do path."""
        path = "/message/sendText/test_instance/"
        assert self.base_api._get_instance(path) == "test_instance"

    @patch("requests.get")
    def test_send_request_get_success(self, mock_get):
        """Testa uma requisição GET bem-sucedida."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        path = "/test/path/test_instance"
        response = self.base_api._send_request(path, method="GET")

        mock_get.assert_called_once_with(
            "http://evolution-api:8080/test/path/test_instance",
            headers={"Content-Type": "application/json", "apikey": "test_key"},
            json=None,
        )
        assert response.status_code == 200

    @patch("requests.post")
    def test_send_request_post_success(self, mock_post):
        """Testa uma requisição POST bem-sucedida."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        path = "/test/path/test_instance"
        body = {"key": "value"}
        response = self.base_api._send_request(path, method="POST", body=body)

        mock_post.assert_called_once_with(
            "http://evolution-api:8080/test/path/test_instance",
            headers={"Content-Type": "application/json", "apikey": "test_key"},
            json=body,
        )
        assert response.status_code == 201

    def test_send_request_missing_api_key(self):
        """Testa se um ValueError é levantado quando a API key não é encontrada."""
        path = "/test/path/unknown_instance"
        with pytest.raises(ValueError, match="API key não encontrada para instância: unknown_instance"):
            self.base_api._send_request(path)

    def test_send_request_unsupported_method(self):
        """Testa se um ValueError é levantado para um método HTTP não suportado."""
        path = "/test/path/test_instance"
        with pytest.raises(ValueError, match="Método HTTP não suportado: PATCH"):
            self.base_api._send_request(path, method="PATCH")


class TestSendMessage:
    """Testes para a classe SendMessage."""

    def setup_method(self):
        """Configuração inicial para cada teste."""
        self.send_message_api = SendMessage()

    @patch.object(BaseEvolutionAPI, "_send_request")
    def test_send_message(self, mock_send_request):
        """Testa se o método send_message chama _send_request com os parâmetros corretos."""
        instance = "test_instance"
        body = {"number": "123456789", "textMessage": {"text": "Hello"}}

        self.send_message_api.send_message(instance, body)

        mock_send_request.assert_called_once_with(
            f"/message/sendText/{instance}/",
            method="POST",
            body=body,
        )

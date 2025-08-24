"""Testes para a WahaWhatsAppApi."""

import pytest
from unittest.mock import patch, MagicMock

from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.waha.waha_whatsapp_api import (
    WahaWhatsAppApi,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    MessageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import WahaApiError


@pytest.fixture
def waha_api():
    """Fixture para criar uma instância da WahaWhatsAppApi com parâmetros mockados."""
    params = MessageParameters(
        session="test_session",
        chat_id="12345",
        message="Hello",
        error=WahaApiError,
    )
    api = WahaWhatsAppApi(params)
    return api


@patch("requests.post")
@patch("smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.waha.waha_whatsapp_api.SERVICEHUB")
def test_send_message_success(mock_service_hub, mock_post, waha_api):
    """Testa o envio de mensagem com sucesso."""
    mock_service_hub.WHATSAPP_API_BASE_URL = "http://waha.api"
    mock_service_hub.WHATSAPP_API_SEND_TEXT_URL = "sendText"

    waha_api.send_message()

    expected_url = "http://waha.api/sendText"
    expected_payload = {
        "session": "test_session",
        "chatId": "12345",
        "text": "Hello",
    }
    mock_post.assert_called_once_with(
        url=expected_url,
        json=expected_payload,
        headers={"Content-Type": "application/json"},
    )


@patch("requests.post", side_effect=Exception("API Error"))
@patch("smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.waha.waha_whatsapp_api.SERVICEHUB")
def test_send_message_failure(mock_service_hub, mock_post, waha_api):
    """Testa a falha no envio de mensagem."""
    with pytest.raises(Exception, match="API Error"):
        waha_api.send_message()


@patch("requests.post")
@patch("smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.waha.waha_whatsapp_api.SERVICEHUB")
def test_typing_start(mock_service_hub, mock_post, waha_api):
    """Testa o início do indicador de 'digitando'."""
    mock_service_hub.WHATSAPP_API_BASE_URL = "http://waha.api"
    mock_service_hub.WHATSAPP_API_START_TYPING_URL = "startTyping"

    waha_api.typing(typing=True)

    expected_url = "http://waha.api/startTyping"
    expected_payload = {
        "session": "test_session",
        "chatId": "12345",
    }
    mock_post.assert_called_once_with(
        url=expected_url,
        json=expected_payload,
        headers={"Content-Type": "application/json"},
    )


@patch("requests.post")
@patch("smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.waha.waha_whatsapp_api.SERVICEHUB")
def test_typing_stop(mock_service_hub, mock_post, waha_api):
    """Testa a parada do indicador de 'digitando'."""
    mock_service_hub.WHATSAPP_API_BASE_URL = "http://waha.api"
    mock_service_hub.WHATSAPP_API_STOP_TYPING_URL = "stopTyping"

    waha_api.typing(typing=False)

    expected_url = "http://waha.api/stopTyping"
    expected_payload = {
        "session": "test_session",
        "chatId": "12345",
    }
    mock_post.assert_called_once_with(
        url=expected_url,
        json=expected_payload,
        headers={"Content-Type": "application/json"},
    )

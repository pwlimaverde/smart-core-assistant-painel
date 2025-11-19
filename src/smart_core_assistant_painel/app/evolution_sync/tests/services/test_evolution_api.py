from unittest.mock import Mock, patch

import pytest
from requests import Response

from smart_core_assistant_painel.app.evolution_sync.services.evolution_api import (
    EvolutionWhatsAppService,
)


@pytest.fixture
def service() -> EvolutionWhatsAppService:
    return EvolutionWhatsAppService()


@patch("requests.get")
def test_send_request_success(
    mock_get: Mock, service: EvolutionWhatsAppService
) -> None:
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = {"success": True}
    mock_get.return_value = mock_response

    response = service._send_request(
        base_url="http://api.test",
        path="/test",
        api_key="secret",
        method="GET",
    )

    assert response.status_code == 200
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "http://api.test/test"
    assert kwargs["headers"]["apikey"] == "secret"


@patch("requests.post")
def test_send_message_success(
    mock_post: Mock, service: EvolutionWhatsAppService
) -> None:
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.ok = True
    mock_post.return_value = mock_response

    service.send_message(
        instance="inst1",
        api_key="secret",
        number="123456",
        text="hello",
        base_url="http://api.test",
    )

    # Should be called twice: once for typing, once for sending message, once for stop typing?
    # Actually implementation calls: _typing(True) -> _send_request -> _typing(False)
    # _typing calls POST /chat/sendPresence/{instance}
    # send_message calls POST /message/sendText/{instance}

    assert mock_post.call_count == 3

    # Check calls
    calls = mock_post.call_args_list

    # 1. Typing Start
    assert "sendPresence" in calls[0][0][0]
    assert calls[0][1]["json"]["presence"] == "composing"

    # 2. Send Message
    assert "sendText" in calls[1][0][0]
    assert calls[1][1]["json"]["text"] == "hello"

    # 3. Typing Stop
    assert "sendPresence" in calls[2][0][0]
    assert calls[2][1]["json"]["presence"] == "paused"


@patch("requests.post")
def test_send_message_failure(
    mock_post: Mock, service: EvolutionWhatsAppService
) -> None:
    # Mock typing success
    mock_response_ok = Mock(spec=Response)
    mock_response_ok.status_code = 200
    mock_response_ok.ok = True

    # Mock send failure
    mock_response_fail = Mock(spec=Response)
    mock_response_fail.status_code = 500
    mock_response_fail.ok = False
    mock_response_fail.text = "Internal Error"

    # Sequence: Typing OK, Send Fail
    mock_post.side_effect = [mock_response_ok, mock_response_fail]

    with pytest.raises(Exception) as exc:
        service.send_message(
            instance="inst1",
            api_key="secret",
            number="123456",
            text="hello",
            base_url="http://api.test",
        )

    assert "Erro ao enviar mensagem" in str(exc.value)
    assert "500" in str(exc.value)

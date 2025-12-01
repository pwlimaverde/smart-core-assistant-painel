
import pytest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from django.test import RequestFactory
from smart_core_assistant_painel.app.ui.core.views import (
    health_check, home, clickup_callback, _update_env_value, _exchange_code_for_token
)

class TestCoreViews:
    def test_health_check(self):
        factory = RequestFactory()
        request = factory.get("/health")
        response = health_check(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_home(self):
        factory = RequestFactory()
        request = factory.get("/")
        response = home(request)
        assert response.status_code == 200
        assert b"Smart Core Assistant Painel" in response.content

    def test_clickup_callback_no_code(self):
        factory = RequestFactory()
        request = factory.get("/callback")
        response = clickup_callback(request)
        assert response.status_code == 400

    @patch("smart_core_assistant_painel.app.ui.core.views.config")
    def test_clickup_callback_no_redirect_uri(self, mock_config):
        mock_config.return_value = ""
        factory = RequestFactory()
        request = factory.get("/callback?code=123")
        response = clickup_callback(request)
        assert response.status_code == 500

    @patch("smart_core_assistant_painel.app.ui.core.views.config")
    @patch("smart_core_assistant_painel.app.ui.core.views._exchange_code_for_token")
    @patch("smart_core_assistant_painel.app.ui.core.views._update_env_value")
    def test_clickup_callback_success(self, mock_update, mock_exchange, mock_config):
        mock_config.return_value = "http://localhost"
        mock_exchange.return_value = {"access_token": "token123456"}

        factory = RequestFactory()
        request = factory.get("/callback?code=123")
        response = clickup_callback(request)

        assert response.status_code == 200
        mock_update.assert_called_with("CLICKUP_OAUTH_ACCESS_TOKEN", "token123456")
        assert b"ClickUp OAuth" in response.content

    @patch("smart_core_assistant_painel.app.ui.core.views.config")
    @patch("smart_core_assistant_painel.app.ui.core.views._exchange_code_for_token")
    def test_clickup_callback_failure_exchange(self, mock_exchange, mock_config):
        mock_config.return_value = "http://localhost"
        mock_exchange.return_value = {"error": "fail"}

        factory = RequestFactory()
        request = factory.get("/callback?code=123")
        response = clickup_callback(request)

        assert response.status_code == 502

    @patch("smart_core_assistant_painel.app.ui.core.views.urlopen")
    def test_exchange_code_for_token_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"access_token": "abc"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        data = _exchange_code_for_token("code", "uri")
        assert data["access_token"] == "abc"

    @patch("smart_core_assistant_painel.app.ui.core.views.urlopen")
    def test_exchange_code_for_token_http_error(self, mock_urlopen):
        err = HTTPError("url", 400, "Bad Request", {}, None)
        err.read = lambda: b"Body"
        mock_urlopen.side_effect = err

        data = _exchange_code_for_token("code", "uri")
        assert "HTTPError" in data["error"]

    @patch("smart_core_assistant_painel.app.ui.core.views.urlopen")
    def test_exchange_code_for_token_url_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Reason")

        data = _exchange_code_for_token("code", "uri")
        assert "URLError" in data["error"]

    def test_update_env_value(self):
        with patch("pathlib.Path.exists") as mock_exists, \
             patch("pathlib.Path.read_text") as mock_read, \
             patch("pathlib.Path.write_text") as mock_write:

            mock_exists.return_value = True
            mock_read.return_value = "KEY=old\nOTHER=val"

            _update_env_value("KEY", "new")

            mock_write.assert_called()
            args, kwargs = mock_write.call_args
            content = args[0]
            assert "KEY=new" in content
            assert "OTHER=val" in content

    def test_update_env_value_new_file(self):
        with patch("pathlib.Path.exists") as mock_exists, \
             patch("pathlib.Path.write_text") as mock_write:

            mock_exists.return_value = False

            _update_env_value("KEY", "new")

            mock_write.assert_called()
            content = mock_write.call_args[0][0]
            assert "KEY=new" in content

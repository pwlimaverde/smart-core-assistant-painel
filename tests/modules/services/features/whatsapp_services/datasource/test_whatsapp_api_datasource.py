import pytest
from unittest.mock import patch, MagicMock
import requests

from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.whatsapp_api_datasource import (
    WhatsAppAPIDataSource,
)
from smart_core_assistant_painel.modules.services.utils.erros import WhatsAppServiceError
from smart_core_assistant_painel.modules.services.utils.parameters import WSParameters


class TestWhatsAppAPIDataSource:
    """Testes para o WhatsAppAPIDataSource."""

    @pytest.fixture
    def datasource(self) -> WhatsAppAPIDataSource:
        """Fixture que retorna uma instância do WhatsAppAPIDataSource."""
        return WhatsAppAPIDataSource()

    @pytest.fixture
    def mock_servicehub(self):
        """Mock do SERVICEHUB."""
        with patch('smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.whatsapp_api_datasource.SERVICEHUB') as mock:
            mock.WHATSAPP_API_BASE_URL = "http://test-api.com"
            mock.WHATSAPP_API_SEND_TEXT_URL = "/message/sendText/{instance}/"
            yield mock

    @pytest.fixture
    def valid_parameters(self) -> WSParameters:
        """Fixture que retorna parâmetros válidos para os testes."""
        return WSParameters(
            instance="test_instance",
            api_key="test_api_key",
            message_data={"number": "123456789", "textMessage": {"text": "Hello"}},
            error=WhatsAppServiceError("Test error")
        )

    def test_call_success_case(
        self, datasource: WhatsAppAPIDataSource, mock_servicehub, valid_parameters: WSParameters
    ) -> None:
        """Testa o caso de sucesso do método __call__."""
        # Mock da resposta da requisição
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Success"

        with patch('requests.post', return_value=mock_response):
            result = datasource(valid_parameters)
            
            # Verifica se o resultado é o esperado
            assert result == mock_response
            mock_servicehub.WHATSAPP_API_BASE_URL = "http://test-api.com"
            mock_servicehub.WHATSAPP_API_SEND_TEXT_URL = "/message/sendText/{instance}/"

    def test_call_with_error_status_code(
        self, datasource: WhatsAppAPIDataSource, mock_servicehub, valid_parameters: WSParameters
    ) -> None:
        """Testa o caso de erro com status code inválido."""
        # Mock da resposta da requisição com erro
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch('requests.post', return_value=mock_response):
            with pytest.raises(WhatsAppServiceError):
                datasource(valid_parameters)

    def test_call_without_base_url(
        self, datasource: WhatsAppAPIDataSource, valid_parameters: WSParameters
    ) -> None:
        """Testa o caso em que a URL base não está configurada."""
        with patch('smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.whatsapp_api_datasource.SERVICEHUB') as mock_servicehub:
            mock_servicehub.WHATSAPP_API_BASE_URL = ""
            mock_servicehub.WHATSAPP_API_SEND_TEXT_URL = "/message/sendText/{instance}/"
            
            with pytest.raises(WhatsAppServiceError):
                datasource(valid_parameters)

    def test_call_without_send_text_url(
        self, datasource: WhatsAppAPIDataSource, valid_parameters: WSParameters
    ) -> None:
        """Testa o caso em que a URL de envio de texto não está configurada."""
        with patch('smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.whatsapp_api_datasource.SERVICEHUB') as mock_servicehub:
            mock_servicehub.WHATSAPP_API_BASE_URL = "http://test-api.com"
            mock_servicehub.WHATSAPP_API_SEND_TEXT_URL = ""
            
            with pytest.raises(WhatsAppServiceError):
                datasource(valid_parameters)
import pytest
from unittest.mock import Mock, patch

from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.whatsapp_services_datasource import (
    WhatsappServicesDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    MessageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    WahaApiError,
)


class TestWhatsappServicesDatasource:
    """Testes para a classe WhatsappServicesDatasource."""

    @pytest.fixture
    def datasource(self):
        """Fixture para criar uma instância do datasource."""
        return WhatsappServicesDatasource()

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        return MessageParameters(
            session="test-session",
            chat_id="5511999999999",
            message="Mensagem de teste",
            error=WahaApiError("Erro de teste da API"),
        )

    def test_call_returns_whatsapp_api(self, datasource, sample_parameters):
        """Testa se o datasource retorna uma instância de WhatsappApi."""
        # Act
        result = datasource(sample_parameters)
        
        # Assert
        assert isinstance(result, WhatsappApi)
        assert result._parameters == sample_parameters

    def test_call_with_different_parameters(self, datasource):
        """Testa o datasource com diferentes parâmetros."""
        # Arrange
        parameters = MessageParameters(
            session="another-session",
            chat_id="5511888888888",
            message="Outra mensagem",
            error=None,
        )
        
        # Act
        result = datasource(parameters)
        
        # Assert
        assert isinstance(result, WhatsappApi)
        assert result._parameters.session == "another-session"
        assert result._parameters.chat_id == "5511888888888"
        assert result._parameters.message == "Outra mensagem"

    def test_call_preserves_parameters(self, datasource, sample_parameters):
        """Testa se os parâmetros são preservados corretamente."""
        # Act
        result = datasource(sample_parameters)
        
        # Assert
        assert result._parameters.session == sample_parameters.session
        assert result._parameters.chat_id == sample_parameters.chat_id
        assert result._parameters.message == sample_parameters.message
        assert result._parameters.error == sample_parameters.error

    @patch('smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.whatsapp_services_datasource.WahaWhatsAppApi')
    def test_call_creates_waha_api_instance(self, mock_waha_api, datasource, sample_parameters):
        """Testa se o datasource cria uma instância de WahaWhatsAppApi."""
        # Arrange
        mock_instance = Mock()
        mock_waha_api.return_value = mock_instance
        
        # Act
        result = datasource(sample_parameters)
        
        # Assert
        mock_waha_api.assert_called_once_with(parameters=sample_parameters)
        assert result == mock_instance

    def test_multiple_calls_create_different_instances(self, datasource, sample_parameters):
        """Testa se múltiplas chamadas criam instâncias diferentes."""
        # Act
        result1 = datasource(sample_parameters)
        result2 = datasource(sample_parameters)
        
        # Assert
        assert result1 is not result2
        assert isinstance(result1, WhatsappApi)
        assert isinstance(result2, WhatsappApi)
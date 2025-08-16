import pytest
from unittest.mock import patch, MagicMock
from py_return_success_or_error import NoParams

from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_api_datasource import (
    EvolutionAPIDatasource,
)
from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.interface.whatsapp_service import (
    WhatsAppService,
)


class TestEvolutionAPIDatasource:
    """Testes para o EvolutionAPIDatasource."""

    @pytest.fixture
    def datasource(self) -> EvolutionAPIDatasource:
        """Fixture que retorna uma instância do EvolutionAPIDatasource."""
        return EvolutionAPIDatasource()

    @pytest.fixture
    def mock_servicehub(self):
        """Mock do SERVICEHUB."""
        with patch('smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.whatsapp_api_datasource.SERVICEHUB') as mock:
            mock.WHATSAPP_API_BASE_URL = "http://test-api.com"
            mock.WHATSAPP_API_SEND_TEXT_URL = "/message/sendText/{instance}/"
            yield mock

    @pytest.fixture
    def valid_parameters(self) -> NoParams:
        """Fixture que retorna parâmetros válidos para os testes."""
        return NoParams()

    def test_call_success_case(
        self, datasource: EvolutionAPIDatasource, valid_parameters: NoParams
    ) -> None:
        """Testa o caso de sucesso do método __call__."""
        result = datasource(valid_parameters)
        
        # Verifica se o resultado é uma instância de WhatsAppService
        assert isinstance(result, WhatsAppService)

    def test_call_with_exception(
        self, datasource: EvolutionAPIDatasource, valid_parameters: NoParams
    ) -> None:
        """Testa o caso de erro durante a criação do serviço."""
        # Mock do EvolutionWhatsAppService para lançar exceção
        with patch(
            "smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_api_datasource.EvolutionWhatsAppService",
            side_effect=Exception("Test error")
        ):
            with pytest.raises(TypeError, match="Erro ao carregar serviço Evolution: Test error"):
                datasource(valid_parameters)
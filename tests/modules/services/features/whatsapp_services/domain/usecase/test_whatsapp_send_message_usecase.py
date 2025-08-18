import pytest
from unittest.mock import MagicMock
import requests

from py_return_success_or_error import SuccessReturn, ErrorReturn

from smart_core_assistant_painel.modules.services import (
    WhatsAppMensagemParameters,
    WhatsAppServiceError,
)
from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.usecase.whatsapp_service_usecase import (
    WhatsAppServiceUsecase,
)


class TestWhatsAppServiceUsecase:
    """Testes para o WhatsAppServiceUsecase."""

    @pytest.fixture
    def usecase(self) -> WhatsAppServiceUsecase:
        """Fixture que retorna uma instância do WhatsAppServiceUsecase."""
        # Mock do datasource
        mock_datasource = MagicMock()
        return WhatsAppServiceUsecase(mock_datasource)

    @pytest.fixture
    def valid_parameters(self) -> WhatsAppMensagemParameters:
        """Fixture que retorna parâmetros válidos para os testes."""
        return WhatsAppMensagemParameters(
            instance="test_instance",
            api_key="test_api_key",
            message_data={"number": "123456789", "textMessage": {"text": "Hello"}},
            error=WhatsAppServiceError("Test error")
        )

    def test_call_success_case(
        self, usecase: WhatsAppServiceUsecase, valid_parameters: WhatsAppMensagemParameters
    ) -> None:
        """Testa o caso de sucesso do método __call__."""
        # Mock do resultado do datasource
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        usecase._datasource.return_value = mock_response

        result = usecase(valid_parameters)
        
        # Verifica se o resultado é o esperado
        assert isinstance(result, SuccessReturn)
        assert result.result == mock_response

    def test_call_error_from_datasource(
        self, usecase: WhatsAppServiceUsecase, valid_parameters: WhatsAppMensagemParameters
    ) -> None:
        """Testa o caso de erro vindo do datasource."""
        # Configura o datasource para lançar uma exceção
        usecase._datasource.side_effect = WhatsAppServiceError("Datasource error")

        result = usecase(valid_parameters)
        
        # Verifica se o resultado é o esperado
        assert isinstance(result, ErrorReturn)
        assert isinstance(result.result, WhatsAppServiceError)

    def test_call_exception_handling(
        self, usecase: WhatsAppServiceUsecase, valid_parameters: WhatsAppMensagemParameters
    ) -> None:
        """Testa o tratamento de exceções."""
        # Configura o _resultDatasource para lançar uma exceção genérica
        usecase._resultDatasource = MagicMock(side_effect=Exception("Generic error"))

        result = usecase(valid_parameters)
        
        # Verifica se o resultado é o esperado
        assert isinstance(result, ErrorReturn)
        assert isinstance(result.result, WhatsAppServiceError)
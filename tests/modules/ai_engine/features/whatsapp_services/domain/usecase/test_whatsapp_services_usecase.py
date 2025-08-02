import pytest
from unittest.mock import Mock, patch
from py_return_success_or_error import (
    EMPTY,
    ErrorReturn,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.usecase.whatsapp_services_usecase import (
    WhatsappServicesUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    MessageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import WahaApiError


class TestWhatsappServicesUseCase:
    """Testes para a classe WhatsappServicesUseCase."""

    @pytest.fixture
    def mock_datasource(self):
        """Fixture para criar um mock do datasource."""
        return Mock()

    @pytest.fixture
    def mock_whatsapp_api(self):
        """Fixture para criar um mock da WhatsappApi."""
        mock_api = Mock(spec=WhatsappApi)
        mock_api.typing = Mock()
        mock_api.send_message = Mock()
        return mock_api

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        return MessageParameters(
            session="session_123",
            chat_id="chat_456",
            message="Mensagem de teste",
            error=WahaApiError("Erro de teste da API WhatsApp"),
        )

    @pytest.fixture
    def usecase(self, mock_datasource):
        """Fixture para criar uma instância do usecase."""
        return WhatsappServicesUseCase(mock_datasource)

    def test_call_success_case(self, usecase, sample_parameters, mock_whatsapp_api):
        """Testa o caso de sucesso da chamada do usecase."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(mock_whatsapp_api)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert result.result == EMPTY
            
            # Verifica se os métodos da API foram chamados na ordem correta
            mock_whatsapp_api.typing.assert_any_call(typing=True)
            mock_whatsapp_api.send_message.assert_called_once()
            mock_whatsapp_api.typing.assert_any_call(typing=False)
            
            # Verifica se typing foi chamado exatamente 2 vezes
            assert mock_whatsapp_api.typing.call_count == 2

    def test_call_error_from_datasource(self, usecase, sample_parameters):
        """Testa o caso de erro retornado pelo datasource."""
        # Arrange
        error_message = "Erro no datasource"
        
        with patch.object(
            usecase, '_resultDatasource', return_value=ErrorReturn(error_message)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, ErrorReturn)
            assert isinstance(result.result, WahaApiError)
            assert "Erro ao obter dados do datasource." in str(result.result)

    def test_call_exception_handling(self, usecase, sample_parameters):
        """Testa o tratamento de exceções durante a execução."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', side_effect=Exception("Erro inesperado")
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, ErrorReturn)
            assert isinstance(result.result, WahaApiError)
            assert "Erro inesperado" in str(result.result)

    def test_whatsapp_api_send_message_exception(self, usecase, sample_parameters, mock_whatsapp_api):
        """Testa o comportamento quando send_message lança uma exceção."""
        # Arrange
        mock_whatsapp_api.send_message.side_effect = Exception("Erro ao enviar mensagem")
        
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(mock_whatsapp_api)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, ErrorReturn)
            assert isinstance(result.result, WahaApiError)
            assert "Erro ao enviar mensagem" in str(result.result)

    def test_whatsapp_api_typing_exception(self, usecase, sample_parameters, mock_whatsapp_api):
        """Testa o comportamento quando typing lança uma exceção."""
        # Arrange
        mock_whatsapp_api.typing.side_effect = Exception("Erro no typing")
        
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(mock_whatsapp_api)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, ErrorReturn)
            assert isinstance(result.result, WahaApiError)
            assert "Erro no typing" in str(result.result)

    def test_parameters_validation(self, mock_datasource):
        """Testa a validação dos parâmetros de entrada."""
        # Arrange
        usecase = WhatsappServicesUseCase(mock_datasource)
        invalid_params = None
        
        # Mock _resultDatasource para simular que o datasource será chamado
        # com parameters=None, o que deve causar um erro no _resultDatasource
        with patch.object(
            usecase, '_resultDatasource', side_effect=AttributeError("'NoneType' object has no attribute")
        ):
            # Act & Assert
            # Quando parameters é None, o _resultDatasource tentará acessar atributos
            # de None, causando AttributeError que será capturado pelo try/catch
            result = usecase(invalid_params)
            
            # O usecase deve retornar um ErrorReturn com WahaApiError
            assert isinstance(result, ErrorReturn)
            assert isinstance(result.result, WahaApiError)

    def test_datasource_call_parameters(self, usecase, sample_parameters, mock_whatsapp_api):
        """Testa se o datasource é chamado com os parâmetros corretos."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(mock_whatsapp_api)
        ) as mock_result_datasource:
            # Act
            usecase(sample_parameters)
            
            # Assert
            mock_result_datasource.assert_called_once_with(
                parameters=sample_parameters, datasource=usecase._datasource
            )

    def test_typing_sequence(self, usecase, sample_parameters, mock_whatsapp_api):
        """Testa a sequência correta de chamadas de typing."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(mock_whatsapp_api)
        ):
            # Act
            usecase(sample_parameters)
            
            # Assert
            # Verifica a ordem das chamadas
            expected_calls = [
                ((True,), {}),  # typing(typing=True)
                ((False,), {})  # typing(typing=False)
            ]
            actual_calls = [(call.args, call.kwargs) for call in mock_whatsapp_api.typing.call_args_list]
            
            # Verifica se as chamadas foram feitas com os argumentos corretos
            assert len(actual_calls) == 2
            assert actual_calls[0][1] == {'typing': True} or actual_calls[0][0] == (True,)
            assert actual_calls[1][1] == {'typing': False} or actual_calls[1][0] == (False,)

    def test_empty_message_parameters(self, usecase, mock_whatsapp_api):
        """Testa o comportamento com mensagem vazia."""
        # Arrange
        empty_message_params = MessageParameters(
            session="session_123",
            chat_id="chat_456",
            message="",  # Mensagem vazia
            error=WahaApiError("Erro de teste"),
        )
        
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(mock_whatsapp_api)
        ):
            # Act
            result = usecase(empty_message_params)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert result.result == EMPTY
            mock_whatsapp_api.send_message.assert_called_once()

    def test_none_message_parameters(self, usecase, mock_whatsapp_api):
        """Testa o comportamento com mensagem None."""
        # Arrange
        none_message_params = MessageParameters(
            session="session_123",
            chat_id="chat_456",
            message=None,
            error=WahaApiError("Erro de teste"),
        )
        
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(mock_whatsapp_api)
        ):
            # Act
            result = usecase(none_message_params)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert result.result == EMPTY
            mock_whatsapp_api.send_message.assert_called_once()

    def test_multiple_consecutive_calls(self, usecase, sample_parameters, mock_whatsapp_api):
        """Testa múltiplas chamadas consecutivas do usecase."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(mock_whatsapp_api)
        ):
            # Act
            result1 = usecase(sample_parameters)
            result2 = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result1, SuccessReturn)
            assert isinstance(result2, SuccessReturn)
            
            # Verifica se os métodos foram chamados para ambas as execuções
            assert mock_whatsapp_api.typing.call_count == 4  # 2 calls per execution
            assert mock_whatsapp_api.send_message.call_count == 2
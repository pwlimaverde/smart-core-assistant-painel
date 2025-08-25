"""Testes para o SetEnvironRemoteUseCase."""

import pytest
from unittest.mock import MagicMock
from py_return_success_or_error import EMPTY, ErrorReturn, SuccessReturn

from smart_core_assistant_painel.modules.services.features.set_environ_remote.domain.usecase.set_environ_remote_usecase import SetEnvironRemoteUseCase
from smart_core_assistant_painel.modules.services.utils.parameters import SetEnvironRemoteParameters
from smart_core_assistant_painel.modules.services.utils.erros import SetEnvironRemoteError


class TestSetEnvironRemoteUseCase:
    """Testes para a classe SetEnvironRemoteUseCase."""

    def setup_method(self):
        """Configuração inicial para cada teste."""
        self.mock_datasource = MagicMock()
        self.usecase = SetEnvironRemoteUseCase(datasource=self.mock_datasource)
        
        # Mock da função _resultDatasource
        self.usecase._resultDatasource = MagicMock()
        
        # Parâmetros de teste
        self.test_error = SetEnvironRemoteError(message="Erro de teste")
        self.parameters = SetEnvironRemoteParameters(
            config_mapping={"key": "value"}, 
            error=self.test_error
        )

    def test_call_success_return(self):
        """Testa o caso de sucesso quando o datasource retorna SuccessReturn."""
        # Configura o mock para retornar sucesso
        self.usecase._resultDatasource.return_value = SuccessReturn(None)
        
        result = self.usecase(self.parameters)
        
        assert isinstance(result, SuccessReturn)
        assert result.result == EMPTY
        self.usecase._resultDatasource.assert_called_once_with(
            parameters=self.parameters, 
            datasource=self.mock_datasource
        )

    def test_call_error_return(self):
        """Testa quando o datasource retorna ErrorReturn."""
        # Configura o mock para retornar erro
        mock_error = SetEnvironRemoteError(message="Erro do datasource")
        error_return = ErrorReturn(mock_error)
        self.usecase._resultDatasource.return_value = error_return
        
        result = self.usecase(self.parameters)
        
        assert isinstance(result, ErrorReturn)
        assert result.result == mock_error

    def test_call_unexpected_return_type(self):
        """Testa quando o datasource retorna um tipo inesperado."""
        # Configura o mock para retornar algo que não é Success nem Error
        self.usecase._resultDatasource.return_value = "unexpected_type"
        
        result = self.usecase(self.parameters)
        
        assert isinstance(result, ErrorReturn)
        assert result.result == self.test_error

    def test_call_exception_handling(self):
        """Testa o tratamento de exceções durante a execução."""
        # Configura o mock para levantar exceção
        self.usecase._resultDatasource.side_effect = Exception("Erro inesperado")
        
        result = self.usecase(self.parameters)
        
        assert isinstance(result, ErrorReturn)
        assert "Erro inesperado" in result.result.message
        assert "Erro de teste - Exception:" in result.result.message
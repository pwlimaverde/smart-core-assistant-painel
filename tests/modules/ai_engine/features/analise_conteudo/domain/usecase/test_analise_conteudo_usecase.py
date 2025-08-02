import pytest
from unittest.mock import Mock, patch
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.domain.usecase.analise_conteudo_usecase import (
    AnaliseConteudoUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LlmParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import LlmError


class TestAnaliseConteudoUseCase:
    """Testes para a classe AnaliseConteudoUseCase."""

    @pytest.fixture
    def mock_datasource(self):
        """Fixture para criar um mock do datasource."""
        return Mock()

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        return LlmParameters(
            llm_class=Mock,
            model="test-model",
            extra_params={"temperature": 0.7},
            prompt_system="Sistema de teste",
            prompt_human="Humano de teste",
            context="Contexto de teste",
            error=LlmError("Erro de teste LLM"),
        )

    @pytest.fixture
    def usecase(self, mock_datasource):
        """Fixture para criar uma instância do usecase."""
        return AnaliseConteudoUseCase(mock_datasource)

    def test_call_success_case(self, usecase, sample_parameters):
        """Testa o caso de sucesso da chamada do usecase."""
        # Arrange
        expected_result = "Análise de conteúdo realizada com sucesso"
        
        # Mock do _resultDatasource para retornar SuccessReturn
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(expected_result)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert result.result == expected_result

    def test_call_error_from_datasource(self, usecase, sample_parameters):
        """Testa o caso de erro retornado pelo datasource."""
        # Arrange
        error_message = "Erro no datasource"
        
        # Mock do _resultDatasource para retornar ErrorReturn
        with patch.object(
            usecase, '_resultDatasource', return_value=ErrorReturn(error_message)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, ErrorReturn)
            assert result.result == error_message

    def test_parameters_validation(self, mock_datasource):
        """Testa a validação dos parâmetros de entrada."""
        # Arrange
        usecase = AnaliseConteudoUseCase(mock_datasource)
        invalid_params = None
        
        # Mock do _resultDatasource para simular comportamento real
        with patch.object(
            usecase, '_resultDatasource', side_effect=AttributeError("'NoneType' object has no attribute")
        ):
            # Act & Assert
            # Quando parameters é None, o _resultDatasource tentará acessar atributos
            # de None, causando AttributeError
            with pytest.raises(AttributeError):
                usecase(invalid_params)

    def test_datasource_call_parameters(self, usecase, sample_parameters):
        """Testa se o datasource é chamado com os parâmetros corretos."""
        # Arrange
        expected_result = "Resultado do datasource"
        
        # Mock do _resultDatasource
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(expected_result)
        ) as mock_result_datasource:
            # Act
            usecase(sample_parameters)
            
            # Assert
            mock_result_datasource.assert_called_once_with(
                parameters=sample_parameters, datasource=usecase._datasource
            )

    def test_empty_result(self, usecase, sample_parameters):
        """Testa o comportamento com resultado vazio."""
        # Arrange
        empty_result = ""
        
        # Mock do _resultDatasource para retornar string vazia
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(empty_result)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert result.result == empty_result

    def test_large_content_analysis(self, usecase, sample_parameters):
        """Testa a análise de conteúdo grande."""
        # Arrange
        large_content = "Conteúdo muito grande " * 1000
        
        # Mock do _resultDatasource
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(large_content)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert result.result == large_content
            assert len(result.result) > 1000
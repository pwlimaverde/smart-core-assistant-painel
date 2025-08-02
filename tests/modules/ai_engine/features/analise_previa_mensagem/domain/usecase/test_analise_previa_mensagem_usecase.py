import pytest
from unittest.mock import Mock, patch
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.usecase.analise_previa_mensagem_usecase import (
    AnalisePreviaMensagemUsecase,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.interface.analise_previa_mensagem import (
    AnalisePreviaMensagem,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
    LlmParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import APMTuple
from smart_core_assistant_painel.modules.ai_engine.utils.erros import LlmError


class TestAnalisePreviaMensagemUsecase:
    """Testes para a classe AnalisePreviaMensagemUsecase."""

    @pytest.fixture
    def mock_datasource(self):
        """Fixture para criar um mock do datasource."""
        return Mock()

    @pytest.fixture
    def mock_analise_previa_mensagem(self):
        """Fixture para criar um mock de AnalisePreviaMensagem."""
        mock_analise = Mock(spec=AnalisePreviaMensagem)
        mock_analise.intent = [{"saudacao": "ola"}, {"pergunta": "como_esta"}]
        mock_analise.entities = [{"pessoa": "João"}, {"local": "São Paulo"}]
        return mock_analise

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        llm_params = LlmParameters(
            llm_class=Mock,
            model="test-model",
            extra_params={"temperature": 0.7},
            prompt_system="Sistema de teste",
            prompt_human="Humano de teste",
            context="Contexto de teste",
            error=LlmError("Erro de teste LLM"),
        )
        
        return AnalisePreviaMensagemParameters(
            historico_atendimento={"mensagens": ["Olá", "Como você está?"]},
            valid_intent_types='[{"type": "saudacao"}, {"type": "pergunta"}]',
            valid_entity_types='[{"type": "pessoa"}, {"type": "local"}]',
            llm_parameters=llm_params,
            error=LlmError("Erro de teste"),
        )

    @pytest.fixture
    def usecase(self, mock_datasource):
        """Fixture para criar uma instância do usecase."""
        return AnalisePreviaMensagemUsecase(mock_datasource)

    def test_call_success_case(self, usecase, sample_parameters, mock_analise_previa_mensagem):
        """Testa o caso de sucesso do método __call__."""
        # Arrange
        expected_tuple = APMTuple(
            intent_types=mock_analise_previa_mensagem.intent,
            entity_types=mock_analise_previa_mensagem.entities,
        )
        
        # Mock do método _resultDatasource para retornar sucesso
        with patch.object(
            usecase, '_resultDatasource', 
            return_value=SuccessReturn(mock_analise_previa_mensagem)
        ):
            # Act
            result = usecase(sample_parameters)

            # Assert
            assert isinstance(result, SuccessReturn)
            assert isinstance(result.result, APMTuple)
            assert result.result.intent_types == expected_tuple.intent_types
            assert result.result.entity_types == expected_tuple.entity_types

    def test_call_error_from_datasource(self, usecase, sample_parameters):
        """Testa o caso de erro retornado pelo datasource."""
        # Arrange
        error_message = "Erro no datasource"
        error_return = ErrorReturn(LlmError(error_message))
        
        # Mock do método _resultDatasource para retornar erro
        with patch.object(usecase, '_resultDatasource', return_value=error_return):
            # Act
            result = usecase(sample_parameters)

            # Assert
            assert isinstance(result, ErrorReturn)
            assert str(result.result) == f"LlmError - {error_message}"

    def test_call_unexpected_return_type(self, usecase, sample_parameters):
        """Testa o caso de tipo de retorno inesperado do datasource."""
        # Arrange
        unexpected_return = "tipo_inesperado"
        
        # Mock do método _resultDatasource para retornar tipo inesperado
        with patch.object(usecase, '_resultDatasource', return_value=unexpected_return):
            # Act
            result = usecase(sample_parameters)

            # Assert
            assert isinstance(result, ErrorReturn)
            assert result.result == sample_parameters.error

    def test_call_exception_handling(self, usecase, sample_parameters):
        """Testa o tratamento de exceções no método __call__."""
        # Arrange
        exception_message = "Erro inesperado"
        
        # Mock do método _resultDatasource para lançar exceção
        with patch.object(
            usecase, '_resultDatasource', 
            side_effect=Exception(exception_message)
        ):
            # Act
            result = usecase(sample_parameters)

            # Assert
            assert isinstance(result, ErrorReturn)
            assert exception_message in str(result.result.message)
            assert sample_parameters.error.message in str(result.result.message)

    def test_apm_tuple_creation(self, usecase, sample_parameters, mock_analise_previa_mensagem):
        """Testa a criação correta do APMTuple."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', 
            return_value=SuccessReturn(mock_analise_previa_mensagem)
        ):
            # Act
            result = usecase(sample_parameters)

            # Assert
            assert isinstance(result, SuccessReturn)
            tuple_result = result.result
            assert isinstance(tuple_result, APMTuple)
            assert hasattr(tuple_result, 'intent_types')
            assert hasattr(tuple_result, 'entity_types')
            assert tuple_result.intent_types == mock_analise_previa_mensagem.intent
            assert tuple_result.entity_types == mock_analise_previa_mensagem.entities

    def test_parameters_validation(self, mock_datasource):
        """Testa a validação dos parâmetros de entrada."""
        # Arrange
        usecase = AnalisePreviaMensagemUsecase(mock_datasource)
        invalid_params = None
        
        # Mock _resultDatasource para lançar uma exceção que force o usecase
        # a tentar acessar parameters.error na linha 42
        mock_datasource.return_value = Exception("Erro simulado")
        
        # Act & Assert
        # Quando uma exceção ocorre no _resultDatasource, o usecase tenta
        # acessar parameters.error na linha 42, causando AttributeError
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'error'"):
            usecase(invalid_params)

    def test_datasource_call_parameters(self, usecase, sample_parameters, mock_analise_previa_mensagem):
        """Testa se o datasource é chamado com os parâmetros corretos."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', 
            return_value=SuccessReturn(mock_analise_previa_mensagem)
        ) as mock_result_datasource:
            # Act
            usecase(sample_parameters)

            # Assert
            mock_result_datasource.assert_called_once_with(
                parameters=sample_parameters, 
                datasource=usecase._datasource
            )

    def test_empty_intent_and_entities(self, usecase, sample_parameters):
        """Testa o comportamento com intent e entities vazios."""
        # Arrange
        mock_analise = Mock(spec=AnalisePreviaMensagem)
        mock_analise.intent = []
        mock_analise.entities = []
        
        with patch.object(
            usecase, '_resultDatasource', 
            return_value=SuccessReturn(mock_analise)
        ):
            # Act
            result = usecase(sample_parameters)

            # Assert
            assert isinstance(result, SuccessReturn)
            assert result.result.intent_types == []
            assert result.result.entity_types == []

    def test_complex_intent_and_entities(self, usecase, sample_parameters):
        """Testa o comportamento com intent e entities complexos."""
        # Arrange
        mock_analise = Mock(spec=AnalisePreviaMensagem)
        mock_analise.intent = [
            {"saudacao": "bom dia"},
            {"despedida": "tchau"},
            {"pergunta": "como funciona"}
        ]
        mock_analise.entities = [
            {"pessoa": "Maria Silva"},
            {"local": "Rio de Janeiro"},
            {"data": "2024-01-15"},
            {"produto": "smartphone"}
        ]
        
        with patch.object(
            usecase, '_resultDatasource', 
            return_value=SuccessReturn(mock_analise)
        ):
            # Act
            result = usecase(sample_parameters)

            # Assert
            assert isinstance(result, SuccessReturn)
            assert len(result.result.intent_types) == 3
            assert len(result.result.entity_types) == 4
            assert result.result.intent_types == mock_analise.intent
            assert result.result.entity_types == mock_analise.entities
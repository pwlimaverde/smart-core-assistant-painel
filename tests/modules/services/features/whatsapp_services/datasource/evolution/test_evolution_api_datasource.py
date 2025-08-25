"""Testes para EvolutionAPIDatasource."""

import pytest
from unittest.mock import Mock, patch

from py_return_success_or_error import NoParams

from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_api_datasource import (
    EvolutionAPIDatasource,
)
from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.interface.whatsapp_service import (
    WhatsAppService,
)


class TestEvolutionAPIDatasource:
    """Testes para a classe EvolutionAPIDatasource."""

    @pytest.fixture
    def datasource(self):
        """Fixture para criar uma instância do datasource."""
        return EvolutionAPIDatasource()

    @pytest.fixture
    def no_params(self):
        """Fixture para criar NoParams."""
        return NoParams()

    def test_datasource_inheritance(self, datasource):
        """Testa se o datasource herda corretamente da classe base."""
        # Verifica se é uma instância válida com o método esperado
        assert hasattr(datasource, '__call__')
        assert callable(datasource)

    def test_call_returns_evolution_whatsapp_service(self, datasource, no_params):
        """Testa se o datasource retorna uma instância de EvolutionWhatsAppService."""
        # Act
        result = datasource(no_params)
        
        # Assert
        assert isinstance(result, WhatsAppService)
        # Verifica se é especificamente uma instância de EvolutionWhatsAppService
        from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_whatsapp_service import (
            EvolutionWhatsAppService,
        )
        assert isinstance(result, EvolutionWhatsAppService)

    @patch('smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_api_datasource.EvolutionWhatsAppService')
    def test_call_with_mock_service(self, mock_evolution_service, datasource, no_params):
        """Testa se o datasource chama o construtor do EvolutionWhatsAppService."""
        # Arrange
        mock_instance = Mock()
        mock_evolution_service.return_value = mock_instance
        
        # Act
        result = datasource(no_params)
        
        # Assert
        mock_evolution_service.assert_called_once()
        assert result == mock_instance

    @patch('smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_api_datasource.EvolutionWhatsAppService')
    def test_call_handles_exception(self, mock_evolution_service, datasource, no_params):
        """Testa se o datasource lida com exceções do EvolutionWhatsAppService."""
        # Arrange
        mock_evolution_service.side_effect = Exception("Erro no serviço")
        
        # Act & Assert
        with pytest.raises(TypeError, match="Erro ao carregar serviço Evolution: Erro no serviço"):
            datasource(no_params)

    @patch('smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_api_datasource.EvolutionWhatsAppService')
    def test_call_handles_specific_exception_types(self, mock_evolution_service, datasource, no_params):
        """Testa o tratamento de diferentes tipos de exceções."""
        # Arrange - RuntimeError
        mock_evolution_service.side_effect = RuntimeError("Erro de runtime")
        
        # Act & Assert
        with pytest.raises(TypeError, match="Erro ao carregar serviço Evolution: Erro de runtime"):
            datasource(no_params)
        
        # Arrange - ValueError  
        mock_evolution_service.side_effect = ValueError("Valor inválido")
        
        # Act & Assert
        with pytest.raises(TypeError, match="Erro ao carregar serviço Evolution: Valor inválido"):
            datasource(no_params)

    def test_multiple_calls_return_same_instance_due_to_singleton(self, datasource, no_params):
        """Testa se múltiplas chamadas retornam a mesma instância (devido ao Singleton)."""
        # Act
        result1 = datasource(no_params)
        result2 = datasource(no_params)
        
        # Assert
        # Devido ao padrão Singleton do EvolutionWhatsAppService, 
        # ambas as instâncias devem ser iguais
        assert result1 is result2

    def test_call_signature_matches_interface(self, datasource):
        """Testa se a assinatura do método __call__ está correta."""
        # Verifica se o método aceita NoParams
        import inspect
        sig = inspect.signature(datasource.__call__)
        params = list(sig.parameters.keys())
        
        assert len(params) == 1  # Apenas 'parameters'
        assert 'parameters' in params

    def test_docstring_and_metadata(self, datasource):
        """Testa se a documentação e metadados estão presentes."""
        assert hasattr(datasource, '__call__')
        assert datasource.__call__.__doc__ is not None
        assert "Inicializa e retorna uma instância do serviço WhatsApp" in datasource.__call__.__doc__

    def test_datasource_is_callable(self, datasource):
        """Testa se o datasource é chamável."""
        assert callable(datasource)

    @patch('smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_api_datasource.EvolutionWhatsAppService')
    def test_exception_message_format(self, mock_evolution_service, datasource, no_params):
        """Testa o formato da mensagem de exceção."""
        # Arrange
        original_error = "Specific error message"
        mock_evolution_service.side_effect = Exception(original_error)
        
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            datasource(no_params)
        
        error_message = str(exc_info.value)
        assert "Erro ao carregar serviço Evolution:" in error_message
        assert original_error in error_message
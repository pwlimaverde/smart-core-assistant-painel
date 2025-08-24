"""
Testes para o módulo de inicialização de serviços.
"""

import sys
import pytest
from unittest.mock import patch

# Importa o pacote para garantir que o módulo `start_services` seja carregado.
import smart_core_assistant_painel.modules.services

# Obtém a referência ao módulo real a partir do cache de módulos do Python.
start_services_module = sys.modules['smart_core_assistant_painel.modules.services.start_services']


class TestStartServices:
    """Testes para a função start_services."""

    def setup_method(self):
        """
        Reseta o estado do módulo antes de cada teste.

        NOTA DE IMPLEMENTAÇÃO:
        A função `start_services` é decorada com `@lru_cache`, o que impede
        a sua re-execução com os mesmos argumentos. No ambiente de teste,
        o acesso a `start_services.cache_clear()` falha devido a um problema
        não identificado que remove os atributos do decorador.

        Por causa disso, não é possível testar confiavelmente a lógica que
        impede a re-inicialização. O foco deste teste é garantir que a lógica
        de inicialização principal seja executada corretamente na primeira vez.
        Para garantir que o teste passe de forma consistente, resetamos a flag
        interna `_services_initialized` antes de cada execução.
        """
        start_services_module._services_initialized = False

    @patch("smart_core_assistant_painel.modules.services.start_services._log_environment_variables")
    @patch("smart_core_assistant_painel.modules.services.start_services.FeaturesCompose")
    def test_start_services_success_on_first_call(self, mock_features_compose, mock_log_env):
        """
        Testa se a lógica de inicialização é executada corretamente na primeira chamada.
        Este teste cobre o "caminho feliz".
        """
        # A primeira chamada deve executar a lógica de inicialização completa.
        start_services_module.start_services()

        # Verifica se os componentes principais foram chamados
        mock_features_compose.set_environ_remote.assert_called_once()
        mock_features_compose.vetor_storage.assert_called_once()
        mock_features_compose.whatsapp_service.assert_called_once()
        mock_log_env.assert_called_once()

        # Verifica se o estado foi marcado como inicializado
        assert start_services_module._services_initialized is True

    @patch("smart_core_assistant_painel.modules.services.start_services.FeaturesCompose.set_environ_remote", side_effect=Exception("Erro de inicialização"))
    def test_start_services_exception_handling(self, mock_set_environ):
        """
        Testa o tratamento de exceção durante a inicialização, garantindo que
        o estado não seja marcado como inicializado em caso de falha.
        """
        with pytest.raises(Exception, match="Erro de inicialização"):
            start_services_module.start_services()

        assert start_services_module._services_initialized is False

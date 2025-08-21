import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import asyncio

from smart_core_assistant_painel.modules.services.features.set_environ_remote.datasource.set_environ_remote_firebase_datasource import SetEnvironRemoteFirebaseDatasource
from smart_core_assistant_painel.modules.services.utils.parameters import SetEnvironRemoteParameters
from smart_core_assistant_painel.modules.services.utils.erros import SetEnvironRemoteError

@pytest.fixture
def mock_firebase_admin():
    with patch('smart_core_assistant_painel.modules.services.features.set_environ_remote.datasource.set_environ_remote_firebase_datasource.firebase_admin') as mock:
        yield mock

@pytest.fixture
def mock_remote_config():
    with patch('smart_core_assistant_painel.modules.services.features.set_environ_remote.datasource.set_environ_remote_firebase_datasource.remote_config') as mock:
        # Mock the template and its evaluation
        mock_template = MagicMock()
        mock_config = MagicMock()
        mock_config.get_string.side_effect = lambda key: f"value_for_{key}"
        mock_template.evaluate.return_value = mock_config
        mock_template.load = AsyncMock() # Mock the async load method
        mock.init_server_template.return_value = mock_template
        yield mock

class TestSetEnvironRemoteFirebaseDatasource:

    def test_load_remote_config_values_success_already_initialized(self, mock_firebase_admin, mock_remote_config):
        """
        Testa o carregamento bem-sucedido quando o Firebase já está inicializado.
        """
        config_mapping = {"REMOTE_KEY_1": "ENV_VAR_1", "REMOTE_KEY_2": "ENV_VAR_2"}

        # Simula que o app já existe
        mock_firebase_admin.get_app.return_value = True

        asyncio.run(SetEnvironRemoteFirebaseDatasource._load_remote_config_values(config_mapping))

        # Verifica se o get_app foi chamado, mas o initialize_app não
        mock_firebase_admin.get_app.assert_called_once()
        mock_firebase_admin.initialize_app.assert_not_called()

        # Verifica se as variáveis de ambiente foram definidas
        assert os.environ["ENV_VAR_1"] == "value_for_REMOTE_KEY_1"
        assert os.environ["ENV_VAR_2"] == "value_for_REMOTE_KEY_2"

    def test_load_remote_config_values_success_needs_initialization(self, mock_firebase_admin, mock_remote_config):
        """
        Testa o carregamento bem-sucedido quando o Firebase precisa ser inicializado.
        """
        config_mapping = {"REMOTE_KEY_3": "ENV_VAR_3"}

        # Simula que o app não existe, forçando a inicialização
        mock_firebase_admin.get_app.side_effect = ValueError("App not initialized")

        asyncio.run(SetEnvironRemoteFirebaseDatasource._load_remote_config_values(config_mapping))

        # Verifica se tentou obter o app e depois o inicializou
        mock_firebase_admin.get_app.assert_called_once()
        mock_firebase_admin.initialize_app.assert_called_once()

        # Verifica se a variável de ambiente foi definida
        assert os.environ["ENV_VAR_3"] == "value_for_REMOTE_KEY_3"

    def test_load_remote_config_values_handles_empty_value(self, mock_firebase_admin, mock_remote_config):
        """
        Testa que a variável de ambiente não é definida se o valor remoto for vazio.
        """
        config_mapping = {"EMPTY_KEY": "EMPTY_ENV_VAR"}

        # Configura o mock para retornar um valor vazio
        mock_config = mock_remote_config.init_server_template.return_value.evaluate.return_value
        mock_config.get_string.side_effect = None
        mock_config.get_string.return_value = ""

        # Limpa a variável de ambiente antes do teste, se existir
        if "EMPTY_ENV_VAR" in os.environ:
            del os.environ["EMPTY_ENV_VAR"]

        asyncio.run(SetEnvironRemoteFirebaseDatasource._load_remote_config_values(config_mapping))

        # Verifica que a variável de ambiente não foi definida
        assert "EMPTY_ENV_VAR" not in os.environ

    def test_load_remote_config_values_raises_type_error_on_get_string_failure(self, mock_firebase_admin, mock_remote_config):
        """
        Testa se um TypeError é levantado se get_string falhar.
        """
        config_mapping = {"FAIL_KEY": "FAIL_ENV_VAR"}

        # Configura o mock para levantar uma exceção
        mock_config = mock_remote_config.init_server_template.return_value.evaluate.return_value
        mock_config.get_string.side_effect = Exception("Firebase error")

        with pytest.raises(TypeError, match="Erro ao carregar variável de ambiente FAIL_KEY"):
            asyncio.run(SetEnvironRemoteFirebaseDatasource._load_remote_config_values(config_mapping))

    def test_call_method_invokes_async_load(self):
        """
        Testa se o método __call__ executa a função assíncrona corretamente.
        """
        datasource = SetEnvironRemoteFirebaseDatasource()
        params = SetEnvironRemoteParameters(config_mapping={"A": "B"}, error=SetEnvironRemoteError)

        with patch.object(datasource, '_load_remote_config_values', new_callable=AsyncMock) as mock_async_load:
            result = datasource(params)

            mock_async_load.assert_awaited_once_with({"A": "B"})
            assert result is True

    def test_call_method_handles_exception(self):
        """
        Testa se o método __call__ lida com exceções da função assíncrona.
        """
        datasource = SetEnvironRemoteFirebaseDatasource()
        params = SetEnvironRemoteParameters(config_mapping={}, error=SetEnvironRemoteError)

        with patch.object(datasource, '_load_remote_config_values', new_callable=AsyncMock) as mock_async_load:
            mock_async_load.side_effect = Exception("Async error")

            with pytest.raises(TypeError, match="Erro ao carregar variáveis de ambiente: Async error"):
                datasource(params)

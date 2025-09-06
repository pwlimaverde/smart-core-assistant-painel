"""Testes para o FirebaseInitUseCase."""

import pytest
from unittest.mock import patch, MagicMock

from smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase import FirebaseInitUseCase
from smart_core_assistant_painel.modules.initial_loading.utils.parameters import FirebaseInitParameters
from smart_core_assistant_painel.modules.initial_loading.utils.erros import FirebaseInitError
from py_return_success_or_error import EMPTY, ErrorReturn, SuccessReturn


class TestFirebaseInitUseCase:
    """Testes para a classe FirebaseInitUseCase."""

    def setup_method(self):
        """Configuração inicial para cada teste."""
        self.usecase = FirebaseInitUseCase()
        self.error = FirebaseInitError(message="Erro de teste no Firebase")
        self.parameters = FirebaseInitParameters(error=self.error)

    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.load_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.find_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.firebase_admin')
    def test_firebase_init_success_app_already_exists(self, mock_firebase_admin, mock_find_dotenv, mock_load_dotenv):
        """Testa inicialização bem-sucedida quando o app Firebase já existe."""
        # Configura os mocks
        mock_find_dotenv.return_value = ".env"
        mock_firebase_admin.get_app.return_value = MagicMock()  # Simula que o app já existe
        
        # Executa o caso de uso
        result = self.usecase(self.parameters)
        
        # Verifica os resultados
        assert isinstance(result, SuccessReturn)
        assert result.result == EMPTY
        
        # Verifica se as funções foram chamadas
        mock_find_dotenv.assert_called_once()
        mock_load_dotenv.assert_called_once_with(".env")
        mock_firebase_admin.get_app.assert_called_once()
        mock_firebase_admin.initialize_app.assert_not_called()  # Não deve chamar initialize

    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.load_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.find_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.firebase_admin')
    def test_firebase_init_success_needs_initialization(self, mock_firebase_admin, mock_find_dotenv, mock_load_dotenv):
        """Testa inicialização bem-sucedida quando precisa inicializar o app Firebase."""
        # Configura os mocks
        mock_find_dotenv.return_value = ".env"
        mock_firebase_admin.get_app.side_effect = ValueError("App não encontrado")
        
        # Executa o caso de uso
        result = self.usecase(self.parameters)
        
        # Verifica os resultados
        assert isinstance(result, SuccessReturn)
        assert result.result == EMPTY
        
        # Verifica se as funções foram chamadas
        mock_find_dotenv.assert_called_once()
        mock_load_dotenv.assert_called_once_with(".env")
        mock_firebase_admin.get_app.assert_called_once()
        mock_firebase_admin.initialize_app.assert_called_once()  # Deve chamar initialize

    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.load_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.find_dotenv')
    def test_firebase_init_error_on_find_dotenv(self, mock_find_dotenv, mock_load_dotenv):
        """Testa tratamento de erro quando find_dotenv falha."""
        # Configura o mock para levantar exceção
        mock_find_dotenv.side_effect = Exception("Arquivo .env não encontrado")
        
        # Executa o caso de uso
        result = self.usecase(self.parameters)
        
        # Verifica os resultados
        assert isinstance(result, ErrorReturn)
        assert "Arquivo .env não encontrado" in result.result.message
        assert "Erro de teste no Firebase - Exception:" in result.result.message

    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.load_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.find_dotenv')
    def test_firebase_init_error_on_load_dotenv(self, mock_find_dotenv, mock_load_dotenv):
        """Testa tratamento de erro quando load_dotenv falha."""
        # Configura os mocks
        mock_find_dotenv.return_value = ".env"
        mock_load_dotenv.side_effect = Exception("Erro ao carregar .env")
        
        # Executa o caso de uso
        result = self.usecase(self.parameters)
        
        # Verifica os resultados
        assert isinstance(result, ErrorReturn)
        assert "Erro ao carregar .env" in result.result.message

    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.load_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.find_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.firebase_admin')
    def test_firebase_init_error_on_initialize_app(self, mock_firebase_admin, mock_find_dotenv, mock_load_dotenv):
        """Testa tratamento de erro quando initialize_app falha."""
        # Configura os mocks
        mock_find_dotenv.return_value = ".env"
        mock_firebase_admin.get_app.side_effect = ValueError("App não encontrado")
        mock_firebase_admin.initialize_app.side_effect = Exception("Erro na inicialização do Firebase")
        
        # Executa o caso de uso
        result = self.usecase(self.parameters)
        
        # Verifica os resultados
        assert isinstance(result, ErrorReturn)
        assert "Erro na inicialização do Firebase" in result.result.message

    def test_firebase_init_different_error_types(self):
        """Testa com diferentes tipos de erro no parâmetro."""
        # Testa com mensagem customizada
        custom_error = FirebaseInitError(message="Erro customizado Firebase")
        custom_parameters = FirebaseInitParameters(error=custom_error)
        
        with patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.find_dotenv') as mock_find:
            mock_find.side_effect = Exception("Teste de erro customizado")
            
            result = self.usecase(custom_parameters)
            
            assert isinstance(result, ErrorReturn)
            assert "Erro customizado Firebase - Exception:" in result.result.message
            assert "Teste de erro customizado" in result.result.message

    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.load_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.find_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.firebase_admin')
    def test_firebase_init_multiple_get_app_calls(self, mock_firebase_admin, mock_find_dotenv, mock_load_dotenv):
        """Testa comportamento com múltiplas chamadas para get_app."""
        # Configura os mocks
        mock_find_dotenv.return_value = ".env"
        
        # Primeira chamada: app não existe, segunda chamada: app existe
        mock_firebase_admin.get_app.side_effect = [ValueError("App não encontrado"), MagicMock()]
        
        # Executa o caso de uso duas vezes
        result1 = self.usecase(self.parameters)
        result2 = self.usecase(self.parameters)
        
        # Ambos devem ter sucesso
        assert isinstance(result1, SuccessReturn)
        assert isinstance(result2, SuccessReturn)
        
        # Verifica que initialize_app foi chamado apenas uma vez
        assert mock_firebase_admin.initialize_app.call_count == 1
        assert mock_firebase_admin.get_app.call_count == 2

    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.load_dotenv')
    @patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.find_dotenv')
    def test_firebase_init_with_none_dotenv_result(self, mock_find_dotenv, mock_load_dotenv):
        """Testa quando find_dotenv retorna None."""
        # Configura o mock para retornar None
        mock_find_dotenv.return_value = None
        
        with patch('smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase.firebase_admin') as mock_firebase_admin:
            mock_firebase_admin.get_app.return_value = MagicMock()
            
            # Executa o caso de uso
            result = self.usecase(self.parameters)
            
            # Deve ter sucesso mesmo com dotenv None
            assert isinstance(result, SuccessReturn)
            mock_load_dotenv.assert_called_once_with(None)
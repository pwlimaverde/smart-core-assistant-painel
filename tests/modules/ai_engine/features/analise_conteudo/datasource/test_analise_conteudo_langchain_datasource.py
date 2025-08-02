import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage

from smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource import (
    AnaliseConteudoLangchainDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LlmParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import LlmError


class TestAnaliseConteudoLangchainDatasource:
    """Testes para a classe AnaliseConteudoLangchainDatasource."""

    @pytest.fixture
    def datasource(self):
        """Fixture para criar uma instância do datasource."""
        return AnaliseConteudoLangchainDatasource()

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        mock_llm = Mock()
        return LlmParameters(
            llm_class=Mock,
            model="test-model",
            extra_params={"temperature": 0.7},
            prompt_system="Você é um assistente útil.",
            prompt_human="Analise o seguinte conteúdo",
            context="Este é um texto de exemplo para análise.",
            error=LlmError("Erro de teste LLM"),
        )

    @pytest.fixture
    def mock_llm_response(self):
        """Fixture para criar uma resposta mock do LLM."""
        mock_response = Mock(spec=AIMessage)
        mock_response.content = "Análise do conteúdo: O texto apresenta informações relevantes."
        return mock_response

    def test_call_success_case(self, datasource, mock_llm_response):
        """Testa o caso de sucesso da chamada do datasource."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_llm_response
        
        # Criar um mock completo dos parâmetros
        mock_parameters = Mock()
        mock_parameters.create_llm.return_value = mock_llm
        mock_parameters.prompt_system = "Você é um assistente útil."
        mock_parameters.prompt_human = "Analise o seguinte conteúdo"
        mock_parameters.context = "Este é um texto de exemplo para análise."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = datasource(mock_parameters)
            
            # Assert
            assert result == "Análise do conteúdo: O texto apresenta informações relevantes."
            mock_chain.invoke.assert_called_once()

    def test_call_with_think_tags(self, datasource):
        """Testa o processamento de resposta com tags <think>."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock(spec=AIMessage)
        mock_response.content = "<think>Pensando sobre o conteúdo...</think>Análise final do conteúdo."
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock completo dos parâmetros
        mock_parameters = Mock()
        mock_parameters.create_llm.return_value = mock_llm
        mock_parameters.prompt_system = "Você é um assistente útil."
        mock_parameters.prompt_human = "Analise o seguinte conteúdo"
        mock_parameters.context = "Este é um texto de exemplo para análise."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = datasource(mock_parameters)
            
            # Assert
            assert result == "Análise final do conteúdo."
            assert "<think>" not in result
            assert "</think>" not in result

    def test_call_with_multiline_think_tags(self, datasource):
        """Testa o processamento de resposta com tags <think> multilinhas."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock(spec=AIMessage)
        mock_response.content = """<think>
Primeiro, vou analisar o contexto.
Depois, vou formular uma resposta.
</think>
Esta é a análise final do conteúdo fornecido."""
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock completo dos parâmetros
        mock_parameters = Mock()
        mock_parameters.create_llm.return_value = mock_llm
        mock_parameters.prompt_system = "Você é um assistente útil."
        mock_parameters.prompt_human = "Analise o seguinte conteúdo"
        mock_parameters.context = "Este é um texto de exemplo para análise."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = datasource(mock_parameters)
            
            # Assert
            assert result == "Esta é a análise final do conteúdo fornecido."
            assert "<think>" not in result
            assert "</think>" not in result

    def test_call_non_string_response_error(self, datasource):
        """Testa o erro quando a resposta não é uma string."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock(spec=AIMessage)
        mock_response.content = None  # Simula resposta não-string
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock completo dos parâmetros
        mock_parameters = Mock()
        mock_parameters.create_llm.return_value = mock_llm
        mock_parameters.prompt_system = "Você é um assistente útil."
        mock_parameters.prompt_human = "Analise o seguinte conteúdo"
        mock_parameters.context = "Este é um texto de exemplo para análise."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act & Assert
            with pytest.raises(TypeError, match="Resposta do LLM deve ser uma string, mas recebeu: <class 'NoneType'>"):
                datasource(mock_parameters)

    def test_prompt_template_creation(self, datasource, mock_llm_response):
        """Testa a criação do template de prompt."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_llm_response
        
        # Criar um mock completo dos parâmetros
        mock_parameters = Mock()
        mock_parameters.create_llm.return_value = mock_llm
        mock_parameters.prompt_system = "Você é um assistente útil."
        mock_parameters.prompt_human = "Analise o seguinte conteúdo"
        mock_parameters.context = "Este é um texto de exemplo para análise."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            datasource(mock_parameters)
            
            # Assert
            mock_template.from_messages.assert_called_once_with([
                ("system", mock_parameters.prompt_system),
                ("human", "{prompt_human}: {context}")
            ])

    def test_chain_invocation_parameters(self, datasource, mock_llm_response):
        """Testa os parâmetros passados para a invocação da chain."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_llm_response
        
        # Criar um mock completo dos parâmetros
        mock_parameters = Mock()
        mock_parameters.create_llm.return_value = mock_llm
        mock_parameters.prompt_system = "Você é um assistente útil."
        mock_parameters.prompt_human = "Analise o seguinte conteúdo"
        mock_parameters.context = "Este é um texto de exemplo para análise."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            datasource(mock_parameters)
            
            # Assert
            mock_chain.invoke.assert_called_once_with({
                "prompt_human": mock_parameters.prompt_human,
                "context": mock_parameters.context,
            })

    def test_empty_response_handling(self, datasource):
        """Testa o tratamento de resposta vazia."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock(spec=AIMessage)
        mock_response.content = ""
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock completo dos parâmetros
        mock_parameters = Mock()
        mock_parameters.create_llm.return_value = mock_llm
        mock_parameters.prompt_system = "Você é um assistente útil."
        mock_parameters.prompt_human = "Analise o seguinte conteúdo"
        mock_parameters.context = "Este é um texto de exemplo para análise."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = datasource(mock_parameters)
            
            # Assert
            assert result == ""

    def test_whitespace_response_handling(self, datasource):
        """Testa o tratamento de resposta com apenas espaços em branco."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock(spec=AIMessage)
        mock_response.content = "   \n\t   "
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock completo dos parâmetros
        mock_parameters = Mock()
        mock_parameters.create_llm.return_value = mock_llm
        mock_parameters.prompt_system = "Você é um assistente útil."
        mock_parameters.prompt_human = "Analise o seguinte conteúdo"
        mock_parameters.context = "Este é um texto de exemplo para análise."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = datasource(mock_parameters)
            
            # Assert
            assert result == ""
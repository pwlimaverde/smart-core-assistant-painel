"""Testes para AnaliseConteudoLangchainDatasource."""

import pytest
import re
from unittest.mock import Mock, patch

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
    def llm_parameters(self):
        """Fixture para criar parâmetros do LLM."""
        return LlmParameters(
            llm_class=Mock,  # Usando Mock como classe
            model="test-model",
            extra_params={"temperature": 0.7},
            prompt_system="System prompt for analysis",
            prompt_human="Human prompt for analysis",
            context="Text to be analyzed",
            error=LlmError,  # Usando a classe, não uma instância
        )

    def test_datasource_inheritance(self, datasource):
        """Testa se o datasource herda corretamente da classe base."""
        # Verifica se é uma instância válida com o método esperado
        assert hasattr(datasource, '__call__')
        assert callable(datasource)

    @patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate')
    def test_call_successful_string_response(self, mock_chat_prompt, datasource, llm_parameters):
        """Testa resposta bem-sucedida com string."""
        # Arrange
        mock_response = Mock()
        mock_response.content = "Resposta limpa do LLM"
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_messages = Mock()
        mock_messages.__or__ = Mock(return_value=mock_chain)
        mock_chat_prompt.from_messages.return_value = mock_messages
        
        # Act
        result = datasource(llm_parameters)
        
        # Assert
        assert result == "Resposta limpa do LLM"
        mock_chat_prompt.from_messages.assert_called_once()
        mock_chain.invoke.assert_called_once_with({
            "prompt_human": "Human prompt for analysis",
            "context": "Text to be analyzed",
        })

    @patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate')
    def test_call_with_think_tags_removal(self, mock_chat_prompt, datasource, llm_parameters):
        """Testa a remoção de tags <think> da resposta."""
        # Arrange
        mock_response = Mock()
        mock_response.content = "Início <think>pensamento interno</think> final <think>outro pensamento</think> resultado"
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_messages = Mock()
        mock_messages.__or__ = Mock(return_value=mock_chain)
        mock_chat_prompt.from_messages.return_value = mock_messages
        
        # Act
        result = datasource(llm_parameters)
        
        # Assert
        assert result == "Início  final  resultado"
        assert "<think>" not in result
        assert "</think>" not in result

    @patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate')
    def test_call_with_multiline_think_tags(self, mock_chat_prompt, datasource, llm_parameters):
        """Testa a remoção de tags <think> multilinhas."""
        # Arrange
        mock_response = Mock()
        mock_response.content = """Início
<think>
pensamento
multilinhas
</think>
final"""
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_messages = Mock()
        mock_messages.__or__ = Mock(return_value=mock_chain)
        mock_chat_prompt.from_messages.return_value = mock_messages
        
        # Act
        result = datasource(llm_parameters)
        
        # Assert
        expected = "Início\n\nfinal"
        assert result == expected

    @patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate')
    def test_call_with_whitespace_cleanup(self, mock_chat_prompt, datasource, llm_parameters):
        """Testa a limpeza de espaços em branco."""
        # Arrange
        mock_response = Mock()
        mock_response.content = "   \n  Resposta com espaços  \n  "
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_messages = Mock()
        mock_messages.__or__ = Mock(return_value=mock_chain)
        mock_chat_prompt.from_messages.return_value = mock_messages
        
        # Act
        result = datasource(llm_parameters)
        
        # Assert
        assert result == "Resposta com espaços"

    @patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate')
    def test_call_non_string_response_raises_type_error(self, mock_chat_prompt, datasource, llm_parameters):
        """Testa se TypeError é levantado para resposta não-string."""
        # Arrange
        mock_response = Mock()
        mock_response.content = {"key": "value"}  # Não é string
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_messages = Mock()
        mock_messages.__or__ = Mock(return_value=mock_chain)
        mock_chat_prompt.from_messages.return_value = mock_messages
        
        # Act & Assert
        with pytest.raises(TypeError, match="Resposta do LLM deve ser uma string, mas recebeu: <class 'dict'>"):
            datasource(llm_parameters)

    @patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate')
    def test_call_none_response_raises_type_error(self, mock_chat_prompt, datasource, llm_parameters):
        """Testa se TypeError é levantado para resposta None."""
        # Arrange
        mock_response = Mock()
        mock_response.content = None
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_messages = Mock()
        mock_messages.__or__ = Mock(return_value=mock_chain)
        mock_chat_prompt.from_messages.return_value = mock_messages
        
        # Act & Assert
        with pytest.raises(TypeError, match="Resposta do LLM deve ser uma string, mas recebeu: <class 'NoneType'>"):
            datasource(llm_parameters)

    @patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate')
    def test_prompt_template_construction(self, mock_chat_prompt, datasource, llm_parameters):
        """Testa se o template de prompt é construído corretamente."""
        # Arrange
        mock_response = Mock()
        mock_response.content = "Response"
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_messages = Mock()
        mock_messages.__or__ = Mock(return_value=mock_chain)
        mock_chat_prompt.from_messages.return_value = mock_messages
        
        # Act
        datasource(llm_parameters)
        
        # Assert
        mock_chat_prompt.from_messages.assert_called_once_with([
            ("system", "System prompt for analysis"),
            ("human", "{prompt_human}: {context}"),
        ])

    @patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate')
    def test_llm_creation_and_chaining(self, mock_chat_prompt, datasource, llm_parameters):
        """Testa se o LLM é criado e encadeado corretamente."""
        # Arrange
        mock_response = Mock()
        mock_response.content = "Response"
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_messages = Mock()
        mock_messages.__or__ = Mock(return_value=mock_chain)
        mock_chat_prompt.from_messages.return_value = mock_messages
        
        # Act
        datasource(llm_parameters)
        
        # Assert
        # Verifica se create_llm foi chamado
        assert llm_parameters.create_llm is not None
        # Verifica se o chaining foi feito
        mock_messages.__or__.assert_called_once()

    def test_empty_response_handling(self, datasource):
        """Testa o tratamento de resposta vazia."""
        # Arrange
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_chat_prompt:
            mock_response = Mock()
            mock_response.content = ""
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_response
            
            mock_messages = Mock()
            mock_messages.__or__ = Mock(return_value=mock_chain)
            mock_chat_prompt.from_messages.return_value = mock_messages
            
            llm_params = LlmParameters(
                llm_class=Mock,  # Usando Mock como classe
                model="test",
                extra_params={},
                prompt_system="sys",
                prompt_human="human",
                context="ctx",
                error=LlmError,  # Usando a classe
            )
            
            # Act
            result = datasource(llm_params)
            
            # Assert
            assert result == ""

    def test_complex_think_tags_scenario(self, datasource):
        """Testa cenário complexo com múltiplas tags <think> aninhadas."""
        # Arrange
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource.ChatPromptTemplate') as mock_chat_prompt:
            mock_response = Mock()
            mock_response.content = """
            Análise inicial
            <think>
            Vou analisar este texto:
            1. Primeiro ponto
            2. Segundo ponto
            </think>
            Conclusão da análise
            <think>Pensamento final</think>
            Resultado final
            """
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_response
            
            mock_messages = Mock()
            mock_messages.__or__ = Mock(return_value=mock_chain)
            mock_chat_prompt.from_messages.return_value = mock_messages
            
            mock_llm_class = Mock()
            llm_params = LlmParameters(
                llm_class=mock_llm_class,
                model="test",
                extra_params={},
                prompt_system="sys",
                prompt_human="human",
                context="ctx",
                error=LlmError("err"),
            )
            
            # Act
            result = datasource(llm_params)
            
            # Assert
            assert "<think>" not in result
            assert "</think>" not in result
            assert "Análise inicial" in result
            assert "Conclusão da análise" in result
            assert "Resultado final" in result

    def test_docstring_and_class_metadata(self, datasource):
        """Testa se a documentação está presente."""
        assert hasattr(datasource, '__call__')
        assert datasource.__call__.__doc__ is not None
        assert "Executa a chamada para o LLM" in datasource.__call__.__doc__
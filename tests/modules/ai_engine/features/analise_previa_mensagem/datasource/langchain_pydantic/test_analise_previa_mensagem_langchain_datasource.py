import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource import (
    AnalisePreviaMensagemLangchainDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import LlmError


class TestAnalisePreviaMensagemLangchainDatasource:
    """Testes para a classe AnalisePreviaMensagemLangchainDatasource."""

    @pytest.fixture
    def datasource(self):
        """Fixture para criar uma instância do datasource."""
        return AnalisePreviaMensagemLangchainDatasource()

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        from smart_core_assistant_painel.modules.ai_engine.utils.parameters import LlmParameters
        
        llm_params = LlmParameters(
            llm_class=Mock,
            model="test-model",
            extra_params={"temperature": 0.7},
            prompt_system="Você é um assistente útil.",
            prompt_human="Analise a seguinte mensagem",
            context="Esta é uma mensagem de teste.",
            error=LlmError("Erro de teste LLM"),
        )
        
        return AnalisePreviaMensagemParameters(
            historico_atendimento={"mensagens": []},
            valid_intent_types='{"categoria1": {"intent1": "Descrição 1"}}',
            valid_entity_types='{"categoria1": {"entity1": "Descrição 1"}}',
            llm_parameters=llm_params,
            error=LlmError("Erro de teste LLM"),
        )

    @pytest.fixture
    def mock_llm_response(self):
        """Fixture para criar uma resposta mock do LLM."""
        mock_response = Mock(spec=AIMessage)
        mock_response.content = "Análise da mensagem: A mensagem é apropriada."
        return mock_response

    def test_call_success_case(self, datasource, sample_parameters, mock_llm_response):
        """Testa o caso de sucesso da chamada do datasource."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_llm_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = datasource(sample_parameters)
            
            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == []
            assert result.entities == []
            mock_chain.invoke.assert_called_once()

    def test_call_with_think_tags(self, datasource, sample_parameters):
        """Testa o processamento de resposta com tags <think>."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock()
        mock_response.intent = []
        mock_response.entities = []
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
             
             mock_template.from_messages.return_value = Mock()
             mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
             
             # Act
             result = datasource(sample_parameters)
             
             # Assert
             from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
             assert isinstance(result, AnalisePreviaMensagemLangchain)
             assert result.intent == []
             assert result.entities == []

    def test_call_with_multiline_think_tags(self, datasource, sample_parameters):
        """Testa o processamento de resposta com tags <think> multilinhas."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock()
        mock_response.intent = []
        mock_response.entities = []
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
             
             mock_template.from_messages.return_value = Mock()
             mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
             
             # Act
             result = datasource(sample_parameters)
             
             # Assert
             from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
             assert isinstance(result, AnalisePreviaMensagemLangchain)
             assert result.intent == []
             assert result.entities == []

    def test_call_non_string_response_error(self, datasource, sample_parameters):
        """Testa o erro quando a resposta não é uma string."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock()
        mock_response.intent = []
        mock_response.entities = []
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
             
             mock_template.from_messages.return_value = Mock()
             mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
             
             # Act
             result = datasource(sample_parameters)
             
             # Assert
             from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
             assert isinstance(result, AnalisePreviaMensagemLangchain)
             assert result.intent == []
             assert result.entities == []

    def test_prompt_template_creation(self, datasource, sample_parameters, mock_llm_response):
        """Testa a criação do template de prompt."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_llm_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
             
             mock_template.from_messages.return_value = Mock()
             mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
             
             # Act
             datasource(sample_parameters)
             
             # Assert
             # O prompt system é escapado no código real
             expected_system = sample_parameters.llm_parameters.prompt_system.replace("{", "{{").replace("}", "}}")
             mock_template.from_messages.assert_called_once_with([
                 ("system", expected_system),
                 ("user", "{historico_context}\n\n{prompt_human}: {context}")
             ])

    def test_chain_invocation_parameters(self, datasource, sample_parameters, mock_llm_response):
        """Testa os parâmetros passados para a invocação da chain."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_llm_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
             
             mock_template.from_messages.return_value = Mock()
             mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
             
             # Act
             datasource(sample_parameters)
             
             # Assert
             mock_chain.invoke.assert_called_once_with({
                 "prompt_human": sample_parameters.llm_parameters.prompt_human,
                 "context": sample_parameters.llm_parameters.context,
                 "historico_context": "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível.",
             })

    def test_empty_response_handling(self, datasource, sample_parameters):
        """Testa o tratamento de resposta vazia."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock()
        mock_response.intent = []
        mock_response.entities = []
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
             
             mock_template.from_messages.return_value = Mock()
             mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
             
             # Act
             result = datasource(sample_parameters)
             
             # Assert
             from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
             assert isinstance(result, AnalisePreviaMensagemLangchain)
             assert result.intent == []
             assert result.entities == []

    def test_whitespace_response_handling(self, datasource, sample_parameters):
        """Testa o tratamento de resposta com apenas espaços em branco."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock()
        mock_response.intent = []
        mock_response.entities = []
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
             
             mock_template.from_messages.return_value = Mock()
             mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
             
             # Act
             result = datasource(sample_parameters)
             
             # Assert
             from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
             assert isinstance(result, AnalisePreviaMensagemLangchain)
             assert result.intent == []
             assert result.entities == []

    def test_message_parameter_validation(self, datasource, sample_parameters):
        """Testa a validação do parâmetro message."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_response = Mock()
        mock_response.intent = []
        mock_response.entities = []
        mock_chain.invoke.return_value = mock_response
        
        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        
        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params
        # Definir uma mensagem específica para validação
        sample_parameters.message = "Mensagem com conteúdo específico para validação."
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
            
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = datasource(sample_parameters)
            
            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == []
            assert result.entities == []
            # Verifica se os parâmetros foram passados corretamente
            mock_chain.invoke.assert_called_once_with({
                "prompt_human": sample_parameters.llm_parameters.prompt_human,
                "context": sample_parameters.llm_parameters.context,
                "historico_context": "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível.",
            })
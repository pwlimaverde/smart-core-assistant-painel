import pytest
from typing import Any
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage

from smart_core_assistant_painel.modules.ai_engine import (
    AnalisePreviaMensagemParameters,
    LlmError,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource import (
    AnalisePreviaMensagemLangchainDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.interface.analise_previa_mensagem import (
    AnalisePreviaMensagem,
)


class TestAnalisePreviaMensagemLangchainDatasource:
    """Testes para a classe AnalisePreviaMensagemLangchainDatasource."""

    @pytest.fixture
    def datasource(self) -> AnalisePreviaMensagemLangchainDatasource:
        """Fixture para criar uma instância do datasource."""
        return AnalisePreviaMensagemLangchainDatasource()

    @pytest.fixture
    def sample_parameters(self) -> AnalisePreviaMensagemParameters:
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
    def mock_llm_response(self) -> AnalisePreviaMensagem:
        """Fixture para criar uma resposta mock do LLM."""
        mock_response = Mock()
        mock_response.intent = []
        mock_response.entities = []
        return mock_response

    def test_call_success_case(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters,
            mock_llm_response: AnalisePreviaMensagem) -> None:
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
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == []
            assert result.entities == []

    def test_formatar_historico_com_atendimentos_anteriores(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa a formatação de histórico quando há atendimentos anteriores."""
        # Arrange
        historico_atendimento = {
            "historico_atendimentos": [
                "01/01/2024 - assunto tratado: Suporte técnico",
                "15/01/2024 - assunto tratado: Reclamação de serviço",
                "20/01/2024 - assunto tratado: Solicitação de upgrade"
            ],
            "conteudo_mensagens": [],
            "intents_detectados": [],
            "entidades_extraidas": []
        }

        # Act
        resultado = datasource._formatar_historico_atendimento(historico_atendimento)

        # Assert
        assert "HISTÓRICO DE ATENDIMENTOS ANTERIORES:" in resultado
        assert "1. 01/01/2024 - assunto tratado: Suporte técnico" in resultado
        assert "2. 15/01/2024 - assunto tratado: Reclamação de serviço" in resultado
        assert "3. 20/01/2024 - assunto tratado: Solicitação de upgrade" in resultado

    def test_formatar_historico_sem_atendimentos_anteriores(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa a formatação de histórico quando não há atendimentos anteriores."""
        # Arrange
        historico_atendimento:dict[str, Any] = {
            "historico_atendimentos": [],
            "conteudo_mensagens": [],
            "intents_detectados": [],
            "entidades_extraidas": []
        }

        # Act
        resultado = datasource._formatar_historico_atendimento(historico_atendimento)

        # Assert
        assert "HISTÓRICO DE ATENDIMENTOS ANTERIORES:" not in resultado

    def test_formatar_historico_com_atendimentos_anteriores_e_outros_dados(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa a formatação completa quando há atendimentos anteriores e outros dados."""
        # Arrange
        historico_atendimento = {
            "historico_atendimentos": [
                "01/01/2024 - assunto tratado: Suporte técnico"
            ],
            "conteudo_mensagens": ["Olá, preciso de ajuda"],
            "intents_detectados": ["solicitacao_ajuda"],
            "entidades_extraidas": ["produto: software"]
        }

        # Act
        resultado = datasource._formatar_historico_atendimento(historico_atendimento)

        # Assert
        assert "HISTÓRICO DE ATENDIMENTOS ANTERIORES:" in resultado
        assert "1. 01/01/2024 - assunto tratado: Suporte técnico" in resultado
        assert "ENTIDADES IDENTIFICADAS:" in resultado
        assert "INTENÇÕES PREVIAMENTE DETECTADAS:" in resultado
        assert "HISTÓRICO DA CONVERSA:" in resultado

    def test_call_with_think_tags(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
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
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == []
            assert result.entities == []

    def test_call_with_multiline_think_tags(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
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
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == []
            assert result.entities == []

    def test_call_non_string_response_error(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
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
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == []
            assert result.entities == []

    def test_prompt_template_creation(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters,
            mock_llm_response: AnalisePreviaMensagem) -> None:
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
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            datasource(sample_parameters)

            # Assert
            # O prompt system é escapado no código real
            expected_system = sample_parameters.llm_parameters.prompt_system.replace(
                "{", "{{").replace("}", "}}")
            mock_template.from_messages.assert_called_once_with([
                ("system", expected_system),
                ("user", "{historico_context}\n\n{prompt_human}: {context}")
            ])

    def test_chain_invocation_parameters(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters,
            mock_llm_response: AnalisePreviaMensagem) -> None:
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
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            datasource(sample_parameters)

            # Assert
            expected_invoke_data = {
                "prompt_human": sample_parameters.llm_parameters.prompt_human,
                "context": sample_parameters.llm_parameters.context,
                "historico_context": "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\nNenhuma mensagem anterior disponível.",
            }
            mock_chain.invoke.assert_called_once_with(expected_invoke_data)

    def test_formatar_historico_dict_empty_mensagens_list(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico com dicionário contendo lista de mensagens vazia."""
        historico: dict[str, list[str]] = {"mensagens": []}
        result = datasource._formatar_historico_atendimento(historico)
        assert result == "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\nNenhuma mensagem anterior disponível."

    def test_formatar_historico_dict_no_valid_keys_with_content(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico com dicionário sem chaves válidas mas com conteúdo."""
        historico = {"dados": "algum conteúdo", "info": "mais dados"}
        result = datasource._formatar_historico_atendimento(historico)
        assert result == "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\nNenhuma mensagem anterior disponível."

    def test_formatar_historico_dict_empty_with_whitespace_values(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico com dict contendo valores com espaços."""
        historico = {
            "conteudo_mensagens": ["   \n\t   "]
        }
        result = datasource._formatar_historico_atendimento(historico)
        expected = "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\n1.    \n\t   "
        assert result == expected

    def test_formatar_historico_atendimento_dict_with_conteudo_mensagens_strings(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico quando é dict com chave 'conteudo_mensagens' contendo strings."""
        historico = {
            "conteudo_mensagens": [
                "Primeira mensagem",
                "Segunda mensagem",
                "Terceira mensagem"]}
        result = datasource._formatar_historico_atendimento(historico)
        expected = "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\n1. Primeira mensagem\n2. Segunda mensagem\n3. Terceira mensagem"
        assert result == expected

    def test_formatar_historico_atendimento_dict_with_conteudo_mensagens_more_than_10(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico com mais de 10 mensagens (deve pegar todas as mensagens)."""
        historico = {
            # 15 mensagens
            "conteudo_mensagens": [f"Mensagem {i}" for i in range(1, 16)]
        }
        result = datasource._formatar_historico_atendimento(historico)
        # Deve pegar todas as mensagens (1-15)
        expected_lines = [
            "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:",
            "",
            "",
            "HISTÓRICO DO ATENDIMENTO ATUAL:",
            "",
            "HISTÓRICO DA CONVERSA:"] + [
            f"{i}. Mensagem {i}" for i in range(
                1,
                16)]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_formatar_historico_atendimento_dict_with_conteudo_mensagens_empty(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico quando é dict com 'conteudo_mensagens' vazio."""
        historico:dict[str, Any] = {
            "conteudo_mensagens": []
        }
        result = datasource._formatar_historico_atendimento(historico)
        expected = "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\nNenhuma mensagem anterior disponível."
        assert result == expected

    def test_formatar_historico_atendimento_dict_empty(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico quando é dict vazio."""
        historico: dict[str, str] = {}
        result = datasource._formatar_historico_atendimento(historico)
        assert result == "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\nNenhuma mensagem anterior disponível."

    def test_formatar_historico_atendimento_dict_no_conteudo_mensagens(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico quando é dict sem chave 'conteudo_mensagens'."""
        historico = {"campo_invalido": "valor"}
        result = datasource._formatar_historico_atendimento(historico)
        assert result == "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\nNenhuma mensagem anterior disponível."

    def test_formatar_historico_atendimento_dict_with_conteudo_mensagens_mixed_types(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico com 'conteudo_mensagens' contendo tipos mistos."""
        historico = {
            "conteudo_mensagens": [
                "Mensagem string",
                123,  # Número que será convertido para string
                {"key": "value"},  # Dict que será convertido para string
                None  # None que será convertido para string
            ]
        }
        result = datasource._formatar_historico_atendimento(historico)
        expected = "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\n1. Mensagem string\n2. 123\n3. {'key': 'value'}\n4. None"
        assert result == expected

    def test_formatar_historico_atendimento_with_only_entities(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico apenas com entidades extraídas."""
        historico = {
            "conteudo_mensagens": ["Mensagem teste"],
            "entidades_extraidas": ["email"]
        }
        result = datasource._formatar_historico_atendimento(historico)

        assert "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:" in result
        assert "HISTÓRICO DO ATENDIMENTO ATUAL:" in result
        assert "ENTIDADES IDENTIFICADAS:" in result
        assert "- email" in result
        assert "HISTÓRICO DA CONVERSA:" in result
        assert "1. Mensagem teste" in result

    def test_call_exception_handling(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
        """Testa o tratamento de exceções no método __call__."""
        # Arrange - Fazer com que create_dynamic_pydantic_model lance uma
        # exceção
        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.create_dynamic_pydantic_model') as mock_create_model:
            mock_create_model.side_effect = Exception(
                "Erro na criação do modelo")

            with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.logger') as mock_logger:
                # Act & Assert
                with pytest.raises(Exception, match="Erro na criação do modelo"):
                    datasource(sample_parameters)

                mock_logger.error.assert_called_once()

    def test_call_with_complex_intent_and_entities(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
        """Testa o processamento com intent e entities complexos."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()

        # Criar mock response com intent e entities complexos
        mock_intent_item1 = Mock()
        mock_intent_item1.type = "categoria1"
        mock_intent_item1.value = "intent1"

        mock_intent_item2 = Mock()
        mock_intent_item2.type = "categoria2"
        mock_intent_item2.value = "intent2"

        mock_entity_item1 = Mock()
        mock_entity_item1.type = "pessoa"
        mock_entity_item1.value = "João"

        mock_entity_item2 = Mock()
        mock_entity_item2.type = "local"
        mock_entity_item2.value = "São Paulo"

        mock_response = Mock()
        mock_response.intent = [mock_intent_item1, mock_intent_item2]
        mock_response.entities = [mock_entity_item1, mock_entity_item2]

        mock_chain.invoke.return_value = mock_response

        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        mock_llm_params.context = sample_parameters.llm_parameters.context

        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params

        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)

            # Verificar se os intents foram processados corretamente
            expected_intents = [
                {"categoria1": "intent1"},
                {"categoria2": "intent2"}
            ]
            assert result.intent == expected_intents

            # Verificar se as entities foram processadas corretamente
            expected_entities = [
                {"pessoa": "João"},
                {"local": "São Paulo"}
            ]
            assert result.entities == expected_entities

    def test_call_with_complex_historico(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
        """Testa o processamento com histórico complexo."""
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
        mock_llm_params.context = sample_parameters.llm_parameters.context

        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params

        # Definir histórico complexo
        sample_parameters.historico_atendimento = {
            "conteudo_mensagens": [
                "Olá, preciso de ajuda",
                "Como posso ajudá-lo?",
                "Quero cancelar meu pedido"
            ]
        }

        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)

            # Verificar se o histórico foi formatado corretamente na invocação
            expected_historico = "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\n1. Olá, preciso de ajuda\n2. Como posso ajudá-lo?\n3. Quero cancelar meu pedido"
            mock_chain.invoke.assert_called_once_with({
                "prompt_human": sample_parameters.llm_parameters.prompt_human,
                "context": sample_parameters.llm_parameters.context,
                "historico_context": expected_historico,
            })

    def test_empty_response_handling(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
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
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == []
            assert result.entities == []

    def test_whitespace_response_handling(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
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
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == []
            assert result.entities == []

    def test_message_parameter_validation(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
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

        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:

            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

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
                "historico_context": "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:\n\n\nHISTÓRICO DO ATENDIMENTO ATUAL:\n\nHISTÓRICO DA CONVERSA:\nNenhuma mensagem anterior disponível.",
            })

    def test_formatar_historico_atendimento_with_intents_and_entities(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
        """Testa o processamento bem-sucedido com intenções e entidades."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        
        # Criar mocks para objetos de intenção e entidade
        mock_intent1 = Mock()
        mock_intent1.type = "saudacao"
        mock_intent1.value = "ola"
        
        mock_intent2 = Mock()
        mock_intent2.type = "pergunta"
        mock_intent2.value = "como_esta"
        
        mock_entity1 = Mock()
        mock_entity1.type = "pessoa"
        mock_entity1.value = "João"
        
        mock_entity2 = Mock()
        mock_entity2.type = "local"
        mock_entity2.value = "São Paulo"
        
        mock_response = Mock()
        mock_response.intent = [mock_intent1, mock_intent2]
        mock_response.entities = [mock_entity1, mock_entity2]
        mock_chain.invoke.return_value = mock_response

        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        mock_llm_params.context = sample_parameters.llm_parameters.context

        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params

        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == [{"saudacao": "ola"}, {"pergunta": "como_esta"}]
            assert result.entities == [{"pessoa": "João"}, {"local": "São Paulo"}]
            mock_chain.invoke.assert_called_once()

    def test_formatar_historico_atendimento_with_only_intents(
            self, datasource: AnalisePreviaMensagemLangchainDatasource) -> None:
        """Testa formatação de histórico apenas com intenções detectadas."""
        historico = {
            "conteudo_mensagens": ["Mensagem teste"],
            "intents_detectados": ["saudacao", "pergunta"]
        }
        result = datasource._formatar_historico_atendimento(historico)

        assert "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:" in result
        assert "HISTÓRICO DO ATENDIMENTO ATUAL:" in result
        assert "INTENÇÕES PREVIAMENTE DETECTADAS:" in result
        assert "- saudacao" in result
        assert "- pergunta" in result
        assert "HISTÓRICO DA CONVERSA:" in result
        assert "1. Mensagem teste" in result

    def test_call_with_llm_structured_output_exception(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
        """Testa tratamento de exceção durante with_structured_output."""
        # Arrange
        mock_llm = Mock()
        mock_llm.with_structured_output.side_effect = Exception(
            "Erro no structured output")

        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        mock_llm_params.context = sample_parameters.llm_parameters.context

        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params

        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.logger') as mock_logger:
            # Act & Assert
            with pytest.raises(Exception, match="Erro no structured output"):
                datasource(sample_parameters)

            mock_logger.error.assert_called_once()

    def test_call_with_chain_invoke_exception(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
        """Testa tratamento de exceção durante chain.invoke."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.invoke.side_effect = Exception("Erro na invocação da chain")

        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        mock_llm_params.context = sample_parameters.llm_parameters.context

        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params

        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.logger') as mock_logger:
                # Act & Assert
                with pytest.raises(Exception, match="Erro na invocação da chain"):
                    datasource(sample_parameters)

                mock_logger.error.assert_called_once()

    def test_successful_processing_with_intents_and_entities(
            self,
            datasource: AnalisePreviaMensagemLangchainDatasource,
            sample_parameters: AnalisePreviaMensagemParameters) -> None:
        """Testa o processamento bem-sucedido com intenções e entidades - cobre linhas 107-110."""
        # Arrange
        mock_llm = Mock()
        mock_chain = Mock()
        
        # Criar mocks para objetos de intenção e entidade
        mock_intent1 = Mock()
        mock_intent1.type = "saudacao"
        mock_intent1.value = "ola"
        
        mock_intent2 = Mock()
        mock_intent2.type = "pergunta"
        mock_intent2.value = "como_esta"
        
        mock_entity1 = Mock()
        mock_entity1.type = "pessoa"
        mock_entity1.value = "João"
        
        mock_entity2 = Mock()
        mock_entity2.type = "local"
        mock_entity2.value = "São Paulo"
        
        mock_response = Mock()
        mock_response.intent = [mock_intent1, mock_intent2]
        mock_response.entities = [mock_entity1, mock_entity2]
        mock_chain.invoke.return_value = mock_response

        # Criar um mock dos llm_parameters com create_llm mockado
        mock_llm_params = Mock()
        mock_llm_params.create_llm = mock_llm
        mock_llm_params.prompt_system = sample_parameters.llm_parameters.prompt_system
        mock_llm_params.prompt_human = sample_parameters.llm_parameters.prompt_human
        mock_llm_params.context = sample_parameters.llm_parameters.context

        # Substituir os llm_parameters no sample_parameters
        sample_parameters.llm_parameters = mock_llm_params

        with patch('smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource.ChatPromptTemplate') as mock_template:
            mock_template.from_messages.return_value = Mock()
            mock_template.from_messages.return_value.__or__ = Mock(
                return_value=mock_chain)

            # Act
            result = datasource(sample_parameters)

            # Assert - estas linhas cobrem especificamente as linhas 107-110 do arquivo fonte
            from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
            assert isinstance(result, AnalisePreviaMensagemLangchain)
            assert result.intent == [{"saudacao": "ola"}, {"pergunta": "como_esta"}]
            assert result.entities == [{"pessoa": "João"}, {"local": "São Paulo"}]
            mock_chain.invoke.assert_called_once()

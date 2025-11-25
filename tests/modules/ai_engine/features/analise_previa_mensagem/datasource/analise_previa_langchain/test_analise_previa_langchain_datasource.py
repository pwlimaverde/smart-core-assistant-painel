
import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from pydantic import BaseModel

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_langchain_datasource import (
    AnalisePreviaLangchainDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
    LlmParameters,
)


class TestAnalisePreviaLangchainDatasource(unittest.TestCase):
    def setUp(self):
        self.datasource = AnalisePreviaLangchainDatasource()

        self.mock_llm_params = MagicMock(spec=LlmParameters)
        self.mock_llm_params.prompt_system = "System Prompt"
        self.mock_llm_params.prompt_human = "Human Prompt"
        self.mock_llm_params.context = "Context"
        self.mock_llm = MagicMock()
        self.mock_llm_params.create_llm = self.mock_llm

        self.parameters = AnalisePreviaMensagemParameters(
            historico_atendimento={},
            valid_intent_types=[],
            valid_entity_types=[],
            llm_parameters=self.mock_llm_params,
            error=MagicMock()
        )

    @patch("smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_langchain_datasource.build_analise_previa_model")
    def test_call_success_structured_output(self, mock_build_model):
        # Setup Mock Model
        MockModel = MagicMock()
        mock_build_model.return_value = MockModel

        # Setup LLM with_structured_output
        mock_structured_llm = MagicMock()
        self.mock_llm.with_structured_output.return_value = mock_structured_llm

        # Setup Chain invoke
        mock_chain = MagicMock()
        mock_structured_llm.__ror__ = MagicMock(return_value=mock_chain) # handle prompt | llm
        # Actually the code does: messages | structured_llm
        # I need to mock ChatPromptTemplate too or ensure the pipe works.

        # If I mock ChatPromptTemplate.from_messages
        with patch("smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_langchain_datasource.ChatPromptTemplate") as MockPrompt:
            mock_messages = MagicMock()
            MockPrompt.from_messages.return_value = mock_messages
            mock_messages.__or__.return_value = mock_chain

            # Mock response
            mock_response_obj = MagicMock(spec=BaseModel)
            i1 = MagicMock(); i1.type = "intent1"; i1.value = "val1"
            e1 = MagicMock(); e1.type = "entity1"; e1.value = "val2"
            mock_response_obj.intent = [i1]
            mock_response_obj.entities = [e1]
            mock_chain.invoke.return_value = mock_response_obj

            result = self.datasource(self.parameters)

            self.assertIsInstance(result, AnalisePreviaMensagemLangchain)
            self.assertEqual(result.intent, [{"intent1": "val1"}])
            self.assertEqual(result.entities, [{"entity1": "val2"}])

    def test_normalize_types_config_json(self):
        config = '{"key": "value"}'
        result = self.datasource._normalize_types_config(config)
        self.assertEqual(result, [{"key": "value"}])

    def test_normalize_types_config_list(self):
        config = ["type1", {"type": "type2"}]
        result = self.datasource._normalize_types_config(config)
        self.assertEqual(result, [{"type": "type1"}, {"type": "type2"}])

    def test_format_service_history_dict(self):
        history = {"conteudo_mensagens": ["msg1"]}
        result = self.datasource._format_service_history(history)
        self.assertIn("1. msg1", result)

    def test_format_service_history_str_json(self):
        history = '{"conteudo_mensagens": ["msg1"]}'
        result = self.datasource._format_service_history(history)
        self.assertIn("1. msg1", result)

    def test_format_service_history_str_simple(self):
        history = "simple message"
        result = self.datasource._format_service_history(history)
        self.assertIn("1. simple message", result)

    def test_slugify_type(self):
        self.assertEqual(self.datasource._slugify_type("Teste de Ação"), "teste_de_acao")
        self.assertEqual(self.datasource._slugify_type("  Space  "), "space")

    def test_map_to_allowed(self):
        allowed = {"pergunta", "horario", "nome_contato"}

        # Direct match
        self.assertEqual(self.datasource._map_to_allowed("pergunta", allowed, "intent"), "pergunta")
        # Prefix match
        self.assertEqual(self.datasource._map_to_allowed("pergunta_preco", allowed, "intent"), "pergunta")
        # Underscore split match
        self.assertEqual(self.datasource._map_to_allowed("horario_funcionamento", allowed, "intent"), "horario")
        # Special case
        self.assertEqual(self.datasource._map_to_allowed("nome", allowed, "intent"), "nome_contato")
        # No match
        self.assertIsNone(self.datasource._map_to_allowed("outra_coisa", allowed, "intent"))

    def test_filter_and_convert_items(self):
        MockItem = MagicMock
        items = [
            MockItem(type="t1", value="v1"),
            MockItem(type=None, value="v2"), # Skipped
            MockItem(type="t3", value=""), # Skipped
        ]
        # Mock attributes on MagicMock instance need configuration or setting
        i1 = MagicMock()
        i1.type = "t1"
        i1.value = "v1"
        i2 = MagicMock()
        i2.type = None
        i2.value = "v2"
        i3 = MagicMock()
        i3.type = "t3"
        i3.value = ""

        result = self.datasource._filter_and_convert_items([i1, i2, i3])
        self.assertEqual(result, [{"t1": "v1"}])

    def test_parse_json_to_model(self):
        class MyModel(BaseModel):
            field: str

        json_str = '```json\n{"field": "value"}\n```'
        result = self.datasource._parse_json_to_model(json_str, MyModel)
        self.assertEqual(result.field, "value")

    @patch("smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_langchain_datasource.build_analise_previa_model")
    def test_call_fallback_parsing(self, mock_build_model):
        class ItemModel(BaseModel):
            type: str
            value: str

        # Mock Model
        class MockModel(BaseModel):
            intent: list[ItemModel] = []
            entities: list[ItemModel] = []
            # Attributes added by build_analise_previa_model
            __intent_allowed__ = ("i1",)
            __entity_allowed__ = ()

        mock_build_model.return_value = MockModel

        # Mock LLM to fail structured output (return None or raise)
        # The code tries json_schema then default. If both fail, structured_llm is None.
        self.mock_llm.with_structured_output.side_effect = Exception("Fail")

        # Mock Chain for fallback
        with patch("smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_langchain_datasource.ChatPromptTemplate") as MockPrompt:
            mock_messages = MagicMock()
            MockPrompt.from_messages.return_value = mock_messages
            mock_chain = MagicMock()
            mock_messages.__or__.return_value = mock_chain # messages | llm

            # The code invokes chain_fallback.invoke
            mock_raw_response = MagicMock()
            mock_raw_response.content = '{"intent": [{"type": "i1", "value": "v1"}]}'
            mock_chain.invoke.return_value = mock_raw_response

            result = self.datasource(self.parameters)

            self.assertEqual(result.intent, [{"i1": "v1"}])

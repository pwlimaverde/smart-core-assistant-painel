import os
import unittest
from unittest.mock import patch

from langchain.docstore.document import Document

from smart_core_assistant_painel.modules.services import ServiceHub


class TestServiceHub(unittest.TestCase):
    def setUp(self):
        # Reset the singleton instance before each test
        ServiceHub._instance = None
        ServiceHub._initialized = False

    @patch.dict(os.environ, {"TIME_CACHE": "30"})
    def test_time_cache_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.TIME_CACHE, 30)

    def test_time_cache_property_without_env_var(self):
        if "TIME_CACHE" in os.environ:
            del os.environ["TIME_CACHE"]
        hub = ServiceHub()
        self.assertEqual(hub.TIME_CACHE, 20)

    @patch.dict(os.environ, {"CHUNK_OVERLAP": "300"})
    def test_chunk_overlap_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.CHUNK_OVERLAP, 300)

    def test_chunk_overlap_property_without_env_var(self):
        if "CHUNK_OVERLAP" in os.environ:
            del os.environ["CHUNK_OVERLAP"]
        hub = ServiceHub()
        self.assertEqual(hub.CHUNK_OVERLAP, 200)

    @patch.dict(os.environ, {"CHUNK_SIZE": "1500"})
    def test_chunk_size_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.CHUNK_SIZE, 1500)

    def test_chunk_size_property_without_env_var(self):
        if "CHUNK_SIZE" in os.environ:
            del os.environ["CHUNK_SIZE"]
        hub = ServiceHub()
        self.assertEqual(hub.CHUNK_SIZE, 1000)

    @patch.dict(os.environ, {"EMBEDDINGS_MODEL": "test_model"})
    def test_embeddings_model_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.EMBEDDINGS_MODEL, "test_model")

    def test_embeddings_model_property_without_env_var(self):
        if "EMBEDDINGS_MODEL" in os.environ:
            del os.environ["EMBEDDINGS_MODEL"]
        hub = ServiceHub()
        self.assertEqual(hub.EMBEDDINGS_MODEL, "")

    def test_singleton_pattern(self):
        hub1 = ServiceHub()
        hub2 = ServiceHub()
        self.assertIs(hub1, hub2)

    @patch.dict(os.environ, {"PROMPT_SYSTEM_ANALISE_CONTEUDO": "test_prompt"})
    def test_prompt_system_analise_conteudo_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.PROMPT_SYSTEM_ANALISE_CONTEUDO, "test_prompt")

    def test_prompt_system_analise_conteudo_property_without_env_var(self):
        if "PROMPT_SYSTEM_ANALISE_CONTEUDO" in os.environ:
            del os.environ["PROMPT_SYSTEM_ANALISE_CONTEUDO"]
        hub = ServiceHub()
        self.assertEqual(hub.PROMPT_SYSTEM_ANALISE_CONTEUDO, "")

    @patch.dict(os.environ, {"LLM_CLASS": "ChatGroq"})
    def test_get_llm_class_chatgroq(self):
        hub = ServiceHub()
        from langchain_groq import ChatGroq

        self.assertEqual(hub.LLM_CLASS, ChatGroq)

    @patch.dict(os.environ, {"LLM_CLASS": "ChatOpenAI"})
    def test_get_llm_class_chatopenai(self):
        hub = ServiceHub()
        from langchain_openai import ChatOpenAI

        self.assertEqual(hub.LLM_CLASS, ChatOpenAI)

    @patch.dict(os.environ, {"LLM_CLASS": "InvalidLLM"})
    def test_get_llm_class_invalid(self):
        hub = ServiceHub()
        with self.assertRaises(ValueError):
            _ = hub.LLM_CLASS

    @patch.dict(os.environ, {"PROMPT_HUMAN_ANALISE_CONTEUDO": "test_prompt"})
    def test_prompt_human_analise_conteudo_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.PROMPT_HUMAN_ANALISE_CONTEUDO, "test_prompt")

    def test_prompt_human_analise_conteudo_property_without_env_var(self):
        if "PROMPT_HUMAN_ANALISE_CONTEUDO" in os.environ:
            del os.environ["PROMPT_HUMAN_ANALISE_CONTEUDO"]
        hub = ServiceHub()
        self.assertEqual(hub.PROMPT_HUMAN_ANALISE_CONTEUDO, "")

    @patch.dict(os.environ, {"PROMPT_SYSTEM_MELHORIA_CONTEUDO": "test_prompt"})
    def test_prompt_system_melhoria_conteudo_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.PROMPT_SYSTEM_MELHORIA_CONTEUDO, "test_prompt")

    def test_prompt_system_melhoria_conteudo_property_without_env_var(self):
        if "PROMPT_SYSTEM_MELHORIA_CONTEUDO" in os.environ:
            del os.environ["PROMPT_SYSTEM_MELHORIA_CONTEUDO"]
        hub = ServiceHub()
        self.assertEqual(hub.PROMPT_SYSTEM_MELHORIA_CONTEUDO, "")

    @patch.dict(
        os.environ, {"PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM": "test_prompt"}
    )
    def test_prompt_system_analise_previa_mensagem_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(
            hub.PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM, "test_prompt"
        )

    def test_prompt_system_analise_previa_mensagem_without_env_var(self):
        if "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM" in os.environ:
            del os.environ["PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM"]
        hub = ServiceHub()
        self.assertEqual(hub.PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM, "")

    @patch.dict(
        os.environ, {"PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM": "test_prompt"}
    )
    def test_prompt_human_analise_previa_mensagem_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(
            hub.PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM, "test_prompt"
        )

    def test_prompt_human_analise_previa_mensagem_without_env_var(self):
        if "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM" in os.environ:
            del os.environ["PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM"]
        hub = ServiceHub()
        self.assertEqual(hub.PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM, "")

    @patch.dict(os.environ, {"VALID_INTENT_TYPES": '["intent1", "intent2"]'})
    def test_valid_intent_types_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.VALID_INTENT_TYPES, '["intent1", "intent2"]')

    def test_valid_intent_types_without_env_var(self):
        if "VALID_INTENT_TYPES" in os.environ:
            del os.environ["VALID_INTENT_TYPES"]
        hub = ServiceHub()
        self.assertEqual(hub.VALID_INTENT_TYPES, "")

    @patch.dict(os.environ, {"VALID_ENTITY_TYPES": '["entity1", "entity2"]'})
    def test_valid_entity_types_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.VALID_ENTITY_TYPES, '["entity1", "entity2"]')

    def test_valid_entity_types_without_env_var(self):
        if "VALID_ENTITY_TYPES" in os.environ:
            del os.environ["VALID_ENTITY_TYPES"]
        hub = ServiceHub()
        self.assertEqual(hub.VALID_ENTITY_TYPES, "")

    # Testes para propriedades LLM
    @patch.dict(os.environ, {"MODEL": "test_model"})
    def test_model_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.MODEL, "test_model")

    def test_model_property_without_env_var(self):
        if "MODEL" in os.environ:
            del os.environ["MODEL"]
        hub = ServiceHub()
        self.assertEqual(hub.MODEL, "llama3.1")

    @patch.dict(os.environ, {"LLM_TEMPERATURE": "1"})
    def test_llm_temperature_property_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.LLM_TEMPERATURE, 1)

    def test_llm_temperature_property_without_env_var(self):
        if "LLM_TEMPERATURE" in os.environ:
            del os.environ["LLM_TEMPERATURE"]
        hub = ServiceHub()
        self.assertEqual(hub.LLM_TEMPERATURE, 0)

    # Testes para propriedades WhatsApp
    @patch.dict(os.environ, {"WHATSAPP_API_BASE_URL": "http://test.com"})
    def test_whatsapp_api_base_url_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.WHATSAPP_API_BASE_URL, "http://test.com")

    def test_whatsapp_api_base_url_without_env_var(self):
        if "WHATSAPP_API_BASE_URL" in os.environ:
            del os.environ["WHATSAPP_API_BASE_URL"]
        hub = ServiceHub()
        self.assertEqual(hub.WHATSAPP_API_BASE_URL, "")

    # Testes para EMBEDDINGS_CLASS
    @patch.dict(os.environ, {"EMBEDDINGS_CLASS": "HuggingFaceEmbeddings"})
    def test_embeddings_class_with_env_var(self):
        hub = ServiceHub()
        self.assertEqual(hub.EMBEDDINGS_CLASS, "HuggingFaceEmbeddings")

    def test_embeddings_class_without_env_var(self):
        if "EMBEDDINGS_CLASS" in os.environ:
            del os.environ["EMBEDDINGS_CLASS"]
        hub = ServiceHub()
        self.assertEqual(hub.EMBEDDINGS_CLASS, "OpenAIEmbeddings")



    # Testes para métodos
    def test_set_whatsapp_service(self):
        from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.interface.whatsapp_service import WhatsAppService
        from unittest.mock import Mock
        
        mock_service = Mock(spec=WhatsAppService)
        hub = ServiceHub()
        hub.set_whatsapp_service(mock_service)
        self.assertEqual(hub.whatsapp_service, mock_service)

    def test_whatsapp_service_not_configured(self):
        hub = ServiceHub()
        with self.assertRaises(RuntimeError) as context:
            _ = hub.whatsapp_service
        self.assertIn("WhatsAppService não configurado", str(context.exception))

    def test_reload_config_method(self):
        hub = ServiceHub()
        # Testa se o método reload_config não gera erro
        hub.reload_config()
        # Verifica se as configurações foram recarregadas
        self.assertIsNotNone(hub.TIME_CACHE)

    @patch.dict(os.environ, {"LLM_CLASS": "ChatOllama"})
    def test_get_llm_class_chatollama_default(self):
        hub = ServiceHub()
        from langchain_ollama import ChatOllama
        self.assertEqual(hub.LLM_CLASS, ChatOllama)


if __name__ == "__main__":
    unittest.main()

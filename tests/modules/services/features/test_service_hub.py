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

    # Novos testes para melhorar cobertura
    
    @patch.dict(os.environ, {"WHATSAPP_SERVICE_TYPE": "evolution"})
    def test_init_whatsapp_service_type_error(self):
        """Testa RuntimeError quando WHATSAPP_SERVICE_TYPE está definida mas _whatsapp_service é None - cobre linha 112."""
        hub = ServiceHub()
        
        with self.assertRaises(RuntimeError) as context:
            hub.reload_config()  # A linha 112 está no reload_config, não no __init__
        
        self.assertIn("Falha ao auto-configurar WhatsAppService", str(context.exception))
        self.assertIn("Use set_whatsapp_service()", str(context.exception))

    @patch.dict(os.environ, {
        "HUGGINGFACE_API_KEY": "",  # Vazio, força buscar fallback
        "HUGGINGFACEHUB_API_KEY": "fallback_key"
    })
    def test_huggingface_api_key_fallback(self):
        """Testa fallback para HUGGINGFACEHUB_API_KEY - cobre linhas 134-138."""
        hub = ServiceHub()
        # Inicializa a propriedade para None para forçar o fallback
        hub._huggingface_api_key = None
        result = hub.HUGGINGFACE_API_KEY
        self.assertEqual(result, "fallback_key")

    def test_huggingface_api_key_both_empty(self):
        """Testa quando ambas as chaves estão vazias ou ausentes."""
        # Remove as variáveis de ambiente
        for key in ["HUGGINGFACE_API_KEY", "HUGGINGFACEHUB_API_KEY"]:
            if key in os.environ:
                del os.environ[key]
        
        hub = ServiceHub()
        # Inicializa a propriedade para None
        hub._huggingface_api_key = None
        result = hub.HUGGINGFACE_API_KEY
        self.assertEqual(result, "")

    def test_model_property_when_none(self):
        """Testa propriedade MODEL quando _model é None - cobre linha 152."""
        hub = ServiceHub()
        # Força _model para None
        hub._model = None
        if "MODEL" in os.environ:
            del os.environ["MODEL"]
        
        result = hub.MODEL
        self.assertEqual(result, "llama3.1")

    def test_llm_temperature_property_when_none(self):
        """Testa propriedade LLM_TEMPERATURE quando _llm_temperature é None - cobre linha 159."""
        hub = ServiceHub()
        # Força _llm_temperature para None
        hub._llm_temperature = None
        if "LLM_TEMPERATURE" in os.environ:
            del os.environ["LLM_TEMPERATURE"]
        
        result = hub.LLM_TEMPERATURE
        self.assertEqual(result, 0)

    def test_prompt_system_analise_conteudo_when_none(self):
        """Testa propriedade quando valor interno é None - cobre linha 166→170."""
        hub = ServiceHub()
        hub._prompt_system_analise_conteudo = None
        if "PROMPT_SYSTEM_ANALISE_CONTEUDO" in os.environ:
            del os.environ["PROMPT_SYSTEM_ANALISE_CONTEUDO"]
        
        result = hub.PROMPT_SYSTEM_ANALISE_CONTEUDO
        self.assertEqual(result, "")

    def test_prompt_human_analise_conteudo_when_none(self):
        """Testa propriedade quando valor interno é None - cobre linha 179→183."""
        hub = ServiceHub()
        hub._prompt_human_analise_conteudo = None
        if "PROMPT_HUMAN_ANALISE_CONTEUDO" in os.environ:
            del os.environ["PROMPT_HUMAN_ANALISE_CONTEUDO"]
        
        result = hub.PROMPT_HUMAN_ANALISE_CONTEUDO
        self.assertEqual(result, "")

    def test_prompt_system_melhoria_conteudo_when_none(self):
        """Testa propriedade quando valor interno é None - cobre linha 192→196."""
        hub = ServiceHub()
        hub._prompt_system_melhoria_conteudo = None
        if "PROMPT_SYSTEM_MELHORIA_CONTEUDO" in os.environ:
            del os.environ["PROMPT_SYSTEM_MELHORIA_CONTEUDO"]
        
        result = hub.PROMPT_SYSTEM_MELHORIA_CONTEUDO
        self.assertEqual(result, "")

    def test_prompt_human_melhoria_conteudo_when_none(self):
        """Testa propriedade quando valor interno é None - cobre linhas 205-209."""
        hub = ServiceHub()
        hub._prompt_human_melhoria_conteudo = None
        if "PROMPT_HUMAN_MELHORIA_CONTEUDO" in os.environ:
            del os.environ["PROMPT_HUMAN_MELHORIA_CONTEUDO"]
        
        result = hub.PROMPT_HUMAN_MELHORIA_CONTEUDO
        self.assertEqual(result, "")

    def test_prompt_human_analise_previa_mensagem_when_none(self):
        """Testa propriedade quando valor interno é None - cobre linha 218→222."""
        hub = ServiceHub()
        hub._prompt_human_analise_previa_mensagem = None
        if "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM" in os.environ:
            del os.environ["PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM"]
        
        result = hub.PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM
        self.assertEqual(result, "")

    def test_prompt_system_analise_previa_mensagem_when_none(self):
        """Testa propriedade quando valor interno é None - cobre linha 231→235."""
        hub = ServiceHub()
        hub._prompt_system_analise_previa_mensagem = None
        if "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM" in os.environ:
            del os.environ["PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM"]
        
        result = hub.PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM
        self.assertEqual(result, "")

    def test_chunk_overlap_when_none(self):
        """Testa propriedade CHUNK_OVERLAP quando valor interno é None - cobre linha 246."""
        hub = ServiceHub()
        hub._chunk_overlap = None
        if "CHUNK_OVERLAP" in os.environ:
            del os.environ["CHUNK_OVERLAP"]
        
        result = hub.CHUNK_OVERLAP
        self.assertEqual(result, 200)

    def test_chunk_size_when_none(self):
        """Testa propriedade CHUNK_SIZE quando valor interno é None - cobre linha 253."""
        hub = ServiceHub()
        hub._chunk_size = None
        if "CHUNK_SIZE" in os.environ:
            del os.environ["CHUNK_SIZE"]
        
        result = hub.CHUNK_SIZE
        self.assertEqual(result, 1000)

    def test_embeddings_model_when_none(self):
        """Testa propriedade EMBEDDINGS_MODEL quando valor interno é None - cobre linha 266→268."""
        hub = ServiceHub()
        hub._embeddings_model = None
        if "EMBEDDINGS_MODEL" in os.environ:
            del os.environ["EMBEDDINGS_MODEL"]
        
        result = hub.EMBEDDINGS_MODEL
        self.assertEqual(result, "")

    def test_embeddings_class_when_none(self):
        """Testa propriedade EMBEDDINGS_CLASS quando valor interno é None - cobre linhas 285-287."""
        hub = ServiceHub()
        hub._embeddings_class = None
        if "EMBEDDINGS_CLASS" in os.environ:
            del os.environ["EMBEDDINGS_CLASS"]
        
        result = hub.EMBEDDINGS_CLASS
        self.assertEqual(result, "OpenAIEmbeddings")

    def test_whatsapp_api_base_url_when_none(self):
        """Testa propriedade WHATSAPP_API_BASE_URL quando valor interno é None - cobre linhas 296-298."""
        hub = ServiceHub()
        hub._whatsapp_api_base_url = None
        if "WHATSAPP_API_BASE_URL" in os.environ:
            del os.environ["WHATSAPP_API_BASE_URL"]
        
        result = hub.WHATSAPP_API_BASE_URL
        self.assertEqual(result, "")

    def test_whatsapp_api_send_text_url_when_none(self):
        """Testa propriedade WHATSAPP_API_SEND_TEXT_URL quando valor interno é None - cobre linhas 307-309."""
        hub = ServiceHub()
        hub._whatsapp_api_send_text_url = None
        if "WHATSAPP_API_SEND_TEXT_URL" in os.environ:
            del os.environ["WHATSAPP_API_SEND_TEXT_URL"]
        
        result = hub.WHATSAPP_API_SEND_TEXT_URL
        self.assertEqual(result, "")

    def test_whatsapp_api_start_typing_url_when_none(self):
        """Testa propriedade WHATSAPP_API_START_TYPING_URL quando valor interno é None - cobre linhas 334→336."""
        hub = ServiceHub()
        hub._whatsapp_api_start_typing_url = None
        if "WHATSAPP_API_START_TYPING_URL" in os.environ:
            del os.environ["WHATSAPP_API_START_TYPING_URL"]
        
        result = hub.WHATSAPP_API_START_TYPING_URL
        self.assertEqual(result, "")

    def test_whatsapp_api_stop_typing_url_when_none(self):
        """Testa propriedade WHATSAPP_API_STOP_TYPING_URL quando valor interno é None - cobre linhas 341→343."""
        hub = ServiceHub()
        hub._whatsapp_api_stop_typing_url = None
        if "WHATSAPP_API_STOP_TYPING_URL" in os.environ:
            del os.environ["WHATSAPP_API_STOP_TYPING_URL"]
        
        result = hub.WHATSAPP_API_STOP_TYPING_URL
        self.assertEqual(result, "")

    def test_valid_entity_types_when_none(self):
        """Testa propriedade VALID_ENTITY_TYPES quando valor interno é None - cobre linha 349."""
        hub = ServiceHub()
        hub._valid_entity_types = None
        if "VALID_ENTITY_TYPES" in os.environ:
            del os.environ["VALID_ENTITY_TYPES"]
        
        result = hub.VALID_ENTITY_TYPES
        self.assertEqual(result, "")

    def test_valid_intent_types_when_none(self):
        """Testa propriedade VALID_INTENT_TYPES quando valor interno é None."""
        hub = ServiceHub()
        hub._valid_intent_types = None
        if "VALID_INTENT_TYPES" in os.environ:
            del os.environ["VALID_INTENT_TYPES"]
        
        result = hub.VALID_INTENT_TYPES
        self.assertEqual(result, "")

    def test_time_cache_when_none(self):
        """Testa propriedade TIME_CACHE quando valor interno é None."""
        hub = ServiceHub()
        hub._time_cache = None
        if "TIME_CACHE" in os.environ:
            del os.environ["TIME_CACHE"]
        
        result = hub.TIME_CACHE
        self.assertEqual(result, 20)


if __name__ == "__main__":
    unittest.main()

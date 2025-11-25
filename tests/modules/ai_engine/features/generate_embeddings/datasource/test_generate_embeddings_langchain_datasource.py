
import unittest
from unittest.mock import MagicMock, patch

from smart_core_assistant_painel.modules.ai_engine.features.generate_embeddings.datasource.generate_embeddings_langchain_datasource import (
    GenerateEmbeddingsLangchainDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import EmbeddingError
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    GenerateEmbeddingsParameters,
)

# Caminho para patch do SERVICEHUB onde ele é usado
SERVICEHUB_PATCH_PATH = "smart_core_assistant_painel.modules.ai_engine.features.generate_embeddings.datasource.generate_embeddings_langchain_datasource.SERVICEHUB"


class TestGenerateEmbeddingsLangchainDatasource(unittest.TestCase):
    def setUp(self):
        self.datasource = GenerateEmbeddingsLangchainDatasource()
        self.params = GenerateEmbeddingsParameters(
            text="test text", error=EmbeddingError("Default error")
        )

    @patch(SERVICEHUB_PATCH_PATH)
    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_instance_openai(self, mock_openai, mock_servicehub):
        """Testa a criação de instância OpenAIEmbeddings."""
        mock_servicehub.EMBEDDINGS_CLASS = "OpenAIEmbeddings"
        mock_servicehub.EMBEDDINGS_MODEL = "text-embedding-3-small"

        instance = self.datasource._create_embeddings_instance()

        mock_openai.assert_called_once_with(model="text-embedding-3-small")
        self.assertEqual(instance, mock_openai.return_value)

    @patch(SERVICEHUB_PATCH_PATH)
    @patch("langchain_ollama.OllamaEmbeddings")
    def test_create_embeddings_instance_ollama(self, mock_ollama, mock_servicehub):
        """Testa a criação de instância OllamaEmbeddings."""
        mock_servicehub.EMBEDDINGS_CLASS = "OllamaEmbeddings"
        mock_servicehub.EMBEDDINGS_MODEL = "llama3"

        instance = self.datasource._create_embeddings_instance()

        mock_ollama.assert_called_once_with(model="llama3")
        self.assertEqual(instance, mock_ollama.return_value)

    @patch(SERVICEHUB_PATCH_PATH)
    @patch("langchain_community.embeddings.HuggingFaceEmbeddings")
    def test_create_embeddings_instance_huggingface(self, mock_hf, mock_servicehub):
        """Testa a criação de instância HuggingFaceEmbeddings."""
        mock_servicehub.EMBEDDINGS_CLASS = "HuggingFaceEmbeddings"
        mock_servicehub.EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

        instance = self.datasource._create_embeddings_instance()

        mock_hf.assert_called_once_with(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.assertEqual(instance, mock_hf.return_value)

    @patch(SERVICEHUB_PATCH_PATH)
    @patch("langchain_community.embeddings.HuggingFaceInferenceAPIEmbeddings")
    def test_create_embeddings_instance_huggingface_inference(
        self, mock_hf_inf, mock_servicehub
    ):
        """Testa a criação de instância HuggingFaceInferenceAPIEmbeddings."""
        mock_servicehub.EMBEDDINGS_CLASS = "HuggingFaceInferenceAPIEmbeddings"
        mock_servicehub.EMBEDDINGS_MODEL = (
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        mock_servicehub.HUGGINGFACE_API_KEY = "hf_test_key"

        instance = self.datasource._create_embeddings_instance()

        # Verifica se foi chamado corretamente. Note que api_key é passado como SecretStr
        args, kwargs = mock_hf_inf.call_args
        self.assertEqual(
            kwargs["model_name"], "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.assertEqual(kwargs["api_key"].get_secret_value(), "hf_test_key")
        self.assertEqual(instance, mock_hf_inf.return_value)

    @patch(SERVICEHUB_PATCH_PATH)
    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_instance_fallback(
        self, mock_openai, mock_servicehub
    ):
        """Testa o fallback para OpenAIEmbeddings."""
        mock_servicehub.EMBEDDINGS_CLASS = "UnknownClass"
        mock_servicehub.EMBEDDINGS_MODEL = "text-embedding-ada-002"

        instance = self.datasource._create_embeddings_instance()

        mock_openai.assert_called_once_with(model="text-embedding-ada-002")
        self.assertEqual(instance, mock_openai.return_value)

    @patch.object(
        GenerateEmbeddingsLangchainDatasource, "_create_embeddings_instance"
    )
    def test_call_success(self, mock_create_instance):
        """Testa o método __call__ com sucesso."""
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_create_instance.return_value = mock_embeddings

        result = self.datasource(self.params)

        mock_embeddings.embed_query.assert_called_once_with("test text")
        self.assertEqual(result, [0.1, 0.2, 0.3])

    @patch.object(
        GenerateEmbeddingsLangchainDatasource, "_create_embeddings_instance"
    )
    def test_call_exception(self, mock_create_instance):
        """Testa o tratamento de exceção no método __call__."""
        mock_create_instance.side_effect = Exception("Test error")

        with self.assertRaises(Exception) as context:
            self.datasource(self.params)

        self.assertIn(
            "Erro ao gerar embeddings: Test error", str(context.exception)
        )

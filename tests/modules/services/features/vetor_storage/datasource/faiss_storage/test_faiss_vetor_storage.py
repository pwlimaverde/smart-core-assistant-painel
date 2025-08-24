import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any
from pydantic import SecretStr

# Mock do FAISS antes de qualquer importação para evitar DeprecationWarning
if 'faiss' not in sys.modules:
    mock_faiss = types.ModuleType('faiss')
    
    class MockFaissIndex:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.d = 384
            self.ntotal = 0
            
        def add(self, vectors: Any) -> None:
            pass
            
        def search(self, query: Any, k: int) -> tuple[Any, Any]:
            import numpy as np
            return np.array([[0.1]]), np.array([[0]])
    
    mock_faiss.IndexFlatL2 = MockFaissIndex
    mock_faiss.IndexFlatIP = MockFaissIndex
    mock_faiss.read_index = lambda path: MockFaissIndex()
    mock_faiss.write_index = lambda index, path: None
    
    sys.modules['faiss'] = mock_faiss

from langchain.docstore.document import Document

from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import (
    FaissVetorStorage,
)


class TestFaissVetorStorage(unittest.TestCase):
    def setUp(self) -> None:
        """Set up a temporary directory for the tests."""
        self.test_dir = tempfile.mkdtemp()

        # Mock SERVICEHUB constants
        self.servicehub_patcher = patch(
            "smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage.SERVICEHUB"
        )
        self.mock_servicehub = self.servicehub_patcher.start()
        self.mock_servicehub.EMBEDDINGS_MODEL = "all-minilm-l6-v2"
        self.mock_servicehub.CHUNK_SIZE = 100
        self.mock_servicehub.CHUNK_OVERLAP = 10
        self.mock_servicehub.EMBEDDINGS_CLASS = "OllamaEmbeddings"  # String válida
        self.mock_servicehub.HUGGINGFACE_API_KEY = ""

        # Mock OllamaEmbeddings
        self.embeddings_patcher = patch(
            "smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage.OllamaEmbeddings"
        )
        self.mock_embeddings_class = self.embeddings_patcher.start()
        self.mock_embeddings_instance = MagicMock()
        self.mock_embeddings_class.return_value = self.mock_embeddings_instance

        # Mock FAISS
        self.faiss_patcher = patch(
            "smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage.FAISS"
        )
        self.mock_faiss = self.faiss_patcher.start()
        self.mock_vectordb = MagicMock()
        self.mock_faiss.from_documents.return_value = self.mock_vectordb
        self.mock_faiss.load_local.return_value = self.mock_vectordb

        # Reset the singleton instance before each test
        from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import _FaissVetorStorageMeta
        _FaissVetorStorageMeta._instances.clear()

        # Patch Path to control where the db is created
        self.path_patcher = patch(
            "smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage.Path"
        )
        mock_path = self.path_patcher.start()
        # When Path(__file__) is called, make its parent the temp directory
        mock_path.return_value.parent = Path(self.test_dir)
        self.db_path = str(Path(self.test_dir) / "banco_faiss")

    def tearDown(self) -> None:
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)
        self.servicehub_patcher.stop()
        self.embeddings_patcher.stop()
        self.faiss_patcher.stop()
        self.path_patcher.stop()

    def test_singleton_creation(self) -> None:
        """Test that the singleton pattern is correctly implemented."""
        instance1 = FaissVetorStorage()
        instance2 = FaissVetorStorage()
        self.assertIs(instance1, instance2)

    @patch("os.path.exists", return_value=False)
    def test_initialization_creates_new_db(self, mock_exists: MagicMock) -> None:
        """Test that a new database is created if one doesn't exist."""
        storage = FaissVetorStorage()
        self.mock_faiss.from_documents.assert_called()
        self.mock_vectordb.save_local.assert_called_with(self.db_path)

    @patch("os.path.exists", return_value=True)
    def test_initialization_loads_existing_db(self, mock_exists: MagicMock) -> None:
        """Test that an existing database is loaded."""
        storage = FaissVetorStorage()
        self.mock_faiss.load_local.assert_called_with(
            self.db_path,
            self.mock_embeddings_instance,
            allow_dangerous_deserialization=True,
        )
        self.mock_faiss.from_documents.assert_called()  # Called for dummy doc creation

    @patch("os.path.exists", return_value=True)
    def test_initialization_handles_load_error(self, mock_exists: MagicMock) -> None:
        """Test that it creates a new DB if loading fails."""
        self.mock_faiss.load_local.side_effect = Exception("Load error")
        storage = FaissVetorStorage()
        # Should fall back to creating a new one
        self.mock_faiss.from_documents.assert_called()

    @patch("os.path.exists", return_value=True)
    def test_write_documents(self, mock_exists: MagicMock) -> None:
        """Test writing documents to the vector store."""
        storage = FaissVetorStorage()
        docs = [Document(page_content="test content")]
        storage.write(docs)

        # Check that documents are added and saved
        self.mock_vectordb.add_documents.assert_called()
        self.mock_vectordb.save_local.assert_called_with(self.db_path)

    def test_write_invalid_chunks_raises_error(self) -> None:
        """Test that writing invalid chunks raises a ValueError."""
        storage = FaissVetorStorage()
        # An empty document content should result in no valid chunks
        docs = [Document(page_content=" ")]
        with self.assertRaises(ValueError) as cm:
            storage.write(docs)
        self.assertIn("Nenhum chunk válido encontrado", str(cm.exception))

    def test_write_add_documents_fails(self) -> None:
        """Test that write handles exceptions from add_documents."""
        storage = FaissVetorStorage()
        self.mock_vectordb.add_documents.side_effect = Exception("DB error")
        docs = [Document(page_content="test")]
        with self.assertRaises(ValueError) as cm:
            storage.write(docs)
        self.assertIn("Erro ao adicionar documentos ao banco de dados FAISS", str(cm.exception))

    def test_write_empty_list_raises_error(self) -> None:
        """Test that writing an empty list of documents raises a ValueError."""
        storage = FaissVetorStorage()
        with self.assertRaises(ValueError):
            storage.write([])

    def test_read_documents(self) -> None:
        """Test reading documents from the vector store."""
        storage = FaissVetorStorage()
        query = "test query"
        storage.read(query, k=10)

        # Check that similarity search is called
        self.mock_vectordb.similarity_search.assert_called_with(query, k=10)

    def test_remove_by_metadata(self) -> None:
        """Test removing documents by metadata."""
        storage = FaissVetorStorage()
        
        # Mock the vectordb to have proper structure for metadata search
        self.mock_vectordb.index_to_docstore_id = {"0": "doc1_id"}
        mock_doc = MagicMock()
        mock_doc.metadata = {"some_key": "some_value"}
        self.mock_vectordb.docstore.search.return_value = mock_doc
        
        result = storage.remove_by_metadata("some_key", "some_value")
        
        self.assertTrue(result)
        self.mock_vectordb.delete.assert_called_with(["doc1_id"])
        self.mock_vectordb.save_local.assert_called_with(self.db_path)

    def test_remove_by_metadata_no_match(self) -> None:
        """Test removing documents by metadata when no documents match."""
        storage = FaissVetorStorage()
        
        # Mock the vectordb to have proper structure but no matches
        self.mock_vectordb.index_to_docstore_id = {"0": "doc1_id"}
        mock_doc = MagicMock()
        mock_doc.metadata = {"other_key": "other_value"}
        self.mock_vectordb.docstore.search.return_value = mock_doc
        
        result = storage.remove_by_metadata("some_key", "some_value")
        
        self.assertFalse(result)
        self.mock_vectordb.delete.assert_not_called()

    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="file content")
    @patch("os.path.exists", return_value=True)
    def test_add_from_file_success(self, mock_exists, mock_open):
        """Test adding a document from a file successfully."""
        storage = FaissVetorStorage()
        result = storage.add_from_file("dummy/path.txt")
        self.assertTrue(result)
        self.mock_vectordb.add_documents.assert_called()
        self.mock_vectordb.save_local.assert_called_with(self.db_path)

    @patch("os.path.exists", return_value=False)
    def test_add_from_file_not_found(self, mock_exists):
        """Test that add_from_file returns False if the file does not exist."""
        storage = FaissVetorStorage()
        result = storage.add_from_file("nonexistent/path.txt")
        self.assertFalse(result)
        self.mock_vectordb.add_documents.assert_not_called()

    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="  ")
    @patch("os.path.exists", return_value=True)
    def test_add_from_file_empty_content(self, mock_exists, mock_open):
        """Test that add_from_file returns False for empty or whitespace-only files."""
        storage = FaissVetorStorage()
        result = storage.add_from_file("empty/path.txt")
        self.assertFalse(result)
        self.mock_vectordb.add_documents.assert_not_called()

    @patch("smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage.HuggingFaceInferenceAPIEmbeddings")
    def test_create_embeddings_huggingface(self, mock_hf_embeddings):
        """Test creation of HuggingFace embeddings."""
        self.mock_servicehub.EMBEDDINGS_CLASS = "HuggingFaceInferenceAPIEmbeddings"
        with patch.dict(os.environ, {"HUGGINGFACE_API_KEY": "test_key"}):
            storage = FaissVetorStorage()
            # Access internal method for testing purposes
            embeddings = storage._FaissVetorStorage__create_embeddings()
            mock_hf_embeddings.assert_called_with(api_key=SecretStr("test_key"), model_name="all-minilm-l6-v2")

    @patch("smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage.OpenAIEmbeddings")
    def test_create_embeddings_openai(self, mock_openai_embeddings):
        """Test creation of OpenAI embeddings."""
        self.mock_servicehub.EMBEDDINGS_CLASS = "OpenAIEmbeddings"
        storage = FaissVetorStorage()
        embeddings = storage._FaissVetorStorage__create_embeddings()
        mock_openai_embeddings.assert_called_with(model="all-minilm-l6-v2")


if __name__ == "__main__":
    unittest.main()

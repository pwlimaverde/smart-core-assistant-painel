import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain.docstore.document import Document

from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import (
    FaissVetorStorage,
)


class TestFaissVetorStorage(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for the tests."""
        self.test_dir = tempfile.mkdtemp()

        # Mock SERVICEHUB constants
        self.servicehub_patcher = patch(
            "smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage.SERVICEHUB"
        )
        self.mock_servicehub = self.servicehub_patcher.start()
        self.mock_servicehub.FAISS_MODEL = "all-minilm-l6-v2"
        self.mock_servicehub.CHUNK_SIZE = 100
        self.mock_servicehub.CHUNK_OVERLAP = 10

        # Mock OllamaEmbeddings
        self.embeddings_patcher = patch(
            "smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage.OllamaEmbeddings"
        )
        self.mock_embeddings = self.embeddings_patcher.start()
        self.mock_embeddings.return_value = MagicMock()

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

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)
        self.servicehub_patcher.stop()
        self.embeddings_patcher.stop()
        self.faiss_patcher.stop()
        self.path_patcher.stop()

    def test_singleton_creation(self):
        """Test that the singleton pattern is correctly implemented."""
        instance1 = FaissVetorStorage()
        instance2 = FaissVetorStorage()
        self.assertIs(instance1, instance2)

    @patch("os.path.exists", return_value=False)
    def test_initialization_creates_new_db(self, mock_exists):
        """Test that a new database is created if one doesn't exist."""
        storage = FaissVetorStorage()
        self.mock_faiss.from_documents.assert_called()
        storage._FaissVetorStorage__vectordb.save_local.assert_called_with(
            self.db_path
        )

    @patch("os.path.exists", return_value=True)
    def test_initialization_loads_existing_db(self, mock_exists):
        """Test that an existing database is loaded."""
        storage = FaissVetorStorage()
        self.mock_faiss.load_local.assert_called_with(
            self.db_path,
            storage._FaissVetorStorage__embeddings,
            allow_dangerous_deserialization=True,
        )
        self.mock_faiss.from_documents.assert_not_called()

    @patch("os.path.exists", return_value=True)
    def test_initialization_handles_load_error(self, mock_exists):
        """Test that it creates a new DB if loading fails."""
        self.mock_faiss.load_local.side_effect = Exception("Load error")
        storage = FaissVetorStorage()
        # Should fall back to creating a new one
        self.mock_faiss.from_documents.assert_called()

    @patch("os.path.exists", return_value=True)
    def test_write_documents(self, mock_exists):
        """Test writing documents to the vector store."""
        storage = FaissVetorStorage()
        docs = [Document(page_content="test content")]
        storage.write(docs)

        # Check that documents are added and saved
        self.mock_vectordb.add_documents.assert_called()
        self.mock_vectordb.save_local.assert_called_with(self.db_path)

    def test_write_invalid_chunks_raises_error(self):
        """Test that writing invalid chunks raises a ValueError."""
        storage = FaissVetorStorage()
        # An empty document content should result in no valid chunks
        docs = [Document(page_content=" ")]
        with self.assertRaises(ValueError) as cm:
            storage.write(docs)
        self.assertIn("Nenhum chunk válido encontrado", str(cm.exception))

    def test_write_add_documents_fails(self):
        """Test that write handles exceptions from add_documents."""
        storage = FaissVetorStorage()
        self.mock_vectordb.add_documents.side_effect = Exception("DB error")
        docs = [Document(page_content="test")]
        with self.assertRaises(ValueError) as cm:
            storage.write(docs)
        self.assertIn("Erro ao adicionar documentos ao banco FAISS", str(cm.exception))

    def test_write_empty_list_raises_error(self):
        """Test that writing an empty list of documents raises a ValueError."""
        storage = FaissVetorStorage()
        with self.assertRaises(ValueError):
            storage.write([])

    def test_read_documents(self):
        """Test reading documents from the vector store."""
        storage = FaissVetorStorage()
        query = "test query"
        storage.read(query, k=10)

        # Check that similarity search is called
        self.mock_vectordb.similarity_search.assert_called_with(query, k=10)

    def test_remove_by_metadata(self):
        """Test removing documents by metadata."""
        storage = FaissVetorStorage()
        # Mock the internal find_by_metadata to return some IDs
        with patch.object(
            storage, "_FaissVetorStorage__find_by_metadata", return_value=["doc1_id"]
        ) as mock_find:
            storage.remove_by_metadata("some_key", "some_value")
            mock_find.assert_called_with("some_key", "some_value")
            self.mock_vectordb.delete.assert_called_with(["doc1_id"])
            self.mock_vectordb.save_local.assert_called_with(self.db_path)

    def test_remove_by_metadata_no_match(self):
        """Test removing documents by metadata when no documents match."""
        storage = FaissVetorStorage()
        with patch.object(
            storage, "_FaissVetorStorage__find_by_metadata", return_value=[]
        ) as mock_find:
            storage.remove_by_metadata("some_key", "some_value")
            mock_find.assert_called_with("some_key", "some_value")
            self.mock_vectordb.delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()

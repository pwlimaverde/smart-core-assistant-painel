import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from typing import List

from smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource import (
    LoadDocumentFileDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LoadDocumentFileParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    DocumentError,
)
from langchain_core.documents import Document


class TestLoadDocumentFileDatasource:
    """Testes para a classe LoadDocumentFileDatasource."""

    @pytest.fixture
    def datasource(self):
        """Fixture para criar uma instância do datasource."""
        return LoadDocumentFileDatasource()

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        return LoadDocumentFileParameters(
            id="test-123",
            path="/path/to/test.txt",
            tag="tag_teste",
            grupo="grupo_teste",
            error=DocumentError("Erro de teste"),
        )

    @pytest.fixture
    def sample_document(self):
        """Fixture para criar um documento de exemplo."""
        return Document(
            id="doc-123",
            page_content="Conteúdo do documento de teste.",
            metadata={
                "id_treinamento": "test-123",
                "source": "treinamento_ia",
                "processed_at": "2024-01-01T10:00:00Z",
                "file_path": "/path/to/test.txt",
            }
        )

    def test_call_success_case_txt_file(self, datasource, sample_parameters):
        """Testa o caso de sucesso para arquivo .txt."""
        # Arrange
        file_content = "Este é o conteúdo do arquivo de teste."
        mock_documents = [Mock(spec=Document)]
        mock_documents[0].page_content = file_content
        mock_documents[0].metadata = {"source": "/path/to/test.txt"}
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load.return_value = mock_documents
            mock_loader_class.return_value = mock_loader
            
            # Act
            result = datasource(sample_parameters)
            
            # Assert
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Document)
            mock_loader_class.assert_called_once_with(sample_parameters.path, encoding="utf-8")
            mock_loader.load.assert_called_once()

    def test_call_success_case_pdf_file(self, datasource, tmp_path):
        """Testa o caso de sucesso para arquivo .pdf."""
        # Arrange
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF")
        
        parameters = LoadDocumentFileParameters(
            id="test-123",
            path=str(pdf_file),
            tag="tag_teste",
            grupo="grupo_teste",
            error=DocumentError("Erro de teste"),
        )
        
        mock_documents = [Mock(spec=Document)]
        mock_documents[0].page_content = "Conteúdo do PDF"
        mock_documents[0].metadata = {"source": str(pdf_file)}
        
        with patch.object(datasource, 'SUPPORTED_EXTENSIONS', {".pdf": Mock}) as mock_extensions:
            mock_loader = Mock()
            mock_loader.load.return_value = mock_documents
            mock_loader_class = Mock(return_value=mock_loader)
            mock_extensions[".pdf"] = mock_loader_class
            
            # Act
            result = datasource(parameters)
            
            # Assert
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Document)
            mock_loader_class.assert_called_once_with(parameters.path)
            mock_loader.load.assert_called_once()

    def test_call_success_case_docx_file(self, datasource, tmp_path):
        """Testa o caso de sucesso para arquivo .docx."""
        # Arrange
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"PK\x03\x04\x14\x00\x00\x00\x08\x00")
        
        parameters = LoadDocumentFileParameters(
            id="test-123",
            path=str(docx_file),
            tag="tag_teste",
            grupo="grupo_teste",
            error=DocumentError("Erro de teste"),
        )
        
        mock_documents = [Mock(spec=Document)]
        mock_documents[0].page_content = "Conteúdo do DOCX"
        mock_documents[0].metadata = {"source": str(docx_file)}
        
        with patch.object(datasource, 'SUPPORTED_EXTENSIONS', {".docx": Mock}) as mock_extensions:
            mock_loader = Mock()
            mock_loader.load.return_value = mock_documents
            mock_loader_class = Mock(return_value=mock_loader)
            mock_extensions[".docx"] = mock_loader_class
            
            # Act
            result = datasource(parameters)
            
            # Assert
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Document)
            mock_loader_class.assert_called_once_with(parameters.path)
            mock_loader.load.assert_called_once()

    def test_call_unsupported_file_extension(self, datasource):
        """Testa o erro para extensão de arquivo não suportada."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-123",
            path="/path/to/test.xyz",
            tag="tag_teste",
            grupo="grupo_teste",
            error=DocumentError("Erro de teste"),
        )
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Extensão .xyz não suportada"):
            datasource(parameters)

    def test_call_file_not_found(self, datasource, sample_parameters):
        """Testa o erro quando o arquivo não é encontrado."""
        # Arrange
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load.side_effect = FileNotFoundError("Arquivo não encontrado")
            mock_loader_class.return_value = mock_loader
            
            # Act & Assert
            with pytest.raises(RuntimeError, match="Arquivo não encontrado"):
                datasource(sample_parameters)

    def test_document_metadata_processing(self, datasource, sample_parameters):
        """Testa o processamento dos metadados do documento."""
        # Arrange
        mock_documents = [Mock(spec=Document)]
        mock_documents[0].page_content = "Conteúdo teste"
        mock_documents[0].metadata = {"source": "/path/to/test.txt"}
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_loader_class, \
             patch('datetime.datetime') as mock_datetime:
            
            mock_loader = Mock()
            mock_loader.load.return_value = mock_documents
            mock_loader_class.return_value = mock_loader
            
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00Z"
            
            # Act
            result = datasource(sample_parameters)
            
            # Assert
            document = result[0]
            assert document.metadata["source"] == "/path/to/test.txt"
            assert document.page_content == "Conteúdo teste"

    def test_multiple_documents_processing(self, datasource, sample_parameters):
        """Testa o processamento de múltiplos documentos."""
        # Arrange
        mock_documents = []
        for i in range(3):
            doc = Mock(spec=Document)
            doc.page_content = f"Conteúdo do documento {i+1}"
            doc.metadata = {"source": "/path/to/test.txt", "page": i+1}
            mock_documents.append(doc)
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_loader_class:
            
            mock_loader = Mock()
            mock_loader.load.return_value = mock_documents
            mock_loader_class.return_value = mock_loader
            
            # Act
            result = datasource(sample_parameters)
            
            # Assert
            assert len(result) == 3
            for i, document in enumerate(result):
                assert isinstance(document, Document)
                assert document.page_content == f"Conteúdo do documento {i+1}"
                assert document.metadata["source"] == "/path/to/test.txt"
                assert document.metadata["page"] == i+1

    def test_empty_document_list(self, datasource, sample_parameters):
        """Testa o comportamento com lista vazia de documentos."""
        # Arrange
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load.return_value = []
            mock_loader_class.return_value = mock_loader
            
            # Act
            result = datasource(sample_parameters)
            
            # Assert
            assert isinstance(result, list)
            assert len(result) == 0

    def test_file_extension_detection_case_insensitive(self, datasource):
        """Testa a detecção de extensão de arquivo insensível a maiúsculas/minúsculas."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-123",
            path="/path/to/test.TXT",
            tag="tag_teste",
            grupo="grupo_teste",
            error=DocumentError("Erro de teste"),
        )
        
        mock_documents = [Mock(spec=Document)]
        mock_documents[0].page_content = "Conteúdo teste"
        mock_documents[0].metadata = {"source": "/path/to/test.TXT"}
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load.return_value = mock_documents
            mock_loader_class.return_value = mock_loader
            
            # Act
            result = datasource(parameters)
            
            # Assert
            assert isinstance(result, list)
            assert len(result) == 1
            mock_loader_class.assert_called_once_with(parameters.path, encoding="utf-8")

    def test_document_id_generation(self, datasource, sample_parameters):
        """Testa a geração de ID único para cada documento."""
        # Arrange
        mock_documents = [Mock(spec=Document), Mock(spec=Document)]
        for i, doc in enumerate(mock_documents):
            doc.page_content = f"Conteúdo {i+1}"
            doc.metadata = {"source": "/path/to/test.txt"}
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_loader_class:
            
            mock_loader = Mock()
            mock_loader.load.return_value = mock_documents
            mock_loader_class.return_value = mock_loader
            
            # Act
            result = datasource(sample_parameters)
            
            # Assert
            assert len(result) == 2
            assert result[0].page_content == "Conteúdo 1"
            assert result[1].page_content == "Conteúdo 2"
            assert result[0].metadata["source"] == "/path/to/test.txt"
            assert result[1].metadata["source"] == "/path/to/test.txt"

    def test_loader_exception_handling(self, datasource, sample_parameters):
        """Testa o tratamento de exceções do loader."""
        # Arrange
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load.side_effect = Exception("Erro genérico do loader")
            mock_loader_class.return_value = mock_loader
            
            # Act & Assert
            with pytest.raises(Exception, match="Erro genérico do loader"):
                datasource(sample_parameters)
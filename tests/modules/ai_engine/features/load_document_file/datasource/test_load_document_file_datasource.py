"""Testes para LoadDocumentFileDatasource."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from langchain.docstore.document import Document

from smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource import (
    LoadDocumentFileDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LoadDocumentFileParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import DocumentError


class TestLoadDocumentFileDatasource:
    """Testes para a classe LoadDocumentFileDatasource."""

    @pytest.fixture
    def datasource(self):
        """Fixture para criar uma instância do datasource."""
        return LoadDocumentFileDatasource()

    def test_datasource_inheritance(self, datasource):
        """Testa se o datasource herda corretamente da classe base."""
        # Verifica se é uma instância válida com o método esperado
        assert hasattr(datasource, '__call__')
        assert callable(datasource)

    def test_supported_extensions_constant(self, datasource):
        """Testa se as extensões suportadas estão definidas corretamente."""
        expected_extensions = {
            ".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".csv"
        }
        actual_extensions = set(datasource.SUPPORTED_EXTENSIONS.keys())
        assert actual_extensions == expected_extensions

    def test_supported_extensions_mapping(self, datasource):
        """Testa se o mapeamento de extensões está correto."""
        from langchain_community.document_loaders import (
            Docx2txtLoader,
            PyPDFLoader,
            TextLoader,
            UnstructuredExcelLoader,
        )
        
        assert datasource.SUPPORTED_EXTENSIONS[".pdf"] == PyPDFLoader
        assert datasource.SUPPORTED_EXTENSIONS[".doc"] == Docx2txtLoader
        assert datasource.SUPPORTED_EXTENSIONS[".docx"] == Docx2txtLoader
        assert datasource.SUPPORTED_EXTENSIONS[".txt"] == TextLoader
        assert datasource.SUPPORTED_EXTENSIONS[".xlsx"] == UnstructuredExcelLoader
        assert datasource.SUPPORTED_EXTENSIONS[".xls"] == UnstructuredExcelLoader
        assert datasource.SUPPORTED_EXTENSIONS[".csv"] == TextLoader

    @patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader')
    def test_call_txt_file_success(self, mock_text_loader, datasource):
        """Testa carregamento bem-sucedido de arquivo .txt."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-doc",
            path="/path/to/test.txt",
            tag="test-tag",
            grupo="test-group",
            error=DocumentError("Test error"),
        )
        
        mock_document = Document(page_content="Test content", metadata={"source": "/path/to/test.txt"})
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_document]
        mock_text_loader.return_value = mock_loader_instance
        
        # Act
        result = datasource(parameters)
        
        # Assert
        assert result == [mock_document]
        mock_text_loader.assert_called_once_with("/path/to/test.txt", encoding="utf-8")
        mock_loader_instance.load.assert_called_once()

    @patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader')
    def test_call_csv_file_success(self, mock_text_loader, datasource):
        """Testa carregamento bem-sucedido de arquivo .csv."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-csv",
            path="/path/to/test.csv",
            tag="csv-tag",
            grupo="csv-group",
            error=DocumentError("Test error"),
        )
        
        mock_document = Document(page_content="CSV,Content", metadata={"source": "/path/to/test.csv"})
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_document]
        mock_text_loader.return_value = mock_loader_instance
        
        # Act
        result = datasource(parameters)
        
        # Assert
        assert result == [mock_document]
        mock_text_loader.assert_called_once_with("/path/to/test.csv", encoding="utf-8")

    def test_call_pdf_file_success(self, datasource):
        """Testa carregamento bem-sucedido de arquivo .pdf."""
        # Arrange - Cria um arquivo temporário para simular o PDF
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF")
            temp_pdf_path = temp_pdf.name
        
        try:
            parameters = LoadDocumentFileParameters(
                id="test-pdf",
                path=temp_pdf_path,
                tag="pdf-tag",
                grupo="pdf-group",
                error=DocumentError("Test error"),
            )
            
            # Mocka apenas o load method para evitar processamento real do PDF
            with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.PyPDFLoader.load') as mock_load:
                mock_document = Document(page_content="PDF content", metadata={"source": temp_pdf_path})
                mock_load.return_value = [mock_document]
                
                # Act
                result = datasource(parameters)
                
                # Assert
                assert result == [mock_document]
                mock_load.assert_called_once()
        finally:
            # Limpa o arquivo temporário
            os.unlink(temp_pdf_path)

    def test_call_docx_file_success(self, datasource):
        """Testa carregamento bem-sucedido de arquivo .docx."""
        # Arrange - Cria um arquivo temporário
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_docx:
            temp_docx.write(b"fake docx content")  # Conteúdo fake para teste
            temp_docx_path = temp_docx.name
        
        try:
            parameters = LoadDocumentFileParameters(
                id="test-docx",
                path=temp_docx_path,
                tag="docx-tag",
                grupo="docx-group",
                error=DocumentError("Test error"),
            )
            
            # Mocka apenas o load method
            with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.Docx2txtLoader.load') as mock_load:
                mock_document = Document(page_content="DOCX content", metadata={})
                mock_load.return_value = [mock_document]
                
                # Act
                result = datasource(parameters)
                
                # Assert
                assert result == [mock_document]
                mock_load.assert_called_once()
        finally:
            os.unlink(temp_docx_path)

    def test_call_doc_file_success(self, datasource):
        """Testa carregamento bem-sucedido de arquivo .doc."""
        # Arrange - Cria um arquivo temporário
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as temp_doc:
            temp_doc.write(b"fake doc content")
            temp_doc_path = temp_doc.name
        
        try:
            parameters = LoadDocumentFileParameters(
                id="test-doc",
                path=temp_doc_path,
                tag="doc-tag",
                grupo="doc-group",
                error=DocumentError("Test error"),
            )
            
            # Mocka apenas o load method
            with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.Docx2txtLoader.load') as mock_load:
                mock_document = Document(page_content="DOC content", metadata={})
                mock_load.return_value = [mock_document]
                
                # Act
                result = datasource(parameters)
                
                # Assert
                assert result == [mock_document]
                mock_load.assert_called_once()
        finally:
            os.unlink(temp_doc_path)

    def test_call_xlsx_file_success(self, datasource):
        """Testa carregamento bem-sucedido de arquivo .xlsx."""
        # Arrange - Cria um arquivo temporário
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_xlsx:
            temp_xlsx.write(b"fake xlsx content")
            temp_xlsx_path = temp_xlsx.name
        
        try:
            parameters = LoadDocumentFileParameters(
                id="test-xlsx",
                path=temp_xlsx_path,
                tag="xlsx-tag",
                grupo="xlsx-group",
                error=DocumentError("Test error"),
            )
            
            # Mocka apenas o load method
            with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.UnstructuredExcelLoader.load') as mock_load:
                mock_document = Document(page_content="Excel content", metadata={})
                mock_load.return_value = [mock_document]
                
                # Act
                result = datasource(parameters)
                
                # Assert
                assert result == [mock_document]
                mock_load.assert_called_once()
        finally:
            os.unlink(temp_xlsx_path)

    def test_call_xls_file_success(self, datasource):
        """Testa carregamento bem-sucedido de arquivo .xls."""
        # Arrange - Cria um arquivo temporário
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as temp_xls:
            temp_xls.write(b"fake xls content")
            temp_xls_path = temp_xls.name
        
        try:
            parameters = LoadDocumentFileParameters(
                id="test-xls",
                path=temp_xls_path,
                tag="xls-tag",
                grupo="xls-group",
                error=DocumentError("Test error"),
            )
            
            # Mocka apenas o load method
            with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.UnstructuredExcelLoader.load') as mock_load:
                mock_document = Document(page_content="XLS content", metadata={})
                mock_load.return_value = [mock_document]
                
                # Act
                result = datasource(parameters)
                
                # Assert
                assert result == [mock_document]
                mock_load.assert_called_once()
        finally:
            os.unlink(temp_xls_path)

    def test_call_unsupported_extension_raises_value_error(self, datasource):
        """Testa se ValueError é levantado para extensão não suportada."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-unsupported",
            path="/path/to/test.xyz",
            tag="unsupported-tag",
            grupo="unsupported-group",
            error=DocumentError("Test error"),
        )
        
        # Act & Assert
        with pytest.raises(RuntimeError, match=r"Falha carregar o documento 'test-unsupported'.*Extensão \.xyz não suportada"):
            datasource(parameters)

    def test_call_case_insensitive_extension(self, datasource):
        """Testa se extensões são tratadas de forma case-insensitive."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-case",
            path="/path/to/test.TXT",
            tag="case-tag",
            grupo="case-group",
            error=DocumentError("Test error"),
        )
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_text_loader:
            mock_loader_instance = Mock()
            mock_loader_instance.load.return_value = [Document(page_content="content")]
            mock_text_loader.return_value = mock_loader_instance
            
            # Act
            result = datasource(parameters)
            
            # Assert
            assert len(result) == 1
            mock_text_loader.assert_called_once_with("/path/to/test.TXT", encoding="utf-8")

    @patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader')
    def test_call_loader_exception_raises_runtime_error(self, mock_text_loader, datasource):
        """Testa se RuntimeError é levantado quando o loader falha."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-fail",
            path="/path/to/test.txt",
            tag="fail-tag",
            grupo="fail-group",
            error=DocumentError("Test error"),
        )
        
        mock_text_loader.side_effect = FileNotFoundError("File not found")
        
        # Act & Assert
        with pytest.raises(RuntimeError, match=r"Falha carregar o documento 'test-fail'.*File not found"):
            datasource(parameters)

    @patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader')
    def test_call_load_method_exception_raises_runtime_error(self, mock_text_loader, datasource):
        """Testa se RuntimeError é levantado quando o método load falha."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-load-fail",
            path="/path/to/test.txt",
            tag="load-fail-tag",
            grupo="load-fail-group",
            error=DocumentError("Test error"),
        )
        
        mock_loader_instance = Mock()
        mock_loader_instance.load.side_effect = IOError("IO Error")
        mock_text_loader.return_value = mock_loader_instance
        
        # Act & Assert
        with pytest.raises(RuntimeError, match=r"Falha carregar o documento 'test-load-fail'.*IO Error"):
            datasource(parameters)

    def test_call_multiple_documents_returned(self, datasource):
        """Testa se múltiplos documentos são retornados corretamente."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-multi",
            path="/path/to/test.txt",
            tag="multi-tag",
            grupo="multi-group",
            error=DocumentError("Test error"),
        )
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.TextLoader') as mock_text_loader:
            doc1 = Document(page_content="Content 1", metadata={"page": 1})
            doc2 = Document(page_content="Content 2", metadata={"page": 2})
            
            mock_loader_instance = Mock()
            mock_loader_instance.load.return_value = [doc1, doc2]
            mock_text_loader.return_value = mock_loader_instance
            
            # Act
            result = datasource(parameters)
            
            # Assert
            assert len(result) == 2
            assert result[0] == doc1
            assert result[1] == doc2

    def test_path_suffix_extraction(self, datasource):
        """Testa se a extração da extensão do arquivo funciona corretamente."""
        # Arrange - Cria um arquivo PDF temporário real com nome complexo
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".name.pdf", delete=False) as temp_pdf:
            # Cria um PDF válido mínimo
            temp_pdf.write(b"%PDF-1.4\n1 0 obj\n<<>>\nstream\nBT\n/F1 12 Tf\n100 100 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 2\n0000000000 65535 f \n0000000009 00000 n \ntrailer\n<<\n/Size 2\n/Root 1 0 R\n>>\nstartxref\n74\n%%EOF")
            temp_pdf_path = temp_pdf.name
        
        try:
            parameters = LoadDocumentFileParameters(
                id="test-path",
                path=temp_pdf_path,
                tag="path-tag",
                grupo="path-group",
                error=DocumentError("Test error"),
            )
            
            with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource.PyPDFLoader.load') as mock_load:
                mock_document = Document(page_content="PDF content", metadata={})
                mock_load.return_value = [mock_document]
                
                # Act
                result = datasource(parameters)
                
                # Assert
                assert len(result) == 1
                assert result[0] == mock_document
                mock_load.assert_called_once()
        finally:
            os.unlink(temp_pdf_path)

    def test_empty_path_raises_runtime_error(self, datasource):
        """Testa se caminho vazio levanta RuntimeError."""
        # Arrange
        parameters = LoadDocumentFileParameters(
            id="test-empty",
            path="",
            tag="empty-tag",
            grupo="empty-group",
            error=DocumentError("Test error"),
        )
        
        # Act & Assert
        with pytest.raises(RuntimeError, match=r"Falha carregar o documento 'test-empty'"):
            datasource(parameters)

    def test_docstring_and_metadata(self, datasource):
        """Testa se a documentação está presente."""
        assert hasattr(datasource, '__call__')
        assert datasource.__call__.__doc__ is not None
        assert "Carrega um arquivo do caminho especificado" in datasource.__call__.__doc__
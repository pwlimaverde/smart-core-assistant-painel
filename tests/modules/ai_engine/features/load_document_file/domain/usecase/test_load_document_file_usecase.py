import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)
from langchain_core.documents import Document

from smart_core_assistant_painel.modules.ai_engine.features.load_document_file.domain.usecase.load_document_file_usecase import (
    LoadDocumentFileUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LoadDocumentFileParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import DocumentError


class TestLoadDocumentFileUseCase:
    """Testes para a classe LoadDocumentFileUseCase."""

    @pytest.fixture
    def mock_datasource(self):
        """Fixture para criar um mock do datasource."""
        return Mock()

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        return LoadDocumentFileParameters(
            id="doc_123",
            path="/path/to/document.pdf",
            tag="tag_teste",
            grupo="grupo_teste",
            error=DocumentError("Erro de teste de documento"),
        )

    @pytest.fixture
    def usecase(self, mock_datasource):
        """Fixture para criar uma instância do usecase."""
        return LoadDocumentFileUseCase(mock_datasource)

    @pytest.fixture
    def sample_documents(self):
        """Fixture para criar documentos de exemplo."""
        return [
            Document(
                page_content="Conteúdo do documento 1",
                metadata={"source": "/path/to/doc1.pdf"}
            ),
            Document(
                page_content="Conteúdo do documento 2",
                metadata={"source": "/path/to/doc2.pdf"}
            ),
        ]

    def test_call_success_case(self, usecase, sample_parameters, sample_documents):
        """Testa o caso de sucesso da chamada do usecase."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(sample_documents)
        ), patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.domain.usecase.load_document_file_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert isinstance(result.result, list)
            assert len(result.result) == 2
            
            # Verifica se os metadados foram adicionados corretamente
            for doc in result.result:
                assert doc.id == "doc_123"  # id é atributo do documento
                assert doc.metadata["id_treinamento"] == "doc_123"
                assert doc.metadata["tag"] == "tag_teste"
                assert doc.metadata["grupo"] == "grupo_teste"
                assert doc.metadata["source"] == "treinamento_ia"
                assert "processed_at" in doc.metadata
                assert "T" in doc.metadata["processed_at"]  # Formato ISO

    def test_call_error_from_datasource(self, usecase, sample_parameters):
        """Testa o caso de erro retornado pelo datasource."""
        # Arrange
        error_message = "Erro ao carregar documento"
        
        with patch.object(
            usecase, '_resultDatasource', return_value=ErrorReturn(error_message)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, ErrorReturn)
            assert isinstance(result.result, DocumentError)
            assert result.result.message == "Erro ao obter dados do datasource."

    def test_parameters_validation(self, mock_datasource):
        """Testa a validação dos parâmetros de entrada."""
        # Arrange
        usecase = LoadDocumentFileUseCase(mock_datasource)
        invalid_params = None
        
        # Mock _resultDatasource para retornar sucesso com documentos
        # Isso fará com que o usecase tente acessar parameters.id, causando AttributeError
        sample_docs = [Document(page_content="test", metadata={})]
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(sample_docs)
        ):
            # Act & Assert
            with pytest.raises(AttributeError, match="'NoneType' object has no attribute"):
                usecase(invalid_params)

    def test_empty_documents_list(self, usecase, sample_parameters):
        """Testa o comportamento com lista vazia de documentos."""
        # Arrange
        empty_documents = []
        
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(empty_documents)
        ):
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert isinstance(result.result, list)
            assert len(result.result) == 0

    def test_single_document(self, usecase, sample_parameters):
        """Testa o processamento de um único documento."""
        # Arrange
        single_document = [
            Document(
                page_content="Conteúdo único",
                metadata={"source": "/path/to/single.pdf"}
            )
        ]
        
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(single_document)
        ), patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.domain.usecase.load_document_file_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert len(result.result) == 1
            doc = result.result[0]
            assert doc.page_content == "Conteúdo único"
            assert doc.id == "doc_123"  # id é atributo do documento
            assert doc.metadata["id_treinamento"] == "doc_123"
            assert doc.metadata["tag"] == "tag_teste"
            assert doc.metadata["grupo"] == "grupo_teste"
            assert doc.metadata["source"] == "treinamento_ia"

    def test_datasource_call_parameters(self, usecase, sample_parameters, sample_documents):
        """Testa se o datasource é chamado com os parâmetros corretos."""
        # Arrange
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(sample_documents)
        ) as mock_result_datasource:
            # Act
            usecase(sample_parameters)
            
            # Assert
            mock_result_datasource.assert_called_once_with(
                parameters=sample_parameters, datasource=usecase._datasource
            )

    def test_metadata_processing(self, usecase, sample_parameters):
        """Testa o processamento correto dos metadados."""
        # Arrange
        document_with_existing_metadata = [
            Document(
                page_content="Teste",
                metadata={
                    "source": "/original/path.pdf",
                    "existing_key": "existing_value"
                }
            )
        ]
        
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(document_with_existing_metadata)
        ), patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.domain.usecase.load_document_file_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            doc = result.result[0]
            # Verifica se os metadados existentes foram preservados
            assert doc.metadata["existing_key"] == "existing_value"
            # Verifica se os novos metadados foram adicionados
            assert doc.id == "doc_123"  # id é atributo do documento
            assert doc.metadata["id_treinamento"] == "doc_123"
            assert doc.metadata["source"] == "treinamento_ia"  # Sobrescrito

    def test_large_document_list(self, usecase, sample_parameters):
        """Testa o processamento de uma lista grande de documentos."""
        # Arrange
        large_document_list = [
            Document(
                page_content=f"Conteúdo do documento {i}",
                metadata={"source": f"/path/to/doc{i}.pdf"}
            )
            for i in range(100)
        ]
        
        with patch.object(
            usecase, '_resultDatasource', return_value=SuccessReturn(large_document_list)
        ), patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_file.domain.usecase.load_document_file_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            assert len(result.result) == 100
            # Verifica alguns documentos aleatórios
            for i in [0, 50, 99]:
                doc = result.result[i]
                assert doc.id == "doc_123"  # id é atributo do documento
                assert doc.metadata["id_treinamento"] == "doc_123"
                assert doc.metadata["tag"] == "tag_teste"
                assert doc.metadata["grupo"] == "grupo_teste"
                assert doc.metadata["source"] == "treinamento_ia"
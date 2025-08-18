import pytest
from unittest.mock import patch
from datetime import datetime
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)
from langchain_core.documents import Document

from smart_core_assistant_painel.modules.ai_engine import (
    DocumentError,
    LoadDocumentConteudoParameters,
)
from smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase import (
    LoadDocumentConteudoUseCase,
)


class TestLoadDocumentConteudoUseCase:
    """Testes para a classe LoadDocumentConteudoUseCase."""

    @pytest.fixture
    def sample_parameters(self):
        """Fixture para criar parâmetros de exemplo."""
        return LoadDocumentConteudoParameters(
            id="doc_456",
            conteudo="Este é o conteúdo do documento de teste.",
            tag="tag_conteudo",
            grupo="grupo_conteudo",
            error=DocumentError("Erro de teste de documento"),
        )

    @pytest.fixture
    def usecase(self):
        """Fixture para criar uma instância do usecase."""
        return LoadDocumentConteudoUseCase()

    def test_call_success_case(self, usecase, sample_parameters):
        """Testa o caso de sucesso da chamada do usecase."""
        # Act
        result = usecase(sample_parameters)
        
        # Assert
        assert isinstance(result, SuccessReturn)
        assert isinstance(result.result, list)
        assert len(result.result) == 1
        
        document = result.result[0]
        assert isinstance(document, Document)
        assert document.page_content == sample_parameters.conteudo
        assert document.id == sample_parameters.id
        
        # Verifica metadados
        assert document.metadata["id_treinamento"] == str(sample_parameters.id)
        assert document.metadata["tag"] == sample_parameters.tag
        assert document.metadata["grupo"] == sample_parameters.grupo
        assert document.metadata["source"] == "treinamento_ia"
        assert "processed_at" in document.metadata
        # Verifica se processed_at está no formato ISO
        assert "T" in document.metadata["processed_at"]

    def test_call_with_empty_content(self, usecase):
        """Testa o comportamento com conteúdo vazio."""
        # Arrange
        empty_parameters = LoadDocumentConteudoParameters(
            id="doc_empty",
            conteudo="",
            tag="tag_empty",
            grupo="grupo_empty",
            error=DocumentError("Erro de teste"),
        )
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(empty_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            document = result.result[0]
            assert document.page_content == ""
            assert document.metadata["id_treinamento"] == "doc_empty"

    def test_call_with_large_content(self, usecase):
        """Testa o comportamento com conteúdo grande."""
        # Arrange
        large_content = "Conteúdo muito grande " * 1000
        large_parameters = LoadDocumentConteudoParameters(
            id="doc_large",
            conteudo=large_content,
            tag="tag_large",
            grupo="grupo_large",
            error=DocumentError("Erro de teste"),
        )
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(large_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            document = result.result[0]
            assert document.page_content == large_content
            assert len(document.page_content) > 1000

    def test_call_with_special_characters(self, usecase):
        """Testa o comportamento com caracteres especiais."""
        # Arrange
        special_content = "Conteúdo com acentos: ção, ã, é, ü, ñ, 中文, 🚀"
        special_parameters = LoadDocumentConteudoParameters(
            id="doc_special",
            conteudo=special_content,
            tag="tag_special",
            grupo="grupo_special",
            error=DocumentError("Erro de teste"),
        )
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(special_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            document = result.result[0]
            assert document.page_content == special_content

    def test_parameters_validation_none(self, usecase):
        """Testa a validação com parâmetros None."""
        # Arrange
        invalid_params = None
        
        # Act & Assert
        # Quando parameters é None, o usecase tenta acessar parameters.error
        # causando AttributeError
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute"):
            usecase(invalid_params)

    def test_exception_handling(self, usecase, sample_parameters):
        """Testa o tratamento de exceções durante a criação do documento."""
        # Arrange
        # Simula uma exceção durante a criação do Document
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase.Document') as mock_document:
            mock_document.side_effect = Exception("Erro na criação do documento")
            
            # Act
            result = usecase(sample_parameters)
            
            # Assert
            assert isinstance(result, ErrorReturn)
            assert "Erro de teste de documento" in result.result.message
            assert "Exception: Erro na criação do documento" in result.result.message

    def test_metadata_formatting(self, usecase, sample_parameters):
        """Testa a formatação correta dos metadados."""
        # Act
        result = usecase(sample_parameters)
        
        # Assert
        document = result.result[0]
        assert "processed_at" in document.metadata
        assert "T" in document.metadata["processed_at"]  # Formato ISO
        assert document.metadata["source"] == "treinamento_ia"
        assert document.metadata["id_treinamento"] == str(sample_parameters.id)
        assert document.metadata["tag"] == sample_parameters.tag
        assert document.metadata["grupo"] == sample_parameters.grupo

    def test_multiline_content(self, usecase):
        """Testa o comportamento com conteúdo multilinha."""
        # Arrange
        multiline_content = """Primeira linha
Segunda linha
Terceira linha

Quinta linha após linha vazia"""
        multiline_parameters = LoadDocumentConteudoParameters(
            id="doc_multiline",
            conteudo=multiline_content,
            tag="tag_multiline",
            grupo="grupo_multiline",
            error=DocumentError("Erro de teste"),
        )
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(multiline_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            document = result.result[0]
            assert document.page_content == multiline_content
            assert "\n" in document.page_content

    def test_whitespace_content(self, usecase):
        """Testa o comportamento com conteúdo apenas com espaços em branco."""
        # Arrange
        whitespace_content = "   \n\t   \r\n   "
        whitespace_parameters = LoadDocumentConteudoParameters(
            id="doc_whitespace",
            conteudo=whitespace_content,
            tag="tag_whitespace",
            grupo="grupo_whitespace",
            error=DocumentError("Erro de teste"),
        )
        
        with patch('smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            # Act
            result = usecase(whitespace_parameters)
            
            # Assert
            assert isinstance(result, SuccessReturn)
            document = result.result[0]
            assert document.page_content == whitespace_content
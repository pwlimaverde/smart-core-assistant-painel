import unittest
from unittest.mock import MagicMock, patch

from langchain.docstore.document import Document
from py_return_success_or_error import ErrorReturn, SuccessReturn

from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    DocumentError,
)


class TestFeaturesCompose(unittest.TestCase):
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentConteudoUseCase"
    )
    def test_load_document_conteudo_success(self, mock_use_case):
        # Arrange
        mock_instance = mock_use_case.return_value
        expected_docs = [Document(page_content="Test content")]
        mock_instance.return_value = SuccessReturn(expected_docs)

        # Act
        result = FeaturesCompose.load_document_conteudo(
            id="1", conteudo="Test", tag="test", grupo="test"
        )

        # Assert
        self.assertEqual(result, expected_docs)
        mock_use_case.assert_called_once()
        mock_instance.assert_called_once()

    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentConteudoUseCase"
    )
    def test_load_document_conteudo_error(self, mock_use_case):
        # Arrange
        mock_instance = mock_use_case.return_value
        error = DocumentError("Test error")
        mock_instance.return_value = ErrorReturn(error)

        # Act & Assert
        with self.assertRaises(DocumentError):
            FeaturesCompose.load_document_conteudo(
                id="1", conteudo="Test", tag="test", grupo="test"
            )

    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentFileUseCase"
    )
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentFileDatasource"
    )
    def test_load_document_file_success(
        self, mock_datasource, mock_use_case
    ):
        # Arrange
        mock_use_case_instance = mock_use_case.return_value
        expected_docs = [Document(page_content="Test file content")]
        mock_use_case_instance.return_value = SuccessReturn(expected_docs)

        # Act
        result = FeaturesCompose.load_document_file(
            id="1", path="/fake/path", tag="test", grupo="test"
        )

        # Assert
        self.assertEqual(result, expected_docs)
        mock_datasource.assert_called_once()
        mock_use_case.assert_called_once()
        mock_use_case_instance.assert_called_once()

    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentFileUseCase"
    )
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentFileDatasource"
    )
    def test_load_document_file_error(self, mock_datasource, mock_use_case):
        # Arrange
        mock_use_case_instance = mock_use_case.return_value
        error = DocumentError("Test error")
        mock_use_case_instance.return_value = ErrorReturn(error)

        # Act & Assert
        with self.assertRaises(DocumentError):
            FeaturesCompose.load_document_file(
                id="1", path="/fake/path", tag="test", grupo="test"
            )


    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseConteudoLangchainDatasource"
    )
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseConteudoUseCase"
    )
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB"
    )
    def test_pre_analise_ia_treinamento_success(
        self, mock_service_hub, mock_use_case, mock_datasource
    ):
        # Arrange
        mock_use_case_instance = mock_use_case.return_value
        mock_use_case_instance.return_value = SuccessReturn("Analise")

        # Act
        result = FeaturesCompose.pre_analise_ia_treinamento(context="Test context")

        # Assert
        self.assertEqual(result, "Analise")
        mock_datasource.assert_called_once()
        mock_use_case.assert_called_once()
        mock_use_case_instance.assert_called_once()

    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseConteudoLangchainDatasource"
    )
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseConteudoUseCase"
    )
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB"
    )
    def test_melhoria_ia_treinamento_success(
        self, mock_service_hub, mock_use_case, mock_datasource
    ):
        # Arrange
        mock_use_case_instance = mock_use_case.return_value
        mock_use_case_instance.return_value = SuccessReturn("Melhoria")

        # Act
        result = FeaturesCompose.melhoria_ia_treinamento(context="Test context")

        # Assert
        self.assertEqual(result, "Melhoria")
        mock_datasource.assert_called_once()
        mock_use_case.assert_called_once()
        mock_use_case_instance.assert_called_once()


    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnalisePreviaMensagemLangchainDatasource"
    )
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnalisePreviaMensagemUsecase"
    )
    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB"
    )
    def test_analise_previa_mensagem_success(
        self, mock_service_hub, mock_use_case, mock_datasource
    ):
        # Arrange
        mock_use_case_instance = mock_use_case.return_value
        expected_result = ("intent", "entities")
        mock_use_case_instance.return_value = SuccessReturn(expected_result)

        # Act
        result = FeaturesCompose.analise_previa_mensagem(
            historico_atendimento={}, context="Test context"
        )

        # Assert
        self.assertEqual(result, expected_result)
        mock_datasource.assert_called_once()
        mock_use_case.assert_called_once()
        mock_use_case_instance.assert_called_once()

    def test_converter_contexto(self):
        # Arrange
        metadata = {"type": "image"}

        # Act
        result = FeaturesCompose._converter_contexto(metadata)

        # Assert
        self.assertEqual(result, "contexto")

    @patch(
        "smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadMensageDataUseCase"
    )
    def test_load_message_data_success(self, mock_use_case):
        # Arrange
        mock_instance = mock_use_case.return_value
        mock_message_data = MagicMock()
        mock_message_data.metadados = {}
        mock_instance.return_value = SuccessReturn(mock_message_data)

        # Act
        result = FeaturesCompose.load_message_data(data={})

        # Assert
        self.assertEqual(result, mock_message_data)
        mock_use_case.assert_called_once()
        mock_instance.assert_called_once()


if __name__ == "__main__":
    unittest.main()

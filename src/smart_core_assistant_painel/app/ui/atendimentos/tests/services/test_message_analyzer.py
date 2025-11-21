import pytest
from unittest.mock import patch, MagicMock

# Assuming the models and services are in the correct path.
from smart_core_assistant_painel.app.ui.atendimentos.services.message_analyzer import (
    MessageAnalyzer,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Mensagem,
    Atendimento,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato


pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_message():
    """Fixture for a mock Mensagem with its related objects."""
    contato = MagicMock(spec=Contato)
    contato.id = 1
    contato.nome_contato = ""
    contato.metadados = {}
    contato.save = MagicMock()

    atendimento = MagicMock(spec=Atendimento)
    atendimento.id = 1
    atendimento.contato = contato
    atendimento.carregar_historico_mensagens.return_value = {
        "conteudo_mensagens": ["histórico"]
    }

    mensagem = MagicMock(spec=Mensagem)
    mensagem.id = 1
    mensagem.atendimento = atendimento
    mensagem.conteudo = "Gostaria de saber o preço do produto X"
    mensagem.save = MagicMock()

    return mensagem


@patch(
    "smart_core_assistant_painel.app.ui.atendimentos.models.Mensagem.objects.get"
)
@patch(
    "smart_core_assistant_painel.app.ui.atendimentos.models.Atendimento.objects.filter"
)
@patch(
    "smart_core_assistant_painel.app.ui.treinamento.models.QueryCompose.build_intent_types_config"
)
@patch(
    "smart_core_assistant_painel.app.ui.atendimentos.services.message_analyzer.FeaturesCompose"
)
class TestMessageAnalyzer:
    def test_analyze_message_content_happy_path(
        self,
        mock_features_compose,
        mock_query_compose,
        mock_atendimento_filter,
        mock_mensagem_get,
        mock_message,
    ):
        """Tests the happy path for message analysis."""
        mock_mensagem_get.return_value = mock_message
        mock_atendimento_filter.return_value.exists.return_value = (
            True  # Not the first atendimento
        )
        mock_query_compose.return_value = {"valid_intents": {}}

        mock_analysis_result = MagicMock()
        mock_analysis_result.intent_types = [{"compra": "produto X"}]
        mock_analysis_result.entity_types = [
            {"produto": "X", "nome_contato": "John Doe"}
        ]
        mock_features_compose.analise_previa_mensagem.return_value = (
            mock_analysis_result
        )

        analyzer = MessageAnalyzer()
        # Mock the process_contact_entities to isolate the test to analyze_message_content
        analyzer.process_contact_entities = MagicMock()

        result = analyzer.analyze_message_content(message_id=1)

        mock_mensagem_get.assert_called_once_with(id=1)
        mock_message.atendimento.carregar_historico_mensagens.assert_called_once_with(
            excluir_mensagem_id=1
        )
        mock_features_compose.analise_previa_mensagem.assert_called_once()
        mock_message.save.assert_called_once_with(
            update_fields=["intent_detectado", "entidades_extraidas"]
        )

        assert (
            mock_message.intent_detectado == mock_analysis_result.intent_types
        )
        assert (
            mock_message.entidades_extraidas
            == mock_analysis_result.entity_types
        )

        analyzer.process_contact_entities.assert_called_once_with(
            mock_message, mock_analysis_result.entity_types
        )

        assert result["intent_types"] == mock_analysis_result.intent_types
        assert result["entity_types"] == mock_analysis_result.entity_types

    def test_analyze_message_content_first_message(
        self,
        mock_features_compose,
        mock_query_compose,
        mock_atendimento_filter,
        mock_mensagem_get,
        mock_message,
    ):
        """Tests the flow for the very first message from a contact."""
        mock_mensagem_get.return_value = mock_message
        mock_atendimento_filter.return_value.exclude.return_value.exists.return_value = False  # First atendimento
        mock_message.atendimento.carregar_historico_mensagens.return_value = {
            "conteudo_mensagens": []
        }  # No history

        analyzer = MessageAnalyzer()
        analyzer.process_contact_entities = MagicMock()

        analyzer.analyze_message_content(message_id=1)

        mock_features_compose.mensagem_apresentacao.assert_called_once()

    def test_process_contact_entities_updates(
        self,
        mock_features_compose,
        mock_query_compose,
        mock_atendimento_filter,
        mock_mensagem_get,
        mock_message,
    ):
        """Tests updates of contact info based on entities."""
        analyzer = MessageAnalyzer()
        analyzer._get_valid_metadata_entities = MagicMock(
            return_value={"cidade", "empresa"}
        )

        entities = [
            {"nome_contato": "  Jane Doe  "},
            {"cidade": "São Paulo"},
            {"produto": "Produto Y"},  # Should be ignored
        ]

        analyzer.process_contact_entities(mock_message, entities)

        contact = mock_message.atendimento.contato
        assert contact.nome_contato == "Jane Doe"
        assert contact.metadados["cidade"] == "São Paulo"
        assert "produto" not in contact.metadados
        contact.save.assert_called()

    def test_process_contact_entities_solicita_info(
        self,
        mock_features_compose,
        mock_query_compose,
        mock_atendimento_filter,
        mock_mensagem_get,
        mock_message,
    ):
        """Tests that info is requested if contact name is missing after processing."""
        analyzer = MessageAnalyzer()
        analyzer._get_valid_metadata_entities = MagicMock(
            return_value={"cidade"}
        )

        # Ensure contact name is empty
        mock_message.atendimento.contato.nome_contato = ""

        analyzer.process_contact_entities(
            mock_message, [{"cidade": "São Paulo"}]
        )

        mock_features_compose.solicitacao_info_cliene.assert_called_once()

    @patch(
        "smart_core_assistant_painel.app.ui.atendimentos.services.message_analyzer.SERVICEHUB"
    )
    def test_get_valid_metadata_entities(
        self,
        mock_servicehub,
        mock_features_compose,
        mock_query_compose,
        mock_atendimento_filter,
        mock_mensagem_get,
    ):
        """Tests the extraction of valid entity types for metadata."""
        mock_servicehub.VALID_ENTITY_TYPES = '{"entity_types": {"dados_pessoais": {"nome_contato": {}, "cpf": {}}, "localizacao": {"cidade": {}, "estado": {}}}}'

        analyzer = MessageAnalyzer()
        valid_entities = analyzer._get_valid_metadata_entities()

        assert valid_entities == {"cpf", "cidade", "estado"}
        assert "nome_contato" not in valid_entities

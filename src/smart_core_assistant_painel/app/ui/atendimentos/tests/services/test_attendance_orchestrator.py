from unittest.mock import MagicMock, patch

import pytest

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
)

# Assuming the models and services are in the correct path.
from smart_core_assistant_painel.app.ui.atendimentos.services.attendance_orchestrator import (
    AttendanceOrchestrator,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_services():
    """Fixture for mock service dependencies."""
    return {
        "message_analyzer": MagicMock(),
        "structure_manager": MagicMock(),
        "rules_engine": MagicMock(),
    }


@pytest.fixture
def orchestrator_instance(mock_services):
    """Fixture for an AttendanceOrchestrator instance with mocked dependencies."""
    return AttendanceOrchestrator(**mock_services)


@patch(
    "smart_core_assistant_painel.app.ui.atendimentos.services.attendance_orchestrator.clear_buffer_contact"
)
@patch(
    "smart_core_assistant_painel.app.ui.atendimentos.services.attendance_orchestrator.cache"
)
class TestAttendanceOrchestrator:
    def test_process_contact_response_no_messages(
        self, mock_cache, mock_clear_buffer, orchestrator_instance
    ):
        """Tests that processing is skipped if there are no messages in the buffer."""
        mock_cache.get.return_value = []

        orchestrator_instance.process_contact_response(contact_id=1)

        mock_cache.get.assert_called_once_with("evo_buffer_1", [])
        # _create_message is an internal method, we check that it is not called implicitly
        # by checking a follow up method call
        orchestrator_instance._message_analyzer.analyze_message_content.assert_not_called()
        mock_clear_buffer.assert_called_once_with(
            1
        )  # finally block should still run

    @patch.object(AttendanceOrchestrator, "_get_buffered_messages")
    @patch.object(AttendanceOrchestrator, "_compile_message_content")
    @patch.object(AttendanceOrchestrator, "_create_message")
    @patch.object(AttendanceOrchestrator, "_process_message_and_respond")
    def test_process_contact_response_happy_path(
        self,
        mock_process_and_respond,
        mock_create_message,
        mock_compile_content,
        mock_get_buffered,
        mock_cache,
        mock_clear_buffer,
        orchestrator_instance,
    ):
        """Tests the full successful flow of processing a contact response."""
        contact_id = 1
        message_id = 123
        api_key = "test_api_key"
        mock_buffered_messages = [{"message": {"text": "hello"}}]
        mock_compiled_data = {
            "content": "hello",
            "message_type": "text",
            "message_id": "wamid1",
            "metadados": {},
            "profile_name": "Test User",
            "api_key": api_key,
        }

        mock_get_buffered.return_value = mock_buffered_messages
        mock_compile_content.return_value = mock_compiled_data
        mock_create_message.return_value = message_id

        orchestrator_instance.process_contact_response(
            contact_id=contact_id, api_key=api_key
        )

        mock_get_buffered.assert_called_once_with(contact_id)
        mock_compile_content.assert_called_once_with(mock_buffered_messages)
        mock_create_message.assert_called_once_with(
            contact_id=contact_id,
            content=mock_compiled_data["content"],
            message_type=mock_compiled_data["message_type"],
            message_id_whatsapp=mock_compiled_data["message_id"],
            metadados=mock_compiled_data["metadados"],
            profile_name=mock_compiled_data["profile_name"],
            api_key=api_key,
        )
        mock_process_and_respond.assert_called_once_with(
            message_id=message_id,
            contact_id=contact_id,
            api_key=api_key,
            env_list=mock_buffered_messages,
        )
        mock_clear_buffer.assert_called_once_with(contact_id)

    def test_compile_message_content(
        self, mock_cache, mock_clear_buffer, orchestrator_instance
    ):
        """Tests the compilation of message content from multiple envelopes."""
        env_list = [
            {
                "message": {"text": "Hello", "metadata": {"source": "ios"}},
                "profile": {},
                "apikey": "key1",
            },
            {
                "message": {
                    "text": "World",
                    "type": "imageMessage",
                    "id": "wamid2",
                    "metadata": {"size": 1024},
                },
                "profile": {"push_name": "Final Name"},
                "apikey": "key2",
            },
        ]

        result = orchestrator_instance._compile_message_content(env_list)

        assert result["content"] == "Hello\nWorld"
        assert result["message_type"] == "imageMessage"
        assert result["message_id"] == "wamid2"
        assert result["profile_name"] == "Final Name"
        assert result["metadados"] == {"source": "ios", "size": 1024}
        assert result["api_key"] == "key2"

    @patch(
        "smart_core_assistant_painel.app.ui.atendimentos.models.processar_mensagem_por_contato"
    )
    def test_create_message(
        self,
        mock_processar_msg,
        mock_cache,
        mock_clear_buffer,
        orchestrator_instance,
    ):
        """Tests the message creation step."""
        mock_processar_msg.return_value = 42

        msg_id = orchestrator_instance._create_message(
            contact_id=1,
            content="Test",
            message_type="text",
            message_id_whatsapp="wamid1",
            metadados={},
            profile_name="Test",
            api_key="key1",
        )

        assert msg_id == 42
        mock_processar_msg.assert_called_once()

        # Test empty content
        empty_msg_id = orchestrator_instance._create_message(
            contact_id=1,
            content="",
            message_type="text",
            message_id_whatsapp="wamid2",
            metadados={},
            profile_name="Test",
            api_key="key1",
        )
        assert empty_msg_id is None

    @patch(
        "smart_core_assistant_painel.app.ui.atendimentos.models.Mensagem.objects.get"
    )
    def test_process_message_and_respond_bot_can_respond(
        self,
        mock_msg_get,
        mock_cache,
        mock_clear_buffer,
        orchestrator_instance,
        mock_services,
    ):
        """Tests the flow where the bot is allowed to respond."""
        mock_message = MagicMock(spec=Mensagem)
        mock_message.atendimento = MagicMock(spec=Atendimento)
        mock_msg_get.return_value = mock_message
        mock_services["rules_engine"].can_bot_respond.return_value = True
        orchestrator_instance._generate_and_register_response = MagicMock()

        orchestrator_instance._process_message_and_respond(
            message_id=1, contact_id=1, api_key="key", env_list=[]
        )

        mock_services[
            "message_analyzer"
        ].analyze_message_content.assert_called_once_with(1)
        mock_message.refresh_from_db.assert_called_once()
        orchestrator_instance._generate_and_register_response.assert_called_once()

    @patch(
        "smart_core_assistant_painel.app.ui.atendimentos.models.Mensagem.objects.get"
    )
    def test_process_message_and_respond_bot_cannot_respond(
        self,
        mock_msg_get,
        mock_cache,
        mock_clear_buffer,
        orchestrator_instance,
        mock_services,
    ):
        """Tests the flow where the bot is not allowed to respond."""
        mock_message = MagicMock(spec=Mensagem)
        mock_message.atendimento = MagicMock(spec=Atendimento)
        mock_msg_get.return_value = mock_message
        mock_services["rules_engine"].can_bot_respond.return_value = False
        orchestrator_instance._generate_and_register_response = MagicMock()

        orchestrator_instance._process_message_and_respond(
            message_id=1, contact_id=1, api_key="key", env_list=[]
        )

        mock_services["rules_engine"].can_bot_respond.assert_called_once_with(
            mock_message.atendimento
        )
        orchestrator_instance._generate_and_register_response.assert_not_called()

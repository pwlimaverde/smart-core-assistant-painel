"""Additional tests for the Atendimentos app utils."""

from unittest.mock import patch, MagicMock
import json
import os

from django.test import TestCase
from django.core.cache import cache
from django.utils import timezone

from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.treinamento.models import Documento
from smart_core_assistant_painel.modules.ai_engine import MessageData, FeaturesCompose
from smart_core_assistant_painel.modules.services import SERVICEHUB

from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento, Mensagem, TipoRemetente, processar_mensagem_whatsapp
from smart_core_assistant_painel.app.ui.atendimentos.signals import mensagem_bufferizada
from smart_core_assistant_painel.app.ui.atendimentos.utils import (
    set_wa_buffer, clear_wa_buffer, send_message_response, sched_message_response,
    _obter_entidades_metadados_validas, _processar_entidades_contato,
    _analisar_conteudo_mensagem, _pode_bot_responder_atendimento,
    _compile_message_data_list
)


class TestAtendimentosUtilsBuffer(TestCase):
    """Tests for the buffer-related utility functions."""

    def setUp(self) -> None:
        """Set up test environment."""
        cache.clear()
        self.phone = "5511999999999"
        self.message_data = MessageData(
            instance="test_instance",
            api_key="test_api_key",
            numero_telefone=self.phone,
            from_me=False,
            conteudo="Test message",
            message_type="text",
            message_id="test_message_id",
            metadados={},
            nome_perfil_whatsapp="Test User"
        )

    def test_set_wa_buffer_success(self) -> None:
        """Test successful addition of message to WhatsApp buffer."""
        # Act
        set_wa_buffer(self.message_data)

        # Assert
        cache_key = f"wa_buffer_{self.phone}"
        buffer = cache.get(cache_key)
        self.assertIsNotNone(buffer)
        self.assertEqual(len(buffer), 1)
        self.assertEqual(buffer[0], self.message_data)

    def test_clear_wa_buffer_success(self) -> None:
        """Test successful clearing of WhatsApp buffer."""
        # Arrange
        cache_key = f"wa_buffer_{self.phone}"
        timer_key = f"wa_timer_{self.phone}"
        cache.set(cache_key, [self.message_data])
        cache.set(timer_key, True)

        # Act
        clear_wa_buffer(self.phone)

        # Assert
        self.assertIsNone(cache.get(cache_key))
        self.assertIsNone(cache.get(timer_key))

    def test_clear_wa_buffer_nonexistent_keys(self) -> None:
        """Test clearing buffer when keys don't exist."""
        # Act
        clear_wa_buffer("nonexistent_phone")

        # Assert - should not raise any exceptions
        # Just verify no errors occurred


class TestAtendimentosUtilsCompilation(TestCase):
    """Tests for the message compilation utility functions."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.messages = [
            MessageData(
                instance="test_instance",
                api_key="test_api_key",
                numero_telefone="5511999999999",
                from_me=False,
                conteudo="First message",
                message_type="text",
                message_id="msg1",
                metadados={"key1": "value1"},
                nome_perfil_whatsapp="Test User"
            ),
            MessageData(
                instance="test_instance",
                api_key="test_api_key",
                numero_telefone="5511999999999",
                from_me=False,
                conteudo="Second message",
                message_type="text",
                message_id="msg2",
                metadados={"key2": "value2"},
                nome_perfil_whatsapp="Test User"
            )
        ]

    def test_compile_message_data_list_success(self) -> None:
        """Test successful compilation of message data list."""
        # Act
        result = _compile_message_data_list(self.messages)

        # Assert
        self.assertEqual(result.instance, "test_instance")
        self.assertEqual(result.api_key, "test_api_key")
        self.assertEqual(result.numero_telefone, "5511999999999")
        self.assertEqual(result.from_me, False)
        self.assertEqual(result.conteudo, "First message\nSecond message")
        self.assertEqual(result.message_type, "text")
        self.assertEqual(result.message_id, "msg2")  # Should be from last message
        self.assertEqual(result.metadados, {"key1": "value1", "key2": "value2"})
        self.assertEqual(result.nome_perfil_whatsapp, "Test User")

    def test_compile_message_data_list_empty_list_raises_error(self) -> None:
        """Test that empty list raises ValueError."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            _compile_message_data_list([])
        
        self.assertEqual(str(context.exception), "lista de mensagens não pode estar vazia")

    def test_compile_message_data_list_single_message(self) -> None:
        """Test compilation with single message."""
        # Act
        result = _compile_message_data_list([self.messages[0]])

        # Assert
        self.assertEqual(result.conteudo, "First message")
        self.assertEqual(result.metadados, {"key1": "value1"})


class TestAtendimentosUtilsScheduling(TestCase):
    """Tests for the scheduling utility functions."""

    def setUp(self) -> None:
        """Set up test environment."""
        cache.clear()
        self.phone = "5511999999999"

    def test_sched_message_response_sets_timer(self) -> None:
        """Test that sched_message_response sets timer in cache."""
        # Act
        sched_message_response(self.phone)

        # Assert
        timer_key = f"wa_timer_{self.phone}"
        timer_value = cache.get(timer_key)
        self.assertTrue(timer_value)

    @patch('smart_core_assistant_painel.app.ui.atendimentos.signals.mensagem_bufferizada.send')
    def test_sched_message_response_sends_signal_when_no_timer(
        self,
        mock_signal_send: MagicMock
    ) -> None:
        """Test that sched_message_response sends signal when no timer exists."""
        # Act
        sched_message_response(self.phone)

        # Assert
        mock_signal_send.assert_called_once_with(sender="atendimentos", phone=self.phone)

    @patch('smart_core_assistant_painel.app.ui.atendimentos.signals.mensagem_bufferizada.send')
    def test_sched_message_response_no_signal_when_timer_exists(
        self,
        mock_signal_send: MagicMock
    ) -> None:
        """Test that sched_message_response doesn't send signal when timer exists."""
        # Arrange
        timer_key = f"wa_timer_{self.phone}"
        cache.set(timer_key, True)

        # Act
        sched_message_response(self.phone)

        # Assert
        mock_signal_send.assert_not_called()


class TestAtendimentosUtilsEntidades(TestCase):
    """Tests for the entity processing utility functions."""

    @patch.dict(os.environ, {'VALID_ENTITY_TYPES': '{"entity_types": {"pessoa": {"cpf": "", "nome": ""}, "contato": {"telefone": ""}}}'})
    def test_obter_entidades_metadados_validas_success(self) -> None:
        """Test successful retrieval of valid metadata entities."""
        # Reset the cached value in SERVICEHUB
        SERVICEHUB._valid_entity_types = None
        
        # Act
        result = _obter_entidades_metadados_validas()

        # Assert
        # Should include cpf and nome, but exclude contato, telefone, and nome_contato
        self.assertIn("cpf", result)
        self.assertIn("nome", result)
        self.assertNotIn("contato", result)
        self.assertNotIn("telefone", result)
        self.assertNotIn("nome_contato", result)

    @patch.dict(os.environ, {'VALID_ENTITY_TYPES': ''})
    def test_obter_entidades_metadados_validas_empty_config(self) -> None:
        """Test entity retrieval with empty configuration."""
        # Reset the cached value in SERVICEHUB
        SERVICEHUB._valid_entity_types = None
        
        # Act
        result = _obter_entidades_metadados_validas()

        # Assert
        self.assertEqual(result, set())

    @patch.dict(os.environ, {'VALID_ENTITY_TYPES': 'invalid_json'})
    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils.logger')
    def test_obter_entidades_metadados_validas_invalid_json(
        self,
        mock_logger: MagicMock
    ) -> None:
        """Test entity retrieval with invalid JSON."""
        # Reset the cached value in SERVICEHUB
        SERVICEHUB._valid_entity_types = None
        
        # Act
        result = _obter_entidades_metadados_validas()

        # Assert
        self.assertEqual(result, set())
        mock_logger.error.assert_called_once()

    def test_processar_entidades_contato_updates_nome_contato(self) -> None:
        """Test that contact entities update contact name."""
        # Arrange
        contato = MagicMock()
        contato.nome_contato = "Old"
        contato.metadados = {}
        
        mensagem = MagicMock()
        mensagem.atendimento.contato = contato
        
        entity_types = [{"nome_contato": "New Full Name"}]

        # Act
        _processar_entidades_contato(mensagem, entity_types)

        # Assert
        self.assertEqual(contato.nome_contato, "New Full Name")
        contato.save.assert_called_once()

    def test_processar_entidades_contato_updates_metadata(self) -> None:
        """Test that contact entities update metadata."""
        # Arrange
        contato = MagicMock()
        contato.nome_contato = "Test Name"
        contato.metadados = {}
        
        mensagem = MagicMock()
        mensagem.atendimento.contato = contato
        
        entity_types = [{"cpf": "12345678900"}]

        # Act
        _processar_entidades_contato(mensagem, entity_types)

        # Assert
        self.assertEqual(contato.metadados["cpf"], "12345678900")
        contato.save.assert_called_once()

    def test_processar_entidades_contato_no_updates_needed(self) -> None:
        """Test that no updates occur when data is already current."""
        # Arrange
        contato = MagicMock()
        contato.nome_contato = "Current Name"
        contato.metadados = {"cpf": "12345678900"}
        
        mensagem = MagicMock()
        mensagem.atendimento.contato = contato
        
        entity_types = [{"nome_contato": "Current Name"}, {"cpf": "12345678900"}]

        # Act
        _processar_entidades_contato(mensagem, entity_types)

        # Assert
        contato.save.assert_not_called()

    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils.logger')
    def test_processar_entidades_contato_exception_handling(
        self,
        mock_logger: MagicMock
    ) -> None:
        """Test exception handling in _processar_entidades_contato."""
        # Arrange
        mensagem = MagicMock()
        mensagem.atendimento.contato = MagicMock()
        mensagem.atendimento.contato.save.side_effect = Exception("Test exception")
        
        entity_types = [{"nome_contato": "Test Name"}]

        # Act
        _processar_entidades_contato(mensagem, entity_types)

        # Assert
        mock_logger.error.assert_called_once()
        self.assertIn("Erro ao processar entidades do contato", mock_logger.error.call_args[0][0])


class TestAtendimentosUtilsBotResponse(TestCase):
    """Tests for the bot response utility functions."""

    def test_pode_bot_responder_atendimento_none_returns_false(self) -> None:
        """Test that None atendimento returns False."""
        # Act
        result = _pode_bot_responder_atendimento(None)

        # Assert
        self.assertFalse(result)

    def test_pode_bot_responder_atendimento_no_human_interaction(self) -> None:
        """Test that bot can respond when there's no human interaction."""
        # Arrange
        atendimento = MagicMock()
        atendimento.atendente_humano = None
        atendimento.mensagens.filter.return_value.exists.return_value = False

        # Act
        result = _pode_bot_responder_atendimento(atendimento)

        # Assert
        self.assertTrue(result)

    def test_pode_bot_responder_atendimento_with_human_attendant(self) -> None:
        """Test that bot cannot respond when there's a human attendant."""
        # Arrange
        atendimento = MagicMock()
        atendimento.atendente_humano = MagicMock()

        # Act
        result = _pode_bot_responder_atendimento(atendimento)

        # Assert
        self.assertFalse(result)

    def test_pode_bot_responder_atendimento_with_human_messages(self) -> None:
        """Test that bot cannot respond when there are human messages."""
        # Arrange
        atendimento = MagicMock()
        atendimento.atendente_humano = None
        atendimento.mensagens.filter.return_value.exists.return_value = True

        # Act
        result = _pode_bot_responder_atendimento(atendimento)

        # Assert
        self.assertFalse(result)

    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils.logger')
    def test_pode_bot_responder_atendimento_exception_handling(
        self,
        mock_logger: MagicMock
    ) -> None:
        """Test exception handling in _pode_bot_responder_atendimento."""
        # Arrange
        atendimento = MagicMock()
        # Force an exception by making the filter method raise an error
        atendimento.mensagens.filter.side_effect = Exception("Test exception")

        # Act
        result = _pode_bot_responder_atendimento(atendimento)

        # Assert
        self.assertFalse(result)
        mock_logger.error.assert_called_once()
        self.assertIn("Erro ao verificar se o bot pode responder", mock_logger.error.call_args[0][0])


class TestAtendimentosUtilsSendMessage(TestCase):
    """Tests for the send_message_response function."""

    def setUp(self) -> None:
        """Set up test environment."""
        cache.clear()
        self.phone = "5511999999999"
        self.message_data = MessageData(
            instance="test_instance",
            api_key="test_api_key",
            numero_telefone=self.phone,
            from_me=False,
            conteudo="Test message",
            message_type="text",
            message_id="test_message_id",
            metadados={},
            nome_perfil_whatsapp="Test User"
        )

    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils.logger')
    def test_send_message_response_empty_buffer(self, mock_logger: MagicMock) -> None:
        """Test send_message_response with empty buffer."""
        # Act
        send_message_response(self.phone)

        # Assert
        mock_logger.warning.assert_called_once_with(f"Buffer vazio para {self.phone}")

    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils._compile_message_data_list')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils.processar_mensagem_whatsapp')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.models.Mensagem.objects.get')
    @patch('smart_core_assistant_painel.modules.ai_engine.FeaturesCompose.generate_embeddings')
    @patch('smart_core_assistant_painel.app.ui.treinamento.models.Documento.buscar_documentos_similares')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils._analisar_conteudo_mensagem')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils._pode_bot_responder_atendimento')
    @patch('smart_core_assistant_painel.modules.services.SERVICEHUB.whatsapp_service.send_message')
    def test_send_message_response_success(
        self,
        mock_send_message: MagicMock,
        mock_pode_responder: MagicMock,
        mock_analisar_conteudo: MagicMock,
        mock_buscar_documentos: MagicMock,
        mock_generate_embeddings: MagicMock,
        mock_get_mensagem: MagicMock,
        mock_processar_mensagem: MagicMock,
        mock_compile_message_data: MagicMock
    ) -> None:
        """Test successful message sending."""
        # Arrange
        cache_key = f"wa_buffer_{self.phone}"
        cache.set(cache_key, [self.message_data])
        
        mock_compile_message_data.return_value = self.message_data
        mock_processar_mensagem.return_value = 1  # mensagem_id
        
        mensagem_mock = MagicMock()
        mensagem_mock.intent_detectado = [{"unknown_tag": "detected value"}]
        mock_get_mensagem.return_value = mensagem_mock
        
        mock_pode_responder.return_value = True
        
        # Mock WhatsApp service methods to avoid exceptions
        mock_send_message.return_value = None
        
        # Act
        send_message_response(self.phone)

        # Assert
        mock_compile_message_data.assert_called_once()
        mock_processar_mensagem.assert_called_once()
        mock_analisar_conteudo.assert_called_once_with(1)
        mock_generate_embeddings.assert_called_once()
        mock_send_message.assert_called_once()

    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils._compile_message_data_list')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.models.processar_mensagem_whatsapp')
    @patch('smart_core_assistant_painel.app.ui.atendimentos.utils.logger')
    def test_send_message_response_exception_handling(
        self,
        mock_logger: MagicMock,
        mock_processar_mensagem: MagicMock,
        mock_compile_message_data: MagicMock
    ) -> None:
        """Test exception handling in send_message_response."""
        # Arrange
        cache_key = f"wa_buffer_{self.phone}"
        cache.set(cache_key, [self.message_data])
        
        mock_compile_message_data.side_effect = Exception("Test exception")

        # Act
        send_message_response(self.phone)

        # Assert
        mock_logger.error.assert_called_once()
        self.assertIn("Erro ao processar mensagens para", mock_logger.error.call_args[0][0])
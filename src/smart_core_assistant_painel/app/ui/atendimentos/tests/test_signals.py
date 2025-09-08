"""Tests for the Atendimentos app signals."""

from unittest.mock import patch, MagicMock
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django_q.models import Schedule

from smart_core_assistant_painel.modules.services import SERVICEHUB
from smart_core_assistant_painel.app.ui.atendimentos.signals import mensagem_bufferizada, signal_agendar_processamento_mensagens


class TestAtendimentosSignals(TestCase):
    """Tests for the Atendimentos app signals."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.phone = "5511999999999"

    def test_signal_agendar_processamento_mensagens_integration(self) -> None:
        """Test integration of message processing scheduling."""
        # Act
        signal_agendar_processamento_mensagens(sender="test", phone=self.phone)

        # Assert
        # Check if schedule was created
        schedule_name = f"process_msg_{self.phone}"
        schedules = Schedule.objects.filter(name=schedule_name)
        self.assertEqual(schedules.count(), 1)
        
        schedule = schedules.first()
        self.assertEqual(schedule.func, "smart_core_assistant_painel.app.ui.atendimentos.utils.send_message_response")
        self.assertEqual(schedule.args, self.phone)
        self.assertEqual(schedule.schedule_type, Schedule.ONCE)
        
        # Check that next_run is in the future
        self.assertGreater(schedule.next_run, timezone.now())

    @patch('smart_core_assistant_painel.app.ui.atendimentos.signals.logger')
    def test_signal_agendar_processamento_mensagens_exception_handling(
        self,
        mock_logger: MagicMock
    ) -> None:
        """Test exception handling in signal_agendar_processamento_mensagens."""
        # Arrange
        # Force an exception by making Schedule.objects.create raise an error
        with patch('smart_core_assistant_painel.app.ui.atendimentos.signals.Schedule.objects') as mock_schedule_objects:
            mock_schedule_objects.create.side_effect = Exception("Test exception")

            # Act
            signal_agendar_processamento_mensagens(sender="test", phone=self.phone)

            # Assert
            mock_logger.error.assert_called_once()
            self.assertIn("Erro ao agendar processamento", mock_logger.error.call_args[0][0])

    def test_mensagem_bufferizada_signal_connection(self) -> None:
        """Test that mensagem_bufferizada signal is properly connected."""
        # Check if the signal has the receiver connected
        receivers = mensagem_bufferizada.receivers
        self.assertTrue(len(receivers) > 0)
        
        # Just check that there are receivers connected - detailed inspection can be complex
        # with weak references and internal Django structures
        pass
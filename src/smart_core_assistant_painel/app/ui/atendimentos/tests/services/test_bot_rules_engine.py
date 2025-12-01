
from unittest.mock import MagicMock, patch

import pytest

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    TipoRemetente,
)

from smart_core_assistant_painel.app.ui.atendimentos.services.bot_rules_engine import (
    BotRulesEngine,
)
from smart_core_assistant_painel.app.ui.operacional.models import (
    Atendente,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_atendimento():
    """Fixture for a mock Atendimento."""
    atendimento = MagicMock(spec=Atendimento)
    atendimento.id = 1
    atendimento.atendente_humano = None
    atendimento.departamento = None
    atendimento.bot_pode_atender = True  # Default for "can respond"

    # Mock the related manager for messages
    mensagens_manager = MagicMock()
    mensagens_manager.filter.return_value.exists.return_value = False
    atendimento.mensagens = mensagens_manager

    return atendimento


class TestBotRulesEngine:
    def test_can_bot_respond_true(self, mock_atendimento):
        """Tests that bot can respond when conditions are met."""
        engine = BotRulesEngine()

        with patch.object(
            engine, "_has_human_interaction", return_value=False
        ) as mock_has_human:
            assert engine.can_bot_respond(mock_atendimento) is True
            mock_has_human.assert_called_once_with(mock_atendimento)

    def test_can_bot_respond_false_if_human_interaction(
        self, mock_atendimento
    ):
        """Tests that bot cannot respond if there is human interaction."""
        engine = BotRulesEngine()

        with patch.object(
            engine, "_has_human_interaction", return_value=True
        ) as mock_has_human:
            assert engine.can_bot_respond(mock_atendimento) is False
            mock_has_human.assert_called_once_with(mock_atendimento)

    def test_can_bot_respond_false_if_flag_false(self, mock_atendimento):
        """Tests that bot cannot respond if bot_pode_atender is False."""
        mock_atendimento.bot_pode_atender = False
        engine = BotRulesEngine()

        with patch.object(
            engine, "_has_human_interaction", return_value=False
        ):
            assert engine.can_bot_respond(mock_atendimento) is False

    def test_can_bot_respond_false_for_none_attendance(self):
        """Tests that bot cannot respond if attendance is None."""
        engine = BotRulesEngine()
        assert engine.can_bot_respond(None) is False

    def test_has_human_interaction_false(self, mock_atendimento):
        """Tests for no human interaction."""
        # Only check messages
        mock_atendimento.mensagens.filter.return_value.exists.return_value = (
            False
        )
        engine = BotRulesEngine()
        assert engine._has_human_interaction(mock_atendimento) is False
        mock_atendimento.mensagens.filter.assert_called_once_with(
            remetente=TipoRemetente.ATENDENTE_HUMANO
        )

    def test_has_human_interaction_true_with_message(self, mock_atendimento):
        """Tests for human interaction when there is a message from an agent."""
        mock_atendimento.mensagens.filter.return_value.exists.return_value = (
            True
        )
        engine = BotRulesEngine()
        assert engine._has_human_interaction(mock_atendimento) is True

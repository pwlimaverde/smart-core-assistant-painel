from unittest.mock import MagicMock, patch

import pytest

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    TipoRemetente,
)

# Assuming the models and services are in the correct path.
from smart_core_assistant_painel.app.ui.atendimentos.services.bot_rules_engine import (
    BotRulesEngine,
)
from smart_core_assistant_painel.app.ui.operacional.models import (
    Atendente,
    Departamento,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_atendimento():
    """Fixture for a mock Atendimento."""
    atendimento = MagicMock(spec=Atendimento)
    atendimento.atendente_humano = None
    atendimento.departamento = None

    # Mock the related manager for messages
    mensagens_manager = MagicMock()
    mensagens_manager.filter.return_value.exists.return_value = False
    atendimento.mensagens = mensagens_manager

    return atendimento


class TestBotRulesEngine:
    def test_can_bot_respond_true(self, mock_atendimento):
        """Tests that bot can respond when conditions are met."""
        engine = BotRulesEngine()

        # Mock internal checks to isolate the can_bot_respond logic
        with (
            patch.object(
                engine, "_is_in_bot_department", return_value=True
            ) as mock_is_in_dept,
            patch.object(
                engine, "_has_human_interaction", return_value=False
            ) as mock_has_human,
        ):
            assert engine.can_bot_respond(mock_atendimento) is True
            mock_is_in_dept.assert_called_once_with(mock_atendimento)
            mock_has_human.assert_called_once_with(mock_atendimento)

    def test_can_bot_respond_false_if_wrong_department(self, mock_atendimento):
        """Tests that bot cannot respond if in the wrong department."""
        engine = BotRulesEngine()

        with patch.object(
            engine, "_is_in_bot_department", return_value=False
        ) as mock_is_in_dept:
            assert engine.can_bot_respond(mock_atendimento) is False
            mock_is_in_dept.assert_called_once_with(mock_atendimento)

    def test_can_bot_respond_false_if_human_interaction(
        self, mock_atendimento
    ):
        """Tests that bot cannot respond if there is human interaction."""
        engine = BotRulesEngine()

        with (
            patch.object(engine, "_is_in_bot_department", return_value=True),
            patch.object(
                engine, "_has_human_interaction", return_value=True
            ) as mock_has_human,
        ):
            assert engine.can_bot_respond(mock_atendimento) is False
            mock_has_human.assert_called_once_with(mock_atendimento)

    def test_can_bot_respond_human_interaction_priority(
        self, mock_atendimento
    ):
        """Tests that human interaction blocks bot even if bot_pode_atender is True."""
        mock_atendimento.bot_pode_atender = True
        engine = BotRulesEngine()

        with patch.object(
            engine, "_has_human_interaction", return_value=True
        ) as mock_has_human:
            assert engine.can_bot_respond(mock_atendimento) is False
            mock_has_human.assert_called_once_with(mock_atendimento)

    def test_can_bot_respond_true_override(self, mock_atendimento):
        """Tests that bot_pode_atender=True allows response even if department is wrong."""
        mock_atendimento.bot_pode_atender = True
        engine = BotRulesEngine()

        with (
            patch.object(engine, "_has_human_interaction", return_value=False),
            patch.object(engine, "_is_in_bot_department", return_value=False),
        ):
            assert engine.can_bot_respond(mock_atendimento) is True

    def test_can_bot_respond_false_for_none_attendance(self):
        """Tests that bot cannot respond if attendance is None."""
        engine = BotRulesEngine()
        assert engine.can_bot_respond(None) is False

    @patch(
        "smart_core_assistant_painel.app.ui.atendimentos.services.attendance_structure_manager.AttendanceStructureManager"
    )
    def test_is_in_bot_department_no_department(
        self, mock_structure_manager, mock_atendimento
    ):
        """Tests that default structure is configured if no department is set."""
        mock_atendimento.departamento = None
        engine = BotRulesEngine()

        assert engine._is_in_bot_department(mock_atendimento) is True

        # Verify that the structure manager was called to configure the default
        mock_structure_manager_instance = mock_structure_manager.return_value
        mock_structure_manager_instance.configure_default_attendance.assert_called_once_with(
            mock_atendimento
        )

    def test_is_in_bot_department_correct_department(self, mock_atendimento):
        """Tests the check for the correct bot department."""
        mock_atendimento.departamento = MagicMock(
            spec=Departamento, nome="Atendimento"
        )
        engine = BotRulesEngine()
        assert engine._is_in_bot_department(mock_atendimento) is True

    def test_is_in_bot_department_wrong_department(self, mock_atendimento):
        """Tests the check for an incorrect department."""
        mock_atendimento.departamento = MagicMock(
            spec=Departamento, nome="Vendas"
        )
        engine = BotRulesEngine()
        assert engine._is_in_bot_department(mock_atendimento) is False

    def test_has_human_interaction_false(self, mock_atendimento):
        """Tests for no human interaction."""
        mock_atendimento.atendente_humano = None
        mock_atendimento.mensagens.filter.return_value.exists.return_value = (
            False
        )
        engine = BotRulesEngine()
        assert engine._has_human_interaction(mock_atendimento) is False
        mock_atendimento.mensagens.filter.assert_called_once_with(
            remetente=TipoRemetente.ATENDENTE_HUMANO
        )

    def test_has_human_interaction_true_with_agent(self, mock_atendimento):
        """Tests for human interaction when an agent is assigned."""
        mock_atendimento.atendente_humano = MagicMock(spec=Atendente)
        engine = BotRulesEngine()
        assert engine._has_human_interaction(mock_atendimento) is True

    def test_has_human_interaction_true_with_message(self, mock_atendimento):
        """Tests for human interaction when there is a message from an agent."""
        mock_atendimento.atendente_humano = None
        mock_atendimento.mensagens.filter.return_value.exists.return_value = (
            True
        )
        engine = BotRulesEngine()
        assert engine._has_human_interaction(mock_atendimento) is True

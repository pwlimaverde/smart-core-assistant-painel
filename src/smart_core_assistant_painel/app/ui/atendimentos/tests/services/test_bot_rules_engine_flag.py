import pytest
from unittest.mock import MagicMock, patch
from smart_core_assistant_painel.app.ui.atendimentos.services.bot_rules_engine import (
    BotRulesEngine,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.ui.operacional.models import (
    Atendente,
    Departamento,
)

pytestmark = pytest.mark.django_db


class TestBotRulesEngineFlag:
    def test_can_bot_respond_flag_true(self):
        """Test that bot can respond when flag is True and other conditions met."""
        atendimento = MagicMock(spec=Atendimento)
        atendimento.bot_pode_atender = True
        atendimento.id = 1

        engine = BotRulesEngine()

        with (
            patch.object(engine, "_is_in_bot_department", return_value=True),
            patch.object(engine, "_has_human_interaction", return_value=False),
        ):
            assert engine.can_bot_respond(atendimento) is True

    def test_can_bot_respond_flag_false(self):
        """Test that bot CANNOT respond when flag is False."""
        atendimento = MagicMock(spec=Atendimento)
        atendimento.bot_pode_atender = False
        atendimento.id = 1

        engine = BotRulesEngine()

        # Even if other conditions are met
        with (
            patch.object(engine, "_is_in_bot_department", return_value=True),
            patch.object(engine, "_has_human_interaction", return_value=False),
        ):
            assert engine.can_bot_respond(atendimento) is False

    def test_assumir_atendimento_sets_flag_false(self):
        """Test that assumir_atendimento sets bot_pode_atender to False."""
        # Create real objects since we are testing model method
        departamento = Departamento.objects.create(nome="Suporte")
        atendente = Atendente.objects.create(
            nome="João", departamento=departamento
        )

        # Mock Contato since it's required for Atendimento
        from smart_core_assistant_painel.app.ui.clientes.models import Contato

        contato = Contato.objects.create(
            nome_contato="Cliente", telefone="5511999999999"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, departamento=departamento, bot_pode_atender=True
        )

        assert atendimento.bot_pode_atender is True
        assert atendimento.atendente_humano is None

        atendimento.assumir_atendimento(atendente.id)

        atendimento.refresh_from_db()
        assert atendimento.bot_pode_atender is False
        assert atendimento.atendente_humano == atendente
        assert atendimento.status == StatusAtendimento.EM_ATENDIMENTO

    def test_transfer_to_department_sets_flag_false(self):
        """Test that transfer_to_department sets bot_pode_atender to False."""
        departamento_origem = Departamento.objects.create(nome="Origem")
        departamento_destino = Departamento.objects.create(nome="Destino")

        from smart_core_assistant_painel.app.ui.clientes.models import Contato

        contato = Contato.objects.create(
            nome_contato="Cliente 2", telefone="5511888888888"
        )

        atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=departamento_origem,
            bot_pode_atender=True,
        )

        atendimento.transfer_to_department(departamento_destino)

        atendimento.refresh_from_db()
        assert atendimento.bot_pode_atender is False
        assert atendimento.departamento == departamento_destino
        assert atendimento.status == StatusAtendimento.FILA

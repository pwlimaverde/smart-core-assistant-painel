from unittest.mock import ANY, MagicMock, patch

import pytest

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
)

# Assuming the models and services are in the correct path.
from smart_core_assistant_painel.app.atendimentos.services.attendance_structure_manager import (
    AttendanceStructureManager,
)
from smart_core_assistant_painel.app.operacional.models import (
    Departamento,
    EtapaFluxo,
    FluxoAtendimento,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_atendimento_instance():
    """Fixture for a mock Atendimento instance."""
    atendimento = MagicMock(spec=Atendimento)
    atendimento.id = 1
    atendimento.save = MagicMock()
    return atendimento


@patch(
    "smart_core_assistant_painel.app.operacional.models.Departamento.objects.get_or_create"
)
@patch(
    "smart_core_assistant_painel.app.operacional.models.FluxoAtendimento.objects.get_or_create"
)
class TestAttendanceStructureManager:
    def test_ensure_default_structure_creates_new(
        self, mock_fluxo_get_or_create, mock_dept_get_or_create
    ):
        """Tests that the default structure is created if it does not exist."""
        mock_dept = MagicMock(spec=Departamento)
        mock_fluxo = MagicMock(spec=FluxoAtendimento)
        mock_dept_get_or_create.return_value = (mock_dept, True)
        mock_fluxo_get_or_create.return_value = (mock_fluxo, True)

        manager = AttendanceStructureManager()
        departamento, fluxo = manager.ensure_default_structure()

        mock_dept_get_or_create.assert_called_once_with(
            nome="Atendimento", defaults=ANY
        )
        mock_fluxo_get_or_create.assert_called_once_with(
            departamento=mock_dept,
            nome="Atendimento Inicial",
            defaults=ANY,
        )
        assert departamento == mock_dept
        assert fluxo == mock_fluxo

    def test_ensure_default_structure_gets_existing(
        self, mock_fluxo_get_or_create, mock_dept_get_or_create
    ):
        """Tests that existing default structure is retrieved."""
        mock_dept = MagicMock(spec=Departamento)
        mock_fluxo = MagicMock(spec=FluxoAtendimento)
        mock_dept_get_or_create.return_value = (mock_dept, False)
        mock_fluxo_get_or_create.return_value = (mock_fluxo, False)

        manager = AttendanceStructureManager()
        departamento, fluxo = manager.ensure_default_structure()

        assert departamento == mock_dept
        assert fluxo == mock_fluxo

    @patch(
        "smart_core_assistant_painel.app.operacional.models.FluxoAtendimento.objects.filter"
    )
    def test_get_available_flows(
        self, mock_filter, mock_fluxo_get_or_create, mock_dept_get_or_create
    ):
        """Tests the retrieval of available flows."""
        # Mocking the queryset result
        mock_dept_vendas = MagicMock(spec=Departamento, nome="Vendas")
        mock_fluxo_vendas = MagicMock(
            spec=FluxoAtendimento,
            nome="Novos Leads",
            departamento=mock_dept_vendas,
            descricao="Processo de novos leads",
        )

        mock_dept_suporte = MagicMock(spec=Departamento, nome="Suporte")
        mock_fluxo_suporte = MagicMock(
            spec=FluxoAtendimento,
            nome="Tickets N1",
            departamento=mock_dept_suporte,
            descricao="Suporte Nível 1",
        )

        mock_queryset = MagicMock()
        mock_queryset.exclude.return_value.select_related.return_value.order_by.return_value = [
            mock_fluxo_vendas,
            mock_fluxo_suporte,
        ]
        mock_filter.return_value = mock_queryset

        manager = AttendanceStructureManager()
        available_flows = manager.get_available_flows()

        expected_flows = {
            "Novos Leads - Vendas": "Processo de novos leads",
            "Tickets N1 - Suporte": "Suporte Nível 1",
        }
        assert available_flows == expected_flows
        mock_filter.assert_called_once_with(ativo=True)
        mock_queryset.exclude.assert_called_once_with(
            nome="Atendimento Inicial", departamento__nome="Atendimento"
        )

    def test_configure_default_attendance(
        self,
        mock_fluxo_get_or_create,
        mock_dept_get_or_create,
        mock_atendimento_instance,
    ):
        """Tests configuring an attendance with the default structure."""
        mock_dept = MagicMock(spec=Departamento)
        mock_fluxo = MagicMock(spec=FluxoAtendimento)
        mock_etapa = MagicMock(spec=EtapaFluxo, nome="Fila de Atendimento")

        mock_dept_get_or_create.return_value = (mock_dept, True)
        mock_fluxo_get_or_create.return_value = (mock_fluxo, True)
        mock_fluxo.etapas.filter.return_value.first.return_value = mock_etapa

        manager = AttendanceStructureManager()
        manager.configure_default_attendance(mock_atendimento_instance)

        assert mock_atendimento_instance.departamento == mock_dept
        assert mock_atendimento_instance.etapa_atual == mock_etapa
        mock_fluxo.etapas.filter.assert_called_once_with(
            nome="Fila de Atendimento", tipo_etapa="fila"
        )  # Using string to avoid import issue from TipoEtapa
        mock_atendimento_instance.save.assert_called_once_with(
            update_fields=["departamento", "etapa_atual"]
        )

    def test_update_attendance_status_ongoing(
        self,
        mock_fluxo_get_or_create,
        mock_dept_get_or_create,
        mock_atendimento_instance,
    ):
        """Tests updating an attendance to the 'Em Atendimento' status and etapa."""
        mock_dept = MagicMock()
        mock_fluxo = MagicMock()
        mock_etapa = MagicMock(spec=EtapaFluxo, nome="Em Atendimento")

        mock_dept_get_or_create.return_value = (mock_dept, False)
        mock_fluxo_get_or_create.return_value = (mock_fluxo, False)
        mock_fluxo.etapas.filter.return_value.first.return_value = mock_etapa

        manager = AttendanceStructureManager()
        manager._update_attendance_status_ongoing(mock_atendimento_instance)

        assert (
            mock_atendimento_instance.status
            == StatusAtendimento.EM_ATENDIMENTO
        )
        assert mock_atendimento_instance.etapa_atual == mock_etapa
        mock_fluxo.etapas.filter.assert_called_once_with(
            nome="Em Atendimento", tipo_etapa="trabalho"
        )  # Using string to avoid import issue from TipoEtapa
        mock_atendimento_instance.save.assert_called_once_with(
            update_fields=["status", "etapa_atual"]
        )

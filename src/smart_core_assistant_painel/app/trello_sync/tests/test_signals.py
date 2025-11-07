from typing import Any

from unittest.mock import patch

from django.test import TestCase

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
)


class SignalCreationTests(TestCase):
    @patch(
        "smart_core_assistant_painel.app.trello_sync.services.flow_sync_service.FlowSyncService.ensure_board_for_fluxo"
    )
    def test_fluxo_post_save_triggers_board_creation(
        self, mock_ensure: Any
    ) -> None:
        dep: Departamento = Departamento.objects.create(nome="Suporte")
        FluxoAtendimento.objects.create(departamento=dep, nome="Fluxo X")
        self.assertTrue(mock_ensure.called)
from typing import Any

from unittest.mock import patch

from django.test import TestCase

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    Atendente,
    EtapaFluxo,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento
from smart_core_assistant_painel.app.trello_sync.models import TrelloBoard, TrelloList, TrelloCard


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

    @patch(
        "smart_core_assistant_painel.app.trello_sync.services.member_sync_service.MemberSyncService.invite_for_atendente"
    )
    def test_atendente_post_save_triggers_invite(self, mock_invite: Any) -> None:
        dep: Departamento = Departamento.objects.create(nome="Suporte")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Y"
        )
        # Necessário board para convite
        TrelloBoard.objects.create(
            fluxo=fluxo, external_id="b1", name="Board Y"
        )
        Atendente.objects.create(
            nome="Maria", cargo="Agente", departamento=dep, fluxo=fluxo,
            email="maria@example.com"
        )
        self.assertTrue(mock_invite.called)

    @patch(
        "smart_core_assistant_painel.app.trello_sync.services.member_sync_service.MemberSyncService.resolve_member_external_id",
        return_value="mem1",
    )
    def test_atendimento_update_adds_member_and_updates_desc(self, _mock_resolve: Any) -> None:
        dep: Departamento = Departamento.objects.create(nome="Atendimento")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Z"
        )
        etapa: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Triagem", ordem=1
        )
        board = TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bZ", name="Board Z"
        )
        lista = TrelloList.objects.create(
            etapa=etapa, board=board, external_id="lZ", name="Triagem"
        )

        agente: Atendente = Atendente.objects.create(
            nome="João", cargo="Agente", departamento=dep, fluxo=fluxo,
            email="joao@example.com", especialidades=["Vendas", "Suporte"]
        )
        at: Atendimento = Atendimento.objects.create(
            departamento=dep, etapa_atual=etapa, atendente_humano=agente,
            assunto="Ticket Teste", produto_servico="Consultoria"
        )
        # Card Trello existente
        card = TrelloCard.objects.create(
            atendimento=at, list_sync=lista, external_id="cZ", name="Ticket Teste"
        )

        class StubClient:
            def __init__(self) -> None:
                self.add_called: bool = False
                self.update_called: bool = False

            def add_member_to_card(self, card_id: str, member_id: str) -> bool:
                self.add_called = (card_id == "cZ" and member_id == "mem1")
                return True

            def update_item(self, data_source_id: str, item_id: str, payload: dict) -> str:
                # Verifica descrição contendo "Agente:", "Especialidades:" e serviço atual
                desc: str = payload.get("desc", "")
                self.update_called = (
                    data_source_id == "lZ"
                    and item_id == "cZ"
                    and "Agente:" in desc
                    and "Especialidades:" in desc
                    and "Consultoria" in desc
                )
                return item_id

        with patch(
            "smart_core_assistant_painel.app.trello_sync.signals.SERVICEHUB"
        ) as mock_hub:
            mock_hub.unified_data_service = StubClient()
            # Dispara post_save updated
            at.assunto = "Ticket Atualizado"
            at.save()
            self.assertTrue(mock_hub.unified_data_service.add_called)
            self.assertTrue(mock_hub.unified_data_service.update_called)

    @patch(
        "smart_core_assistant_painel.app.trello_sync.services.member_sync_service.MemberSyncService.resolve_member_external_id",
        return_value="memX",
    )
    def test_atendente_delete_removes_member_from_board(self, _mock_resolve: Any) -> None:
        dep: Departamento = Departamento.objects.create(nome="Operações")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Remoção"
        )
        board = TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bX", name="Board Remoção"
        )
        agente: Atendente = Atendente.objects.create(
            nome="Ana", cargo="Agente", departamento=dep, fluxo=fluxo,
            email="ana@example.com"
        )

        class StubClientRemove:
            def __init__(self) -> None:
                self.remove_called: bool = False

            def remove_member_from_board(self, board_id: str, member_id: str) -> bool:
                self.remove_called = (board_id == "bX" and member_id == "memX")
                return True

        with patch(
            "smart_core_assistant_painel.app.trello_sync.signals.SERVICEHUB"
        ) as mock_hub:
            mock_hub.unified_data_service = StubClientRemove()
            # Dispara pre_delete
            agente.delete()
            self.assertTrue(mock_hub.unified_data_service.remove_called)

from typing import Any

from unittest.mock import patch

from django.test import TestCase
from django_q.models import Schedule

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    Atendente,
    EtapaFluxo,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloBoard,
    TrelloList,
    TrelloCard,
)
from smart_core_assistant_painel.app.trello_sync.tasks import (
    task_atendimento_assign_member_and_update,
    task_atendente_remove_member,
    task_atendimento_archive_card,
)


class SignalCreationTests(TestCase):
    def test_fluxo_post_save_schedules_board_creation(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Suporte")
        fluxo = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo X"
        )
        schedule_name = f"trello_flow_board_{fluxo.id}"
        schedules = Schedule.objects.filter(name=schedule_name)
        self.assertEqual(schedules.count(), 1)
        sched = schedules.first()
        self.assertEqual(
            sched.func,
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_fluxo_ensure_board"
            ),
        )
        self.assertEqual(sched.args, str(fluxo.id))

    def test_atendente_post_save_schedules_invite(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Suporte")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Y"
        )
        # Necessário board para convite
        TrelloBoard.objects.create(
            fluxo=fluxo, external_id="b1", name="Board Y"
        )
        atendente = Atendente.objects.create(
            nome="Maria", cargo="Agente", departamento=dep, fluxo=fluxo,
            email="maria@example.com"
        )
        schedule_name = f"trello_member_invite_{atendente.id}"
        schedules = Schedule.objects.filter(name=schedule_name)
        self.assertEqual(schedules.count(), 1)
        sched = schedules.first()
        self.assertEqual(
            sched.func,
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendente_invite"
            ),
        )
        self.assertEqual(sched.args, str(atendente.id))

    @patch(
        "smart_core_assistant_painel.app.trello_sync.services.member_sync_service.MemberSyncService.resolve_member_external_id",
        return_value="mem1",
    )
    def test_task_assign_member_and_update_executes(self, _mock_resolve: Any) -> None:
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
        contato: Contato = Contato.objects.create(
            telefone="5511977777777", nome_contato="Cliente Z"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa,
            atendente_humano=agente,
            assunto="Ticket Teste",
            produto_servico="Consultoria",
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

            def update_item(
                self,
                data_source_id: str,
                item_id: str,
                payload: dict[str, Any],
            ) -> str:
                # Comentário: valida texto conforme _build_rich_description
                # Espera conter "Atendente:" e o produto/serviço informado.
                desc: str = payload.get("desc", "")
                self.update_called = (
                    data_source_id == "lZ"
                    and item_id == "cZ"
                    and "Atendente:" in desc
                    and "Consultoria" in desc
                )
                return item_id

        # Patch duplo: tasks.SERVICEHUB e modules.services.SERVICEHUB
        class HubStub:
            def __init__(self, client: Any) -> None:
                self.unified_data_service = client

        stub_client = StubClient()
        hub_stub = HubStub(stub_client)
        with patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.SERVICEHUB",
            new=hub_stub,
        ), patch(
            "smart_core_assistant_painel.app.trello_sync.services.ticket_sync_service.SERVICEHUB",
            new=hub_stub,
        ):
            # Executa a task diretamente
            task_atendimento_assign_member_and_update(at.id)
            self.assertTrue(stub_client.add_called)
            self.assertTrue(stub_client.update_called)

    def test_atendimento_resolvido_schedules_archive(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Suporte")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Arch"
        )
        etapa: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa", ordem=1
        )
        TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bArch", name="Board Arch"
        )
        contato: Contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa,
            assunto="Teste",
        )
        at.status = StatusAtendimento.RESOLVIDO
        at.save()
        schedule_name = f"trello_at_archive_{at.id}"
        schedules = Schedule.objects.filter(name=schedule_name)
        self.assertEqual(schedules.count(), 1)
        sched = schedules.first()
        self.assertEqual(
            sched.func,
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_archive_card"
            ),
        )
        self.assertEqual(sched.args, str(at.id))

    def test_task_atendimento_archive_executes(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Ops")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo X"
        )
        etapa: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa X", ordem=1
        )
        board = TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bX", name="Board X"
        )
        lista = TrelloList.objects.create(
            etapa=etapa, board=board, external_id="lX", name="Lista X"
        )
        contato: Contato = Contato.objects.create(
            telefone="5511988888888", nome_contato="Cliente X"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa,
            assunto="Ticket",
        )
        card = TrelloCard.objects.create(
            atendimento=at, list_sync=lista, external_id="cX", name="Ticket"
        )

        class StubArchive:
            def __init__(self) -> None:
                self.archive_called: bool = False

            def archive_item(self, item_id: str) -> bool:
                self.archive_called = (item_id == "cX")
                return True

        class HubStubArch:
            def __init__(self, client: Any) -> None:
                self.unified_data_service = client

        stub_arch = StubArchive()
        hub_stub_arch = HubStubArch(stub_arch)
        with patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.SERVICEHUB",
            new=hub_stub_arch,
        ), patch(
            "smart_core_assistant_painel.modules.services.SERVICEHUB",
            new=hub_stub_arch,
        ):
            task_atendimento_archive_card(at.id)
            self.assertTrue(stub_arch.archive_called)

    @patch(
        "smart_core_assistant_painel.app.trello_sync.services.member_sync_service.MemberSyncService.resolve_member_external_id",
        return_value="memX",
    )
    def test_atendente_delete_schedules_remove(self, _mock_resolve: Any) -> None:
        dep: Departamento = Departamento.objects.create(nome="Operações")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Remoção"
        )
        board = TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bX", name="Board Remoção"
        )
        atendente: Atendente = Atendente.objects.create(
            nome="Ana", cargo="Agente", departamento=dep, fluxo=fluxo,
            email="ana@example.com"
        )
        atendente_id = atendente.id
        atendente.delete()
        schedule_name = f"trello_member_remove_{atendente_id}"
        schedules = Schedule.objects.filter(name=schedule_name)
        self.assertEqual(schedules.count(), 1)
        sched = schedules.first()
        self.assertEqual(
            sched.func,
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendente_remove_member"
            ),
        )
        self.assertEqual(sched.args, str(atendente_id))

    @patch(
        "smart_core_assistant_painel.app.trello_sync.services.member_sync_service.MemberSyncService.resolve_member_external_id",
        return_value="memY",
    )
    def test_task_remove_member_executes(self, _mock_resolve: Any) -> None:
        dep: Departamento = Departamento.objects.create(nome="Operações2")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Remoção2"
        )
        TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bY", name="Board Remoção2"
        )
        atendente: Atendente = Atendente.objects.create(
            nome="Leo", cargo="Agente", departamento=dep, fluxo=fluxo,
            email="leo@example.com"
        )

        class StubClientRemove:
            def __init__(self) -> None:
                self.remove_called: bool = False

            def remove_member_from_board(self, board_id: str, member_id: str) -> bool:
                self.remove_called = (board_id == "bY" and member_id == "memY")
                return True

        class HubStubRemove:
            def __init__(self, client: Any) -> None:
                self.unified_data_service = client

        stub_remove = StubClientRemove()
        hub_stub_remove = HubStubRemove(stub_remove)
        with patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.SERVICEHUB",
            new=hub_stub_remove,
        ), patch(
            "smart_core_assistant_painel.modules.services.SERVICEHUB",
            new=hub_stub_remove,
        ):
            task_atendente_remove_member(atendente.id)
            self.assertTrue(stub_remove.remove_called)

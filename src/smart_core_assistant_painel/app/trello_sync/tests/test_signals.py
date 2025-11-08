from typing import Any

from unittest.mock import patch

from django.test import TestCase
from django_q.models import Schedule

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    Atendente,
    EtapaFluxo,
    TipoEtapa,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
    Mensagem,
    TipoMensagem,
    TipoRemetente,
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
    task_atendimento_move_to_etapa_list,
    task_trello_archive_card_by_external_id,
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
        # Espera serialização em tupla para Django-Q
        self.assertEqual(sched.args, repr((fluxo.id,)))

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
        # Espera serialização em tupla para Django-Q
        self.assertEqual(sched.args, repr((atendente.id,)))

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

    def test_atendimento_resolvido_move_to_resolvido_list_is_scheduled(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Suporte")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Arch"
        )
        # Etapa inicial qualquer
        etapa_inicial: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa", ordem=1
        )
        # Etapa padrão Resolvido
        etapa_res: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Resolvido", ordem=1000, tipo_etapa="finalizacao"
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
            etapa_atual=etapa_inicial,
            assunto="Teste",
        )
        at.status = StatusAtendimento.RESOLVIDO
        at.save()

        # Deve ter atualizado a etapa para "Resolvido"
        at.refresh_from_db()
        self.assertEqual(at.etapa_atual_id, etapa_res.id)

        # Agenda deve apontar para a task de movimento por etapa
        schedules = Schedule.objects.filter(
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_move_to_etapa_list"
            ),
            args=repr((at.id,)),
        )
        self.assertEqual(schedules.count(), 1)

    def test_atendimento_pendencia_move_to_pendencia_list_is_scheduled(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Suporte P")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Pend"
        )
        # Etapa inicial qualquer
        etapa_inicial: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa", ordem=1
        )
        # Etapa padrão Pendência
        etapa_pend: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Pendência", ordem=999, tipo_etapa="espera"
        )
        TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bPend", name="Board Pend"
        )
        contato: Contato = Contato.objects.create(
            telefone="5511988888888", nome_contato="Cliente P"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa_inicial,
            assunto="Teste Pend",
        )
        at.status = StatusAtendimento.PENDENCIA
        at.save()

        # Deve ter atualizado a etapa para "Pendência"
        at.refresh_from_db()
        self.assertEqual(at.etapa_atual_id, etapa_pend.id)

        # Agenda deve apontar para a task de movimento por etapa
        schedules = Schedule.objects.filter(
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_move_to_etapa_list"
            ),
            args=repr((at.id,)),
        )
        self.assertEqual(schedules.count(), 1)

    def test_atendimento_cancelado_move_to_cancelado_list_is_scheduled(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Suporte2")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Cancel"
        )
        # Etapa inicial qualquer
        etapa_inicial: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa", ordem=1
        )
        # Etapa padrão Cancelado
        etapa_cancel: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Cancelado", ordem=1001, tipo_etapa="finalizacao"
        )
        TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bCancel", name="Board Cancel"
        )
        contato: Contato = Contato.objects.create(
            telefone="5511900000000", nome_contato="Cliente Cancel"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa_inicial,
            assunto="Teste Cancel",
        )
        at.status = StatusAtendimento.CANCELADO
        at.save()

        # Deve ter atualizado a etapa para "Cancelado"
        at.refresh_from_db()
        self.assertEqual(at.etapa_atual_id, etapa_cancel.id)

        # Agenda deve apontar para a task de movimento por etapa
        schedules = Schedule.objects.filter(
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_move_to_etapa_list"
            ),
            args=repr((at.id,)),
        )
        self.assertEqual(schedules.count(), 1)

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
        # Espera serialização em tupla para Django-Q
        self.assertEqual(sched.args, repr((atendente_id,)))

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

    def test_task_atendimento_move_to_etapa_list_executes(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Ops")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Move"
        )
        etapa1: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa 1", ordem=1
        )
        etapa2: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa 2", ordem=2
        )
        board = TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bMove", name="Board Move"
        )
        lista1 = TrelloList.objects.create(
            etapa=etapa1, board=board, external_id="l1", name="Etapa 1"
        )
        lista2 = TrelloList.objects.create(
            etapa=etapa2, board=board, external_id="l2", name="Etapa 2"
        )

        contato: Contato = Contato.objects.create(
            telefone="5511911111111", nome_contato="Cliente Move"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa1,
            assunto="Mover",
        )
        card = TrelloCard.objects.create(
            atendimento=at, list_sync=lista1, external_id="c1", name="Mover"
        )

        class StubClientMove:
            def __init__(self) -> None:
                self.move_called: bool = False

            def update_item(
                self,
                data_source_id: str,
                item_id: str,
                payload: dict[str, Any],
            ) -> str:
                # Comentário: valida mudança de lista via idList.
                id_list = payload.get("idList")
                self.move_called = (
                    data_source_id == "l2" and item_id == "c1" and id_list == "l2"
                )
                return item_id

        class HubStubMove:
            def __init__(self, client: Any) -> None:
                self.unified_data_service = client

        class TicketServiceStub:
            def __init__(self) -> None:
                self.client = stub_move

            def ensure_card_for_atendimento(self, atendimento: Any) -> TrelloCard:
                # Comentário: retorna o card já existente
                return card

            def update_card_rich_content(
                self, card_obj: TrelloCard, atendimento_obj: Atendimento
            ) -> None:
                # Comentário: noop para evitar I/O externo
                return None

        # Atualiza a etapa do atendimento para a etapa 2
        at.etapa_atual = etapa2
        at.save()

        stub_move = StubClientMove()
        hub_stub_move = HubStubMove(stub_move)
        with patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.SERVICEHUB",
            new=hub_stub_move,
        ), patch(
            "smart_core_assistant_painel.modules.services.SERVICEHUB",
            new=hub_stub_move,
        ), patch(
            "smart_core_assistant_painel.app.trello_sync.services.ticket_sync_service.SERVICEHUB",
            new=hub_stub_move,
        ), patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.TicketSyncService",
            new=TicketServiceStub,
        ):
            task_atendimento_move_to_etapa_list(at.id)
            self.assertTrue(stub_move.move_called)

        # Recarrega o card e valida que a lista foi atualizada
        card.refresh_from_db()
        self.assertEqual(card.list_sync_id, lista2.id)

    def test_task_move_to_finalizacao_marks_due_complete(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Ops F")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Final"
        )
        etapa1: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa 1", ordem=1
        )
        etapa_final: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo,
            nome="Resolvido",
            ordem=2,
            tipo_etapa=TipoEtapa.FINALIZACAO,
        )
        board = TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bF", name="Board Final"
        )
        lista1 = TrelloList.objects.create(
            etapa=etapa1, board=board, external_id="lF1", name="Etapa 1"
        )
        lista2 = TrelloList.objects.create(
            etapa=etapa_final,
            board=board,
            external_id="lF2",
            name="Resolvido",
        )

        contato: Contato = Contato.objects.create(
            telefone="5511900001111", nome_contato="Cliente F"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa1,
            assunto="Final",
        )
        card = TrelloCard.objects.create(
            atendimento=at, list_sync=lista1, external_id="cF", name="Final"
        )

        class StubClientFinal:
            def __init__(self) -> None:
                self.saw_due_complete: bool = False
                self.move_called: bool = False

            def update_item(
                self,
                data_source_id: str,
                item_id: str,
                payload: dict[str, Any],
            ) -> str:
                if payload.get("idList") == "lF2":
                    self.move_called = True
                if payload.get("dueComplete") is True:
                    self.saw_due_complete = True
                return item_id

            def get_item(self, data_source_id: str, item_id: str) -> dict[str, Any]:
                # Comentário: retorna sem labels para forçar adição
                return {"idLabels": []}

            def ensure_labels(self, board_id: str, labels: dict[str, str]) -> dict[str, str]:
                # Comentário: finge criação de label e retorna um id estável
                return {list(labels.keys())[0]: "lblF"}

        class HubStubFinal:
            def __init__(self, client: Any) -> None:
                self.unified_data_service = client

        class TicketServiceStub:
            def __init__(self) -> None:
                self.client = stub_final

            def ensure_card_for_atendimento(self, atendimento: Any) -> TrelloCard:
                return card

            def update_card_rich_content(
                self, card_obj: TrelloCard, atendimento_obj: Atendimento
            ) -> None:
                return None

        # Muda etapa para finalização
        at.etapa_atual = etapa_final
        at.save()

        stub_final = StubClientFinal()
        hub_stub_final = HubStubFinal(stub_final)
        with patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.SERVICEHUB",
            new=hub_stub_final,
        ), patch(
            "smart_core_assistant_painel.modules.services.SERVICEHUB",
            new=hub_stub_final,
        ), patch(
            "smart_core_assistant_painel.app.trello_sync.services.ticket_sync_service.SERVICEHUB",
            new=hub_stub_final,
        ), patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.TicketSyncService",
            new=TicketServiceStub,
        ):
            task_atendimento_move_to_etapa_list(at.id)
            self.assertTrue(stub_final.move_called)
            self.assertTrue(stub_final.saw_due_complete)

    def test_task_move_sets_cover_color_from_stage(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Ops C")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Cover"
        )
        etapa1: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa 1", ordem=1
        )
        etapa2: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa 2", ordem=2, cor="#FF0000"
        )
        board = TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bC", name="Board Cover"
        )
        lista1 = TrelloList.objects.create(
            etapa=etapa1, board=board, external_id="lC1", name="Etapa 1"
        )
        lista2 = TrelloList.objects.create(
            etapa=etapa2, board=board, external_id="lC2", name="Etapa 2"
        )

        contato: Contato = Contato.objects.create(
            telefone="5511900002222", nome_contato="Cliente C"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa1,
            assunto="Cover",
        )
        card = TrelloCard.objects.create(
            atendimento=at, list_sync=lista1, external_id="cC", name="Cover"
        )

        class StubClientCover:
            def __init__(self) -> None:
                self.move_called: bool = False
                self.cover_color: str = ""

            def update_item(
                self,
                data_source_id: str,
                item_id: str,
                payload: dict[str, Any],
            ) -> str:
                id_list = payload.get("idList")
                self.move_called = (
                    data_source_id == "lC2" and item_id == "cC" and id_list == "lC2"
                )
                return item_id

            def set_card_cover_color(self, card_id: str, color: str) -> bool:
                if card_id == "cC":
                    self.cover_color = color
                return True

        class HubStubCover:
            def __init__(self, client: Any) -> None:
                self.unified_data_service = client

        class TicketServiceStub:
            def __init__(self) -> None:
                self.client = stub_cover

            def ensure_card_for_atendimento(self, atendimento: Any) -> TrelloCard:
                return card

            def update_card_rich_content(
                self, card_obj: TrelloCard, atendimento_obj: Atendimento
            ) -> None:
                return None

        # Move para etapa 2 (com cor definida)
        at.etapa_atual = etapa2
        at.save()

        stub_cover = StubClientCover()
        hub_stub_cover = HubStubCover(stub_cover)
        with patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.SERVICEHUB",
            new=hub_stub_cover,
        ), patch(
            "smart_core_assistant_painel.modules.services.SERVICEHUB",
            new=hub_stub_cover,
        ), patch(
            "smart_core_assistant_painel.app.trello_sync.services.ticket_sync_service.SERVICEHUB",
            new=hub_stub_cover,
        ), patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.TicketSyncService",
            new=TicketServiceStub,
        ):
            task_atendimento_move_to_etapa_list(at.id)
            self.assertTrue(stub_cover.move_called)
            self.assertEqual(stub_cover.cover_color, "red")

    def test_atendimento_delete_schedules_archive_by_external_id(self) -> None:
        dep: Departamento = Departamento.objects.create(nome="Ops")
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep, nome="Fluxo Del"
        )
        etapa: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo, nome="Etapa", ordem=1
        )
        board = TrelloBoard.objects.create(
            fluxo=fluxo, external_id="bDel", name="Board Del"
        )
        lista = TrelloList.objects.create(
            etapa=etapa, board=board, external_id="lDel", name="Etapa"
        )
        contato: Contato = Contato.objects.create(
            telefone="5511922222222", nome_contato="Cliente Del"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato,
            departamento=dep,
            etapa_atual=etapa,
            assunto="Deletar",
        )
        TrelloCard.objects.create(
            atendimento=at, list_sync=lista, external_id="cDel", name="Del"
        )

        # Dispara diretamente o receiver para evitar efeitos colaterais
        from smart_core_assistant_painel.app.trello_sync.signals import (
            atendimento_deleted_archive_card,
        )
        atendimento_deleted_archive_card(Atendimento, at)
        schedule = Schedule.objects.get(
            name=f"trello_at_archive_del_{at.id}"
        )
        self.assertEqual(
            schedule.func,
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_trello_archive_card_by_external_id"
            ),
        )
        # Espera serialização em tupla para Django-Q
        self.assertEqual(schedule.args, repr(("cDel",)))

    def test_task_trello_archive_by_external_id_executes(self) -> None:
        class StubClientArchive:
            def __init__(self) -> None:
                self.archive_called: bool = False

            def archive_item(self, item_id: str) -> bool:
                self.archive_called = (item_id == "cDel")
                return True

        class HubStubArchive:
            def __init__(self, client: Any) -> None:
                self.unified_data_service = client

        stub_archive = StubClientArchive()
        hub_stub_archive = HubStubArchive(stub_archive)
        with patch(
            "smart_core_assistant_painel.app.trello_sync.tasks.SERVICEHUB",
            new=hub_stub_archive,
        ), patch(
            "smart_core_assistant_painel.modules.services.SERVICEHUB",
            new=hub_stub_archive,
        ):
            task_trello_archive_card_by_external_id("cDel")
            self.assertTrue(stub_archive.archive_called)

    def test_mensagem_post_save_schedules_card_update(self) -> None:
        """Ao criar Mensagem, deve agendar atualização de card Trello."""
        contato: Contato = Contato.objects.create(
            telefone="5511900000000", nome_contato="Cliente S"
        )
        at: Atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.EM_ANDAMENTO
        )

        Mensagem.objects.create(
            atendimento=at,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Nova mensagem",
            message_id_whatsapp="MSG001",
        )

        schedule_name = f"trello_at_msg_update_{at.id}"
        schedules = Schedule.objects.filter(name=schedule_name)
        self.assertEqual(schedules.count(), 1)
        sched = schedules.first()
        self.assertEqual(
            sched.func,
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_update_card_rich_content"
            ),
        )
        # Espera serialização em tupla para Django-Q
        self.assertEqual(sched.args, repr((at.id,)))

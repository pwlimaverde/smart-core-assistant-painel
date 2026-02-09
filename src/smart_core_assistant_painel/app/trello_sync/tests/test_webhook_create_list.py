from django.test import TestCase

from smart_core_assistant_painel.app.operacional.models import (
    Departamento,
    EtapaFluxo,
    FluxoAtendimento,
)
from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloBoard,
    TrelloList,
)
from smart_core_assistant_painel.app.trello_sync.services.webhook_processing_service import (
    WebhookProcessingService,
)


class TestWebhookCreateList(TestCase):
    def setUp(self):
        self.service = WebhookProcessingService()

        # Setup Data
        self.departamento = Departamento.objects.create(
            nome="Dep Test", slug="dep-test"
        )
        self.fluxo = FluxoAtendimento.objects.create(
            departamento=self.departamento,
            nome="Fluxo Test",
            # slug="fluxo-test"  <-- Removed
        )
        self.board = TrelloBoard.objects.create(
            fluxo=self.fluxo, external_id="board123", name="Board Test"
        )

        # Create an initial stage to verify order increment
        self.etapa1 = EtapaFluxo.objects.create(
            fluxo=self.fluxo, nome="Etapa 1", ordem=1
        )

    def test_create_list_webhook(self):
        # Get current max order
        last_etapa = (
            EtapaFluxo.objects.filter(fluxo=self.fluxo)
            .order_by("-ordem")
            .first()
        )
        max_order = last_etapa.ordem if last_etapa else 0

        payload = {
            "action": {
                "id": "act123",
                "type": "createList",
                "data": {
                    "board": {"id": "board123", "name": "Board Test"},
                    "list": {
                        "id": "list999",
                        "name": "Nova Lista Trello",
                        "pos": 12345.67,
                    },
                },
            }
        }

        self.service.process(payload)

        # Verify EtapaFluxo created
        etapa_created = EtapaFluxo.objects.filter(
            fluxo=self.fluxo, nome="Nova Lista Trello"
        ).first()
        self.assertIsNotNone(etapa_created)
        self.assertEqual(etapa_created.ordem, max_order + 1)
        self.assertEqual(etapa_created.tipo_etapa, "TRABALHO")

        # Verify TrelloList created
        trello_list = TrelloList.objects.filter(external_id="list999").first()
        self.assertIsNotNone(trello_list)
        self.assertEqual(trello_list.etapa, etapa_created)
        self.assertEqual(trello_list.board, self.board)
        self.assertEqual(trello_list.name, "Nova Lista Trello")

    def test_create_list_webhook_pos_top(self):
        """Test webhook with pos='top' (string) instead of float."""
        payload = {
            "action": {
                "type": "createList",
                "data": {
                    "board": {"id": "board123", "name": "Board Test"},
                    "list": {
                        "id": "list_top",
                        "name": "Lista Top",
                        "pos": "top",
                    },
                },
            }
        }

        self.service.process(payload)

        trello_list = TrelloList.objects.filter(external_id="list_top").first()
        self.assertIsNotNone(trello_list)
        self.assertEqual(trello_list.position, 0.0)

    def test_create_list_webhook_unknown_board(self):
        payload = {
            "action": {
                "type": "createList",
                "data": {
                    "board": {"id": "unknown_board", "name": "Unknown"},
                    "list": {"id": "list888", "name": "Lista Ignorada"},
                },
            }
        }

        self.service.process(payload)

        self.assertFalse(
            TrelloList.objects.filter(external_id="list888").exists()
        )

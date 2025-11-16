import json
from typing import Any, Dict

from django.test import Client, TestCase
from django.urls import reverse

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
)
from smart_core_assistant_painel.app.ui.atendimentos.utils import (
    send_message_response_by_contact,
)


class TestEvolutionWebhookFlow(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()

    def test_end_to_end_contact_attendance_message(self) -> None:
        payload: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "99910a55-8bbd-440a-9e14-9d5833a63c5e",
            "apikey": "TEST_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "558897141275@s.whatsapp.net",
                    "remoteJidAlt": "62921321222334@lid",
                    "fromMe": False,
                    "id": "ACE67E7835EF52C7FF28C63C5616F4A4",
                    "participant": "",
                    "addressingMode": "pn",
                },
                "pushName": "Paulo Weslley Limaverde",
                "status": "DELIVERY_ACK",
                "message": {
                    "conversation": "Teste recebimento de mensagens",
                },
                "messageType": "conversation",
                "messageTimestamp": 1763301593,
                "instanceId": "99910a55-8bbd-440a-9e14-9d5833a63c5e",
                "source": "android",
            },
            "sender": "5588921729550@s.whatsapp.net",
        }

        resp = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        evo_contact: EvolutionContact | None = EvolutionContact.objects.first()
        self.assertIsNotNone(evo_contact)
        assert evo_contact is not None
        self.assertIsNotNone(evo_contact.contact_id)

        send_message_response_by_contact(int(evo_contact.contact_id))

        contato: Contato | None = Contato.objects.filter(id=evo_contact.contact_id).first()
        self.assertIsNotNone(contato)
        assert contato is not None

        atendimento: Atendimento | None = Atendimento.objects.filter(contato=contato).first()
        self.assertIsNotNone(atendimento)
        assert atendimento is not None

        mensagem: Mensagem | None = Mensagem.objects.filter(atendimento=atendimento).first()
        self.assertIsNotNone(mensagem)
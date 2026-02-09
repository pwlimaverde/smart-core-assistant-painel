import json
import os
import sys

import django
from django.test import RequestFactory

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

# Setup Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.core.settings",
)
django.setup()

from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
)
from smart_core_assistant_painel.app.evolution_sync.views import webhook


def run_test():
    # Clear existing data
    Contato.objects.all().delete()
    EvolutionContact.objects.all().delete()

    print("Initial state: Contato count =", Contato.objects.count())

    # Scenario 2: LID Payload
    payload_lid = {
        "event": "messages.upsert",
        "instance": "5588921729550",
        "data": {
            "key": {
                "remoteJid": "76201477542116@lid",
                "remoteJidAlt": "558893074699@s.whatsapp.net",
                "fromMe": False,
                "id": "ACF74C317ABADED4BE7EDC7E41BE13EE",
                "participant": "",
                "addressingMode": "lid",
            },
            "pushName": "Gleidiane Limaverde",
            "status": "DELIVERY_ACK",
            "message": {
                "conversation": "Teste envio de mensagem",
                "messageContextInfo": {
                    "deviceListMetadata": {
                        "senderKeyIndexes": [],
                        "recipientKeyIndexes": [],
                        "senderTimestamp": {
                            "low": 1761759212,
                            "high": 0,
                            "unsigned": True,
                        },
                        "recipientKeyHash": {
                            "0": 194,
                        },
                        "recipientTimestamp": {
                            "low": 1763240581,
                            "high": 0,
                            "unsigned": True,
                        },
                    },
                    "deviceListMetadataVersion": 2,
                    "messageSecret": {
                        "0": 30,
                    },
                },
            },
            "messageType": "conversation",
            "messageTimestamp": 1763326182,
            "instanceId": "99910a55-8bbd-440a-9e14-9d5833a63c5e",
            "source": "android",
        },
        "destination": " http://192.168.3.90:8000/sync/evolution/webhook/ ",
        "date_time": "2025-11-16T17:49:42.155Z",
        "sender": "5588921729550@s.whatsapp.net",
        "server_url": "http://localhost:8080",
        "apikey": "50675099048D-44D0-A0C6-FAE0F020EC3E",
    }

    print("\n--- Sending LID Payload ---")
    factory = RequestFactory()
    request = factory.post(
        "/evolution/webhook/",
        data=json.dumps(payload_lid),
        content_type="application/json",
    )

    response = webhook(request)
    print("Response:", response.status_code, response.content)

    print("Final state: Contato count =", Contato.objects.count())
    for c in Contato.objects.all():
        print(
            f"Contato: id={c.id}, nome='{c.nome_contato}', telefone='{c.telefone}'"
        )

    print(
        "Final state: EvolutionContact count =",
        EvolutionContact.objects.count(),
    )
    for ec in EvolutionContact.objects.all():
        print(
            f"EvoContact: id={ec.id}, jid={ec.jid}, contact_id={ec.contact_id}"
        )


if __name__ == "__main__":
    run_test()

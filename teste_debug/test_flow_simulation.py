import os
import sys
import django
from unittest.mock import patch, MagicMock
import json
import traceback
from loguru import logger

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)
os.environ["DISABLE_APP_SERVICES_INIT"] = (
    "1"  # Bypass service initialization (Firebase)
)

try:
    django.setup()
except Exception as e:
    print(f"Failed to setup Django: {e}")
    traceback.print_exc()
    sys.exit(1)

# Now import app modules
from django.test import RequestFactory
from smart_core_assistant_painel.app.evolution_sync.views import (
    webhook as evolution_webhook,
)
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Contato,
    Mensagem,
    Atendimento,
)
from smart_core_assistant_painel.app.ui.atendimentos.utils import (
    send_message_response_by_contact,
)
from django_q.models import Schedule
from django.core.cache import cache

# Configure logger
logger.add("teste_debug/test_log.log", rotation="1 MB")

# Payload provided by user
PAYLOAD = {
    "source": "EvolutionAPI",
    "instance": "5588921729550",
    "instance_id": "99910a55-8bbd-440a-9e14-9d5833a63c5e",
    "sender_jid": "5588921729550@s.whatsapp.net",
    "contact": {
        "jid": "558893074699@s.whatsapp.net",
        "lid": "76201477542116@lid",
        "addressing_mode": "lid",
        "phone": "",
    },
    "message": {
        "id": "ACF74C317ABADED4BE7EDC7E41BE13EE",
        "type": "conversation",
        "text": "Teste envio de mensagem",
        "metadata": {
            "messageTimestamp": 1763326182,
            "instanceId": "99910a55-8bbd-440a-9e14-9d5833a63c5e",
            "source": "android",
        },
    },
    "profile": {"push_name": "Gleidiane Limaverde"},
    "apikey": "50675099048D-44D0-A0C6-FAE0F020EC3E",
    "raw": {
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
                            "1": 76,
                            "2": 52,
                            "3": 107,
                            "4": 100,
                            "5": 206,
                            "6": 22,
                            "7": 173,
                            "8": 241,
                            "9": 201,
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
                        "1": 154,
                        "2": 207,
                        "3": 193,
                        "4": 156,
                        "5": 85,
                        "6": 58,
                        "7": 211,
                        "8": 2,
                        "9": 110,
                        "10": 152,
                        "11": 241,
                        "12": 158,
                        "13": 192,
                        "14": 100,
                        "15": 47,
                        "16": 150,
                        "17": 55,
                        "18": 135,
                        "19": 110,
                        "20": 58,
                        "21": 45,
                        "22": 8,
                        "23": 250,
                        "24": 188,
                        "25": 146,
                        "26": 126,
                        "27": 145,
                        "28": 181,
                        "29": 154,
                        "30": 19,
                        "31": 247,
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
    },
}


def run_test():
    print("--- Starting Automated Flow Test ---")

    # 1. Simulate Webhook
    print("\n[1] Simulating Webhook...")
    factory = RequestFactory()
    request = factory.post(
        "/sync/evolution/webhook/",
        data=json.dumps(PAYLOAD["raw"]),
        content_type="application/json",
    )

    # Mock requests to avoid external calls during webhook processing if any
    with patch("requests.post") as mock_post:
        response = evolution_webhook(request)
        print(
            f"Webhook Response: {response.status_code} - {response.content.decode()}"
        )

    if response.status_code != 200:
        print("FAILED: Webhook returned non-200 status")
        return

    # 2. Verify Contact Creation
    print("\n[2] Verifying Contact Creation...")
    # Extract expected data
    jid = PAYLOAD["contact"]["jid"]
    lid = PAYLOAD["contact"]["lid"]
    push_name = PAYLOAD["profile"]["push_name"]

    evo_contact = EvolutionContact.objects.filter(jid=jid).first()
    if not evo_contact and lid:
        evo_contact = EvolutionContact.objects.filter(lid=lid).first()

    if evo_contact:
        print(f"SUCCESS: EvolutionContact found (ID: {evo_contact.id})")
        contact = evo_contact.contact
        if contact:
            print(f"SUCCESS: Linked Contact found (ID: {contact.id})")
            print(f"Contact Name: {contact.nome_contato}")
            print(f"Contact Profile Name: {contact.nome_perfil_whatsapp}")

            if contact.nome_perfil_whatsapp != push_name:
                print(
                    f"WARNING: Profile name mismatch. Expected '{push_name}', got '{contact.nome_perfil_whatsapp}'"
                )
            else:
                print("SUCCESS: Profile name matches")
        else:
            print("FAILED: EvolutionContact has no linked Contact")
            return
    else:
        print("FAILED: EvolutionContact not found")
        return

    contact_id = contact.id

    # 3. Verify Buffer
    print("\n[3] Verifying Buffer...")
    cache_key = f"evo_buffer_{contact_id}"
    buffer = cache.get(cache_key)
    if buffer:
        print(f"SUCCESS: Buffer found with {len(buffer)} messages")
        print(f"Buffer content: {buffer}")
    else:
        print("FAILED: Buffer is empty or not found")
        # return # Proceed to see if schedule exists

    # 4. Verify Schedule
    print("\n[4] Verifying Schedule...")
    schedule_name = f"process_contact_{contact_id}"
    schedule = Schedule.objects.filter(name=schedule_name).first()
    if schedule:
        print(f"SUCCESS: Schedule found (ID: {schedule.id})")
        print(f"Schedule Args: {schedule.args}")
        print(f"Schedule Next Run: {schedule.next_run}")
    else:
        print("FAILED: Schedule not found")
        return

    # 5. Simulate Processing
    print("\n[5] Simulating Processing (send_message_response_by_contact)...")

    # Mock AI analysis to avoid costs and latency
    mock_ai_result = MagicMock()
    mock_ai_result.resposta_bot = (
        "Resposta automática de teste gerada pelo mock."
    )
    mock_ai_result.confiabilidade = 0.95
    mock_ai_result.transferir_atendimento = False

    with patch(
        "smart_core_assistant_painel.app.ui.atendimentos.utils.FeaturesCompose.analise_mensage",
        return_value=mock_ai_result,
    ) as mock_ai:
        # Execute the function directly with the args from the schedule
        # The args are stored as a string representation of a tuple in the DB, e.g. "(123,)"
        # We need to parse it or just pass the contact_id directly as the function supports it
        try:
            send_message_response_by_contact(contact_id)
            print("SUCCESS: Processing function executed without error")
        except Exception as e:
            print(f"FAILED: Processing function raised exception: {e}")
            import traceback

            traceback.print_exc()
            return

    # 6. Verify Message Creation
    print("\n[6] Verifying Message Creation...")
    # Check for messages created in the last few seconds for this contact
    # Assuming we can find the atendimento
    atendimento = (
        Atendimento.objects.filter(cliente_id=contact_id)
        .order_by("-id")
        .first()
    )
    if atendimento:
        print(f"SUCCESS: Atendimento found (ID: {atendimento.id})")
        last_msg = (
            Mensagem.objects.filter(atendimento=atendimento)
            .order_by("-id")
            .first()
        )
        if last_msg:
            print(f"SUCCESS: Message created (ID: {last_msg.id})")
            print(f"Message Content: {last_msg.conteudo}")
            print(f"Message Type: {last_msg.message_type}")
            print(f"Bot Response: {last_msg.resposta_bot}")

            if last_msg.conteudo == PAYLOAD["message"]["text"]:
                print("SUCCESS: Message content matches payload")
            else:
                print(
                    f"WARNING: Message content mismatch. Expected '{PAYLOAD['message']['text']}', got '{last_msg.conteudo}'"
                )
        else:
            print("FAILED: No message found for this atendimento")
    else:
        print("FAILED: No Atendimento found for this contact")

    print("\n--- Test Completed ---")


if __name__ == "__main__":
    try:
        run_test()
    except Exception:
        with open("teste_debug/error.log", "w") as f:
            f.write(traceback.format_exc())
        print("ERROR: Check teste_debug/error.log")

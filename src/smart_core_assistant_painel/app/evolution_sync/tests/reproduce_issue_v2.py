import os
import uuid
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)
django.setup()

from smart_core_assistant_painel.app.evolution_sync.services.webhook import (
    WebhookProcessor,
)
from smart_core_assistant_painel.app.evolution_sync.domain.schemas import (
    EvolutionWebhookEnvelope,
)
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionInstance,
)
from unittest.mock import MagicMock, patch

# Create instances with mismatched digit counts
# Instance A: Registered with 13 digits (with 9)
EvolutionInstance.objects.update_or_create(
    name="5588997141275",
    defaults={
        "instance_id": "inst_a",
        "api_key": "key_a",
        "phone_number": "5588997141275",
    },
)

# Instance B: Receiver
EvolutionInstance.objects.update_or_create(
    name="5588921729550",
    defaults={
        "instance_id": "inst_b",
        "api_key": "key_b",
        "phone_number": "5588921729550",
    },
)

# Payload: Instance B receiving message from Instance A
# BUT Instance A shows up as 12 digits (without 9) in the sender field
payload = {
    "event": "messages.upsert",
    "instance": "5588921729550",
    "data": {
        "key": {
            "remoteJid": "558897141275@s.whatsapp.net",  # 12 digits here!
            "fromMe": False,
            "id": f"MSG-{uuid.uuid4()}",
        },
        "message": {"conversation": "Teste"},
        "pushName": "Paulo",
        "messageType": "conversation",
        "messageTimestamp": 1234567890,
        "instanceId": "inst_b",
        "source": "android",
    },
    "sender": "5588921729550@s.whatsapp.net",
    "apikey": "key_b",
}

processor = WebhookProcessor()
envelopes = [EvolutionWebhookEnvelope.from_dict_single(payload)]

print(f"Processing webhook...")
print(f"Sender (RemoteJid): {envelopes[0].contact.phone}")

# We expect this to be IGNORED (return status 'ignored_from_me' or similar, or valid_envelopes empty)
# But currently it likely passes because 558897141275 != 5588997141275

with patch(
    "smart_core_assistant_painel.app.evolution_sync.services.webhook.logger"
) as mock_logger:
    result = processor.process_webhook(payload, envelopes)
    print(f"Result: {result}")

    # Check if it was ignored
    ignored = False
    for call in mock_logger.info.call_args_list:
        if "Ignoring interaction with instance" in str(call):
            print(f"SUCCESS: Logged as ignored: {call}")
            ignored = True
            break

    if not ignored:
        print("FAILURE: Message was NOT ignored.")

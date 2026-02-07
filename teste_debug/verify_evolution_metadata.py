import os
import django
from django.conf import settings

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.config.settings"
)
django.setup()

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    Mensagem,
    TipoMensagem,
    TipoRemetente,
)
from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionInstance,
    EvolutionContact,
)
from smart_core_assistant_painel.app.atendimentos.services.attendance_orchestrator import (
    AttendanceOrchestrator,
)
from smart_core_assistant_painel.app.atendimentos.services.message_analyzer import (
    MessageAnalyzer,
)
from smart_core_assistant_painel.app.atendimentos.services.attendance_structure_manager import (
    AttendanceStructureManager,
)
from smart_core_assistant_painel.app.atendimentos.services.bot_rules_engine import (
    BotRulesEngine,
)
from unittest.mock import MagicMock, patch


def test_evolution_metadata_optimization():
    print("Starting verification...")

    # 1. Setup Data
    api_key = "test_api_key_123"
    instance_name = "test_instance"
    phone_number = "5511999999999"

    # Create Instance
    instance, _ = EvolutionInstance.objects.get_or_create(
        name=instance_name,
        defaults={
            "api_key": api_key,
            "phone_number": "5511888888888",
            "active": True,
        },
    )
    instance.api_key = api_key  # Ensure api_key is set
    instance.save()
    print(
        f"Instance created: {instance.name} (ID: {instance.id}, API Key: {instance.api_key})"
    )

    # Create Contact
    contato, _ = Contato.objects.get_or_create(
        telefone=phone_number, defaults={"nome_contato": "Test User"}
    )
    print(f"Contact created: {contato.nome_contato} ({contato.telefone})")

    # Create Evolution Contact
    evo_contact, _ = EvolutionContact.objects.get_or_create(
        instance=instance,
        jid=f"{phone_number}@s.whatsapp.net",
        defaults={"contact": contato},
    )
    if not evo_contact.contact:
        evo_contact.contact = contato
        evo_contact.save()
    print(f"Evolution Contact created: {evo_contact.jid}")

    # Create Attendance
    atendimento = Atendimento.objects.create(contato=contato, status="fila")
    print(f"Attendance created: ID {atendimento.id}")

    # Create Message (simulating incoming message)
    mensagem = Mensagem.objects.create(
        atendimento=atendimento,
        tipo=TipoMensagem.TEXTO_FORMATADO,
        conteudo="Hello",
        remetente=TipoRemetente.CONTATO,
        metadados={},
    )
    print(f"Message created: ID {mensagem.id}")

    # 2. Test Metadata Saving (AttendanceOrchestrator)
    orchestrator = AttendanceOrchestrator(
        message_analyzer=MessageAnalyzer(),
        structure_manager=AttendanceStructureManager(),
        rules_engine=BotRulesEngine(),
    )

    # Simulate envelope list
    env_list = [
        {
            "apikey": api_key,
            "instance": instance_name,
            "instance_id": "some_uuid",
            "evolution": {"instance_db_id": instance.id},
        }
    ]

    print("Saving evolution metadata...")
    orchestrator._save_evolution_metadata(
        atendimento, env_list, message=mensagem
    )

    mensagem.refresh_from_db()
    print(f"Message Metadata: {mensagem.metadados}")

    # Verify Metadata
    evolution_meta = mensagem.metadados.get("evolution", {})
    if "api_key" in evolution_meta and evolution_meta["api_key"] == api_key:
        print("SUCCESS: api_key found in metadata.")
    else:
        print(
            f"FAILURE: api_key not found or incorrect in metadata. Found: {evolution_meta}"
        )

    if (
        "instance_id" not in evolution_meta
        and "instance_name" not in evolution_meta
        and "instance_db_id" not in evolution_meta
    ):
        print("SUCCESS: Unused fields removed from metadata.")
    else:
        print(
            f"FAILURE: Unused fields still present in metadata. Found: {evolution_meta}"
        )

    # 3. Test Signal Behavior (Evolution Instance Retrieval)
    print("\nTesting Signal Behavior...")

    # Mock EvolutionWhatsAppService to avoid actual network call
    with patch(
        "smart_core_assistant_painel.app.evolution_sync.signals.EvolutionWhatsAppService"
    ) as MockService:
        mock_instance = MockService.return_value

        # Trigger signal by saving a bot response
        mensagem.resposta_bot = "Bot Response"
        mensagem.save()

        # Verify if signal was triggered and found the correct instance
        # The signal calls EvolutionWhatsAppService().send_message(...)
        # We check if it was called with the correct api_key and instance name

        if mock_instance.send_message.called:
            call_args = mock_instance.send_message.call_args[1]
            print(f"Signal called send_message with: {call_args}")

            if call_args.get("api_key") == api_key:
                print("SUCCESS: Signal used the correct API Key.")
            else:
                print(
                    f"FAILURE: Signal used incorrect API Key. Expected {api_key}, got {call_args.get('api_key')}"
                )

            if (
                call_args.get("instance") == instance_name
            ):  # Note: instance name might be retrieved from DB using api_key
                print("SUCCESS: Signal resolved the correct Instance Name.")
            else:
                print(
                    f"FAILURE: Signal resolved incorrect Instance Name. Expected {instance_name}, got {call_args.get('instance')}"
                )

        else:
            print("FAILURE: Signal did not call send_message.")


if __name__ == "__main__":
    try:
        test_evolution_metadata_optimization()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()

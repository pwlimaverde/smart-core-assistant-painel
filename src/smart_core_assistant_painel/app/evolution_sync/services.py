from typing import Optional

from .models import EvolutionContact
from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_whatsapp_service import (
    EvolutionWhatsAppService,
)


def send_message_by_contact_id(contact_id: int, text: str) -> None:
    evo_contact: Optional[EvolutionContact] = (
        EvolutionContact.objects.select_related("instance")
        .filter(contact_id=contact_id, active=True)
        .first()
    )
    if not evo_contact:
        raise ValueError("contact mapping not found")
    inst = evo_contact.instance
    svc = EvolutionWhatsAppService()
    number = ""
    if evo_contact.addressing_mode == "pn" and evo_contact.jid:
        number = evo_contact.jid.split("@")[0]
    elif inst.phone_number:
        number = inst.phone_number
    svc.send_message(
        instance=str(inst.name or inst.instance_id or ""),
        api_key=inst.api_key,
        number=number,
        text=text,
    )
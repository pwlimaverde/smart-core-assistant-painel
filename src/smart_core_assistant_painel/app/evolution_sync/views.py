import json
from typing import Any, Dict

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger

from smart_core_assistant_painel.app.ui.clientes.models import Contato

from .models import EvolutionContact, EvolutionInstance
from .normalizers import normalize_evolution_webhook
from .utils import sched_response_contact, set_buffer_contact


@csrf_exempt
def webhook(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"detail": "method not allowed"}, status=405)
    try:
        payload: Dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "invalid json"}, status=400)

    envelope: Dict[str, Any] = normalize_evolution_webhook(payload)

    inst_name: str | None = envelope.get("instance")
    inst_id: str | None = envelope.get("instance_id")
    api_key: str = str(envelope.get("apikey") or "")
    server_url: str | None = payload.get("server_url")

    instance, _ = EvolutionInstance.objects.get_or_create(
        instance_id=inst_id or "",
        defaults={
            "name": str(inst_name or inst_id or ""),
            "api_key": api_key,
            "server_url": server_url,
        },
    )

    contact_info: Dict[str, Any] = envelope.get("contact") or {}
    jid: str | None = contact_info.get("jid")
    lid: str | None = contact_info.get("lid")
    addressing_mode: str | None = contact_info.get("addressing_mode")

    qs = EvolutionContact.objects.filter(instance=instance)
    if jid:
        qs = qs.filter(jid=jid)
    if not qs.exists() and lid:
        qs = EvolutionContact.objects.filter(instance=instance, lid=lid)

    evo_contact = qs.first()
    if evo_contact is None:
        evo_contact = EvolutionContact.objects.create(
            instance=instance,
            jid=jid,
            lid=lid,
            addressing_mode=addressing_mode,
        )

    if not evo_contact.contact_id:
        profile = envelope.get("profile") or {}
        push_name = profile.get("push_name")
        phone = (envelope.get("contact") or {}).get("phone") or None
        contato: Contato | None = None
        if phone:
            contato, _ = Contato.objects.get_or_create(
                telefone=str(phone),
                defaults={
                    "nome_contato": str(push_name or ""),
                    "nome_perfil_whatsapp": str(push_name or ""),
                    "ativo": True,
                    "metadados": {},
                },
            )
        else:
            contato = Contato.objects.create(
                nome_contato=str(push_name or ""),
                nome_perfil_whatsapp=str(push_name or ""),
                ativo=True,
                metadados={},
            )
        evo_contact.contact = contato
        evo_contact.save(update_fields=["contact"])

    if evo_contact.contact_id:
        phone_env = (envelope.get("contact") or {}).get("phone")
        if phone_env:
            contato = evo_contact.contact
            if contato and not getattr(contato, "telefone", None):
                contato.telefone = str(phone_env)
                contato.save(update_fields=["telefone"])
        logger.info(
            f"Contact %s scheduled to response {evo_contact.contact_id}-{envelope}"
        )
        set_buffer_contact(evo_contact.contact_id, envelope)
        sched_payload: Dict[str, Any] = {
            "contact_id": evo_contact.contact_id,
            "api_key": envelope.get("apikey"),
            "message": envelope.get("message"),
        }
        sched_response_contact(sched_payload)
        return JsonResponse({"status": "ok"}, status=200)

    return JsonResponse({"status": "accepted"}, status=202)

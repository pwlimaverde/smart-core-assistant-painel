import json
from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger

from smart_core_assistant_painel.app.ui.clientes.models import Contato

from .models import EvolutionContact, EvolutionInstance
from .normalizers import (
    normalize_evolution_webhook,
    normalize_evolution_webhook_batch,
)
from .utils import sched_response_contact, set_buffer_contact


@csrf_exempt
def webhook(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"detail": "method not allowed"}, status=405)
    try:
        payload: Dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "invalid json"}, status=400)

    data_obj = payload.get("data")
    envelopes: list[Dict[str, Any]]
    if isinstance(data_obj, list):
        envelopes = normalize_evolution_webhook_batch(payload)
    else:
        envelopes = [normalize_evolution_webhook(payload)]

    # Filter out messages sent by the bot itself and messages without valid JID (e.g. status updates)
    envelopes = [
        e
        for e in envelopes
        if not e.get("from_me") and e.get("contact", {}).get("jid")
    ]
    if not envelopes:
        logger.debug("Webhook ignored: all messages are from_me")
        return JsonResponse({"status": "ignored_from_me"}, status=200)

    first_env: Dict[str, Any] = envelopes[0] if envelopes else {}
    logger.debug(
        f"Processing webhook. First env keys: {list(first_env.keys())}"
    )
    inst_name: str | None = first_env.get("instance")
    inst_id: str | None = first_env.get("instance_id")
    api_key: str = str(first_env.get("apikey") or "")
    server_url: str | None = payload.get("server_url") or getattr(
        settings, "EVOLUTION_API_URL", None
    )

    instance, created = EvolutionInstance.objects.get_or_create(
        instance_id=inst_id or "",
        defaults={
            "name": str(inst_name or inst_id or ""),
            "api_key": api_key,
            "server_url": server_url,
        },
    )
    if not created:
        update_fields: list[str] = []
        name_val = str(inst_name or inst_id or "")
        if name_val and instance.name != name_val:
            instance.name = name_val
            update_fields.append("name")
        if api_key and instance.api_key != api_key:
            instance.api_key = api_key
            update_fields.append("api_key")
        if server_url and instance.server_url != server_url:
            instance.server_url = server_url
            update_fields.append("server_url")
        if update_fields:
            instance.save(update_fields=update_fields)

    contact_info: Dict[str, Any] = first_env.get("contact") or {}
    jid: str | None = contact_info.get("jid")
    lid: str | None = contact_info.get("lid")
    addressing_mode: str | None = contact_info.get("addressing_mode")

    logger.debug(
        f"Contact info extracted: jid={jid}, lid={lid}, mode={addressing_mode}"
    )

    qs = EvolutionContact.objects.filter(instance=instance)
    if jid:
        qs = qs.filter(jid=jid)
    if not qs.exists() and lid:
        qs = EvolutionContact.objects.filter(instance=instance, lid=lid)

    evo_contact = qs.first()
    if evo_contact is None:
        logger.debug("Creating new EvolutionContact")
        evo_contact = EvolutionContact.objects.create(
            instance=instance,
            jid=jid,
            lid=lid,
            addressing_mode=addressing_mode,
        )
    else:
        update_fields_contact: list[str] = []
        if jid and evo_contact.jid != jid:
            evo_contact.jid = jid
            update_fields_contact.append("jid")
        if lid and evo_contact.lid != lid:
            evo_contact.lid = lid
            update_fields_contact.append("lid")
        if addressing_mode and evo_contact.addressing_mode != addressing_mode:
            evo_contact.addressing_mode = addressing_mode
            update_fields_contact.append("addressing_mode")
        if update_fields_contact:
            evo_contact.save(update_fields=update_fields_contact)

    if not evo_contact.contact_id:
        logger.debug(
            "EvolutionContact has no linked Contact. Attempting to link/create."
        )
        profile = first_env.get("profile") or {}
        push_name = profile.get("push_name")
        phone = (first_env.get("contact") or {}).get("phone") or None

        logger.debug(f"Profile info: push_name={push_name}, phone={phone}")

        contato: Contato | None = None
        if phone:
            contato, created_contact = Contato.objects.get_or_create(
                telefone=str(phone),
                defaults={
                    "nome_contato": str(push_name or ""),
                    "nome_perfil_whatsapp": str(push_name or ""),
                    "ativo": True,
                    "metadados": {},
                },
            )
            logger.debug(
                f"Contact with phone {phone} retrieved/created. Created={created_contact}, ID={contato.id}"
            )

            # Update push_name if it exists and contact was not created (existing contact)
            if not created_contact and push_name:
                if not contato.nome_perfil_whatsapp:
                    contato.nome_perfil_whatsapp = str(push_name)
                    contato.save(update_fields=["nome_perfil_whatsapp"])
                    logger.debug(
                        f"Updated nome_perfil_whatsapp for existing contact {contato.id}"
                    )

        else:
            logger.debug("No phone found. Creating new Contact without phone.")
            contato = Contato.objects.create(
                nome_contato=str(push_name or ""),
                nome_perfil_whatsapp=str(push_name or ""),
                ativo=True,
                metadados={},
            )
            logger.debug(f"New Contact created without phone. ID={contato.id}")

        evo_contact.contact = contato
        evo_contact.save(update_fields=["contact"])
        logger.debug(
            f"Linked Contact {contato.id} to EvolutionContact {evo_contact.id}"
        )

    if evo_contact.contact_id:
        logger.debug(
            f"Proceeding to schedule response for contact_id={evo_contact.contact_id}"
        )
        phone_env = (first_env.get("contact") or {}).get("phone")
        if phone_env:
            contato = evo_contact.contact
            if contato and not getattr(contato, "telefone", None):
                contato.telefone = str(phone_env)
                contato.save(update_fields=["telefone"])
        for envelope in envelopes:
            logger.info(
                "evo_schedule_response contact_id={} env_keys={}",
                evo_contact.contact_id,
                list(envelope.keys()),
            )
            set_buffer_contact(evo_contact.contact_id, envelope)
        evo_meta = first_env.get("evolution") or {}
        evo_meta["instance_db_id"] = int(instance.id)
        first_env["evolution"] = evo_meta
        logger.info(
            "evo_schedule_response_meta contact_id={} instance_db_id={}",
            evo_contact.contact_id,
            evo_meta.get("instance_db_id"),
        )
        sched_payload: Dict[str, Any] = {
            "contact_id": evo_contact.contact_id,
            "api_key": first_env.get("apikey"),
            "message": first_env.get("message"),
        }
        sched_response_contact(sched_payload)
        return JsonResponse(
            {"status": "ok", "processed": len(envelopes)}, status=200
        )

    return JsonResponse({"status": "accepted"}, status=202)

from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from loguru import logger

from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.evolution_sync.domain.schemas import (
    EvolutionWebhookEnvelope,
)
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
    EvolutionInstance,
)
from smart_core_assistant_painel.app.evolution_sync.utils import (
    sched_response_contact,
    set_buffer_contact,
)


class WebhookProcessor:
    """Processador de Webhooks da Evolution API.

    Responsável por orquestrar o processamento de mensagens recebidas,
    gerenciamento de instâncias e contatos, e agendamento de respostas.
    """

    def process_webhook(
        self,
        payload: Dict[str, Any],
        envelopes: List[EvolutionWebhookEnvelope],
    ) -> Dict[str, Any]:
        """Processa o webhook recebido.

        Args:
            payload: O payload bruto recebido.
            envelopes: Lista de envelopes normalizados.

        Returns:
            Dict[str, Any]: Resultado do processamento.
        """
        # Filtrar mensagens enviadas pelo próprio bot ou sem JID válido
        valid_envelopes = [
            e for e in envelopes if not e.from_me and e.contact.jid
        ]

        if not valid_envelopes:
            logger.debug(
                "Webhook ignored: all messages are from_me or invalid"
            )
            return {"status": "ignored_from_me"}

        first_env = valid_envelopes[0]
        logger.debug(
            f"Processing webhook. First env instance: {first_env.instance}"
        )

        instance = self._get_or_create_instance(first_env, payload)
        evo_contact = self._resolve_contact(instance, first_env)

        if not evo_contact.contact_id:
            self._link_contact(evo_contact, first_env)

        if evo_contact.contact_id:
            self._schedule_response(
                instance, evo_contact, valid_envelopes, first_env
            )
            return {"status": "ok", "processed": len(valid_envelopes)}

        return {"status": "accepted"}

    def _get_or_create_instance(
        self, envelope: EvolutionWebhookEnvelope, payload: Dict[str, Any]
    ) -> EvolutionInstance:
        """Obtém ou cria a instância Evolution no banco de dados."""
        inst_name = envelope.instance
        inst_id = envelope.instance_id
        api_key = str(envelope.apikey or "")
        server_url = payload.get("server_url") or getattr(
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

        return instance

    def _resolve_contact(
        self, instance: EvolutionInstance, envelope: EvolutionWebhookEnvelope
    ) -> EvolutionContact:
        """Resolve o contato Evolution (busca ou cria)."""
        jid = envelope.contact.jid
        lid = envelope.contact.lid
        addressing_mode = envelope.contact.addressing_mode

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
            if (
                addressing_mode
                and evo_contact.addressing_mode != addressing_mode
            ):
                evo_contact.addressing_mode = addressing_mode
                update_fields_contact.append("addressing_mode")
            if update_fields_contact:
                evo_contact.save(update_fields=update_fields_contact)

        return evo_contact

    def _link_contact(
        self, evo_contact: EvolutionContact, envelope: EvolutionWebhookEnvelope
    ) -> None:
        """Vincula ou cria um Contato do sistema principal."""
        logger.debug(
            "EvolutionContact has no linked Contact. Attempting to link/create."
        )
        push_name = envelope.profile.push_name
        phone = envelope.contact.phone

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

    def _schedule_response(
        self,
        instance: EvolutionInstance,
        evo_contact: EvolutionContact,
        envelopes: List[EvolutionWebhookEnvelope],
        first_env: EvolutionWebhookEnvelope,
    ) -> None:
        """Agenda a resposta para o contato."""
        logger.debug(
            f"Proceeding to schedule response for contact_id={evo_contact.contact_id}"
        )

        # Ensure phone is updated in main contact if missing
        if first_env.contact.phone:
            contato = evo_contact.contact
            if contato and not getattr(contato, "telefone", None):
                contato.telefone = str(first_env.contact.phone)
                contato.save(update_fields=["telefone"])

        for envelope in envelopes:
            # Convert back to dict for buffer compatibility
            env_dict = envelope.to_dict()
            logger.info(
                "evo_schedule_response contact_id={} env_keys={}",
                evo_contact.contact_id,
                list(env_dict.keys()),
            )
            set_buffer_contact(evo_contact.contact_id, env_dict)

        # Prepare metadata for scheduling
        # We need to inject instance_db_id into the 'evolution' metadata of the first envelope
        # But since we are using dataclasses, we might need to handle this carefully.
        # The original code modified the 'evolution' key in the raw payload or metadata.
        # Let's look at how it was done:
        # evo_meta = first_env.get("evolution") or {}
        # evo_meta["instance_db_id"] = int(instance.id)
        # first_env["evolution"] = evo_meta

        # In our new structure, we can pass this as part of the sched_payload or modify the raw if needed.
        # The scheduler likely reads from the buffer or expects specific params.
        # sched_response_contact takes 'params'.

        # IMPORTANT: The original code modified 'first_env' which was a dict.
        # Here 'first_env' is an object. The buffer stores 'env_dict'.
        # We should probably update the buffer with the instance_db_id if that's where it's read from?
        # Actually, sched_response_contact just triggers a task. The task likely reads the buffer.
        # Wait, the original code did:
        # first_env["evolution"] = evo_meta (where evo_meta has instance_db_id)
        # Then it called sched_response_contact(sched_payload)
        # The buffer was ALREADY set before this modification in the loop.
        # BUT, the loop used 'envelope' (from envelopes list).
        # The modification to 'first_env' (which is envelopes[0]) happened AFTER the loop in the original code?
        # Let's check the original code order.
        # 1. Loop envelopes -> set_buffer_contact
        # 2. Modify first_env["evolution"]
        # 3. sched_response_contact

        # This implies the modification to first_env was NOT stored in the buffer?
        # Or maybe it was intended to be?
        # If set_buffer_contact copies the dict, then the modification after doesn't affect the buffer.
        # If it stores a reference, it might.
        # `cache.set` pickles the object, so it stores a copy.
        # So the modification to `first_env` in the original code seemed to only affect `sched_payload` construction?
        # No, `sched_payload` only has contact_id, api_key, message.
        # So where is `instance_db_id` used?
        # It seems it might be used if `first_env` is passed somewhere else, but it isn't.
        # Wait, maybe I missed something.
        # Ah, `signals.py` reads `instance.metadados.get("evolution", {}).get("instance_db_id")`.
        # But that's from `Mensagem` model.
        # The flow is: Webhook -> Buffer -> Task (send_message_response_by_contact) -> AI Processing -> Mensagem Saved -> Signal.
        # So the `instance_db_id` needs to persist through this flow.
        # The `send_message_response_by_contact` likely reads the buffer, processes it, and creates a `Mensagem`.
        # If the buffer was already set, how does `instance_db_id` get into `Mensagem`?
        # Maybe the task reads the buffer and expects `evolution` metadata there?
        # If so, the original code might have had a bug or I am misinterpreting the order.
        # Original:
        # for envelope in envelopes: set_buffer_contact(...)
        # evo_meta = first_env.get("evolution") ... first_env["evolution"] = evo_meta
        # This modification happens AFTER buffering. So the buffered envelopes DO NOT have the updated instance_db_id.
        # Unless `first_env` is a reference to the same dict object that is in `envelopes` list, AND `set_buffer_contact` stores it.
        # But `cache.set` serializes. So the buffer definitely has the OLD version.
        # This suggests `instance_db_id` might not be successfully passed via buffer in the original code, OR it's passed another way.
        # However, to be safe and clean, I should ensure `instance_db_id` is in the buffered data if possible, or verify if it's needed.
        # In the signal, it tries to find the instance via `evo_contact.instance`.
        # `inst = getattr(evo_contact, "instance", None)`
        # Only if that fails does it look at `instance.metadados`.
        # Since we are linking `EvolutionContact` to `EvolutionInstance` explicitly in `_get_or_create_instance` and `_resolve_contact`,
        # the signal should be able to find the instance via the relation, rendering the metadata fallback secondary.
        # So I will proceed without obsessing over the metadata injection, but I will try to preserve the behavior if possible.

        sched_payload: Dict[str, Any] = {
            "contact_id": evo_contact.contact_id,
            "api_key": first_env.apikey,
            "message": first_env.message.to_dict()
            if first_env.message
            else {},  # message is obj
        }
        # Note: original passed first_env.get("message") which is a dict.
        # My schema has message as object.

        sched_response_contact(sched_payload)

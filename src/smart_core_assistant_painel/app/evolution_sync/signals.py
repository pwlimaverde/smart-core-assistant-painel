from typing import Any, Optional

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.ui.atendimentos.models import Mensagem
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
    EvolutionInstance,
)
from smart_core_assistant_painel.app.evolution_sync.services.evolution_api import (
    EvolutionWhatsAppService,
)


@receiver(post_save, sender=Mensagem)
def _on_message_saved(
    sender: type[Mensagem], instance: Mensagem, created: bool, **kwargs: Any
) -> None:
    """Signal handler disparado quando uma Mensagem é salva.

    Verifica se a mensagem é uma resposta do bot que precisa ser enviada
    via WhatsApp e, se for, dispara o envio.

    Args:
        sender: A classe do modelo que enviou o sinal.
        instance: A instância da mensagem salva.
        created: Booleano indicando se foi criado (True) ou atualizado (False).
        **kwargs: Argumentos adicionais.
    """
    try:
        logger.info(
            "signal_message_saved id=%s created=%s responded=%s",
            instance.id,
            created,
            instance.respondida,
        )
        if not instance.respondida:
            logger.info("signal_skip_not_responded id=%s", instance.id)
            return
        if not instance.resposta_bot:
            logger.info("signal_skip_empty_bot_response id=%s", instance.id)
            return
        if not getattr(instance, "atendimento", None):
            logger.error("signal_skip_no_atendimento id=%s", instance.id)
            return
        if instance.atendimento.canal != "whatsapp":
            logger.info(
                "signal_skip_non_whatsapp id=%s canal=%s",
                instance.id,
                instance.atendimento.canal,
            )
            return

        text: str = str(instance.resposta_bot).strip()
        if not text:
            return

        contato = getattr(instance.atendimento, "contato", None)
        number: str = str(getattr(contato, "telefone", "") or "").strip()
        evo_contact: Optional[EvolutionContact] = (
            EvolutionContact.objects.select_related("instance", "contact")
            .filter(contact_id=getattr(contato, "id", None), active=True)
            .order_by("-updated_at")
            .first()
        )
        logger.info(
            "signal_contact number=%s contact_id=%s evo_contact=%s",
            number,
            getattr(contato, "id", None),
            bool(evo_contact),
        )
        if (
            not number
            and evo_contact
            and evo_contact.jid
            and evo_contact.jid.endswith("@s.whatsapp.net")
        ):
            number = evo_contact.jid.split("@")[0]
        if not number:
            logger.error(
                "signal_fail_number_unavailable msg_id=%s", instance.id
            )
            return

        inst: Optional[EvolutionInstance] = getattr(
            evo_contact, "instance", None
        )
        if not inst:
            meta = dict(getattr(instance, "metadados", {}) or {})
            evo = dict(meta.get("evolution", {}) or {})
            inst_db_id = evo.get("instance_db_id")
            if inst_db_id:
                inst = EvolutionInstance.objects.filter(
                    id=int(inst_db_id), active=True
                ).first()
        logger.info(
            "signal_instance_resolved inst=%s meta_id=%s",
            getattr(inst, "id", None),
            evo.get("instance_db_id") if "evo" in locals() else None,
        )
        if not inst:
            logger.error(
                "signal_fail_instance_unavailable contact_id=%s",
                getattr(contato, "id", None),
            )
            return

        instance_name: str = str(
            (inst.name or inst.phone_number or inst.instance_id or "")
        )
        api_key: str = str(inst.api_key or "")
        base_url: str = str(getattr(settings, "EVOLUTION_API_URL", "") or "")
        logger.info(
            "signal_send_check instance=%s base_url=%s api_key_set=%s",
            instance_name,
            base_url,
            bool(api_key),
        )
        if not instance_name or not api_key or not base_url:
            logger.error(
                "signal_fail_missing_data instance=%s base_url=%s api_key_set=%s",
                instance_name,
                base_url,
                bool(api_key),
            )
            return

        logger.info(
            "signal_send_start msg_id=%s number=%s text_len=%s",
            instance.id,
            number,
            len(text),
        )
        EvolutionWhatsAppService().send_message(
            instance=instance_name,
            api_key=api_key,
            number=number,
            text=text,
            base_url=base_url,
        )
        logger.info("signal_send_success msg_id=%s", instance.id)
    except Exception as e:
        logger.exception("signal_exception msg_id=%s err=%s", instance.id, e)

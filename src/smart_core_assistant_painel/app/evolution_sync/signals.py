from typing import Any, Optional

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
    EvolutionInstance,
)
from smart_core_assistant_painel.app.evolution_sync.services.evolution_api import (
    EvolutionWhatsAppService,
)
from smart_core_assistant_painel.app.tenants.middleware import get_current_tenant
from smart_core_assistant_painel.app.tenants.models import TenantEvolution
from smart_core_assistant_painel.app.ui.atendimentos.models import Mensagem


@receiver(pre_save, sender=Mensagem)
def _on_message_pre_save(
    sender: type[Mensagem], instance: Mensagem, **kwargs: Any
) -> None:
    """Verifica se o campo resposta_bot foi alterado."""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.resposta_bot != instance.resposta_bot:
                instance._resposta_bot_changed = True
        except sender.DoesNotExist:
            pass


def _resolve_evolution_base_url(inst: EvolutionInstance) -> str:
    """Resolve URL da Evolution API com base na configuração do tenant."""
    tenant_id = getattr(inst, "tenant_id", None)
    if tenant_id:
        tenant_cfg = TenantEvolution.objects.filter(
            tenant_id=tenant_id
        ).first()
        if tenant_cfg and tenant_cfg.server_url:
            return str(tenant_cfg.server_url).rstrip("/")

    tenant = get_current_tenant()
    if tenant:
        tenant_cfg = TenantEvolution.objects.filter(tenant=tenant).first()
        if tenant_cfg and tenant_cfg.server_url:
            return str(tenant_cfg.server_url).rstrip("/")

    return ""


@receiver(post_save, sender=Mensagem)
def _on_message_saved(
    sender: type[Mensagem], instance: Mensagem, created: bool, **kwargs: Any
) -> None:
    """Signal handler disparado quando uma Mensagem é salva.

    Verifica se a mensagem é uma resposta do bot que precisa ser enviada
    via WhatsApp. Após envio bem-sucedido, marca a mensagem como respondida.

    Args:
        sender: A classe do modelo que enviou o sinal.
        instance: A instância da mensagem salva.
        created: Booleano indicando se foi criado (True) ou atualizado (False).
        **kwargs: Argumentos adicionais.
    """
    try:
        # Verifica se deve enviar a mensagem
        should_send = False
        if created and instance.resposta_bot:
            should_send = True
        elif (
            getattr(instance, "_resposta_bot_changed", False)
            and instance.resposta_bot
        ):
            should_send = True

        if not should_send:
            return

        # Se já foi respondida (enviada), não enviar novamente
        # Isso evita loop quando salvamos respondida=True
        if instance.respondida:
            return

        if not getattr(instance, "atendimento", None):
            return

        # Canal está armazenado em contexto_conversa (JSONField)
        contexto = getattr(instance.atendimento, "contexto_conversa", {}) or {}
        canal = contexto.get("canal", "")
        if canal != "whatsapp":
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

        if (
            not number
            and evo_contact
            and evo_contact.jid
            and evo_contact.jid.endswith("@s.whatsapp.net")
        ):
            number = evo_contact.jid.split("@")[0]
        if not number:
            return

        # Tenta obter instância dos metadados da mensagem PRIMEIRO
        # Isso garante que respondemos pela mesma instância que recebeu a mensagem
        inst: Optional[EvolutionInstance] = None

        meta = dict(getattr(instance, "metadados", {}) or {})
        evo = dict(meta.get("evolution", {}) or {})
        api_key_meta = evo.get("api_key")

        if api_key_meta:
            inst = EvolutionInstance.objects.filter(
                api_key=str(api_key_meta), active=True
            ).first()

        # Se não encontrou nos metadados, usa a do contato (fallback)
        if not inst:
            inst = getattr(evo_contact, "instance", None)

        if not inst:
            return

        instance_name: str = str(
            (inst.name or inst.phone_number or inst.instance_id or "")
        )
        api_key: str = str(inst.api_key or "")
        base_url: str = _resolve_evolution_base_url(inst)

        if not instance_name or not api_key or not base_url:
            logger.warning(
                "Envio Evolution ignorado por configuração incompleta: "
                f"instance={instance_name!r}, api_key={'set' if api_key else 'empty'}, "
                f"base_url={base_url!r}"
            )
            return

        logger.info(
            f"Enviando resposta da mensagem {instance.id} via Evolution API "
            f"para {number}"
        )

        # Tenta enviar a mensagem
        try:
            EvolutionWhatsAppService().send_message(
                instance=instance_name,
                api_key=api_key,
                number=number,
                text=text,
                base_url=base_url,
            )

            # Marca como respondida APENAS após sucesso do envio
            instance.respondida = True
            instance.save(update_fields=["respondida"])

            logger.info(
                f"Mensagem {instance.id} enviada com sucesso e marcada como "
                f"respondida"
            )

        except Exception as e:
            logger.error(
                f"Erro ao enviar mensagem {instance.id} via Evolution API: {e}"
            )
            # NÃO marca como respondida em caso de erro
            raise

    except Exception as e:
        logger.error(
            f"Erro no signal _on_message_saved para mensagem {instance.id}: "
            f"{e}"
        )
        # Em caso de erro, não propaga para não bloquear o save
        ...

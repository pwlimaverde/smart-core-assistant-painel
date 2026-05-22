# pyright: reportAttributeAccessIssue=false, reportUnusedFunction=false, reportUnknownArgumentType=false, reportCallIssue=false
"""Sinais do app Chat Evolution.

Observa mudanças em Mensagem e publica eventos SSE voltados ao chat.
"""

from __future__ import annotations

from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.atendimento_unificado.services.realtime_publisher import (
    publish_event,
)
from smart_core_assistant_painel.app.atendimentos.models import (
    Mensagem,
    TipoRemetente,
)


@receiver(post_save, sender=Mensagem)
def _on_mensagem_bot_extrair_campos(
    sender: Any, instance: Mensagem, created: bool, **kwargs: Any
) -> None:
    """Dispara extração de campos personalizados após resposta do bot."""
    if not created:
        return
    try:
        if instance.remetente != TipoRemetente.BOT.value:
            return

        from smart_core_assistant_painel.app.tenants.tenant_context import (
            get_current_tenant_slug,
        )

        tenant_slug = get_current_tenant_slug() or ""

        # Importa a task assíncrona do monolito (atendimento_unificado)
        from smart_core_assistant_painel.app.atendimento_unificado.tasks import (
            extract_custom_fields_async,
        )

        extract_custom_fields_async.apply_async(
            kwargs={
                "tenant_slug": tenant_slug,
                "atendimento_id": instance.atendimento_id,
                "mensagem_id": instance.id,
            },
        )
    except Exception as exc:
        logger.warning(
            "Falha ao enfileirar extração de campos para msg {}: {}",
            instance.id,
            exc,
        )


@receiver(post_save, sender=Mensagem)
def _on_mensagem_saved(
    sender: Any, instance: Mensagem, created: bool, **kwargs: Any
) -> None:
    """Publica evento SSE de chat quando uma Mensagem é criada/atualizada."""
    try:
        preview = (instance.conteudo or instance.resposta_bot or "")[:120]
        publish_event(
            "chat.message" if created else "chat.message_updated",
            {
                "atendimento_id": instance.atendimento_id,
                "mensagem_id": instance.id,
                "remetente": instance.remetente,
                "tipo": instance.tipo,
                "preview": preview,
                "respondida": instance.respondida,
                "timestamp": (
                    instance.timestamp.isoformat()
                    if instance.timestamp
                    else None
                ),
            },
        )
    except Exception as exc:
        logger.warning(
            "Falha ao publicar SSE chat.message para msg {}: {}",
            instance.id,
            exc,
        )

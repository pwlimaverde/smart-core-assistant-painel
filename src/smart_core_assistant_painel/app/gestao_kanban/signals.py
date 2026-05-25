# pyright: reportAttributeAccessIssue=false, reportUnusedFunction=false, reportUnknownArgumentType=false, reportCallIssue=false
"""Sinais do app Gestão Kanban.

Observa mudanças em Atendimento e MovimentoFluxo e publica eventos SSE voltados ao Kanban.
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
    Atendimento,
    MovimentoFluxo,
)


@receiver(post_save, sender=MovimentoFluxo)
def _on_movimento_fluxo_saved(
    sender: Any, instance: MovimentoFluxo, created: bool, **kwargs: Any
) -> None:
    """Publica `kanban.board_moved` quando um MovimentoFluxo é criado."""
    if not created:
        return
    try:
        publish_event(
            "kanban.board_moved",
            {
                "atendimento_id": instance.atendimento_id,
                "etapa_origem_id": instance.etapa_origem_id,
                "etapa_destino_id": instance.etapa_destino_id,
                "automatico": instance.automatico,
            },
        )
    except Exception as exc:
        logger.warning(
            "Falha ao publicar SSE kanban.board_moved para movimento {}: {}",
            instance.id,
            exc,
        )


@receiver(post_save, sender=Atendimento)
def _on_atendimento_saved(
    sender: Any, instance: Atendimento, created: bool, **kwargs: Any
) -> None:
    """Publica evento SSE de Kanban quando um Atendimento é criado/atualizado."""
    event = (
        "kanban.atendimento_created"
        if created
        else "kanban.atendimento_updated"
    )
    try:
        publish_event(
            event,
            {
                "atendimento_id": instance.id,
                "status": instance.status,
                "prioridade": instance.prioridade,
                "etapa_id": instance.etapa_atual_id,
                "fluxo_id": instance.fluxo_atendimento_id,
                "atendente_id": instance.atendente_humano_id,
            },
        )
    except Exception as exc:
        logger.warning(
            "Falha ao publicar SSE {} para atendimento {}: {}",
            event,
            instance.id,
            exc,
        )

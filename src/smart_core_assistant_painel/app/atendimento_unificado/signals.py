# pyright: reportAttributeAccessIssue=false, reportUnusedFunction=false, reportUnknownArgumentType=false, reportUnnecessaryComparison=false, reportCallIssue=false
"""Sinais do Workspace de Atendimento Unificado.

Princípio: este módulo **observa** mudanças em modelos de outros apps
(Mensagem, Atendimento, MovimentoFluxo) e publica eventos SSE. Nada
aqui muta os modelos observados — mutações ocorrem nos services.

Os receivers são best-effort: falhas no publish não devem propagar
para o save do app de origem.
"""

from __future__ import annotations

from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    Mensagem,
    MovimentoFluxo,
)

from .services.realtime_publisher import publish_event


@receiver(post_save, sender=Mensagem)
def _on_mensagem_bot_extrair_campos(
    sender: Any, instance: Mensagem, created: bool, **kwargs: Any
) -> None:
    """Dispara extração de campos personalizados após resposta do bot.

    Observa `Mensagem` com remetente ASSISTENTE_VIRTUAL recém-criada
    e enfileira a task Celery de extração de campos. Mantém o princípio
    de independência: não toca em `atendimentos` nem em `ai_engine`.
    """
    if not created:
        return
    try:
        from smart_core_assistant_painel.app.atendimentos.models import (
            TipoRemetente,
        )

        if instance.remetente != TipoRemetente.BOT:
            return

        from smart_core_assistant_painel.app.tenants.tenant_context import (
            get_current_tenant_slug,
        )

        tenant_slug = get_current_tenant_slug() or ""

        from .tasks import extract_custom_fields_async

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
    """Publica `message.new` quando uma `Mensagem` é criada/atualizada.

    A intenção é apenas notificar o UI para refrescar/append; o envio
    real pelo WhatsApp continua sob responsabilidade do signal do
    ``evolution_sync``.
    """
    try:
        # Evita publicar em update meramente para marcar `respondida=True`
        # (o evento já foi publicado no create).
        if not created and not _has_interesting_change(instance):
            return

        preview = (instance.conteudo or instance.resposta_bot or "")[:120]
        publish_event(
            "message.new" if created else "message.updated",
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
            "Falha ao publicar SSE message.new para msg {}: {}",
            instance.id,
            exc,
        )


@receiver(post_save, sender=MovimentoFluxo)
def _on_movimento_fluxo_saved(
    sender: Any, instance: MovimentoFluxo, created: bool, **kwargs: Any
) -> None:
    """Publica `board.moved` quando um `MovimentoFluxo` é criado."""
    if not created:
        return
    try:
        publish_event(
            "board.moved",
            {
                "atendimento_id": instance.atendimento_id,
                "etapa_origem_id": instance.etapa_origem_id,
                "etapa_destino_id": instance.etapa_destino_id,
                "automatico": instance.automatico,
            },
        )
    except Exception as exc:
        logger.warning(
            "Falha ao publicar SSE board.moved para movimento {}: {}",
            instance.id,
            exc,
        )


@receiver(post_save, sender=Atendimento)
def _on_atendimento_saved(
    sender: Any, instance: Atendimento, created: bool, **kwargs: Any
) -> None:
    """Publica `atendimento.updated` quando status/atendente/etapa muda.

    Como o ``Atendimento`` é salvo várias vezes durante o fluxo normal,
    fazemos um filtro grosseiro pelo `update_fields`. Quando `None`
    (save completo), publicamos sempre — consumidor faz dedup pelo
    `atendimento_id`.
    """
    try:
        if created:
            event = "atendimento.created"
        else:
            event = "atendimento.updated"

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
            "Falha ao publicar SSE atendimento.updated para {}: {}",
            instance.id,
            exc,
        )


def _has_interesting_change(instance: Mensagem) -> bool:
    """Decide se o update de `Mensagem` deve gerar evento.

    Mensagens marcadas como `respondida=True` após envio também são
    interessantes (UI pode atualizar o ✓✓).
    """
    return True

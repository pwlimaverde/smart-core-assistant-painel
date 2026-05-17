"""Publica eventos do Workspace no Redis pub/sub (consumido por SSE).

Isolamento multi-tenant: canal nomeado por tenant (`sse:{slug}:events`).
Cada evento é serializado como uma linha JSON e contém:
    {
        "type": <event_name>,
        "tenant_slug": <slug>,
        "data": {...}
    }

Falhas são logadas mas nunca propagam: a UI deve degradar suavemente
(usuário pode dar refresh para sincronizar).
"""

from __future__ import annotations

import json
from typing import Any, Optional

from django.conf import settings
from loguru import logger

from smart_core_assistant_painel.app.tenants.tenant_context import (
    get_current_tenant_slug,
)

from ..feature_flags import get_sse_channel

_redis_client = None


def _build_redis_url() -> str:
    """Reusa o broker do Celery (DB 0) para pub/sub."""
    try:
        url = getattr(settings, "CELERY_BROKER_URL", None)
        if url:
            return str(url)
    except Exception:
        pass
    return "redis://localhost:6379/0"


def _get_redis():
    """Retorna cliente Redis síncrono lazy-init."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis  # type: ignore[import-not-found]

            _redis_client = redis.from_url(_build_redis_url())
        except Exception as exc:
            logger.warning(
                "Não foi possível inicializar cliente Redis para SSE: {}",
                exc,
            )
            _redis_client = None
    return _redis_client


def publish_event(
    event_type: str,
    data: dict[str, Any],
    tenant_slug: Optional[str] = None,
) -> bool:
    """Publica evento para SSE no canal do tenant.

    Args:
        event_type: Nome do evento (`message.new`, `board.moved`, etc.).
        data: Payload do evento (deve ser JSON-serializável).
        tenant_slug: Slug do tenant. Se ``None``, busca contexto atual.

    Returns:
        True se publicou, False se falhou (não-fatal).
    """
    slug = (
        tenant_slug if tenant_slug is not None else get_current_tenant_slug()
    )
    if not slug:
        logger.debug(
            "publish_event ignorado: sem tenant_slug (event={})", event_type
        )
        return False

    channel = get_sse_channel(slug)
    payload = json.dumps(
        {"type": event_type, "tenant_slug": slug, "data": data},
        default=str,
        ensure_ascii=False,
    )
    client = _get_redis()
    if client is None:
        return False
    try:
        client.publish(channel, payload)
        logger.debug(
            "SSE publish ok: channel={}, type={}, atendimento={}",
            channel,
            event_type,
            data.get("atendimento_id"),
        )
        return True
    except Exception as exc:
        logger.warning("Falha ao publicar SSE no canal {}: {}", channel, exc)
        return False

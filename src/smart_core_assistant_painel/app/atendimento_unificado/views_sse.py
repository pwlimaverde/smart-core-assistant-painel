# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportReturnType=false
"""Async view de Server-Sent Events do Workspace.

Subscribe ao canal Redis por tenant (`sse:{tenant_slug}:events`) e
emite cada evento como linha SSE.

Implementação minimalista, sem dependência de Channels:
- ``StreamingHttpResponse`` com ``async`` iterator (Django 4.1+).
- ``redis.asyncio`` para subscribe não-bloqueante.
- Heartbeat (``: ping``) a cada 25s para evitar timeouts intermediários.
- Filtra por tenant_slug da request, descartando payloads de outros tenants
  (defense-in-depth: o canal já é separado, mas validamos novamente).

Requer worker async (Uvicorn) — sob Gunicorn sync a conexão segura
ficaria pendurada bloqueando o worker.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from loguru import logger

from .feature_flags import get_sse_channel, is_workspace_enabled_for_tenant

HEARTBEAT_INTERVAL_SECONDS = 25.0


def workspace_events(request: HttpRequest) -> HttpResponse:
    """Endpoint SSE para o Workspace (sync stub + delegação opcional).

    Sob worker WSGI (Gunicorn sync), uma view ``async`` que retorne
    ``StreamingHttpResponse`` com ``async_generator`` trava o worker até
    timeout (120 s) e SIGKILL, derrubando o app inteiro. Por isso, esta
    view é sempre ``sync`` e — quando a flag está OFF — devolve um
    "close" imediato. O cliente reconecta com backoff sem prejuízo
    funcional (kanban/chat seguem via REST).

    Para habilitar SSE de verdade: troque o Gunicorn para
    ``uvicorn.workers.UvicornWorker`` e setar
    ``ATENDIMENTO_UNIFICADO_SSE_ENABLED=True``.
    """

    if not getattr(settings, "ATENDIMENTO_UNIFICADO_SSE_ENABLED", False):
        return _sse_close_response("sse_disabled")
    # Quando ASGI está disponível, Django aceita retornar a coroutine.
    return _async_workspace_events(request)  # type: ignore[return-value]


async def _async_workspace_events(request: HttpRequest) -> HttpResponse:
    """Implementação async real do endpoint SSE (uso sob worker ASGI)."""

    # Validações iniciais (sync via sync_to_async para evitar acessos
    # bloqueantes ao request.user que dispara ORM em alguns middlewares).
    user_is_authenticated = await sync_to_async(
        lambda: bool(request.user.is_authenticated)
    )()
    if not user_is_authenticated:
        return _sse_close_response("unauthenticated")

    enabled = await sync_to_async(is_workspace_enabled_for_tenant)()
    if not enabled:
        return _sse_close_response("feature_disabled")

    can_view = await sync_to_async(_user_can_view)(request)
    if not can_view:
        return _sse_close_response("forbidden")

    tenant_slug = await sync_to_async(_get_tenant_slug)(request)
    channel = get_sse_channel(tenant_slug)

    response = StreamingHttpResponse(
        _event_stream(channel, tenant_slug),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Nginx
    response["Connection"] = "keep-alive"
    return response


async def _event_stream(
    channel: str, tenant_slug: str
) -> AsyncIterator[bytes]:
    """Iterador async que produz linhas SSE.

    Yieldsa eventos do Redis + heartbeats periódicos.
    """
    yield b": connected\n\n"

    pubsub = None
    redis_client = None
    try:
        try:
            from redis import (
                asyncio as aioredis,  # type: ignore[import-not-found]
            )
        except Exception as exc:
            logger.error("redis.asyncio indisponível para SSE: {}", exc)
            return

        from django.conf import settings

        redis_url = str(
            getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
        )

        redis_client = aioredis.from_url(redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)
        logger.info(
            "SSE subscribe ok: channel={}, tenant_slug={}",
            channel,
            tenant_slug,
        )

        last_heartbeat = asyncio.get_event_loop().time()

        while True:
            try:
                msg = await asyncio.wait_for(
                    pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    ),
                    timeout=2.0,
                )
            except asyncio.TimeoutError:
                msg = None
            except asyncio.CancelledError:
                break

            now = asyncio.get_event_loop().time()
            if (now - last_heartbeat) > HEARTBEAT_INTERVAL_SECONDS:
                yield b": ping\n\n"
                last_heartbeat = now

            if msg is None:
                continue

            data = msg.get("data")
            if not data:
                continue
            try:
                payload = json.loads(data) if isinstance(data, str) else data
            except Exception:
                continue

            # Defense-in-depth: descarta se tenant_slug não bate.
            if (
                isinstance(payload, dict)
                and payload.get("tenant_slug")
                and payload.get("tenant_slug") != tenant_slug
            ):
                continue

            event_type = (
                payload.get("type", "message")
                if isinstance(payload, dict)
                else "message"
            )
            event_data = (
                payload.get("data", payload)
                if isinstance(payload, dict)
                else payload
            )
            chunk = _format_sse(event_type, event_data)
            yield chunk.encode("utf-8")
    except asyncio.CancelledError:
        # Cliente desconectou — sai limpo.
        pass
    except Exception as exc:
        logger.warning("Erro no stream SSE ({}): {}", channel, exc)
    finally:
        try:
            if pubsub is not None:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
        except Exception:
            pass
        try:
            if redis_client is not None:
                await redis_client.close()
        except Exception:
            pass


def _format_sse(event_type: str, data: object) -> str:
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event_type}\ndata: {payload}\n\n"


def _sse_close_response(reason: str) -> StreamingHttpResponse:
    body = (f'event: error\ndata: {{"reason":"{reason}"}}\n\n').encode("utf-8")
    response = StreamingHttpResponse(
        iter([body]), content_type="text/event-stream"
    )
    response.status_code = 200
    response["Cache-Control"] = "no-cache"
    return response


def _user_can_view(request: HttpRequest) -> bool:
    if request.user.is_superuser:
        return True
    tenant = getattr(request, "tenant", None)
    if tenant and getattr(tenant, "owner_id", None) == request.user.id:
        return True
    tenant_user = getattr(request, "tenant_user", None)
    if tenant_user is None:
        try:
            tenant_user = request.user.tenant_profile
        except Exception:
            tenant_user = None
    if tenant_user is None:
        return False
    return tenant_user.has_module_permission("atendimento", "view")


def _get_tenant_slug(request: HttpRequest) -> str:
    tenant = getattr(request, "tenant", None)
    if tenant is not None and getattr(tenant, "slug", None):
        return str(tenant.slug)
    # Fallback: tenta thread-local
    from smart_core_assistant_painel.app.tenants.tenant_context import (
        get_current_tenant_slug,
    )

    return get_current_tenant_slug() or "default"

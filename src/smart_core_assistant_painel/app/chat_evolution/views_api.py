# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false, reportReturnType=false
"""Endpoints JSON do Chat Evolution (sob /workspace/chat/api/).

Exige usuário autenticado, workspace ativado para o tenant e permissão adequada.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from loguru import logger

from smart_core_assistant_painel.app.atendimento_unificado.feature_flags import (
    is_workspace_enabled_for_tenant,
)
from smart_core_assistant_painel.app.chat_evolution.services.media_dispatch_service import (
    upload_and_send_media,
)
from smart_core_assistant_painel.app.chat_evolution.services.message_dispatch_service import (
    mark_read,
    send_text_message,
)
from smart_core_assistant_painel.app.operacional.models import Atendente

from .selectors import (
    contar_nao_lidos_global,
    get_atendimento_detail,
    get_messages,
    list_conversations,
    list_fluxos_acessiveis,
)


def _err(msg: str, code: str = "error", status: int = 400) -> JsonResponse:
    return JsonResponse({"error": msg, "code": code}, status=status)


def _require_workspace(
    func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """Decorator: verifica feature flag + autenticação + permissão."""

    def wrapper(
        view_self: View, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        if not request.user.is_authenticated:
            return _err("Autenticação obrigatória.", "unauthenticated", 401)
        if not is_workspace_enabled_for_tenant():
            return _err(
                "Workspace não habilitado para este tenant.",
                "feature_disabled",
                404,
            )
        if not _user_can_view(request):
            return _err("Permissão negada.", "forbidden", 403)
        return func(view_self, request, *args, **kwargs)

    return wrapper


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


def _is_owner_user(request: HttpRequest) -> bool:
    if request.user.is_superuser:
        return True
    tenant = getattr(request, "tenant", None)
    return bool(
        tenant and getattr(tenant, "owner_id", None) == request.user.id
    )


def _resolve_atendente(request: HttpRequest) -> Optional[Atendente]:
    try:
        return (
            Atendente.objects.select_related("departamento", "fluxo")
            .filter(usuario_id=request.user.id, ativo=True)
            .first()
        )
    except Exception:
        return None


def _resolve_tenant_user(request: HttpRequest) -> Any:
    tu = getattr(request, "tenant_user", None)
    if tu is not None:
        return tu
    try:
        return request.user.tenant_profile
    except Exception:
        return None


def _allowed_flow_ids(request: HttpRequest) -> Optional[set[int]]:
    if _is_owner_user(request):
        return None
    tenant_user = _resolve_tenant_user(request)
    atendente = _resolve_atendente(request)
    fluxos = list_fluxos_acessiveis(
        atendente=atendente,
        is_owner=False,
        tenant_user=tenant_user,
    )
    return {int(f["id"]) for f in fluxos}


def _can_access_fluxo(request: HttpRequest, fluxo_id: Optional[int]) -> bool:
    if fluxo_id is None:
        return True
    allowed = _allowed_flow_ids(request)
    if allowed is None:
        return True
    return int(fluxo_id) in allowed


def _can_access_atendimento(request: HttpRequest, atendimento_id: int) -> bool:
    allowed = _allowed_flow_ids(request)
    if allowed is None:
        return True
    from smart_core_assistant_painel.app.atendimentos.models import (
        Atendimento,
    )

    fluxo_id = (
        Atendimento.objects.filter(id=atendimento_id)
        .values_list("fluxo_atendimento_id", flat=True)
        .first()
    )
    if fluxo_id is None:
        return False
    return int(fluxo_id) in allowed


def _load_body(request: HttpRequest) -> dict[str, Any]:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _get_int(value: Any) -> Optional[int]:
    try:
        return int(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def _get_datetime(value: Any):
    if not value:
        return None
    try:
        from django.utils.dateparse import parse_datetime

        return parse_datetime(str(value))
    except Exception:
        return None


class ConversationsListView(View):
    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        atendente = _resolve_atendente(request)
        fluxo_id = _get_int(request.GET.get("fluxo"))
        if not _can_access_fluxo(request, fluxo_id):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        q = (request.GET.get("q") or "").strip() or None
        tag = (request.GET.get("tag") or "").strip() or None
        limit = min(_get_int(request.GET.get("limit")) or 100, 200)
        cursor = _get_datetime(request.GET.get("cursor"))
        prioridade = (request.GET.get("prioridade") or "").strip() or None
        atendente_id_filtro = _get_int(request.GET.get("atendente_id"))
        etiqueta_id = _get_int(request.GET.get("etiqueta_id"))
        apenas_nao_lidos = (
            request.GET.get("apenas_nao_lidos") or ""
        ).lower() in ("1", "true", "yes")
        items = list_conversations(
            fluxo_id=fluxo_id,
            atendente=atendente,
            is_owner=_is_owner_user(request),
            q=q,
            tag=tag,
            limit=limit,
            cursor=cursor,
            prioridade=prioridade,
            atendente_id_filtro=atendente_id_filtro,
            etiqueta_id=etiqueta_id,
            apenas_nao_lidos=apenas_nao_lidos,
        )
        return JsonResponse({"conversations": items})


class ConversationMessagesView(View):
    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        limit = min(_get_int(request.GET.get("limit")) or 50, 200)
        before_id = _get_int(request.GET.get("before_id"))
        msgs = get_messages(
            atendimento_id=int(atendimento_id),
            limit=limit,
            before_id=before_id,
        )
        return JsonResponse({"messages": msgs})


class ConversationDetailView(View):
    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        data = get_atendimento_detail(int(atendimento_id))
        if data is None:
            return _err("Atendimento não encontrado.", "not_found", 404)
        return JsonResponse(data)


@method_decorator(csrf_protect, name="dispatch")
class ConversationSendView(View):
    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        body = _load_body(request)
        texto = (body.get("texto") or "").strip()
        if not texto:
            return _err("Texto vazio.", "validation", 400)
        quoted_message_id = _get_int(body.get("quoted_message_id"))
        atendente = _resolve_atendente(request)
        try:
            msg = send_text_message(
                atendimento_id=int(atendimento_id),
                texto=texto,
                atendente=atendente,
                quoted_message_id=quoted_message_id,
            )
        except ValueError as exc:
            return _err(str(exc), "validation", 400)
        except Exception as exc:
            logger.exception("Falha ao enviar mensagem: {}", exc)
            return _err("Falha ao enviar mensagem.", "internal", 500)
        return JsonResponse(
            {
                "id": msg.id,
                "atendimento_id": msg.atendimento_id,
                "resposta_bot": msg.resposta_bot or "",
                "timestamp": (
                    msg.timestamp.isoformat() if msg.timestamp else None
                ),
            },
            status=201,
        )


@method_decorator(csrf_protect, name="dispatch")
class ConversationMarkReadView(View):
    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        atendente = _resolve_atendente(request)
        if atendente is None:
            return _err(
                "Apenas atendentes cadastrados podem marcar como lido.",
                "no_atendente",
                400,
            )
        read_at = mark_read(
            atendimento_id=atendimento_id, atendente_id=atendente.id
        )
        return JsonResponse(
            {
                "atendimento_id": atendimento_id,
                "atendente_id": atendente.id,
                "ultima_leitura_at": read_at.isoformat(),
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class ConversationPresenceView(View):
    _VALID_STATES = {"composing", "recording", "paused", "available"}

    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        body = _load_body(request)
        state = (body.get("state") or "composing").strip().lower()
        if state not in self._VALID_STATES:
            state = "composing"
        is_audio = bool(body.get("is_audio", False))

        try:
            _dispatch_presence(int(atendimento_id), state, is_audio)
        except Exception as exc:
            logger.warning("presence dispatch falhou (best-effort): {}", exc)

        return JsonResponse({"ok": True, "state": state})


def _dispatch_presence(
    atendimento_id: int, state: str, is_audio: bool = False
) -> None:
    """Despacha set_presence ao Evolution Go para o atendimento."""
    from smart_core_assistant_painel.app.atendimentos.models import Atendimento
    from smart_core_assistant_painel.app.evolution_sync.models import (
        EvolutionContact,
    )
    from smart_core_assistant_painel.app.evolution_sync.services import (
        EvolutionGoAdapter,
    )

    atend = (
        Atendimento.objects.select_related("contato")
        .filter(id=atendimento_id)
        .first()
    )
    if not atend or not atend.contato:
        return

    evo_contact = (
        EvolutionContact.objects.select_related("instance")
        .filter(contact_id=atend.contato_id, active=True)
        .order_by("-updated_at")
        .first()
    )
    if not evo_contact or not evo_contact.instance:
        return

    inst = evo_contact.instance
    tenant_id = getattr(inst, "tenant_id", None)
    base_url = ""
    if tenant_id:
        from smart_core_assistant_painel.app.tenants.models import (
            TenantEvolution,
        )

        cfg = TenantEvolution.objects.filter(tenant_id=tenant_id).first()
        if cfg and cfg.server_url:
            base_url = str(cfg.server_url).rstrip("/")
    if not base_url:
        return

    jid = evo_contact.jid or ""
    if not jid and atend.contato.telefone:
        jid = f"{atend.contato.telefone}@s.whatsapp.net"
    if not jid:
        return

    adapter = EvolutionGoAdapter()
    adapter.set_presence(
        instance=str(inst.name or ""),
        api_key=str(inst.api_key or ""),
        base_url=base_url,
        number=jid,
        state=state,
        is_audio=is_audio,
    )


@method_decorator(csrf_protect, name="dispatch")
class ConversationUploadView(View):
    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )

        uploaded = request.FILES.get("file")
        if uploaded is None:
            return _err("Campo `file` obrigatório.", "validation", 400)
        if uploaded.size > 10 * 1024 * 1024:
            return _err("Arquivo excede limite de 10 MB.", "validation", 400)
        file_bytes = uploaded.read()
        filename = uploaded.name or "arquivo"
        content_type = uploaded.content_type or "application/octet-stream"
        caption = (request.POST.get("caption") or "").strip()
        atendente = _resolve_atendente(request)
        try:
            msg = upload_and_send_media(
                atendimento_id=atendimento_id,
                file_bytes=file_bytes,
                filename=filename,
                content_type=content_type,
                atendente=atendente,
                caption=caption,
            )
        except ValueError as exc:
            return _err(str(exc), "validation", 400)
        except Exception as exc:
            logger.exception("Falha ao fazer upload de mídia: {}", exc)
            return _err("Falha ao enviar mídia.", "internal", 500)
        return JsonResponse(
            {
                "id": msg.id,
                "atendimento_id": msg.atendimento_id,
                "tipo": msg.tipo,
                "respondida": msg.respondida,
                "timestamp": (
                    msg.timestamp.isoformat() if msg.timestamp else None
                ),
            },
            status=201,
        )


class ConversationMediasView(View):
    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        from .selectors import list_medias

        return JsonResponse({"medias": list_medias(int(atendimento_id))})


class NotificationsUnreadCountView(View):
    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        atendente = _resolve_atendente(request)
        total = contar_nao_lidos_global(
            atendente=atendente, is_owner=_is_owner_user(request)
        )
        return JsonResponse({"total": int(total)})

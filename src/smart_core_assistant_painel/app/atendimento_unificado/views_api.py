# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false
"""Endpoints JSON do Workspace (consumidos pelo store Alpine).

Toda rota:
- Exige usuário autenticado.
- Exige ``module_permissions["atendimento"]["view"]`` (ou owner).
- Valida que o tenant atual tem a feature flag ligada.

Erros são serializados em JSON ``{"error": "...", "code": "..."}``.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from loguru import logger

from smart_core_assistant_painel.app.operacional.models import Atendente

from .feature_flags import is_workspace_enabled_for_tenant
from .selectors import (
    board_snapshot_by_fluxo,
    get_atendimento_detail,
    get_messages,
    list_conversations,
    list_fluxos_acessiveis,
)
from .services.board_service import (
    BoardMoveError,
    assign_atendimento,
    mark_read,
    move_atendimento,
)
from .services.message_dispatch_service import send_text_message


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


def _load_body(request: HttpRequest) -> dict[str, Any]:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


class FluxosListView(View):
    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        atendente = _resolve_atendente(request)
        return JsonResponse(
            {
                "fluxos": list_fluxos_acessiveis(
                    atendente=atendente, is_owner=_is_owner_user(request)
                )
            }
        )


class ConversationsListView(View):
    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        atendente = _resolve_atendente(request)
        fluxo_id = _get_int(request.GET.get("fluxo"))
        q = (request.GET.get("q") or "").strip() or None
        limit = min(_get_int(request.GET.get("limit")) or 100, 200)
        cursor = _get_datetime(request.GET.get("cursor"))
        items = list_conversations(
            fluxo_id=fluxo_id,
            atendente=atendente,
            is_owner=_is_owner_user(request),
            q=q,
            limit=limit,
            cursor=cursor,
        )
        return JsonResponse({"conversations": items})


class ConversationMessagesView(View):
    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
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
        data = get_atendimento_detail(int(atendimento_id))
        if data is None:
            return _err("Atendimento não encontrado.", "not_found", 404)
        return JsonResponse(data)


@method_decorator(csrf_protect, name="dispatch")
class ConversationSendView(View):
    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        body = _load_body(request)
        texto = (body.get("texto") or "").strip()
        if not texto:
            return _err("Texto vazio.", "validation", 400)
        atendente = _resolve_atendente(request)
        try:
            msg = send_text_message(
                atendimento_id=int(atendimento_id),
                texto=texto,
                atendente=atendente,
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
        atendente = _resolve_atendente(request)
        if atendente is None:
            return _err(
                "Apenas atendentes cadastrados podem marcar como lido.",
                "no_atendente",
                400,
            )
        obj = mark_read(
            atendimento_id=int(atendimento_id), atendente_id=atendente.id
        )
        return JsonResponse(
            {
                "atendimento_id": obj.atendimento_id,
                "atendente_id": obj.atendente_id,
                "ultima_leitura_at": obj.ultima_leitura_at.isoformat(),
            }
        )


class BoardSnapshotView(View):
    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        fluxo_id = _get_int(request.GET.get("fluxo"))
        if fluxo_id is None:
            return _err("Parâmetro `fluxo` obrigatório.", "validation", 400)
        atendente = _resolve_atendente(request)
        data = board_snapshot_by_fluxo(
            fluxo_id=fluxo_id,
            atendente=atendente,
            is_owner=_is_owner_user(request),
        )
        return JsonResponse(data)


@method_decorator(csrf_protect, name="dispatch")
class BoardMoveView(View):
    @_require_workspace
    def post(self, request: HttpRequest) -> HttpResponse:
        body = _load_body(request)
        atendimento_id = _get_int(body.get("atendimento_id"))
        etapa_destino_id = _get_int(body.get("etapa_destino_id"))
        if atendimento_id is None or etapa_destino_id is None:
            return _err(
                "Campos `atendimento_id` e `etapa_destino_id` obrigatórios.",
                "validation",
                400,
            )
        atendente = _resolve_atendente(request)
        try:
            result = move_atendimento(
                atendimento_id=atendimento_id,
                etapa_destino_id=etapa_destino_id,
                atendente_actor=atendente,
                motivo=(body.get("motivo") or None),
            )
        except BoardMoveError as exc:
            return _err(str(exc), "board_move", 400)
        except Exception as exc:
            logger.exception("Falha ao mover card: {}", exc)
            return _err("Falha ao mover card.", "internal", 500)
        return JsonResponse(
            {
                "atendimento_id": result.atendimento.id,
                "etapa_id": result.atendimento.etapa_atual_id,
                "fluxo_id": result.atendimento.fluxo_atendimento_id,
                "novo_status": result.novo_status,
                "cross_board": result.cross_board,
                "finalizou": result.finalizou,
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class BoardAssignView(View):
    @_require_workspace
    def post(self, request: HttpRequest) -> HttpResponse:
        body = _load_body(request)
        atendimento_id = _get_int(body.get("atendimento_id"))
        atendente_id = _get_int(body.get("atendente_id"))
        com_saudacao = bool(body.get("com_saudacao", True))
        if atendimento_id is None or atendente_id is None:
            return _err(
                "Campos `atendimento_id` e `atendente_id` obrigatórios.",
                "validation",
                400,
            )
        atendente = Atendente.objects.filter(
            id=atendente_id, ativo=True
        ).first()
        if atendente is None:
            return _err("Atendente não encontrado.", "not_found", 404)
        try:
            atend = assign_atendimento(
                atendimento_id=atendimento_id,
                atendente=atendente,
                com_saudacao=com_saudacao,
            )
        except Exception as exc:
            logger.exception("Falha ao atribuir atendimento: {}", exc)
            return _err("Falha ao atribuir atendimento.", "internal", 500)
        return JsonResponse(
            {
                "atendimento_id": atend.id,
                "atendente_id": atend.atendente_humano_id,
                "status": atend.status,
            }
        )


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

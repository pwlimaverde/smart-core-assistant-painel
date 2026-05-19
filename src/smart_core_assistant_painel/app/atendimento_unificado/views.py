# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false
"""Views HTML do Workspace.

A `WorkspaceView` renderiza o shell único (Tailwind+Alpine) e injeta o
``fluxo_selecionado`` no contexto. Toda interatividade acontece via
endpoints JSON (`views_api.py`) e SSE (`views_sse.py`).
"""

from __future__ import annotations

from typing import Any, Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from smart_core_assistant_painel.app.operacional.models import Atendente
from smart_core_assistant_painel.app.tenants.tenant_context import (
    get_current_tenant_slug,
)

from .feature_flags import is_workspace_enabled_for_tenant
from .selectors import list_fluxos_acessiveis


@method_decorator(login_required, name="dispatch")
class WorkspaceView(View):
    """Shell HTML do Workspace de Atendimento Unificado."""

    template_name = "atendimento_unificado/workspace.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        if not is_workspace_enabled_for_tenant():
            return _disabled_response(request)
        if not _user_can_view(request):
            return HttpResponseForbidden(
                "Você não tem permissão para acessar o Workspace."
            )

        atendente = _resolve_atendente(request)
        is_owner = _is_owner_user(request)
        tenant_user = _resolve_tenant_user(request)

        fluxos = list_fluxos_acessiveis(
            atendente=atendente,
            is_owner=is_owner,
            tenant_user=tenant_user,
        )
        try:
            fluxo_param = request.GET.get("fluxo")
            fluxo_id: Optional[int] = int(fluxo_param) if fluxo_param else None
        except (TypeError, ValueError):
            fluxo_id = None

        # Recupera/persiste preferência em session
        if fluxo_id is None:
            fluxo_id = request.session.get("workspace_fluxo_id")
            if not _fluxo_in_list(fluxo_id, fluxos):
                fluxo_id = fluxos[0]["id"] if fluxos else None
        if fluxo_id is not None:
            request.session["workspace_fluxo_id"] = fluxo_id

        contexto: dict[str, Any] = {
            "fluxos": fluxos,
            "fluxo_id": fluxo_id,
            "tenant_slug": get_current_tenant_slug(),
            "atendente_id": getattr(atendente, "id", None),
            "atendente_nome": getattr(atendente, "nome", ""),
            "sse_enabled": bool(
                getattr(settings, "ATENDIMENTO_UNIFICADO_SSE_ENABLED", False)
            ),
        }
        return render(request, self.template_name, contexto)


def _disabled_response(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "atendimento_unificado/workspace_disabled.html",
        status=200,
    )


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


def _resolve_tenant_user(request: HttpRequest) -> Any:
    """Resolve o TenantUser do usuário autenticado, se houver.

    Owner do tenant não tem TenantUser obrigatoriamente — neste caso
    retorna None e a gate de owner é aplicada antes pelo selector.
    """
    tu = getattr(request, "tenant_user", None)
    if tu is not None:
        return tu
    try:
        return request.user.tenant_profile
    except Exception:
        return None


def _resolve_atendente(request: HttpRequest) -> Optional[Atendente]:
    user = request.user
    if not user.is_authenticated:
        return None
    try:
        return (
            Atendente.objects.select_related("departamento", "fluxo")
            .filter(usuario_id=user.id, ativo=True)
            .first()
        )
    except Exception:
        return None


def _fluxo_in_list(
    fluxo_id: Optional[int], fluxos: list[dict[str, Any]]
) -> bool:
    if fluxo_id is None:
        return False
    return any(f["id"] == fluxo_id for f in fluxos)

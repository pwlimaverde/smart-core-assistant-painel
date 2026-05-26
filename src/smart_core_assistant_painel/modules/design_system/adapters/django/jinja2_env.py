import os
from typing import Any, Optional

from django.contrib.staticfiles import finders
from django.middleware.csrf import get_token
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escapejs
from django.utils.safestring import mark_safe
from jinja2 import Environment, pass_context

from smart_core_assistant_painel.app.tenants.models import Tenant, TenantUser


def _csrf_input(request: Any) -> Any:
    """Retorna o input CSRF com segurança para formulários Jinja2."""
    token = get_token(request)
    return mark_safe(
        f'<input type="hidden" name="csrfmiddlewaretoken" value="{token}">'
    )


def _resolve_mtime(path: str) -> Optional[float]:
    try:
        located = finders.find(path)
    except Exception:
        located = None
    if not located or not isinstance(located, str):
        return None
    if not os.path.isfile(located):
        return None
    try:
        return os.path.getmtime(located)
    except OSError:
        return None


def static_versioned(path: str) -> str:
    """Versão Jinja2 para cache-busting baseado no mtime do arquivo estático."""
    url = static(path)
    mtime = _resolve_mtime(path)
    if mtime is None:
        return url
    return f"{url}?v={int(mtime)}"


def _resolve_tenant_context(
    request: Any,
) -> tuple[Optional[Tenant], Optional[TenantUser]]:
    tenant = getattr(request, "tenant", None)
    tenant_user = None
    if tenant:
        try:
            tenant_user = TenantUser.objects.get(
                user=request.user, tenant=tenant, is_active=True
            )
        except TenantUser.DoesNotExist:
            tenant_user = None
        return tenant, tenant_user

    # Tenta via TenantUser
    try:
        tenant_user = request.user.tenant_profile
        tenant = tenant_user.tenant
        return tenant, tenant_user
    except Exception:
        pass

    # Tenta via owner
    tenant = Tenant.objects.filter(owner=request.user).first()
    return tenant, None


@pass_context
def can_view_module(context: Any, module_name: str) -> bool:
    """Verifica se o usuário tem permissão para visualizar um módulo específico."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False

    # Superuser sempre tem acesso
    if request.user.is_superuser:
        return True

    tenant, tenant_user = _resolve_tenant_context(request)
    if not tenant:
        return False

    # Owner do tenant sempre tem acesso total
    if tenant.owner == request.user:
        return True

    if not tenant_user:
        return False
    return tenant_user.has_module_permission(module_name, "view")


@pass_context
def has_any_module_permission(context: Any) -> bool:
    """Retorna True se o usuário tiver ao menos 1 permissão de módulo (view)."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False

    if request.user.is_superuser:
        return True

    tenant, tenant_user = _resolve_tenant_context(request)
    if not tenant:
        return False

    if tenant.owner == request.user:
        return True
    if tenant_user is None:
        return False

    for perms in tenant_user.module_permissions.values():
        if isinstance(perms, dict) and perms.get("view") is True:
            return True
    return False


@pass_context
def has_no_module_permissions(context: Any) -> bool:
    """Retorna True se o usuário do tenant não tiver nenhuma permissão de módulo."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False

    tenant, tenant_user = _resolve_tenant_context(request)
    if not tenant:
        return False

    if tenant.owner == request.user:
        return False
    if tenant_user is None:
        return False

    for perms in tenant_user.module_permissions.values():
        if isinstance(perms, dict) and perms.get("view") is True:
            return False
    return True


@pass_context
def has_full_module_permissions(context: Any) -> bool:
    """Retorna True se o usuário tiver todas as permissões de módulo (view)."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False

    if request.user.is_superuser:
        return True

    tenant, tenant_user = _resolve_tenant_context(request)
    if not tenant:
        return False

    if tenant.owner == request.user:
        return True
    if tenant_user is None:
        return False

    from smart_core_assistant_painel.app.tenants.permissions import (
        TenantModule,
    )

    for module in TenantModule.all_values():
        if module == TenantModule.PAINEL_ADMIN.value:
            continue
        perms = tenant_user.module_permissions.get(module, {})
        if not isinstance(perms, dict) or perms.get("view") is not True:
            return False
    return True


@pass_context
def can_access_admin_panel(context: Any) -> bool:
    """Retorna True se o usuário puder acessar o painel admin do tenant."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False

    if request.user.is_superuser:
        return True

    tenant, tenant_user = _resolve_tenant_context(request)
    if not tenant:
        return False

    if tenant.owner == request.user:
        return True
    if tenant_user is None:
        return False

    from smart_core_assistant_painel.app.tenants.permissions import (
        TenantModule,
    )

    if tenant_user.has_module_permission(
        TenantModule.PAINEL_ADMIN.value, "view"
    ):
        return True

    for module in (
        TenantModule.CLIENTES.value,
        TenantModule.OPERACIONAL.value,
        TenantModule.ATENDIMENTOS.value,
    ):
        if tenant_user.has_module_permission(module, "view"):
            return True
    return False


@pass_context
def is_owner_user(context: Any) -> bool:
    """Retorna True se o usuário for owner do tenant atual."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False
    tenant, _tenant_user = _resolve_tenant_context(request)
    if not tenant:
        return False
    return tenant.owner == request.user


def environment(**options: Any) -> Environment:
    """Inicializa e configura o ambiente Jinja2."""
    env = Environment(**options)
    env.globals.update(
        {
            # Equivalentes Django
            "url": reverse,
            "static": static,
            "csrf_input": _csrf_input,
            "static_versioned": static_versioned,
            "now": timezone.now,
            # Helpers de permissão e tenant
            "can_view_module": can_view_module,
            "is_owner_user": is_owner_user,
            "can_access_admin_panel": can_access_admin_panel,
            "has_no_module_permissions": has_no_module_permissions,
            "has_any_module_permission": has_any_module_permission,
            "has_full_module_permissions": has_full_module_permissions,
        }
    )
    env.filters["escapejs"] = escapejs
    return env

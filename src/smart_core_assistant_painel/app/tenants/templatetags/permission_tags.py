from django import template
from smart_core_assistant_painel.app.tenants.models import Tenant, TenantUser

register = template.Library()


@register.simple_tag(takes_context=True)
def can_view_module(context, module_name):
    """
    Verifica se o usuário tem permissão para visualizar um módulo específico.
    Uso: {% can_view_module "database" as can_view_db %}

    Retorna True se:
    - Usuário é superuser
    - Usuário é owner do tenant
    - Usuário tem role='admin' no TenantUser
    - Usuário tem a permissão específica do módulo
    """
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


@register.simple_tag(takes_context=True)
def has_any_module_permission(context) -> bool:
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


@register.simple_tag(takes_context=True)
def has_no_module_permissions(context) -> bool:
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


@register.simple_tag(takes_context=True)
def has_full_module_permissions(context) -> bool:
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


@register.simple_tag(takes_context=True)
def can_access_admin_panel(context) -> bool:
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


@register.simple_tag(takes_context=True)
def is_owner_user(context) -> bool:
    """Retorna True se o usuário for owner do tenant atual."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False
    tenant, _tenant_user = _resolve_tenant_context(request)
    if not tenant:
        return False
    return tenant.owner == request.user


def _resolve_tenant_context(request):
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

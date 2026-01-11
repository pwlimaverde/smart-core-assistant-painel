from django import template
from smart_core_assistant_painel.app.tenants.models import TenantUser

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

    # Verifica se o request tem tenant (definido pelo TenantMiddleware)
    tenant = getattr(request, "tenant", None)
    if not tenant:
        # Sem tenant, permite acesso básico para evitar sidebar vazia
        return True

    # Owner do tenant sempre tem acesso total
    if tenant.owner == request.user:
        return True

    # Verifica permissão via TenantUser
    try:
        tenant_user = TenantUser.objects.get(
            user=request.user, tenant=tenant, is_active=True
        )
        # Admin sempre tem acesso
        if tenant_user.role == "admin":
            return True
        # Verifica permissão específica do módulo
        return tenant_user.has_module_permission(module_name, "view")
    except TenantUser.DoesNotExist:
        # Se não encontrar TenantUser mas o usuário está autenticado,
        # permite acesso para não bloquear a UI
        return True

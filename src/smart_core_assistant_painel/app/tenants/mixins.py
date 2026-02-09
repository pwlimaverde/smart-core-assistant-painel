from typing import Any, Optional

from django.db.models import QuerySet
from django.http import HttpRequest
from loguru import logger

from .middleware import get_current_tenant, set_current_tenant


def _get_tenant_from_request(request: HttpRequest) -> Optional[Any]:
    """
    Tenta obter o tenant de múltiplas fontes:
    1. Contexto thread-local (set pelo middleware)
    2. Atributo request.tenant (set pelo TenantAdminSite.has_permission)
    3. Fallback: busca pelo owner do usuário logado
    """
    # 1. Tentar do thread-local
    tenant = get_current_tenant()
    if tenant:
        return tenant

    # 2. Tentar do request.tenant
    tenant = getattr(request, "tenant", None)
    if tenant:
        # Popular no contexto thread-local para uso nas queries
        set_current_tenant(tenant)
        return tenant

    # 3. Fallback: buscar pelo owner
    if hasattr(request, "user") and request.user.is_authenticated:
        from smart_core_assistant_painel.app.tenants.models import Tenant

        tenant = Tenant.objects.filter(owner=request.user).first()
        if tenant:
            request.tenant = tenant  # type: ignore[attr-defined]
            set_current_tenant(tenant)
            return tenant
        else:
            logger.warning(
                f"[Mixin] Nenhum tenant encontrado para owner: {request.user}"
            )

    logger.warning("[Mixin] Nenhum tenant encontrado em nenhuma fonte")
    return None


class TenantModelAdminMixin:
    """
    Mixin para ModelAdmins do TenantAdminSite.
    Assegura que as permissões de escrita dependam do tenant estar ativo no contexto.
    O isolamento de dados (leitura/escrita) é garantido primariamente pelo TenantDatabaseRouter,
    que roteia as queries para o banco do tenant.
    """

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """
        Retorna o queryset para o model.
        O roteamento de banco de dados (TenantDatabaseRouter) garantirá
        que a query seja executada no banco correto.
        """
        # Garantir que o tenant está no contexto
        _get_tenant_from_request(request)
        return super().get_queryset(request)  # type: ignore

    def has_module_permission(self, request: HttpRequest) -> bool:
        """
        Verifica se o usuário tem permissão para ver o módulo.
        Retorna True se o tenant está ativo (não delega para Django).
        """
        tenant = _get_tenant_from_request(request)
        if not tenant or not tenant.active:
            return False
        # Para o tenant admin, se o tenant está ativo, permite acesso
        return True

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[Any] = None
    ) -> bool:
        """Permite visualizar se o tenant está ativo."""
        tenant = _get_tenant_from_request(request)
        if not tenant or not tenant.active:
            return False
        return True

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Permite adicionar se o tenant está ativo."""
        tenant = _get_tenant_from_request(request)
        if not tenant or not tenant.active:
            return False
        return True

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Any] = None
    ) -> bool:
        """Permite editar se o tenant está ativo."""
        tenant = _get_tenant_from_request(request)
        if not tenant or not tenant.active:
            return False
        return True

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Any] = None
    ) -> bool:
        """Permite deletar se o tenant está ativo."""
        tenant = _get_tenant_from_request(request)
        if not tenant or not tenant.active:
            return False
        return True

    def save_model(
        self, request: Any, obj: Any, form: Any, change: bool
    ) -> None:
        """
        Hook para salvar o objeto. O router direcionará para o banco correto.
        Pode ser usado para logs de auditoria futuros.
        """
        # Garantir contexto
        _get_tenant_from_request(request)
        super().save_model(request, obj, form, change)  # type: ignore

    def delete_model(self, request: Any, obj: Any) -> None:
        """
        Hook para deletar o objeto.
        """
        _get_tenant_from_request(request)
        super().delete_model(request, obj)  # type: ignore

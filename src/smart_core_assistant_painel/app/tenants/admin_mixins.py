"""
Mixins de admin para verificação de permissões por módulo do tenant.

Este módulo fornece mixins reutilizáveis para ModelAdmins que precisam
verificar permissões granulares por módulo e tenant.
"""

from typing import Any, Optional

from django.contrib import admin
from django.http import HttpRequest


class TenantPermissionMixin:
    """
    Mixin para verificação de permissão por módulo do tenant.

    Deve ser usado em conjunto com ModelAdmin para restringir acesso
    com base no papel (role) e permissões de módulo do TenantUser.

    Atributos:
        module_name: Nome do módulo para verificação (ex: 'clientes').
    """

    module_name: str = ""  # Override em cada admin

    def has_module_permission(self, request: HttpRequest) -> bool:
        """Verifica se o usuário tem permissão para acessar o módulo."""
        if request.user.is_superuser:
            return True

        tenant = getattr(request, "tenant", None)
        if tenant and tenant.owner == request.user:
            return True

        tenant_user = getattr(request, "tenant_user", None)
        if tenant_user and self.module_name:
            return tenant_user.has_module_permission(self.module_name, "view")

        return False

    def has_view_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Verifica permissão de visualização."""
        return self._check_permission(request, "view")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Verifica permissão de adição (requer 'edit')."""
        return self._check_permission(request, "edit")

    def has_change_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Verifica permissão de alteração."""
        return self._check_permission(request, "edit")

    def has_delete_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Verifica permissão de exclusão."""
        return self._check_permission(request, "delete")

    def _check_permission(self, request: HttpRequest, action: str) -> bool:
        """Lógica centralizada de verificação de permissão."""
        if request.user.is_superuser:
            return True

        tenant = getattr(request, "tenant", None)
        if tenant and tenant.owner == request.user:
            return True

        tenant_user = getattr(request, "tenant_user", None)
        if tenant_user and self.module_name:
            return tenant_user.has_module_permission(self.module_name, action)

        return False


class TenantFilterMixin:
    """
    Mixin para filtragem automática de queryset por tenant.

    Garante que apenas objetos do tenant atual sejam exibidos
    e que novos objetos sejam automaticamente associados ao tenant.
    """

    def get_queryset(self, request: HttpRequest) -> Any:
        """Filtra queryset pelo tenant da request."""
        qs = super().get_queryset(request)  # type: ignore[misc]
        tenant = getattr(request, "tenant", None)
        if tenant and hasattr(qs.model, "tenant"):
            return qs.filter(tenant=tenant)
        return qs

    def save_model(
        self, request: HttpRequest, obj: Any, form: Any, change: bool
    ) -> None:
        """Injeta tenant automaticamente ao salvar."""
        if not change and hasattr(obj, "tenant"):
            tenant = getattr(request, "tenant", None)
            if tenant and not obj.tenant_id:
                obj.tenant = tenant
        super().save_model(request, obj, form, change)  # type: ignore[misc]


class BaseTenantModelAdmin(
    TenantPermissionMixin, TenantFilterMixin, admin.ModelAdmin
):
    """
    ModelAdmin base para uso no tenant-admin.

    Combina verificação de permissões por módulo e filtragem por tenant.
    Subclasses devem definir `module_name` apropriado.

    Exemplo:
        class ClienteAdmin(BaseTenantModelAdmin):
            module_name = "clientes"
            list_display = ["nome", "telefone"]

        tenant_admin_site.register(Cliente, ClienteAdmin)
    """

    pass

"""Mixins e decorators para proteção de APIs REST por tenant."""

from functools import wraps
from typing import Any, Callable

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied


def tenant_required(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator que exige tenant na request."""

    @wraps(view_func)
    def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
        if not getattr(request, "tenant", None):
            raise PermissionDenied("Tenant não identificado.")
        return view_func(request, *args, **kwargs)

    return wrapper


class TenantQuerysetMixin:
    """
    Mixin para ViewSets do DRF com filtragem por tenant.
    Suporta verificação de permissões granulares por módulo.
    """

    module_name: str = ""  # Override em cada ViewSet

    def get_queryset(self) -> Any:
        qs = super().get_queryset()  # type: ignore
        tenant = getattr(self.request, "tenant", None)

        if not tenant:
            return qs.none()  # Segurança: sem tenant, sem dados

        # Verificar permissão de módulo para funcionários
        if hasattr(self.request, "tenant_user"):
            tenant_user = getattr(self.request, "tenant_user")
            if (
                tenant_user
                and self.module_name
                and not tenant_user.has_module_permission(
                    self.module_name, "view"
                )
            ):
                return qs.none()

        if hasattr(qs.model, "tenant"):
            return qs.filter(tenant=tenant)
        return qs


class TenantCreateMixin:
    """Mixin para injetar tenant ao criar objetos via API."""

    def perform_create(self, serializer: Any) -> None:
        tenant = getattr(self.request, "tenant", None)
        if tenant:
            serializer.save(tenant=tenant)
        else:
            raise PermissionDenied("Tenant não identificado.")


class TenantForeignKeyValidator:
    """
    Valida que FKs pertencem ao mesmo tenant.
    Uso no serializer: validators = [TenantForeignKeyValidator(['campo_fk'])]
    """

    def __init__(self, fk_fields: list[str]) -> None:
        self.fk_fields = fk_fields

    def __call__(self, attrs: dict[str, Any], serializer: Any) -> None:
        request = serializer.context.get("request")
        tenant = getattr(request, "tenant", None) if request else None

        if not tenant:
            # Se não tem tenant no contexto, geralmente validação falhará antes
            return

        for field_name in self.fk_fields:
            obj = attrs.get(field_name)
            # Verifica se objeto existe e tem tenant_id
            if obj and hasattr(obj, "tenant_id"):
                if obj.tenant_id != tenant.id:
                    raise serializers.ValidationError(
                        {field_name: "Este objeto pertence a outro tenant."}
                    )

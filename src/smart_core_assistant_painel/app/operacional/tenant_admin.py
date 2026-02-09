from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from smart_core_assistant_painel.app.atendimentos.models import (
    MovimentoFluxo,
)
from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)
from smart_core_assistant_painel.app.tenants.admin_mixins import (
    BaseTenantModelAdmin,
)

from .models import (
    AppInstance,
    Atendente,
    Departamento,
    EtapaFluxo,
    FluxoAtendimento,
)


class TenantDepartamentoAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[Departamento]
):
    """Admin para gestão de Departamentos isolados por tenant."""

    module_name = "operacional"

    list_display = ("nome", "descricao", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


class TenantAtendenteAdmin(BaseTenantModelAdmin, admin.ModelAdmin[Atendente]):
    """Admin para gestão de Atendentes isolados por tenant."""

    module_name = "operacional"

    list_display = ("nome", "telefone", "departamento", "ativo")
    search_fields = ("nome", "telefone")
    list_filter = ("departamento", "ativo")


class TenantAppInstanceAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[AppInstance]
):
    """Admin para gestão de Instâncias de App isoladas por tenant."""

    module_name = "operacional"

    list_display = ("display_name", "channel", "active")
    list_filter = ("channel", "active")
    search_fields = ("display_name", "api_key")


class TenantFluxoAtendimentoAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[FluxoAtendimento]
):
    """Admin para gestão de Fluxos de Atendimento isolados por tenant."""

    module_name = "operacional"

    list_display = ("nome", "departamento", "ativo")
    search_fields = ("nome",)
    list_filter = ("ativo", "departamento")


class TenantEtapaFluxoAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[EtapaFluxo]
):
    """Admin para gestão de Etapas de Fluxo isoladas por tenant."""

    module_name = "operacional"

    list_display = ("nome", "ordem", "tipo_etapa", "fluxo")
    list_filter = ("fluxo", "tipo_etapa")
    ordering = ("fluxo", "ordem")


class TenantMovimentoFluxoAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[MovimentoFluxo]
):
    """Admin para visualização de Movimentos de Fluxo isolados por tenant."""

    module_name = "operacional"

    list_display = (
        "atendimento",
        "etapa_origem",
        "etapa_destino",
        "data_movimento",
    )
    list_filter = ("data_movimento",)

    def has_add_permission(self, request: HttpRequest) -> bool:  # type: ignore[override]
        return False

    def has_delete_permission(  # type: ignore[override]
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        return False

    def has_change_permission(  # type: ignore[override]
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        return False


# Register to TenantAdminSite
tenant_admin_site.register(Departamento, TenantDepartamentoAdmin)
tenant_admin_site.register(Atendente, TenantAtendenteAdmin)
tenant_admin_site.register(AppInstance, TenantAppInstanceAdmin)
tenant_admin_site.register(FluxoAtendimento, TenantFluxoAtendimentoAdmin)
tenant_admin_site.register(EtapaFluxo, TenantEtapaFluxoAdmin)
tenant_admin_site.register(MovimentoFluxo, TenantMovimentoFluxoAdmin)

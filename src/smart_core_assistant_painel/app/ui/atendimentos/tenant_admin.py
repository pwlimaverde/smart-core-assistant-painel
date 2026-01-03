from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)
from smart_core_assistant_painel.app.tenants.admin_mixins import (
    BaseTenantModelAdmin,
)

from .models import Atendimento, Mensagem


class TenantMensagemInline(admin.TabularInline[Mensagem]):
    """Inline de mensagens dentro de um atendimento."""

    model = Mensagem
    extra = 0
    readonly_fields = ("remetente", "tipo", "conteudo", "timestamp")
    can_delete = True

    def has_add_permission(  # type: ignore[override]
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        return False


class TenantAtendimentoAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[Atendimento]
):
    """Admin para gestão de Atendimentos isolados por tenant."""

    module_name = "atendimentos"

    list_display = ("id", "contato", "status", "data_inicio")
    list_filter = ("status", "data_inicio")
    search_fields = ("contato__telefone",)
    readonly_fields = (
        "contato",
        "data_inicio",
        "data_fim",
    )
    inlines = [TenantMensagemInline]

    def has_add_permission(  # type: ignore[override]
        self, request: HttpRequest
    ) -> bool:
        return False

    def has_delete_permission(  # type: ignore[override]
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        return True


class TenantMensagemAdmin(BaseTenantModelAdmin, admin.ModelAdmin[Mensagem]):
    """Admin para visualização de Mensagens isoladas por tenant."""

    module_name = "atendimentos"

    list_display = ("atendimento", "remetente", "timestamp")
    list_filter = ("remetente", "timestamp")
    search_fields = ("conteudo",)

    def has_add_permission(  # type: ignore[override]
        self, request: HttpRequest
    ) -> bool:
        return False

    def has_change_permission(  # type: ignore[override]
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        return False

    def has_delete_permission(  # type: ignore[override]
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        return True


tenant_admin_site.register(Atendimento, TenantAtendimentoAdmin)
tenant_admin_site.register(Mensagem, TenantMensagemAdmin)

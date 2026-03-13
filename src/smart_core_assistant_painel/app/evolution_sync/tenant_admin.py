"""
Admin de tenant para modelos de evolution_sync.

Este módulo registra os modelos de evolution_sync no tenant_admin_site
para gestão isolada por tenant.
"""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)
from smart_core_assistant_painel.app.tenants.mixins import (
    TenantModelAdminMixin,
)

from .forms import WhiteListAdminForm
from .models import EvolutionContact, EvolutionInstance, WhiteList


class TenantEvolutionInstanceAdmin(
    TenantModelAdminMixin, admin.ModelAdmin[EvolutionInstance]
):
    """Admin para gestão de Instâncias Evolution isoladas por tenant."""

    list_display = ("name", "phone_number", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name", "phone_number")
    readonly_fields = ("instance_id", "api_key", "name", "created_at")

    def has_add_permission(  # type: ignore[override]
        self, request: HttpRequest
    ) -> bool:
        # Instâncias são criadas via API/setup, não manualmente
        return False

    def has_delete_permission(  # type: ignore[override]
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        return False


class TenantEvolutionContactAdmin(
    TenantModelAdminMixin, admin.ModelAdmin[EvolutionContact]
):
    """Admin para visualização de Contatos Evolution mapeados."""

    list_display = ("contact", "instance", "jid", "active", "updated_at")
    list_filter = ("instance", "active")
    search_fields = ("jid", "lid")
    readonly_fields = (
        "jid",
        "lid",
        "addressing_mode",
        "metadados",
        "created_at",
        "updated_at",
    )

    def has_add_permission(  # type: ignore[override]
        self, request: HttpRequest
    ) -> bool:
        # Contatos são criados via webhook, não manualmente
        return False


class TenantWhiteListAdmin(TenantModelAdminMixin, admin.ModelAdmin[WhiteList]):
    """Admin para gestão de Whitelist de números bloqueados.

    Quando um contato é selecionado, os campos ``name`` e ``phone_number``
    são preenchidos automaticamente com os dados do contato via JavaScript
    (AJAX) e também pelo ``save_model`` como fallback de segurança.
    """

    form = WhiteListAdminForm
    list_display = ("name", "contact", "phone_number", "active", "created_at")
    list_filter = ("active",)
    search_fields = (
        "name",
        "phone_number",
        "contact__nome_contato",
        "contact__telefone",
    )
    readonly_fields = ("created_at",)
    list_select_related = ("contact",)

    def save_model(
        self,
        request: HttpRequest,
        obj: WhiteList,
        form: Any,
        change: bool,
    ) -> None:
        """Garante que name e phone_number são populados do contato.

        Funciona como camada de segurança caso o JavaScript não tenha
        preenchido os campos automaticamente.
        """
        if obj.contact:
            if not obj.name and obj.contact.nome_contato:
                obj.name = obj.contact.nome_contato
            if not obj.phone_number and obj.contact.telefone:
                obj.phone_number = obj.contact.telefone
        super().save_model(request, obj, form, change)  # type: ignore[misc]


# Registro no tenant_admin_site
tenant_admin_site.register(EvolutionInstance, TenantEvolutionInstanceAdmin)
tenant_admin_site.register(EvolutionContact, TenantEvolutionContactAdmin)
tenant_admin_site.register(WhiteList, TenantWhiteListAdmin)

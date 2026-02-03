"""
Admin de tenant para modelos do trello_sync.

Este módulo registra os modelos do trello_sync no tenant_admin_site
para gestão isolada por tenant.
"""

from django.contrib import admin

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)
from smart_core_assistant_painel.app.tenants.mixins import (
    TenantModelAdminMixin,
)

from .models import (
    TrelloBoard,
    TrelloCard,
    TrelloList,
    TrelloMember,
    TrelloWebhookEvent,
)


class TenantTrelloBoardAdmin(
    TenantModelAdminMixin, admin.ModelAdmin[TrelloBoard]
):
    """Admin para gestão de Boards Trello isolados por tenant."""

    list_display = ["name", "external_id", "fluxo", "url", "created_at"]
    search_fields = ["name", "external_id", "url"]
    list_filter = ["fluxo"]
    readonly_fields = ["external_id", "url", "created_at", "updated_at"]


class TenantTrelloListAdmin(
    TenantModelAdminMixin, admin.ModelAdmin[TrelloList]
):
    """Admin para gestão de Listas Trello isoladas por tenant."""

    list_display = ["name", "external_id", "board", "etapa", "position"]
    search_fields = ["name", "external_id"]
    list_filter = ["board"]
    readonly_fields = ["external_id"]


class TenantTrelloCardAdmin(
    TenantModelAdminMixin, admin.ModelAdmin[TrelloCard]
):
    """Admin para gestão de Cards Trello isolados por tenant."""

    list_display = [
        "name",
        "external_id",
        "atendimento",
        "list_sync",
        "created_at",
    ]
    search_fields = ["name", "external_id"]
    list_filter = ["list_sync__board"]
    readonly_fields = ["external_id", "url", "created_at", "updated_at"]


class TenantTrelloMemberAdmin(
    TenantModelAdminMixin, admin.ModelAdmin[TrelloMember]
):
    """Admin para gestão de Membros Trello isolados por tenant."""

    list_display = ["username", "full_name", "external_id", "atendente"]
    search_fields = ["username", "full_name", "external_id"]
    readonly_fields = ["external_id"]


class TenantTrelloWebhookEventAdmin(
    TenantModelAdminMixin, admin.ModelAdmin[TrelloWebhookEvent]
):
    """Admin para visualização de eventos de webhook Trello."""

    list_display = ["action_id", "model_type", "received_at"]
    search_fields = ["action_id", "model_type"]
    list_filter = ["model_type"]
    readonly_fields = ["action_id", "model_type", "payload", "received_at"]


# Registro no tenant_admin_site
tenant_admin_site.register(TrelloBoard, TenantTrelloBoardAdmin)
tenant_admin_site.register(TrelloList, TenantTrelloListAdmin)
tenant_admin_site.register(TrelloCard, TenantTrelloCardAdmin)
tenant_admin_site.register(TrelloMember, TenantTrelloMemberAdmin)
tenant_admin_site.register(TrelloWebhookEvent, TenantTrelloWebhookEventAdmin)

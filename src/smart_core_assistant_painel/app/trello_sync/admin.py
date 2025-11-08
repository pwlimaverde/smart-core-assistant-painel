"""
Configuração do painel de administração do Django para o aplicativo Trello Sync.

Este módulo registra os modelos do aplicativo trello_sync no painel
de administração do Django e personaliza a forma como eles são exibidos.
"""

from django.contrib import admin

from .models import (
    TrelloBoard,
    TrelloCard,
    TrelloList,
    TrelloMember,
    TrelloWebhookEvent,
)


@admin.register(TrelloBoard)
class TrelloBoardAdmin(admin.ModelAdmin[TrelloBoard]):
    """Admin para o modelo TrelloBoard."""

    list_display = [
        "id",
        "name",
        "external_id",
        "fluxo",
        "url",
        "created_at",
    ]
    search_fields = ["name", "external_id", "url", "fluxo__nome"]
    list_filter = ["fluxo", "created_at"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "metadata"]
    list_per_page = 25
    save_on_top = True


@admin.register(TrelloList)
class TrelloListAdmin(admin.ModelAdmin[TrelloList]):
    """Admin para o modelo TrelloList."""

    list_display = [
        "id",
        "name",
        "external_id",
        "board",
        "etapa",
        "position",
    ]
    search_fields = [
        "name",
        "external_id",
        "board__name",
        "etapa__nome",
    ]
    list_filter = ["board"]
    ordering = ["board__name", "position"]
    readonly_fields = ["metadata"]
    list_per_page = 25
    save_on_top = True


@admin.register(TrelloCard)
class TrelloCardAdmin(admin.ModelAdmin[TrelloCard]):
    """Admin para o modelo TrelloCard."""

    list_display = [
        "id",
        "name",
        "external_id",
        "atendimento",
        "list_sync",
        "url",
        "created_at",
    ]
    search_fields = [
        "name",
        "external_id",
        "atendimento__assunto",
        "list_sync__name",
    ]
    list_filter = ["list_sync__board", "created_at"]
    ordering = ["-created_at"]
    readonly_fields = ["metadata", "created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 25
    save_on_top = True


@admin.register(TrelloMember)
class TrelloMemberAdmin(admin.ModelAdmin[TrelloMember]):
    """Admin para o modelo TrelloMember."""

    list_display = [
        "id",
        "username",
        "full_name",
        "external_id",
        "atendente",
    ]
    search_fields = [
        "username",
        "full_name",
        "external_id",
        "atendente__nome",
    ]
    list_filter = ["atendente__departamento"]
    ordering = ["username"]
    list_per_page = 25
    save_on_top = True


@admin.register(TrelloWebhookEvent)
class TrelloWebhookEventAdmin(admin.ModelAdmin[TrelloWebhookEvent]):
    """Admin para o modelo TrelloWebhookEvent."""

    list_display = [
        "id",
        "action_id",
        "model_type",
        "received_at",
    ]
    search_fields = ["action_id", "model_type"]
    list_filter = ["model_type", "received_at"]
    ordering = ["-received_at"]
    readonly_fields = ["payload", "received_at"]
    date_hierarchy = "received_at"
    list_per_page = 25
    save_on_top = True

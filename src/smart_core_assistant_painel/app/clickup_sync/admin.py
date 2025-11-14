"""Configuração do Django Admin para o app clickup_sync.

Este módulo registra os models de integração com ClickUp no Django Admin,
permitindo visualização e gerenciamento via interface administrativa.
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import (
    ClickupList,
    ClickupMember,
    ClickupSpace,
    ClickupFolder,
    ClickupTask,
    ClickupWebhookEvent,
    ClickupStatus,
    ClickupCustomField,
)


@admin.register(ClickupSpace)
class ClickupSpaceAdmin(admin.ModelAdmin[ClickupSpace]):
    list_display = ("name", "external_id", "departamento_id")
    search_fields = ("name", "external_id")
    ordering = ("name",)


@admin.register(ClickupList)
class ClickupListAdmin(admin.ModelAdmin[ClickupList]):
    list_display = (
        "name",
        "external_id",
        "space_external_id",
        "fluxo_atendimento_id",
        "statuses_count",
    )
    search_fields = ("name", "external_id", "space_external_id")
    ordering = ("name",)

    def statuses_count(self, obj: ClickupList) -> int:  # type: ignore[override]
        """Quantidade de statuses mapeados para esta List.

        Comentário: ajuda a visualizar se o fluxo está com os
        `statuses` persistidos no mapeamento.
        """
        return (
            ClickupStatus.objects.filter(
                list_external_id=obj.external_id
            ).count()
        )


@admin.register(ClickupMember)
class ClickupMemberAdmin(admin.ModelAdmin[ClickupMember]):
    list_display = ("username", "external_id", "atendente_id")
    search_fields = ("username", "external_id")
    ordering = ("username",)


@admin.register(ClickupTask)
class ClickupTaskAdmin(admin.ModelAdmin[ClickupTask]):
    list_display = (
        "name",
        "external_id",
        "atendimento_id",
        "list_external_id",
    )
    search_fields = ("name", "external_id", "list_external_id")
    ordering = ("name",)


@admin.register(ClickupWebhookEvent)
class ClickupWebhookEventAdmin(admin.ModelAdmin[ClickupWebhookEvent]):
    list_display = ("event_type", "resource_id", "created_at")
    search_fields = ("event_type", "resource_id")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(ClickupStatus)
class ClickupStatusAdmin(admin.ModelAdmin[ClickupStatus]):
    """Admin para o mapeamento de EtapaFluxo ↔ Status da List."""

    list_display = (
        "status_name",
        "status_type",
        "color",
        "order_index",
        "etapa_fluxo_id",
        "list_external_id",
        "created_at",
    )
    search_fields = ("status_name", "list_external_id")
    list_filter = ("status_type", "list_external_id")
    ordering = ("list_external_id", "order_index")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")


@admin.register(ClickupFolder)
class ClickupFolderAdmin(admin.ModelAdmin[ClickupFolder]):
    list_display = (
        "name",
        "external_id",
        "space_external_id",
        "departamento_id",
    )
    search_fields = ("name", "external_id", "space_external_id")
    ordering = ("name",)


@admin.register(ClickupCustomField)
class ClickupCustomFieldAdmin(admin.ModelAdmin[ClickupCustomField]):
    """Admin para visualizar e gerenciar Custom Fields mapeados.

    Comentário (PT-BR): exibe identificação do campo, tipo e escopo
    (Workspace/List), permitindo auditoria das configurações usadas na
    sincronização de cards.
    """

    list_display = (
        "name",
        "field_id",
        "type",
        "scope_type",
        "scope_external_id",
        "created_at",
    )
    search_fields = ("name", "field_id", "scope_external_id")
    list_filter = ("scope_type", "type")
    ordering = ("name",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
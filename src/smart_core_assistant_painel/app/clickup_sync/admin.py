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
    ClickupTask,
    ClickupWebhookEvent,
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
    )
    search_fields = ("name", "external_id", "space_external_id")
    ordering = ("name",)


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
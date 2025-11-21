from typing import Any, cast

from django.contrib import admin
from django.db.models import QuerySet

from .models import EvolutionContact, EvolutionInstance, WhiteList


@admin.register(WhiteList)
class WhiteListAdmin(admin.ModelAdmin[WhiteList]):
    list_display = ("name", "phone_number", "active", "created_at")
    search_fields = ("name", "phone_number")
    list_filter = ("active",)
    ordering = ("name",)
    readonly_fields = ("created_at",)


@admin.register(EvolutionInstance)
class EvolutionInstanceAdmin(admin.ModelAdmin[EvolutionInstance]):
    list_display = (
        "name",
        "instance_id",
        "phone_number",
        "active",
        "created_at",
    )
    search_fields = ("name", "instance_id", "phone_number")
    list_filter = ("active",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)


@admin.register(EvolutionContact)
class EvolutionContactAdmin(admin.ModelAdmin[EvolutionContact]):
    list_display = (
        "contact",
        "instance",
        "jid",
        "lid",
        "addressing_mode",
        "active",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "jid",
        "lid",
        "contact__telefone",
        "contact__nome_contato",
        "instance__name",
        "instance__instance_id",
    )
    list_filter = ("addressing_mode", "active", "instance")
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("contact", "instance")
    autocomplete_fields = ("contact", "instance")

    def get_queryset(self, request: Any) -> QuerySet[EvolutionContact]:
        return cast(
            QuerySet[EvolutionContact],
            super()
            .get_queryset(request)
            .select_related("contact", "instance"),
        )

"""Registro de modelos no Tenant Admin Site.

E.1 expõe apenas `LeituraAtendimento` (status de leitura por atendente).
E.2 estenderá com `CampoPersonalizado` / `ValorCampoAtendimento`.
"""

from __future__ import annotations

from django.contrib import admin

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)

from .models import LeituraAtendimento


@admin.register(LeituraAtendimento, site=tenant_admin_site)
class LeituraAtendimentoAdmin(admin.ModelAdmin[LeituraAtendimento]):
    list_display = (
        "id",
        "atendimento_id",
        "atendente_id",
        "ultima_leitura_at",
    )
    list_filter = ("ultima_leitura_at",)
    search_fields = ("atendimento_id", "atendente_id")
    readonly_fields = ("ultima_leitura_at",)

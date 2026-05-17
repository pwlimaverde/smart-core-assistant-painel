"""Registro de modelos no Tenant Admin Site."""

from __future__ import annotations

from django.contrib import admin

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)

from .models import (
    CampoPersonalizado,
    LeituraAtendimento,
    ValorCampoAtendimento,
)


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


@admin.register(CampoPersonalizado, site=tenant_admin_site)
class CampoPersonalizadoAdmin(admin.ModelAdmin[CampoPersonalizado]):
    list_display = (
        "slug",
        "nome",
        "escopo",
        "fluxo_id",
        "tipo",
        "obrigatorio",
        "extrair_automaticamente",
        "mostrar_no_card",
        "ordem",
        "ativo",
    )
    list_filter = (
        "escopo",
        "tipo",
        "extrair_automaticamente",
        "ativo",
        "mostrar_no_card",
    )
    search_fields = ("slug", "nome", "descricao")
    readonly_fields = ("data_criacao", "data_atualizacao")
    ordering = ("ordem", "nome")
    fieldsets = (
        (
            "Identificação",
            {
                "fields": ("slug", "nome", "descricao", "escopo", "fluxo_id"),
            },
        ),
        (
            "Tipo e Opções",
            {
                "fields": ("tipo", "opcoes", "obrigatorio"),
            },
        ),
        (
            "Extração IA",
            {
                "fields": ("extrair_automaticamente", "extrair_hint"),
                "description": "Controla se o bot extrai este campo automaticamente.",
            },
        ),
        (
            "Exibição",
            {
                "fields": ("mostrar_no_card", "ordem", "ativo"),
            },
        ),
        (
            "Auditoria",
            {
                "fields": ("data_criacao", "data_atualizacao"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ValorCampoAtendimento, site=tenant_admin_site)
class ValorCampoAtendimentoAdmin(admin.ModelAdmin[ValorCampoAtendimento]):
    list_display = (
        "id",
        "atendimento_id",
        "campo",
        "valor",
        "origem",
        "confianca",
        "data_atualizacao",
    )
    list_filter = ("origem", "campo__escopo")
    search_fields = ("atendimento_id", "campo__slug", "campo__nome")
    readonly_fields = ("data_atualizacao",)
    raw_id_fields = ("campo",)

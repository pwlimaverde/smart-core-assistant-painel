"""Registro de modelos no Tenant Admin Site."""

from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)
from smart_core_assistant_painel.app.tenants.admin_mixins import (
    BaseTenantModelAdmin,
)

from .models import (
    CampoPersonalizado,
    Etiqueta,
    EtiquetaAtendimento,
    LeituraAtendimento,
    Nota,
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


@admin.register(Etiqueta, site=tenant_admin_site)
class EtiquetaAdmin(BaseTenantModelAdmin, admin.ModelAdmin[Etiqueta]):
    module_name = "atendimento"
    list_display = ("swatch", "nome", "cor", "descricao", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "descricao")
    readonly_fields = ("data_criacao",)
    ordering = ("nome",)

    @admin.display(description="")
    def swatch(self, obj: Etiqueta) -> str:
        return format_html(
            '<span style="display:inline-block;width:14px;height:14px;'
            'border-radius:50%;background:{};border:1px solid rgba(0,0,0,0.15);"></span>',
            obj.cor or "#a98f71",
        )


@admin.register(EtiquetaAtendimento, site=tenant_admin_site)
class EtiquetaAtendimentoAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[EtiquetaAtendimento]
):
    module_name = "atendimento"
    list_display = (
        "id",
        "atendimento_id",
        "etiqueta",
        "aplicada_em",
        "aplicada_por_id",
    )
    list_filter = ("etiqueta", "aplicada_em")
    search_fields = ("atendimento_id", "etiqueta__nome")
    readonly_fields = ("aplicada_em",)
    raw_id_fields = ("etiqueta",)


@admin.register(Nota, site=tenant_admin_site)
class NotaAdmin(BaseTenantModelAdmin, admin.ModelAdmin[Nota]):
    module_name = "atendimento"
    list_display = (
        "id",
        "atendimento_id",
        "texto_curto",
        "criado_por_id",
        "criado_em",
    )
    list_filter = ("criado_em",)
    search_fields = ("atendimento_id", "texto")
    readonly_fields = ("criado_em",)
    ordering = ("-criado_em",)

    @admin.display(description="Texto")
    def texto_curto(self, obj: Nota) -> str:
        if len(obj.texto) <= 60:
            return obj.texto
        return obj.texto[:60] + "…"

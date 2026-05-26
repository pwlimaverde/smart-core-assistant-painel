from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)
from smart_core_assistant_painel.app.tenants.admin_mixins import (
    BaseTenantModelAdmin,
)

from .models import (
    Atendimento,
    CampoPersonalizado,
    Etiqueta,
    EtiquetaAtendimento,
    Mensagem,
    Nota,
    ValorCampoAtendimento,
)


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


# ---------------------------------------------------------------------------
# Informação consolidada (campos personalizados, etiquetas, notas)
# ---------------------------------------------------------------------------


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

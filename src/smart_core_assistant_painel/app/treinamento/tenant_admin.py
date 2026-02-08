"""
Admin de tenant para modelos de treinamento.

Este módulo registra os modelos de treinamento no tenant_admin_site
para gestão isolada por tenant.
"""

from django.contrib import admin

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)
from smart_core_assistant_painel.app.tenants.admin_mixins import (
    BaseTenantModelAdmin,
)

from .models import Documento, QueryCompose, Treinamento


class TenantTreinamentoAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[Treinamento]
):
    """Admin para gestão de Treinamentos isolados por tenant."""

    module_name = "treinamento"

    list_display = (
        "tag",
        "grupo",
        "treinamento_finalizado",
        "treinamento_vetorizado",
        "data_criacao",
    )
    list_filter = (
        "treinamento_finalizado",
        "treinamento_vetorizado",
        "tag",
        "grupo",
    )
    search_fields = ("tag", "grupo", "conteudo")
    readonly_fields = ("data_criacao", "data_atualizacao")


class TenantDocumentoAdmin(BaseTenantModelAdmin, admin.ModelAdmin[Documento]):
    """Admin para gestão de Documentos de treinamento isolados por tenant."""

    module_name = "treinamento"

    list_display = ("id", "treinamento", "ordem", "data_criacao")
    list_filter = ("treinamento", "data_criacao")
    search_fields = ("conteudo",)
    readonly_fields = ("data_criacao", "embedding")


class TenantQueryComposeAdmin(
    BaseTenantModelAdmin, admin.ModelAdmin[QueryCompose]
):
    """Admin para gestão de Query Compose (Intenções) isoladas por tenant."""

    module_name = "treinamento"

    list_display = ("tag", "grupo", "descricao", "created_at")
    list_filter = ("grupo", "created_at")
    search_fields = ("tag", "grupo", "descricao", "exemplo")
    readonly_fields = ("created_at", "updated_at", "embedding")


# Registro no tenant_admin_site
tenant_admin_site.register(Treinamento, TenantTreinamentoAdmin)
tenant_admin_site.register(Documento, TenantDocumentoAdmin)
tenant_admin_site.register(QueryCompose, TenantQueryComposeAdmin)

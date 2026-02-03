"""
Admin de tenant para modelos do clientes.

Este módulo registra os modelos do clientes no tenant_admin_site
para gestão isolada por tenant.
"""

from typing import cast

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)
from smart_core_assistant_painel.app.tenants.admin_mixins import (
    BaseTenantModelAdmin,
)

from .models import Cliente, Contato


class TenantContatoAdmin(BaseTenantModelAdmin, admin.ModelAdmin[Contato]):
    """Admin para gestão de Contatos isolados por tenant."""

    module_name = "clientes"

    list_display = [
        "telefone",
        "nome_contato",
        "email",
        "nome_perfil_whatsapp",
        "data_cadastro",
        "ultima_interacao",
    ]
    list_filter = ["ativo", "data_cadastro"]
    search_fields = ["telefone", "nome_contato", "email"]
    readonly_fields = ["data_cadastro", "ultima_interacao"]


class TenantClienteAdmin(BaseTenantModelAdmin, admin.ModelAdmin[Cliente]):
    """Admin para gestão de Clientes isolados por tenant."""

    module_name = "clientes"

    list_display = [
        "nome_fantasia",
        "razao_social",
        "tipo",
        "cnpj",
        "cpf",
        "cidade",
        "uf",
        "ativo",
    ]
    list_filter = ["ativo", "tipo", "uf"]
    search_fields = [
        "nome_fantasia",
        "razao_social",
        "cnpj",
        "cpf",
        "cidade",
        "uf",
    ]
    readonly_fields = ["data_cadastro", "ultima_atualizacao"]
    filter_horizontal = ["contatos"]

    @admin.display(description="Total de Contatos")
    def total_contatos(self, obj: Cliente) -> int:
        """Retorna o número total de contatos vinculados ao cliente."""
        return cast(int, obj.contatos.count())

    def get_queryset(self, request: HttpRequest) -> QuerySet[Cliente]:
        """Otimiza as consultas carregando contatos relacionados."""
        return super().get_queryset(request).prefetch_related("contatos")


# Registro no tenant_admin_site
tenant_admin_site.register(Contato, TenantContatoAdmin)
tenant_admin_site.register(Cliente, TenantClienteAdmin)

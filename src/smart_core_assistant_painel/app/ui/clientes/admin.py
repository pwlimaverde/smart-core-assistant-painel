"""Configuração do painel de administração do Django para o aplicativo Clientes.

Este módulo registra os modelos do aplicativo Clientes no painel de administração
do Django e personaliza a forma como eles são exibidos e gerenciados.
"""

import csv
from typing import cast

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse

from .models import Cliente, Contato


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin[Contato]):
    """Admin para o modelo Contato."""

    list_display = [
        "telefone",
        "nome_contato",
        "nome_perfil_whatsapp",
        "data_cadastro",
        "ultima_interacao",
        "total_atendimentos",
        "total_clientes",
    ]
    list_filter = ["data_cadastro", "ultima_interacao", "ativo"]
    search_fields = ["telefone", "nome_contato", "nome_perfil_whatsapp"]
    readonly_fields = ["data_cadastro", "ultima_interacao"]
    ordering = ["-ultima_interacao"]
    list_per_page = 25
    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "telefone",
                    "nome_contato",
                    "nome_perfil_whatsapp",
                    "ativo",
                )
            },
        ),
        ("Datas", {"fields": ("data_cadastro", "ultima_interacao")}),
        ("Metadados", {"fields": ("metadados",), "classes": ("collapse",)}),
    )

    @admin.display(description="Total de Atendimentos")
    def total_atendimentos(self, obj: Contato) -> int:
        """Retorna o número total de atendimentos do contato."""
        return cast(int, getattr(obj, "atendimentos").count())

    @admin.display(description="Total de Clientes")
    def total_clientes(self, obj: Contato) -> int:
        """Retorna o número total de clientes vinculados ao contato."""
        return cast(
            int,
            getattr(obj, "clientes").count() if hasattr(obj, "clientes") else 0,
        )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Contato]:
        """Otimiza as consultas carregando clientes relacionados."""
        return super().get_queryset(request).prefetch_related("clientes")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin[Cliente]):
    """Admin para o modelo Cliente."""

    list_display = [
        "nome_fantasia",
        "razao_social",
        "tipo",
        "cnpj",
        "cpf",
        "cidade",
        "uf",
        "ramo_atividade",
        "total_contatos",
        "ativo",
        "data_cadastro",
    ]
    list_filter = [
        "ativo",
        "tipo",
        "uf",
        "cidade",
        "ramo_atividade",
        "data_cadastro",
        "ultima_atualizacao",
    ]
    search_fields = [
        "nome_fantasia",
        "razao_social",
        "cnpj",
        "cpf",
        "telefone",
        "cidade",
        "ramo_atividade",
    ]
    readonly_fields = [
        "data_cadastro",
        "ultima_atualizacao",
        "get_endereco_completo_display",
        "total_contatos",
    ]
    filter_horizontal = ["contatos"]
    list_per_page = 25
    save_on_top = True
    actions = ["marcar_como_ativa", "marcar_como_inativa", "exportar_dados"]

    @admin.display(description="Total de Contatos")
    def total_contatos(self, obj: Cliente) -> int:
        """Retorna o número total de contatos vinculados ao cliente."""
        return obj.contatos.count()

    @admin.display(description="Endereço Completo")
    def get_endereco_completo_display(self, obj: Cliente) -> str:
        """Exibe o endereço completo formatado no admin."""
        return obj.get_endereco_completo() or "-"

    @admin.action(description="Marcar clientes selecionados como ativos")
    def marcar_como_ativa(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> None:
        """Marca os clientes selecionados como ativos."""
        queryset.update(ativo=True)
        self.message_user(request, f"{queryset.count()} clientes marcados como ativos.")

    @admin.action(description="Marcar clientes selecionados como inativos")
    def marcar_como_inativa(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> None:
        """Marca os clientes selecionados como inativos."""
        queryset.update(ativo=False)
        self.message_user(request, f"{queryset.count()} clientes marcados como inativos.")

    @admin.action(description="Exportar dados dos clientes selecionados (CSV)")
    def exportar_dados(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> HttpResponse:
        """Exporta os dados dos clientes selecionados em formato CSV."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="clientes.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Nome Fantasia",
                "Razão Social",
                "Tipo",
                "CNPJ",
                "CPF",
                "Telefone",
                "Site",
                "Ramo de Atividade",
                "CEP",
                "Endereço Completo",
                "Cidade",
                "UF",
                "País",
                "Total de Contatos",
                "Ativo",
                "Data de Cadastro",
            ]
        )

        for cliente in queryset.select_related().prefetch_related("contatos"):
            tipo_choices = {
                "fisica": "Pessoa Física",
                "juridica": "Pessoa Jurídica",
            }
            tipo_display = (
                tipo_choices.get(cliente.tipo, "") if cliente.tipo else ""
            )
            writer.writerow(
                [
                    cliente.nome_fantasia,
                    cliente.razao_social or "",
                    tipo_display,
                    cliente.cnpj or "",
                    cliente.cpf or "",
                    cliente.telefone or "",
                    cliente.site or "",
                    cliente.ramo_atividade or "",
                    cliente.cep or "",
                    cliente.get_endereco_completo(),
                    cliente.cidade or "",
                    cliente.uf or "",
                    cliente.pais or "",
                    cliente.contatos.count(),
                    "Sim" if cliente.ativo else "Não",
                    cliente.data_cadastro.strftime("%d/%m/%Y %H:%M")
                    if cliente.data_cadastro
                    else "",
                ]
            )

        self.message_user(
            request,
            f"Dados de {queryset.count()} clientes exportados com sucesso.",
        )
        return response

    def get_queryset(self, request: HttpRequest) -> QuerySet[Cliente]:
        """Otimiza as consultas carregando contatos relacionados."""
        return super().get_queryset(request).prefetch_related("contatos")
"""Configuração do painel de administração do Django para o aplicativo Operacional.

Este módulo registra os modelos do aplicativo Operacional no painel de administração
do Django e personaliza a forma como eles são exibidos e gerenciados.
"""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import AtendenteHumano, Departamento


@admin.register(AtendenteHumano)
class AtendenteHumanoAdmin(admin.ModelAdmin[AtendenteHumano]):
    """Admin para o modelo AtendenteHumano."""

    list_display = [
        "id",
        "nome",
        "cargo",
        "telefone",
        "email",
        "ativo",
        "disponivel",
        "get_atendimentos_ativos",
        "max_atendimentos_simultaneos",
        "ultima_atividade",
    ]
    search_fields = [
        "nome",
        "cargo",
        "telefone",
        "email",
        "departamento__nome",
    ]
    list_filter = ["ativo", "disponivel", "cargo", "data_cadastro"]
    readonly_fields = [
        "data_cadastro",
        "ultima_atividade",
        "get_atendimentos_ativos",
    ]
    ordering = ["nome"]
    fieldsets = (
        (
            "Informações Pessoais",
            {"fields": ("nome", "cargo", "departamento")},
        ),
        ("Contatos", {"fields": ("telefone", "email")}),
        ("Sistema", {"fields": ("usuario_sistema", "ativo", "disponivel")}),
        (
            "Capacidades",
            {"fields": ("max_atendimentos_simultaneos", "especialidades")},
        ),
        (
            "Horários",
            {"fields": ("horario_trabalho",), "classes": ("collapse",)},
        ),
        ("Metadados", {"fields": ("metadados",), "classes": ("collapse",)}),
        (
            "Informações do Sistema",
            {
                "fields": (
                    "data_cadastro",
                    "ultima_atividade",
                    "get_atendimentos_ativos",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    list_per_page = 25
    save_on_top = True
    actions = ["marcar_como_disponivel", "marcar_como_indisponivel"]

    @admin.display(description="Atendimentos Ativos")
    def get_atendimentos_ativos(self, obj: AtendenteHumano) -> int:
        """Retorna a quantidade de atendimentos ativos do atendente."""
        return obj.get_atendimentos_ativos() if obj else 0

    @admin.action(description="Marcar atendentes selecionados como disponíveis")
    def marcar_como_disponivel(
        self, request: HttpRequest, queryset: QuerySet[AtendenteHumano]
    ) -> None:
        """Marca os atendentes selecionados como disponíveis."""
        queryset.update(disponivel=True)
        self.message_user(
            request,
            f"{queryset.count()} atendentes marcados como disponíveis.",
        )

    @admin.action(description="Marcar atendentes selecionados como indisponíveis")
    def marcar_como_indisponivel(
        self, request: HttpRequest, queryset: QuerySet[AtendenteHumano]
    ) -> None:
        """Marca os atendentes selecionados como indisponíveis."""
        queryset.update(disponivel=False)
        self.message_user(
            request,
            f"{queryset.count()} atendentes marcados como indisponíveis.",
        )


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin[Departamento]):
    """Admin para o modelo Departamento."""

    list_display = [
        "id",
        "nome",
        "telefone_instancia",
        "api_key",
        "instance_id",
        "ativo",
        "data_criacao",
    ]
    search_fields = ["nome", "telefone_instancia", "api_key", "instance_id"]
    list_filter = ["ativo", "data_criacao", "ultima_validacao"]
    ordering = ["nome"]
    readonly_fields = ["data_criacao"]
    list_per_page = 25
    save_on_top = True
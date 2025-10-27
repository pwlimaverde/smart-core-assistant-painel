"""Configuração do painel de administração do Django para o aplicativo Operacional.

Este módulo registra os modelos do aplicativo Operacional no painel de administração
do Django e personaliza a forma como eles são exibidos e gerenciados.
"""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import AtendenteHumano, Departamento, WhatsAppInstance


@admin.register(AtendenteHumano)
class AtendenteHumanoAdmin(admin.ModelAdmin[AtendenteHumano]):
    """Admin para o modelo AtendenteHumano."""

    list_display = [
        "id",
        "nome",
        "cargo",
        "departamento",
        "telefone",
        "email",
        "ativo",
        "disponivel",
        "get_atendimentos_ativos",
        "max_atendimentos_simultaneos",
        "data_ultima_atribuicao",
        "ultima_atividade",
    ]
    search_fields = [
        "nome",
        "cargo",
        "telefone",
        "email",
        "departamento__nome",
    ]
    list_filter = ["ativo", "disponivel", "cargo", "departamento", "data_cadastro"]
    readonly_fields = [
        "data_cadastro",
        "ultima_atividade",
        "get_atendimentos_ativos",
        "data_ultima_atribuicao",
    ]
    ordering = ["nome"]
    fieldsets = (
        (
            "Informações Pessoais",
            {"fields": ("nome", "cargo", "departamento")},
        ),
        ("Contatos", {"fields": ("telefone", "email")}),
        ("Sistema", {"fields": ("usuario", "usuario_sistema", "ativo", "disponivel")}),
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
                    "data_ultima_atribuicao",
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

    @admin.action(
        description="Marcar atendentes selecionados como disponíveis"
    )
    def marcar_como_disponivel(
        self, request: HttpRequest, queryset: QuerySet[AtendenteHumano]
    ) -> None:
        """Marca os atendentes selecionados como disponíveis."""
        queryset.update(disponivel=True)
        self.message_user(
            request,
            f"{queryset.count()} atendentes marcados como disponíveis.",
        )

    @admin.action(
        description="Marcar atendentes selecionados como indisponíveis"
    )
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
        "slug",
        "ativo",
        "data_criacao",
    ]
    search_fields = ["nome", "slug"]
    list_filter = ["ativo", "data_criacao"]
    ordering = ["nome"]
    readonly_fields = ["data_criacao"]
    list_per_page = 25
    save_on_top = True
    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("nome", "slug", "ativo")},
        ),
        (
            "Detalhes",
            {"fields": ("descricao",)},
        ),
        (
            "Configurações",
            {"fields": ("configuracoes",), "classes": ("collapse",)},
        ),
        (
            "Metadados",
            {"fields": ("metadados",), "classes": ("collapse",)},
        ),
        (
            "Informações do Sistema",
            {
                "fields": ("data_criacao",),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(WhatsAppInstance)
class WhatsAppInstanceAdmin(admin.ModelAdmin[WhatsAppInstance]):
    """Admin para o modelo WhatsAppInstance."""

    list_display = [
        "id",
        "get_tipo_instancia_display",
        "phone_number",
        "instance_id",
        "get_responsavel_display",
        "provider",
        "ativo",
        "data_criacao",
        "ultima_validacao",
    ]
    search_fields = [
        "phone_number",
        "instance_id",
        "departamento__nome",
        "owner__nome",
    ]
    list_filter = [
        "ativo",
        "provider",
        "departamento",
        "data_criacao",
        "ultima_validacao",
    ]
    readonly_fields = [
        "data_criacao",
        "ultima_validacao",
        "get_tipo_instancia_display",
        "get_responsavel_display",
    ]
    ordering = ["-data_criacao"]
    list_per_page = 25
    save_on_top = True
    fieldsets = (
        (
            "Identificação",
            {"fields": ("phone_number", "instance_id", "provider")},
        ),
        (
            "Tipo de Instância",
            {
                "fields": ("departamento", "owner"),
                "description": "Uma instância deve estar vinculada a UM departamento OU UM atendente, nunca ambos."
            },
        ),
        (
            "Credenciais",
            {"fields": ("api_key",)},
        ),
        (
            "Status",
            {"fields": ("ativo",)},
        ),
        (
            "Informações Resumidas",
            {
                "fields": (
                    "get_tipo_instancia_display",
                    "get_responsavel_display",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadados",
            {"fields": ("metadados",), "classes": ("collapse",)},
        ),
        (
            "Informações do Sistema",
            {
                "fields": (
                    "data_criacao",
                    "ultima_validacao",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    actions = ["ativar_instancias", "desativar_instancias"]

    @admin.action(
        description="Ativar instâncias selecionadas"
    )
    def ativar_instancias(
        self, request: HttpRequest, queryset: QuerySet[WhatsAppInstance]
    ) -> None:
        """Ativa as instâncias selecionadas."""
        queryset.update(ativo=True)
        self.message_user(
            request,
            f"{queryset.count()} instâncias ativadas.",
        )

    @admin.action(
        description="Desativar instâncias selecionadas"
    )
    def desativar_instancias(
        self, request: HttpRequest, queryset: QuerySet[WhatsAppInstance]
    ) -> None:
        """Desativa as instâncias selecionadas."""
        queryset.update(ativo=False)
        self.message_user(
            request,
            f"{queryset.count()} instâncias desativadas.",
        )

    @admin.display(description="Tipo", ordering="tipo_instancia")
    def get_tipo_instancia_display(self, obj: WhatsAppInstance) -> str:
        """Exibe o tipo da instância de forma amigável."""
        tipo = obj.tipo_instancia
        if tipo == "departamental":
            return "🏢 Departamental"
        elif tipo == "individual":
            return "👤 Individual"
        return "❓ Desconhecido"

    @admin.display(description="Responsável", ordering="responsavel_principal")
    def get_responsavel_display(self, obj: WhatsAppInstance) -> str:
        """Exibe o responsável principal da instância."""
        responsavel = obj.responsavel_principal
        if not responsavel:
            return "—"

        if isinstance(responsavel, Departamento):
            return f"🏢 {responsavel.nome}"
        elif isinstance(responsavel, AtendenteHumano):
            return f"👤 {responsavel.nome} ({responsavel.cargo})"
        return str(responsavel)

    def get_form(self, request, obj=None, **kwargs):
        """Personaliza o formulário para ajudar na escolha do tipo de instância."""
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.pk:
            # Se está editando um objeto existente
            if obj.departamento:
                form.base_fields['owner'].widget.attrs['placeholder'] = "Não aplicável para instâncias departamentais"
                form.base_fields['owner'].help_text = "Esta instância é departamental. Para mudar, primeiro remova o departamento."
            elif obj.owner:
                form.base_fields['departamento'].widget.attrs['placeholder'] = "Não aplicável para instâncias individuais"
                form.base_fields['departamento'].help_text = "Esta instância é individual. Para mudar, primeiro remova o atendente."
        else:
            # Se está criando um novo objeto
            form.base_fields['departamento'].help_text = "Selecione um departamento para instância departamental OU deixe em branco para instância individual"
            form.base_fields['owner'].help_text = "Selecione um atendente para instância individual OU deixe em branco para instância departamental"

        return form

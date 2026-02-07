"""Configuração do painel de administração do Django para o aplicativo Operacional.

Este módulo registra os modelos do aplicativo Operacional no painel de administração
do Django e personaliza a forma como eles são exibidos e gerenciados.
"""

from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from smart_core_assistant_painel.app.atendimentos.models import (
    MovimentoFluxo,
)

from .models import (
    AppInstance,
    Atendente,
    Departamento,
    EtapaFluxo,
    FluxoAtendimento,
)


# Desregistrado do admin principal - disponível apenas no tenant_admin
# @admin.register(Atendente)
class AtendenteAdmin(admin.ModelAdmin[Atendente]):
    """Admin para o modelo Atendente."""

    list_display = [
        "id",
        "nome",
        "cargo",
        "departamento",
        "fluxo",
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
        "fluxo__nome",
    ]
    list_filter = [
        "ativo",
        "disponivel",
        "cargo",
        "departamento",
        "fluxo",
        "data_cadastro",
    ]
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
            {"fields": ("nome", "cargo", "departamento", "fluxo")},
        ),
        ("Contatos", {"fields": ("telefone", "email")}),
        (
            "Sistema",
            {"fields": ("usuario", "usuario_sistema", "ativo", "disponivel")},
        ),
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
    def get_atendimentos_ativos(self, obj: Atendente) -> int:
        """Retorna a quantidade de atendimentos ativos do atendente."""
        return obj.get_atendimentos_ativos() if obj else 0

    @admin.action(
        description="Marcar atendentes selecionados como disponíveis"
    )
    def marcar_como_disponivel(
        self, request: HttpRequest, queryset: QuerySet[Atendente]
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
        self, request: HttpRequest, queryset: QuerySet[Atendente]
    ) -> None:
        """Marca os atendentes selecionados como indisponíveis."""
        queryset.update(disponivel=False)
        self.message_user(
            request,
            f"{queryset.count()} atendentes marcados como indisponíveis.",
        )


# Compatibilidade retroativa com testes/nomes antigos
# Comentario: exporta alias para manter referencias existentes nos testes.
AtendenteHumanoAdmin = AtendenteAdmin


# Desregistrado do admin principal - disponível apenas no tenant_admin
# @admin.register(Departamento)
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


# Desregistrado do admin principal - disponível apenas no tenant_admin
# @admin.register(AppInstance)
class AppInstanceAdmin(admin.ModelAdmin[AppInstance]):
    list_display = [
        "id",
        "channel",
        "api_key",
        "display_name",
        "departamento",
        "owner",
        "active",
        "created_at",
    ]
    search_fields = [
        "api_key",
        "display_name",
        "departamento__nome",
        "owner__nome",
    ]
    list_filter = ["active", "channel", "departamento", "created_at"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
    list_per_page = 25


# Desregistrado do admin principal - disponível apenas no tenant_admin
# @admin.register(FluxoAtendimento)
class FluxoAtendimentoAdmin(admin.ModelAdmin[FluxoAtendimento]):
    """Admin para o modelo FluxoAtendimento."""

    class FluxoAtendimentoAdminForm(forms.ModelForm):
        """Form do admin permitindo múltiplos fluxos por departamento.

        Comentário: remove a validação 1:1; agora é possível
        criar vários fluxos no mesmo departamento.
        """

        class Meta:
            model = FluxoAtendimento
            fields = "__all__"

        # Sem validação adicional: relação passa a ser 1:N.

    form = FluxoAtendimentoAdminForm

    list_display = [
        "id",
        "nome",
        "departamento",
        "ativo",
        "total_etapas",
        "data_criacao",
        "data_atualizacao",
    ]
    search_fields = ["nome", "departamento__nome", "descricao"]
    list_filter = ["ativo", "departamento", "data_criacao"]
    readonly_fields = ["data_criacao", "data_atualizacao", "total_etapas"]
    ordering = ["departamento__nome", "nome"]
    list_per_page = 25
    save_on_top = True
    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("departamento", "nome", "ativo")},
        ),
        (
            "Detalhes",
            {"fields": ("descricao",)},
        ),
        (
            "Informações do Sistema",
            {
                "fields": (
                    "data_criacao",
                    "data_atualizacao",
                    "total_etapas",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    actions = ["ativar_fluxos", "desativar_fluxos"]

    @admin.display(description="Etapas")
    def total_etapas(self, obj: FluxoAtendimento) -> int:
        """Retorna o número total de etapas no fluxo."""
        return obj.etapas.count() if obj else 0

    @admin.action(description="Ativar fluxos selecionados")
    def ativar_fluxos(
        self, request: HttpRequest, queryset: QuerySet[FluxoAtendimento]
    ) -> None:
        """Ativa os fluxos selecionados."""
        queryset.update(ativo=True)
        self.message_user(
            request,
            f"{queryset.count()} fluxos ativados.",
        )

    @admin.action(description="Desativar fluxos selecionados")
    def desativar_fluxos(
        self, request: HttpRequest, queryset: QuerySet[FluxoAtendimento]
    ) -> None:
        """Desativa os fluxos selecionados."""
        queryset.update(ativo=False)
        self.message_user(
            request,
            f"{queryset.count()} fluxos desativados.",
        )


# Desregistrado do admin principal - disponível apenas no tenant_admin
# @admin.register(EtapaFluxo)
class EtapaFluxoAdmin(admin.ModelAdmin[EtapaFluxo]):
    """Admin para o modelo EtapaFluxo."""

    list_display = [
        "id",
        "nome",
        "fluxo",
        "ordem",
        "tipo_etapa",
        "cor_display",
        "permite_atribuicao",
        "automatico",
        "ativo",
        "data_criacao",
    ]
    search_fields = [
        "nome",
        "fluxo__nome",
        "fluxo__departamento__nome",
        "descricao",
    ]
    list_filter = [
        "tipo_etapa",
        "permite_atribuicao",
        "automatico",
        "ativo",
        "fluxo__departamento",
        "data_criacao",
    ]
    readonly_fields = ["data_criacao", "cor_display"]
    ordering = ["fluxo__departamento__nome", "fluxo__nome", "ordem"]
    list_per_page = 25
    save_on_top = True
    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("fluxo", "nome", "ordem", "cor")},
        ),
        (
            "Configurações",
            {
                "fields": (
                    "tipo_etapa",
                    "permite_atribuicao",
                    "automatico",
                    "ativo",
                )
            },
        ),
        (
            "Detalhes",
            {"fields": ("descricao",)},
        ),
        (
            "Regras e Validações",
            {
                "fields": ("regras_transicao", "campos_obrigatorios"),
                "classes": ("collapse",),
            },
        ),
        (
            "Informações do Sistema",
            {
                "fields": (
                    "data_criacao",
                    "cor_display",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    actions = ["ativar_etapas", "desativar_etapas"]

    @admin.display(description="Cor", ordering="cor")
    def cor_display(self, obj: EtapaFluxo) -> str:
        """Exibe a cor como um quadrado colorido."""
        if obj.cor:
            return f'<span style="display: inline-block; width: 20px; height: 20px; background-color: {obj.cor}; border: 1px solid #ccc;"></span> {obj.cor}'
        return "-"

    cor_display.allow_tags = True

    @admin.action(description="Ativar etapas selecionadas")
    def ativar_etapas(
        self, request: HttpRequest, queryset: QuerySet[EtapaFluxo]
    ) -> None:
        """Ativa as etapas selecionadas."""
        queryset.update(ativo=True)
        self.message_user(
            request,
            f"{queryset.count()} etapas ativadas.",
        )

    @admin.action(description="Desativar etapas selecionadas")
    def desativar_etapas(
        self, request: HttpRequest, queryset: QuerySet[EtapaFluxo]
    ) -> None:
        """Desativa as etapas selecionadas."""
        queryset.update(ativo=False)
        self.message_user(
            request,
            f"{queryset.count()} etapas desativadas.",
        )


# Desregistrado do admin principal - disponível apenas no tenant_admin
# @admin.register(MovimentoFluxo)
class MovimentoFluxoAdmin(admin.ModelAdmin[MovimentoFluxo]):
    """Admin para o modelo MovimentoFluxo."""

    list_display = [
        "id",
        "atendimento",
        "get_origem_destino",
        "get_atendentes",
        "automatico",
        "duracao_formatada",
        "data_movimento",
    ]
    search_fields = [
        "atendimento__id",
        "atendimento__contato__telefone",
        "atendimento__contato__nome_contato",
        "motivo",
    ]
    list_filter = [
        "automatico",
        "etapa_destino__tipo_etapa",
        "etapa_destino__fluxo__departamento",
        "data_movimento",
    ]
    readonly_fields = ["data_movimento", "duracao_formatada"]
    ordering = ["-data_movimento"]
    list_per_page = 25
    date_hierarchy = "data_movimento"

    fieldsets = (
        (
            "Informações do Movimento",
            {"fields": ("atendimento", "etapa_origem", "etapa_destino")},
        ),
        (
            "Atribuição",
            {"fields": ("atendente_origem", "atendente_destino")},
        ),
        (
            "Detalhes",
            {"fields": ("motivo", "automatico", "duracao_formatada")},
        ),
        (
            "Dados Complementares",
            {"fields": ("dados_complementares",), "classes": ("collapse",)},
        ),
        (
            "Informações do Sistema",
            {
                "fields": ("data_movimento",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Origem → Destino")
    def get_origem_destino(self, obj: MovimentoFluxo) -> str:
        """Retorna a movimentação de forma amigável."""
        origem = obj.etapa_origem.nome if obj.etapa_origem else "Novo"
        destino = (
            obj.etapa_destino.nome if obj.etapa_destino else "Desconhecido"
        )
        return f"{origem} → {destino}"

    @admin.display(description="Atendentes")
    def get_atendentes(self, obj: MovimentoFluxo) -> str:
        """Retorna os atendentes envolvidos na movimentação."""
        partes = []
        if obj.atendente_origem:
            partes.append(f"De: {obj.atendente_origem.nome}")
        if obj.atendente_destino:
            partes.append(f"Para: {obj.atendente_destino.nome}")
        return " | ".join(partes) if partes else "-"

    @admin.display(description="Duração")
    def duracao_formatada(self, obj: MovimentoFluxo) -> str:
        """Retorna a duração formatada."""
        if obj.duracao_segundos:
            if obj.duracao_segundos < 60:
                return f"{obj.duracao_segundos}s"
            elif obj.duracao_segundos < 3600:
                minutos = obj.duracao_segundos // 60
                segundos = obj.duracao_segundos % 60
                return f"{minutos}m {segundos}s"
            else:
                horas = obj.duracao_segundos // 3600
                minutos = (obj.duracao_segundos % 3600) // 60
                return f"{horas}h {minutos}m"
        return "-"

    def get_queryset(self, request: HttpRequest) -> QuerySet[MovimentoFluxo]:
        """Otimiza a consulta com selects relacionados."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "atendimento",
                "atendimento__contato",
                "etapa_origem",
                "etapa_destino",
                "atendente_origem",
                "atendente_destino",
            )
        )

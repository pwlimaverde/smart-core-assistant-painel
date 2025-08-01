from typing import TYPE_CHECKING

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

if TYPE_CHECKING:
    from typing import Any

from .models import (
    AtendenteHumano,
    Atendimento,
    Cliente,
    Contato,
    FluxoConversa,
    Mensagem,
    Treinamentos,
)


@admin.register(Treinamentos)
class TreinamentosAdmin(admin.ModelAdmin):  # type: ignore
    # Campos a serem exibidos na lista
    list_display = [
        "id",
        "tag",
        "grupo",
        "treinamento_finalizado",
        "get_documentos_preview",
    ]

    # Campos que podem ser pesquisados
    search_fields = [
        "tag",
    ]

    # Ordenação padrão
    ordering = ["id"]

    # Organização dos campos no formulário
    fieldsets = (
        (
            "Informações do Treinamento",
            {
                "fields": ("tag", "grupo", "treinamento_finalizado", "_documentos"),
                "classes": ("wide",),
            },
        ),
    )

    # Função para exibir preview do documentos JSON
    @admin.display(description="Preview do Documento", ordering="_documentos")
    def get_documentos_preview(self, obj: Treinamentos) -> str:
        """Retorna uma prévia do documentos JSON limitada a 100 caracteres"""
        if obj and obj._documentos:
            try:
                # Se for um dict, converte para string
                if isinstance(obj._documentos, dict):
                    preview = str(obj._documentos)[:1000]
                else:
                    preview = str(obj._documentos)[:1000]
                return preview + "..." if len(str(obj._documentos)) > 1000 else preview
            except Exception:
                return "Erro ao exibir documentos"
        return "Documento vazio"

    # Configurações adicionais
    list_per_page = 25
    save_on_top = True


@admin.register(AtendenteHumano)
class AtendenteHumanoAdmin(admin.ModelAdmin):  # type: ignore
    # Campos a serem exibidos na lista
    list_display = [
        "id",
        "nome",
        "cargo",
        "departamento",
        "telefone",
        "ativo",
        "disponivel",
        "get_atendimentos_ativos",
        "max_atendimentos_simultaneos",
        "ultima_atividade",
    ]

    # Campos que podem ser pesquisados
    search_fields = [
        "nome",
        "cargo",
        "departamento",
        "telefone",
        "email",
    ]

    # Filtros laterais
    list_filter = [
        "ativo",
        "disponivel",
        "departamento",
        "cargo",
        "data_cadastro",
    ]

    # Campos somente leitura
    readonly_fields = [
        "data_cadastro",
        "ultima_atividade",
        "get_atendimentos_ativos",
    ]

    # Ordenação padrão
    ordering = ["nome"]

    # Organização dos campos no formulário
    fieldsets = (
        (
            "Informações Pessoais",
            {"fields": ("nome", "cargo", "departamento"), "classes": ("wide",)},
        ),
        ("Contatos", {"fields": ("telefone", "email"), "classes": ("wide",)}),
        (
            "Sistema",
            {
                "fields": ("usuario_sistema", "ativo", "disponivel"),
            },
        ),
        (
            "Capacidades",
            {
                "fields": ("max_atendimentos_simultaneos", "especialidades"),
            },
        ),
        ("Horários", {"fields": ("horario_trabalho",), "classes": ("collapse",)}),
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

    # Função para exibir quantidade de atendimentos ativos
    @admin.display(description="Atendimentos Ativos")
    def get_atendimentos_ativos(self, obj: AtendenteHumano) -> int:
        """Retorna a quantidade de atendimentos ativos do atendente"""
        if obj:
            return obj.get_atendimentos_ativos()
        return 0

    # Configurações adicionais
    list_per_page = 25
    save_on_top = True

    # Actions customizadas
    actions = ["marcar_como_disponivel", "marcar_como_indisponivel"]

    @admin.action(description="Marcar atendentes selecionados como disponíveis")
    def marcar_como_disponivel(
        self, request: HttpRequest, queryset: QuerySet[AtendenteHumano]
    ) -> None:
        queryset.update(disponivel=True)
        self.message_user(
            request, f"{queryset.count()} atendentes marcados como disponíveis."
        )

    @admin.action(description="Marcar atendentes selecionados como indisponíveis")
    def marcar_como_indisponivel(
        self, request: HttpRequest, queryset: QuerySet[AtendenteHumano]
    ) -> None:
        queryset.update(disponivel=False)
        self.message_user(
            request, f"{queryset.count()} atendentes marcados como indisponíveis."
        )


# =====================================================================
# ADMINS PARA O SISTEMA DE CHATBOT
# =====================================================================


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):  # type: ignore
    list_display = [
        "telefone",
        "nome_contato",
        "nome_perfil_whatsapp",
        "ultima_interacao",
        "data_cadastro",
        "total_atendimentos",
        "total_clientes",
    ]
    list_filter = ["data_cadastro", "ultima_interacao", "ativo"]
    search_fields = ["telefone", "nome_contato", "nome_perfil_whatsapp"]
    readonly_fields = ["data_cadastro", "ultima_interacao"]

    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("telefone", "nome_contato", "nome_perfil_whatsapp", "ativo")},
        ),
        ("Datas", {"fields": ("data_cadastro", "ultima_interacao")}),
        ("Metadados", {"fields": ("metadados",), "classes": ("collapse",)}),
    )

    @admin.display(description="Total de Atendimentos")
    def total_atendimentos(self, obj: Contato) -> "Any":
        return getattr(obj, "atendimentos").count()

    @admin.display(description="Total de Clientes")
    def total_clientes(self, obj: Contato) -> "Any":
        """Retorna o número total de clientes vinculados ao contato"""
        if hasattr(obj, "clientes"):
            return getattr(obj, "clientes").count()
        return 0

    def get_queryset(self, request: HttpRequest) -> QuerySet[Contato]:
        """Otimiza consultas carregando clientes relacionados"""
        return super().get_queryset(request).prefetch_related("clientes")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):  # type: ignore
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
    filter_horizontal = ["contatos"]  # Interface melhorada para ManyToMany

    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("nome_fantasia", "razao_social", "tipo", "ativo")},
        ),
        ("Documentos", {"fields": ("cnpj", "cpf")}),
        ("Contatos", {"fields": ("telefone", "site", "ramo_atividade")}),
        (
            "Endereço",
            {
                "fields": (
                    ("cep", "uf"),
                    "logradouro",
                    ("numero", "complemento"),
                    "bairro",
                    ("cidade", "pais"),
                ),
                "classes": ("wide",),
            },
        ),
        ("Relacionamentos", {"fields": ("contatos",)}),
        ("Observações", {"fields": ("observacoes",), "classes": ("collapse",)}),
        ("Metadados", {"fields": ("metadados",), "classes": ("collapse",)}),
        (
            "Informações do Sistema",
            {
                "fields": (
                    "data_cadastro",
                    "ultima_atualizacao",
                    "get_endereco_completo_display",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Total de Contatos")
    def total_contatos(self, obj: Cliente) -> "Any":
        """Retorna o número total de contatos vinculados ao cliente"""
        return obj.contatos.count()

    @admin.display(description="Endereço Completo")
    def get_endereco_completo_display(self, obj: Cliente) -> str:
        """Exibe o endereço completo formatado no admin"""
        return obj.get_endereco_completo() or "-"

    # Configurações adicionais
    list_per_page = 25
    save_on_top = True

    # Actions customizadas
    actions = ["marcar_como_ativa", "marcar_como_inativa", "exportar_dados"]

    @admin.action(description="Marcar clientes selecionados como ativos")
    def marcar_como_ativa(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> None:
        queryset.update(ativo=True)
        self.message_user(request, f"{queryset.count()} clientes marcados como ativos.")

    @admin.action(description="Marcar clientes selecionados como inativos")
    def marcar_como_inativa(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> None:
        queryset.update(ativo=False)
        self.message_user(
            request, f"{queryset.count()} clientes marcados como inativos."
        )

    @admin.action(description="Exportar dados dos clientes selecionados (CSV)")
    def exportar_dados(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> "Any":
        """
        Exporta dados dos clientes selecionados em formato CSV.
        """
        import csv

        from django.http import HttpResponse

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
            # Mapeia o valor do tipo para o display
            tipo_choices = {"fisica": "Pessoa Física", "juridica": "Pessoa Jurídica"}
            tipo_display = tipo_choices.get(cliente.tipo, "") if cliente.tipo else ""

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
            request, f"Dados de {queryset.count()} clientes exportados com sucesso."
        )
        return response

    def get_queryset(self, request: HttpRequest) -> QuerySet[Cliente]:
        """Otimiza consultas carregando contatos relacionados"""
        return super().get_queryset(request).prefetch_related("contatos")


class MensagemInline(admin.TabularInline):  # type: ignore
    model = Mensagem
    extra = 0
    readonly_fields = [
        "timestamp",
        "message_id_whatsapp",
        "entidades_extraidas_preview",
    ]
    fields = [
        "tipo",
        "conteudo",
        "remetente",
        "respondida",
        "entidades_extraidas_preview",
        "timestamp",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Mensagem]:
        return super().get_queryset(request).order_by("timestamp")

    @admin.display(description="Entidades Extraídas")
    def entidades_extraidas_preview(self, obj: Mensagem) -> str:
        """Retorna uma prévia das entidades extraídas da mensagem"""
        if obj.entidades_extraidas:
            try:
                # Converte para string se for dict/list
                if isinstance(obj.entidades_extraidas, (dict, list)):
                    import json

                    entidades_str = json.dumps(
                        obj.entidades_extraidas, ensure_ascii=False
                    )
                else:
                    entidades_str = str(obj.entidades_extraidas)
                return (
                    entidades_str[:30] + "..."
                    if len(entidades_str) > 30
                    else entidades_str
                )
            except Exception:
                return "Erro ao exibir entidades"
        return "-"


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):  # type: ignore
    list_display = [
        "id",
        "contato_telefone",
        "status",
        "atendente_humano_nome",
        "data_inicio",
        "data_fim",
        "avaliacao",
        "total_mensagens",
    ]
    list_filter = [
        "status",
        "prioridade",
        "data_inicio",
        "avaliacao",
        "atendente_humano",
    ]
    search_fields = [
        "contato__telefone",
        "contato__nome_contato",
        "assunto",
        "atendente_humano__nome",
    ]
    readonly_fields = ["data_inicio", "data_fim"]
    inlines = [MensagemInline]

    fieldsets = (
        (
            "Informações do Atendimento",
            {"fields": ("contato", "status", "assunto", "prioridade")},
        ),
        ("Datas", {"fields": ("data_inicio", "data_fim")}),
        ("Atendente", {"fields": ("atendente_humano",)}),
        ("Avaliação", {"fields": ("avaliacao", "feedback")}),
        (
            "Contexto e Histórico",
            {
                "fields": ("contexto_conversa", "historico_status", "tags"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Telefone", ordering="contato__telefone")
    def contato_telefone(self, obj: Atendimento) -> "Any":
        try:
            return obj.contato.telefone  # type: ignore
        except AttributeError:
            return "-"

    @admin.display(description="Atendente", ordering="atendente_humano__nome")
    def atendente_humano_nome(self, obj: Atendimento) -> "Any":
        try:
            return obj.atendente_humano.nome if obj.atendente_humano else "-"  # type: ignore
        except AttributeError:
            return "-"

    @admin.display(description="Mensagens")
    def total_mensagens(self, obj: Atendimento) -> "Any":
        return getattr(obj, "mensagens").count()

    def get_queryset(self, request: HttpRequest) -> QuerySet[Atendimento]:
        return (
            super().get_queryset(request).select_related("contato", "atendente_humano")
        )


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):  # type: ignore
    list_display = [
        "id",
        "atendimento_id",
        "contato_telefone",
        "tipo",
        "conteudo_preview",
        "remetente",
        "respondida",
        "entidades_extraidas_preview",
        "timestamp",
    ]
    list_filter = ["tipo", "remetente", "respondida", "timestamp"]
    search_fields = [
        "conteudo",
        "atendimento__contato__telefone",
        "entidades_extraidas",
    ]
    readonly_fields = ["timestamp", "message_id_whatsapp"]

    fieldsets = (
        (
            "Informações da Mensagem",
            {"fields": ("atendimento", "tipo", "conteudo", "remetente", "respondida")},
        ),
        (
            "Resposta do Bot",
            {
                "fields": (
                    "resposta_bot",
                    "confianca_resposta",
                    "intent_detectado",
                    "entidades_extraidas",
                )
            },
        ),
        (
            "Metadados",
            {"fields": ("message_id_whatsapp", "metadados"), "classes": ("collapse",)},
        ),
        ("Timestamps", {"fields": ("timestamp",)}),
    )

    @admin.display(description="Telefone", ordering="atendimento__contato__telefone")
    def contato_telefone(self: "MensagemAdmin", obj: Mensagem) -> "Any":
        try:
            return obj.atendimento.contato.telefone  # type: ignore
        except AttributeError:
            return "-"

    @admin.display(description="Conteúdo")
    def conteudo_preview(self: "MensagemAdmin", obj: Mensagem) -> "Any":
        return obj.conteudo[:50] + "..." if len(obj.conteudo) > 50 else obj.conteudo

    @admin.display(description="Entidades Extraídas")
    def entidades_extraidas_preview(self: "MensagemAdmin", obj: Mensagem) -> "Any":
        if obj.entidades_extraidas:
            try:
                # Converte para string se for dict/list
                if isinstance(obj.entidades_extraidas, (dict, list)):
                    import json

                    entidades_str = json.dumps(
                        obj.entidades_extraidas, ensure_ascii=False
                    )
                else:
                    entidades_str = str(obj.entidades_extraidas)
                return (
                    entidades_str[:40] + "..."
                    if len(entidades_str) > 40
                    else entidades_str
                )
            except Exception:
                return "Erro ao exibir entidades"
        return "-"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Mensagem]:
        return super().get_queryset(request).select_related("atendimento__contato")


@admin.register(FluxoConversa)
class FluxoConversaAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ["nome", "ativo", "data_criacao", "data_modificacao"]
    list_filter = ["ativo", "data_criacao"]
    search_fields = ["nome", "descricao"]
    readonly_fields = ["data_criacao", "data_modificacao"]

    fieldsets = (
        ("Informações do Fluxo", {"fields": ("nome", "descricao", "ativo")}),
        (
            "Configuração",
            {"fields": ("condicoes_entrada", "estados"), "classes": ("collapse",)},
        ),
        ("Datas", {"fields": ("data_criacao", "data_modificacao")}),
    )


# Customizações adicionais do admin
admin.site.site_header = "Smart Core Assistant - Painel de Administração"
admin.site.site_title = "Smart Core Assistant"
admin.site.index_title = "Painel de Controle do Chatbot"

"""Configuração do painel de administração do Django para o aplicativo Oráculo.

Este módulo registra os modelos do aplicativo Oráculo no painel de administração
do Django e personaliza a forma como eles são exibidos e gerenciados.
"""

from typing import TYPE_CHECKING, cast

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse

if TYPE_CHECKING:
    from typing import Any

from .models import (
    AtendenteHumano,
    Atendimento,
    Cliente,
    Contato,
    FluxoConversa,
    Mensagem,
)
from .models_departamento import Departamento
from .models_treinamento import Treinamento
from .models_documento import Documento


@admin.register(Treinamento)
class TreinamentoAdmin(admin.ModelAdmin[Treinamento]):
    """Admin para o modelo Treinamento."""

    list_display = [
        "id",
        "tag",
        "grupo",
        "treinamento_finalizado",
        "treinamento_vetorizado",
        "embedding_preview",
        "get_documentos_count",
    ]
    search_fields = ["tag"]
    list_filter = ["treinamento_finalizado", "treinamento_vetorizado"]
    ordering = ["id"]
    fieldsets = (
        (
            "Informações do Treinamento",
            {
                "fields": (
                    "tag",
                    "grupo",
                    "conteudo",
                    "treinamento_finalizado",
                    "treinamento_vetorizado",
                    "embedding_preview",
                ),
                "classes": ("wide",),
            },
        ),
    )
    list_per_page = 25
    save_on_top = True
    readonly_fields = ["embedding_preview"]
    actions = ["marcar_como_vetorizado", "marcar_como_nao_vetorizado", "reprocessar_treinamentos"]

    @admin.display(description="Número de Documentos")
    def get_documentos_count(self, obj: Treinamento) -> int:
        """Retorna o número de documentos associados ao treinamento."""
        if obj and obj.pk:
            try:
                return obj.documentos.count()
            except Exception:
                return 0
        return 0

    @admin.display(description="Embedding (prévia)")
    def embedding_preview(self, obj: Treinamento) -> str:
        """Exibe uma prévia do vetor de embedding salvo.

        Mostra os primeiros valores (até 10) formatados com 4 casas decimais,
        junto com o tamanho total do vetor, para facilitar inspeção no admin.
        """
        try:
            vetor = getattr(obj, "embedding", None)
            
            # Verificação mais robusta para diferentes tipos de dados
            if vetor is None:
                return "-"
            
            # Verifica se é vazio de forma segura
            try:
                # Para numpy arrays e arrays similares
                if hasattr(vetor, 'size') and getattr(vetor, 'size', 0) == 0:
                    return "[embedding vazio]"
                # Para listas, tuplas e outros iteráveis
                elif hasattr(vetor, '__len__'):
                    try:
                        if len(vetor) == 0:
                            return "[embedding vazio]"
                    except (ValueError, TypeError):
                        # Se len() falhar (ex: numpy arrays multidimensionais), continua
                        pass
            except Exception:
                pass

            # Converte para lista de forma segura
            seq = []
            try:
                if isinstance(vetor, (list, tuple)):
                    seq = list(vetor)
                elif hasattr(vetor, 'tolist') and callable(getattr(vetor, 'tolist')):
                    seq = vetor.tolist()
                else:
                    # Tenta converter iterando sobre o objeto
                    try:
                        for i, item in enumerate(vetor):
                            if i >= 10:  # Limita para evitar processamento excessivo
                                break
                            seq.append(item)
                    except (TypeError, ValueError):
                        return "[embedding inválido]"
            except Exception:
                return "[embedding inválido]"

            # Verifica se a sequência resultante está vazia
            if not seq:
                return "[embedding vazio]"

            # Normaliza os elementos para float
            normalizado = []
            for i, x in enumerate(seq):
                if i >= 10:  # Limita a 10 elementos para preview
                    break
                try:
                    normalizado.append(float(x))
                except (ValueError, TypeError):
                    continue

            if not normalizado:
                return "[embedding vazio]"

            # Estima o tamanho total do vetor original
            tam_total = len(normalizado)  # fallback
            try:
                if hasattr(vetor, 'size'):
                    tam_total = getattr(vetor, 'size', tam_total)
                elif hasattr(vetor, '__len__'):
                    try:
                        tam_total = len(vetor)
                    except (ValueError, TypeError):
                        tam_total = len(seq)
                else:
                    tam_total = len(seq)
            except Exception:
                pass

            # Formata a preview
            head = normalizado[:10]
            fmt_head = ", ".join(f"{x:.4f}" for x in head)
            sufixo = ", ..." if tam_total > 10 else ""
            return f"[{fmt_head}{sufixo}] (dim={tam_total})"
            
        except Exception as e:
            return f"Erro: {type(e).__name__}"

    @admin.action(description="Marcar treinamentos selecionados como vetorizados")
    def marcar_como_vetorizado(
        self, request: HttpRequest, queryset: QuerySet[Treinamento]
    ) -> None:
        """Marca os treinamentos selecionados como vetorizados.

        Args:
            request (HttpRequest): O objeto de requisição.
            queryset (QuerySet[Treinamento]): O queryset de treinamentos.
        """
        queryset.update(treinamento_vetorizado=True)
        self.message_user(
            request, f"{queryset.count()} treinamentos marcados como vetorizados."
        )

    @admin.action(description="Marcar treinamentos selecionados como não vetorizados")
    def marcar_como_nao_vetorizado(
        self, request: HttpRequest, queryset: QuerySet[Treinamento]
    ) -> None:
        """Marca os treinamentos selecionados como não vetorizados.

        Args:
            request (HttpRequest): O objeto de requisição.
            queryset (QuerySet[Treinamento]): O queryset de treinamentos.
        """
        queryset.update(treinamento_vetorizado=False)
        self.message_user(
            request, f"{queryset.count()} treinamentos marcados como não vetorizados."
        )

    @admin.action(description="Reprocessar treinamentos selecionados (marca como finalizado)")
    def reprocessar_treinamentos(
        self, request: HttpRequest, queryset: QuerySet[Treinamento]
    ) -> None:
        """Reprocessa os treinamentos selecionados marcando como finalizados.

        Isso irá disparar o signal que inicia o processo de vetorização.

        Args:
            request (HttpRequest): O objeto de requisição.
            queryset (QuerySet[Treinamento]): O queryset de treinamentos.
        """
        queryset.update(treinamento_finalizado=True, treinamento_vetorizado=False)
        self.message_user(
            request, f"{queryset.count()} treinamentos marcados para reprocessamento."
        )


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
    search_fields = ["nome", "cargo", "telefone", "email", "departamento__nome"]
    list_filter = ["ativo", "disponivel", "cargo", "data_cadastro"]
    readonly_fields = [
        "data_cadastro",
        "ultima_atividade",
        "get_atendimentos_ativos",
    ]
    ordering = ["nome"]
    fieldsets = (
        ("Informações Pessoais", {"fields": ("nome", "cargo", "departamento")}),
        ("Contatos", {"fields": ("telefone", "email")}),
        ("Sistema", {"fields": ("usuario_sistema", "ativo", "disponivel")}),
        ("Capacidades", {"fields": ("max_atendimentos_simultaneos", "especialidades")}),
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
    list_per_page = 25
    save_on_top = True
    actions = ["marcar_como_disponivel", "marcar_como_indisponivel"]

    @admin.display(description="Atendimentos Ativos")
    def get_atendimentos_ativos(self, obj: AtendenteHumano) -> int:
        """Retorna a quantidade de atendimentos ativos do atendente.

        Args:
            obj (AtendenteHumano): A instância do atendente.

        Returns:
            int: O número de atendimentos ativos.
        """
        return obj.get_atendimentos_ativos() if obj else 0

    @admin.action(description="Marcar atendentes selecionados como disponíveis")
    def marcar_como_disponivel(
        self, request: HttpRequest, queryset: QuerySet[AtendenteHumano]
    ) -> None:
        """Marca os atendentes selecionados como disponíveis.

        Args:
            request (HttpRequest): O objeto de requisição.
            queryset (QuerySet[AtendenteHumano]): O queryset de atendentes.
        """
        queryset.update(disponivel=True)
        self.message_user(
            request, f"{queryset.count()} atendentes marcados como disponíveis."
        )

    @admin.action(description="Marcar atendentes selecionados como indisponíveis")
    def marcar_como_indisponivel(
        self, request: HttpRequest, queryset: QuerySet[AtendenteHumano]
    ) -> None:
        """Marca os atendentes selecionados como indisponíveis.

        Args:
            request (HttpRequest): O objeto de requisição.
            queryset (QuerySet[AtendenteHumano]): O queryset de atendentes.
        """
        queryset.update(disponivel=False)
        self.message_user(
            request, f"{queryset.count()} atendentes marcados como indisponíveis."
        )


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
            {"fields": ("telefone", "nome_contato", "nome_perfil_whatsapp", "ativo")},
        ),
        ("Datas", {"fields": ("data_cadastro", "ultima_interacao")}),
        ("Metadados", {"fields": ("metadados",), "classes": ("collapse",)}),
    )

    @admin.display(description="Total de Atendimentos")
    def total_atendimentos(self, obj: Contato) -> int:
        """Retorna o número total de atendimentos do contato.

        Args:
            obj (Contato): A instância do contato.

        Returns:
            int: O número de atendimentos.
        """
        return cast(int, getattr(obj, "atendimentos").count())

    @admin.display(description="Total de Clientes")
    def total_clientes(self, obj: Contato) -> int:
        """Retorna o número total de clientes vinculados ao contato.

        Args:
            obj (Contato): A instância do contato.

        Returns:
            int: O número de clientes.
        """
        return cast(int, getattr(obj, "clientes").count() if hasattr(obj, "clientes") else 0)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Contato]:
        """Otimiza as consultas carregando clientes relacionados.

        Args:
            request (HttpRequest): O objeto de requisição.

        Returns:
            QuerySet[Contato]: O queryset otimizado.
        """
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
        """Retorna o número total de contatos vinculados ao cliente.

        Args:
            obj (Cliente): A instância do cliente.

        Returns:
            int: O número de contatos.
        """
        return obj.contatos.count()

    @admin.display(description="Endereço Completo")
    def get_endereco_completo_display(self, obj: Cliente) -> str:
        """Exibe o endereço completo formatado no admin.

        Args:
            obj (Cliente): A instância do cliente.

        Returns:
            str: O endereço completo.
        """
        return obj.get_endereco_completo() or "-"

    @admin.action(description="Marcar clientes selecionados como ativos")
    def marcar_como_ativa(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> None:
        """Marca os clientes selecionados como ativos.

        Args:
            request (HttpRequest): O objeto de requisição.
            queryset (QuerySet[Cliente]): O queryset de clientes.
        """
        queryset.update(ativo=True)
        self.message_user(request, f"{queryset.count()} clientes marcados como ativos.")

    @admin.action(description="Marcar clientes selecionados como inativos")
    def marcar_como_inativa(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> None:
        """Marca os clientes selecionados como inativos.

        Args:
            request (HttpRequest): O objeto de requisição.
            queryset (QuerySet[Cliente]): O queryset de clientes.
        """
        queryset.update(ativo=False)
        self.message_user(
            request, f"{queryset.count()} clientes marcados como inativos."
        )

    @admin.action(description="Exportar dados dos clientes selecionados (CSV)")
    def exportar_dados(
        self, request: HttpRequest, queryset: QuerySet[Cliente]
    ) -> HttpResponse:
        """Exporta os dados dos clientes selecionados em formato CSV.

        Args:
            request (HttpRequest): O objeto de requisição.
            queryset (QuerySet[Cliente]): O queryset de clientes.

        Returns:
            HttpResponse: A resposta HTTP com o arquivo CSV.
        """
        import csv

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
        """Otimiza as consultas carregando contatos relacionados.

        Args:
            request (HttpRequest): O objeto de requisição.

        Returns:
            QuerySet[Cliente]: O queryset otimizado.
        """
        return super().get_queryset(request).prefetch_related("contatos")


class MensagemInline(admin.TabularInline[Mensagem, Atendimento]):
    """Inline para o modelo Mensagem."""

    model = Mensagem
    fields = (
        "tipo",
        "conteudo",
        "remetente",
        "respondida",
        "entidades_extraidas_preview",
        "timestamp",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Mensagem]:
        """Ordena as mensagens por timestamp.

        Args:
            request (HttpRequest): O objeto de requisição.

        Returns:
            QuerySet[Mensagem]: O queryset ordenado.
        """
        return super().get_queryset(request).order_by("timestamp")

    @admin.display(description="Entidades Extraídas")
    def entidades_extraidas_preview(self, obj: Mensagem) -> str:
        """Retorna uma prévia das entidades extraídas da mensagem.

        Args:
            obj (Mensagem): A instância da mensagem.

        Returns:
            str: Uma prévia das entidades.
        """
        if obj.entidades_extraidas:
            try:
                entidades_str = str(obj.entidades_extraidas)
                return (
                    (entidades_str[:30] + "...")
                    if len(entidades_str) > 30
                    else entidades_str
                )
            except Exception:
                return "Erro ao exibir entidades"
        return "-"


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin[Atendimento]):
    """Admin para o modelo Atendimento."""

    list_display = [
        "id",
        "contato_telefone",
        "status",
        "data_inicio",
        "data_fim",
        "atendente_humano_nome",
        "avaliacao",
        "total_mensagens",
        "duracao_formatada",
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
    readonly_fields = ["data_inicio"]
    inlines = [MensagemInline]
    date_hierarchy = "data_inicio"
    ordering = ["-data_inicio"]
    list_per_page = 25

    @admin.display(description="Telefone")
    def contato_telefone(self, obj: Atendimento) -> str:
        """Retorna o telefone do contato."""
        if obj.contato:
            return cast(str, obj.contato.telefone)  # type: ignore[attr-defined]
        return "-"

    @admin.display(description="Atendente")
    def atendente_humano_nome(self, obj: Atendimento) -> str:
        """Retorna o nome do atendente humano."""
        if obj.atendente_humano:
            return cast(str, obj.atendente_humano.nome)  # type: ignore[attr-defined]
        return "-"

    @admin.display(description="Mensagens")
    def total_mensagens(self, obj: Atendimento) -> int:
        """Retorna o número total de mensagens no atendimento.

        Args:
            obj (Atendimento): A instância do atendimento.

        Returns:
            int: O número de mensagens.
        """
        return cast(int, getattr(obj, "mensagens").count())

    @admin.display(description="Duração")
    def duracao_formatada(self, obj: Atendimento) -> str:
        """Retorna a duração formatada do atendimento.

        Args:
            obj (Atendimento): A instância do atendimento.

        Returns:
            str: A duração formatada.
        """
        if obj.data_fim and obj.data_inicio:
            duracao = obj.data_fim - obj.data_inicio
            total_seconds = int(duracao.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}"
        return "Em andamento"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Atendimento]:
        """Otimiza a consulta pré-carregando dados relacionados."""
        return (
            super()
            .get_queryset(request)
            .select_related("contato", "atendente_humano", "departamento")
            .prefetch_related("mensagens")
        )


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin[Mensagem]):
    """Admin para o modelo Mensagem."""

    list_display = [
        "id",
        "atendimento_id",
        "atendimento",
        "remetente",
        "tipo",
        "conteudo_truncado",
        "contato_telefone",
        "respondida",
        "entidades_extraidas_preview",
        "timestamp",
        "message_id_whatsapp",
    ]
    list_filter = ["remetente", "tipo", "timestamp"]
    search_fields = [
        "conteudo",
        "message_id_whatsapp",
        "atendimento__contato__nome_contato",
        "atendimento__contato__telefone",
    ]
    readonly_fields = ["timestamp", "message_id_whatsapp"]
    date_hierarchy = "timestamp"
    list_per_page = 25

    @admin.display(description="Telefone", ordering="atendimento__contato__telefone")
    def contato_telefone(self, obj: Mensagem) -> str:
        """Retorna o telefone do contato associado à mensagem.

        Args:
            obj (Mensagem): A instância da mensagem.

        Returns:
            str: O telefone do contato.
        """
        return (
            obj.atendimento.contato.telefone
            if hasattr(obj, "atendimento") and hasattr(obj.atendimento, "contato")
            else "-"
        )

    @admin.display(description="Conteúdo")
    def conteudo_truncado(self, obj: Mensagem) -> str:
        """Retorna uma versão truncada do conteúdo da mensagem.

        Args:
            obj (Mensagem): A instância da mensagem.

        Returns:
            str: O conteúdo truncado.
        """
        return cast(str, (obj.conteudo[:47] + "...") if len(obj.conteudo) > 50 else obj.conteudo)

    @admin.display(description="Entidades Extraídas")
    def entidades_extraidas_preview(self, obj: Mensagem) -> str:
        """Retorna uma prévia das entidades extraídas.

        Args:
            obj (Mensagem): A instância da mensagem.

        Returns:
            str: Uma prévia das entidades.
        """
        if obj.entidades_extraidas:
            try:
                entidades_str = str(obj.entidades_extraidas)
                return (
                    (entidades_str[:40] + "...")
                    if len(entidades_str) > 40
                    else entidades_str
                )
            except Exception:
                return "Erro ao exibir entidades"
        return "-"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Mensagem]:
        """Otimiza as consultas carregando dados relacionados.

        Args:
            request (HttpRequest): O objeto de requisição.

        Returns:
            QuerySet[Mensagem]: O queryset otimizado.
        """
        return (
            super()
            .get_queryset(request)
            .select_related("atendimento", "atendimento__contato")
        )


@admin.register(FluxoConversa)
class FluxoConversaAdmin(admin.ModelAdmin[FluxoConversa]):
    """Admin para o modelo FluxoConversa."""

    list_display = ["nome", "ativo", "data_criacao", "data_modificacao"]
    list_filter = ["ativo", "data_criacao"]
    search_fields = ["nome", "descricao"]
    readonly_fields = ["data_criacao", "data_modificacao"]


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


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin[Documento]):
    """Admin para o modelo Documento."""
    
    list_display = [
        "id",
        "treinamento_tag",
        "ordem",
        "conteudo_preview",
        "metadata_preview",
        "data_criacao",
    ]
    search_fields = ["treinamento__tag", "conteudo"]
    list_filter = ["treinamento__tag", "treinamento__grupo", "data_criacao"]
    ordering = ["treinamento__tag", "ordem"]
    exclude = ["embedding"]  # Exclui o campo embedding do formulário
    readonly_fields = [
        "treinamento", 
        "conteudo", 
        "metadata", 
        "embedding_preview",
        "ordem",
        "data_criacao"
    ]
    list_per_page = 50
    save_on_top = True
    
    def has_change_permission(self, request: HttpRequest, obj: Documento | None = None) -> bool:
        """Impede a modificação de documentos existentes."""
        return False
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """Impede a criação manual de documentos."""
        return False
    
    @admin.display(description="Tag do Treinamento")
    def treinamento_tag(self, obj: Documento) -> str:
        """Retorna a tag do treinamento associado."""
        return obj.treinamento.tag if obj.treinamento and obj.treinamento.tag else "-"  # type: ignore[attr-defined]
    
    @admin.display(description="Conteúdo (prévia)")
    def conteudo_preview(self, obj: Documento) -> str:
        """Exibe uma prévia do conteúdo do documento."""
        if obj and obj.conteudo:
            preview = obj.conteudo[:200]
            return preview + "..." if len(obj.conteudo) > 200 else preview
        return "Conteúdo vazio"
    
    @admin.display(description="Metadados")
    def metadata_preview(self, obj: Documento) -> str:
        """Exibe uma prévia dos metadados do documento."""
        if obj and obj.metadata:
            try:
                metadata_str = str(obj.metadata)
                preview = metadata_str[:100]
                return preview + "..." if len(metadata_str) > 100 else preview
            except Exception:
                return "Erro ao exibir metadados"
        return "Sem metadados"
    
    @admin.display(description="Embedding (prévia)")
    def embedding_preview(self, obj: Documento) -> str:
        """Exibe uma prévia do vetor de embedding salvo."""
        try:
            vetor = getattr(obj, "embedding", None)
            
            # Verificação mais robusta para diferentes tipos de dados
            if vetor is None:
                return "-"
            
            # Verifica se é vazio de forma segura
            try:
                # Para numpy arrays e arrays similares
                if hasattr(vetor, 'size') and getattr(vetor, 'size', 0) == 0:
                    return "[embedding vazio]"
                # Para listas, tuplas e outros iteráveis
                elif hasattr(vetor, '__len__'):
                    try:
                        if len(vetor) == 0:
                            return "[embedding vazio]"
                    except (ValueError, TypeError):
                        # Se len() falhar (ex: numpy arrays multidimensionais), continua
                        pass
            except Exception:
                pass
            
            # Converte para lista de forma segura
            seq = []
            try:
                if isinstance(vetor, (list, tuple)):
                    seq = list(vetor)
                elif hasattr(vetor, 'tolist') and callable(getattr(vetor, 'tolist')):
                    seq = vetor.tolist()
                else:
                    # Tenta converter iterando sobre o objeto
                    try:
                        for i, item in enumerate(vetor):
                            if i >= 10:  # Limita para evitar processamento excessivo
                                break
                            seq.append(item)
                    except (TypeError, ValueError):
                        return "[embedding inválido]"
            except Exception:
                return "[embedding inválido]"
            
            # Verifica se a sequência resultante está vazia
            if not seq:
                return "[embedding vazio]"
            
            # Normaliza os elementos para float
            normalizado = []
            for i, x in enumerate(seq):
                if i >= 10:  # Limita a 10 elementos para preview
                    break
                try:
                    normalizado.append(float(x))
                except (ValueError, TypeError):
                    continue
            
            if not normalizado:
                return "[embedding vazio]"
            
            # Estima o tamanho total do vetor original
            tam_total = len(normalizado)  # fallback
            try:
                if hasattr(vetor, 'size'):
                    tam_total = getattr(vetor, 'size', tam_total)
                elif hasattr(vetor, '__len__'):
                    try:
                        tam_total = len(vetor)
                    except (ValueError, TypeError):
                        tam_total = len(seq)
                else:
                    tam_total = len(seq)
            except Exception:
                pass
            
            # Formata a preview
            head = normalizado[:10]
            fmt_head = ", ".join(f"{x:.4f}" for x in head)
            sufixo = ", ..." if tam_total > 10 else ""
            return f"[{fmt_head}{sufixo}] (dim={tam_total})"
            
        except Exception as e:
            return f"Erro: {type(e).__name__}"


admin.site.site_header = "Smart Core Assistant - Painel de Administração"
admin.site.site_title = "Smart Core Assistant"
admin.site.index_title = "Painel de Controle do Chatbot"
"""Configuração do painel de administração do app Atendimentos.

Este módulo registra os modelos do aplicativo Atendimentos no painel de
administração do Django e personaliza como são exibidos e gerenciados.
"""

from typing import Any, Optional, cast

from django.contrib import admin
from django.db.models import QuerySet, F
from django.http import HttpRequest
from django.utils import timezone
from django import forms

from .models import Atendimento, Mensagem
from smart_core_assistant_painel.app.ui.operacional.models import EtapaFluxo


class MensagemInline(admin.TabularInline[Mensagem, Atendimento]):
    """Inline para o modelo Mensagem."""

    model = Mensagem
    fields = (
        "tipo",
        "conteudo",
        "remetente",
        "respondida",
        "entidades_extraidas_preview",
    )
    readonly_fields = ("timestamp", "entidades_extraidas_preview")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Mensagem]:
        """Ordena as mensagens por timestamp."""
        return super().get_queryset(request).order_by("timestamp")

    @admin.display(description="Entidades Extraídas")
    def entidades_extraidas_preview(self, obj: Mensagem) -> str:
        """Retorna uma prévia das entidades extraídas da mensagem."""
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
        "etapa_atual",
        "departamento",
        "data_inicio",
        "data_fim",
        "atendente_humano",
        "total_mensagens",
        "duracao_formatada",
        "prioridade",
    ]
    list_filter = [
        "status",
        "etapa_atual",
        "departamento",
        "prioridade",
        "data_inicio",
    ]
    search_fields = [
        "contato__telefone",
        "contato__nome_contato",
        "assunto",
        "tags",
    ]
    readonly_fields = [
        "data_inicio",
        "duracao_calculada",
    ]
    inlines = [MensagemInline]
    date_hierarchy = "data_inicio"
    ordering = ["-data_inicio"]
    list_per_page = 25
    save_on_top = True
    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "contato",
                    "departamento",
                    "status",
                    "etapa_atual",
                    "atendente_humano",
                )
            },
        ),
        (
            "Detalhes do Atendimento",
            {
                "fields": (
                    "assunto",
                    "prioridade",
                    "tags",
                )
            },
        ),
        (
            "Informações Complementares",
            {
                "fields": (
                    "avaliacao",
                    "feedback",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Informações de Sistema",
            {
                "fields": (
                    "canal",
                    "data_inicio",
                    "data_fim",
                    "duracao_calculada",
                    "data_ultima_mensagem",
                    "data_primeira_resposta",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Contexto e Histórico",
            {
                "fields": (
                    "contexto_conversa",
                    "historico_status",
                ),
                "classes": ("collapse",),
            },
        ),
        # Seções comerciais/financeiras removidas do modelo foram excluídas
    )

    @admin.display(description="Telefone")
    def contato_telefone(self, obj: Atendimento) -> str:
        """Retorna o telefone do contato."""
        if obj.contato:
            return cast(str, obj.contato.telefone)
        return "-"

    @admin.display(description="Mensagens")
    def total_mensagens(self, obj: Atendimento) -> int:
        """Retorna o número total de mensagens no atendimento."""
        return cast(int, getattr(obj, "mensagens").count())

    @admin.display(description="Duração Calculada")
    def duracao_calculada(self, obj: Atendimento) -> str:
        """Retorna a duração formatada do atendimento."""
        if obj.data_fim and obj.data_inicio:
            duracao = obj.data_fim - obj.data_inicio
            total_seconds = int(duracao.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}"
        elif obj.data_inicio:
            duracao = timezone.now() - obj.data_inicio
            total_seconds = int(duracao.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02} (em andamento)"
        return "-"

    @admin.display(description="Duração")
    def duracao_formatada(self, obj: Atendimento) -> str:
        """Retorna a duração formatada do atendimento."""
        if obj.data_fim and obj.data_inicio:
            duracao = obj.data_fim - obj.data_inicio
            total_seconds = int(duracao.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}"
        return "Em andamento"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Atendimento]:
        """Otimiza a consulta evitando FKs ausentes e pré-carrega dados necessários."""
        return (
            super()
            .get_queryset(request)
            .select_related("contato")
            .prefetch_related("mensagens")
            .only(
                "id",
                "contato",
                "status",
                "departamento",
                "data_inicio",
                "data_fim",
                "atendente_humano",
                "avaliacao",
                "feedback",
            )
            .defer(
                "contexto_conversa",
                "historico_status",
                "tags",
            )
        )

    def get_form(
        self,
        request: HttpRequest,
        obj: Optional[Atendimento] = None,
        **kwargs: Any,
    ) -> type[forms.ModelForm]:
        """Filtra `etapa_atual` pelo departamento selecionado.

        - Em criação: usa `departamento` vindo de GET/POST.
        - Em edição: usa `obj.departamento`.
        """
        form_cls: type[forms.ModelForm] = super().get_form(
            request, obj, **kwargs
        )

        dept_id_raw: Optional[str] = None
        if obj and obj.departamento_id:
            dept_id_raw = str(obj.departamento_id)
        else:
            # QueryDict aceita .get; mocks podem usar dict simples
            dept_id_raw = (
                getattr(request, "POST", {}).get("departamento")
                or getattr(request, "GET", {}).get("departamento")
            )

        if "etapa_atual" in form_cls.base_fields:
            if dept_id_raw:
                try:
                    dept_id: int = int(dept_id_raw)
                    qs: QuerySet[EtapaFluxo] = EtapaFluxo.objects.filter(
                        fluxo__departamento_id=dept_id
                    ).order_by("fluxo__nome", "ordem")
                    form_cls.base_fields["etapa_atual"].queryset = qs
                    form_cls.base_fields["etapa_atual"].help_text = (
                        "Mostrando apenas etapas do departamento selecionado."
                    )
                except ValueError:
                    form_cls.base_fields["etapa_atual"].queryset = (
                        EtapaFluxo.objects.none()
                    )
                    form_cls.base_fields["etapa_atual"].help_text = (
                        "Selecione um departamento para carregar etapas."
                    )
            else:
                form_cls.base_fields["etapa_atual"].queryset = (
                    EtapaFluxo.objects.none()
                )
                form_cls.base_fields["etapa_atual"].help_text = (
                    "Selecione um departamento para carregar etapas."
                )

        return form_cls


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin[Mensagem]):
    """Admin para o modelo Mensagem."""

    list_display = [
        "id",
        "atendimento_id",
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

    @admin.display(
        description="Telefone", ordering="atendimento__contato__telefone"
    )
    def contato_telefone(self, obj: Mensagem) -> str:
        """Retorna o telefone do contato associado à mensagem."""
        return cast(str, getattr(obj, "contato_tel", "-"))

    @admin.display(description="Conteúdo")
    def conteudo_truncado(self, obj: Mensagem) -> str:
        """Retorna uma versão truncada do conteúdo da mensagem."""
        return cast(
            str,
            (obj.conteudo[:47] + "...")
            if len(obj.conteudo) > 50
            else obj.conteudo,
        )

    @admin.display(description="Entidades Extraídas")
    def entidades_extraidas_preview(self, obj: Mensagem) -> str:
        """Retorna uma prévia das entidades extraídas."""
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
        """Otimiza as consultas evitando carregar o Atendimento completo."""
        return (
            super()
            .get_queryset(request)
            .annotate(contato_tel=F("atendimento__contato__telefone"))
        )

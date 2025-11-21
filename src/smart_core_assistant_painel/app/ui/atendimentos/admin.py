"""Configuração do painel de administração do app Atendimentos.

Este módulo registra os modelos do aplicativo Atendimentos no painel de
administração do Django e personaliza como são exibidos e gerenciados.
"""

from typing import Any, Optional, cast

from django import forms
from django.contrib import admin
from django.db.models import F, QuerySet
from django.http import HttpRequest, JsonResponse
from django.urls import path
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.ui.operacional.models import (
    EtapaFluxo,
    FluxoAtendimento,
)

from .models import Atendimento, Mensagem


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
        "atendente_humano_nome",
        "total_mensagens",
        "duracao_formatada",
        "avaliacao",
        "prioridade",
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
                    "fluxo_atendimento",
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

    @admin.display(description="Atendente")
    def atendente_humano_nome(self, obj: Atendimento) -> str:
        """Retorna o nome do atendente humano vinculado."""
        if obj.atendente_humano:
            return cast(str, obj.atendente_humano.nome)
        return "-"

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
        """Retorna o formulário padrão.

        Comentário: a filtragem de `etapa_atual` é feita em
        `formfield_for_foreignkey` para evitar inconsistências
        na validação do POST.
        """
        # Armazena o objeto em edição no request para ser utilizado
        # posteriormente em `formfield_for_foreignkey`, permitindo que
        # o queryset de `etapa_atual` seja filtrado pelo departamento
        # do próprio objeto quando não houver parâmetro em GET/POST.
        setattr(request, "_admin_current_obj", obj)
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(
        self,
        db_field: Any,
        request: HttpRequest,
        **kwargs: Any,
    ) -> forms.Field:
        """Filtra `fluxo_atendimento` por departamento e `etapa_atual` por fluxo.

        Também injeta `data-initial` nos widgets para que o JS
        selecione os valores previamente salvos ao carregar opções.
        """
        field: forms.Field = super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )
        name = getattr(db_field, "name", None)

        # Filtragem do campo FluxoAtendimento pelo departamento selecionado
        if name == "fluxo_atendimento":
            dept_id_raw: Optional[str] = getattr(request, "POST", {}).get(
                "departamento"
            ) or getattr(request, "GET", {}).get("departamento")

            initial_fluxo_id: Optional[str] = getattr(request, "POST", {}).get(
                "fluxo_atendimento"
            )

            if not dept_id_raw or not initial_fluxo_id:
                current_obj: Optional[Atendimento] = cast(
                    Optional[Atendimento],
                    getattr(request, "_admin_current_obj", None),
                )
                if current_obj is not None:
                    if not dept_id_raw and current_obj.departamento_id:
                        dept_id_raw = str(current_obj.departamento_id)
                    if (
                        not initial_fluxo_id
                        and current_obj.fluxo_atendimento_id
                    ):
                        initial_fluxo_id = str(
                            current_obj.fluxo_atendimento_id
                        )
                else:
                    try:
                        object_id = request.resolver_match.kwargs.get(
                            "object_id"
                        )
                    except Exception:
                        object_id = None
                    if object_id:
                        try:
                            obj_loaded = Atendimento.objects.only(
                                "departamento_id",
                                "fluxo_atendimento_id",
                            ).get(pk=object_id)
                            if not dept_id_raw and obj_loaded.departamento_id:
                                dept_id_raw = str(obj_loaded.departamento_id)
                            if (
                                not initial_fluxo_id
                                and obj_loaded.fluxo_atendimento_id
                            ):
                                initial_fluxo_id = str(
                                    obj_loaded.fluxo_atendimento_id
                                )
                        except Atendimento.DoesNotExist:
                            pass

            if dept_id_raw:
                try:
                    dept_id: int = int(dept_id_raw)
                    qs_fluxos: QuerySet[FluxoAtendimento] = (
                        FluxoAtendimento.objects.filter(
                            departamento_id=dept_id
                        ).order_by("nome")
                    )
                    cast(forms.ModelChoiceField, field).queryset = qs_fluxos
                    field.help_text = (
                        "Mostrando fluxos do departamento selecionado."
                    )
                except ValueError:
                    cast(
                        forms.ModelChoiceField, field
                    ).queryset = FluxoAtendimento.objects.none()
                    field.help_text = (
                        "Selecione um departamento para carregar fluxos."
                    )
            else:
                cast(
                    forms.ModelChoiceField, field
                ).queryset = FluxoAtendimento.objects.none()
                field.help_text = (
                    "Selecione um departamento para carregar fluxos."
                )

            try:
                field.widget.attrs["data-initial"] = initial_fluxo_id or ""
            except Exception:
                pass
            return field

        # Filtragem do campo EtapaFluxo pelo fluxo selecionado
        if name == "etapa_atual":
            fluxo_id_raw: Optional[str] = getattr(request, "POST", {}).get(
                "fluxo_atendimento"
            ) or getattr(request, "GET", {}).get("fluxo_atendimento")

            initial_etapa_id: Optional[str] = getattr(request, "POST", {}).get(
                "etapa_atual"
            )

            if not fluxo_id_raw or not initial_etapa_id:
                current_obj2: Optional[Atendimento] = cast(
                    Optional[Atendimento],
                    getattr(request, "_admin_current_obj", None),
                )
                if current_obj2 is not None:
                    if not fluxo_id_raw and current_obj2.fluxo_atendimento_id:
                        fluxo_id_raw = str(current_obj2.fluxo_atendimento_id)
                    if not initial_etapa_id and current_obj2.etapa_atual_id:
                        initial_etapa_id = str(current_obj2.etapa_atual_id)
                else:
                    try:
                        object_id2 = request.resolver_match.kwargs.get(
                            "object_id"
                        )
                    except Exception:
                        object_id2 = None
                    if object_id2:
                        try:
                            obj_loaded2 = Atendimento.objects.only(
                                "fluxo_atendimento_id",
                                "etapa_atual_id",
                            ).get(pk=object_id2)
                            if (
                                not fluxo_id_raw
                                and obj_loaded2.fluxo_atendimento_id
                            ):
                                fluxo_id_raw = str(
                                    obj_loaded2.fluxo_atendimento_id
                                )
                            if (
                                not initial_etapa_id
                                and obj_loaded2.etapa_atual_id
                            ):
                                initial_etapa_id = str(
                                    obj_loaded2.etapa_atual_id
                                )
                        except Atendimento.DoesNotExist:
                            pass

            if fluxo_id_raw:
                try:
                    fluxo_id: int = int(fluxo_id_raw)
                    qs_etapas: QuerySet[EtapaFluxo] = (
                        EtapaFluxo.objects.filter(fluxo_id=fluxo_id)
                        .select_related("fluxo")
                        .order_by("ordem")
                    )
                    cast(forms.ModelChoiceField, field).queryset = qs_etapas
                    field.help_text = "Mostrando etapas do fluxo selecionado."
                except ValueError:
                    cast(
                        forms.ModelChoiceField, field
                    ).queryset = EtapaFluxo.objects.none()
                    field.help_text = (
                        "Selecione um fluxo para carregar etapas."
                    )
            else:
                cast(
                    forms.ModelChoiceField, field
                ).queryset = EtapaFluxo.objects.none()
                field.help_text = "Selecione um fluxo para carregar etapas."

            try:
                field.widget.attrs["data-initial"] = initial_etapa_id or ""
            except Exception:
                pass
            return field

        return field

    # Comentário: endpoints no admin para carregar fluxos e etapas via AJAX
    def get_urls(self) -> list[Any]:
        """Registra URLs adicionais para o admin de Atendimento."""
        urls = super().get_urls()
        custom = [
            # Fluxos por departamento
            path(
                "fetch-fluxos/",
                self.admin_site.admin_view(self.admin_fluxos_by_departamento),
                name="atendimento_fetch_fluxos",
            ),
            path(
                "<path:object_id>/fetch-fluxos/",
                self.admin_site.admin_view(self.admin_fluxos_by_departamento),
                name="atendimento_fetch_fluxos_obj",
            ),
            path(
                "fetch-etapas/",
                self.admin_site.admin_view(self.admin_etapas_by_departamento),
                name="atendimento_fetch_etapas",
            ),
            # Suporta também chamadas vindas da página de edição
            # no formato: /<obj_id>/fetch-etapas/
            path(
                "<path:object_id>/fetch-etapas/",
                self.admin_site.admin_view(self.admin_etapas_by_departamento),
                name="atendimento_fetch_etapas_obj",
            ),
            # Etapas por fluxo
            path(
                "fetch-etapas-by-fluxo/",
                self.admin_site.admin_view(self.admin_etapas_by_fluxo),
                name="atendimento_fetch_etapas_by_fluxo",
            ),
            path(
                "<path:object_id>/fetch-etapas-by-fluxo/",
                self.admin_site.admin_view(self.admin_etapas_by_fluxo),
                name="atendimento_fetch_etapas_by_fluxo_obj",
            ),
        ]
        return custom + urls

    def admin_etapas_by_departamento(
        self, request: HttpRequest
    ) -> JsonResponse:
        """Retorna etapas de fluxo filtradas por departamento.

        Espera o parâmetro `departamento_id` em GET.
        """
        dept_id_raw: Optional[str] = request.GET.get("departamento_id")
        data: list[dict[str, Any]] = []
        if dept_id_raw:
            try:
                dept_id: int = int(dept_id_raw)
                qs: QuerySet[EtapaFluxo] = (
                    EtapaFluxo.objects.filter(fluxo__departamento_id=dept_id)
                    .select_related("fluxo")
                    .order_by("fluxo__nome", "ordem")
                )
                # Loga informações para diagnóstico no admin.
                logger.info(
                    "Admin etapas: dept_id={} count={}",
                    dept_id,
                    qs.count(),
                )
                for ef in qs:
                    label: str = f"{ef.fluxo.nome} • {ef.nome} (#{ef.ordem})"
                    data.append({"id": ef.id, "label": label})
            except ValueError:
                data = []
        return JsonResponse({"results": data})

    def admin_fluxos_by_departamento(
        self, request: HttpRequest
    ) -> JsonResponse:
        """Retorna fluxos filtrados por departamento.

        Espera o parâmetro `departamento_id` em GET.
        """
        dept_id_raw: Optional[str] = request.GET.get("departamento_id")
        data: list[dict[str, Any]] = []
        if dept_id_raw:
            try:
                dept_id: int = int(dept_id_raw)
                qs: QuerySet[FluxoAtendimento] = (
                    FluxoAtendimento.objects.filter(
                        departamento_id=dept_id
                    ).order_by("nome")
                )
                logger.info(
                    "Admin fluxos: dept_id={} count={}", dept_id, qs.count()
                )
                for fluxo in qs:
                    data.append({"id": fluxo.id, "label": fluxo.nome})
            except ValueError:
                data = []
        return JsonResponse({"results": data})

    def admin_etapas_by_fluxo(self, request: HttpRequest) -> JsonResponse:
        """Retorna etapas filtradas por fluxo.

        Espera o parâmetro `fluxo_id` em GET.
        """
        fluxo_id_raw: Optional[str] = request.GET.get("fluxo_id")
        data: list[dict[str, Any]] = []
        if fluxo_id_raw:
            try:
                fluxo_id: int = int(fluxo_id_raw)
                qs: QuerySet[EtapaFluxo] = EtapaFluxo.objects.filter(
                    fluxo_id=fluxo_id
                ).order_by("ordem")
                logger.info(
                    "Admin etapas: fluxo_id={} count={}",
                    fluxo_id,
                    qs.count(),
                )
                for ef in qs:
                    label: str = f"{ef.nome} (#{ef.ordem})"
                    data.append({"id": ef.id, "label": label})
            except ValueError:
                data = []
        return JsonResponse({"results": data})

    class Media:
        """Inclui JS para dependência dinâmica de etapas por departamento."""

        js = ("atendimentos/admin_etapas.js",)


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin[Mensagem]):
    """Admin para o modelo Mensagem."""

    list_display = [
        "id",
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

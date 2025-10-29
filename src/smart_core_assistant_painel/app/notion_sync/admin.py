"""
Configuração do Django Admin para o app notion_sync.

Este módulo registra os models do app de sincronização no Django Admin,
permitindo visualização e gerenciamento via interface web.
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import (
    AtendenteSync,
    AtendimentoSync,
    ClienteSync,
    ContatoSync,
    DepartamentoSync,
    MensagemSync,
    NotionDatabaseConfig,
)


@admin.register(NotionDatabaseConfig)
class NotionDatabaseConfigAdmin(admin.ModelAdmin[NotionDatabaseConfig]):
    list_display = (
        "django_model",
        "name",
        "notion_database_id_short",
        "sync_enabled",
        "updated_at",
    )
    list_filter = ("sync_enabled", "created_at", "updated_at")
    search_fields = ("django_model", "name", "notion_database_id")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("django_model",)

    def notion_database_id_short(self, obj: NotionDatabaseConfig) -> str:
        if obj.notion_database_id:
            return f"{str(obj.notion_database_id)[:20]}..."
        return "-"

    notion_database_id_short.short_description = "Database ID"


class BaseSyncAdmin(admin.ModelAdmin):
    def sync_status_colored(self, obj: Any) -> str:
        if obj.sync_status == "synced":
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Sincronizado</span>'
            )
        elif obj.sync_status == "error":
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Erro</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ {}</span>'.format(
                    obj.get_sync_status_display()
                )
            )

    sync_status_colored.short_description = "Status"

    def external_id_short(self, obj: Any) -> str:
        if obj.external_id:
            return f"{str(obj.external_id)[:20]}..."
        return "-"

    external_id_short.short_description = "ID Externo"

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(ContatoSync)
class ContatoSyncAdmin(BaseSyncAdmin):
    list_display = (
        "id",
        "contato_info",
        "external_id_short",
        "sync_status_colored",
        "last_sync_at",
        "retry_count",
    )
    list_filter = ("sync_status", "last_sync_at")
    search_fields = ("contato__telefone", "contato__nome_contato", "external_id")
    readonly_fields = [f.name for f in ContatoSync._meta.fields]
    ordering = ("-updated_at",)

    def contato_info(self, obj: ContatoSync) -> str:
        return f"{obj.contato.telefone} - {obj.contato.nome_contato or 'Sem nome'}"

    contato_info.short_description = "Contato"


@admin.register(ClienteSync)
class ClienteSyncAdmin(BaseSyncAdmin):
    list_display = (
        "id",
        "cliente_info",
        "external_id_short",
        "sync_status_colored",
        "last_sync_at",
        "retry_count",
    )
    list_filter = ("sync_status", "last_sync_at")
    search_fields = ("cliente__nome_fantasia", "cliente__razao_social", "external_id")
    readonly_fields = [f.name for f in ClienteSync._meta.fields]
    ordering = ("-updated_at",)

    def cliente_info(self, obj: ClienteSync) -> str:
        return obj.cliente.nome_fantasia

    cliente_info.short_description = "Cliente"


@admin.register(DepartamentoSync)
class DepartamentoSyncAdmin(BaseSyncAdmin):
    list_display = (
        "id",
        "departamento_info",
        "external_id_short",
        "sync_status_colored",
        "last_sync_at",
        "retry_count",
    )
    list_filter = ("sync_status", "last_sync_at")
    search_fields = ("departamento__nome", "external_id")
    readonly_fields = [f.name for f in DepartamentoSync._meta.fields]
    ordering = ("-updated_at",)

    def departamento_info(self, obj: DepartamentoSync) -> str:
        return obj.departamento.nome

    departamento_info.short_description = "Departamento"


@admin.register(AtendenteSync)
class AtendenteSyncAdmin(BaseSyncAdmin):
    list_display = (
        "id",
        "atendente_info",
        "external_id_short",
        "sync_status_colored",
        "last_sync_at",
        "retry_count",
    )
    list_filter = ("sync_status", "last_sync_at")
    search_fields = ("atendente__nome", "atendente__email", "external_id")
    readonly_fields = [f.name for f in AtendenteSync._meta.fields]
    ordering = ("-updated_at",)

    def atendente_info(self, obj: AtendenteSync) -> str:
        return obj.atendente.nome

    atendente_info.short_description = "Atendente"


@admin.register(AtendimentoSync)
class AtendimentoSyncAdmin(BaseSyncAdmin):
    list_display = (
        "id",
        "atendimento_info",
        "external_id_short",
        "sync_status_colored",
        "last_sync_at",
        "retry_count",
    )
    list_filter = ("sync_status", "last_sync_at")
    search_fields = ("atendimento__protocolo", "atendimento__contato__nome_contato", "external_id")
    readonly_fields = [f.name for f in AtendimentoSync._meta.fields]
    ordering = ("-updated_at",)

    def atendimento_info(self, obj: AtendimentoSync) -> str:
        # Usa getattr para evitar AttributeError caso protocolo não exista
        protocolo = getattr(obj.atendimento, "protocolo", None)
        return protocolo or f"Atendimento #{obj.atendimento.id}"

    atendimento_info.short_description = "Atendimento"


@admin.register(MensagemSync)
class MensagemSyncAdmin(BaseSyncAdmin):
    list_display = (
        "id",
        "mensagem_info",
        "atendimento_sync",
        "sync_status_colored",
        "last_sync_at",
    )
    list_filter = ("sync_status", "last_sync_at")
    search_fields = ("mensagem__conteudo", "external_id")
    readonly_fields = [f.name for f in MensagemSync._meta.fields]
    ordering = ("-updated_at",)

    def mensagem_info(self, obj: MensagemSync) -> str:
        return f"{obj.mensagem.conteudo[:50]}..."

    mensagem_info.short_description = "Mensagem"

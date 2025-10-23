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

from .models import ClienteSync, ContatoSync, NotionDatabaseConfig, SyncConfig, SyncLog


@admin.register(SyncConfig)
class SyncConfigAdmin(admin.ModelAdmin[SyncConfig]):
    """
    Admin para o model SyncConfig.

    Permite gerenciar configurações do sistema de sincronização.
    """

    list_display = (
        "key",
        "value_preview",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("key", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("key",)

    fieldsets = (
        (
            "Informações Principais",
            {
                "fields": ("key", "value", "description", "is_active")
            },
        ),
        (
            "Metadados",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def value_preview(self, obj: SyncConfig) -> str:
        """
        Retorna preview do valor da configuração.

        Args:
            obj: Instância de SyncConfig.

        Returns:
            Preview limitado do valor.
        """
        value_str = str(obj.value)
        if len(value_str) > 50:
            return f"{value_str[:50]}..."
        return value_str

    value_preview.short_description = "Valor"  # type: ignore


@admin.register(NotionDatabaseConfig)
class NotionDatabaseConfigAdmin(admin.ModelAdmin[NotionDatabaseConfig]):
    """
    Admin para o model NotionDatabaseConfig.

    Permite visualizar e gerenciar configurações de databases do Notion.
    """

    list_display = (
        "model_name",
        "database_name",
        "database_id_short",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("model_name", "database_name", "database_id")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("model_name",)

    fieldsets = (
        (
            "Informações Principais",
            {
                "fields": (
                    "model_name",
                    "database_id",
                    "database_name",
                    "is_active"
                )
            },
        ),
        (
            "Schema",
            {
                "fields": ("properties_schema",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadados",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def database_id_short(self, obj: NotionDatabaseConfig) -> str:
        """
        Retorna versão curta do database_id.

        Args:
            obj: Instância de NotionDatabaseConfig.

        Returns:
            Database ID truncado.
        """
        return f"{obj.database_id[:20]}..."

    database_id_short.short_description = "Database ID"  # type: ignore


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin[SyncLog]):
    """
    Admin para o model SyncLog.

    Permite visualizar e filtrar logs de sincronização.
    """

    list_display = (
        "id",
        "model_name",
        "django_id",
        "operation",
        "direction",
        "status_colored",
        "duration_formatted",
        "retry_count",
        "created_at",
    )
    list_filter = (
        "status",
        "operation",
        "direction",
        "model_name",
        "created_at",
    )
    search_fields = (
        "model_name",
        "django_id",
        "external_id",
        "error_message",
    )
    readonly_fields = (
        "model_name",
        "django_id",
        "external_id",
        "operation",
        "direction",
        "status",
        "error_message",
        "error_details",
        "duration_ms",
        "retry_count",
        "created_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "model_name",
                    "django_id",
                    "external_id",
                )
            },
        ),
        (
            "Operação",
            {
                "fields": (
                    "operation",
                    "direction",
                    "status",
                    "duration_ms",
                    "retry_count",
                )
            },
        ),
        (
            "Erro (se aplicável)",
            {
                "fields": ("error_message", "error_details"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadados",
            {
                "fields": ("created_at",),
            },
        ),
    )

    def status_colored(self, obj: SyncLog) -> str:
        """
        Retorna o status com cor HTML.

        Args:
            obj: Instância de SyncLog.

        Returns:
            HTML com status colorido.
        """
        colors = {
            "success": "green",
            "error": "red",
            "pending": "orange",
            "retry": "blue",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_colored.short_description = "Status"  # type: ignore

    def duration_formatted(self, obj: SyncLog) -> str:
        """
        Retorna a duração formatada.

        Args:
            obj: Instância de SyncLog.

        Returns:
            Duração formatada ou "-".
        """
        if obj.duration_ms is not None:
            return f"{obj.duration_ms}ms"
        return "-"

    duration_formatted.short_description = "Duração"  # type: ignore

    def has_add_permission(
        self,
        request: HttpRequest
    ) -> bool:
        """
        Remove permissão de adicionar logs manualmente.

        Args:
            request: Requisição HTTP.

        Returns:
            False (logs são criados automaticamente).
        """
        return False


@admin.register(ContatoSync)
class ContatoSyncAdmin(admin.ModelAdmin[ContatoSync]):
    """
    Admin para o model ContatoSync.

    Permite visualizar e gerenciar sincronização de Contatos.
    """

    list_display = (
        "id",
        "contato_info",
        "external_id_short",
        "sync_status_colored",
        "last_synced_at",
        "sync_attempts",
    )
    list_filter = (
        "is_synced",
        "last_synced_at",
        "created_at",
    )
    search_fields = (
        "contato__telefone",
        "contato__nome_contato",
        "external_id",
    )
    readonly_fields = (
        "contato",
        "external_id",
        "is_synced",
        "last_synced_at",
        "sync_error",
        "sync_attempts",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    date_hierarchy = "last_synced_at"

    fieldsets = (
        (
            "Relacionamento",
            {
                "fields": ("contato",)
            },
        ),
        (
            "Sincronização",
            {
                "fields": (
                    "external_id",
                    "is_synced",
                    "last_synced_at",
                    "sync_attempts",
                )
            },
        ),
        (
            "Erro (se aplicável)",
            {
                "fields": ("sync_error",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadados",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def contato_info(self, obj: ContatoSync) -> str:
        """
        Retorna informações do contato.

        Args:
            obj: Instância de ContatoSync.

        Returns:
            String com telefone e nome do contato.
        """
        return f"{obj.contato.telefone} - {obj.contato.nome_contato or 'Sem nome'}"

    contato_info.short_description = "Contato"  # type: ignore

    def external_id_short(self, obj: ContatoSync) -> str:
        """
        Retorna versão curta do external_id.

        Args:
            obj: Instância de ContatoSync.

        Returns:
            External ID truncado ou "-".
        """
        if obj.external_id:
            return f"{obj.external_id[:20]}..."
        return "-"

    external_id_short.short_description = "ID Externo"  # type: ignore

    def sync_status_colored(self, obj: ContatoSync) -> str:
        """
        Retorna o status de sincronização com cor HTML.

        Args:
            obj: Instância de ContatoSync.

        Returns:
            HTML com status colorido.
        """
        if obj.is_synced:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Sincronizado</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Não Sincronizado</span>'
            )

    sync_status_colored.short_description = "Status"  # type: ignore

    def has_add_permission(
        self,
        request: HttpRequest
    ) -> bool:
        """
        Remove permissão de adicionar manualmente.

        Args:
            request: Requisição HTTP.

        Returns:
            False (registros criados automaticamente via signals).
        """
        return False


@admin.register(ClienteSync)
class ClienteSyncAdmin(admin.ModelAdmin[ClienteSync]):
    """
    Admin para o model ClienteSync.

    Permite visualizar e gerenciar sincronização de Clientes.
    """

    list_display = (
        "id",
        "cliente_info",
        "external_id_short",
        "sync_status_colored",
        "last_synced_at",
        "sync_attempts",
    )
    list_filter = (
        "is_synced",
        "last_synced_at",
        "created_at",
    )
    search_fields = (
        "cliente__nome_fantasia",
        "cliente__razao_social",
        "cliente__cnpj",
        "external_id",
    )
    readonly_fields = (
        "cliente",
        "external_id",
        "is_synced",
        "last_synced_at",
        "sync_error",
        "sync_attempts",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    date_hierarchy = "last_synced_at"

    fieldsets = (
        (
            "Relacionamento",
            {
                "fields": ("cliente",)
            },
        ),
        (
            "Sincronização",
            {
                "fields": (
                    "external_id",
                    "is_synced",
                    "last_synced_at",
                    "sync_attempts",
                )
            },
        ),
        (
            "Erro (se aplicável)",
            {
                "fields": ("sync_error",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadados",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def cliente_info(self, obj: ClienteSync) -> str:
        """
        Retorna informações do cliente.

        Args:
            obj: Instância de ClienteSync.

        Returns:
            String com nome fantasia do cliente.
        """
        return obj.cliente.nome_fantasia

    cliente_info.short_description = "Cliente"  # type: ignore

    def external_id_short(self, obj: ClienteSync) -> str:
        """
        Retorna versão curta do external_id.

        Args:
            obj: Instância de ClienteSync.

        Returns:
            External ID truncado ou "-".
        """
        if obj.external_id:
            return f"{obj.external_id[:20]}..."
        return "-"

    external_id_short.short_description = "ID Externo"  # type: ignore

    def sync_status_colored(self, obj: ClienteSync) -> str:
        """
        Retorna o status de sincronização com cor HTML.

        Args:
            obj: Instância de ClienteSync.

        Returns:
            HTML com status colorido.
        """
        if obj.is_synced:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Sincronizado</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Não Sincronizado</span>'
            )

    sync_status_colored.short_description = "Status"  # type: ignore

    def has_add_permission(
        self,
        request: HttpRequest
    ) -> bool:
        """
        Remove permissão de adicionar manualmente.

        Args:
            request: Requisição HTTP.

        Returns:
            False (registros criados automaticamente via signals).
        """
        return False

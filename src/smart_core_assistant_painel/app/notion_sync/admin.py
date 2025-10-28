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
    ClienteSync,
    ContatoSync,
    DepartamentoSync,
    NotionDatabaseConfig,
)


@admin.register(NotionDatabaseConfig)
class NotionDatabaseConfigAdmin(admin.ModelAdmin[NotionDatabaseConfig]):
    """
    Admin para o model NotionDatabaseConfig.

    Permite visualizar e gerenciar configurações de databases do Notion.
    """

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

    fieldsets = (
        (
            "Informações Principais",
            {
                "fields": (
                    "slug",
                    "name",
                    "django_model",
                    "notion_database_id",
                    "sync_enabled",
                )
            },
        ),
        (
            "Schema",
            {
                "fields": ("notion_schema", "field_mappings"),
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

    def notion_database_id_short(self, obj: NotionDatabaseConfig) -> str:
        """
        Retorna versão curta do notion_database_id.

        Args:
            obj: Instância de NotionDatabaseConfig.

        Returns:
            Database ID truncado.
        """
        if obj.notion_database_id:
            return f"{str(obj.notion_database_id)[:20]}..."
        return "-"

    notion_database_id_short.short_description = "Database ID"  # type: ignore


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
        "last_sync_at",
        "retry_count",
    )
    list_filter = (
        "sync_status",
        "last_sync_at",
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
        "sync_status",
        "last_sync_at",
        "sync_error",
        "retry_count",
        "sync_metadata",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    date_hierarchy = "last_sync_at"

    fieldsets = (
        (
            "Relacionamento",
            {"fields": ("contato",)},
        ),
        (
            "Sincronização",
            {
                "fields": (
                    "external_id",
                    "sync_status",
                    "last_sync_at",
                    "retry_count",
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
                "fields": ("sync_metadata", "created_at", "updated_at"),
                "classes": ("collapse",),
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
            return f"{str(obj.external_id)[:20]}..."
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

    sync_status_colored.short_description = "Status"  # type: ignore

    def has_add_permission(self, request: HttpRequest) -> bool:
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
        "last_sync_at",
        "retry_count",
    )
    list_filter = (
        "sync_status",
        "last_sync_at",
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
        "sync_status",
        "last_sync_at",
        "sync_error",
        "retry_count",
        "notion_properties",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    date_hierarchy = "last_sync_at"

    fieldsets = (
        (
            "Relacionamento",
            {"fields": ("cliente",)},
        ),
        (
            "Sincronização",
            {
                "fields": (
                    "external_id",
                    "sync_status",
                    "last_sync_at",
                    "retry_count",
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
                "fields": ("notion_properties", "created_at", "updated_at"),
                "classes": ("collapse",),
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
            return f"{str(obj.external_id)[:20]}..."
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

    sync_status_colored.short_description = "Status"  # type: ignore

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Remove permissão de adicionar manualmente.

        Args:
            request: Requisição HTTP.

        Returns:
            False (registros criados automaticamente via signals).
        """
        return False


@admin.register(DepartamentoSync)
class DepartamentoSyncAdmin(admin.ModelAdmin[DepartamentoSync]):
    """
    Admin para o model DepartamentoSync.

    Permite visualizar e gerenciar sincronização de Departamentos.
    """

    list_display = (
        "id",
        "departamento_info",
        "external_id_short",
        "sync_status_colored",
        "last_sync_at",
        "count_atendentes",
        "retry_count",
    )
    list_filter = (
        "sync_status",
        "last_sync_at",
        "created_at",
    )
    search_fields = (
        "departamento__nome",
        "departamento__slug",
        "external_id",
    )
    readonly_fields = (
        "departamento",
        "external_id",
        "sync_status",
        "last_sync_at",
        "sync_error",
        "retry_count",
        "notion_properties",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    date_hierarchy = "last_sync_at"

    fieldsets = (
        (
            "Relacionamento",
            {"fields": ("departamento",)},
        ),
        (
            "Sincronização",
            {
                "fields": (
                    "external_id",
                    "sync_status",
                    "last_sync_at",
                    "retry_count",
                )
            },
        ),
        (
            "Dados Formatados",
            {
                "fields": (
                    "nome_formatado",
                    "slug_formatado",
                    "status_formatado",
                    "count_atendentes",
                ),
                "classes": ("collapse",),
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
                "fields": ("notion_properties", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def departamento_info(self, obj: DepartamentoSync) -> str:
        """
        Retorna informações do departamento.

        Args:
            obj: Instância de DepartamentoSync.

        Returns:
            String com nome e status do departamento.
        """
        status = "✓" if obj.departamento.ativo else "✗"
        return f"{obj.departamento.nome} {status}"

    departamento_info.short_description = "Departamento"  # type: ignore

    def external_id_short(self, obj: DepartamentoSync) -> str:
        """
        Retorna versão curta do external_id.

        Args:
            obj: Instância de DepartamentoSync.

        Returns:
            External ID truncado ou "-".
        """
        if obj.external_id:
            return f"{str(obj.external_id)[:20]}..."
        return "-"

    external_id_short.short_description = "ID Externo"  # type: ignore

    def sync_status_colored(self, obj: DepartamentoSync) -> str:
        """
        Retorna o status de sincronização com cor HTML.

        Args:
            obj: Instância de DepartamentoSync.

        Returns:
            HTML com status colorido.
        """
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

    sync_status_colored.short_description = "Status"  # type: ignore

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Remove permissão de adicionar manualmente.

        Args:
            request: Requisição HTTP.

        Returns:
            False (registros criados automaticamente via signals).
        """
        return False


@admin.register(AtendenteSync)
class AtendenteSyncAdmin(admin.ModelAdmin[AtendenteSync]):
    """
    Admin para o model AtendenteSync.

    Permite visualizar e gerenciar sincronização de Atendentes.
    """

    list_display = (
        "id",
        "atendente_info",
        "departamento_nome",
        "external_id_short",
        "sync_status_colored",
        "last_sync_at",
        "carga_info",
        "retry_count",
    )
    list_filter = (
        "sync_status",
        "last_sync_at",
        "created_at",
        "departamento_sync__departamento__nome",
    )
    search_fields = (
        "atendente__nome",
        "atendente__cargo",
        "atendente__email",
        "atendente__telefone",
        "external_id",
    )
    readonly_fields = (
        "atendente",
        "external_id",
        "sync_status",
        "last_sync_at",
        "sync_error",
        "retry_count",
        "notion_properties",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    date_hierarchy = "last_sync_at"

    fieldsets = (
        (
            "Relacionamento",
            {"fields": ("atendente", "departamento_sync")},
        ),
        (
            "Sincronização",
            {
                "fields": (
                    "external_id",
                    "sync_status",
                    "last_sync_at",
                    "retry_count",
                )
            },
        ),
        (
            "Dados Formatados",
            {
                "fields": (
                    "nome_formatado",
                    "cargo_formatado",
                    "departamento_nome",
                    "status_formatado",
                    "disponibilidade_formatada",
                    "carga_atual",
                    "capacidade_maxima",
                ),
                "classes": ("collapse",),
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
                "fields": ("notion_properties", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def atendente_info(self, obj: AtendenteSync) -> str:
        """
        Retorna informações do atendente.

        Args:
            obj: Instância de AtendenteSync.

        Returns:
            String com nome e cargo do atendente.
        """
        status = "✓" if obj.atendente.ativo else "✗"
        return f"{obj.atendente.nome} - {obj.atendente.cargo} {status}"

    atendente_info.short_description = "Atendente"  # type: ignore

    def departamento_nome(self, obj: AtendenteSync) -> str:
        """
        Retorna o nome do departamento.

        Args:
            obj: Instância de AtendenteSync.

        Returns:
            Nome do departamento ou "-".
        """
        return (
            obj.atendente.departamento.nome
            if obj.atendente.departamento
            else "-"
        )

    departamento_nome.short_description = "Departamento"  # type: ignore

    def external_id_short(self, obj: AtendenteSync) -> str:
        """
        Retorna versão curta do external_id.

        Args:
            obj: Instância de AtendenteSync.

        Returns:
            External ID truncado ou "-".
        """
        if obj.external_id:
            return f"{str(obj.external_id)[:20]}..."
        return "-"

    external_id_short.short_description = "ID Externo"  # type: ignore

    def carga_info(self, obj: AtendenteSync) -> str:
        """
        Retorna informação da carga de trabalho.

        Args:
            obj: Instância de AtendenteSync.

        Returns:
            String com carga atual/capacidade máxima.
        """
        if obj.capacidade_maxima > 0:
            pct = (obj.carga_atual / obj.capacidade_maxima) * 100
            cor = "green" if pct < 70 else "orange" if pct < 90 else "red"
            return format_html(
                '<span style="color: {};">{}/{} ({:.0f}%)</span>',
                cor,
                obj.carga_atual,
                obj.capacidade_maxima,
                pct,
            )
        return f"{obj.carga_atual}/{obj.capacidade_maxima}"

    carga_info.short_description = "Carga"  # type: ignore

    def sync_status_colored(self, obj: AtendenteSync) -> str:
        """
        Retorna o status de sincronização com cor HTML.

        Args:
            obj: Instância de AtendenteSync.

        Returns:
            HTML com status colorido.
        """
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

    sync_status_colored.short_description = "Status"  # type: ignore

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Remove permissão de adicionar manualmente.

        Args:
            request: Requisição HTTP.

        Returns:
            False (registros criados automaticamente via signals).
        """
        return False

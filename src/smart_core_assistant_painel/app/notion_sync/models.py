"""
Models para tracking e configuração da sincronização com plataformas externas.

Este módulo contém os models que armazenam:
- Configurações do sistema de sincronização (SyncConfig)
- Logs e auditoria de operações (SyncLog)
- Metadados de sincronização por model (Shadow Models)
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, override

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from ..ui.clientes.models import Cliente, Contato


class SyncConfig(models.Model):
    """
    Model para armazenar configurações do sistema de sincronização.

    Permite configurar tokens, database IDs, e outras opções necessárias
    para a integração com plataformas externas sem hardcoding.

    Attributes:
        key: Chave única da configuração (ex: "notion_token").
        value: Valor da configuração (JSON para flexibilidade).
        description: Descrição do propósito da configuração.
        is_active: Se a configuração está ativa.
        created_at: Data de criação da configuração.
        updated_at: Data da última atualização.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    key: models.CharField[str] = models.CharField(
        max_length=100,
        unique=True,
        help_text="Chave única da configuração (ex: 'notion_token')"
    )
    value: models.JSONField[Any] = models.JSONField(
        help_text="Valor da configuração (pode ser string, dict, list, etc)"
    )
    description: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição do propósito desta configuração"
    )
    is_active: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Se a configuração está ativa"
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação da configuração"
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atualização"
    )

    class Meta:
        verbose_name = "Configuração de Sincronização"
        verbose_name_plural = "Configurações de Sincronização"
        ordering = ["key"]
        db_table = "notion_sync_config"

    @override
    def __str__(self) -> str:
        """Retorna representação em string da configuração."""
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(
        cls,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Obtém o valor de uma configuração pela chave.

        Args:
            key: Chave da configuração desejada.
            default: Valor padrão se configuração não existir.

        Returns:
            Valor da configuração ou valor padrão.
        """
        try:
            config = cls.objects.get(key=key, is_active=True)
            return config.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(
        cls,
        key: str,
        value: Any,
        description: str | None = None
    ) -> "SyncConfig":
        """
        Define ou atualiza o valor de uma configuração.

        Args:
            key: Chave da configuração.
            value: Valor a ser armazenado.
            description: Descrição opcional da configuração.

        Returns:
            Instância da configuração criada ou atualizada.
        """
        config, created = cls.objects.update_or_create(
            key=key,
            defaults={
                "value": value,
                "description": description,
                "is_active": True,
            }
        )
        return config


class NotionDatabaseConfig(models.Model):
    """
    Model para armazenar configurações e IDs dos databases no Notion.

    Este model persiste os IDs dos databases criados no Notion e os
    mapeamentos entre models Django e databases Notion, permitindo
    que o sistema sempre saiba qual database usar para cada model.

    Attributes:
        model_name: Nome do modelo Django (ex: "Cliente", "Contato").
        database_id: ID do database no Notion.
        database_name: Nome do database no Notion.
        properties_schema: Schema das propriedades/colunas (JSON).
        is_active: Se esta configuração está ativa.
        created_at: Data de criação da configuração.
        updated_at: Data da última atualização.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    model_name: models.CharField[str] = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome do modelo Django (ex: 'Cliente', 'Contato')"
    )
    database_id: models.CharField[str] = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID do database no Notion"
    )
    database_name: models.CharField[str] = models.CharField(
        max_length=200,
        help_text="Nome do database no Notion"
    )
    properties_schema: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Schema das propriedades/colunas do database"
    )
    is_active: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Se esta configuração está ativa"
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação da configuração"
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atualização"
    )

    class Meta:
        verbose_name = "Configuração de Database Notion"
        verbose_name_plural = "Configurações de Databases Notion"
        ordering = ["model_name"]
        db_table = "notion_database_config"

    @override
    def __str__(self) -> str:
        """Retorna representação em string da configuração."""
        return f"{self.model_name} → {self.database_name} ({self.database_id[:8]}...)"

    @classmethod
    def get_database_id(cls, model_name: str) -> str | None:
        """
        Obtém o database ID para um modelo Django.

        Args:
            model_name: Nome do modelo Django.

        Returns:
            Database ID do Notion ou None se não encontrado.
        """
        try:
            config = cls.objects.get(model_name=model_name, is_active=True)
            return config.database_id
        except cls.DoesNotExist:
            return None

    @classmethod
    def set_database(
        cls,
        model_name: str,
        database_id: str,
        database_name: str,
        properties_schema: dict[str, Any] | None = None
    ) -> "NotionDatabaseConfig":
        """
        Define ou atualiza a configuração de database para um modelo.

        Args:
            model_name: Nome do modelo Django.
            database_id: ID do database no Notion.
            database_name: Nome do database no Notion.
            properties_schema: Schema das propriedades.

        Returns:
            Instância da configuração criada ou atualizada.
        """
        config, created = cls.objects.update_or_create(
            model_name=model_name,
            defaults={
                "database_id": database_id,
                "database_name": database_name,
                "properties_schema": properties_schema or {},
                "is_active": True,
            }
        )
        return config


class SyncLog(models.Model):
    """
    Model para logging e auditoria de operações de sincronização.

    Registra todas as tentativas de sincronização, sucessos e falhas,
    permitindo rastreabilidade e debugging.

    Attributes:
        model_name: Nome do modelo Django sincronizado.
        django_id: ID do registro no Django.
        external_id: ID do registro na plataforma externa.
        operation: Tipo de operação (create, update, delete).
        direction: Direção da sincronização (django_to_external, etc).
        status: Status da operação (success, error, pending).
        error_message: Mensagem de erro se operação falhou.
        error_details: Detalhes adicionais do erro (JSON).
        duration_ms: Duração da operação em milissegundos.
        created_at: Timestamp da operação.
    """

    OPERATION_CHOICES = [
        ("create", "Criar"),
        ("update", "Atualizar"),
        ("delete", "Deletar"),
        ("sync", "Sincronizar"),
    ]

    DIRECTION_CHOICES = [
        ("django_to_external", "Django → Externa"),
        ("external_to_django", "Externa → Django"),
        ("bidirectional", "Bidirecional"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("success", "Sucesso"),
        ("error", "Erro"),
        ("retry", "Tentando Novamente"),
    ]

    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    model_name: models.CharField[str] = models.CharField(
        max_length=100,
        help_text="Nome do modelo Django (ex: 'Cliente', 'Contato')"
    )
    django_id: models.IntegerField[int | None] = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID do registro no Django"
    )
    external_id: models.CharField[str | None] = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID do registro na plataforma externa"
    )
    operation: models.CharField[str] = models.CharField(
        max_length=20,
        choices=OPERATION_CHOICES,
        help_text="Tipo de operação realizada"
    )
    direction: models.CharField[str] = models.CharField(
        max_length=30,
        choices=DIRECTION_CHOICES,
        help_text="Direção da sincronização"
    )
    status: models.CharField[str] = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Status da operação"
    )
    error_message: models.TextField[str | None] = models.TextField(
        null=True,
        blank=True,
        help_text="Mensagem de erro se operação falhou"
    )
    error_details: models.JSONField[dict[str, Any] | None] = models.JSONField(
        null=True,
        blank=True,
        help_text="Detalhes adicionais do erro (stack trace, etc)"
    )
    duration_ms: models.IntegerField[int | None] = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duração da operação em milissegundos"
    )
    retry_count: models.IntegerField[int] = models.IntegerField(
        default=0,
        help_text="Número de tentativas de retry"
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp da operação",
        db_index=True
    )

    class Meta:
        verbose_name = "Log de Sincronização"
        verbose_name_plural = "Logs de Sincronização"
        ordering = ["-created_at"]
        db_table = "notion_sync_log"
        indexes = [
            models.Index(
                fields=["model_name", "django_id"],
                name="idx_sync_log_model"
            ),
            models.Index(
                fields=["status", "created_at"],
                name="idx_sync_log_status"
            ),
        ]

    @override
    def __str__(self) -> str:
        """Retorna representação em string do log."""
        return (
            f"{self.model_name}#{self.django_id} - "
            f"{self.operation} [{self.status}]"
        )

    @classmethod
    def log_operation(
        cls,
        model_name: str,
        django_id: int | None,
        external_id: str | None,
        operation: str,
        direction: str,
        status: str,
        error_message: str | None = None,
        error_details: dict[str, Any] | None = None,
        duration_ms: int | None = None,
    ) -> "SyncLog":
        """
        Cria um novo log de operação de sincronização.

        Args:
            model_name: Nome do modelo Django.
            django_id: ID do registro no Django.
            external_id: ID do registro na plataforma externa.
            operation: Tipo de operação (create, update, delete, sync).
            direction: Direção da sincronização.
            status: Status da operação (pending, success, error, retry).
            error_message: Mensagem de erro (se aplicável).
            error_details: Detalhes do erro (se aplicável).
            duration_ms: Duração da operação em milissegundos.

        Returns:
            Instância do log criado.
        """
        return cls.objects.create(
            model_name=model_name,
            django_id=django_id,
            external_id=external_id,
            operation=operation,
            direction=direction,
            status=status,
            error_message=error_message,
            error_details=error_details,
            duration_ms=duration_ms,
        )


class ContatoSync(models.Model):
    """
    Shadow model para tracking de sincronização de Contato.

    Armazena metadados sobre a sincronização de cada Contato com a
    plataforma externa, permitindo rastrear estado e status.

    Attributes:
        contato: Relação one-to-one com o model Contato original.
        external_id: ID do registro na plataforma externa (ex: page_id).
        is_synced: Se o registro está sincronizado com a externa.
        last_synced_at: Timestamp da última sincronização bem-sucedida.
        sync_error: Última mensagem de erro (se houver).
        sync_attempts: Número de tentativas de sincronização.
        created_at: Data de criação do tracking.
        updated_at: Data da última atualização do tracking.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    contato: models.OneToOneField["Contato", "Contato"] = (
        models.OneToOneField(
            "clientes.Contato",
            on_delete=models.CASCADE,
            related_name="sync_metadata",
            help_text="Contato original sendo sincronizado"
        )
    )
    external_id: models.CharField[str | None] = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="ID do registro na plataforma externa (ex: page_id Notion)"
    )
    is_synced: models.BooleanField[bool] = models.BooleanField(
        default=False,
        help_text="Se o registro está atualmente sincronizado"
    )
    last_synced_at: models.DateTimeField[datetime | None] = (
        models.DateTimeField(
            null=True,
            blank=True,
            help_text="Timestamp da última sincronização bem-sucedida"
        )
    )
    sync_error: models.TextField[str | None] = models.TextField(
        null=True,
        blank=True,
        help_text="Última mensagem de erro de sincronização"
    )
    sync_attempts: models.IntegerField[int] = models.IntegerField(
        default=0,
        help_text="Número total de tentativas de sincronização"
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do tracking"
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atualização do tracking"
    )

    class Meta:
        verbose_name = "Sincronização de Contato"
        verbose_name_plural = "Sincronizações de Contatos"
        ordering = ["-updated_at"]
        db_table = "notion_sync_contato"

    @override
    def __str__(self) -> str:
        """Retorna representação em string do tracking."""
        status = "Sincronizado" if self.is_synced else "Não Sincronizado"
        return f"Contato #{self.contato_id} - {status}"

    def mark_as_synced(
        self,
        external_id: str
    ) -> None:
        """
        Marca o contato como sincronizado com sucesso.

        Args:
            external_id: ID do registro criado na plataforma externa.
        """
        self.external_id = external_id
        self.is_synced = True
        self.last_synced_at = timezone.now()
        self.sync_error = None
        self.sync_attempts += 1
        self.save()

    def mark_as_failed(
        self,
        error_message: str
    ) -> None:
        """
        Marca o contato como falha na sincronização.

        Args:
            error_message: Mensagem de erro da falha.
        """
        self.is_synced = False
        self.sync_error = error_message
        self.sync_attempts += 1
        self.save()


class ClienteSync(models.Model):
    """
    Shadow model para tracking de sincronização de Cliente.

    Armazena metadados sobre a sincronização de cada Cliente com a
    plataforma externa, permitindo rastrear estado e status.

    Attributes:
        cliente: Relação one-to-one com o model Cliente original.
        external_id: ID do registro na plataforma externa (ex: page_id).
        is_synced: Se o registro está sincronizado com a externa.
        last_synced_at: Timestamp da última sincronização bem-sucedida.
        sync_error: Última mensagem de erro (se houver).
        sync_attempts: Número de tentativas de sincronização.
        created_at: Data de criação do tracking.
        updated_at: Data da última atualização do tracking.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    cliente: models.OneToOneField["Cliente", "Cliente"] = (
        models.OneToOneField(
            "clientes.Cliente",
            on_delete=models.CASCADE,
            related_name="sync_metadata",
            help_text="Cliente original sendo sincronizado"
        )
    )
    external_id: models.CharField[str | None] = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="ID do registro na plataforma externa (ex: page_id Notion)"
    )
    is_synced: models.BooleanField[bool] = models.BooleanField(
        default=False,
        help_text="Se o registro está atualmente sincronizado"
    )
    last_synced_at: models.DateTimeField[datetime | None] = (
        models.DateTimeField(
            null=True,
            blank=True,
            help_text="Timestamp da última sincronização bem-sucedida"
        )
    )
    sync_error: models.TextField[str | None] = models.TextField(
        null=True,
        blank=True,
        help_text="Última mensagem de erro de sincronização"
    )
    sync_attempts: models.IntegerField[int] = models.IntegerField(
        default=0,
        help_text="Número total de tentativas de sincronização"
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do tracking"
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atualização do tracking"
    )

    class Meta:
        verbose_name = "Sincronização de Cliente"
        verbose_name_plural = "Sincronizações de Clientes"
        ordering = ["-updated_at"]
        db_table = "notion_sync_cliente"

    @override
    def __str__(self) -> str:
        """Retorna representação em string do tracking."""
        status = "Sincronizado" if self.is_synced else "Não Sincronizado"
        return f"Cliente #{self.cliente_id} - {status}"

    def mark_as_synced(
        self,
        external_id: str
    ) -> None:
        """
        Marca o cliente como sincronizado com sucesso.

        Args:
            external_id: ID do registro criado na plataforma externa.
        """
        self.external_id = external_id
        self.is_synced = True
        self.last_synced_at = timezone.now()
        self.sync_error = None
        self.sync_attempts += 1
        self.save()

    def mark_as_failed(
        self,
        error_message: str
    ) -> None:
        """
        Marca o cliente como falha na sincronização.

        Args:
            error_message: Mensagem de erro da falha.
        """
        self.is_synced = False
        self.sync_error = error_message
        self.sync_attempts += 1
        self.save()

"""Modelos do adapter AppFlowy.

Este módulo define a estrutura mínima de dados para espelhar um Grid
de Atendimentos no servidor Django, servindo como fonte de verdade para
sincronização com o cliente AppFlowy Desktop.

Comentários em Português e anotações de tipo completas conforme padrão
do projeto.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional, Union

from django.db import models
from django.utils import timezone


class ColumnType(models.TextChoices):
    """Tipos de coluna suportados no Grid.

    Mantém um conjunto básico suficiente para o MVI.
    """

    STRING = "string", "String"
    TEXT = "text", "Text"
    NUMBER = "number", "Number"
    DATE = "date", "Date"
    SELECT = "select", "Select"
    MULTI_SELECT = "multi_select", "Multi Select"
    BOOLEAN = "boolean", "Boolean"


class AppFlowyWorkspace(models.Model):
    """Workspace lógico do AppFlowy.

    No MVI, geralmente teremos um único workspace `default`.
    """

    workspace_id: models.UUIDField[uuid.UUID] = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único do workspace",
    )
    name: models.CharField[str] = models.CharField(
        max_length=100,
        help_text="Nome do workspace",
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do workspace",
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data de atualização do workspace",
    )

    class Meta:
        db_table = "appflowy_workspace"
        verbose_name = "Workspace AppFlowy"
        verbose_name_plural = "Workspaces AppFlowy"

    def __str__(self) -> str:  # noqa: D401
        """Representação textual do workspace."""

        return f"Workspace({self.name})"


class AppFlowyGrid(models.Model):
    """Grid (Database) do AppFlowy.

    Representa um conjunto de colunas e linhas, espelhando a entidade
    operacional (ex.: Atendimentos).
    """

    grid_id: models.UUIDField[uuid.UUID] = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único do grid",
    )
    workspace: models.ForeignKey[AppFlowyWorkspace] = models.ForeignKey(
        AppFlowyWorkspace,
        on_delete=models.CASCADE,
        related_name="grids",
        help_text="Workspace ao qual o grid pertence",
    )
    name: models.CharField[str] = models.CharField(
        max_length=100,
        help_text="Nome do grid",
    )
    description: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição opcional do grid",
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do grid",
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data de atualização do grid",
    )

    class Meta:
        db_table = "appflowy_grid"
        verbose_name = "Grid AppFlowy"
        verbose_name_plural = "Grids AppFlowy"

    def __str__(self) -> str:  # noqa: D401
        """Representação textual do grid."""

        return f"Grid({self.name})"


class AppFlowyColumn(models.Model):
    """Coluna de metadados de um Grid."""

    column_id: models.UUIDField[uuid.UUID] = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único da coluna",
    )
    grid: models.ForeignKey[AppFlowyGrid] = models.ForeignKey(
        AppFlowyGrid,
        on_delete=models.CASCADE,
        related_name="columns",
        help_text="Grid ao qual a coluna pertence",
    )
    key: models.CharField[str] = models.CharField(
        max_length=50,
        help_text="Chave/slug da coluna (ex.: 'status', 'priority')",
    )
    name: models.CharField[str] = models.CharField(
        max_length=100,
        help_text="Nome exibido da coluna",
    )
    type: models.CharField[str] = models.CharField(
        max_length=20,
        choices=ColumnType.choices,
        help_text="Tipo da coluna",
    )
    order: models.IntegerField[int] = models.IntegerField(
        default=0,
        help_text="Ordem de exibição",
    )
    required: models.BooleanField[bool] = models.BooleanField(
        default=False,
        help_text="Indica se a coluna é obrigatória",
    )

    class Meta:
        db_table = "appflowy_column"
        verbose_name = "Coluna AppFlowy"
        verbose_name_plural = "Colunas AppFlowy"
        unique_together = ("grid", "key")
        ordering = ["order", "name"]

    def __str__(self) -> str:  # noqa: D401
        """Representação textual da coluna."""

        return f"Column({self.key}:{self.type})"


class AppFlowyRow(models.Model):
    """Linha de dados de um Grid."""

    row_id: models.UUIDField[uuid.UUID] = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único da linha",
    )
    grid: models.ForeignKey[AppFlowyGrid] = models.ForeignKey(
        AppFlowyGrid,
        on_delete=models.CASCADE,
        related_name="rows",
        help_text="Grid ao qual a linha pertence",
    )
    ticket_id: models.CharField[str] = models.CharField(
        max_length=120,
        db_index=True,
        help_text="Chave idempotente associada ao domínio (ex.: Atendimento)",
    )
    received_at: models.DateTimeField[datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data/hora de recebimento inicial",
    )
    name: models.CharField[str] = models.CharField(
        max_length=200,
        help_text="Nome/título do item",
    )
    channel: models.CharField[str] = models.CharField(
        max_length=50,
        help_text="Canal de origem (ex.: whatsapp)",
    )
    status: models.CharField[str] = models.CharField(
        max_length=50,
        help_text="Status normalizado",
    )
    priority: models.CharField[str] = models.CharField(
        max_length=20,
        help_text="Prioridade normalizada",
    )
    assigned_to: models.CharField[str] = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Responsável pelo item",
    )
    tags: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags do item",
    )
    last_message: models.TextField[str] = models.TextField(
        blank=True,
        default="",
        help_text="Última mensagem relevante (se aplicável)",
    )
    sla_due: models.DateTimeField[datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data/hora de SLA (se aplicável)",
    )
    version: models.IntegerField[int] = models.IntegerField(
        default=1,
        help_text="Versão incrementada a cada atualização",
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data de atualização da linha",
    )

    class Meta:
        db_table = "appflowy_row"
        verbose_name = "Linha AppFlowy"
        verbose_name_plural = "Linhas AppFlowy"
        indexes = [
            models.Index(fields=["grid", "ticket_id"]),
            models.Index(fields=["grid", "updated_at"]),
        ]

    def __str__(self) -> str:  # noqa: D401
        """Representação textual da linha."""

        return f"Row({self.ticket_id}:{self.status})"


class AppFlowyRowValue(models.Model):
    """Valores de propriedades por linha.

    Estrutura flexível que armazena o valor da coluna em formato JSON,
    suficiente para o MVI sem tipagem por coluna.
    """

    value_id: models.UUIDField[uuid.UUID] = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único do valor",
    )
    row: models.ForeignKey[AppFlowyRow] = models.ForeignKey(
        AppFlowyRow,
        on_delete=models.CASCADE,
        related_name="values",
        help_text="Linha à qual o valor pertence",
    )
    column: models.ForeignKey[AppFlowyColumn] = models.ForeignKey(
        AppFlowyColumn,
        on_delete=models.CASCADE,
        related_name="values",
        help_text="Coluna à qual o valor pertence",
    )
    JSONScalar = Union[str, int, float, bool, None]
    JSONValue = Union[dict[str, Any], list[Any], JSONScalar]

    value: models.JSONField[JSONValue] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Valor armazenado em JSON",
    )

    class Meta:
        db_table = "appflowy_row_value"
        verbose_name = "Valor de Coluna AppFlowy"
        verbose_name_plural = "Valores de Coluna AppFlowy"
        unique_together = ("row", "column")

    def __str__(self) -> str:  # noqa: D401
        """Representação textual do valor."""

        return f"Value(row={self.row_id})"


class AppFlowySyncState(models.Model):
    """Estado de sincronização por Grid.

    Controla o `since` para deltas incrementais e auxilia na paginação.
    """

    grid: models.OneToOneField[AppFlowyGrid] = models.OneToOneField(
        AppFlowyGrid,
        on_delete=models.CASCADE,
        related_name="sync_state",
        help_text="Grid associado ao estado de sincronização",
    )
    since: models.DateTimeField[datetime] = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp do último delta consumido",
    )

    class Meta:
        db_table = "appflowy_sync_state"
        verbose_name = "Estado de Sincronização"
        verbose_name_plural = "Estados de Sincronização"

    def __str__(self) -> str:  # noqa: D401
        """Representação textual do estado de sincronização."""

        return (
            f"SyncState(grid={self.grid_id}, since={self.since.isoformat()})"
        )

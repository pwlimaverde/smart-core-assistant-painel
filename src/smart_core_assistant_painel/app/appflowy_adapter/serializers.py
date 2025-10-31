"""Serializers do adapter AppFlowy.

Fornece serializers para Workspace, Grid, Column e Row.

Comentários em Português conforme padrão do projeto.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import (
    AppFlowyColumn,
    AppFlowyGrid,
    AppFlowyRow,
    AppFlowyWorkspace,
)


class AppFlowyWorkspaceSerializer(serializers.ModelSerializer):
    """Serializer para `AppFlowyWorkspace`."""

    class Meta:
        model = AppFlowyWorkspace
        fields = (
            "workspace_id",
            "name",
            "created_at",
            "updated_at",
        )


class AppFlowyGridSerializer(serializers.ModelSerializer):
    """Serializer para `AppFlowyGrid`."""

    class Meta:
        model = AppFlowyGrid
        fields = (
            "grid_id",
            "workspace",
            "name",
            "description",
            "created_at",
            "updated_at",
        )


class AppFlowyColumnSerializer(serializers.ModelSerializer):
    """Serializer para `AppFlowyColumn`."""

    class Meta:
        model = AppFlowyColumn
        fields = (
            "column_id",
            "grid",
            "key",
            "name",
            "type",
            "order",
            "required",
        )


class AppFlowyRowSerializer(serializers.ModelSerializer):
    """Serializer para `AppFlowyRow`."""

    class Meta:
        model = AppFlowyRow
        fields = (
            "row_id",
            "grid",
            "ticket_id",
            "received_at",
            "name",
            "channel",
            "status",
            "priority",
            "assigned_to",
            "tags",
            "last_message",
            "sla_due",
            "version",
            "updated_at",
        )


def validate_if_match_version(
    header_value: str | None,
    current_version: int,
) -> tuple[bool, str]:
    """Valida o cabeçalho `If-Match` para controle de versão.

    Retorna uma tupla `(ok, message)`.
    """

    if header_value is None:
        return False, "If-Match ausente"
    try:
        expected = int(header_value)
    except ValueError:
        return False, "If-Match inválido"
    if expected != current_version:
        return False, "Versão divergente"
    return True, "ok"
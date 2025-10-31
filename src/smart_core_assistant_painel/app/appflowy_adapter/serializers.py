"""Serializers do adapter AppFlowy.

Fornece serializers para Workspace, Grid, Column e Row.

Comentários em Português conforme padrão do projeto.
"""

from __future__ import annotations

from typing import Any, Iterable

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


# --- Validações de payload (escrita) ---

# Conjuntos mínimos permitidos no MVI para normalização
ALLOWED_CHANNELS: set[str] = {
    "whatsapp",
    "email",
    "web",
    "telegram",
}

ALLOWED_STATUS: set[str] = {
    "new",
    "open",
    "in_progress",
    "waiting",
    "closed",
    "canceled",
}

ALLOWED_PRIORITIES: set[str] = {
    "low",
    "medium",
    "high",
    "urgent",
}


class AppFlowyRowWriteSerializer(serializers.ModelSerializer):
    """Serializer de escrita para `AppFlowyRow`.

    Aplica validações de tipos, ranges e campos obrigatórios para
    criação/atualização idempotente de linhas.
    """

    class Meta:
        model = AppFlowyRow
        # Campos aceitos no payload (grid vem da rota)
        fields = (
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
        )

    def validate_ticket_id(self, value: Any) -> str:
        """`ticket_id` deve ser string não vazia (1..120)."""

        s: str = str(value).strip()
        if not s:
            raise serializers.ValidationError("ticket_id obrigatório")
        if len(s) > 120:
            raise serializers.ValidationError("ticket_id muito longo")
        return s

    def validate_name(self, value: Any) -> str:
        """`name` deve ser string não vazia (1..200)."""

        s: str = str(value).strip()
        if not s:
            raise serializers.ValidationError("name obrigatório")
        if len(s) > 200:
            raise serializers.ValidationError("name muito longo")
        return s

    def validate_channel(self, value: Any) -> str:
        """`channel` deve pertencer ao conjunto permitido."""

        s: str = str(value).strip().lower()
        if s not in ALLOWED_CHANNELS:
            raise serializers.ValidationError(
                f"channel inválido: {s}"
            )
        return s

    def validate_status(self, value: Any) -> str:
        """`status` deve pertencer ao conjunto permitido."""

        s: str = str(value).strip().lower()
        if s not in ALLOWED_STATUS:
            raise serializers.ValidationError(f"status inválido: {s}")
        return s

    def validate_priority(self, value: Any) -> str:
        """`priority` deve pertencer ao conjunto permitido."""

        s: str = str(value).strip().lower()
        if s not in ALLOWED_PRIORITIES:
            raise serializers.ValidationError(
                f"priority inválida: {s}"
            )
        return s

    def validate_assigned_to(self, value: Any) -> str:
        """`assigned_to` é opcional, limita tamanho (<=120)."""

        s: str = str(value).strip()
        if len(s) > 120:
            raise serializers.ValidationError(
                "assigned_to muito longo"
            )
        return s

    def validate_tags(self, value: Any) -> list[str]:
        """`tags` deve ser lista de strings simples."""

        if value is None:
            return []
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            raise serializers.ValidationError("tags deve ser uma lista")
        out: list[str] = []
        for item in value:
            s = str(item).strip()
            if not s:
                raise serializers.ValidationError(
                    "tags não deve conter vazios"
                )
            out.append(s)
        return out

    def validate_last_message(self, value: Any) -> str:
        """`last_message` opcional, normaliza para string curta."""

        s: str = str(value)
        if len(s) > 5000:
            raise serializers.ValidationError(
                "last_message muito longo"
            )
        return s

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Valida coerência temporal entre `received_at` e `sla_due`."""

        received = attrs.get("received_at")
        sla_due = attrs.get("sla_due")
        if received and sla_due and sla_due < received:
            raise serializers.ValidationError(
                "sla_due deve ser posterior a received_at"
            )
        return attrs


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
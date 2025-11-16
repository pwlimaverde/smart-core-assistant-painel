from datetime import datetime
from typing import Any, Optional

from django.db import models


class EvolutionInstance(models.Model):
    id: models.AutoField = models.AutoField(primary_key=True)
    name: models.CharField[str] = models.CharField(max_length=100)
    instance_id: models.CharField[str | None] = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    api_key: models.CharField[str] = models.CharField(max_length=100)
    server_url: models.URLField[str | None] = models.URLField(
        max_length=200, blank=True, null=True
    )
    phone_number: models.CharField[str | None] = models.CharField(
        max_length=20, blank=True, null=True
    )
    active: models.BooleanField[bool] = models.BooleanField(default=True)
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "evolution_sync_instance"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # type: ignore[override]
        return self.name


class EvolutionContact(models.Model):
    id: models.AutoField = models.AutoField(primary_key=True)
    contact: models.ForeignKey["clientes.Contato"] = models.ForeignKey(
        "clientes.Contato",
        on_delete=models.SET_NULL,
        related_name="evolution_links",
        blank=True,
        null=True,
    )
    instance: models.ForeignKey[EvolutionInstance] = models.ForeignKey(
        EvolutionInstance,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    jid: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True
    )
    lid: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True
    )
    addressing_mode: models.CharField[str | None] = models.CharField(
        max_length=8, blank=True, null=True
    )
    active: models.BooleanField[bool] = models.BooleanField(default=True)
    metadados: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict, blank=True
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "evolution_sync_contact"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["jid"]),
            models.Index(fields=["lid"]),
            models.Index(fields=["contact"]),
            models.Index(fields=["instance"]),
        ]

    def __str__(self) -> str:  # type: ignore[override]
        ident = self.jid or self.lid or "unknown"
        return f"{self.instance.name} - {ident}"
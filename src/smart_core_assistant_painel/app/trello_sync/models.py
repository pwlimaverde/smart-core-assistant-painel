from datetime import datetime
from typing import Any, override

from django.db import models


class TrelloBoard(models.Model):
    """[TRL-FLW-001] Board Trello vinculado a um FluxoAtendimento.

    Geração Automática de Quadros.

    Comentário: Shadow model para mapear um fluxo/board e IDs externos.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    fluxo: models.OneToOneField["ui.operacional.FluxoAtendimento"] = (
        models.OneToOneField(
            "operacional.FluxoAtendimento",
            on_delete=models.CASCADE,
            related_name="trello_board",
        )
    )
    external_id: models.CharField[str] = models.CharField(
        max_length=64, unique=True
    )
    name: models.CharField[str] = models.CharField(max_length=200)
    url: models.URLField[str | None] = models.URLField(blank=True, null=True)
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True
    )
    metadata: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict, blank=True
    )

    class Meta:
        db_table = "trello_board_sync"
        indexes = [models.Index(fields=["external_id"])]

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.external_id})"


class TrelloList(models.Model):
    """[TRL-LST-001] List Trello vinculada a uma EtapaFluxo.

    Geração Automática de Listas.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    etapa: models.OneToOneField["ui.operacional.EtapaFluxo"] = (
        models.OneToOneField(
            "operacional.EtapaFluxo",
            on_delete=models.CASCADE,
            related_name="trello_list",
        )
    )
    board: models.ForeignKey[TrelloBoard] = models.ForeignKey(
        TrelloBoard,
        on_delete=models.CASCADE,
        related_name="lists",
    )
    external_id: models.CharField[str] = models.CharField(
        max_length=64, unique=True
    )
    name: models.CharField[str] = models.CharField(max_length=200)
    position: models.FloatField[float] = models.FloatField(default=0.0)
    metadata: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict, blank=True
    )

    class Meta:
        db_table = "trello_list_sync"
        indexes = [models.Index(fields=["external_id", "board"])]

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.external_id})"


class TrelloMember(models.Model):
    """[TRL-MEM-001] Member Trello vinculado a um Atendente.

    Sincronização de Membros.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    atendente: models.OneToOneField["ui.operacional.Atendente"] = (
        models.OneToOneField(
            "operacional.Atendente",
            on_delete=models.CASCADE,
            related_name="trello_member",
        )
    )
    external_id: models.CharField[str | None] = models.CharField(
        max_length=64, unique=True, blank=True, null=True
    )
    username: models.CharField[str] = models.CharField(
        max_length=100, blank=True
    )
    full_name: models.CharField[str] = models.CharField(max_length=200)
    email: models.EmailField[str | None] = models.EmailField(
        blank=True, null=True
    )
    metadata: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict, blank=True
    )
    is_invited: models.BooleanField[bool] = models.BooleanField(default=False)
    invite_sent_at: models.DateTimeField[datetime | None] = (
        models.DateTimeField(blank=True, null=True)
    )

    class Meta:
        db_table = "trello_member_sync"
        indexes = [models.Index(fields=["external_id"])]

    @override
    def __str__(self) -> str:
        return f"{self.username} ({self.external_id})"


class TrelloCard(models.Model):
    """[TRL-CRD-001] Card Trello vinculado a um Atendimento.

    Criação Automática de Cartões.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    atendimento: models.OneToOneField["ui.atendimentos.Atendimento"] = (
        models.OneToOneField(
            "atendimentos.Atendimento",
            on_delete=models.CASCADE,
            related_name="trello_card",
        )
    )
    list_sync: models.ForeignKey[TrelloList] = models.ForeignKey(
        TrelloList,
        on_delete=models.CASCADE,
        related_name="cards",
    )
    external_id: models.CharField[str] = models.CharField(
        max_length=64, unique=True
    )
    name: models.CharField[str] = models.CharField(max_length=200)
    url: models.URLField[str | None] = models.URLField(blank=True, null=True)
    metadata: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict, blank=True
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "trello_card_sync"
        indexes = [models.Index(fields=["external_id", "list_sync"])]

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.external_id})"


class TrelloWebhookEvent(models.Model):
    """[TRL-MOV-001] Registro persistente de eventos recebidos de webhooks do Trello.

    Sincronização Bidirecional de Movimentação.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    action_id: models.CharField[str] = models.CharField(max_length=64)
    model_type: models.CharField[str] = models.CharField(max_length=32)
    payload: models.JSONField[dict[str, Any]] = models.JSONField(default=dict)
    received_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "trello_webhook_event"
        indexes = [models.Index(fields=["action_id", "model_type"])]

    @override
    def __str__(self) -> str:
        return f"Webhook {self.model_type}:{self.action_id}"

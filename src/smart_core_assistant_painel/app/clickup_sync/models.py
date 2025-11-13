from typing import Any

from django.db import models


class ClickupSpace(models.Model):
    """Mapeia um Space do ClickUp para um Departamento local."""

    departamento_id = models.BigIntegerField()
    external_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = "ClickUp Space"
        verbose_name_plural = "ClickUp Spaces"


class ClickupFolder(models.Model):
    """Mapeia um Folder do ClickUp para um Departamento local.

    Relaciona o Folder (agrupador) dentro de um Space com o
    Departamento correspondente. Mantemos `external_id` único
    para evitar duplicidades.
    """

    departamento_id = models.BigIntegerField()
    external_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    space_external_id = models.CharField(max_length=128)

    class Meta:
        verbose_name = "ClickUp Folder"
        verbose_name_plural = "ClickUp Folders"


class ClickupList(models.Model):
    """Mapeia uma List do ClickUp para um FluxoAtendimento local."""

    fluxo_atendimento_id = models.BigIntegerField()
    external_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    space_external_id = models.CharField(max_length=128)

    class Meta:
        verbose_name = "ClickUp List"
        verbose_name_plural = "ClickUp Lists"


class ClickupMember(models.Model):
    """Mapeia um membro do ClickUp para um Atendente local."""

    atendente_id = models.BigIntegerField()
    external_id = models.CharField(max_length=128, unique=True)
    username = models.CharField(max_length=128)

    class Meta:
        verbose_name = "ClickUp Member"
        verbose_name_plural = "ClickUp Members"


class ClickupTask(models.Model):
    """Mapeia uma Task do ClickUp para um Atendimento local."""

    atendimento_id = models.BigIntegerField(unique=True)
    external_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=256)
    list_external_id = models.CharField(max_length=128)

    class Meta:
        verbose_name = "ClickUp Task"
        verbose_name_plural = "ClickUp Tasks"


class ClickupWebhookEvent(models.Model):
    """Persiste eventos recebidos via webhook do ClickUp."""

    event_type = models.CharField(max_length=64)
    resource_id = models.CharField(max_length=128)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ClickUp Webhook Event"
        verbose_name_plural = "ClickUp Webhook Events"


class ClickupStatus(models.Model):
    """Mapeia o Status da List para uma Etapa do Fluxo.

    Este modelo relaciona uma `EtapaFluxo` do sistema ao status
    correspondente em uma `List` do ClickUp. O ClickUp atualiza
    o status de uma Task usando o nome do status, por isso
    persistimos `status_name` para garantir a atualização correta.

    Attributes:
        etapa_fluxo_id: ID da etapa no banco local.
        list_external_id: ID externo da List no ClickUp.
        status_name: Nome do status na List do ClickUp.
        status_type: Tipo do status ("open" ou "closed").
        color: Cor hex do status (ex.: "#6B7280").
        order_index: Índice de ordenação do status na List.
        created_at: Data de criação do registro.
        updated_at: Data da última atualização do registro.
    """

    etapa_fluxo_id = models.BigIntegerField()
    list_external_id = models.CharField(max_length=128)
    status_name = models.CharField(max_length=128)
    status_type = models.CharField(max_length=16)
    color = models.CharField(max_length=16)
    order_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ClickUp Status"
        verbose_name_plural = "ClickUp Statuses"
        constraints = [
            models.UniqueConstraint(
                fields=["etapa_fluxo_id", "list_external_id"],
                name="uniq_etapa_list_status",
            )
        ]

    def __str__(self) -> str:  # type: ignore[override]
        """Representação legível do status mapeado."""
        return f"{self.status_name} ({self.list_external_id})"
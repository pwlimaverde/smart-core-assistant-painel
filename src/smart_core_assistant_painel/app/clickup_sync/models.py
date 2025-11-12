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
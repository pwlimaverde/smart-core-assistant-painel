"""Modelo para gerenciar departamentos e configurações da Evolution API.

Este módulo define o modelo Departamento, que centraliza as configurações
de API, o relacionamento com atendentes e a validação de webhooks.
"""

import re
from datetime import datetime
from typing import Any, Optional, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.indexes import Index
from loguru import logger


def validate_api_key(value: str) -> None:
    """Valida o formato da chave de API da Evolution API.

    Args:
        value (str): A chave de API a ser validada.

    Raises:
        ValidationError: Se o formato for inválido.
    """
    if not value:
        raise ValidationError("A chave de API não pode estar vazia.")
    if len(value) < 8:
        raise ValidationError(
            "A chave de API deve ter pelo menos 8 caracteres."
        )


def validate_telefone_instancia(value: str) -> None:
    """Valida o formato do telefone da instância da Evolution API.

    Args:
        value (str): O telefone da instância.

    Raises:
        ValidationError: Se o formato for inválido.
    """
    if not value:
        raise ValidationError("O telefone da instância é obrigatório.")
    telefone_limpo:str = re.sub(r"\D", "", value)
    if len(telefone_limpo) < 10:
        raise ValidationError("Telefone da instância inválido.")
    if len(telefone_limpo) > 15:
        raise ValidationError("O telefone não pode ter mais de 15 dígitos.")


class Departamento(models.Model):
    """Modelo para departamentos com configurações da Evolution API."""

    id: models.AutoField = models.AutoField(primary_key=True)
    nome: models.CharField[str] = models.CharField(max_length=100, unique=True)
    descricao: models.TextField[str | None] = models.TextField(
        blank=True, null=True
    )
    telefone_instancia: models.CharField[str] = models.CharField(
        max_length=20, unique=True, validators=[validate_telefone_instancia]
    )
    api_key: models.CharField[str] = models.CharField(
        max_length=100, unique=True, validators=[validate_api_key]
    )
    instance_id: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True
    )
    url_evolution_api: models.URLField[str] = models.URLField(
        default="http://www.evolution-api:8080"
    )
    ativo: models.BooleanField[bool] = models.BooleanField(default=True)
    configuracoes: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict, blank=True
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )
    ultima_validacao: models.DateTimeField[datetime | None] = (
        models.DateTimeField(blank=True, null=True)
    )
    metadados: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict, blank=True
    )

    class Meta:
        verbose_name:str = "Departamento"
        verbose_name_plural:str = "Departamentos"
        ordering:list[str] = ["nome"]
        indexes:list[Index] = [
            models.Index(fields=["api_key"]),
            models.Index(fields=["telefone_instancia"]),
            models.Index(fields=["ativo", "nome"]),
        ]

    @override
    def __str__(self) -> str:
        """Retorna a representação em string do departamento."""
        return f"{self.nome} ({self.telefone_instancia})"

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Salva o departamento, normalizando o telefone da instância."""
        if self.telefone_instancia:
            self.telefone_instancia = re.sub(
                r"\D", "", self.telefone_instancia
            )
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        """Valida os campos antes de salvar."""
        super().clean()
        if self.api_key:
            validate_api_key(self.api_key)

    @classmethod
    def validar_api_key(cls, data: dict[str, Any]) -> Optional["Departamento"]:
        """Valida a chave de API e a instância a partir dos dados do webhook.

        Args:
            data (dict): O dicionário com os dados do webhook.

        Returns:
            Optional[Departamento]: O departamento correspondente ou None.
        """
        api_key = data.get("apikey")
        instance = data.get("instance")
        if not api_key or not instance:
            logger.warning(
                "Chave de API ou instância não fornecida no webhook."
            )
            return None
        try:
            return cls.objects.get(
                api_key=api_key, telefone_instancia=instance, ativo=True
            )
        except cls.DoesNotExist:
            logger.warning(
                f"Tentativa de acesso com chave de API inválida para a instância {instance}."
            )
            return None

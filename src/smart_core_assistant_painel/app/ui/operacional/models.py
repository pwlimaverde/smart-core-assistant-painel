import re
from datetime import datetime
from typing import Any, Optional, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.indexes import Index
from loguru import logger


def validate_telefone(value: str) -> None:
    """
    Valida se o número de telefone está no formato correto.
    """
    telefone_limpo: str = re.sub(r"\D", "", value)
    if len(telefone_limpo) < 10 or len(telefone_limpo) > 15:
        raise ValidationError("Número de telefone deve ter entre 10 e 15 dígitos.")
    if not telefone_limpo.isdigit():
        raise ValidationError("Número de telefone deve conter apenas números.")

def validate_api_key(value: str) -> None:
    """Valida o formato da chave de API da Evolution API."""
    if not value:
        raise ValidationError("A chave de API não pode estar vazia.")
    if len(value) < 8:
        raise ValidationError("A chave de API deve ter pelo menos 8 caracteres.")

def validate_telefone_instancia(value: str) -> None:
    """Valida o formato do telefone da instância da Evolution API."""
    if not value:
        raise ValidationError("O telefone da instância é obrigatório.")
    telefone_limpo: str = re.sub(r"\D", "", value)
    if len(telefone_limpo) < 10:
        raise ValidationError("Telefone da instância inválido.")
    if len(telefone_limpo) > 15:
        raise ValidationError("O telefone não pode ter mais de 15 dígitos.")

class Departamento(models.Model):
    """Modelo para departamentos com configurações da Evolution API."""

    id: models.AutoField = models.AutoField(primary_key=True)
    nome: models.CharField[str] = models.CharField(max_length=100, unique=True)
    descricao: models.TextField[str | None] = models.TextField(blank=True, null=True)
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
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(auto_now_add=True)
    ultima_validacao: models.DateTimeField[datetime | None] = models.DateTimeField(
        blank=True, null=True
    )
    metadados: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict, blank=True
    )

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["nome"]
        db_table = "oraculo_departamento"
        indexes: list[Index] = [
            models.Index(fields=["api_key"]),
            models.Index(fields=["telefone_instancia"]),
            models.Index(fields=["ativo", "nome"]),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.nome} ({self.telefone_instancia})"

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.telefone_instancia:
            self.telefone_instancia = re.sub(r"\D", "", self.telefone_instancia)
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        super().clean()
        if self.api_key:
            validate_api_key(self.api_key)

    @classmethod
    def validar_api_key(cls, data: dict[str, Any]) -> Optional["Departamento"]:
        api_key = data.get("apikey")
        instance = data.get("instance")
        if not api_key or not instance:
            logger.warning("Chave de API ou instância não fornecida no webhook.")
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

class AtendenteHumano(models.Model):
    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    telefone: models.CharField[str | None] = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_telefone],
        null=True,
        blank=True,
        help_text="Número de telefone do atendente (usado como sessão única)",
    )
    nome: models.CharField[str] = models.CharField(
        max_length=100, help_text="Nome completo do atendente"
    )
    cargo: models.CharField[str] = models.CharField(
        max_length=100, help_text="Cargo/função do atendente"
    )
    departamento: models.ForeignKey[Optional["Departamento"]] = models.ForeignKey(
        "Departamento",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="atendentes",
        help_text="Departamento ao qual o atendente pertence",
    )
    email: models.EmailField[str | None] = models.EmailField(
        blank=True, null=True, help_text="E-mail corporativo do atendente"
    )
    usuario_sistema: models.CharField[str | None] = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Usuário do sistema para login (se aplicável)",
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True, help_text="Status de atividade do atendente"
    )
    disponivel: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Disponibilidade atual para receber novos atendimentos",
    )
    max_atendimentos_simultaneos: models.PositiveIntegerField[int] = (
        models.PositiveIntegerField(
            default=5,
            help_text="Máximo de atendimentos simultâneos permitidos",
        )
    )
    especialidades: models.JSONField[list[str] | None] = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de especialidades/áreas de conhecimento do atendente",
    )
    horario_trabalho: models.JSONField[dict[str, Any] | None] = (
        models.JSONField(
            default=dict,
            blank=True,
            help_text="Horário de trabalho (ex: {'segunda': '08:00-18:00', 'terca': '08:00-18:00'})",
        )
    )
    data_cadastro: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de cadastro no sistema"
    )
    ultima_atividade: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True, help_text="Data da última atividade no sistema"
    )
    metadados: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais do atendente (configurações, preferências, etc.)",
    )

    class Meta:
        verbose_name = "Atendente Humano"
        verbose_name_plural = "Atendentes Humanos"
        ordering = ["nome"]
        db_table = "oraculo_atendentehumano"

    @override
    def __str__(self) -> str:
        return f"{self.nome} - {self.cargo}"

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.telefone:
            telefone_limpo = re.sub(r"\D", "", self.telefone)
            if not telefone_limpo.startswith("55"):
                telefone_limpo = "55" + telefone_limpo
            self.telefone = "+" + telefone_limpo
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        super().clean()
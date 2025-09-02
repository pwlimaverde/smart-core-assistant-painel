"""Modelo para gerenciar departamentos e configurações da Evolution API.

Este módulo define o modelo Departamento, que centraliza as configurações
de API, o relacionamento com atendentes e a validação de webhooks.
"""

import re
from typing import Any, Optional, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
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
        raise ValidationError("A chave de API deve ter pelo menos 8 caracteres.")


def validate_telefone_instancia(value: str) -> None:
    """Valida o formato do telefone da instância da Evolution API.

    Args:
        value (str): O telefone da instância.

    Raises:
        ValidationError: Se o formato for inválido.
    """
    if not value:
        raise ValidationError("O telefone da instância é obrigatório.")
    telefone_limpo = re.sub(r"\D", "", value)
    if len(telefone_limpo) < 10:
        raise ValidationError("Telefone da instância inválido.")
    if len(telefone_limpo) > 15:
        raise ValidationError("O telefone não pode ter mais de 15 dígitos.")


class Departamento(models.Model):
    """Modelo para departamentos com configurações da Evolution API."""

    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    telefone_instancia = models.CharField(
        max_length=20, unique=True, validators=[validate_telefone_instancia]
    )
    api_key = models.CharField(
        max_length=100, unique=True, validators=[validate_api_key]
    )
    instance_id = models.CharField(max_length=100, blank=True, null=True)
    url_evolution_api = models.URLField(default="http://www.evolution-api:8080")
    ativo = models.BooleanField(default=True)
    configuracoes = models.JSONField(default=dict, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_validacao = models.DateTimeField(blank=True, null=True)
    metadados = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["nome"]
        indexes = [
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
            self.telefone_instancia = re.sub(r"\D", "", self.telefone_instancia)
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        """Valida os campos antes de salvar."""
        super().clean()
        if self.api_key:
            validate_api_key(self.api_key)

    def get_atendentes_ativos(self) -> QuerySet[Any]:
        """Retorna os atendentes ativos deste departamento.

        Returns:
            QuerySet: Um queryset de atendentes ativos.
        """
        return self.atendentes.filter(ativo=True)

    def get_atendentes_disponiveis(self) -> QuerySet[Any]:
        """Retorna os atendentes disponíveis para novos atendimentos.

        Returns:
            QuerySet: Um queryset de atendentes disponíveis.
        """
        return self.atendentes.filter(ativo=True, disponivel=True)

    def atualizar_configuracao(self, chave: str, valor: Any) -> None:
        """Atualiza uma configuração específica.

        Args:
            chave (str): A chave da configuração.
            valor: O novo valor da configuração.
        """
        if not self.configuracoes:
            self.configuracoes = {}
        self.configuracoes[chave] = valor
        self.save(update_fields=["configuracoes"])

    def get_configuracao(self, chave: str, padrao: Any = None) -> Any:
        """Obtém uma configuração específica.

        Args:
            chave (str): A chave da configuração.
            padrao: O valor padrão a ser retornado se a chave não for encontrada.

        Returns:
            O valor da configuração ou o valor padrão.
        """
        return self.configuracoes.get(chave, padrao) if self.configuracoes else padrao

    @classmethod
    def buscar_por_api_key(cls, api_key: str) -> Optional["Departamento"]:
        """Busca um departamento pela chave de API.

        Args:
            api_key (str): A chave de API a ser buscada.

        Returns:
            Optional[Departamento]: O departamento encontrado ou None.
        """
        try:
            return cls.objects.get(api_key=api_key, ativo=True)
        except cls.DoesNotExist:
            logger.warning("Departamento não encontrado para a chave de API.")
            return None

    @classmethod
    def buscar_por_telefone_instancia(cls, telefone: str) -> Optional["Departamento"]:
        """Busca um departamento pelo telefone da instância.

        Args:
            telefone (str): O telefone da instância.

        Returns:
            Optional[Departamento]: O departamento encontrado ou None.
        """
        telefone_limpo = re.sub(r"\D", "", telefone)
        try:
            return cls.objects.get(telefone_instancia=telefone_limpo, ativo=True)
        except cls.DoesNotExist:
            logger.warning(
                f"Departamento não encontrado para o telefone: {telefone_limpo}"
            )
            return None

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

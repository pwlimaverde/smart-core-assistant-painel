"""
Modelo para gerenciar departamentos e configurações da Evolution API.

Este módulo define o modelo Departamento que centraliza:
- Configurações de API key por instância da Evolution API
- Relacionamento com atendentes humanos
- Validação de webhooks
- Configurações específicas por departamento
"""

import re
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import models
from loguru import logger


def validate_api_key(value: str) -> None:
    """
    Valida formato da API key da Evolution API.

    Args:
        value (str): API key a ser validada

    Raises:
        ValidationError: Se o formato for inválido
    """
    if not value:
        raise ValidationError("API key não pode estar vazia")

    # Padrão típico: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    pattern = r"^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$"
    if not re.match(pattern, value, re.IGNORECASE):
        logger.warning(f"API key com formato suspeito: {value[:8]}...")
        # Permite outros formatos mas registra warning

    if len(value) < 8:
        raise ValidationError("API key deve ter pelo menos 8 caracteres")


def validate_telefone_instancia(value: str) -> None:
    """
    Valida formato do telefone de instância da Evolution API.

    Args:
        value (str): Telefone da instância

    Raises:
        ValidationError: Se o formato for inválido
    """
    if not value:
        raise ValidationError("Telefone da instância é obrigatório")

    # Remove caracteres não numéricos
    telefone_limpo = re.sub(r"\D", "", value)

    # Deve ter pelo menos 10 dígitos (código de área + número)
    if len(telefone_limpo) < 10:
        raise ValidationError("Telefone da instância inválido")

    # Máximo 15 dígitos (padrão internacional)
    if len(telefone_limpo) > 15:
        raise ValidationError("Telefone não pode ter mais que 15 dígitos")


class Departamento(models.Model):
    """
    Modelo para departamentos com configurações da Evolution API.

    Centraliza configurações de instâncias da Evolution API, incluindo
    API keys, telefones de instância e relacionamento com atendentes.

    Attributes:
        id: Chave primária
        nome: Nome do departamento
        descricao: Descrição detalhada
        telefone_instancia: Número do WhatsApp da instância
        api_key: Chave de API da Evolution API
        instance_id: ID da instância (UUID da Evolution API)
        url_evolution_api: URL base da Evolution API
        ativo: Status de atividade
        configuracoes: Configurações específicas (JSON)
        data_criacao: Data de criação
        ultima_validacao: Última validação da API key
        metadados: Informações adicionais
    """

    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do departamento"
    )

    nome: models.CharField = models.CharField(
        max_length=100, unique=True, help_text="Nome único do departamento"
    )

    descricao: models.TextField = models.TextField(
        blank=True, null=True, help_text="Descrição detalhada do departamento"
    )

    telefone_instancia: models.CharField = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_telefone_instancia],
        help_text="Número do WhatsApp da instância (ex: 5588921729550)",
    )

    api_key: models.CharField = models.CharField(
        max_length=100,
        unique=True,
        validators=[validate_api_key],
        help_text="API key da Evolution API para esta instância",
    )

    instance_id: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="UUID da instância na Evolution API",
    )

    url_evolution_api: models.URLField = models.URLField(
        default="http://www.evolution-api:8080", help_text="URL base da Evolution API"
    )

    ativo: models.BooleanField = models.BooleanField(
        default=True, help_text="Departamento ativo para receber mensagens"
    )

    configuracoes: models.JSONField = models.JSONField(
        default=dict, blank=True, help_text="Configurações específicas do departamento"
    )

    data_criacao: models.DateTimeField = models.DateTimeField(
        auto_now_add=True, help_text="Data de criação do departamento"
    )

    ultima_validacao: models.DateTimeField = models.DateTimeField(
        blank=True, null=True, help_text="Última validação bem-sucedida da API key"
    )

    metadados: models.JSONField = models.JSONField(
        default=dict, blank=True, help_text="Metadados adicionais do departamento"
    )

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["api_key"]),
            models.Index(fields=["telefone_instancia"]),
            models.Index(fields=["ativo", "nome"]),
        ]

    def __str__(self) -> str:
        """Representação string do departamento."""
        return f"{self.nome} ({self.telefone_instancia})"

    def save(self, *args, **kwargs):
        """
        Salva o departamento normalizando o telefone da instância.
        """
        # Normaliza telefone da instância
        if self.telefone_instancia:
            telefone_limpo = re.sub(r"\D", "", self.telefone_instancia)
            if not telefone_limpo.startswith("55"):
                telefone_limpo = "55" + telefone_limpo
            self.telefone_instancia = telefone_limpo

        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Valida campos antes do save"""
        super().clean()
        if self.api_key:
            try:
                validate_api_key(self.api_key)
            except ValidationError as e:
                raise ValidationError({"api_key": e.messages})

    def get_atendentes_ativos(self):
        """
        Retorna atendentes ativos deste departamento.

        Returns:
            QuerySet: Atendentes humanos ativos
        """
        return self.atendentes.filter(ativo=True)

    def get_atendentes_disponiveis(self):
        """
        Retorna atendentes disponíveis para novos atendimentos.

        Returns:
            QuerySet: Atendentes disponíveis
        """
        return self.atendentes.filter(ativo=True, disponivel=True)

    def atualizar_configuracao(self, chave: str, valor) -> None:
        """
        Atualiza uma configuração específica.

        Args:
            chave (str): Chave da configuração
            valor: Valor da configuração
        """
        if not self.configuracoes:
            self.configuracoes = {}

        self.configuracoes[chave] = valor
        self.save(update_fields=["configuracoes"])

    def get_configuracao(self, chave: str, padrao=None):
        """
        Obtém uma configuração específica.

        Args:
            chave (str): Chave da configuração
            padrao: Valor padrão se não encontrado

        Returns:
            Valor da configuração ou padrão
        """
        if not self.configuracoes:
            return padrao

        return self.configuracoes.get(chave, padrao)

    @classmethod
    def buscar_por_api_key(cls, api_key: str) -> Optional["Departamento"]:
        """
        Busca departamento pela API key.

        Args:
            api_key (str): API key a ser buscada

        Returns:
            Departamento encontrado ou None
        """
        try:
            return cls.objects.get(api_key=api_key, ativo=True)
        except cls.DoesNotExist:
            logger.warning(
                f"Departamento não encontrado para API key: {api_key[:8]}..."
            )
            return None

    @classmethod
    def buscar_por_telefone_instancia(cls, telefone: str) -> Optional["Departamento"]:
        """
        Busca departamento pelo telefone da instância.

        Args:
            telefone (str): Telefone da instância

        Returns:
            Departamento encontrado ou None
        """
        # Normaliza telefone para busca
        telefone_limpo = re.sub(r"\D", "", telefone)
        if not telefone_limpo.startswith("55"):
            telefone_limpo = "55" + telefone_limpo

        try:
            return cls.objects.get(telefone_instancia=telefone_limpo, ativo=True)
        except cls.DoesNotExist:
            logger.warning(
                f"Departamento não encontrado para telefone: {telefone_limpo}"
            )
            return None

    @classmethod
    def validar_api_key(cls, data: dict) -> Optional["Departamento"]:
        """
        Valida a API key e a instância a partir dos dados do webhook.

        Args:
            data (dict): Dicionário com os dados do webhook.

        Returns:
            Departamento: O departamento correspondente se a validação for bem-sucedida,
                         None caso contrário.
        """
        api_key = data.get("apikey")
        instance = data.get("instance")

        if not api_key or not instance:
            logger.warning("API key ou instância não fornecida no webhook.")
            return None

        try:
            # A 'instance' do webhook corresponde ao 'telefone_instancia'
            departamento = cls.objects.get(
                api_key=api_key, telefone_instancia=instance, ativo=True
            )
            return departamento
        except cls.DoesNotExist:
            logger.warning(
                f"Tentativa de acesso com API key inválida ou inativa para a instância {instance}."
            )
            return None

import re
from datetime import datetime
from typing import Any, Optional, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.indexes import Index
from django.contrib.auth.models import User
from loguru import logger


def validate_telefone(value: str) -> None:
    """
    Valida se o número de telefone está no formato correto.
    """
    telefone_limpo: str = re.sub(r"\D", "", value)
    if len(telefone_limpo) < 10 or len(telefone_limpo) > 15:
        raise ValidationError(
            "Número de telefone deve ter entre 10 e 15 dígitos."
        )
    if not telefone_limpo.isdigit():
        raise ValidationError("Número de telefone deve conter apenas números.")


def validate_api_key(value: str) -> None:
    """Valida o formato da chave de API da Evolution API."""
    if not value:
        raise ValidationError("A chave de API não pode estar vazia.")
    if len(value) < 8:
        raise ValidationError(
            "A chave de API deve ter pelo menos 8 caracteres."
        )


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
    """Modelo para departamentos da organização."""

    id: models.AutoField = models.AutoField(primary_key=True)
    nome: models.CharField[str] = models.CharField(max_length=100, unique=True)
    slug: models.SlugField[str | None] = models.SlugField(max_length=120, unique=True, blank=True, null=True)
    descricao: models.TextField[str | None] = models.TextField(
        blank=True, null=True
    )
    ativo: models.BooleanField[bool] = models.BooleanField(default=True)
    configuracoes: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict, blank=True
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
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
            models.Index(fields=["slug"]),
            models.Index(fields=["ativo", "nome"]),
        ]

    @override
    def __str__(self) -> str:
        return self.nome

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        super().clean()



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
    departamento: models.ForeignKey[Optional["Departamento"]] = (
        models.ForeignKey(
            "Departamento",
            on_delete=models.SET_NULL,
            blank=True,
            null=True,
            related_name="atendentes",
            help_text="Departamento ao qual o atendente pertence",
        )
    )
    email: models.EmailField[str | None] = models.EmailField(
        blank=True, null=True, help_text="E-mail corporativo do atendente"
    )
    usuario: models.OneToOneField[User | None] = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="atendente_humano",
        help_text="Usuário do Django associado ao atendente (opcional)",
    )
    usuario_sistema: models.CharField[str | None] = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Usuário do sistema para login (se aplicável)",
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True, help_text="Indica se o atendente está ativo"
    )
    disponivel: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Se o atendente está aceitando novos atendimentos",
    )
    max_atendimentos_simultaneos: models.PositiveIntegerField[int] = (
        models.PositiveIntegerField(
            default=5,
            help_text="Capacidade máxima de atendimentos simultâneos",
        )
    )
    # Campo para registro da última atribuição, usado para ordenação (round-robin / fairness)
    data_ultima_atribuicao: models.DateTimeField[datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e hora da última atribuição de um novo atendimento",
    )
    horario_trabalho: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Horários de trabalho do atendente",
    )
    especialidades: models.JSONField[list[str]] = models.JSONField(
        default=list, blank=True, help_text="Especialidades do atendente"
    )
    metadados: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais do atendente (configurações, preferências, etc.)",
    )
    data_cadastro: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de cadastro no sistema"
    )
    ultima_atividade: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True, help_text="Data da última atividade no sistema"
    )

    class Meta:
        verbose_name = "Atendente Humano"
        verbose_name_plural = "Atendentes Humanos"
        ordering = ["nome"]
        db_table = "oraculo_atendentehumano"
        indexes = [
            models.Index(fields=["departamento", "disponivel"]),
            models.Index(fields=["disponivel", "max_atendimentos_simultaneos"]),
            models.Index(fields=["data_ultima_atribuicao"]),
        ]

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

    def get_atendimentos_ativos(self) -> int:
        """Retorna a quantidade de atendimentos ativos deste atendente.

        "Atendimentos ativos" são considerados aqueles cujo status ainda não
        é finalizador (ou seja, não "resolvido" nem "cancelado"). Para evitar
        import circular, a enum de status é importada localmente.
        """
        # Import local para evitar import circular com app de atendimentos.
        from smart_core_assistant_painel.app.ui.atendimentos.models import (
            StatusAtendimento,
        )

        ativos = [
            StatusAtendimento.FILA,
            StatusAtendimento.EM_ATENDIMENTO,
            StatusAtendimento.AGUARDANDO_RETORNO,
        ]
        return self.atendimentos.filter(status__in=ativos).count()

    def is_available(self) -> bool:
        """Verifica se o atendente está disponível considerando capacidade atual."""
        if not self.ativo or not self.disponivel:
            return False
        return self.get_atendimentos_ativos() < self.max_atendimentos_simultaneos

    def current_load(self) -> int:
        """Retorna a carga atual de atendimentos ativos do atendente."""
        return self.get_atendimentos_ativos()


class WhatsAppInstance(models.Model):
    """Modelo para instâncias WhatsApp centralizando credenciais.

    - Substitui o uso direto de credenciais em Departamento.
    - Permite múltiplas instâncias por departamento.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    departamento: models.ForeignKey[Departamento | None] = models.ForeignKey(
        "Departamento",
        on_delete=models.CASCADE,
        related_name="whatsapp_instances",
        null=True,
        blank=True,
        help_text="Departamento associado a esta instância",
    )
    phone_number: models.CharField[str | None] = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_telefone_instancia],
        help_text="Telefone vinculado à instância",
        blank=True,
        null=True,
    )
    instance_id: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="ID único da instância no provedor",
    )
    api_key: models.CharField[str] = models.CharField(
        max_length=100,
        unique=True,
        validators=[validate_api_key],
        help_text="Chave de API para autenticação",
    )
    provider: models.CharField[str] = models.CharField(
        max_length=30,
        choices=[("evolution", "Evolution"), ("other", "Other")],
        default="evolution",
        help_text="Provedor da API de WhatsApp",
    )
    owner: models.OneToOneField[Optional["AtendenteHumano"]] = models.OneToOneField(
        "AtendenteHumano",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="whatsapp_instance",
        help_text="Atendente dono desta instância (opcional)",
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Se a instância está ativa",
    )
    metadados: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais da instância",
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do registro",
    )
    ultima_validacao: models.DateTimeField[datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data da última validação de credenciais",
    )

    class Meta:
        verbose_name = "Instância WhatsApp"
        verbose_name_plural = "Instâncias WhatsApp"
        ordering = ["-data_criacao"]
        db_table = "oraculo_whatsapp_instance"
        indexes = [
            models.Index(fields=["api_key"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["instance_id"]),
            models.Index(fields=["provider"]),
        ]

    @override
    def __str__(self) -> str:
        ident = self.instance_id or self.phone_number
        dep = self.departamento.nome if self.departamento else "sem-departamento"
        return f"{dep} - {ident}"

    @override
    def clean(self) -> None:
        super().clean()
        if self.api_key:
            validate_api_key(self.api_key)
        if self.phone_number:
            validate_telefone_instancia(self.phone_number)
        if self.owner and self.owner.departamento and self.departamento:
            if self.owner.departamento_id != self.departamento_id:
                raise ValidationError(
                    "Atendente dono deve pertencer ao mesmo departamento da instância."
                )

    @property
    def atendentes(self):
        """Retorna QuerySet de atendentes do departamento desta instância.

        Caso a instância não esteja vinculada a um departamento, retorna um QuerySet vazio.
        """
        from .models import AtendenteHumano  # import local para evitar ciclos
        if not self.departamento:
            return AtendenteHumano.objects.none()
        return self.departamento.atendentes.all()

    @classmethod
    def validar_api_key(cls, data: dict[str, Any]) -> Optional["WhatsAppInstance"]:
        """Valida credenciais do webhook e retorna a instância correspondente.

        Preferência:
        - Se `instance_id` estiver presente, valida primeiro por ele.
        - Senão, tenta por `phone_number` a partir de `instance`.
        """
        api_key = data.get("apikey")
        instance_id = data.get("instance_id")
        instancia_ou_telefone = data.get("instance")
        if not api_key:
            logger.warning("Chave de API não fornecida no webhook.")
            return None
        # Tenta por instance_id primeiro
        if instance_id:
            try:
                return cls.objects.get(
                    api_key=api_key, instance_id=instance_id, ativo=True
                )
            except cls.DoesNotExist:
                logger.info(
                    "Credenciais por instance_id não encontradas; tentando por phone_number."
                )
        # Fallback: tenta por phone_number
        if not instancia_ou_telefone:
            logger.warning("Instância/telefone não fornecido no webhook.")
            return None
        try:
            return cls.objects.get(
                api_key=api_key, phone_number=instancia_ou_telefone, ativo=True
            )
        except cls.DoesNotExist:
            logger.warning(
                f"Acesso inválido: API key/instância não encontrada ({instancia_ou_telefone})."
            )
            return None

    def selecionar_proximo_atendente(self) -> Optional["AtendenteHumano"]:
        """Seleciona o próximo atendente disponível por round-robin simples.

        Critérios:
        - Atendentes ativos e disponíveis no departamento.
        - Ordenação crescente por `data_ultima_atribuicao` (nulos primeiro), depois por `id`.
        - Escolhe o primeiro que ainda não atingiu sua capacidade máxima.
        """
        # Se não houver departamento vinculado, não há atendentes para selecionar
        if not self.departamento:
            return None

        elegiveis = self.atendentes.filter(
            ativo=True,
            disponivel=True,
        ).order_by("data_ultima_atribuicao", "id")

        for atendente in elegiveis:
            # Usa helper do modelo para contar atendimentos ativos
            if atendente.get_atendimentos_ativos() < atendente.max_atendimentos_simultaneos:
                return atendente
        return None

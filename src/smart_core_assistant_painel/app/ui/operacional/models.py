import re
from datetime import datetime
from typing import Any, Optional, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.indexes import Index
from django.contrib.auth.models import User
from django.utils import timezone
from loguru import logger


def validate_telefone(value: str) -> None:
    """
    Valida se o numero de telefone esta no formato correto.
    """
    telefone_limpo: str = re.sub(r"\D", "", value)
    if len(telefone_limpo) < 10 or len(telefone_limpo) > 15:
        raise ValidationError(
            "Numero de telefone deve ter entre 10 e 15 digitos."
        )
    if not telefone_limpo.isdigit():
        raise ValidationError("Numero de telefone deve conter apenas numeros.")


def validate_api_key(value: str) -> None:
    """Valida o formato da chave de API da Evolution API."""
    if not value:
        raise ValidationError("A chave de API nao pode estar vazia.")
    if len(value) < 8:
        raise ValidationError(
            "A chave de API deve ter pelo menos 8 caracteres."
        )


def validate_telefone_instancia(value: str) -> None:
    """Valida o formato do telefone da instancia da Evolution API."""
    if not value:
        raise ValidationError("O telefone da instancia e obrigatorio.")
    telefone_limpo: str = re.sub(r"\D", "", value)
    if len(telefone_limpo) < 10:
        raise ValidationError("Telefone da instancia invalido.")
    if len(telefone_limpo) > 15:
        raise ValidationError("O telefone nao pode ter mais de 15 digitos.")


class Departamento(models.Model):
    """Modelo para departamentos da organizacao."""

    id: models.AutoField = models.AutoField(primary_key=True)
    nome: models.CharField[str] = models.CharField(max_length=100, unique=True)
    slug: models.SlugField[str | None] = models.SlugField(
        max_length=120, unique=True, blank=True, null=True
    )
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


class Atendente(models.Model):
    """Modelo para atendentes humanos da organizacao."""

    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primaria do registro"
    )
    slug: models.SlugField[str | None] = models.SlugField(
        max_length=250, unique=True, blank=True, null=True, default=""
    )
    telefone: models.CharField[str | None] = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_telefone],
        null=True,
        blank=True,
        help_text="Numero de telefone do atendente (usado como sessao unica)",
    )
    nome: models.CharField[str] = models.CharField(
        max_length=100, help_text="Nome completo do atendente"
    )
    cargo: models.CharField[str] = models.CharField(
        max_length=100, help_text="Cargo/funcao do atendente"
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
        help_text="Usuario do Django associado ao atendente (opcional)",
    )
    usuario_sistema: models.CharField[str | None] = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Usuario do sistema para login (se aplicavel)",
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True, help_text="Indica se o atendente esta ativo"
    )
    disponivel: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Se o atendente esta aceitando novos atendimentos",
    )
    max_atendimentos_simultaneos: models.PositiveIntegerField[int] = (
        models.PositiveIntegerField(
            default=5,
            help_text="Capacidade maxima de atendimentos simultaneos",
        )
    )
    # Campo para registro da ultima atribuicao, usado para ordenacao (round-robin / fairness)
    data_ultima_atribuicao: models.DateTimeField[datetime | None] = (
        models.DateTimeField(
            blank=True,
            null=True,
            help_text="Data e hora da ultima atribuicao de um novo atendimento",
        )
    )
    horario_trabalho: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Horarios de trabalho do atendente",
    )
    especialidades: models.JSONField[list[str]] = models.JSONField(
        default=list, blank=True, help_text="Especialidades do atendente"
    )
    metadados: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informacoes adicionais do atendente (configuracoes, preferencias, etc.)",
    )
    data_cadastro: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de cadastro no sistema"
    )
    ultima_atividade: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True, help_text="Data da ultima atividade no sistema"
    )

    class Meta:
        verbose_name = "Atendente"
        verbose_name_plural = "Atendentes"
        ordering = ["nome"]
        db_table = "oraculo_atendente"
        indexes = [
            models.Index(fields=["departamento", "disponivel"]),
            models.Index(
                fields=["disponivel", "max_atendimentos_simultaneos"]
            ),
            models.Index(fields=["data_ultima_atribuicao"]),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.nome} - {self.cargo}"

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        from django.utils.text import slugify

        # Gera slug automaticamente se nao existir
        if not self.slug:
            base_slug = slugify(self.nome)
            suffix = 1
            slug = base_slug

            # Garante unicidade do slug
            while Atendente.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            self.slug = slug

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

        "Atendimentos ativos" sao considerados aqueles cujo status ainda nao
        e finalizador (ou seja, nao "resolvido" nem "cancelado"). Para evitar
        import circular, a enum de status e importada localmente.
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
        """Verifica se o atendente esta disponivel considerando capacidade atual."""
        if not self.ativo or not self.disponivel:
            return False
        return (
            self.get_atendimentos_ativos() < self.max_atendimentos_simultaneos
        )

    def current_load(self) -> int:
        """Retorna a carga atual de atendimentos ativos do atendente."""
        return self.get_atendimentos_ativos()


class WhatsAppInstance(models.Model):
    """Modelo para instancias WhatsApp centralizando credenciais.

    - Substitui o uso direto de credenciais em Departamento.
    - Permite multiplas instancias por departamento.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    departamento: models.ForeignKey[Departamento | None] = models.ForeignKey(
        "Departamento",
        on_delete=models.CASCADE,
        related_name="whatsapp_instances",
        null=True,
        blank=True,
        help_text="Departamento associado a esta instancia",
    )
    phone_number: models.CharField[str | None] = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_telefone_instancia],
        help_text="Telefone vinculado a instancia",
        blank=True,
        null=True,
    )
    instance_id: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="ID unico da instancia no provedor",
    )
    api_key: models.CharField[str] = models.CharField(
        max_length=100,
        unique=True,
        validators=[validate_api_key],
        help_text="Chave de API para autenticacao",
    )
    provider: models.CharField[str] = models.CharField(
        max_length=30,
        choices=[("evolution", "Evolution"), ("other", "Other")],
        default="evolution",
        help_text="Provedor da API de WhatsApp",
    )
    owner: models.OneToOneField[Optional["Atendente"]] = models.OneToOneField(
        "Atendente",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="whatsapp_instance",
        help_text="Atendente dono desta instancia (opcional)",
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Se a instancia esta ativa",
    )
    metadados: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais da instancia",
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criacao do registro",
    )
    ultima_validacao: models.DateTimeField[datetime | None] = (
        models.DateTimeField(
            blank=True,
            null=True,
            help_text="Data da ultima validacao de credenciais",
        )
    )

    class Meta:
        verbose_name = "Instancia WhatsApp"
        verbose_name_plural = "Instancias WhatsApp"
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
        dep = (
            self.departamento.nome if self.departamento else "sem-departamento"
        )
        return f"{dep} - {ident}"

    @override
    def clean(self) -> None:
        super().clean()
        if self.api_key:
            validate_api_key(self.api_key)
        if self.phone_number:
            validate_telefone_instancia(self.phone_number)

        # Validacao de exclusividade: OU departamento OU owner, nunca ambos ou nenhum
        if self.departamento and self.owner:
            raise ValidationError(
                "Uma instancia deve estar vinculada a UM departamento OU UM atendente, nunca ambos."
            )
        if not self.departamento and not self.owner:
            raise ValidationError(
                "Uma instancia deve estar vinculada a pelo menos UM departamento ou UM atendente."
            )

        # Validacao de consistencia se ambos estiverem preenchidos (caso a regra mude no futuro)
        if self.owner and self.owner.departamento and self.departamento:
            if self.owner.departamento_id != self.departamento_id:
                raise ValidationError(
                    "Atendente dono deve pertencer ao mesmo departamento da instancia."
                )

    @property
    def atendentes(self) -> models.QuerySet["Atendente"]:
        """Retorna QuerySet de atendentes do departamento desta instancia.

        Caso a instancia nao esteja vinculada a um departamento, retorna um QuerySet vazio.
        """
        # Import local para evitar ciclos
        from .models import Atendente

        if not self.departamento:
            return Atendente.objects.none()
        return self.departamento.atendentes.all()

    @property
    def tipo_instancia(self) -> str:
        """Retorna o tipo da instancia para logica de negocio."""
        if self.departamento:
            return "departamental"
        elif self.owner:
            return "individual"
        return "desconhecido"

    @property
    def responsavel_principal(self):
        """Retorna o responsavel principal para roteamento."""
        if self.owner:
            return self.owner
        elif self.departamento:
            return self.departamento
        return None

    def rotear_atendimento(
        self, mensagem: dict[str, Any]
    ) -> Optional["Atendente"]:
        """Roteia mensagem baseada no tipo de instancia.

        Args:
            mensagem: Dicionario com dados da mensagem recebida

        Returns:
            Atendente ou None se nao houver atendente disponivel
        """
        if self.tipo_instancia == "individual":
            # Instancia individual: atribui diretamente ao owner
            if self.owner and self.owner.is_available():
                return self.owner
            return None

        elif self.tipo_instancia == "departamental":
            # Instancia departamental: usa logica de distribuicao existente
            return self.selecionar_proximo_atendente()

        return None

    @classmethod
    def validar_api_key(
        cls, data: dict[str, Any]
    ) -> Optional["WhatsAppInstance"]:
        """Valida credenciais do webhook e retorna a instancia correspondente.

        Preferencia:
        - Se `instance_id` estiver presente, valida primeiro por ele.
        - Senao, tenta por `phone_number` a partir de `instance`.
        """
        api_key = data.get("apikey")
        instance_id = data.get("instance_id")
        instancia_ou_telefone = data.get("instance")
        if not api_key:
            logger.warning("Chave de API nao fornecida no webhook.")
            return None
        # Tenta por instance_id primeiro
        if instance_id:
            try:
                return cls.objects.get(
                    api_key=api_key, instance_id=instance_id, ativo=True
                )
            except cls.DoesNotExist:
                logger.info(
                    "Credenciais por instance_id nao encontradas; tentando por phone_number."
                )
        # Fallback: tenta por phone_number
        if not instancia_ou_telefone:
            logger.warning("Instancia/telefone nao fornecido no webhook.")
            return None
        try:
            return cls.objects.get(
                api_key=api_key, phone_number=instancia_ou_telefone, ativo=True
            )
        except cls.DoesNotExist:
            logger.warning(
                f"Acesso invalido: API key/instancia nao encontrada ({instancia_ou_telefone})."
            )
            return None

    def selecionar_proximo_atendente(self) -> Optional["Atendente"]:
        """Seleciona o proximo atendente disponivel por round-robin simples.

        Criterios:
        - Atendentes ativos e disponiveis no departamento.
        - Ordenacao crescente por `data_ultima_atribuicao` (nulos primeiro), depois por `id`.
        - Escolhe o primeiro que ainda nao atingiu sua capacidade maxima.
        """
        # Se nao houver departamento vinculado, nao ha atendentes para selecionar
        if not self.departamento:
            return None

        elegiveis = self.atendentes.filter(
            ativo=True,
            disponivel=True,
        ).order_by("data_ultima_atribuicao", "id")

        for atendente in elegiveis:
            # Usa helper do modelo para contar atendimentos ativos
            if (
                atendente.get_atendimentos_ativos()
                < atendente.max_atendimentos_simultaneos
            ):
                return atendente
        return None


class TipoEtapa(models.TextChoices):
    """Tipos de etapas possiveis em um fluxo de atendimento."""

    FILA = "fila", "Fila de Entrada"
    TRABALHO = "trabalho", "Em Trabalho"
    ESPERA = "espera", "Aguardando Resposta"
    FINALIZACAO = "finalizacao", "Finalizacao"


class FluxoAtendimento(models.Model):
    """
    Define o fluxo de trabalho personalizado para um departamento.
    Cada departamento pode ter seu proprio fluxo com etapas especificas.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    departamento: models.OneToOneField["Departamento"] = models.OneToOneField(
        Departamento,
        on_delete=models.CASCADE,
        related_name="fluxo_atendimento",
        help_text="Departamento ao qual este fluxo pertence"
    )
    nome: models.CharField[str] = models.CharField(
        max_length=100,
        help_text="Nome descritivo do fluxo"
    )
    descricao: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Descricao detalhada do fluxo de trabalho"
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Indica se o fluxo esta ativo"
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criacao do fluxo"
    )
    data_atualizacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data da ultima atualizacao do fluxo"
    )

    class Meta:
        verbose_name = "Fluxo de Atendimento"
        verbose_name_plural = "Fluxos de Atendimento"
        db_table = "oraculo_fluxo_atendimento"
        ordering = ["departamento__nome"]

    @override
    def __str__(self) -> str:
        return f"{self.nome} - {self.departamento.nome}"

    def get_etapa_inicial(self) -> Optional["EtapaFluxo"]:
        """
        Retorna a etapa inicial do fluxo (primeira na ordem).

        Returns:
            EtapaFluxo inicial ou None se nao houver etapas
        """
        return self.etapas.filter(tipo_etapa=TipoEtapa.FILA).first()

    def get_etapas_por_tipo(self, tipo: str) -> models.QuerySet["EtapaFluxo"]:
        """
        Retorna as etapas do fluxo filtradas por tipo.

        Args:
            tipo: Tipo da etapa (FILA, TRABALHO, ESPERA, FINALIZACAO)

        Returns:
            QuerySet com as etapas do tipo especificado
        """
        return self.etapas.filter(tipo_etapa=tipo).order_by("ordem")


class EtapaFluxo(models.Model):
    """
    Representa uma etapa/coluna no fluxo kanban de um departamento.
    Cada etapa define um status possivel para um atendimento.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    fluxo: models.ForeignKey[FluxoAtendimento] = models.ForeignKey(
        FluxoAtendimento,
        on_delete=models.CASCADE,
        related_name="etapas",
        help_text="Fluxo ao qual esta etapa pertence"
    )
    nome: models.CharField[str] = models.CharField(
        max_length=50,
        help_text="Nome da etapa (ex: 'Solicitacao de Orcamento')"
    )
    descricao: models.CharField[str | None] = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Descricao opcional da etapa"
    )
    ordem: models.PositiveIntegerField = models.PositiveIntegerField(
        help_text="Ordem da etapa no fluxo (menor numero primeiro)"
    )
    cor: models.CharField[str] = models.CharField(
        max_length=7,
        default="#6B7280",
        help_text="Cor hexadecimal para identificacao visual (ex: #FF5733)"
    )
    tipo_etapa: models.CharField[str] = models.CharField(
        max_length=20,
        choices=TipoEtapa.choices,
        default=TipoEtapa.TRABALHO,
        help_text="Tipo da etapa para regras de negocio"
    )
    permite_atribuicao: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Indica se atendentes podem ser atribuidos nesta etapa"
    )
    automatico: models.BooleanField[bool] = models.BooleanField(
        default=False,
        help_text="Indica se o movimento para esta etapa e automatico"
    )
    regras_transicao: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Regras especificas para transicao para esta etapa"
    )
    campos_obrigatorios: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de campos obrigatorios para entrar nesta etapa"
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Indica se a etapa esta ativa no fluxo"
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criacao da etapa"
    )

    class Meta:
        verbose_name = "Etapa do Fluxo"
        verbose_name_plural = "Etapas do Fluxo"
        db_table = "oraculo_etapa_fluxo"
        unique_together = [["fluxo", "ordem"]]
        ordering = ["fluxo", "ordem"]
        indexes = [
            models.Index(fields=["fluxo", "ordem"]),
            models.Index(fields=["tipo_etapa"]),
            models.Index(fields=["ativo"]),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.nome} - {self.fluxo.departamento.nome}"

    @override
    def clean(self) -> None:
        """Validacoes especificas do modelo."""
        super().clean()

        # Validar formato da cor
        if self.cor and not self.cor.startswith("#"):
            self.cor = f"#{self.cor}"

        # Garantir que a cor tenha 7 caracteres (#RRGGBB)
        if self.cor and len(self.cor) == 4:
            # Converter formato #RGB para #RRGGBB
            self.cor = f"#{self.cor[1]}{self.cor[1]}{self.cor[2]}{self.cor[2]}{self.cor[3]}{self.cor[3]}"


class MovimentoFluxo(models.Model):
    """
    Registra a movimentacao de um atendimento entre as etapas do fluxo.
    Mantem historico completo para auditoria e analise.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    atendimento: models.ForeignKey["atendimentos.Atendimento"] = models.ForeignKey(
        "atendimentos.Atendimento",
        on_delete=models.CASCADE,
        related_name="movimentos_fluxo",
        help_text="Atendimento que foi movido"
    )
    etapa_origem: models.ForeignKey[EtapaFluxo] = models.ForeignKey(
        EtapaFluxo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_saida",
        help_text="Etapa de origem (None para novos atendimentos)"
    )
    etapa_destino: models.ForeignKey[EtapaFluxo] = models.ForeignKey(
        EtapaFluxo,
        on_delete=models.CASCADE,
        related_name="movimentos_entrada",
        help_text="Etapa para a qual o atendimento foi movido"
    )
    atendente_origem: models.ForeignKey[Atendente] = models.ForeignKey(
        Atendente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_origem",
        help_text="Atendente que realizou o movimento (se aplicavel)"
    )
    atendente_destino: models.ForeignKey[Atendente] = models.ForeignKey(
        Atendente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_destino",
        help_text="Atendente que foi atribuido ao atendimento (se aplicavel)"
    )
    motivo: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo da movimentacao (opcional)"
    )
    dados_complementares: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dados complementares sobre a movimentacao"
    )
    automatico: models.BooleanField[bool] = models.BooleanField(
        default=False,
        help_text="Indica se o movimento foi automatico"
    )
    data_movimento: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora da movimentacao"
    )
    duracao_segundos: models.PositiveIntegerField[int | None] = (
        models.PositiveIntegerField(
            blank=True,
            null=True,
            help_text="Duracao em segundos da etapa anterior (para calculos de SLA)"
        )
    )

    class Meta:
        verbose_name = "Movimento do Fluxo"
        verbose_name_plural = "Movimentos do Fluxo"
        db_table = "oraculo_movimento_fluxo"
        ordering = ["-data_movimento"]
        indexes = [
            models.Index(fields=["atendimento", "-data_movimento"]),
            models.Index(fields=["etapa_destino", "-data_movimento"]),
            models.Index(fields=["data_movimento"]),
        ]

    @override
    def __str__(self) -> str:
        origem = self.etapa_origem.nome if self.etapa_origem else "Novo"
        destino = self.etapa_destino.nome if self.etapa_destino else "Desconhecido"
        return f"{self.atendimento.id}: {origem} → {destino}"

    @classmethod
    def criar_movimento(
        cls,
        atendimento: "atendimentos.Atendimento",
        etapa_destino: EtapaFluxo,
        atendente_destino: Optional[Atendente] = None,
        motivo: Optional[str] = None,
        automatico: bool = False,
        atendente_origem: Optional[Atendente] = None,
        etapa_origem: Optional[EtapaFluxo] = None,
    ) -> "MovimentoFluxo":
        """
        Cria um novo movimento de fluxo de forma centralizada.

        Args:
            atendimento: Atendimento sendo movido
            etapa_destino: Nova etapa do atendimento
            atendente_destino: Atendente que sera atribuido (opcional)
            motivo: Motivo da movimentacao (opcional)
            automatico: Se o movimento e automatico
            atendente_origem: Atendente que realizou o movimento (opcional)
            etapa_origem: Etapa anterior do atendimento (opcional)

        Returns:
            MovimentoFluxo criado
        """
        # Se nao informada etapa de origem, buscar a atual do atendimento
        duracao_segundos = None
        if not etapa_origem:
            ultimo_movimento = atendimento.movimentos_fluxo.first()
            if ultimo_movimento:
                etapa_origem = ultimo_movimento.etapa_destino
                # Calcular duracao desde o ultimo movimento
                agora = timezone.now()
                if ultimo_movimento.data_movimento:
                    duracao_segundos = int((agora - ultimo_movimento.data_movimento).total_seconds())

        # Criar o movimento
        movimento = cls.objects.create(
            atendimento=atendimento,
            etapa_origem=etapa_origem,
            etapa_destino=etapa_destino,
            atendente_origem=atendente_origem,
            atendente_destino=atendente_destino,
            motivo=motivo,
            automatico=automatico,
            duracao_segundos=duracao_segundos,
        )

        # Atualizar a etapa atual do atendimento
        atendimento.etapa_atual = etapa_destino

        # Atualizar atendente se informado
        if atendente_destino:
            atendimento.atendente_humano = atendente_destino
            atendente_destino.data_ultima_atribuicao = timezone.now()
            atendente_destino.save(update_fields=["data_ultima_atribuicao"])

        atendimento.save(update_fields=["etapa_atual", "atendente_humano"])

        return movimento

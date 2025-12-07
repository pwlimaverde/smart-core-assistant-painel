import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, override

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.indexes import Index
from django.db.models.signals import post_save  # noqa: F401
from django.utils import timezone
from loguru import logger

if TYPE_CHECKING:
    # Import apenas para tipagem, evitando dependencias em tempo de execucao
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Atendimento as AtendimentoModel,
    )


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
    """[OPS-ORG-001] Modelo para departamentos da organizacao.

    Gestão de Departamentos (com isolamento de dados).
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    nome: models.CharField[str] = models.CharField(max_length=100, unique=True)
    slug: models.SlugField[str | None] = models.SlugField(
        max_length=120, unique=True, blank=True, null=True
    )
    descricao: models.TextField[str | None] = models.TextField(
        blank=True, null=True
    )
    ativo: models.BooleanField[bool] = models.BooleanField(default=True)
    telefone_instancia: models.CharField[str | None] = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_telefone_instancia],
        help_text="Telefone (instancia Evolution API) deste departamento",
    )
    api_key: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[validate_api_key],
        help_text="Chave de API (Evolution API) deste departamento",
    )
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
        if self.telefone_instancia:
            return f"{self.nome} ({self.telefone_instancia})"
        return self.nome

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        from django.utils.text import slugify

        if not self.slug:
            self.slug = slugify(self.nome)
        # Normaliza telefone da instancia removendo caracteres nao numericos
        # Comentario: nos testes, nao adicionamos DDI automaticamente, apenas
        # limpamos o formato quando necessario.
        if self.telefone_instancia:
            tel_limpo: str = re.sub(r"\D", "", self.telefone_instancia)
            self.telefone_instancia = tel_limpo
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        super().clean()
        # Valida campos se informados
        if self.api_key:
            validate_api_key(self.api_key)
        if self.telefone_instancia:
            validate_telefone_instancia(self.telefone_instancia)

    @classmethod
    def validar_api_key(cls, data: dict[str, Any]) -> Optional["Departamento"]:
        """Valida credenciais recebidas pelo webhook e retorna o departamento.

        Espera chaves: `apikey` (string) e `instance` (telefone).
        Retorna o departamento ativo que corresponde.
        """
        apikey: Optional[str] = data.get("apikey")
        instancia: Optional[str] = data.get("instance")
        if not apikey:
            logger.warning("Chave de API nao fornecida no webhook.")
            return None
        if not instancia:
            logger.warning("Instancia/telefone nao fornecido no webhook.")
            return None
        try:
            return cls.objects.get(
                api_key=apikey, telefone_instancia=instancia, ativo=True
            )
        except cls.DoesNotExist:
            logger.warning(
                "Acesso invalido: API key/instancia nao encontrada (%s).",
                instancia,
            )
            return None

    def get_fluxo(self) -> Optional["FluxoAtendimento"]:
        """
        Retorna o fluxo de atendimento padrao do departamento.

        Regra atual: primeiro fluxo ativo por ordem de criacao.

        Returns:
            FluxoAtendimento ou None se nao existir vinculo.
        """
        # Busca o primeiro fluxo ativo do departamento, por ordem de criacao
        return self.fluxos.filter(ativo=True).order_by("data_criacao").first()

    def get_fluxo_etapas(self) -> models.QuerySet["EtapaFluxo"]:
        """
        Retorna as etapas do fluxo do departamento, se houver.

        Returns:
            QuerySet de EtapaFluxo ordenado por ordem. Vazio se sem fluxo.
        """
        fluxo: Optional["FluxoAtendimento"] = self.get_fluxo()
        if not fluxo:
            return EtapaFluxo.objects.none()
        return fluxo.etapas.order_by("ordem")

    def ensure_fluxo(self, nome: Optional[str] = None) -> "FluxoAtendimento":
        """
        Garante que o departamento possua um fluxo associado.

        - Se existir, apenas retorna o fluxo atual.
        - Caso contrario, cria um novo fluxo com nome padrao.

        Args:
            nome: Nome opcional para o novo fluxo.

        Returns:
            FluxoAtendimento criado ou existente.
        """
        fluxo_existente: Optional["FluxoAtendimento"] = self.get_fluxo()
        if fluxo_existente:
            return fluxo_existente

        fluxo_novo: "FluxoAtendimento" = FluxoAtendimento.objects.create(
            departamento=self,
            nome=nome or f"Fluxo {self.nome}",
            descricao=(
                "Fluxo criado automaticamente pelo helper ensure_fluxo."
            ),
            ativo=True,
        )
        return fluxo_novo


class Atendente(models.Model):
    """[OPS-ORG-002] Modelo para atendentes humanos da organizacao.

    Gestão de Atendentes (Horários, Limites).
    """

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
        max_length=100,
        blank=False,
        null=False,
        default="",
        help_text="Cargo/funcao do atendente",
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
    # Fluxo (quadro) obrigatório para convite e controle de acesso no Trello
    fluxo: models.ForeignKey["FluxoAtendimento"] = models.ForeignKey(
        "FluxoAtendimento",
        on_delete=models.PROTECT,
        related_name="atendentes",
        blank=False,
        null=True,
        help_text=(
            "Fluxo de atendimento (quadro) ao qual o atendente sera convidado"
        ),
    )
    email: models.EmailField[str | None] = models.EmailField(
        blank=False, null=True, help_text="E-mail corporativo do atendente"
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
            models.Index(fields=["fluxo"]),
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

        # Comentario: validacao de negocio ocorre em ModelForms (via clean())
        # e em chamadas explicitas a full_clean() pelos consumidores.
        # Evitamos chamar full_clean() aqui para nao bloquear criacoes
        # diretas em testes que nao informam certos campos (ex.: cargo).

        if self.telefone:
            telefone_limpo = re.sub(r"\D", "", self.telefone)
            if not telefone_limpo.startswith("55"):
                telefone_limpo = "55" + telefone_limpo
            self.telefone = "+" + telefone_limpo
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        super().clean()
        # Comentario: email e fluxo tornaram-se obrigatorios para garantir
        # o convite correto ao Trello.
        if not self.email:
            raise ValidationError(
                {"email": "E-mail e obrigatorio para cadastro de atendente."}
            )
        # Comentário: usar fluxo_id para evitar acesso ao descriptor quando vazio
        # Comentario: ao criar um novo atendente, o fluxo e obrigatorio.
        # Em edicao (self.pk existe), manteremos o fluxo atual caso
        # nao seja reenviado pelo formulario.
        if self.fluxo_id is None and not self.pk:
            raise ValidationError(
                {"fluxo": "Fluxo de atendimento obrigatorio."}
            )

        # Coerencia: se houver departamento, deve coincidir com o do fluxo
        if self.departamento_id is not None and self.fluxo_id is not None:
            if self.fluxo.departamento_id != self.departamento_id:
                raise ValidationError(
                    {
                        "fluxo": "Fluxo deve pertencer ao mesmo departamento informado.",
                        "departamento": "Departamento deve coincidir com o do fluxo.",
                    }
                )

        # Formato de telefone já validado por validator, normalização ocorre em save()

    # Compatibilidade retroativa com testes/nomes antigos
    # Comentario: exporta alias para manter referencias existentes em testes.
    # Em tempo de import, AtendenteHumano apontara para Atendente.

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
            StatusAtendimento.PENDENCIA,
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


class AppInstance(models.Model):
    """[OPS-ORG-003] Modelo para instâncias de comunicação (ex: Evolution API).

    Configuração das instâncias de conexão com canais de mensagem.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    api_key: models.CharField[str] = models.CharField(
        max_length=128, unique=True
    )
    channel: models.CharField[str] = models.CharField(max_length=32)
    display_name: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True
    )
    departamento: models.ForeignKey[Departamento | None] = models.ForeignKey(
        "Departamento",
        on_delete=models.SET_NULL,
        related_name="app_instances",
        blank=True,
        null=True,
    )
    owner: models.OneToOneField[Optional["Atendente"]] = models.OneToOneField(
        "Atendente",
        on_delete=models.SET_NULL,
        related_name="app_instance",
        blank=True,
        null=True,
    )
    active: models.BooleanField[bool] = models.BooleanField(default=True)
    resposta_bot: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Se True, o bot pode responder automaticamente mensagens desta instância",
    )
    metadata: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict, blank=True
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "oraculo_app_instance"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["api_key"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["departamento"]),
        ]

    def __str__(self) -> str:  # type: ignore[override]
        name = self.display_name or self.api_key
        return f"{self.channel} - {name}"


class TipoEtapa(models.TextChoices):
    """Tipos de etapas possiveis em um fluxo de atendimento."""

    FILA = "fila", "Fila de Entrada"
    TRABALHO = "trabalho", "Em Trabalho"
    ESPERA = "espera", "Aguardando Resposta"
    FINALIZACAO = "finalizacao", "Finalizacao"


class FluxoAtendimento(models.Model):
    """
    Define fluxos de trabalho personalizados por departamento.
    Um departamento pode possuir multiplos fluxos; cada fluxo pertence
    a um unico departamento.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    departamento: models.ForeignKey["Departamento"] = models.ForeignKey(
        Departamento,
        on_delete=models.CASCADE,
        related_name="fluxos",
        help_text="Departamento ao qual este fluxo pertence",
    )
    nome: models.CharField[str] = models.CharField(
        max_length=100, help_text="Nome descritivo do fluxo"
    )
    descricao: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Descricao detalhada do fluxo de trabalho",
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True, help_text="Indica se o fluxo esta ativo"
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de criacao do fluxo"
    )
    data_atualizacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True, help_text="Data da ultima atualizacao do fluxo"
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
        help_text="Fluxo ao qual esta etapa pertence",
    )
    nome: models.CharField[str] = models.CharField(
        max_length=50,
        help_text="Nome da etapa (ex: 'Solicitacao de Orcamento')",
    )
    descricao: models.CharField[str | None] = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Descricao opcional da etapa",
    )
    ordem: models.IntegerField = models.IntegerField(
        help_text="Ordem da etapa no fluxo (menor numero primeiro)"
    )
    cor: models.CharField[str] = models.CharField(
        max_length=7,
        default="#6B7280",
        help_text="Cor hexadecimal para identificacao visual (ex: #FF5733)",
    )
    tipo_etapa: models.CharField[str] = models.CharField(
        max_length=20,
        choices=TipoEtapa.choices,
        default=TipoEtapa.TRABALHO,
        help_text="Tipo da etapa para regras de negocio",
    )
    permite_atribuicao: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Indica se atendentes podem ser atribuidos nesta etapa",
    )
    automatico: models.BooleanField[bool] = models.BooleanField(
        default=False,
        help_text="Indica se o movimento para esta etapa e automatico",
    )
    regras_transicao: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Regras especificas para transicao para esta etapa",
    )
    campos_obrigatorios: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de campos obrigatorios para entrar nesta etapa",
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True, help_text="Indica se a etapa esta ativa no fluxo"
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de criacao da etapa"
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
    atendimento: models.ForeignKey["Atendimento"] = models.ForeignKey(
        "atendimentos.Atendimento",
        on_delete=models.CASCADE,
        related_name="movimentos_fluxo",
        help_text="Atendimento que foi movido",
    )
    etapa_origem: models.ForeignKey[EtapaFluxo] = models.ForeignKey(
        EtapaFluxo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_saida",
        help_text="Etapa de origem (None para novos atendimentos)",
    )
    etapa_destino: models.ForeignKey[EtapaFluxo] = models.ForeignKey(
        EtapaFluxo,
        on_delete=models.CASCADE,
        related_name="movimentos_entrada",
        help_text="Etapa para a qual o atendimento foi movido",
    )
    atendente_origem: models.ForeignKey[Atendente] = models.ForeignKey(
        Atendente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_origem",
        help_text="Atendente que realizou o movimento (se aplicavel)",
    )
    atendente_destino: models.ForeignKey[Atendente] = models.ForeignKey(
        Atendente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_destino",
        help_text="Atendente que foi atribuido ao atendimento (se aplicavel)",
    )
    motivo: models.TextField[str | None] = models.TextField(
        blank=True, null=True, help_text="Motivo da movimentacao (opcional)"
    )
    dados_complementares: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dados complementares sobre a movimentacao",
    )
    automatico: models.BooleanField[bool] = models.BooleanField(
        default=False, help_text="Indica se o movimento foi automatico"
    )
    data_movimento: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data e hora da movimentacao"
    )
    duracao_segundos: models.PositiveIntegerField[int | None] = (
        models.PositiveIntegerField(
            blank=True,
            null=True,
            help_text="Duracao em segundos da etapa anterior (para calculos de SLA)",
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
        destino = (
            self.etapa_destino.nome if self.etapa_destino else "Desconhecido"
        )
        return f"{self.atendimento.id}: {origem} → {destino}"

    @classmethod
    def criar_movimento(
        cls,
        atendimento: "AtendimentoModel",
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
                    duracao_segundos = int(
                        (
                            agora - ultimo_movimento.data_movimento
                        ).total_seconds()
                    )

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


# Alias de compatibilidade com nomenclatura anterior em testes
# Mantem AtendenteHumano apontando para o modelo Atendente
AtendenteHumano = Atendente

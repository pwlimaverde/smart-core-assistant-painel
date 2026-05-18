# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false, reportMissingTypeArgument=false
"""Modelos do app Workspace de Atendimento Unificado.

Princípio de independência (não-negociável conforme plano):

- **ZERO alteração** em tabelas legadas. Toda persistência criada por este
  app vai para tabelas `atu_*` próprias.
- FKs lógicas (BigIntegerField) substituem ForeignKey cross-app para
  evitar acoplamento e permitir migrations isoladas em DB do tenant.

E.1 entregou `LeituraAtendimento` (não-lido por atendente).
E.2 acrescenta `CampoPersonalizado` e `ValorCampoAtendimento`.
"""

from __future__ import annotations

from datetime import datetime
from typing import override

from django.db import models

# ---------------------------------------------------------------------------
# E.1 — Controle de leitura (não-lidos)
# ---------------------------------------------------------------------------


class LeituraAtendimento(models.Model):
    """Marca a última vez que um atendente "leu" um atendimento.

    Permite calcular não-lidos sem alterar `Atendimento`:
    ``Mensagem.filter(atendimento_id=..., remetente=CONTATO,
    timestamp__gt=LeituraAtendimento.ultima_leitura_at).count()``.

    FKs são lógicas (BigIntegerField) e sem constraint cross-app,
    seguindo o mesmo critério adotado pelo `evolution_sync` quando
    referencia entidades do `clientes` no banco de tenant.
    """

    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    atendimento_id: models.BigIntegerField[int] = models.BigIntegerField(
        help_text="ID lógico de atendimentos.Atendimento (sem FK cruzada).",
    )
    atendente_id: models.BigIntegerField[int] = models.BigIntegerField(
        help_text="ID lógico de operacional.Atendente (sem FK cruzada).",
    )
    ultima_leitura_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Momento da última leitura do atendimento pelo atendente.",
    )

    class Meta:
        verbose_name = "Leitura de Atendimento"
        verbose_name_plural = "Leituras de Atendimentos"
        db_table = "atu_leitura_atendimento"
        unique_together = [("atendimento_id", "atendente_id")]
        indexes = [
            models.Index(
                fields=["atendimento_id", "ultima_leitura_at"],
                name="atu_leit_atend_ultima_idx",
            ),
            models.Index(
                fields=["atendente_id", "ultima_leitura_at"],
                name="atu_leit_atend_at_idx",
            ),
        ]

    @override
    def __str__(self) -> str:
        return (
            f"LeituraAtendimento(atendimento={self.atendimento_id}, "
            f"atendente={self.atendente_id}, at={self.ultima_leitura_at})"
        )


# ---------------------------------------------------------------------------
# E.2 — Campos Personalizados
# ---------------------------------------------------------------------------


class EscopoCampo(models.TextChoices):
    GLOBAL = "GLOBAL", "Global (todos os fluxos)"
    FLUXO = "FLUXO", "Por Fluxo"


class TipoCampo(models.TextChoices):
    TEXTO = "texto", "Texto"
    NUMERO = "numero", "Número"
    DATA = "data", "Data"
    ESCOLHA = "escolha", "Escolha única"
    MULTIPLA_ESCOLHA = "multipla_escolha", "Múltipla escolha"
    BOOLEANO = "booleano", "Booleano"


class OrigemValor(models.TextChoices):
    MANUAL = "MANUAL", "Manual (atendente)"
    BOT = "BOT", "Bot (extração IA)"
    IMPORT = "IMPORT", "Importado"


class CampoPersonalizado(models.Model):
    """Define um campo personalizado configurável por tenant.

    Campos GLOBAL se aplicam a todos os fluxos; FLUXO se aplicam apenas
    ao `FluxoAtendimento` referenciado (FK lógica — sem constraint cross-app).

    A coluna `extrair_hint` orienta a IA sobre como reconhecer o campo na
    conversa (exemplo: "CPF ou CNPJ mencionado pelo contato").
    """

    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    slug: models.SlugField = models.SlugField(
        max_length=64,
        help_text="Identificador URL-friendly (ex: 'cnpj_cliente').",
    )
    nome: models.CharField = models.CharField(max_length=120)
    descricao: models.TextField = models.TextField(
        blank=True,
        help_text="Descrição do campo — também usado como hint de extração.",
    )
    escopo: models.CharField = models.CharField(
        max_length=10,
        choices=EscopoCampo.choices,
        default=EscopoCampo.GLOBAL,
    )
    fluxo_id: models.BigIntegerField = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID lógico de operacional.FluxoAtendimento (null se GLOBAL).",
    )
    tipo: models.CharField = models.CharField(
        max_length=20,
        choices=TipoCampo.choices,
        default=TipoCampo.TEXTO,
    )
    opcoes: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text="Opções válidas para tipos escolha/multipla_escolha.",
    )
    obrigatorio: models.BooleanField = models.BooleanField(default=False)
    extrair_automaticamente: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Se True, o bot tenta extrair este campo da conversa.",
    )
    extrair_hint: models.CharField = models.CharField(
        max_length=500,
        blank=True,
        help_text="Dica para a IA sobre como reconhecer este campo.",
    )
    mostrar_no_card: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Exibir valor como badge no card do Kanban.",
    )
    ordem: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        default=0
    )
    ativo: models.BooleanField = models.BooleanField(default=True)
    data_criacao: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )
    data_atualizacao: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Campo Personalizado"
        verbose_name_plural = "Campos Personalizados"
        db_table = "atu_campo_personalizado"
        unique_together = [("slug", "escopo", "fluxo_id")]
        indexes = [
            models.Index(
                fields=["escopo", "fluxo_id", "ativo"],
                name="atu_campo_escopo_fluxo_idx",
            ),
            models.Index(
                fields=["extrair_automaticamente", "ativo"],
                name="atu_campo_extrair_idx",
            ),
        ]
        ordering = ["ordem", "nome"]

    @override
    def __str__(self) -> str:
        return f"CampoPersonalizado({self.slug}, escopo={self.escopo})"


class ValorCampoAtendimento(models.Model):
    """Valor de um `CampoPersonalizado` para um `Atendimento` específico.

    FKs são lógicas (BigIntegerField) para manter isolamento cross-app.
    Quando `origem=BOT`, `confianca` reflete o score retornado pelo LLM.
    A regra de idempotência (nunca sobrescrever MANUAL) é garantida
    pelo service `extract_custom_fields`.
    """

    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    atendimento_id: models.BigIntegerField = models.BigIntegerField(
        help_text="ID lógico de atendimentos.Atendimento (sem FK cruzada).",
    )
    campo: models.ForeignKey = models.ForeignKey(
        CampoPersonalizado,
        on_delete=models.CASCADE,
        related_name="valores",
    )
    valor: models.JSONField = models.JSONField(
        help_text="Valor do campo (string, número, lista, bool, etc.).",
    )
    origem: models.CharField = models.CharField(
        max_length=10,
        choices=OrigemValor.choices,
        default=OrigemValor.MANUAL,
    )
    confianca: models.FloatField = models.FloatField(
        null=True,
        blank=True,
        help_text="Score de confiança da extração (apenas quando origem=BOT).",
    )
    mensagem_origem_id: models.BigIntegerField = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID lógico da Mensagem que originou a extração (BOT).",
    )
    editado_por_id: models.BigIntegerField = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID lógico do Atendente que editou manualmente.",
    )
    data_atualizacao: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Valor de Campo"
        verbose_name_plural = "Valores de Campos"
        db_table = "atu_valor_campo"
        unique_together = [("atendimento_id", "campo")]
        indexes = [
            models.Index(
                fields=["atendimento_id", "campo"],
                name="atu_valor_atend_campo_idx",
            ),
        ]

    @override
    def __str__(self) -> str:
        return (
            f"ValorCampoAtendimento(atendimento={self.atendimento_id}, "
            f"campo={self.campo_id}, origem={self.origem})"
        )


# ---------------------------------------------------------------------------
# E.3 — Etiquetas e Notas
# ---------------------------------------------------------------------------


class Etiqueta(models.Model):
    """Cadastro de etiquetas (tags coloridas) aplicáveis a atendimentos.

    Diferente do campo legado `Atendimento.tags` (JSONField de strings
    soltas, mantido por compatibilidade), `Etiqueta` permite gerenciar um
    catálogo com nome, cor e descrição. Aplicação em atendimentos é feita
    via `EtiquetaAtendimento` (M2M manual com FK lógica).
    """

    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    nome: models.CharField[str] = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nome curto da etiqueta (ex: 'Urgente', 'VIP').",
    )
    cor: models.CharField[str] = models.CharField(
        max_length=7,
        default="#a98f71",
        help_text="Cor hexadecimal usada no chip (ex: '#dc2626').",
    )
    descricao: models.CharField[str] = models.CharField(
        max_length=200,
        blank=True,
        help_text="Descrição exibida no tooltip ao passar o mouse.",
    )
    ativo: models.BooleanField[bool] = models.BooleanField(default=True)
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
        db_table = "atu_etiqueta"
        ordering = ["nome"]

    @override
    def __str__(self) -> str:
        return f"Etiqueta({self.nome})"


class EtiquetaAtendimento(models.Model):
    """Associação M2M manual entre Atendimento e Etiqueta.

    `atendimento_id` é FK lógica (BigIntegerField) seguindo o padrão do app.
    """

    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    atendimento_id: models.BigIntegerField[int] = models.BigIntegerField(
        db_index=True,
        help_text="ID lógico de atendimentos.Atendimento.",
    )
    etiqueta: models.ForeignKey["Etiqueta"] = models.ForeignKey(
        Etiqueta,
        on_delete=models.CASCADE,
        related_name="aplicacoes",
    )
    aplicada_em: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )
    aplicada_por_id: models.BigIntegerField[int | None] = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID lógico de operacional.Atendente que aplicou.",
    )

    class Meta:
        verbose_name = "Etiqueta do Atendimento"
        verbose_name_plural = "Etiquetas dos Atendimentos"
        db_table = "atu_etiqueta_atendimento"
        unique_together = [("atendimento_id", "etiqueta")]
        indexes = [
            models.Index(
                fields=["atendimento_id"],
                name="atu_etiq_atend_idx",
            ),
        ]

    @override
    def __str__(self) -> str:
        return (
            f"EtiquetaAtendimento(atendimento={self.atendimento_id}, "
            f"etiqueta={self.etiqueta_id})"
        )


class Nota(models.Model):
    """Nota interna do atendente vinculada a um atendimento.

    Cada nota pertence a UM atendimento (relação 1:N — atendimento tem
    várias notas). Exibida na sidebar de detalhes após a linha do tempo.
    """

    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    atendimento_id: models.BigIntegerField[int] = models.BigIntegerField(
        db_index=True,
        help_text="ID lógico de atendimentos.Atendimento.",
    )
    texto: models.TextField[str] = models.TextField(
        help_text="Conteúdo livre da nota.",
    )
    criado_por_id: models.BigIntegerField[int | None] = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID lógico de operacional.Atendente que criou a nota.",
    )
    criado_em: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        db_table = "atu_nota"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(
                fields=["atendimento_id", "-criado_em"],
                name="atu_nota_atend_idx",
            ),
        ]

    @override
    def __str__(self) -> str:
        return f"Nota(atendimento={self.atendimento_id}, id={self.pk})"

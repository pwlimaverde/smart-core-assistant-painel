"""Modelos do app Gestão Kanban.

A persistência física das tabelas é mantida pelo `atendimento_unificado` (para
não quebrar o histórico de migrations). Aqui usamos `managed = False` mapeando
para as tabelas reais `atu_*`.
"""

from __future__ import annotations

from datetime import datetime
from typing import override

from django.db import models


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
    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    slug: models.SlugField = models.SlugField(max_length=64)
    nome: models.CharField = models.CharField(max_length=120)
    descricao: models.TextField = models.TextField(blank=True)
    escopo: models.CharField = models.CharField(max_length=10, choices=EscopoCampo.choices, default=EscopoCampo.GLOBAL)
    fluxo_id: models.BigIntegerField = models.BigIntegerField(null=True, blank=True)
    tipo: models.CharField = models.CharField(max_length=20, choices=TipoCampo.choices, default=TipoCampo.TEXTO)
    opcoes: models.JSONField = models.JSONField(default=list, blank=True)
    obrigatorio: models.BooleanField = models.BooleanField(default=False)
    extrair_automaticamente: models.BooleanField = models.BooleanField(default=True)
    extrair_hint: models.CharField = models.CharField(max_length=500, blank=True)
    mostrar_no_card: models.BooleanField = models.BooleanField(default=True)
    ordem: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(default=0)
    ativo: models.BooleanField = models.BooleanField(default=True)
    data_criacao: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    data_atualizacao: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "atu_campo_personalizado"

    @override
    def __str__(self) -> str:
        return f"CampoPersonalizado({self.slug}, escopo={self.escopo})"


class ValorCampoAtendimento(models.Model):
    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    atendimento_id: models.BigIntegerField = models.BigIntegerField()
    campo: models.ForeignKey = models.ForeignKey(CampoPersonalizado, on_delete=models.CASCADE, related_name="valores")
    valor: models.JSONField = models.JSONField()
    origem: models.CharField = models.CharField(max_length=10, choices=OrigemValor.choices, default=OrigemValor.MANUAL)
    confianca: models.FloatField = models.FloatField(null=True, blank=True)
    mensagem_origem_id: models.BigIntegerField = models.BigIntegerField(null=True, blank=True)
    editado_por_id: models.BigIntegerField = models.BigIntegerField(null=True, blank=True)
    data_atualizacao: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "atu_valor_campo"

    @override
    def __str__(self) -> str:
        return f"ValorCampoAtendimento(atendimento={self.atendimento_id}, campo={self.campo_id}, origem={self.origem})"


class Etiqueta(models.Model):
    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    nome: models.CharField[str] = models.CharField(max_length=50)
    cor: models.CharField[str] = models.CharField(max_length=7, default="#a98f71")
    descricao: models.CharField[str] = models.CharField(max_length=200, blank=True)
    ativo: models.BooleanField[bool] = models.BooleanField(default=True)
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "atu_etiqueta"

    @override
    def __str__(self) -> str:
        return f"Etiqueta({self.nome})"


class EtiquetaAtendimento(models.Model):
    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    atendimento_id: models.BigIntegerField[int] = models.BigIntegerField()
    etiqueta: models.ForeignKey["Etiqueta"] = models.ForeignKey(Etiqueta, on_delete=models.CASCADE, related_name="aplicacoes")
    aplicada_em: models.DateTimeField[datetime] = models.DateTimeField(auto_now_add=True)
    aplicada_por_id: models.BigIntegerField[int | None] = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "atu_etiqueta_atendimento"

    @override
    def __str__(self) -> str:
        return f"EtiquetaAtendimento(atendimento={self.atendimento_id}, etiqueta={self.etiqueta_id})"


class Nota(models.Model):
    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    atendimento_id: models.BigIntegerField[int] = models.BigIntegerField()
    texto: models.TextField[str] = models.TextField()
    criado_por_id: models.BigIntegerField[int | None] = models.BigIntegerField(null=True, blank=True)
    criado_em: models.DateTimeField[datetime] = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "atu_nota"

    @override
    def __str__(self) -> str:
        return f"Nota(atendimento={self.atendimento_id}, id={self.pk})"

"""Serializers DRF para o módulo Operacional.

Exposição de dados para departamentos, fluxos e etapas com API pública
do Kanban. Comentários em Português e type hints completos.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import Departamento, FluxoAtendimento, EtapaFluxo


class DepartamentoSerializer(serializers.ModelSerializer[Departamento]):
    """Serializa informações básicas do departamento."""

    class Meta:
        model = Departamento
        fields: list[str] = ["id", "nome", "slug", "descricao", "ativo"]


class EtapaFluxoSerializer(serializers.ModelSerializer[EtapaFluxo]):
    """Serializa cada etapa/coluna do fluxo Kanban."""

    class Meta:
        model = EtapaFluxo
        fields: list[str] = [
            "id",
            "nome",
            "descricao",
            "ordem",
            "cor",
            "tipo_etapa",
            "permite_atribuicao",
            "automatico",
            "ativo",
        ]


class FluxoAtendimentoSerializer(
    serializers.ModelSerializer[FluxoAtendimento]
):
    """Serializa o fluxo com suas etapas."""

    etapas = EtapaFluxoSerializer(many=True, read_only=True)

    class Meta:
        model = FluxoAtendimento
        fields: list[str] = ["id", "nome", "descricao", "ativo", "etapas"]

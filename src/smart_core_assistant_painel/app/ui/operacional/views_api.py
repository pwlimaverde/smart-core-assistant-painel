"""Views de API pública para o módulo Operacional.

Fornece endpoints GET para listar departamentos ativos e obter
o fluxo (etapas) de um departamento específico.
"""

from __future__ import annotations

from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Departamento, FluxoAtendimento
from .serializers import (
    DepartamentoSerializer,
    FluxoAtendimentoSerializer,
)


@api_view(["GET"])  # type: ignore[misc]
@permission_classes([AllowAny])
def departamentos_public(_: Any) -> Response:
    """Lista departamentos ativos (uso público)."""
    qs = Departamento.objects.filter(ativo=True).order_by("nome")
    data = DepartamentoSerializer(qs, many=True).data
    return Response({"departamentos": data})


@api_view(["GET"])  # type: ignore[misc]
@permission_classes([AllowAny])
def fluxo_departamento_public(_: Any, departamento_slug: str) -> Response:
    """Retorna o fluxo e etapas de um departamento pelo slug (público)."""
    departamento = get_object_or_404(
        Departamento, slug=departamento_slug, ativo=True
    )
    fluxo: FluxoAtendimento | None = getattr(
        departamento, "fluxo_atendimento", None
    )
    if not fluxo:
        return Response(
            {
                "departamento": DepartamentoSerializer(departamento).data,
                "fluxo": None,
                "etapas": [],
            }
        )
    fluxo_data = FluxoAtendimentoSerializer(fluxo).data
    return Response(
        {
            "departamento": DepartamentoSerializer(departamento).data,
            "fluxo": fluxo_data,
            "etapas": fluxo_data.get("etapas", []),
        }
    )
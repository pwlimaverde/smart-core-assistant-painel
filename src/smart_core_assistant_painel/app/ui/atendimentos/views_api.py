"""Views de API pública para o módulo Atendimentos.

Endpoints GET: kanban por departamento, detalhe de atendimento,
e lista de mensagens de um atendimento.
"""

from __future__ import annotations

from typing import Any

from django.shortcuts import get_object_or_404
from django.db.models import QuerySet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    EtapaFluxo,
    FluxoAtendimento,
)
from .models import Atendimento, Mensagem
from .serializers import (
    AtendimentoCardSerializer,
    AtendimentoDetailSerializer,
    MensagemSerializer,
)


@api_view(["GET"])  # type: ignore[misc]
@permission_classes([AllowAny])
def kanban_departamento_public(_: Any, departamento_slug: str) -> Response:
    """Retorna dados do Kanban (somente leitura) para um departamento."""
    departamento = get_object_or_404(
        Departamento, slug=departamento_slug, ativo=True
    )
    fluxo: FluxoAtendimento | None = getattr(
        departamento, "fluxo_atendimento", None
    )
    if not fluxo:
        return Response(
            {
                "departamento": {
                    "id": departamento.id,
                    "nome": departamento.nome,
                    "slug": departamento.slug,
                },
                "columns": [],
            }
        )

    etapas_qs: QuerySet[EtapaFluxo] = fluxo.etapas.order_by("ordem")
    columns: list[dict[str, Any]] = []

    for etapa in etapas_qs:
        cards_qs = (
            Atendimento.objects.filter(
                departamento=departamento, etapa_atual=etapa
            )
            .select_related("contato", "atendente_humano", "etapa_atual")
            .order_by("-data_ultima_mensagem", "-data_inicio")
        )
        cards = AtendimentoCardSerializer(cards_qs, many=True).data
        columns.append(
            {
                "id": etapa.id,
                "nome": etapa.nome,
                "cor": etapa.cor,
                "ordem": etapa.ordem,
                "tipo_etapa": etapa.tipo_etapa,
                "cards": cards,
                "count": len(cards),
            }
        )

    return Response(
        {
            "departamento": {
                "id": departamento.id,
                "nome": departamento.nome,
                "slug": departamento.slug,
            },
            "columns": columns,
        }
    )


@api_view(["GET"])  # type: ignore[misc]
@permission_classes([AllowAny])
def atendimento_detalhe_public(_: Any, atendimento_id: int) -> Response:
    """Retorna os detalhes completos de um atendimento (somente leitura)."""
    atendimento = get_object_or_404(Atendimento, id=atendimento_id)
    data = AtendimentoDetailSerializer(atendimento).data
    return Response({"atendimento": data})


@api_view(["GET"])  # type: ignore[misc]
@permission_classes([AllowAny])
def mensagens_list_public(_: Any, atendimento_id: int) -> Response:
    """Lista mensagens de um atendimento ordenadas por timestamp."""
    atendimento = get_object_or_404(Atendimento, id=atendimento_id)
    msgs_qs = atendimento.mensagens.order_by("timestamp")
    data = MensagemSerializer(msgs_qs, many=True).data
    return Response({"mensagens": data})
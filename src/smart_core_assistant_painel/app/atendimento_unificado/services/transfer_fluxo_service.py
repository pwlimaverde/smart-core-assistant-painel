# pyright: reportAttributeAccessIssue=false
"""Serviço para transferir atendimento entre Fluxos de Atendimento.

Wrapper simples sobre ``board_service.move_atendimento`` que descobre a
etapa inicial do fluxo destino (geralmente ``TipoEtapa.FILA``) e delega.
"""

from __future__ import annotations

from typing import Any, Optional

from django.core.exceptions import ValidationError

from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
    FluxoAtendimento,
)

from .board_service import (
    BoardMoveResult,
    move_atendimento,
)


def transferir_fluxo(
    atendimento_id: int,
    fluxo_destino_id: int,
    atendente_actor: Optional[Atendente] = None,
    motivo: Optional[str] = None,
) -> BoardMoveResult:
    """Transfere o atendimento para a etapa inicial do fluxo destino.

    Raises:
        ValidationError: Se o fluxo destino não existe ou está inativo,
            ou se não houver etapa inicial cadastrada.
        BoardMoveError: Propagado de ``move_atendimento``.
    """
    fluxo = FluxoAtendimento.objects.filter(
        id=fluxo_destino_id, ativo=True
    ).first()
    if fluxo is None:
        raise ValidationError(
            f"Fluxo destino {fluxo_destino_id} não encontrado/ativo."
        )

    etapa_inicial = fluxo.get_etapa_inicial()
    if etapa_inicial is None:
        # Fallback: primeira etapa ativa por ordem (related_name reverso).
        etapas_rel: Any = getattr(fluxo, "etapas", None)
        if etapas_rel is not None:
            etapa_inicial = (
                etapas_rel.filter(ativo=True).order_by("ordem", "id").first()
            )
    if etapa_inicial is None:
        raise ValidationError(
            f"Fluxo {fluxo.nome} não tem etapa inicial configurada."
        )

    return move_atendimento(
        atendimento_id=atendimento_id,
        etapa_destino_id=etapa_inicial.id,
        atendente_actor=atendente_actor,
        motivo=motivo or f"Transferido para fluxo {fluxo.nome}",
    )

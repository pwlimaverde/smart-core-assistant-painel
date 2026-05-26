# pyright: reportAttributeAccessIssue=false
"""Serviço para aplicar/remover etiquetas em atendimentos."""

from __future__ import annotations

from typing import Optional

from django.core.exceptions import ValidationError

from smart_core_assistant_painel.app.atendimentos.models import (
    Etiqueta,
    EtiquetaAtendimento,
)


def toggle_etiqueta(
    atendimento_id: int,
    etiqueta_id: int,
    atendente_id: Optional[int] = None,
) -> dict[str, object]:
    """Adiciona ou remove etiqueta de um atendimento (toggle).

    Returns:
        ``{"ativa": True}`` se a etiqueta passou a estar aplicada,
        ``{"ativa": False}`` se foi removida.

    Raises:
        ValidationError: Se a etiqueta não existir ou estiver inativa.
    """
    etiqueta = Etiqueta.objects.filter(id=etiqueta_id, ativo=True).first()
    if etiqueta is None:
        raise ValidationError("Etiqueta não encontrada ou inativa.")

    existente = EtiquetaAtendimento.objects.filter(
        atendimento_id=atendimento_id, etiqueta_id=etiqueta_id
    ).first()

    if existente is not None:
        existente.delete()
        return {"ativa": False, "etiqueta_id": etiqueta_id}

    EtiquetaAtendimento.objects.create(
        atendimento_id=atendimento_id,
        etiqueta_id=etiqueta_id,
        aplicada_por_id=atendente_id,
    )
    return {"ativa": True, "etiqueta_id": etiqueta_id}

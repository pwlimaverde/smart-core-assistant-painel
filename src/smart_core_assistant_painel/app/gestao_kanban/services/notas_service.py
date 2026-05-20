# pyright: reportAttributeAccessIssue=false
"""Serviço de notas internas vinculadas a atendimentos."""

from __future__ import annotations

from typing import Any, Optional

from django.core.exceptions import ValidationError

from smart_core_assistant_painel.app.atendimento_unificado.models import Nota


def criar_nota(
    atendimento_id: int,
    texto: str,
    atendente_id: Optional[int] = None,
) -> dict[str, Any]:
    """Cria uma nota interna no atendimento.

    Args:
        atendimento_id: ID lógico do atendimento.
        texto: Conteúdo livre da nota (não pode ser vazio).
        atendente_id: ID lógico do atendente autor (opcional).

    Raises:
        ValidationError: Se `texto` for vazio após strip.
    """
    if not texto or not texto.strip():
        raise ValidationError("O texto da nota não pode ser vazio.")

    nota = Nota.objects.create(
        atendimento_id=atendimento_id,
        texto=texto.strip(),
        criado_por_id=atendente_id,
    )
    return {
        "id": nota.id,
        "atendimento_id": nota.atendimento_id,
        "texto": nota.texto,
        "criado_em": nota.criado_em.isoformat(),
        "criado_por_id": nota.criado_por_id,
    }


def deletar_nota(nota_id: int, atendente_id: Optional[int] = None) -> bool:
    """Remove uma nota. Atendente só pode deletar nota própria.

    Returns:
        True se a nota foi removida, False se não foi encontrada ou se o
        atendente não é o autor.
    """
    qs = Nota.objects.filter(id=nota_id)
    if atendente_id is not None:
        qs = qs.filter(criado_por_id=atendente_id)
    deleted, _ = qs.delete()
    return deleted > 0

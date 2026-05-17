# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false
"""Despacho de mensagens do atendente humano via Workspace.

A criação de uma `Mensagem(remetente=ATENDENTE_HUMANO, resposta_bot=texto)`
dispara o signal `_on_message_saved` em `evolution_sync.signals`, que
faz o envio via Evolution API. Este service apenas monta o payload com
metadados corretos (API key da instância vinculada ao atendente, quando
existe), evitando duplicar a lógica de roteamento.
"""

from __future__ import annotations

from typing import Any, Optional

from django.db import transaction
from loguru import logger

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    Mensagem,
    TipoMensagem,
    TipoRemetente,
)
from smart_core_assistant_painel.app.operacional.models import (
    AppInstance,
    Atendente,
)


def send_text_message(
    atendimento_id: int,
    texto: str,
    atendente: Optional[Atendente] = None,
) -> Mensagem:
    """Cria mensagem de saída para envio via Evolution.

    Reaproveita o signal existente (`_on_message_saved`) que faz o
    envio quando ``resposta_bot`` é preenchido e ``respondida=False``.

    Args:
        atendimento_id: ID do `Atendimento` alvo.
        texto: Conteúdo a enviar (não pode ser vazio).
        atendente: Atendente autor da mensagem (opcional).

    Returns:
        Mensagem persistida (será marcada `respondida=True` após
        confirmação de envio pelo signal).
    """
    texto = (texto or "").strip()
    if not texto:
        raise ValueError("Texto da mensagem não pode ser vazio.")

    with transaction.atomic():
        atend = Atendimento.objects.select_for_update().get(id=atendimento_id)

        metadados = _build_metadados(atend, atendente)

        mensagem = Mensagem.objects.create(
            atendimento=atend,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            conteudo="",
            remetente=TipoRemetente.ATENDENTE_HUMANO,
            resposta_bot=texto,
            metadados=metadados,
            respondida=False,
        )

        # Atendente humano enviando msg → bot fica passivo
        if atend.bot_pode_atender:
            atend.bot_pode_atender = False
            atend.save(update_fields=["bot_pode_atender"])

        # Atualiza timestamp de ordenação
        try:
            atend.touch_last_message()
        except Exception:
            pass

    logger.info(
        "Mensagem do atendente criada (atendimento={}, msg_id={}, "
        "atendente={})",
        atendimento_id,
        mensagem.id,
        getattr(atendente, "id", None),
    )
    return mensagem


def _build_metadados(
    atend: Atendimento, atendente: Optional[Atendente]
) -> dict[str, Any]:
    """Replica a lógica usada em `transferir_para_humano_com_saudacao`.

    A API key resolvida aqui garante que a mensagem seja enviada pela
    mesma instância Evolution associada ao atendente/departamento.
    """
    metadados: dict[str, Any] = {}

    ultima = atend.mensagens.order_by("-timestamp").first()
    if ultima and ultima.metadados:
        try:
            metadados = dict(ultima.metadados)
        except Exception:
            metadados = {}

    api_key: Optional[str] = None
    app_instance: Optional[AppInstance] = None

    if atendente is not None:
        app_instance = (
            AppInstance.objects.filter(owner=atendente, active=True)
            .order_by("-created_at")
            .first()
        )
        if app_instance is None and atendente.departamento_id:
            app_instance = (
                AppInstance.objects.filter(
                    departamento_id=atendente.departamento_id, active=True
                )
                .order_by("-created_at")
                .first()
            )

    if app_instance is None and atend.departamento_id:
        app_instance = (
            AppInstance.objects.filter(
                departamento_id=atend.departamento_id, active=True
            )
            .order_by("-created_at")
            .first()
        )

    if app_instance is not None:
        api_key = str(app_instance.api_key)

    if api_key:
        evo = dict(metadados.get("evolution", {}) or {})
        evo["api_key"] = api_key
        metadados["evolution"] = evo

    return metadados

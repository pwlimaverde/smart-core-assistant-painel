# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false
"""Renderização do payload visual do card kanban.

Espelha a estrutura do card Trello (`_build_card_name` +
`_build_rich_description` em
`trello_sync.services.ticket_sync_service.TicketSyncService`), mas
retorna apenas dados estruturados para consumo pelo template
``kanban_card.html`` e pela sidebar de conversas.

Funções públicas:
    - ``render_card(atendimento)``: payload usado por ``/board/`` e SSE.
    - Helpers de emoji/tempo são módulo-level para reuso em templates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from django.utils import timezone

PRIORIDADE_LABEL_CLASSES: dict[str, str] = {
    "baixa": "bg-green-100 text-green-800",
    "normal": "bg-blue-100 text-blue-800",
    "alta": "bg-orange-100 text-orange-800",
    "urgente": "bg-red-100 text-red-800",
}

STATUS_EMOJI: dict[str, str] = {
    "fila": "⏳",
    "em_atendimento": "💬",
    "pendencia": "⏸️",
    "resolvido": "✅",
    "cancelado": "❌",
    "transferido": "↪️",
}

PRIORIDADE_EMOJI: dict[str, str] = {
    "baixa": "🟢",
    "normal": "🔵",
    "alta": "🟠",
    "urgente": "🔴",
}


def get_status_emoji(status: str) -> str:
    return STATUS_EMOJI.get(status, "📋")


def get_prioridade_emoji(prioridade: str) -> str:
    return PRIORIDADE_EMOJI.get((prioridade or "").lower(), "⚪")


def get_prioridade_label_class(prioridade: str) -> str:
    return PRIORIDADE_LABEL_CLASSES.get(
        (prioridade or "").lower(), "bg-stone-100 text-stone-700"
    )


def get_canal_emoji(canal: str) -> str:
    canal_lower = (canal or "").lower()
    if "whatsapp" in canal_lower:
        return "📱"
    if "telegram" in canal_lower:
        return "✈️"
    if "email" in canal_lower:
        return "📧"
    if "web" in canal_lower:
        return "🌐"
    return "💬"


def format_time_delta(dt: Optional[datetime]) -> str:
    """Tempo humanizado em pt-BR: ``"há 8 minutos"`` etc."""
    if dt is None:
        return ""
    try:
        delta = timezone.now() - dt
        if delta.total_seconds() < 0:
            return "agora"
        if delta.days > 0:
            return f"há {delta.days} dia(s)"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"há {hours} hora(s)"
        minutes = (delta.seconds % 3600) // 60
        if minutes > 0:
            return f"há {minutes} minuto(s)"
        return "há menos de 1 min"
    except Exception:
        return ""


def build_card_title(atendimento: Any) -> str:
    """Constrói título composto: contato - cliente - assunto - intents."""
    contato = getattr(atendimento, "contato", None)
    nome_contato: str = ""
    if contato is not None:
        nome_contato = (
            getattr(contato, "nome_contato", None)
            or getattr(contato, "nome_perfil_whatsapp", None)
            or getattr(contato, "telefone", "")
        ) or ""
    if len(nome_contato) > 40:
        nome_contato = nome_contato[:40] + "..."

    nome_fantasia: str = ""
    try:
        cliente_rel = getattr(atendimento, "cliente", None)
        if cliente_rel is not None:
            nome_fantasia = getattr(cliente_rel, "nome_fantasia", "") or ""
    except Exception:
        nome_fantasia = ""

    assunto: str = (
        getattr(atendimento, "assunto", None)
        or f"Atendimento #{getattr(atendimento, 'pk', '')}"
    )

    intents_resumo: str = ""
    try:
        hist = atendimento.carregar_historico_mensagens()
        intents_raw = hist.get("intents_detectados", []) or []
        nomes: list[str] = []
        for it in intents_raw:
            if isinstance(it, dict):
                nome = (
                    str(it.get("type", ""))
                    or str(it.get("nome", ""))
                    or str(it.get("name", ""))
                )
                if nome:
                    nomes.append(nome)
            elif isinstance(it, str) and it:
                nomes.append(it)
            if len(nomes) >= 3:
                break
        if nomes:
            intents_resumo = " | ".join(nomes)
    except Exception:
        intents_resumo = ""

    partes: list[str] = []
    if nome_contato:
        partes.append(nome_contato)
    if nome_fantasia:
        partes.append(nome_fantasia)
    if assunto:
        partes.append(assunto)
    if intents_resumo:
        partes.append(intents_resumo)
    return " - ".join(partes) if partes else assunto


def render_card(atendimento: Any) -> dict[str, Any]:
    """Payload do card kanban (formato `cards["<etapa_id>"][i]`).

    Mantém superset de chaves para reaproveitamento na sidebar de
    conversas e no modal de detalhes; consumidores ignoram chaves que
    não usam.
    """
    ultima_msg = None
    try:
        ultima_msg = atendimento.mensagens.order_by("-timestamp").first()
    except Exception:
        ultima_msg = None

    preview = ""
    preview_remetente = ""
    if ultima_msg is not None:
        raw = (
            (ultima_msg.conteudo or ultima_msg.resposta_bot or "")
            .replace("\n", " ")
            .strip()
        )
        preview = raw[:80] + ("…" if len(raw) > 80 else "")
        preview_remetente = ultima_msg.remetente

    contato = getattr(atendimento, "contato", None)
    canal = ""
    if contato is not None:
        ctx = getattr(atendimento, "contexto_conversa", None) or {}
        canal = ctx.get("canal", "") if isinstance(ctx, dict) else ""

    atendente = getattr(atendimento, "atendente_humano", None)

    return {
        "atendimento_id": atendimento.id,
        "titulo": build_card_title(atendimento),
        "status": atendimento.status,
        "status_emoji": get_status_emoji(atendimento.status),
        "prioridade": atendimento.prioridade,
        "prioridade_emoji": get_prioridade_emoji(atendimento.prioridade),
        "prioridade_label_class": get_prioridade_label_class(
            atendimento.prioridade
        ),
        "atendente": (
            {"id": atendente.id, "nome": atendente.nome}
            if atendente is not None
            else None
        ),
        "preview_msg": preview,
        "preview_remetente": preview_remetente,
        "tempo_ultima_msg": format_time_delta(
            atendimento.data_ultima_mensagem
        ),
        "data_ultima_mensagem": (
            atendimento.data_ultima_mensagem.isoformat()
            if atendimento.data_ultima_mensagem
            else None
        ),
        "canal_emoji": get_canal_emoji(canal),
        "tags": list(getattr(atendimento, "tags", []) or []),
        "campos_custom_card": [],  # populado em E.2
    }

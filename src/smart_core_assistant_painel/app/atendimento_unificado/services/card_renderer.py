# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
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


def _get_contato_nome(atendimento: Any) -> str:
    """Resolve nome do contato com fallback consistente.

    Prioridade: ``nome_contato`` (manual) → ``nome_perfil_whatsapp``
    (push_name) → ``telefone`` → ``"(sem nome)"``.
    """
    contato = getattr(atendimento, "contato", None)
    if contato is None:
        return "(sem nome)"

    nome = (
        (getattr(contato, "nome_contato", None) or "").strip()
        or (getattr(contato, "nome_perfil_whatsapp", None) or "").strip()
        or (getattr(contato, "telefone", None) or "").strip()
        or "(sem nome)"
    )
    if len(nome) > 60:
        nome = nome[:60] + "…"
    return nome


def _get_assunto(atendimento: Any) -> str:
    """Retorna o assunto do atendimento (ou string vazia)."""
    assunto = (getattr(atendimento, "assunto", None) or "").strip()
    if len(assunto) > 80:
        assunto = assunto[:80] + "…"
    return assunto


def build_card_title(atendimento: Any) -> str:
    """[DEPRECATED] Retorna apenas o nome do contato.

    Mantido por compatibilidade. Novos consumidores devem usar
    ``_get_contato_nome`` + ``_get_assunto`` diretamente, ou ler
    ``card["contato_nome"]`` / ``card["assunto"]`` do payload de
    ``render_card``.
    """
    return _get_contato_nome(atendimento)


_SLA_THRESHOLD_SECONDS = 8 * 3600  # 8 horas na etapa atual = SLA estourado


def _get_tempo_na_etapa_seconds(atendimento: Any) -> int:
    """Segundos desde a última movimentação de etapa (= tempo na etapa atual)."""
    try:
        ultimo = atendimento.movimentos_fluxo.order_by(
            "-data_movimento"
        ).first()
        if ultimo is not None and ultimo.data_movimento is not None:
            delta = timezone.now() - ultimo.data_movimento
            return max(0, int(delta.total_seconds()))
    except Exception:
        pass
    if atendimento.data_inicio is not None:
        delta = timezone.now() - atendimento.data_inicio
        return max(0, int(delta.total_seconds()))
    return 0


def render_card(
    atendimento: Any, *, nao_lidos: int = 0
) -> dict[str, Any]:
    """Payload do card kanban (formato `cards["<etapa_id>"][i]`).

    Mantém superset de chaves para reaproveitamento na sidebar de
    conversas e no modal de detalhes; consumidores ignoram chaves que
    não usam.

    O contador ``nao_lidos`` é calculado fora (em ``board_snapshot``)
    via batch-fetch de leituras do atendente corrente, para evitar
    N+1 queries. Padrão 0 quando não há atendente autenticado ou a
    contagem não se aplica.
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
    tempo_na_etapa = _get_tempo_na_etapa_seconds(atendimento)

    contato_nome = _get_contato_nome(atendimento)
    assunto = _get_assunto(atendimento)

    return {
        "atendimento_id": atendimento.id,
        "titulo": contato_nome,
        "contato_nome": contato_nome,
        "assunto": assunto,
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
        "campos_custom_card": [],
        "tempo_na_etapa_segundos": tempo_na_etapa,
        "sla_estourado": tempo_na_etapa >= _SLA_THRESHOLD_SECONDS,
        "nao_lidos": nao_lidos,
    }

"""Queries de leitura (selectors) do Workspace de Atendimento Unificado.

Toda função aqui é *read-only*: jamais persiste alterações. Mutações
ocorrem nos services (`services/*.py`).

Princípio de independência: selectors podem ler `Atendimento`/`Mensagem`/
`EtapaFluxo`/`FluxoAtendimento` diretamente (read), mas nunca os mutam.
"""

# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportUnknownArgumentType=false

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from django.db.models import Q
from loguru import logger

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoRemetente,
)
from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
    EtapaFluxo,
    FluxoAtendimento,
)

from .models import LeituraAtendimento


def list_fluxos_acessiveis(
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
) -> list[dict[str, Any]]:
    """Retorna os fluxos visíveis para o usuário/atendente atual.

    Regras:
    - Owner do tenant ou superuser vê todos os fluxos ativos.
    - Atendente regular vê apenas o fluxo ao qual está vinculado e os do
      mesmo departamento.
    """
    qs = FluxoAtendimento.objects.filter(ativo=True).select_related(
        "departamento"
    )
    if not is_owner and atendente is not None:
        condicao = Q(atendentes=atendente)
        if atendente.departamento_id:
            condicao = condicao | Q(departamento_id=atendente.departamento_id)
        qs = qs.filter(condicao).distinct()

    return [
        {
            "id": f.id,
            "nome": f.nome,
            "departamento_id": f.departamento_id,
            "departamento_nome": (
                f.departamento.nome if f.departamento_id else ""
            ),
        }
        for f in qs.order_by("departamento__nome", "nome")
    ]


def list_conversations(
    fluxo_id: Optional[int] = None,
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
    q: Optional[str] = None,
    limit: int = 100,
    cursor: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    """Lista conversas para a sidebar do Modo Conversas.

    Ordenada por `data_ultima_mensagem desc`; usa cursor (datetime) para
    paginação simples.
    """
    qs = Atendimento.objects.select_related(
        "contato",
        "atendente_humano",
        "etapa_atual",
        "fluxo_atendimento",
    ).exclude(
        status__in=[
            StatusAtendimento.RESOLVIDO,
            StatusAtendimento.CANCELADO,
        ]
    )

    if fluxo_id is not None:
        qs = qs.filter(fluxo_atendimento_id=fluxo_id)

    if not is_owner and atendente is not None:
        # Atendente vê fila do seu departamento + seus atendimentos
        qs = qs.filter(
            Q(atendente_humano=atendente)
            | Q(
                atendente_humano__isnull=True,
                departamento_id=atendente.departamento_id,
            )
        )

    if q:
        qs = qs.filter(
            Q(contato__nome_contato__icontains=q)
            | Q(contato__nome_perfil_whatsapp__icontains=q)
            | Q(contato__telefone__icontains=q)
            | Q(assunto__icontains=q)
        )

    if cursor:
        qs = qs.filter(data_ultima_mensagem__lt=cursor)

    qs = qs.order_by("-data_ultima_mensagem", "-data_inicio")[:limit]

    # Pré-busca de leituras para o atendente atual (se houver)
    leituras_map: dict[int, datetime] = {}
    if atendente is not None:
        ids = [a.id for a in qs]
        for leit in LeituraAtendimento.objects.filter(
            atendimento_id__in=ids, atendente_id=atendente.id
        ):
            leituras_map[leit.atendimento_id] = leit.ultima_leitura_at

    resultado: list[dict[str, Any]] = []
    for atend in qs:
        leitura_at = leituras_map.get(atend.id)
        nao_lidos = _contar_nao_lidos(atend.id, leitura_at)
        ultima = atend.mensagens.order_by("-timestamp").first()
        contato = atend.contato
        nome_contato = (
            getattr(contato, "nome_contato", None)
            or getattr(contato, "nome_perfil_whatsapp", None)
            or getattr(contato, "telefone", "")
            or "(sem nome)"
        )
        resultado.append(
            {
                "atendimento_id": atend.id,
                "contato_nome": nome_contato,
                "telefone": getattr(contato, "telefone", ""),
                "assunto": atend.assunto or "",
                "status": atend.status,
                "prioridade": atend.prioridade,
                "fluxo_id": atend.fluxo_atendimento_id,
                "etapa_id": atend.etapa_atual_id,
                "etapa_nome": (
                    atend.etapa_atual.nome if atend.etapa_atual_id else ""
                ),
                "atendente_id": atend.atendente_humano_id,
                "atendente_nome": (
                    atend.atendente_humano.nome
                    if atend.atendente_humano_id
                    else ""
                ),
                "preview_msg": _preview_msg(ultima),
                "preview_remetente": (ultima.remetente if ultima else ""),
                "data_ultima_mensagem": (
                    atend.data_ultima_mensagem.isoformat()
                    if atend.data_ultima_mensagem
                    else None
                ),
                "nao_lidos": nao_lidos,
            }
        )
    return resultado


def get_messages(
    atendimento_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Histórico paginado de mensagens do atendimento.

    Retorna ordem cronológica (mais antigas primeiro), mas a paginação
    é "para trás": `before_id` corta o cursor.
    """
    qs = Mensagem.objects.filter(atendimento_id=atendimento_id)
    if before_id:
        qs = qs.filter(id__lt=before_id)
    msgs = list(qs.order_by("-timestamp")[:limit])
    msgs.reverse()
    return [_serialize_mensagem(m) for m in msgs]


def board_snapshot_by_fluxo(
    fluxo_id: int,
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
) -> dict[str, Any]:
    """Snapshot completo do board kanban para um fluxo.

    Estrutura:
        {
            "etapas": [{id, nome, cor, tipo_etapa, ordem, count}],
            "cards": {"<etapa_id>": [<card_payload>, ...]}
        }

    `card_payload` é produzido por `card_renderer.render_card`.
    """
    from .services.card_renderer import render_card

    etapas_qs = EtapaFluxo.objects.filter(
        fluxo_id=fluxo_id, ativo=True
    ).order_by("ordem", "id")

    atendimentos_qs = (
        Atendimento.objects.filter(fluxo_atendimento_id=fluxo_id)
        .exclude(
            status__in=[
                StatusAtendimento.RESOLVIDO,
                StatusAtendimento.CANCELADO,
            ]
        )
        .select_related(
            "contato",
            "atendente_humano",
            "etapa_atual",
            "fluxo_atendimento",
        )
        .prefetch_related("mensagens")
    )

    if not is_owner and atendente is not None:
        atendimentos_qs = atendimentos_qs.filter(
            Q(atendente_humano=atendente) | Q(atendente_humano__isnull=True)
        )

    cards_por_etapa: dict[int, list[dict[str, Any]]] = {}
    for atend in atendimentos_qs:
        if atend.etapa_atual_id is None:
            continue
        cards_por_etapa.setdefault(atend.etapa_atual_id, []).append(
            render_card(atend)
        )

    etapas_payload = []
    cards_payload: dict[str, list[dict[str, Any]]] = {}
    for etapa in etapas_qs:
        cards_dessa = cards_por_etapa.get(etapa.id, [])
        etapas_payload.append(
            {
                "id": etapa.id,
                "nome": etapa.nome,
                "cor": etapa.cor,
                "tipo_etapa": etapa.tipo_etapa,
                "ordem": etapa.ordem,
                "count": len(cards_dessa),
            }
        )
        cards_payload[str(etapa.id)] = cards_dessa

    return {"etapas": etapas_payload, "cards": cards_payload}


def get_atendimento_detail(atendimento_id: int) -> Optional[dict[str, Any]]:
    """Bloco rico para o painel direito (intents, entidades, métricas)."""
    atend = (
        Atendimento.objects.select_related(
            "contato", "atendente_humano", "etapa_atual", "fluxo_atendimento"
        )
        .filter(id=atendimento_id)
        .first()
    )
    if not atend:
        return None

    try:
        hist = atend.carregar_historico_mensagens()
    except Exception as exc:
        logger.warning("Falha ao carregar histórico: {}", exc)
        hist = {"intents_detectados": [], "entidades_extraidas": []}

    contato = atend.contato
    return {
        "atendimento_id": atend.id,
        "contato": {
            "id": getattr(contato, "id", None),
            "nome": (
                getattr(contato, "nome_contato", None)
                or getattr(contato, "nome_perfil_whatsapp", None)
                or ""
            ),
            "telefone": getattr(contato, "telefone", ""),
            "email": getattr(contato, "email", ""),
        },
        "status": atend.status,
        "prioridade": atend.prioridade,
        "tags": list(atend.tags or []),
        "fluxo_id": atend.fluxo_atendimento_id,
        "etapa_id": atend.etapa_atual_id,
        "atendente": (
            {
                "id": atend.atendente_humano.id,
                "nome": atend.atendente_humano.nome,
                "cargo": atend.atendente_humano.cargo,
            }
            if atend.atendente_humano_id
            else None
        ),
        "data_inicio": (
            atend.data_inicio.isoformat() if atend.data_inicio else None
        ),
        "data_ultima_mensagem": (
            atend.data_ultima_mensagem.isoformat()
            if atend.data_ultima_mensagem
            else None
        ),
        "assunto": atend.assunto or "",
        "intents": hist.get("intents_detectados", []),
        "entidades": hist.get("entidades_extraidas", []),
        "bot_pode_atender": atend.bot_pode_atender,
    }


def _contar_nao_lidos(
    atendimento_id: int, leitura_at: Optional[datetime]
) -> int:
    qs = Mensagem.objects.filter(
        atendimento_id=atendimento_id, remetente=TipoRemetente.CONTATO
    )
    if leitura_at:
        qs = qs.filter(timestamp__gt=leitura_at)
    return qs.count()


def _preview_msg(mensagem: Optional[Mensagem]) -> str:
    if mensagem is None:
        return ""
    raw = mensagem.conteudo or mensagem.resposta_bot or ""
    raw = raw.replace("\n", " ").strip()
    return raw[:80] + ("…" if len(raw) > 80 else "")


def _serialize_mensagem(m: Mensagem) -> dict[str, Any]:
    return {
        "id": m.id,
        "atendimento_id": m.atendimento_id,
        "tipo": m.tipo,
        "conteudo": m.conteudo or "",
        "resposta_bot": m.resposta_bot or "",
        "remetente": m.remetente,
        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        "respondida": m.respondida,
        "message_id_whatsapp": m.message_id_whatsapp or "",
        "metadados": dict(m.metadados or {}),
    }

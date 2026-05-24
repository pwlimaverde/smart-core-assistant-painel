# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportUnknownArgumentType=false, reportReturnType=false
"""Queries de leitura (selectors) do Gestão Kanban."""

from __future__ import annotations

from typing import Any, Optional

from django.db.models import Q
from loguru import logger

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    Etiqueta,
    EtiquetaAtendimento,
    Mensagem,
    Nota,
    StatusAtendimento,
    TipoRemetente,
)
from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
    EtapaFluxo,
    FluxoAtendimento,
    TipoEtapa,
)


def list_fluxos_acessiveis(
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
    tenant_user: Any = None,
) -> list[dict[str, Any]]:
    """Retorna os fluxos visíveis para o usuário/atendente atual."""
    qs = FluxoAtendimento.objects.filter(ativo=True).select_related(
        "departamento"
    )
    if not is_owner:
        if tenant_user is not None:
            allowed_ids = (
                tenant_user.allowed_flow_ids()
                if hasattr(tenant_user, "allowed_flow_ids")
                else list(getattr(tenant_user, "flow_permissions", []) or [])
            )
            if not allowed_ids:
                return []
            qs = qs.filter(id__in=allowed_ids)
        elif atendente is not None:
            condicao = Q(atendentes=atendente)
            if atendente.departamento_id:
                condicao = condicao | Q(
                    departamento_id=atendente.departamento_id
                )
            qs = qs.filter(condicao).distinct()
        else:
            return []

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


_DOT_COLOR_BY_TIPO: dict[str, str] = {
    TipoEtapa.FILA: "#a8a29e",  # stone-400 (cinza neutro)
    TipoEtapa.TRABALHO: "#d97706",  # amber-600 (em andamento)
    TipoEtapa.ESPERA: "#f59e0b",  # amber-500 (aguardando)
    TipoEtapa.FINALIZACAO: "#16a34a",  # green-600 (concluído)
}
_DEFAULT_ETAPA_COR = "#6B7280"


def _resolve_dot_color(etapa: EtapaFluxo) -> str:
    """Cor do bullet da coluna kanban."""
    cor = (etapa.cor or "").strip()
    if cor and cor.lower() != _DEFAULT_ETAPA_COR.lower():
        return cor
    return _DOT_COLOR_BY_TIPO.get(etapa.tipo_etapa, "#a8a29e")


def board_snapshot_by_fluxo(
    fluxo_id: int,
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
    q: Optional[str] = None,
    prioridade: Optional[str] = None,
    atendente_id_filtro: Optional[int] = None,
    etiqueta_id: Optional[int] = None,
    apenas_nao_lidos: bool = False,
) -> dict[str, Any]:
    """Snapshot completo do board kanban para um fluxo."""
    from smart_core_assistant_painel.app.gestao_kanban.services.card_renderer import (
        render_card,
    )

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

    if q:
        atendimentos_qs = atendimentos_qs.filter(
            Q(contato__nome_contato__icontains=q)
            | Q(contato__nome_perfil_whatsapp__icontains=q)
            | Q(contato__telefone__icontains=q)
            | Q(assunto__icontains=q)
        )

    if prioridade:
        atendimentos_qs = atendimentos_qs.filter(prioridade=prioridade)

    if atendente_id_filtro is not None:
        atendimentos_qs = atendimentos_qs.filter(
            atendente_humano_id=atendente_id_filtro
        )

    if etiqueta_id is not None:
        ids_com_etiqueta = EtiquetaAtendimento.objects.filter(
            etiqueta_id=etiqueta_id
        ).values_list("atendimento_id", flat=True)
        atendimentos_qs = atendimentos_qs.filter(id__in=list(ids_com_etiqueta))

    if apenas_nao_lidos:
        ids_com_nao_lidos = (
            Mensagem.objects.filter(
                remetente=TipoRemetente.CONTATO, lido=False
            )
            .values_list("atendimento_id", flat=True)
            .distinct()
        )
        atendimentos_qs = atendimentos_qs.filter(
            id__in=list(ids_com_nao_lidos)
        )

    atendimentos = list(atendimentos_qs)

    cards_por_etapa: dict[int, list[dict[str, Any]]] = {}
    for atend in atendimentos:
        if atend.etapa_atual_id is None:
            continue
        nao_lidos = _contar_nao_lidos(atend.id)
        cards_por_etapa.setdefault(atend.etapa_atual_id, []).append(
            render_card(atend, nao_lidos=nao_lidos)
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
                "dot_color": _resolve_dot_color(etapa),
                "tipo_etapa": etapa.tipo_etapa,
                "ordem": etapa.ordem,
                "count": len(cards_dessa),
            }
        )
        cards_payload[str(etapa.id)] = cards_dessa

    return {"etapas": etapas_payload, "cards": cards_payload}


def _contar_nao_lidos(atendimento_id: int) -> int:
    """Conta mensagens não lidas vindas do contato."""
    return Mensagem.objects.filter(
        atendimento_id=atendimento_id,
        remetente=TipoRemetente.CONTATO,
        lido=False,
    ).count()


def _serialize_etiqueta(e: Etiqueta) -> dict[str, Any]:
    return {
        "id": e.id,
        "nome": e.nome,
        "cor": e.cor,
        "descricao": e.descricao or "",
        "ativo": e.ativo,
    }


def list_etiquetas() -> list[dict[str, Any]]:
    """Lista todas as etiquetas ativas para o popover."""
    return [
        _serialize_etiqueta(e) for e in Etiqueta.objects.filter(ativo=True)
    ]


def list_etiquetas_do_atendimento(atendimento_id: int) -> list[dict[str, Any]]:
    """Etiquetas atualmente aplicadas a um atendimento."""
    qs = EtiquetaAtendimento.objects.filter(
        atendimento_id=atendimento_id
    ).select_related("etiqueta")
    return [
        {
            **_serialize_etiqueta(ea.etiqueta),
            "aplicada_em": ea.aplicada_em.isoformat(),
        }
        for ea in qs
    ]


def list_notas(atendimento_id: int) -> list[dict[str, Any]]:
    """Lista todas as notas de um atendimento (mais recentes primeiro)."""
    from smart_core_assistant_painel.app.operacional.models import Atendente

    notas = list(Nota.objects.filter(atendimento_id=atendimento_id))
    autores_ids = [n.criado_por_id for n in notas if n.criado_por_id]
    autores_map: dict[int, str] = {}
    if autores_ids:
        autores_map = {
            a.id: a.nome for a in Atendente.objects.filter(id__in=autores_ids)
        }
    return [
        {
            "id": n.id,
            "texto": n.texto,
            "criado_em": n.criado_em.isoformat(),
            "criado_por_id": n.criado_por_id,
            "criado_por_nome": (
                autores_map.get(n.criado_por_id, "") if n.criado_por_id else ""
            ),
        }
        for n in notas
    ]


def build_timeline(atendimento_id: int) -> list[dict[str, Any]]:
    """Linha do tempo cronológica de eventos do atendimento."""
    atend = Atendimento.objects.filter(id=atendimento_id).first()
    if atend is None:
        return []

    eventos: list[dict[str, Any]] = []

    if atend.data_inicio:
        eventos.append(
            {
                "tipo": "criacao",
                "label": "Atendimento criado",
                "descricao": "",
                "autor": "",
                "timestamp": atend.data_inicio.isoformat(),
                "icone": "plus",
            }
        )

    if atend.data_primeira_resposta:
        eventos.append(
            {
                "tipo": "primeira_resposta",
                "label": "IA respondeu pela primeira vez",
                "descricao": "",
                "autor": "IA",
                "timestamp": atend.data_primeira_resposta.isoformat(),
                "icone": "bot",
            }
        )

    historico: Any = atend.historico_status or []
    if isinstance(historico, list):
        for item in historico:
            if not isinstance(item, dict):
                continue
            quando = item.get("data") or item.get("timestamp")
            if not quando:
                continue
            eventos.append(
                {
                    "tipo": "status",
                    "label": f"Status: {item.get('status', '?')}",
                    "descricao": str(item.get("observacao") or ""),
                    "autor": str(item.get("autor") or ""),
                    "timestamp": (
                        quando if isinstance(quando, str) else str(quando)
                    ),
                    "icone": "flag",
                }
            )

    try:
        movimentos_rel: Any = getattr(atend, "movimentos_fluxo", None)
        if movimentos_rel is not None:
            movimentos = movimentos_rel.select_related(
                "etapa_destino", "atendente_origem"
            ).order_by("-data_movimento")[:30]
            for mv in movimentos:
                destino_nome = (
                    mv.etapa_destino.nome
                    if getattr(mv, "etapa_destino_id", None)
                    else "?"
                )
                autor_nome = (
                    mv.atendente_origem.nome
                    if getattr(mv, "atendente_origem_id", None)
                    else ""
                )
                eventos.append(
                    {
                        "tipo": "movimento",
                        "label": f"Movido para {destino_nome}",
                        "descricao": str(getattr(mv, "motivo", "") or ""),
                        "autor": autor_nome,
                        "timestamp": mv.data_movimento.isoformat(),
                        "icone": "arrow",
                    }
                )
    except Exception as exc:
        logger.warning("Falha ao carregar movimentos de fluxo: {}", exc)

    notas = Nota.objects.filter(atendimento_id=atendimento_id).order_by(
        "-criado_em"
    )[:30]
    for n in notas:
        eventos.append(
            {
                "tipo": "nota",
                "label": "Nota interna adicionada",
                "descricao": (
                    n.texto[:80] + ("…" if len(n.texto) > 80 else "")
                ),
                "autor": "",
                "timestamp": n.criado_em.isoformat(),
                "icone": "note",
            }
        )

    eventos.sort(key=lambda e: e["timestamp"], reverse=True)
    return eventos[:50]


def contar_nao_lidos_global(
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
) -> int:
    """Total de mensagens não lidas visíveis ao atendente para o sino."""
    qs = Mensagem.objects.filter(
        remetente=TipoRemetente.CONTATO, lido=False
    ).exclude(
        atendimento__status__in=[
            StatusAtendimento.RESOLVIDO,
            StatusAtendimento.CANCELADO,
        ]
    )

    if not is_owner and atendente is not None:
        qs = qs.filter(
            Q(atendimento__atendente_humano=atendente)
            | Q(
                atendimento__atendente_humano__isnull=True,
                atendimento__departamento_id=atendente.departamento_id,
            )
        )

    return qs.count()

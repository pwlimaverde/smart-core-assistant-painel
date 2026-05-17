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

from .models import (
    CampoPersonalizado,
    LeituraAtendimento,
    OrigemValor,
    ValorCampoAtendimento,
)


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
    tag: Optional[str] = None,
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

    if tag:
        qs = qs.filter(tags__contains=[tag])

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
        "campos": _get_campos(atendimento_id),
    }


def get_campos_for_prompt(
    atendimento_id: int,
    fluxo_id: Optional[int] = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Retorna (campos_coletados, campos_pendentes) para injetar no prompt do bot.

    Helper exposto para integrações externas (ex.: orchestrator de atendimentos)
    que queiram passar campos para `AnaliseMensageParameters.campos_coletados`
    e `campos_pendentes`. Mantém princípio de independência: a integração
    chama este helper sem importar models de `atendimento_unificado`.

    Args:
        atendimento_id: ID do atendimento ativo.
        fluxo_id: Se fornecido, restringe a campos do fluxo (além dos GLOBAL).

    Returns:
        Tupla (coletados, pendentes), cada lista com dicts contendo
        `slug`, `nome`, `valor`/`descricao`, `hint`.
    """
    valores_map: dict[int, ValorCampoAtendimento] = {
        v.campo_id: v
        for v in ValorCampoAtendimento.objects.filter(
            atendimento_id=atendimento_id
        ).select_related("campo")
    }

    campos_qs = CampoPersonalizado.objects.filter(
        ativo=True, extrair_automaticamente=True
    )
    if fluxo_id is not None:
        from django.db.models import Q

        campos_qs = campos_qs.filter(
            Q(escopo="GLOBAL") | Q(escopo="FLUXO", fluxo_id=fluxo_id)
        )
    else:
        campos_qs = campos_qs.filter(escopo="GLOBAL")

    coletados: list[dict[str, Any]] = []
    pendentes: list[dict[str, Any]] = []
    for campo in campos_qs.order_by("ordem", "nome"):
        v = valores_map.get(campo.pk)
        is_coletado = v is not None and (
            v.origem != OrigemValor.BOT or (v.confianca or 0) >= 0.6
        )
        if is_coletado and v is not None:
            coletados.append(
                {"slug": campo.slug, "nome": campo.nome, "valor": v.valor}
            )
        else:
            pendentes.append(
                {
                    "slug": campo.slug,
                    "nome": campo.nome,
                    "descricao": campo.descricao or campo.nome,
                    "hint": campo.extrair_hint or "",
                }
            )
    return coletados, pendentes


def _get_campos(atendimento_id: int) -> list[dict[str, Any]]:
    """Retorna campos personalizados com valores para o painel direito."""
    valores = (
        ValorCampoAtendimento.objects.filter(atendimento_id=atendimento_id)
        .select_related("campo")
        .order_by("campo__ordem", "campo__nome")
    )
    result: list[dict[str, Any]] = []
    for v in valores:
        campo = v.campo
        valor_raw = v.valor
        if isinstance(valor_raw, list):
            valor_display = ", ".join(str(x) for x in valor_raw)
        elif valor_raw is None:
            valor_display = ""
        else:
            valor_display = str(valor_raw)
        result.append(
            {
                "slug": campo.slug,
                "nome": campo.nome,
                "tipo": campo.tipo,
                "valor_raw": valor_raw,
                "valor_display": valor_display,
                "origem": v.origem,
                "confianca": v.confianca,
            }
        )
    return result


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
        "media": _extract_media(m),
        "metadados": dict(m.metadados or {}),
    }


_MEDIA_KIND_BY_TIPO: dict[str, str] = {
    "imageMessage": "image",
    "stickerMessage": "image",
    "audioMessage": "audio",
    "videoMessage": "video",
    "documentMessage": "document",
}


def _extract_media(m: Mensagem) -> Optional[dict[str, Any]]:
    """Extrai info de mídia consumível pelo frontend.

    Lida com dois formatos:
    - Outbound (atendente humano): metadados.media.{b64, mimetype, filename}
    - Inbound (contato via Evolution): metadados.{base64, url, mimetype, ...}

    Retorna dict {kind, src (data: ou http), mimetype, filename, seconds}
    ou None se a mensagem não for mídia.
    """
    kind = _MEDIA_KIND_BY_TIPO.get(m.tipo or "")
    if not kind:
        return None

    meta: dict[str, Any] = dict(m.metadados or {})
    nested = (
        meta.get("media") if isinstance(meta.get("media"), dict) else None
    )

    mimetype = (nested or {}).get("mimetype") or meta.get("mimetype") or ""
    filename = (nested or {}).get("filename") or meta.get("fileName") or ""
    seconds = meta.get("seconds")
    b64 = (nested or {}).get("b64") or meta.get("base64") or ""
    remote_url = meta.get("url") or ""

    src: Optional[str] = None
    if b64 and isinstance(b64, str) and len(b64) > 10:
        # data URI quando temos base64 (renderizável inline)
        src = f"data:{mimetype or 'application/octet-stream'};base64,{b64}"

    return {
        "kind": kind,
        "src": src,
        "remote_url": remote_url if isinstance(remote_url, str) else "",
        "mimetype": mimetype,
        "filename": filename,
        "seconds": seconds,
    }

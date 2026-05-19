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
    TipoEtapa,
)

from .models import (
    CampoPersonalizado,
    Etiqueta,
    EtiquetaAtendimento,
    Nota,
    OrigemValor,
    ValorCampoAtendimento,
)


def list_fluxos_acessiveis(
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
    tenant_user: Any = None,
) -> list[dict[str, Any]]:
    """Retorna os fluxos visíveis para o usuário/atendente atual.

    Regras de visibilidade (avaliadas em ordem):
    - Owner do tenant ou superuser vê todos os fluxos ativos.
    - Se ``tenant_user`` informado, `flow_permissions` (lista de IDs em
      TenantUser) é a fonte de verdade: o usuário vê apenas os fluxos
      explicitamente liberados. Lista vazia ⇒ nenhum fluxo.
    - Fallback (sem tenant_user, com atendente): comportamento legado por
      vínculo operacional (Atendente.fluxo + departamento).
    """
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


def list_conversations(
    fluxo_id: Optional[int] = None,
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100,
    cursor: Optional[datetime] = None,
    prioridade: Optional[str] = None,
    atendente_id_filtro: Optional[int] = None,
    etiqueta_id: Optional[int] = None,
    apenas_nao_lidos: bool = False,
) -> list[dict[str, Any]]:
    """Lista conversas para a sidebar do Modo Conversas.

    Ordenada por `data_ultima_mensagem desc`; usa cursor (datetime) para
    paginação simples.

    Filtros opcionais (popover de filtro): prioridade, atendente humano,
    etiqueta aplicada, apenas com mensagens não lidas.
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

    if prioridade:
        qs = qs.filter(prioridade=prioridade)

    if atendente_id_filtro is not None:
        qs = qs.filter(atendente_humano_id=atendente_id_filtro)

    if etiqueta_id is not None:
        ids_com_etiqueta = EtiquetaAtendimento.objects.filter(
            etiqueta_id=etiqueta_id
        ).values_list("atendimento_id", flat=True)
        qs = qs.filter(id__in=list(ids_com_etiqueta))

    if apenas_nao_lidos:
        ids_com_nao_lidos = (
            Mensagem.objects.filter(
                remetente=TipoRemetente.CONTATO, lido=False
            )
            .values_list("atendimento_id", flat=True)
            .distinct()
        )
        qs = qs.filter(id__in=list(ids_com_nao_lidos))

    if cursor:
        qs = qs.filter(data_ultima_mensagem__lt=cursor)

    qs = qs.order_by("-data_ultima_mensagem", "-data_inicio")[:limit]

    resultado: list[dict[str, Any]] = []
    for atend in qs:
        nao_lidos = _contar_nao_lidos(atend.id)
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
    qs = Mensagem.objects.filter(atendimento_id=atendimento_id).select_related(
        "mensagem_citada"
    )
    if before_id:
        qs = qs.filter(id__lt=before_id)
    msgs = list(qs.order_by("-timestamp")[:limit])
    msgs.reverse()
    return [_serialize_mensagem(m) for m in msgs]


_DOT_COLOR_BY_TIPO: dict[str, str] = {
    TipoEtapa.FILA: "#a8a29e",          # stone-400 (cinza neutro)
    TipoEtapa.TRABALHO: "#d97706",      # amber-600 (em andamento)
    TipoEtapa.ESPERA: "#f59e0b",        # amber-500 (aguardando)
    TipoEtapa.FINALIZACAO: "#16a34a",   # green-600 (concluído)
}
_DEFAULT_ETAPA_COR = "#6B7280"


def _resolve_dot_color(etapa: EtapaFluxo) -> str:
    """Cor do bullet da coluna kanban.

    Usa ``etapa.cor`` quando o operador configurou explicitamente (i.e.,
    diferente do default ``#6B7280``); caso contrário, deriva por
    ``tipo_etapa``.
    """
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
    """Snapshot completo do board kanban para um fluxo.

    Estrutura:
        {
            "etapas": [{id, nome, cor, dot_color, tipo_etapa, ordem, count}],
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


def _contar_nao_lidos(atendimento_id: int) -> int:
    """Conta mensagens não lidas (vindas do contato) em um atendimento.

    Fonte da verdade: campo `Mensagem.lido` (atualizado em massa por
    ``board_service.mark_read``). LeituraAtendimento permanece como audit
    log mas não é mais consultado aqui.
    """
    return Mensagem.objects.filter(
        atendimento_id=atendimento_id,
        remetente=TipoRemetente.CONTATO,
        lido=False,
    ).count()


def _preview_msg(mensagem: Optional[Mensagem]) -> str:
    if mensagem is None:
        return ""
    raw = mensagem.conteudo or mensagem.resposta_bot or ""
    raw = raw.replace("\n", " ").strip()
    return raw[:80] + ("…" if len(raw) > 80 else "")


def _serialize_quoted(m: Mensagem) -> dict[str, Any] | None:
    """Serializa o bloco de mensagem citada (reply) para o frontend.

    Prioridade:
    1. FK ``mensagem_citada`` resolvida — usa dados reais da msg original.
    2. ``quoted_preview`` — preview embutido quando FK não foi resolvido.

    Returns:
        Dict com ``{remetente, conteudo_preview, tipo}`` ou ``None`` se a
        mensagem não é um reply.
    """
    citada = getattr(m, "mensagem_citada", None)
    if citada is not None:
        conteudo = (
            getattr(citada, "resposta_bot", None)
            or getattr(citada, "conteudo", "")
            or ""
        )
        return {
            "id": getattr(citada, "id", None),
            "remetente": getattr(citada, "remetente", ""),
            "tipo": getattr(citada, "tipo", "extendedTextMessage"),
            "conteudo_preview": conteudo[:200],
        }

    preview = getattr(m, "quoted_preview", None)
    if preview and isinstance(preview, dict):
        return {
            "id": None,
            "remetente": preview.get("remetente", ""),
            "tipo": preview.get("tipo", "extendedTextMessage"),
            "conteudo_preview": preview.get("conteudo_preview", ""),
        }

    return None


def _serialize_mensagem(m: Mensagem) -> dict[str, Any]:
    return {
        "id": m.id,
        "atendimento_id": m.atendimento_id,
        "tipo": m.tipo,
        "conteudo": m.conteudo or "",
        "resposta_bot": m.resposta_bot or "",
        "analise_midia": m.analise_midia or "",
        "remetente": m.remetente,
        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        "respondida": m.respondida,
        "quoted": _serialize_quoted(m),
        "status_envio": getattr(m, "status_envio", "sent") or "sent",
        "data_entregue": (
            m.data_entregue.isoformat()  # type: ignore[union-attr]
            if getattr(m, "data_entregue", None)
            else None
        ),
        "data_lida": (
            m.data_lida.isoformat()  # type: ignore[union-attr]
            if getattr(m, "data_lida", None)
            else None
        ),
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


def _format_size_label(size_bytes: Optional[int]) -> str:
    """Formata bytes em label humano (KB/MB)."""
    if not size_bytes or size_bytes <= 0:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _extract_media(m: Mensagem) -> Optional[dict[str, Any]]:
    """Extrai info de mídia consumível pelo frontend.

    Prioridade de ``src``:
        1. ``m.arquivo_midia.url`` — URL servida pelo Django/Nginx (preferido).
        2. ``data:`` URI a partir de ``metadados['base64']`` — legado/back-compat.
        3. ``None`` — frontend mostra fallback.

    Lida com dois formatos legados de metadados:
        - Outbound (atendente humano): metadados.media.{b64, mimetype, filename}
        - Inbound (contato via Evolution): metadados.{base64, url, mimetype, ...}

    Returns:
        Dict {kind, src, remote_url, mimetype, filename, seconds, size_label,
        is_pdf, ptt} ou ``None`` se a mensagem não for de mídia.
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
    remote_url = meta.get("url") or ""

    src: Optional[str] = None
    size_label = ""

    # Prioridade 1: arquivo persistido em FileField
    arquivo = getattr(m, "arquivo_midia", None)
    if arquivo:
        try:
            if arquivo.name:
                src = arquivo.url
                try:
                    size_label = _format_size_label(arquivo.size)
                except Exception:
                    size_label = ""
                if not filename:
                    filename = arquivo.name.rsplit("/", 1)[-1]
        except Exception:
            src = None

    # Prioridade 2: data URI legacy via base64 em metadados
    if not src:
        b64 = (nested or {}).get("b64") or meta.get("base64") or ""
        if b64 and isinstance(b64, str) and len(b64) > 10:
            src = (
                f"data:{mimetype or 'application/octet-stream'};base64,{b64}"
            )

    is_pdf = kind == "document" and (
        (mimetype or "").lower() == "application/pdf"
        or (filename or "").lower().endswith(".pdf")
    )

    return {
        "kind": kind,
        "src": src,
        "remote_url": remote_url if isinstance(remote_url, str) else "",
        "mimetype": mimetype,
        "filename": filename,
        "seconds": seconds,
        "size_label": size_label,
        "is_pdf": is_pdf,
        "ptt": bool(meta.get("ptt", False)),
    }


# ---------------------------------------------------------------------------
# E.3 — Etiquetas, Notas, Mídias, Timeline, Notificações
# ---------------------------------------------------------------------------


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
    return [_serialize_etiqueta(e) for e in Etiqueta.objects.filter(ativo=True)]


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
            a.id: a.nome
            for a in Atendente.objects.filter(id__in=autores_ids)
        }
    return [
        {
            "id": n.id,
            "texto": n.texto,
            "criado_em": n.criado_em.isoformat(),
            "criado_por_id": n.criado_por_id,
            "criado_por_nome": (
                autores_map.get(n.criado_por_id, "")
                if n.criado_por_id
                else ""
            ),
        }
        for n in notas
    ]


def list_medias(atendimento_id: int) -> list[dict[str, Any]]:
    """Lista mídias e documentos de um atendimento (mais recentes primeiro)."""
    tipos_midia = list(_MEDIA_KIND_BY_TIPO.keys())
    qs = (
        Mensagem.objects.filter(
            atendimento_id=atendimento_id, tipo__in=tipos_midia
        )
        .order_by("-timestamp")
    )
    resultado: list[dict[str, Any]] = []
    for m in qs:
        info = _extract_media(m)
        if info is None:
            continue
        resultado.append(
            {
                "mensagem_id": m.id,
                "kind": info["kind"],
                "src": info["src"],
                "remote_url": info["remote_url"],
                "mimetype": info["mimetype"],
                "filename": info["filename"],
                "timestamp": m.timestamp.isoformat(),
                "remetente": m.remetente,
            }
        )
    return resultado


def build_timeline(atendimento_id: int) -> list[dict[str, Any]]:
    """Linha do tempo cronológica de eventos do atendimento.

    Agrega:
    - Criação do atendimento (data_inicio)
    - Itens de `historico_status` (JSONField já existente)
    - Movimentos de fluxo (`MovimentoFluxo` em operacional)
    - Notas criadas
    - data_primeira_resposta (quando IA respondeu)

    Limitado a 50 eventos, ordem decrescente (mais recente primeiro).
    """
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

    # JSONField — em runtime pode vir como lista, dict ou outro.
    historico: Any = atend.historico_status or []
    if isinstance(historico, list):  # pyright: ignore[reportUnnecessaryIsInstance]
        for item in historico:
            if not isinstance(item, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
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
    """Total de mensagens não lidas visíveis ao atendente para o sino.

    Usa o mesmo escopo de `list_conversations` (fila do departamento +
    atendimentos próprios), aplicado em Mensagem via `atendimento__`.
    """
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

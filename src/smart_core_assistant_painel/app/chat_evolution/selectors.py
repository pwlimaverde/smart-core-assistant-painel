# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false, reportReturnType=false, reportOptionalMemberAccess=false
"""Queries de leitura (selectors) do Chat Evolution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from django.db.models import Q

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    CampoPersonalizado,
    EtiquetaAtendimento,
    Mensagem,
    OrigemValor,
    StatusAtendimento,
    TipoRemetente,
    ValorCampoAtendimento,
)
from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
    FluxoAtendimento,
)


def list_fluxos_acessiveis(
    atendente: Optional[Atendente] = None,
    is_owner: bool = False,
    tenant_user: Any = None,
) -> list[dict[str, Any]]:
    """Retorna os fluxos visíveis para o usuário/atendente atual.

    Helper de controle de acesso compartilhado pelas views do chat. Mora
    aqui (e não em ``gestao_kanban``) para evitar import cruzado entre apps.

    Args:
        atendente: Atendente vinculado ao usuário, quando houver.
        is_owner: ``True`` se o usuário tem acesso irrestrito (owner/superuser).
        tenant_user: ``TenantUser`` do request, quando houver.

    Returns:
        Lista de dicts ``{id, nome, departamento_id, departamento_nome}``.
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
        avatar_url = ""
        foto = getattr(contato, "foto_perfil", None)
        try:
            if foto and getattr(foto, "name", ""):
                avatar_url = foto.url
        except Exception:
            avatar_url = ""
        resultado.append(
            {
                "atendimento_id": atend.id,
                "contato_nome": nome_contato,
                "contato_avatar_url": avatar_url,
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
    """Histórico paginado de mensagens do atendimento."""
    qs = Mensagem.objects.filter(atendimento_id=atendimento_id).select_related(
        "mensagem_citada"
    )
    if before_id:
        qs = qs.filter(id__lt=before_id)
    msgs = list(qs.order_by("-timestamp")[:limit])
    msgs.reverse()
    return [_serialize_mensagem(m) for m in msgs]


def get_atendimento_detail(atendimento_id: int) -> Optional[dict[str, Any]]:
    """Bloco rico para o painel direito."""
    from loguru import logger

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
    """Retorna (campos_coletados, campos_pendentes) para injetar no prompt do bot."""
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
    """Conta mensagens não lidas (vindas do contato) em um atendimento."""
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


_MEDIA_KIND_BY_TIPO: dict[str, str] = {
    "imageMessage": "image",
    "stickerMessage": "image",
    "audioMessage": "audio",
    "videoMessage": "video",
    "documentMessage": "document",
}


def _format_size_label(size_bytes: Optional[int]) -> str:
    if not size_bytes or size_bytes <= 0:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _extract_media(m: Mensagem) -> Optional[dict[str, Any]]:
    kind = _MEDIA_KIND_BY_TIPO.get(m.tipo or "")
    if not kind:
        return None

    meta: dict[str, Any] = dict(m.metadados or {})
    nested = meta.get("media") if isinstance(meta.get("media"), dict) else None

    mimetype = (nested or {}).get("mimetype") or meta.get("mimetype") or ""
    filename = (nested or {}).get("filename") or meta.get("fileName") or ""
    seconds = meta.get("seconds")
    remote_url = meta.get("url") or ""

    src: Optional[str] = None
    size_label = ""

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

    if not src:
        b64 = (nested or {}).get("b64") or meta.get("base64") or ""
        if b64 and isinstance(b64, str) and len(b64) > 10:
            src = f"data:{mimetype or 'application/octet-stream'};base64,{b64}"

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


def _serialize_mensagem(m: Mensagem) -> dict[str, Any]:
    return {
        "id": m.id,
        "atendimento_id": m.atendimento_id,
        "tipo": m.tipo,
        "conteudo": m.conteudo or "",
        "resposta_bot": m.resposta_bot or "",
        # resumo_midia: resumo curto exibido ao atendente.
        "resumo_midia": m.resumo_midia or "",
        # analise_midia (contexto completo do bot) só é trafegada para áudio —
        # nela a transcrição é o conteúdo útil ao atendente. Para mídia visual
        # a análise completa permanece interna (não exposta no chat).
        "analise_midia": (
            (m.analise_midia or "")
            if (m.tipo or "") == "audioMessage"
            else ""
        ),
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


def list_medias(atendimento_id: int) -> list[dict[str, Any]]:
    """Lista mídias e documentos de um atendimento (mais recentes primeiro)."""
    tipos_midia = list(_MEDIA_KIND_BY_TIPO.keys())
    qs = Mensagem.objects.filter(
        atendimento_id=atendimento_id, tipo__in=tipos_midia
    ).order_by("-timestamp")
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

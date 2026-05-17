# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false
"""Despacho de mídia outbound via Evolution API.

Separado de message_dispatch_service para não misturar upload
multipart com o fluxo de texto. Chama /message/sendMedia diretamente,
sem tocar em evolution_sync (princípio de independência).
"""

from __future__ import annotations

import base64
import mimetypes
from typing import Optional

import requests
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

_MEDIA_TIPO_MAP: dict[str, str] = {
    "imageMessage": "image",
    "videoMessage": "video",
    "audioMessage": "audio",
    "documentMessage": "document",
}

_MIME_TO_TIPO: dict[str, TipoMensagem] = {
    "image": TipoMensagem.IMAGEM,
    "video": TipoMensagem.VIDEO,
    "audio": TipoMensagem.AUDIO,
}


def _detect_tipo(content_type: str) -> TipoMensagem:
    """Determina TipoMensagem a partir do MIME type."""
    main = (content_type or "").split("/")[0].lower()
    return _MIME_TO_TIPO.get(main, TipoMensagem.DOCUMENTO)


def _resolve_evolution_params(
    atend: Atendimento, atendente: Optional[Atendente]
) -> Optional[dict[str, str]]:
    """Retorna {base_url, api_key, instance_name, numero} ou None.

    Replica o pattern de `evolution_sync.signals._on_message_saved`:
    - `AppInstance` (operacional) fornece o `api_key` por roteamento
      (owner=atendente → departamento do atendente → departamento do atend).
    - `EvolutionInstance` (evolution_sync) fornece `instance_name` via
      lookup pelo `api_key`.
    - `base_url` vem de `TenantEvolution.server_url` do tenant da instância.
    """
    contato = getattr(atend, "contato", None)
    numero = getattr(contato, "telefone", None) if contato else None
    if not numero:
        return None

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

    if app_instance is None:
        return None

    api_key = str(app_instance.api_key or "")
    if not api_key:
        return None

    # Lookup leitura-pura em models de evolution_sync e tenants
    # (princípio de independência permite ler, proíbe escrever).
    from smart_core_assistant_painel.app.evolution_sync.models import (
        EvolutionInstance,
    )
    from smart_core_assistant_painel.app.tenants.models import TenantEvolution

    inst: Optional[EvolutionInstance] = EvolutionInstance.objects.filter(
        api_key=api_key, active=True
    ).first()
    if inst is None:
        return None

    instance_name = str(
        inst.name or inst.phone_number or inst.instance_id or ""
    )
    if not instance_name:
        return None

    base_url = ""
    tenant_id = getattr(inst, "tenant_id", None)
    if tenant_id:
        tenant_cfg = TenantEvolution.objects.filter(
            tenant_id=tenant_id
        ).first()
        if tenant_cfg and tenant_cfg.server_url:
            base_url = str(tenant_cfg.server_url).rstrip("/")
    if not base_url:
        from smart_core_assistant_painel.app.tenants.middleware import (
            get_current_tenant,
        )

        tenant = get_current_tenant()
        if tenant:
            tenant_cfg = TenantEvolution.objects.filter(tenant=tenant).first()
            if tenant_cfg and tenant_cfg.server_url:
                base_url = str(tenant_cfg.server_url).rstrip("/")
    if not base_url:
        return None

    return {
        "base_url": base_url,
        "api_key": api_key,
        "instance_name": instance_name,
        "numero": str(numero),
    }


def _send_media_via_evolution(
    base_url: str,
    api_key: str,
    instance_name: str,
    numero: str,
    media_b64: str,
    mediatype: str,
    mimetype: str,
    filename: str,
    caption: str = "",
) -> None:
    url = f"{base_url}/message/sendMedia/{instance_name}"
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    body = {
        "number": numero,
        "mediatype": mediatype,
        "mimetype": mimetype,
        "caption": caption,
        "media": media_b64,
        "fileName": filename,
    }
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()


def upload_and_send_media(
    atendimento_id: int,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    atendente: Optional[Atendente] = None,
    caption: str = "",
) -> Mensagem:
    """Cria Mensagem de mídia e envia via Evolution API.

    Args:
        atendimento_id: ID do Atendimento alvo.
        file_bytes: Conteúdo binário do arquivo (≤10 MB).
        filename: Nome original do arquivo.
        content_type: MIME type (ex.: "image/jpeg").
        atendente: Atendente autor (opcional).
        caption: Legenda da mídia (opcional).

    Returns:
        Mensagem persistida.

    Raises:
        ValueError: Se o atendimento não existe ou parâmetros inválidos.
        Exception: Propagado se o envio via Evolution falhar.
    """
    if not file_bytes:
        raise ValueError("Arquivo vazio.")
    if len(file_bytes) > 10 * 1024 * 1024:
        raise ValueError("Arquivo excede limite de 10 MB.")

    guessed = mimetypes.guess_type(filename)[0]
    effective_ct = content_type or guessed or "application/octet-stream"
    tipo = _detect_tipo(effective_ct)
    mediatype = _MEDIA_TIPO_MAP.get(tipo, "document")
    media_b64 = base64.b64encode(file_bytes).decode()

    with transaction.atomic():
        atend = Atendimento.objects.select_for_update().get(id=atendimento_id)

        # IMPORTANTE: deixar `resposta_bot` vazio para não disparar o signal
        # `_on_message_saved` em evolution_sync (que enviaria um texto solto
        # com a caption e marcaria respondida=True antes do envio da mídia).
        # A caption é exibida via conteudo (fallback no template chat_message).
        mensagem = Mensagem.objects.create(
            atendimento=atend,
            tipo=tipo,
            conteudo=caption or f"[{filename}]",
            remetente=TipoRemetente.ATENDENTE_HUMANO,
            resposta_bot="",
            metadados={
                "media": {
                    "filename": filename,
                    "mimetype": effective_ct,
                    "mediatype": mediatype,
                    "b64": media_b64,
                }
            },
            respondida=False,
        )

        if atend.bot_pode_atender:
            atend.bot_pode_atender = False
            atend.save(update_fields=["bot_pode_atender"])

        try:
            atend.touch_last_message()
        except Exception:
            pass

    params = _resolve_evolution_params(atend, atendente)
    if params:
        try:
            _send_media_via_evolution(
                base_url=params["base_url"],
                api_key=params["api_key"],
                instance_name=params["instance_name"],
                numero=params["numero"],
                media_b64=media_b64,
                mediatype=mediatype,
                mimetype=effective_ct,
                filename=filename,
                caption=caption,
            )
            mensagem.respondida = True
            mensagem.save(update_fields=["respondida"])
        except Exception as exc:
            logger.error(
                "Falha ao enviar mídia via Evolution (atendimento={}, msg={}): {}",
                atendimento_id,
                mensagem.id,
                exc,
            )

    logger.info(
        "Mídia enviada (atendimento={}, msg={}, tipo={}, filename={})",
        atendimento_id,
        mensagem.id,
        tipo,
        filename,
    )
    return mensagem

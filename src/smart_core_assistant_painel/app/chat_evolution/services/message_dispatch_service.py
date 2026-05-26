# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false
"""Despacho de mensagens do atendente humano via Workspace.

A criação de uma `Mensagem(remetente=ATENDENTE_HUMANO, resposta_bot=texto)`
dispara o signal `_on_message_saved` em `evolution_sync.signals`, que
faz o envio via Evolution API. Este service apenas monta o payload com
metadados corretos (API key da instância vinculada ao atendente, quando
existe), evitando duplicar a lógica de roteamento.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from django.db import router, transaction
from django.utils import timezone
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
    quoted_message_id: Optional[int] = None,
) -> Mensagem:
    """Cria mensagem de saída para envio via Evolution.

    Reaproveita o signal existente (`_on_message_saved`) que faz o
    envio quando ``resposta_bot`` é preenchido e ``respondida=False``.

    Args:
        atendimento_id: ID do `Atendimento` alvo.
        texto: Conteúdo a enviar (não pode ser vazio).
        atendente: Atendente autor da mensagem (opcional).
        quoted_message_id: ID (PK) de ``Mensagem`` a citar (reply).

    Returns:
        Mensagem persistida (será marcada `respondida=True` após
        confirmação de envio pelo signal).
    """
    texto = (texto or "").strip()
    if not texto:
        raise ValueError("Texto da mensagem não pode ser vazio.")

    with transaction.atomic(using=router.db_for_write(Atendimento)):
        atend = Atendimento.objects.select_for_update().get(id=atendimento_id)

        metadados = _build_metadados(atend, atendente)

        # Resolve mensagem citada — inclui o message_id_whatsapp nos metadados
        # para que o signal de envio passe o `quoted` para o Evolution Go.
        mensagem_citada: Optional[Mensagem] = None
        if quoted_message_id:
            mensagem_citada = Mensagem.objects.filter(
                id=quoted_message_id,
                atendimento_id=atendimento_id,
            ).first()
            if mensagem_citada and mensagem_citada.message_id_whatsapp:
                metadados["quoted_whatsapp_id"] = (
                    mensagem_citada.message_id_whatsapp
                )

        mensagem = Mensagem.objects.create(
            atendimento=atend,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            conteudo="",
            remetente=TipoRemetente.ATENDENTE_HUMANO,
            resposta_bot=texto,
            metadados=metadados,
            respondida=False,
            mensagem_citada=mensagem_citada,
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


def mark_read(
    atendimento_id: int,
    atendente_id: int,
) -> datetime:
    """Marca todas as mensagens não lidas do contato como lidas.

    Faz duas coisas:
    1. Atualiza em massa ``Mensagem.lido=True`` para mensagens vindas do
       contato — fonte da verdade do contador do sino e dos cards.
    2. Dispara markread no Evolution Go (best-effort, throttled).
       Throttle: 1 chamada por atendimento por abertura de conversa (cache 60s).

    Args:
        atendimento_id: ID do ``Atendimento`` cujas mensagens serão lidas.
        atendente_id: ID do ``Atendente`` que efetuou a leitura.

    Returns:
        Instante (UTC) da leitura.
    """
    Mensagem.objects.filter(
        atendimento_id=atendimento_id,
        remetente=TipoRemetente.CONTATO,
        lido=False,
    ).update(lido=True)

    try:
        _dispatch_evolution_markread(atendimento_id)
    except Exception as exc:
        logger.warning(
            "mark_read: falha ao disparar markread Evolution: {}", exc
        )

    return timezone.now()


def _dispatch_evolution_markread(atendimento_id: int) -> None:
    """Chama markread no Evolution Go para o atendimento.

    Throttle: 1 chamada por atendimento a cada 60 segundos via Django cache.

    Args:
        atendimento_id: ID do atendimento cujas mensagens devem ser marcadas.
    """
    from django.core.cache import cache

    from smart_core_assistant_painel.app.evolution_sync.models import (
        EvolutionContact,
    )
    from smart_core_assistant_painel.app.evolution_sync.services import (
        EvolutionGoAdapter,
    )
    from smart_core_assistant_painel.app.tenants.models import TenantEvolution

    throttle_key = f"evo_markread_throttle_{atendimento_id}"
    if cache.get(throttle_key):
        return  # throttled — já foi chamado nesta janela
    cache.set(throttle_key, 1, timeout=60)

    atendimento = (
        Atendimento.objects.select_related("contato")
        .filter(id=atendimento_id)
        .first()
    )
    if not atendimento or not atendimento.contato:
        return

    contato = atendimento.contato
    evo_contact = (
        EvolutionContact.objects.select_related("instance")
        .filter(contact_id=contato.id, active=True)
        .order_by("-updated_at")
        .first()
    )
    if not evo_contact or not evo_contact.instance:
        return

    inst = evo_contact.instance
    base_url = ""
    tenant_id = getattr(inst, "tenant_id", None)
    if tenant_id:
        tenant_cfg = TenantEvolution.objects.filter(
            tenant_id=tenant_id
        ).first()
        if tenant_cfg and tenant_cfg.server_url:
            base_url = str(tenant_cfg.server_url).rstrip("/")
    if not base_url:
        return

    msg_ids = list(
        Mensagem.objects.filter(
            atendimento_id=atendimento_id,
            remetente=TipoRemetente.CONTATO,
        )
        .exclude(message_id_whatsapp__isnull=True)
        .exclude(message_id_whatsapp="")
        .values_list("message_id_whatsapp", flat=True)[:50]
    )
    if not msg_ids:
        return

    phone = str(getattr(contato, "telefone", "") or "").strip()
    jid = evo_contact.jid or (f"{phone}@s.whatsapp.net" if phone else "")
    if not jid:
        return

    adapter = EvolutionGoAdapter()
    adapter.mark_read(
        instance=inst.name,
        api_key=str(inst.api_key),
        base_url=base_url,
        number=jid,
        message_ids=list(msg_ids),
    )

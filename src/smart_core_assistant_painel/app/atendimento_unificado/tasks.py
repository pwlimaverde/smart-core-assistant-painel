# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false
"""Celery tasks do app Atendimento Unificado.

``extract_custom_fields_async`` extrai campos personalizados da conversa
usando o LLM configurado no tenant, gravando resultados em
`ValorCampoAtendimento`. A task obedece a regra de idempotência:
nunca sobrescreve valores com `origem=MANUAL`.
"""

from __future__ import annotations

from typing import Any

from celery import shared_task
from loguru import logger

from smart_core_assistant_painel.app.tenants.celery import TenantTask


@shared_task(base=TenantTask, acks_late=True)
def extract_custom_fields_async(
    tenant_slug: str,
    atendimento_id: int,
    mensagem_id: int,
) -> None:
    """Extrai campos personalizados da conversa e persiste no banco.

    Disparada pelo signal `_on_mensagem_saved` quando uma mensagem do
    ASSISTENTE_VIRTUAL é salva. Executa de forma assíncrona para não
    bloquear o fluxo de resposta ao contato.

    Args:
        tenant_slug: Slug do tenant (setado pelo TenantTask).
        atendimento_id: ID do Atendimento a processar.
        mensagem_id: ID da Mensagem que disparou a extração.
    """
    import time

    # Aguarda um instante para garantir que a transação foi commitada
    time.sleep(1)

    try:
        _run_extraction(atendimento_id=atendimento_id, mensagem_id=mensagem_id)
    except Exception as exc:
        logger.error(
            "extract_custom_fields_async: falha para atendimento={} mensagem={}: {}",
            atendimento_id,
            mensagem_id,
            exc,
        )
        raise


def _run_extraction(atendimento_id: int, mensagem_id: int) -> None:
    """Núcleo da extração — separado para facilitar testes."""
    from smart_core_assistant_painel.app.atendimentos.models import (
        Mensagem,
    )
    from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
        FeaturesCompose,
    )
    from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
        CampoDefinicao,
    )

    from .models import CampoPersonalizado, OrigemValor, ValorCampoAtendimento

    # 1. Busca campos configurados para extração no tenant
    campos_qs = CampoPersonalizado.objects.filter(
        extrair_automaticamente=True, ativo=True
    ).order_by("ordem", "nome")

    if not campos_qs.exists():
        logger.debug(
            "extract_custom_fields: sem campos para extrair (atendimento={})",
            atendimento_id,
        )
        return

    # 2. Filtra campos que ainda não têm valor MANUAL (respeitando idempotência)
    valores_manuais = set(
        ValorCampoAtendimento.objects.filter(
            atendimento_id=atendimento_id,
            origem=OrigemValor.MANUAL,
        ).values_list("campo_id", flat=True)
    )

    campos_pendentes: list[CampoDefinicao] = []
    for campo in campos_qs:
        if campo.pk in valores_manuais:
            continue
        # Skip se já tem BOT com confiança alta
        valor_existente = ValorCampoAtendimento.objects.filter(
            atendimento_id=atendimento_id,
            campo=campo,
            origem=OrigemValor.BOT,
            confianca__gte=0.9,
        ).first()
        if valor_existente:
            continue
        campos_pendentes.append(
            CampoDefinicao(
                slug=campo.slug,
                nome=campo.nome,
                descricao=campo.descricao or campo.nome,
                hint=campo.extrair_hint or "",
                tipo=campo.tipo,
                opcoes=list(campo.opcoes or []),
            )
        )

    if not campos_pendentes:
        logger.debug(
            "extract_custom_fields: todos campos já têm valor (atendimento={})",
            atendimento_id,
        )
        return

    # 3. Monta histórico de conversa (últimas 40 mensagens)
    mensagens = Mensagem.objects.filter(
        atendimento_id=atendimento_id
    ).order_by("-timestamp")[:40]
    historico: list[dict[str, Any]] = [
        {
            "remetente": m.remetente,
            "conteudo": (m.conteudo or m.resposta_bot or "").strip(),
        }
        for m in reversed(list(mensagens))
        if (m.conteudo or m.resposta_bot or "").strip()
    ]

    if not historico:
        return

    # 4. Invoca LLM para extração
    extraidos = FeaturesCompose.extracao_campos(
        atendimento_id=atendimento_id,
        historico_conversa=historico,
        campos_a_extrair=campos_pendentes,
    )

    if not extraidos:
        logger.debug(
            "extract_custom_fields: nenhum campo extraído (atendimento={})",
            atendimento_id,
        )
        return

    # 5. Persiste resultados respeitando idempotência
    slug_to_campo: dict[str, Any] = {c.slug: c for c in campos_qs}
    persistidos = 0
    for campo_extraido in extraidos:
        campo_obj = slug_to_campo.get(campo_extraido.slug)
        if campo_obj is None:
            continue

        # Nunca sobrescreve MANUAL
        if campo_obj.pk in valores_manuais:
            continue

        # Só sobrescreve BOT se confiança nova for maior
        valor_atual = ValorCampoAtendimento.objects.filter(
            atendimento_id=atendimento_id,
            campo=campo_obj,
        ).first()
        if valor_atual and valor_atual.origem == OrigemValor.MANUAL:
            continue
        if (
            valor_atual
            and valor_atual.confianca is not None
            and campo_extraido.confianca <= valor_atual.confianca
        ):
            continue

        ValorCampoAtendimento.objects.update_or_create(
            atendimento_id=atendimento_id,
            campo=campo_obj,
            defaults={
                "valor": campo_extraido.valor,
                "origem": OrigemValor.BOT,
                "confianca": campo_extraido.confianca,
                "mensagem_origem_id": mensagem_id,
            },
        )
        persistidos += 1

    logger.info(
        "extract_custom_fields: {} campos persistidos para atendimento={}",
        persistidos,
        atendimento_id,
    )

    if persistidos > 0:
        # Publica evento SSE para o UI atualizar o painel de campos
        try:
            from .services.realtime_publisher import publish_event

            publish_event(
                "custom_field.updated",
                {"atendimento_id": atendimento_id, "count": persistidos},
            )
        except Exception as exc:
            logger.warning(
                "extract_custom_fields: falha ao publicar SSE: {}", exc
            )

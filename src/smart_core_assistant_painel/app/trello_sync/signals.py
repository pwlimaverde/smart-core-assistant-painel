from typing import Any

from django.db import router, transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
    EtapaFluxo,
    FluxoAtendimento,
    TipoEtapa,
)
from smart_core_assistant_painel.app.tenants.tenant_context import (
    get_current_tenant_slug,
)
from smart_core_assistant_painel.app.trello_sync.models import TrelloCard
from smart_core_assistant_painel.app.trello_sync.tasks import (
    task_atendente_invite,
    task_atendente_remove_member,
    task_atendimento_ensure_card,
    task_atendimento_move_to_etapa_list,
    task_atendimento_sync_card_members,
    task_atendimento_update_card_rich_content,
    task_etapa_archive_list,
    task_etapa_ensure_list,
    task_fluxo_archive_board,
    task_fluxo_ensure_board,
    task_reorder_lists_for_fluxo,
    task_trello_archive_card_by_external_id,
)


@receiver(post_save, sender=FluxoAtendimento)
def fluxo_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria Board Trello ao criar FluxoAtendimento (após commit)."""
    if not created:
        return
    try:
        slug = get_current_tenant_slug()
        fluxo_id = instance.id
        db = router.db_for_write(FluxoAtendimento)
        transaction.on_commit(
            lambda: task_fluxo_ensure_board.delay(slug, fluxo_id),
            using=db,
        )
    except Exception as exc:
        logger.error("Falha ao criar board Trello: {}", exc)


@receiver(post_save, sender=EtapaFluxo)
def etapa_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria List Trello quando nova etapa e reordena listas (após commit)."""
    try:
        # Prevenção de loop: se a criação veio do Trello, não enviar de volta
        if getattr(instance, "_syncing_from_trello", False):
            return

        slug = get_current_tenant_slug()
        etapa_id = instance.id
        fluxo_id = instance.fluxo_id
        db = router.db_for_write(EtapaFluxo)

        if created:
            transaction.on_commit(
                lambda: task_etapa_ensure_list.delay(slug, etapa_id),
                using=db,
            )
        transaction.on_commit(
            lambda: task_reorder_lists_for_fluxo.delay(slug, fluxo_id),
            using=db,
        )
    except Exception as exc:
        logger.warning("Falha ao operar listas: {}", exc)


@receiver(pre_delete, sender=EtapaFluxo)
def etapa_deleted_archive_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva a List Trello ao excluir uma EtapaFluxo (imediato)."""
    try:
        # Prevenção de loop: se a exclusão veio do Trello, não enviar de volta
        if getattr(instance, "_syncing_from_trello", False):
            return

        task_etapa_archive_list.delay(get_current_tenant_slug(), instance.id)
    except Exception as exc:
        logger.warning("Falha ao arquivar lista: {}", exc)


@receiver(pre_delete, sender=FluxoAtendimento)
def fluxo_deleted_archive_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva o Board Trello ao excluir um FluxoAtendimento (imediato)."""
    try:
        # Tenta recuperar o board associado antes que seja deletado em cascata
        trello_board = getattr(instance, "trello_board", None)
        if trello_board and trello_board.external_id:
            task_fluxo_archive_board.delay(
                get_current_tenant_slug(), trello_board.external_id
            )
        else:
            logger.warning(
                "Board Trello não encontrado para arquivamento do fluxo {}",
                instance.id,
            )
    except Exception as exc:
        logger.warning("Falha ao agendar arquivamento do board: {}", exc)


@receiver(post_save, sender=Atendimento)
def atendimento_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria Card Trello ao criar Atendimento (após commit)."""
    if not created:
        return
    try:
        slug = get_current_tenant_slug()
        atendimento_id = instance.id
        db = router.db_for_write(Atendimento)
        transaction.on_commit(
            lambda: task_atendimento_ensure_card.delay(slug, atendimento_id),
            using=db,
        )
    except Exception as exc:
        logger.warning("Falha ao criar card: {}", exc)


@receiver(post_save, sender=Atendente)
def atendente_created_invite_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Envia convite para o board do fluxo ao cadastrar Atendente (após commit)."""
    if not created:
        return
    try:
        slug = get_current_tenant_slug()
        atendente_id = instance.id
        db = router.db_for_write(Atendente)
        transaction.on_commit(
            lambda: task_atendente_invite.delay(slug, atendente_id),
            using=db,
        )
    except Exception as exc:
        logger.warning("Falha ao convidar atendente: {}", exc)


@receiver(pre_delete, sender=Atendente)
def atendente_deleted_remove_member_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Remove o atendente do board Trello ao excluir o registro."""
    try:
        task_atendente_remove_member.delay(
            get_current_tenant_slug(), instance.id
        )
    except Exception as exc:
        logger.warning("Falha ao remover atendente: {}", exc)


@receiver(post_save, sender=Atendimento)
def atendimento_updated_assign_member_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Atualiza o card quando `atendente_humano` é definido.

    - Garante card existente.
    - Resolve `external_id` do membro e adiciona ao card.
    - Atualiza descrição do card com contexto do atendente.
    """
    if created:
        return
    try:
        slug = get_current_tenant_slug()
        atendimento_id = instance.id
        old_id = getattr(instance, "_old_atendente_id", None)
        db = router.db_for_write(Atendimento)
        transaction.on_commit(
            lambda: task_atendimento_sync_card_members.delay(
                slug, atendimento_id, old_id
            ),
            using=db,
        )
    except Exception as exc:
        logger.warning("Falha ao atualizar card Trello: {}", exc)


@receiver(pre_save, sender=Atendimento)
def atendimento_capture_old_atendente(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Captura o atendente anterior antes de salvar o Atendimento.

    Comentário: guarda o ID anterior no ``instance`` para uso
    no ``post_save`` e sincronização dos membros do card.
    """
    try:
        if getattr(instance, "pk", None):
            prev = Atendimento.objects.filter(pk=instance.pk).first()
            if prev is not None:
                instance._old_atendente_id = getattr(  # type: ignore[attr-defined]
                    prev, "atendente_humano_id", None
                )
            else:
                instance._old_atendente_id = None  # type: ignore[attr-defined]
    except Exception:
        # Comentário: falhas de captura não devem bloquear o fluxo
        pass


@receiver(pre_save, sender=Atendimento)
def atendimento_capture_old_etapa(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Captura a etapa anterior antes de salvar o Atendimento.

    Comentário: guarda o ID anterior no ``instance`` para uso
    no ``post_save`` e evitar agendamentos quando não há mudança.
    """
    try:
        if getattr(instance, "pk", None):
            prev = Atendimento.objects.filter(pk=instance.pk).first()
            if prev is not None:
                instance._old_etapa_id = getattr(  # type: ignore[attr-defined]
                    prev, "etapa_atual_id", None
                )
            else:
                instance._old_etapa_id = None  # type: ignore[attr-defined]
    except Exception as exc:
        logger.warning(
            "Falha ao capturar etapa anterior do atendimento {}: {}",
            getattr(instance, "pk", "?"),
            exc,
        )


@receiver(post_save, sender=Atendimento)
def atendimento_etapa_updated_move_card(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Move o card para a lista da etapa quando a etapa muda.

    Comentário: se a etapa foi definida pela primeira vez (old_etapa_id era
    None e agora tem valor), garante a criação do card. Caso contrário,
    agenda a task de movimento; a task valida se há mudança efetiva de lista
    antes de chamar a API.
    """
    if created:
        return
    try:
        old_etapa_id = getattr(instance, "_old_etapa_id", None)
        new_etapa_id = getattr(instance, "etapa_atual_id", None)

        if old_etapa_id == new_etapa_id:
            # Comentário: sem alteração efetiva de etapa, evita agendar.
            return

        # Prevenção de loop: se a atualização veio do Trello, não enviar de volta
        if getattr(instance, "_syncing_from_trello", False):
            return

        slug = get_current_tenant_slug()
        atendimento_id = instance.id
        db = router.db_for_write(Atendimento)

        if old_etapa_id is None and new_etapa_id is not None:
            # old_etapa_id=None pode significar:
            # a) etapa realmente definida pela primeira vez (card não existe)
            # b) falha na captura do pre_save (card já existe)
            try:
                has_card = TrelloCard.objects.filter(
                    atendimento_id=instance.id
                ).exists()
            except Exception:
                has_card = False

            if has_card:
                transaction.on_commit(
                    lambda: task_atendimento_move_to_etapa_list.delay(
                        slug, atendimento_id
                    ),
                    using=db,
                )
                logger.info(
                    "Card existente para atendimento {}. "
                    "Agendando movimento (etapa anterior não capturada).",
                    instance.id,
                )
            else:
                transaction.on_commit(
                    lambda: task_atendimento_ensure_card.delay(
                        slug, atendimento_id
                    ),
                    using=db,
                )
                logger.info(
                    "Primeira etapa para atendimento {}. "
                    "Agendando criação de card.",
                    instance.id,
                )
        else:
            # Etapa mudou (já existia) - apenas mover o card
            transaction.on_commit(
                lambda: task_atendimento_move_to_etapa_list.delay(
                    slug, atendimento_id
                ),
                using=db,
            )
    except Exception as exc:
        logger.warning("Falha ao mover/criar card Trello: {}", exc)


@receiver(post_save, sender=Atendimento)
def atendimento_resolvido_move_to_resolvido(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Move o card para a lista padrão "Resolvido" ao marcar como resolvido.

    Comentário:
    - Em vez de arquivar o card, ajusta a `etapa_atual` do atendimento
      para a etapa "Resolvido" do fluxo associado e salva.
    - O receiver `atendimento_etapa_updated_move_card` cuidará de agendar
      a task que move o card para a lista da etapa.
    """
    if created:
        return
    try:
        if instance.status != StatusAtendimento.RESOLVIDO:
            return

        # Resolve o fluxo de contexto: preferir o da etapa atual; se ausente,
        # usar o primeiro fluxo ativo do departamento (se houver).
        fluxo: FluxoAtendimento | None = None
        try:
            fluxo = getattr(
                getattr(instance, "etapa_atual", None), "fluxo", None
            )
        except Exception:
            fluxo = None
        if fluxo is None:
            try:
                dep = getattr(instance, "departamento", None)
                fluxo = getattr(dep, "get_fluxo", lambda: None)()
            except Exception:
                fluxo = None

        if fluxo is None:
            logger.warning(
                "Não foi possível determinar fluxo para mover resolvido: {}",
                instance.id,
            )
            return

        # Busca etapa "Resolvido" (prioriza nome exato; senão pega a primeira
        # etapa de finalização como fallback, ordenada por `ordem`).
        etapa_res: EtapaFluxo | None = None
        try:
            etapa_res = fluxo.etapas.filter(nome__iexact="Resolvido").first()
            if etapa_res is None:
                etapa_res = (
                    fluxo.etapas.filter(tipo_etapa=TipoEtapa.FINALIZACAO)
                    .order_by("ordem")
                    .first()
                )
        except Exception:
            etapa_res = None

        if etapa_res is None:
            logger.warning(
                "Etapa 'Resolvido' não encontrada no fluxo #{}, atendimento #{},"
                " mantendo comportamento padrão sem arquivar.",
                fluxo.id,
                instance.id,
            )
            return

        # Atualiza a etapa somente se diferente para evitar loops e re-agendamentos.
        try:
            needs_update: bool = getattr(
                instance, "etapa_atual_id", None
            ) != getattr(etapa_res, "id", None)
        except Exception as exc:
            logger.warning("Falha ao verificar etapa 'Resolvido': {}", exc)
            needs_update = False

        if needs_update:
            try:
                instance.etapa_atual = etapa_res
                # Comentário: salvar com `update_fields` para minimizar side-effects.
                instance.save(update_fields=["etapa_atual"])  # type: ignore[arg-type]
            except Exception as exc:
                logger.warning(
                    "Falha ao ajustar etapa 'Resolvido' no atendimento: {}",
                    exc,
                )
    except Exception as exc:
        logger.warning(
            "Falha no processamento de movimentação para 'Resolvido': {}",
            exc,
        )


@receiver(post_save, sender=Atendimento)
def atendimento_pendencia_move_to_pendencia(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Move o card para a lista padrão "Pendência" ao marcar como pendência.

    Comentário:
    - Ajusta a `etapa_atual` do atendimento para a etapa "Pendência"
      do fluxo associado e salva.
    - O receiver `atendimento_etapa_updated_move_card` cuidará de agendar
      a task que move o card para a lista da etapa.
    """
    if created:
        return
    try:
        if instance.status != StatusAtendimento.PENDENCIA:
            return

        # Resolve o fluxo de contexto: preferir o da etapa atual; se ausente,
        # usar o primeiro fluxo ativo do departamento (se houver).
        fluxo: FluxoAtendimento | None = None
        try:
            fluxo = getattr(
                getattr(instance, "etapa_atual", None), "fluxo", None
            )
        except Exception:
            fluxo = None
        if fluxo is None:
            try:
                dep = getattr(instance, "departamento", None)
                fluxo = getattr(dep, "get_fluxo", lambda: None)()
            except Exception:
                fluxo = None

        if fluxo is None:
            logger.warning(
                "Não foi possível determinar fluxo para mover pendência: {}",
                instance.id,
            )
            return

        # Busca etapa "Pendência" (prioriza nome exato; senão pega a primeira
        # etapa de espera como fallback, ordenada por `ordem`).
        etapa_pend: EtapaFluxo | None = None
        try:
            etapa_pend = fluxo.etapas.filter(nome__iexact="Pendência").first()
            if etapa_pend is None:
                etapa_pend = (
                    fluxo.etapas.filter(tipo_etapa=TipoEtapa.ESPERA)
                    .order_by("ordem")
                    .first()
                )
        except Exception:
            etapa_pend = None

        if etapa_pend is None:
            logger.warning(
                "Etapa 'Pendência' não encontrada no fluxo #{}, atendimento #{},"
                " mantendo comportamento padrão.",
                fluxo.id,
                instance.id,
            )
            return

        # Atualiza a etapa somente se diferente para evitar loops e re-agendamentos.
        try:
            if getattr(instance, "etapa_atual_id", None) != getattr(
                etapa_pend, "id", None
            ):
                instance.etapa_atual = etapa_pend
                # Comentário: salvar com `update_fields` para minimizar side-effects.
                instance.save(update_fields=["etapa_atual"])  # type: ignore[arg-type]
        except Exception as exc:
            logger.warning(
                "Falha ao ajustar etapa 'Pendência' no atendimento: {}",
                exc,
            )
    except Exception as exc:
        logger.warning(
            "Falha no processamento de movimentação para 'Pendência': {}",
            exc,
        )


@receiver(post_save, sender=Atendimento)
def atendimento_cancelado_move_to_cancelado(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Move o card para a lista padrão "Cancelado" ao marcar como cancelado.

    Comentário:
    - Em vez de arquivar o card, ajusta a `etapa_atual` do atendimento
      para a etapa "Cancelado" do fluxo associado e salva.
    - O receiver `atendimento_etapa_updated_move_card` cuidará de agendar
      a task que move o card para a lista da etapa.
    """
    if created:
        return
    try:
        if instance.status != StatusAtendimento.CANCELADO:
            return

        # Resolve o fluxo de contexto: preferir o da etapa atual; se ausente,
        # usar o primeiro fluxo ativo do departamento (se houver).
        fluxo: FluxoAtendimento | None = None
        try:
            fluxo = getattr(
                getattr(instance, "etapa_atual", None), "fluxo", None
            )
        except Exception:
            fluxo = None
        if fluxo is None:
            try:
                dep = getattr(instance, "departamento", None)
                fluxo = getattr(dep, "get_fluxo", lambda: None)()
            except Exception:
                fluxo = None

        if fluxo is None:
            logger.warning(
                "Não foi possível determinar fluxo para mover cancelado: {}",
                instance.id,
            )
            return

        # Busca etapa "Cancelado" (prioriza nome exato; senão pega a primeira
        # etapa de finalização como fallback, ordenada por `ordem`).
        etapa_cancel: EtapaFluxo | None = None
        try:
            etapa_cancel = fluxo.etapas.filter(
                nome__iexact="Cancelado"
            ).first()
            if etapa_cancel is None:
                etapa_cancel = (
                    fluxo.etapas.filter(tipo_etapa=TipoEtapa.FINALIZACAO)
                    .order_by("ordem")
                    .first()
                )
        except Exception:
            etapa_cancel = None

        if etapa_cancel is None:
            logger.warning(
                "Etapa 'Cancelado' não encontrada no fluxo #{}, atendimento #{},"
                " mantendo comportamento padrão sem arquivar.",
                fluxo.id,
                instance.id,
            )
            return

        # Atualiza a etapa somente se diferente para evitar loops e re-agendamentos.
        try:
            if getattr(instance, "etapa_atual_id", None) != getattr(
                etapa_cancel, "id", None
            ):
                instance.etapa_atual = etapa_cancel
                # Comentário: salvar com `update_fields` para minimizar side-effects.
                instance.save(update_fields=["etapa_atual"])  # type: ignore[arg-type]
        except Exception as exc:
            logger.warning(
                "Falha ao ajustar etapa 'Cancelado' no atendimento: {}", exc
            )
    except Exception as exc:
        logger.warning(
            "Falha no processamento de movimentação para 'Cancelado': {}",
            exc,
        )


@receiver(pre_delete, sender=Atendimento)
def atendimento_deleted_archive_card(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva o card Trello ao excluir um Atendimento.

    Tenta arquivamento síncrono via ServiceHub para consistência imediata.
    Se falhar ou timeout, faz fallback para task assíncrona.

    Comentário: usa o ``external_id`` do card.
    """
    # Import local para evitar ciclos.
    from smart_core_assistant_painel.modules.services.features.service_hub import (
        SERVICEHUB,
    )

    try:
        card = getattr(instance, "trello_card", None)
        # Validação robusta do ID
        external_id: str = getattr(card, "external_id", "") if card else ""

        if not external_id:
            logger.warning(
                "Atendimento {} sem card Trello (external_id) para arquivar.",
                instance.id,
            )
            return

        # Tentativa Síncrona
        try:
            logger.info(
                "Tentando arquivar card {} síncronamente (Atendimento {})...",
                external_id,
                instance.id,
            )
            SERVICEHUB.unified_data_service.archive_item(external_id)
            logger.info("Card {} arquivado com sucesso (Sync).", external_id)
            return
        except Exception as sync_exc:
            logger.error(
                "Falha no arquivamento síncrono do card {}: {}. "
                "Agendando fallback assíncrono.",
                external_id,
                sync_exc,
            )

        # Fallback Assíncrono
        task_trello_archive_card_by_external_id.delay(
            get_current_tenant_slug(), external_id
        )
        logger.info("Fallback assíncrono agendado para card {}.", external_id)

    except Exception as exc:
        logger.critical(
            "Erro crítico ao processar arquivamento do card p/ Atendimento {}: {}",
            instance.id,
            exc,
        )


@receiver(post_save, sender=Mensagem)
def mensagem_created_update_trello_card(
    sender: Any, instance: Mensagem, created: bool, **kwargs: Any
) -> None:
    """Atualiza card Trello ao criar uma nova ``Mensagem``.

    Comentário: agenda atualização de descrição/custom fields do card
    associado ao ``Atendimento`` para refletir mensagens recentes.

    Re-dispara em updates quando ``conteudo`` muda (caso típico:
    ``AttendanceOrchestrator._convert_media_context`` substitui o
    placeholder de mídia pelo texto interpretado pela LLM) ou quando
    ``resposta_bot`` é populado.
    """
    update_fields = kwargs.get("update_fields") or []
    is_relevant_update = update_fields and (
        "resposta_bot" in update_fields or "conteudo" in update_fields
    )

    if not created and not is_relevant_update:
        return
    try:
        at_id: int = instance.atendimento_id  # type: ignore[assignment]
        # Captura contexto atual para uso no callback
        current_slug = get_current_tenant_slug()
        db = router.db_for_write(Mensagem)
        transaction.on_commit(
            lambda: task_atendimento_update_card_rich_content.delay(
                current_slug, at_id
            ),
            using=db,
        )
    except Exception as exc:
        logger.warning(
            "Falha ao atualizar card por nova mensagem: {}",
            exc,
        )

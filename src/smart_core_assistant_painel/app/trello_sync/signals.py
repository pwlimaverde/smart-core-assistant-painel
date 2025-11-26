from typing import Any

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django_q.tasks import async_task
from loguru import logger

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.ui.operacional.models import (
    Atendente,
    EtapaFluxo,
    FluxoAtendimento,
    TipoEtapa,
)


@receiver(post_save, sender=FluxoAtendimento)
def fluxo_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria Board Trello ao criar FluxoAtendimento (execução imediata)."""
    if not created:
        return
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_fluxo_ensure_board"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.error("Falha ao criar board Trello: {}", exc)


@receiver(post_save, sender=EtapaFluxo)
def etapa_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria List Trello quando nova etapa e reordena listas (imediato)."""
    try:
        if created:
            async_task(
                (
                    "smart_core_assistant_painel.app.trello_sync.tasks"
                    ".task_etapa_ensure_list"
                ),
                instance.id,
            )
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_reorder_lists_for_fluxo"
            ),
            instance.fluxo_id,
        )
    except Exception as exc:
        logger.warning("Falha ao operar listas: {}", exc)


@receiver(pre_delete, sender=EtapaFluxo)
def etapa_deleted_archive_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva a List Trello ao excluir uma EtapaFluxo (imediato)."""
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_etapa_archive_list"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao arquivar lista: {}", exc)


@receiver(pre_delete, sender=FluxoAtendimento)
def fluxo_deleted_archive_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva o Board Trello ao excluir um FluxoAtendimento (imediato)."""
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_fluxo_archive_board"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao arquivar board: {}", exc)


@receiver(post_save, sender=Atendimento)
def atendimento_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria Card Trello ao criar Atendimento (execução imediata)."""
    if not created:
        return
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_ensure_card"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao criar card: {}", exc)


@receiver(post_save, sender=Atendente)
def atendente_created_invite_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Envia convite para o board do fluxo ao cadastrar Atendente."""
    if not created:
        return
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendente_invite"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao convidar atendente: {}", exc)


@receiver(pre_delete, sender=Atendente)
def atendente_deleted_remove_member_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Remove o atendente do board Trello ao excluir o registro."""
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendente_remove_member"
            ),
            instance.id,
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
        old_id = getattr(instance, "_old_atendente_id", None)
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_sync_card_members"
            ),
            instance.id,
            old_id,
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
    except Exception:
        # Comentário: falhas de captura não devem bloquear o fluxo
        pass


@receiver(post_save, sender=Atendimento)
def atendimento_etapa_updated_move_card(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Move o card para a lista da etapa quando a etapa muda.

    Comentário: sempre agenda a task de movimento pós-update; a task
    valida se há mudança efetiva de lista antes de chamar a API.
    """
    if created:
        return
    try:
        old_etapa_id = getattr(instance, "_old_etapa_id", None)
        if old_etapa_id == getattr(instance, "etapa_atual_id", None):
            # Comentário: sem alteração efetiva de etapa, evita agendar.
            return

        # Prevenção de loop: se a atualização veio do Trello, não enviar de volta
        if getattr(instance, "_syncing_from_trello", False):
            return

        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_move_to_etapa_list"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao mover card Trello: {}", exc)


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

    Comentário: usa o ``external_id`` do card (se disponível) e agenda
    arquivamento direto para evitar depender do banco após a deleção.
    """
    try:
        card = getattr(instance, "trello_card", None)
        external_id: str = getattr(card, "external_id", "") if card else ""
        if external_id:
            async_task(
                (
                    "smart_core_assistant_painel.app.trello_sync.tasks"
                    ".task_trello_archive_card_by_external_id"
                ),
                external_id,
            )
        else:
            logger.warning(
                "Atendimento {} sem card Trello para arquivar na deleção",
                instance.id,
            )
    except Exception as exc:
        logger.warning("Falha ao arquivar por deleção: {}", exc)


@receiver(post_save, sender=Mensagem)
def mensagem_created_update_trello_card(
    sender: Any, instance: Mensagem, created: bool, **kwargs: Any
) -> None:
    """Atualiza card Trello ao criar uma nova ``Mensagem``.

    Comentário: agenda atualização de descrição/custom fields do card
    associado ao ``Atendimento`` para refletir mensagens recentes.
    """
    if not created:
        return
    try:
        at_id: int = instance.atendimento_id  # type: ignore[assignment]
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_update_card_rich_content"
            ),
            at_id,
        )
    except Exception as exc:
        logger.warning(
            "Falha ao atualizar card por nova mensagem: {}",
            exc,
        )

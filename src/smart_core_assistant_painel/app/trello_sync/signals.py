from typing import Any

from django_q.tasks import async_task
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.ui.operacional.models import (
    EtapaFluxo,
    FluxoAtendimento,
    Atendente,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
    Mensagem,
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
        async_task(
            (
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_assign_member_and_update"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao atualizar card Trello: {}", exc)


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
def atendimento_resolvido_archive_card(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Arquiva o card quando o atendimento é marcado como resolvido.

    Comentário: detecta transição de status para RESOLVIDO e agenda a
    task de arquivamento do card associado.
    """
    if created:
        return
    try:
        if instance.status == StatusAtendimento.RESOLVIDO:
            async_task(
                (
                    "smart_core_assistant_painel.app.trello_sync.tasks"
                    ".task_atendimento_archive_card"
                ),
                instance.id,
            )
    except Exception as exc:
        logger.warning("Falha ao arquivar card Trello: {}", exc)


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

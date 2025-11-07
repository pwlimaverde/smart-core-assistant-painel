from typing import Any

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.trello_sync.services import (
    FlowSyncService,
    TicketSyncService,
)
from smart_core_assistant_painel.app.ui.operacional.models import (
    EtapaFluxo,
    FluxoAtendimento,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
)


@receiver(post_save, sender=FluxoAtendimento)
def fluxo_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria Board Trello ao criar FluxoAtendimento (se novo)."""
    if not created:
        return
    try:
        FlowSyncService().ensure_board_for_fluxo(instance)
    except Exception as exc:
        logger.error("Falha ao criar board Trello: {}", exc)


@receiver(post_save, sender=EtapaFluxo)
def etapa_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria List Trello quando nova etapa e reordena listas do board.

    Comentário: em criação, garantimos a lista; sempre após, reordenamos
    o board conforme `etapa.ordem`.
    """
    service = FlowSyncService()
    if created:
        try:
            service.ensure_list_for_etapa(instance)
        except Exception as exc:
            logger.error("Falha ao criar list Trello: {}", exc)

    try:
        service.reorder_lists_for_fluxo(instance.fluxo)
    except Exception as exc:
        logger.warning("Falha ao reordenar listas: {}", exc)


@receiver(pre_delete, sender=EtapaFluxo)
def etapa_deleted_archive_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva a List Trello ao excluir uma EtapaFluxo.

    Comentário: utiliza wrapper de serviço para fechar a lista no Trello
    antes da remoção em cascade dos registros locais.
    """
    try:
        FlowSyncService().archive_list_for_etapa(instance)
    except Exception as exc:
        logger.warning("Falha ao arquivar list Trello: {}", exc)


@receiver(pre_delete, sender=FluxoAtendimento)
def fluxo_deleted_archive_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva o Board Trello ao excluir um FluxoAtendimento.

    Comentário: fecha o board no Trello para remover da visualização.
    """
    try:
        FlowSyncService().archive_board_for_fluxo(instance)
    except Exception as exc:
        logger.warning("Falha ao arquivar board Trello: {}", exc)


@receiver(post_save, sender=Atendimento)
def atendimento_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria Card Trello ao criar Atendimento (se houver etapa atual)."""
    if not created:
        return
    try:
        TicketSyncService().ensure_card_for_atendimento(instance)
    except Exception as exc:
        logger.warning("Card Trello não criado: {}", exc)

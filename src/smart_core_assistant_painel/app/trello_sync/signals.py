from typing import Any

from datetime import timedelta
from django.utils import timezone
from django_q.models import Schedule
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
)


@receiver(post_save, sender=FluxoAtendimento)
def fluxo_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria Board Trello ao criar FluxoAtendimento (se novo)."""
    if not created:
        return
    try:
        schedule_name = f"trello_flow_board_{instance.id}"
        Schedule.objects.create(
            name=schedule_name,
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_fluxo_ensure_board"
            ),
            args=str(instance.id),
            schedule_type=Schedule.ONCE,
            next_run=timezone.now() + timedelta(seconds=1),
        )
    except Exception as exc:
        logger.error("Falha ao agendar criação de board Trello: {}", exc)


@receiver(post_save, sender=EtapaFluxo)
def etapa_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria List Trello quando nova etapa e reordena listas do board.

    Comentário: em criação, garantimos a lista; sempre após, reordenamos
    o board conforme `etapa.ordem`.
    """
    try:
        if created:
            Schedule.objects.create(
                name=f"trello_etapa_list_{instance.id}",
                func=(
                    "smart_core_assistant_painel.app.trello_sync.tasks"
                    ".task_etapa_ensure_list"
                ),
                args=str(instance.id),
                schedule_type=Schedule.ONCE,
                next_run=timezone.now() + timedelta(seconds=1),
            )
        Schedule.objects.create(
            name=f"trello_flow_reorder_{instance.fluxo_id}",
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_reorder_lists_for_fluxo"
            ),
            args=str(instance.fluxo_id),
            schedule_type=Schedule.ONCE,
            next_run=timezone.now() + timedelta(seconds=2),
        )
    except Exception as exc:
        logger.warning("Falha ao agendar operações de listas: {}", exc)


@receiver(pre_delete, sender=EtapaFluxo)
def etapa_deleted_archive_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva a List Trello ao excluir uma EtapaFluxo.

    Comentário: utiliza wrapper de serviço para fechar a lista no Trello
    antes da remoção em cascade dos registros locais.
    """
    try:
        Schedule.objects.create(
            name=f"trello_etapa_archive_{instance.id}",
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_etapa_archive_list"
            ),
            args=str(instance.id),
            schedule_type=Schedule.ONCE,
            next_run=timezone.now() + timedelta(seconds=1),
        )
    except Exception as exc:
        logger.warning("Falha ao agendar arquivamento de lista: {}", exc)


@receiver(pre_delete, sender=FluxoAtendimento)
def fluxo_deleted_archive_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Arquiva o Board Trello ao excluir um FluxoAtendimento.

    Comentário: fecha o board no Trello para remover da visualização.
    """
    try:
        Schedule.objects.create(
            name=f"trello_flow_archive_{instance.id}",
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_fluxo_archive_board"
            ),
            args=str(instance.id),
            schedule_type=Schedule.ONCE,
            next_run=timezone.now() + timedelta(seconds=1),
        )
    except Exception as exc:
        logger.warning("Falha ao agendar arquivamento de board: {}", exc)


@receiver(post_save, sender=Atendimento)
def atendimento_created_sync_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Cria Card Trello ao criar Atendimento (se houver etapa atual)."""
    if not created:
        return
    try:
        Schedule.objects.create(
            name=f"trello_at_card_{instance.id}",
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_ensure_card"
            ),
            args=str(instance.id),
            schedule_type=Schedule.ONCE,
            next_run=timezone.now() + timedelta(seconds=1),
        )
    except Exception as exc:
        logger.warning("Falha ao agendar criação de card: {}", exc)


@receiver(post_save, sender=Atendente)
def atendente_created_invite_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Envia convite para o board do fluxo ao cadastrar Atendente."""
    if not created:
        return
    try:
        Schedule.objects.create(
            name=f"trello_member_invite_{instance.id}",
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendente_invite"
            ),
            args=str(instance.id),
            schedule_type=Schedule.ONCE,
            next_run=timezone.now() + timedelta(seconds=1),
        )
    except Exception as exc:
        logger.warning("Falha ao agendar convite de atendente: {}", exc)


@receiver(pre_delete, sender=Atendente)
def atendente_deleted_remove_member_trello(
    sender: Any, instance: Any, **kwargs: Any
) -> None:
    """Remove o atendente do board Trello ao excluir o registro.

    Comentário: resolve o `member_id` no contexto do board do fluxo
    e executa a remoção via adapter Trello. Caso o membro não exista
    ou ainda não tenha aceitado o convite, registra aviso.
    """
    try:
        Schedule.objects.create(
            name=f"trello_member_remove_{instance.id}",
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendente_remove_member"
            ),
            args=str(instance.id),
            schedule_type=Schedule.ONCE,
            next_run=timezone.now() + timedelta(seconds=1),
        )
    except Exception as exc:
        logger.warning("Falha ao agendar remoção de atendente: {}", exc)


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
        Schedule.objects.create(
            name=f"trello_at_assign_{instance.id}",
            func=(
                "smart_core_assistant_painel.app.trello_sync.tasks"
                ".task_atendimento_assign_member_and_update"
            ),
            args=str(instance.id),
            schedule_type=Schedule.ONCE,
            next_run=timezone.now() + timedelta(seconds=1),
        )
    except Exception as exc:
        logger.warning("Falha ao agendar atualização de card Trello: {}", exc)

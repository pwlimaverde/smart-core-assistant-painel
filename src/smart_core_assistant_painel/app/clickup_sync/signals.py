from typing import Any

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.ui.operacional.models import (
    FluxoAtendimento,
    EtapaFluxo,
    Departamento,
    Atendente,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento

from .tasks import enqueue_task
from .services.department_provision_service import DepartmentProvisionService


@receiver(post_save, sender=FluxoAtendimento)
def fluxo_created_sync_clickup(
    sender: Any, instance: FluxoAtendimento, created: bool, **kwargs: Any
) -> None:
    """Cria/garante List ClickUp ao criar FluxoAtendimento (assíncrono)."""
    try:
        if created:
            enqueue_task("task_fluxo_ensure_list", instance.id)
    except Exception as exc:
        logger.error("Falha ao garantir list ClickUp: {}", exc)


@receiver(post_save, sender=EtapaFluxo)
def etapa_created_sync_clickup(
    sender: Any, instance: EtapaFluxo, created: bool, **kwargs: Any
) -> None:
    """Reconfigura statuses da List quando nova etapa e reordena (assíncrono)."""
    try:
        # Sempre reconfigura após criação/atualização
        enqueue_task("task_etapa_reconfigure_statuses", instance.fluxo_id)
    except Exception as exc:
        logger.warning("Falha ao reconfigurar statuses: {}", exc)


@receiver(pre_delete, sender=EtapaFluxo)
def etapa_deleted_reconfigure_clickup(
    sender: Any, instance: EtapaFluxo, **kwargs: Any
) -> None:
    """Reconfigura statuses da List ao excluir uma EtapaFluxo (assíncrono)."""
    try:
        enqueue_task("task_etapa_reconfigure_statuses", instance.fluxo_id)
    except Exception as exc:
        logger.warning("Falha ao reconfigurar após exclusão: {}", exc)


@receiver(pre_delete, sender=FluxoAtendimento)
def fluxo_deleted_archive_clickup(
    sender: Any, instance: FluxoAtendimento, **kwargs: Any
) -> None:
    """Arquiva a List ClickUp ao excluir um FluxoAtendimento (assíncrono)."""
    try:
        enqueue_task("task_fluxo_archive_list", instance.id)
    except Exception as exc:
        logger.warning("Falha ao arquivar list: {}", exc)


@receiver(pre_save, sender=Atendimento)
def atendimento_capture_old_fields(
    sender: Any, instance: Atendimento, **kwargs: Any
) -> None:
    """Captura atendente e etapa anteriores antes de salvar o Atendimento.

    Comentário: guarda IDs antigos para uso no pós-save.
    """
    try:
        if getattr(instance, "pk", None):
            prev = Atendimento.objects.filter(pk=instance.pk).first()
            if prev is not None:
                instance._old_atendente_id = getattr(prev, "atendente_humano_id", None)  # type: ignore[attr-defined]
                instance._old_etapa_id = getattr(prev, "etapa_atual_id", None)  # type: ignore[attr-defined]
            else:
                instance._old_atendente_id = None  # type: ignore[attr-defined]
                instance._old_etapa_id = None  # type: ignore[attr-defined]
    except Exception:
        # Comentário: falhas de captura não devem bloquear o fluxo
        pass


@receiver(post_save, sender=Atendimento)
def atendimento_post_save(
    sender: Any, instance: Atendimento, created: bool, **kwargs: Any
) -> None:
    """Sincroniza Task ClickUp para Atendimento (assíncrono)."""
    try:
        if created:
            enqueue_task("task_atendimento_ensure_task", instance.id)
            return

        # Atualiza membros e conteúdo rico do card
        old_id = getattr(instance, "_old_atendente_id", None)
        enqueue_task("task_atendimento_sync_task_members", instance.id, old_id)

        # Atualiza apenas se etapa mudou
        old_etapa_id = getattr(instance, "_old_etapa_id", None)
        if old_etapa_id != getattr(instance, "etapa_atual_id", None):
            enqueue_task("task_atendimento_update_task_rich_content", instance.id)
    except Exception as exc:
        logger.warning("Falha ao sincronizar Task ClickUp: {}", exc)


@receiver(post_save, sender=Atendente)
def atendente_created_invite_clickup(
    sender: Any, instance: Atendente, created: bool, **kwargs: Any
) -> None:
    """Invita/Registra membro ao criar Atendente (assíncrono)."""
    if not created:
        return
    try:
        enqueue_task("task_atendente_invite", instance.id)
    except Exception as exc:
        logger.warning("Falha ao convidar atendente: {}", exc)


@receiver(pre_delete, sender=Atendente)
def atendente_deleted_remove_member_clickup(
    sender: Any, instance: Atendente, **kwargs: Any
) -> None:
    """Remove membro ao excluir Atendente (assíncrono, no-op)."""
    try:
        enqueue_task("task_atendente_remove_member", instance.id)
    except Exception as exc:
        logger.warning("Falha ao remover atendente: {}", exc)


@receiver(post_save, sender=Departamento)
def departamento_post_save(
    sender: Any, instance: Departamento, created: bool, **kwargs: Any
) -> None:
    """Ao criar Departamento, garante Folder no ClickUp (Space único).

    Comentário: segue arquitetura proposta (space único, folder por departamento).
    """
    if not created:
        return None
    svc = DepartmentProvisionService()
    try:
        svc.provision_on_department_create(instance)
        logger.info("Provisionamento ClickUp concluído para Departamento {}", instance.id)
    except Exception as exc:
        logger.error("Falha no provisionamento ClickUp para Departamento {}: {}", instance.id, str(exc))
    return None
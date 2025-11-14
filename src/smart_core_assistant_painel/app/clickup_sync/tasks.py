from typing import Any

from loguru import logger
from django_q.tasks import async_task

from .services import FlowSyncService, TicketSyncService, MemberSyncService
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
)


def task_fluxo_ensure_list(fluxo_id: int) -> None:
    """Garante a List para o Fluxo e configura statuses a partir do banco."""
    # Comentário: evita falha no cluster quando Fluxo não existe
    try:
        FlowSyncService().ensure_list_for_fluxo_from_db(fluxo_id)
    except RuntimeError as exc:
        logger.warning("FluxoAtendimento não encontrado: {}", fluxo_id)
        logger.warning("Detalhe: {}", exc)
    except Exception as exc:
        logger.error("Falha ao garantir list do fluxo {}: {}", fluxo_id, exc)


def task_fluxo_archive_list(fluxo_id: int) -> None:
    """Arquiva a List relativa ao Fluxo."""
    FlowSyncService().archive_list_for_fluxo(fluxo_id)


def task_fluxo_delete_list(fluxo_id: int) -> None:
    """Exclui permanentemente a List relativa ao Fluxo."""
    FlowSyncService().delete_list_for_fluxo(fluxo_id)


def task_etapa_reconfigure_statuses(fluxo_id: int) -> None:
    """Reconfigura statuses da List do Fluxo."""
    # Comentário: evita falha no cluster quando Fluxo não existe
    try:
        FlowSyncService().ensure_list_for_fluxo_from_db(fluxo_id)
    except RuntimeError as exc:
        logger.warning("FluxoAtendimento não encontrado: {}", fluxo_id)
        logger.warning("Detalhe: {}", exc)
    except Exception as exc:
        logger.error(
            "Falha ao reconfigurar statuses do fluxo {}: {}",
            fluxo_id,
            exc,
        )


def task_atendimento_ensure_task(atendimento_id: int) -> None:
    """Garante a Task para o Atendimento a partir do banco."""
    at = Atendimento.objects.filter(id=atendimento_id).first()
    if not at:
        logger.warning("Atendimento não encontrado: {}", atendimento_id)
        return
    etapa_nome = getattr(at.etapa_atual, "nome", "")
    # Comentário: trata ausência de List mapeada e falhas de API
    try:
        TicketSyncService().ensure_task(at, etapa_nome)
    except RuntimeError as exc:
        logger.warning(
            "List não encontrada para fluxo do atendimento {}",
            atendimento_id,
        )
        logger.warning("Detalhe: {}", exc)
    except Exception as exc:
        logger.error(
            "Falha ao garantir task do atendimento {}: {}",
            atendimento_id,
            exc,
        )


def task_atendimento_update_task_rich_content(atendimento_id: int) -> None:
    """Atualiza conteúdo enriquecido da Task do Atendimento."""
    at = Atendimento.objects.filter(id=atendimento_id).first()
    if not at:
        logger.warning("Atendimento não encontrado: {}", atendimento_id)
        return
    etapa_nome = getattr(at.etapa_atual, "nome", "")
    try:
        TicketSyncService().update_rich_content(at, etapa_nome)
    except Exception as exc:
        logger.warning(
            "Falha ao atualizar rich content do atendimento {}: {}",
            atendimento_id,
            exc,
        )


def task_atendimento_sync_task_members(
    atendimento_id: int, old_atendente_id: int | None
) -> None:
    """Sincroniza membros (assignees) da Task para o Atendimento."""
    at = Atendimento.objects.filter(id=atendimento_id).first()
    if not at:
        logger.warning("Atendimento não encontrado: {}", atendimento_id)
        return
    # Atualiza assignees conforme atendente vinculado
    try:
        TicketSyncService().sync_assignees(at, old_atendente_id)
    except Exception as exc:
        logger.warning(
            "Falha ao sincronizar membros do atendimento {}: {}",
            atendimento_id,
            exc,
        )
    logger.info(
        "Sincronização de membros agendada para atendimento {}", atendimento_id
    )


def task_atendente_invite(atendente_id: int) -> None:
    """Registra/invita membro localmente para ClickUp (mínimo)."""
    from smart_core_assistant_painel.app.ui.operacional.models import Atendente

    atendente = Atendente.objects.filter(id=atendente_id).first()
    if not atendente:
        logger.warning("Atendente não encontrado: {}", atendente_id)
        return
    username = getattr(atendente, "nome", f"user-{atendente_id}")
    MemberSyncService().invite_for_atendente(atendente, username)


def task_atendente_sync_member_by_email(atendente_id: int) -> None:
    """Sincroniza vínculo de membro ClickUp por e-mail do Atendente."""
    from smart_core_assistant_painel.app.ui.operacional.models import Atendente

    atendente = Atendente.objects.filter(id=atendente_id).first()
    if not atendente:
        logger.warning("Atendente não encontrado: {}", atendente_id)
        return
    try:
        MemberSyncService().find_and_register_by_email(atendente)
    except Exception as exc:
        logger.warning(
            "Falha ao sincronizar membro por e-mail para atendente {}: {}",
            atendente_id,
            exc,
        )


def task_atendimento_delete_task(atendimento_id: int) -> None:
    """Exclui permanentemente a Task relativa ao Atendimento."""
    TicketSyncService().delete_task(atendimento_id)


def task_atendente_remove_member(atendente_id: int) -> None:
    """Remove membro do ClickUp e do banco local."""
    MemberSyncService().remove_member(atendente_id)


def task_mensagem_append_comment(mensagem_id: int) -> None:
    """Adiciona comentário em Markdown na Task do Atendimento da mensagem.

    Comentário (PT-BR): preserva sequência e visual sem poluir o card,
    usando comentários do ClickUp por mensagem criada.
    """
    msg = Mensagem.objects.filter(id=mensagem_id).first()
    if not msg:
        logger.warning("Mensagem não encontrada: {}", mensagem_id)
        return
    try:
        TicketSyncService().append_message_comment(msg)
    except Exception as exc:
        logger.error(
            "Falha ao anexar comentário para mensagem {}: {}",
            mensagem_id,
            exc,
        )


def task_departamento_delete_folder(departamento_id: int) -> None:
    """Exclui permanentemente o Folder do ClickUp correspondente ao Departamento."""
    from smart_core_assistant_painel.app.ui.operacional.models import (
        Departamento,
    )
    from .services.department_provision_service import (
        DepartmentProvisionService,
    )

    departamento = Departamento.objects.filter(id=departamento_id).first()
    if not departamento:
        logger.warning("Departamento não encontrado: {}", departamento_id)
        return

    svc = DepartmentProvisionService()
    svc.delete_on_department_delete(departamento)


def enqueue_task(func_name: str, *args: Any, **kwargs: Any) -> None:
    """Enfileira uma tarefa no Django Q sem gates adicionais.

    Comentário: segue o padrão do Trello, usando apenas signals para
    disparo e enfileiramento das tarefas de sincronização.
    """
    async_task(
        f"smart_core_assistant_painel.app.clickup_sync.tasks.{func_name}",
        *args,
        **kwargs,
    )
    logger.info("Tarefa enfileirada: {}", func_name)

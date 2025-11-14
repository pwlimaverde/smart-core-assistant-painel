from typing import Any

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from loguru import logger
from django_q.tasks import async_task

from smart_core_assistant_painel.app.ui.operacional.models import (
    FluxoAtendimento,
    EtapaFluxo,
    Departamento,
    Atendente,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
)

from .services.department_provision_service import DepartmentProvisionService
from .models import ClickupStatus


@receiver(post_save, sender=FluxoAtendimento)
def fluxo_created_sync_clickup(
    sender: Any, instance: FluxoAtendimento, created: bool, **kwargs: Any
) -> None:
    """Cria/garante List ClickUp ao criar FluxoAtendimento (assíncrono)."""
    try:
        if created:
            async_task(
                (
                    "smart_core_assistant_painel.app.clickup_sync.tasks"
                    ".task_fluxo_ensure_list"
                ),
                instance.id,
            )
    except Exception as exc:
        logger.error("Falha ao garantir list ClickUp: {}", exc)


@receiver(post_save, sender=EtapaFluxo)
def etapa_created_sync_clickup(
    sender: Any, instance: EtapaFluxo, created: bool, **kwargs: Any
) -> None:
    """Reconfigura statuses da List quando nova etapa e reordena (assíncrono)."""
    try:
        # Sempre reconfigura após criação/atualização
        async_task(
            (
                "smart_core_assistant_painel.app.clickup_sync.tasks"
                ".task_etapa_reconfigure_statuses"
            ),
            instance.fluxo_id,
        )
    except Exception as exc:
        logger.warning("Falha ao reconfigurar statuses: {}", exc)


@receiver(pre_delete, sender=EtapaFluxo)
def etapa_deleted_reconfigure_clickup(
    sender: Any, instance: EtapaFluxo, **kwargs: Any
) -> None:
    """Reconfigura statuses da List ao excluir uma EtapaFluxo (assíncrono)."""
    try:
        # Comentário: remove mapeamentos locais da etapa apagada
        ClickupStatus.objects.filter(etapa_fluxo_id=instance.id).delete()

        async_task(
            (
                "smart_core_assistant_painel.app.clickup_sync.tasks"
                ".task_etapa_reconfigure_statuses"
            ),
            instance.fluxo_id,
        )
    except Exception as exc:
        logger.warning("Falha ao reconfigurar após exclusão: {}", exc)


@receiver(pre_delete, sender=FluxoAtendimento)
def fluxo_deleted_delete_clickup(
    sender: Any, instance: FluxoAtendimento, **kwargs: Any
) -> None:
    """Exclui permanentemente a List ClickUp ao excluir um FluxoAtendimento (assíncrono)."""
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.clickup_sync.tasks"
                ".task_fluxo_delete_list"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao excluir list: {}", exc)


@receiver(pre_save, sender=Atendimento)
def atendimento_capture_old_fields(
    sender: Any, instance: Atendimento, **kwargs: Any
) -> None:
    """Captura valores anteriores antes de salvar o Atendimento.

    Comentário (PT-BR): guardamos campos relevantes para decidir se
    precisamos atualizar o conteúdo rico do card. Inclui atendente,
    etapa, departamento, prioridade, assunto, canal e datas de SLA.
    """
    try:
        if getattr(instance, "pk", None):
            prev = Atendimento.objects.filter(pk=instance.pk).first()
            if prev is not None:
                instance._old_atendente_id = getattr(
                    prev, "atendente_humano_id", None
                )  # type: ignore[attr-defined]
                instance._old_etapa_id = getattr(prev, "etapa_atual_id", None)  # type: ignore[attr-defined]
                instance._old_departamento_id = getattr(prev, "departamento_id", None)  # type: ignore[attr-defined]
                instance._old_assunto = getattr(prev, "assunto", None)  # type: ignore[attr-defined]
                instance._old_prioridade = getattr(prev, "prioridade", None)  # type: ignore[attr-defined]
                instance._old_canal = getattr(prev, "canal", None)  # type: ignore[attr-defined]
                instance._old_data_inicio = getattr(prev, "data_inicio", None)  # type: ignore[attr-defined]
                instance._old_data_fim = getattr(prev, "data_fim", None)  # type: ignore[attr-defined]
                instance._old_data_primeira_resposta = getattr(prev, "data_primeira_resposta", None)  # type: ignore[attr-defined]
                instance._old_data_ultima_mensagem = getattr(prev, "data_ultima_mensagem", None)  # type: ignore[attr-defined]
                instance._old_avaliacao = getattr(prev, "avaliacao", None)  # type: ignore[attr-defined]
                instance._old_fluxo_id = getattr(prev, "fluxo_atendimento_id", None)  # type: ignore[attr-defined]
                instance._old_contexto_conversa = getattr(prev, "contexto_conversa", None)  # type: ignore[attr-defined]
            else:
                instance._old_atendente_id = None  # type: ignore[attr-defined]
                instance._old_etapa_id = None  # type: ignore[attr-defined]
                instance._old_departamento_id = None  # type: ignore[attr-defined]
                instance._old_assunto = None  # type: ignore[attr-defined]
                instance._old_prioridade = None  # type: ignore[attr-defined]
                instance._old_canal = None  # type: ignore[attr-defined]
                instance._old_data_inicio = None  # type: ignore[attr-defined]
                instance._old_data_fim = None  # type: ignore[attr-defined]
                instance._old_data_primeira_resposta = None  # type: ignore[attr-defined]
                instance._old_data_ultima_mensagem = None  # type: ignore[attr-defined]
                instance._old_avaliacao = None  # type: ignore[attr-defined]
                instance._old_fluxo_id = None  # type: ignore[attr-defined]
                instance._old_contexto_conversa = None  # type: ignore[attr-defined]
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
            async_task(
                (
                    "smart_core_assistant_painel.app.clickup_sync.tasks"
                    ".task_atendimento_ensure_task"
                ),
                instance.id,
            )
            return

        # Atualiza membros e conteúdo rico do card
        old_id = getattr(instance, "_old_atendente_id", None)
        async_task(
            (
                "smart_core_assistant_painel.app.clickup_sync.tasks"
                ".task_atendimento_sync_task_members"
            ),
            instance.id,
            old_id,
        )

        # Atualiza rich content se qualquer campo relevante mudou
        old_etapa_id = getattr(instance, "_old_etapa_id", None)
        old_departamento_id = getattr(instance, "_old_departamento_id", None)
        old_assunto = getattr(instance, "_old_assunto", None)
        old_prioridade = getattr(instance, "_old_prioridade", None)
        old_canal = getattr(instance, "_old_canal", None)
        old_data_inicio = getattr(instance, "_old_data_inicio", None)
        old_data_fim = getattr(instance, "_old_data_fim", None)
        old_data_primeira_resposta = getattr(
            instance, "_old_data_primeira_resposta", None
        )
        old_data_ultima_mensagem = getattr(
            instance, "_old_data_ultima_mensagem", None
        )
        old_avaliacao = getattr(instance, "_old_avaliacao", None)
        old_fluxo_id = getattr(instance, "_old_fluxo_id", None)
        old_contexto_conversa = getattr(
            instance, "_old_contexto_conversa", None
        )

        changed = (
            old_etapa_id != getattr(instance, "etapa_atual_id", None)
            or old_departamento_id
            != getattr(instance, "departamento_id", None)
            or old_assunto != getattr(instance, "assunto", None)
            or old_prioridade != getattr(instance, "prioridade", None)
            or old_canal != getattr(instance, "canal", None)
            or old_data_inicio != getattr(instance, "data_inicio", None)
            or old_data_fim != getattr(instance, "data_fim", None)
            or old_data_primeira_resposta
            != getattr(instance, "data_primeira_resposta", None)
            or old_data_ultima_mensagem
            != getattr(instance, "data_ultima_mensagem", None)
            or old_avaliacao != getattr(instance, "avaliacao", None)
            or old_fluxo_id
            != getattr(instance, "fluxo_atendimento_id", None)
            or old_contexto_conversa
            != getattr(instance, "contexto_conversa", None)
        )

        if changed:
            async_task(
                (
                    "smart_core_assistant_painel.app.clickup_sync.tasks"
                    ".task_atendimento_update_task_rich_content"
                ),
                instance.id,
            )
    except Exception as exc:
        logger.warning("Falha ao sincronizar Task ClickUp: {}", exc)


@receiver(post_save, sender=Atendente)
def atendente_created_invite_clickup(
    sender: Any, instance: Atendente, created: bool, **kwargs: Any
) -> None:
    """Sincroniza membro ClickUp por e-mail ao criar Atendente (assíncrono)."""
    if not created:
        return
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.clickup_sync.tasks"
                ".task_atendente_sync_member_by_email"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao sincronizar atendente por e-mail: {}", exc)


@receiver(pre_delete, sender=Atendimento)
def atendimento_deleted_delete_task_clickup(
    sender: Any, instance: Atendimento, **kwargs: Any
) -> None:
    """Exclui permanentemente a Task ClickUp ao excluir um Atendimento (assíncrono)."""
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.clickup_sync.tasks"
                ".task_atendimento_delete_task"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao excluir task: {}", exc)


@receiver(pre_delete, sender=Departamento)
def departamento_deleted_delete_folder_clickup(
    sender: Any, instance: Departamento, **kwargs: Any
) -> None:
    """Exclui permanentemente o Folder ClickUp ao excluir um Departamento (assíncrono)."""
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.clickup_sync.tasks"
                ".task_departamento_delete_folder"
            ),
            instance.id,
        )
    except Exception as exc:
        logger.warning("Falha ao excluir folder: {}", exc)


@receiver(pre_delete, sender=Atendente)
def atendente_deleted_remove_member_clickup(
    sender: Any, instance: Atendente, **kwargs: Any
) -> None:
    """Remove membro do ClickUp ao excluir Atendente (assíncrono)."""
    try:
        async_task(
            (
                "smart_core_assistant_painel.app.clickup_sync.tasks"
                ".task_atendente_remove_member"
            ),
            instance.id,
        )
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
        logger.info(
            "Provisionamento ClickUp concluído para Departamento {}",
            instance.id,
        )
    except Exception as exc:
        logger.error(
            "Falha no provisionamento ClickUp para Departamento {}: {}",
            instance.id,
            str(exc),
        )
    return None


@receiver(post_save, sender=Mensagem)
def mensagem_post_save_append_comment(
    sender: Any, instance: Mensagem, created: bool, **kwargs: Any
) -> None:
    """Cria comentário em Markdown na Task ao salvar nova Mensagem.

    Comentário (PT-BR): apenas mensagens novas disparam o comentário; o
    enfileiramento é assíncrono para não bloquear transações.
    """
    try:
        if created:
            async_task(
                (
                    "smart_core_assistant_painel.app.clickup_sync.tasks"
                    ".task_mensagem_append_comment"
                ),
                instance.id,
            )
            # Comentário: também atualiza conteúdo rico para refletir
            # "Last Message At" e KPIs derivados no card.
            async_task(
                (
                    "smart_core_assistant_painel.app.clickup_sync.tasks"
                    ".task_atendimento_update_task_rich_content"
                ),
                instance.atendimento_id,
            )
    except Exception as exc:
        logger.warning(
            "Falha ao enfileirar comentário para mensagem {}: {}",
            instance.id,
            exc,
        )

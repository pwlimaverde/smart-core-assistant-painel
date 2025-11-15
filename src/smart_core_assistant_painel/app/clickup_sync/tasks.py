import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from decouple import AutoConfig
from django_q.tasks import async_task
from loguru import logger

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
)

from .models import ClickupMember, ClickupTask
from .services import FlowSyncService, MemberSyncService, TicketSyncService


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
    """Sincroniza assignees com a lógica do script (PUT /task)."""
    at = Atendimento.objects.filter(id=atendimento_id).first()
    if not at:
        logger.warning("Atendimento não encontrado: {}", atendimento_id)
        return

    task = ClickupTask.objects.filter(atendimento_id=atendimento_id).first()
    if not task:
        logger.warning("Task não encontrada para atendimento {}", atendimento_id)
        return

    def _get_env_token() -> str:
        token: str = ""
        try:
            project_root: Path = Path(__file__).resolve().parents[2]
            config = AutoConfig(search_path=str(project_root))
            token = config("CLICKUP_API_TOKEN", default="")
            if not token:
                token = config("CLICKUP_OAUTH_ACCESS_TOKEN", default="")
            if not token:
                token = config("CLICKUP_PERSONAL_TOKEN", default="")
        except Exception:
            token = os.getenv("CLICKUP_API_TOKEN", "")
            if not token:
                token = os.getenv("CLICKUP_OAUTH_ACCESS_TOKEN", "")
            if not token:
                token = os.getenv("CLICKUP_PERSONAL_TOKEN", "")
        return token

    def _normalize_auth(token: str) -> str:
        if not token:
            return ""
        return token if token.lower().startswith("bearer ") else f"Bearer {token}"

    API_BASE: str = "https://api.clickup.com/api/v2"
    token: str = _get_env_token()
    if not token:
        logger.warning("Token ClickUp não configurado")
        return
    headers: Dict[str, str] = {
        "Authorization": _normalize_auth(token),
        "Content-Type": "application/json",
    }

    new_id: Optional[int] = getattr(at, "atendente_humano_id", None)
    mode: str
    if old_atendente_id is not None and new_id is not None:
        mode = "replace"
    elif new_id is not None:
        mode = "add"
    else:
        mode = "remove"

    target_ids: List[str] = []
    if mode in {"replace", "add"} and new_id is not None:
        member = ClickupMember.objects.filter(atendente_id=new_id).first()
        if not member:
            logger.warning(
                "ClickupMember ausente para atendente {} na task {}",
                new_id,
                task.external_id,
            )
            return
        target_ids = [str(member.external_id)]
    elif mode == "remove" and old_atendente_id is not None:
        member = ClickupMember.objects.filter(atendente_id=old_atendente_id).first()
        if not member:
            logger.warning(
                "ClickupMember ausente para atendente {} na task {}",
                old_atendente_id,
                task.external_id,
            )
            return
        target_ids = [str(member.external_id)]

    try:
        if mode == "add":
            body: Dict[str, Any] = {"assignees": {"add": target_ids}}
        elif mode == "remove":
            body = {"assignees": {"rem": target_ids}}
        else:
            body = {"assignees": target_ids}
        resp = requests.put(
            f"{API_BASE}/task/{task.external_id}",
            json=body,
            headers=headers,
            timeout=30,
        )
        ok: bool = 200 <= resp.status_code < 300
        if not ok:
            logger.warning(
                "Falha no update de assignees ({}): {}",
                resp.status_code,
                resp.text,
            )
        # Verificação pós-update
        check = requests.get(
            f"{API_BASE}/task/{task.external_id}", headers=headers, timeout=30
        )
        applied: List[str] = []
        if 200 <= check.status_code < 300:
            data: Dict[str, Any] = {}
            try:
                data = check.json()
            except Exception:
                data = {}
            for a in data.get("assignees", []) or []:
                if isinstance(a, dict):
                    applied.append(str(a.get("id", "")))
        logger.info(
            "Assignees sync modo={} alvo={} aplicado={}", mode, target_ids, applied
        )
    except Exception as exc:
        logger.warning(
            "Falha ao sincronizar assignees para atendimento {}: {}",
            atendimento_id,
            exc,
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

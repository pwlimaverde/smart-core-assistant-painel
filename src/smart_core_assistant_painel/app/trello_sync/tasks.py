"""Tarefas do Trello executadas via Celery.

Estas funções encapsulam operações de sincronização com o Trello para
serem executadas por workers do Celery, evitando chamadas diretas
no contexto dos sinais.

As tarefas são agendadas pelos sinais em
``smart_core_assistant_painel.app.trello_sync.signals``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, cast

from celery import shared_task
from decouple import config
from django.db import models, router, transaction
from loguru import logger

from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloBoard,
    TrelloList,
)
from smart_core_assistant_painel.app.trello_sync.services import (
    FlowSyncService,
    MemberSyncService,
    TicketSyncService,
)
from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
)
from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
    EtapaFluxo,
    FluxoAtendimento,
    TipoEtapa,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB
from smart_core_assistant_painel.app.tenants.celery import TenantTask


@shared_task(base=TenantTask)
def task_fluxo_ensure_board(tenant_slug: str, fluxo_id: int) -> None:
    """Garante o board Trello para um fluxo.

    Args:
        fluxo_id: ID do ``FluxoAtendimento``.
    """
    try:
        fluxo = FluxoAtendimento.objects.get(id=fluxo_id)
        board = FlowSyncService().ensure_board_for_fluxo(fluxo)

    except FluxoAtendimento.DoesNotExist:
        logger.warning("Fluxo não encontrado para criar board: {}", fluxo_id)
    except Exception as exc:
        logger.error("Falha ao garantir board Trello: {}", exc)


@shared_task(base=TenantTask)
def task_fluxo_archive_board(tenant_slug: str, board_external_id: str) -> None:
    """Arquiva o board Trello ao excluir um fluxo.

    Args:
        board_external_id: ID externo do board Trello.
    """
    try:
        client = SERVICEHUB.unified_data_service
        # Assume que archive_item funciona para boards (closed=True)
        client.archive_item(board_external_id)
        logger.info(
            "Board Trello arquivado com sucesso: {}", board_external_id
        )
    except Exception as exc:
        logger.warning(
            "Falha ao arquivar board Trello {}: {}", board_external_id, exc
        )


@shared_task(base=TenantTask)
def task_etapa_ensure_list(tenant_slug: str, etapa_id: int) -> None:
    """Garante a lista Trello para uma etapa de fluxo.

    Args:
        etapa_id: ID da ``EtapaFluxo``.
    """
    try:
        etapa = EtapaFluxo.objects.get(id=etapa_id)
        # Fix: Garante que o board do fluxo existe antes de tentar criar a lista
        # Isso evita o erro "Board do fluxo ainda não criado para a etapa"
        if etapa.fluxo:
            FlowSyncService().ensure_board_for_fluxo(etapa.fluxo)

        FlowSyncService().ensure_list_for_etapa(etapa)
    except EtapaFluxo.DoesNotExist:
        logger.warning("Etapa não encontrada para criar lista: {}", etapa_id)
    except Exception as exc:
        logger.error("Falha ao garantir lista Trello: {}", exc)


@shared_task(base=TenantTask)
def task_reorder_lists_for_fluxo(tenant_slug: str, fluxo_id: int) -> None:
    """Reordena listas do board de um fluxo.

    Args:
        fluxo_id: ID do ``FluxoAtendimento``.
    """
    try:
        fluxo = FluxoAtendimento.objects.get(id=fluxo_id)
        FlowSyncService().reorder_lists_for_fluxo(fluxo)
    except FluxoAtendimento.DoesNotExist:
        logger.warning(
            "Fluxo não encontrado para reordenar listas: {}", fluxo_id
        )
    except Exception as exc:
        logger.warning("Falha ao reordenar listas do fluxo: {}", exc)


@shared_task(base=TenantTask)
def task_etapa_archive_list(tenant_slug: str, etapa_id: int) -> None:
    """Arquiva a lista Trello quando a etapa é excluída.

    Nota: como a etapa já foi excluída (post_delete) ou está sendo (pre_delete),
    precisamos ter cuidado ao buscar o ID externo. Idealmente, o ID externo
    deveria ser passado como argumento, ou buscamos antes.
    Entretanto, o signal passa a instância.
    No `pre_delete`, a instância ainda existe no banco.
    """
    # TODO: Implementar arquivamento real via Trello API
    # Atualmente o TrelloAdapter suporta `archive_item`? Sim.
    # Precisamos do ID externo da lista.
    pass


@shared_task(base=TenantTask)
def task_atendimento_ensure_card(
    tenant_slug: str, atendimento_id: int
) -> None:
    """Garante o card Trello para um atendimento.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        TicketSyncService().ensure_card_for_atendimento(atendimento)
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para criar card: {}", atendimento_id
        )
    except Exception as exc:
        logger.error("Falha ao garantir card Trello: {}", exc)


@shared_task(base=TenantTask)
def task_atendente_invite(tenant_slug: str, atendente_id: int) -> None:
    """Envia convite do Trello para um atendente.

    Args:
        atendente_id: ID do ``Atendente``.
    """
    try:
        atendente = Atendente.objects.get(id=atendente_id)
        MemberSyncService().ensure_member_for_atendente(atendente)
    except Atendente.DoesNotExist:
        logger.warning(
            "Atendente não encontrado para convidar: {}", atendente_id
        )
    except Exception as exc:
        logger.error("Falha ao convidar atendente: {}", exc)


@shared_task(base=TenantTask)
def task_atendente_remove_member(tenant_slug: str, atendente_id: int) -> None:
    """Remove membro do Trello ao excluir atendente.

    Args:
        atendente_id: ID do ``Atendente``.
    """
    # TODO: Implementar remoção se API suportar
    pass


@shared_task(base=TenantTask)
def task_atendimento_sync_card_members(
    tenant_slug: str,
    atendimento_id: int,
    old_atendente_id: Optional[int] = None,
) -> None:
    """Sincroniza membros do card Trello conforme atendente responsável.

    Args:
        atendimento_id: ID do ``Atendimento``.
        old_atendente_id: ID do atendente anterior (opcional).
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        service = TicketSyncService()
        service.sync_card_members(atendimento, old_atendente_id)
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para sync membros: {}", atendimento_id
        )
    except Exception as exc:
        logger.error("Falha ao sincronizar membros do card: {}", exc)


@shared_task(base=TenantTask)
def task_atendimento_move_to_etapa_list(
    tenant_slug: str, atendimento_id: int
) -> None:
    """Move o card Trello para a lista da etapa atual do atendimento.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        service = TicketSyncService()
        service.move_card_to_etapa(atendimento)
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para mover card: {}", atendimento_id
        )
    except Exception as exc:
        logger.error("Falha ao mover card Trello: {}", exc)


@shared_task(base=TenantTask)
def task_atendimento_update_card_rich_content(
    tenant_slug: str, atendimento_id: int
) -> None:
    """Atualiza conteúdo rico do card (descrição/checklist) com histórico.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        service = TicketSyncService()
        service.update_card_rich_content(atendimento)
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para update rico: {}", atendimento_id
        )
    except Exception as exc:
        logger.error("Falha ao atualizar card rico: {}", exc)


@shared_task(base=TenantTask)
def task_trello_archive_card_by_external_id(
    tenant_slug: str, external_id: str
) -> None:
    """Arquiva um card Trello diretamente pelo ID externo.

    Útil para chamadas `pre_delete` onde o objeto Django já vai sumir.
    """
    try:
        client = SERVICEHUB.unified_data_service
        # Usa método genérico de archive
        # Supondo que archive_item suporte card ID
        client.archive_item(external_id)
    except Exception as exc:
        logger.warning(
            "Falha ao arquivar card Trello {}: {}", external_id, exc
        )


@shared_task(base=TenantTask, queue="webhooks")
def task_process_trello_card_move(
    tenant_slug: str, card_id: str, list_after_id: str, member_creator_id: str
) -> None:
    """Processa movimentação de card vinda do Webhook Trello.

    Args:
        card_id: ID externo do card.
        list_after_id: ID externo da lista de destino.
        member_creator_id: ID externo do usuário que moveu.
    """
    try:
        service = TicketSyncService()
        service.process_webhook_card_move(
            card_id, list_after_id, member_creator_id
        )
        # Opcional: forçar atualização visual (labels, due date) se necessário
        # service.ensure_card_visuals(...)
        # Exemplo: se moveu para "Resolvido", aplicar estilo de concluído?
        # Isso já deve ser tratado no `process_webhook_card_move` ao atualizar o atendimento.

        # Verifica se precisa aplicar estilos visuais baseados na nova etapa
        # Recupera atendimento atualizado
        from smart_core_assistant_painel.app.trello_sync.models import (
            TrelloCard,
            TrelloList,
        )

        try:
            trello_card = TrelloCard.objects.get(external_id=card_id)
            # atendimento = trello_card.atendimento  # Unused
            lista_dest = TrelloList.objects.filter(
                external_id=list_after_id
            ).first()

            if lista_dest and lista_dest.etapa:
                etapa = lista_dest.etapa
                # Se for etapa de finalização, marcar check no card?
                if etapa.tipo_etapa == TipoEtapa.FINALIZACAO:
                    service.client.update_item(
                        data_source_id=lista_dest.external_id,
                        item_id=card_id,
                        payload={"dueComplete": True},
                    )
        except Exception as exc:
            logger.warning(
                "Falha ao aplicar estilos visuais no Trello: {}", exc
            )

    except Exception as exc:
        logger.error("Falha ao processar movimento de card Trello: {}", exc)


@shared_task(base=TenantTask, queue="webhooks")
def task_process_trello_list_create(
    tenant_slug: str, list_id: str, list_name: str, board_id: str
) -> None:
    """Processa criação de lista no Trello (webhook)."""
    try:
        # 1. Verifica se a lista já existe (Idempotência)
        if TrelloList.objects.filter(external_id=list_id).exists():
            logger.info("Lista Trello {} já existe no sistema.", list_id)
            return

        # 2. Busca o Board
        try:
            trello_board = TrelloBoard.objects.get(external_id=board_id)
        except TrelloBoard.DoesNotExist:
            logger.warning("Board Trello {} não encontrado.", board_id)
            return

        fluxo = trello_board.fluxo

        # 3. Cria Etapa e Lista atomicamente
        with transaction.atomic(using=router.db_for_write(EtapaFluxo)):
            # Lock no fluxo para garantir ordem sequencial correta
            _ = FluxoAtendimento.objects.select_for_update().get(id=fluxo.id)

            # Calcula próxima ordem
            last_order = (
                fluxo.etapas.aggregate(models.Max("ordem"))["ordem__max"] or 0
            )
            new_order = last_order + 1

            # Cria Etapa
            etapa = EtapaFluxo(
                fluxo=fluxo,
                nome=list_name,
                ordem=new_order,
                tipo_etapa=TipoEtapa.TRABALHO,
            )
            # Flag para evitar loop (task_etapa_ensure_list)
            etapa._syncing_from_trello = True
            etapa.save()

            # Cria TrelloList vinculada
            TrelloList.objects.create(
                etapa=etapa,
                board=trello_board,
                external_id=list_id,
                name=list_name,
                position=float(new_order),
            )

        logger.info(
            "Sincronizada nova lista Trello: {} -> Etapa #{}",
            list_name,
            etapa.id,
        )

    except Exception as exc:
        logger.error("Falha ao processar criação de lista Trello: {}", exc)


@shared_task(base=TenantTask, queue="webhooks")
def task_process_trello_list_update(
    tenant_slug: str, list_id: str, list_name: str | None, closed: bool | None
) -> None:
    """Processa atualização de lista no Trello (webhook)."""
    try:
        # 1. Busca a Lista
        try:
            trello_list = TrelloList.objects.select_related("etapa").get(
                external_id=list_id
            )
        except TrelloList.DoesNotExist:
            logger.warning(
                "Lista Trello {} não encontrada para update.", list_id
            )
            return

        etapa = trello_list.etapa

        # 2. Processa Arquivamento/Exclusão
        if closed is True:
            logger.info("Lista Trello {} arquivada. Removendo Etapa.", list_id)
            # Flag para evitar loop (task_etapa_archive_list)
            etapa._syncing_from_trello = True
            etapa.delete()
            return

        # 3. Processa Renomeação
        if list_name and list_name != trello_list.name:
            logger.info(
                "Lista Trello {} renomeada: {} -> {}",
                list_id,
                trello_list.name,
                list_name,
            )
            # Atualiza TrelloList
            trello_list.name = list_name
            trello_list.save(update_fields=["name"])

            # Atualiza EtapaFluxo
            etapa.nome = list_name
            # Flag para evitar loop? (não há loop de rename implementado, mas safe to add logic if needed)
            # Atualmente não há signal de rename->trello, então ok.
            etapa.save(update_fields=["nome"])

    except Exception as exc:
        logger.error("Falha ao processar atualização de lista Trello: {}", exc)

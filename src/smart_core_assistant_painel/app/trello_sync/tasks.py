"""Tarefas do Trello executadas via cluster (Django Q).

Estas funções encapsulam operações de sincronização com o Trello para
serem executadas por workers do cluster, evitando chamadas diretas
no contexto dos sinais.

As tarefas são agendadas pelos sinais em
``smart_core_assistant_painel.app.trello_sync.signals``.
"""

from __future__ import annotations

from typing import Any, cast
from typing import Optional

from loguru import logger

from smart_core_assistant_painel.app.trello_sync.services import (
    FlowSyncService,
    MemberSyncService,
    TicketSyncService,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB
from smart_core_assistant_painel.app.ui.operacional.models import (
    EtapaFluxo,
    FluxoAtendimento,
    Atendente,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
)
from smart_core_assistant_painel.app.trello_sync.models import TrelloBoard


def task_fluxo_ensure_board(fluxo_id: int) -> None:
    """Garante o board Trello para um fluxo.

    Args:
        fluxo_id: ID do ``FluxoAtendimento``.
    """
    try:
        fluxo = FluxoAtendimento.objects.get(id=fluxo_id)
        FlowSyncService().ensure_board_for_fluxo(fluxo)
    except FluxoAtendimento.DoesNotExist:
        logger.warning("Fluxo não encontrado para criar board: {}", fluxo_id)
    except Exception as exc:
        logger.error("Falha ao garantir board Trello: {}", exc)


def task_etapa_ensure_list(etapa_id: int) -> None:
    """Garante a lista Trello para uma etapa de fluxo.

    Args:
        etapa_id: ID da ``EtapaFluxo``.
    """
    try:
        etapa = EtapaFluxo.objects.get(id=etapa_id)
        FlowSyncService().ensure_list_for_etapa(etapa)
    except EtapaFluxo.DoesNotExist:
        logger.warning("Etapa não encontrada para criar lista: {}", etapa_id)
    except Exception as exc:
        logger.error("Falha ao garantir lista Trello: {}", exc)


def task_reorder_lists_for_fluxo(fluxo_id: int) -> None:
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


def task_etapa_archive_list(etapa_id: int) -> None:
    """Arquiva a lista Trello relativa a uma etapa.

    Args:
        etapa_id: ID da ``EtapaFluxo``.
    """
    try:
        etapa = EtapaFluxo.objects.get(id=etapa_id)
        FlowSyncService().archive_list_for_etapa(etapa)
    except EtapaFluxo.DoesNotExist:
        logger.warning(
            "Etapa não encontrada para arquivar lista: {}", etapa_id
        )
    except Exception as exc:
        logger.warning("Falha ao arquivar lista Trello: {}", exc)


def task_fluxo_archive_board(fluxo_id: int) -> None:
    """Arquiva o board Trello relativo a um fluxo.

    Args:
        fluxo_id: ID do ``FluxoAtendimento``.
    """
    try:
        fluxo = FluxoAtendimento.objects.get(id=fluxo_id)
        FlowSyncService().archive_board_for_fluxo(fluxo)
    except FluxoAtendimento.DoesNotExist:
        logger.warning(
            "Fluxo não encontrado para arquivar board: {}", fluxo_id
        )
    except Exception as exc:
        logger.warning("Falha ao arquivar board Trello: {}", exc)


def task_atendimento_ensure_card(atendimento_id: int) -> None:
    """Garante o card Trello para um atendimento.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        service = TicketSyncService()
        card = service.ensure_card_for_atendimento(atendimento)
        # Comentário: após criar o card, enriquecer com descrição/membros/custom fields
        try:
            service.update_card_rich_content(card, atendimento)
        except Exception as exc:
            logger.warning("Falha ao enriquecer card após criação: {}", exc)
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para garantir card: {}",
            atendimento_id,
        )
    except Exception as exc:
        logger.warning("Falha ao garantir card Trello: {}", exc)


def task_atendente_invite(atendente_id: int) -> None:
    """Convida um atendente para o board Trello do fluxo associado.

    Args:
        atendente_id: ID do ``Atendente``.
    """
    try:
        atendente = Atendente.objects.get(id=atendente_id)
        MemberSyncService().invite_for_atendente(atendente)
    except Atendente.DoesNotExist:
        logger.warning(
            "Atendente não encontrado para convite Trello: {}",
            atendente_id,
        )
    except Exception as exc:
        logger.warning("Falha ao convidar atendente para Trello: {}", exc)


def task_atendente_remove_member(atendente_id: int) -> None:
    """Remove atendente do board Trello (se membro resolvido).

    Args:
        atendente_id: ID do ``Atendente``.
    """
    try:
        atendente = Atendente.objects.get(id=atendente_id)
        fluxo = getattr(atendente, "fluxo", None)
        if fluxo is None:
            return

        board = TrelloBoard.objects.filter(fluxo=fluxo).first()
        if board is None:
            return

        ms = MemberSyncService()
        member_id = ms.resolve_member_external_id(atendente)

        client = SERVICEHUB.unified_data_service
        try:
            from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
                TrelloUnifiedDataService,
            )

            trello_client = cast(TrelloUnifiedDataService, client)
        except Exception:
            trello_client = client  # type: ignore[assignment]

        if member_id:
            try:
                trello_client.remove_member_from_board(
                    board_id=board.external_id, member_id=member_id
                )
            except Exception as exc:
                logger.warning(
                    "Falha ao remover membro do board Trello: {}",
                    exc,
                )
        else:
            logger.warning(
                "Membro Trello não resolvido para atendente ao remover; "
                "ignorado."
            )
    except Atendente.DoesNotExist:
        logger.warning(
            "Atendente não encontrado para remoção de membro: {}",
            atendente_id,
        )
    except Exception as exc:
        logger.warning("Remoção de membro no Trello falhou: {}", exc)


def task_atendimento_assign_member_and_update(atendimento_id: int) -> None:
    """Atribui membro ao card e atualiza descrição com contexto.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        service = TicketSyncService()
        try:
            card = getattr(atendimento, "trello_card", None)
            if card is None:
                card = service.ensure_card_for_atendimento(atendimento)
        except Exception:
            card = getattr(atendimento, "trello_card", None)

        atendente = getattr(atendimento, "atendente_humano", None)
        if not card or not atendente:
            return

        ms = MemberSyncService()
        member_id = ms.resolve_member_external_id(atendente)

        client = SERVICEHUB.unified_data_service
        try:
            from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
                TrelloUnifiedDataService,
            )

            trello_client = cast(TrelloUnifiedDataService, client)
        except Exception:
            trello_client = client  # type: ignore[assignment]

        if member_id:
            # Comentário: evita erro 400 se o membro já estiver no card
            try:
                card_data = trello_client.get_item(
                    data_source_id=card.list_sync.external_id,
                    item_id=card.external_id,
                )
                existing_ids: list[str] = []
                if isinstance(card_data, dict):
                    existing_ids = [
                        str(mid) for mid in card_data.get("idMembers", [])
                    ]
                if member_id in existing_ids:
                    add_needed: bool = False
                else:
                    add_needed = True
            except Exception:
                add_needed = True

            if add_needed:
                try:
                    trello_client.add_member_to_card(
                        card.external_id, member_id
                    )
                except Exception as exc:
                    logger.warning(
                        "Falha ao adicionar membro ao card: {}",
                        exc,
                    )
        # Comentário: Atualiza conteúdo rico (descrição, membros e custom fields)
        try:
            service.update_card_rich_content(card, atendimento)
        except Exception as exc:
            logger.warning("Falha ao atualizar conteúdo rico do card: {}", exc)
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para atribuir membro/atualizar: {}",
            atendimento_id,
        )
    except Exception as exc:
        logger.warning(
            "Atualização de membro/descrição no Trello falhou: {}",
            exc,
        )


def task_atendimento_sync_card_members(
    atendimento_id: int, old_atendente_id: Optional[int] = None
) -> None:
    """Sincroniza membros do card ao atualizar o Atendimento.

    - Remove o atendente anterior do card, se existir.
    - Adiciona o novo atendente ao card, se definido.
    - Atualiza a descrição e custom fields do card.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        service = TicketSyncService()

        try:
            card = getattr(atendimento, "trello_card", None)
            if card is None:
                card = service.ensure_card_for_atendimento(atendimento)
        except Exception:
            card = getattr(atendimento, "trello_card", None)

        if not card:
            return

        client = SERVICEHUB.unified_data_service
        try:
            from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
                TrelloUnifiedDataService,
            )

            trello_client = cast(TrelloUnifiedDataService, client)
        except Exception:
            trello_client = client  # type: ignore[assignment]

        ms = MemberSyncService()

        # Remove membro anterior, se estiver presente e diferente do novo
        try:
            card_data = trello_client.get_item(
                data_source_id=card.list_sync.external_id,
                item_id=card.external_id,
            )
            existing_ids: list[str] = []
            if isinstance(card_data, dict):
                existing_ids = [
                    str(mid) for mid in card_data.get("idMembers", [])
                ]
        except Exception:
            existing_ids = []

        new_atendente = getattr(atendimento, "atendente_humano", None)
        new_member_id: Optional[str] = None
        if new_atendente is not None:
            try:
                new_member_id = ms.resolve_member_external_id(new_atendente)
            except Exception:
                new_member_id = None

        old_member_id: Optional[str] = None
        if old_atendente_id is not None:
            try:
                from smart_core_assistant_painel.app.ui.operacional.models import (
                    Atendente,
                )
                old_at = Atendente.objects.filter(id=old_atendente_id).first()
                if old_at is not None:
                    old_member_id = ms.resolve_member_external_id(old_at)
            except Exception:
                old_member_id = None

        # Remoção segura do membro anterior
        if old_member_id and old_member_id != new_member_id:
            try:
                if old_member_id in existing_ids:
                    trello_client.remove_member_from_card(
                        card.external_id, old_member_id
                    )
            except Exception as exc:
                logger.warning(
                    "Falha ao remover membro do card: {}",
                    exc,
                )

        # Adição segura do novo membro
        if new_member_id:
            try:
                if new_member_id not in existing_ids:
                    trello_client.add_member_to_card(
                        card.external_id, new_member_id
                    )
            except Exception as exc:
                logger.warning(
                    "Falha ao adicionar membro ao card: {}",
                    exc,
                )

        # Atualiza conteúdo rico do card
        try:
            service.update_card_rich_content(card, atendimento)
        except Exception as exc:
            logger.warning(
                "Falha ao atualizar conteúdo rico do card: {}",
                exc,
            )
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para sync de membros: {}",
            atendimento_id,
        )
    except Exception as exc:
        logger.warning("Sincronização de membros do card falhou: {}", exc)

def task_atendimento_update_card_rich_content(atendimento_id: int) -> None:
    """Atualiza descrição e campos do card após nova mensagem.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        service = TicketSyncService()

        # Comentário: garante que existe um card para este atendimento.
        try:
            card = getattr(atendimento, "trello_card", None)
            if card is None:
                card = service.ensure_card_for_atendimento(atendimento)
        except Exception:
            card = getattr(atendimento, "trello_card", None)

        if not card:
            return

        # Comentário: atualiza conteúdo rico (descrição e custom fields).
        try:
            service.update_card_rich_content(card, atendimento)
        except Exception as exc:
            logger.warning(
                "Falha ao atualizar conteúdo rico do card: {}",
                exc,
            )
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para atualizar conteúdo: {}",
            atendimento_id,
        )
    except Exception as exc:
        logger.warning(
            "Atualização de conteúdo do card Trello falhou: {}",
            exc,
        )


def task_atendimento_archive_card(atendimento_id: int) -> None:
    """Arquiva o card Trello quando o atendimento é resolvido.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        card = getattr(atendimento, "trello_card", None)
        if card is None:
            logger.warning(
                "Atendimento sem card Trello para arquivar: {}",
                atendimento_id,
            )
            return

        client = SERVICEHUB.unified_data_service
        try:
            from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
                TrelloUnifiedDataService,
            )

            trello_client = cast(TrelloUnifiedDataService, client)
        except Exception:
            trello_client = client  # type: ignore[assignment]

        try:
            trello_client.archive_item(card.external_id)
        except Exception as exc:
            logger.warning("Falha ao arquivar card Trello: {}", exc)
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para arquivar card: {}",
            atendimento_id,
        )
    except Exception as exc:
        logger.warning("Arquivamento de card Trello falhou: {}", exc)


def task_trello_archive_card_by_external_id(card_external_id: str) -> None:
    """Arquiva um card no Trello usando apenas o ``external_id``.

    Comentário: pensado para eventos de deleção de ``Atendimento`` onde
    o registro pode não estar mais disponível. Evita dependência do
    banco de dados e atua diretamente via adapter Trello.

    Args:
        card_external_id: ID externo do card no Trello.
    """
    try:
        client = SERVICEHUB.unified_data_service
        try:
            from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
                TrelloUnifiedDataService,
            )

            trello_client = cast(TrelloUnifiedDataService, client)
        except Exception:
            trello_client = client  # type: ignore[assignment]

        try:
            trello_client.archive_item(card_external_id)
        except Exception as exc:
            logger.warning("Falha ao arquivar card Trello por id: {}", exc)
    except Exception as exc:
        logger.warning("Arquivamento direto de card falhou: {}", exc)


def task_atendimento_move_to_etapa_list(atendimento_id: int) -> None:
    """Move o card Trello para a lista da etapa atual do atendimento.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)

        # Comentário: garante que existe um card para este atendimento.
        service = TicketSyncService()
        try:
            card = getattr(atendimento, "trello_card", None)
            if card is None:
                card = service.ensure_card_for_atendimento(atendimento)
        except Exception:
            card = getattr(atendimento, "trello_card", None)

        etapa = getattr(atendimento, "etapa_atual", None)
        if not card or not etapa:
            return

        # Comentário: garante a lista destino da etapa e move o card.
        lista_dest = FlowSyncService().ensure_list_for_etapa(etapa)

        try:
            # Se já estiver na lista destino, não faz nada.
            current_list_id = getattr(card.list_sync, "external_id", None)
            if current_list_id == lista_dest.external_id:
                return

            # Move card no Trello via atualização de `idList`.
            service.client.update_item(
                data_source_id=lista_dest.external_id,
                item_id=card.external_id,
                payload={"idList": lista_dest.external_id},
            )
        except Exception as exc:
            logger.warning("Falha ao mover card de lista no Trello: {}", exc)
            return

        # Atualiza o vínculo local do card com a lista destino.
        try:
            card.list_sync = lista_dest
            card.save(update_fields=["list_sync"])
        except Exception as exc:
            logger.warning(
                "Falha ao atualizar vínculo de lista do card: {}", exc
            )

        # Comentário: opcionalmente atualiza descrição/custom fields após mover.
        try:
            service.update_card_rich_content(card, atendimento)
        except Exception:
            # Não bloquear em caso de falha de enriquecimento.
            pass
    except Atendimento.DoesNotExist:
        logger.warning(
            "Atendimento não encontrado para mover card: {}",
            atendimento_id,
        )
    except Exception as exc:
        logger.warning("Movimento de card Trello falhou: {}", exc)
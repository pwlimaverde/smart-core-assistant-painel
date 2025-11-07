"""Tarefas do Trello executadas via cluster (Django Q).

Estas funções encapsulam operações de sincronização com o Trello para
serem executadas por workers do cluster, evitando chamadas diretas
no contexto dos sinais.

As tarefas são agendadas pelos sinais em
``smart_core_assistant_painel.app.trello_sync.signals``.
"""

from __future__ import annotations

from typing import Any, cast

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
        logger.warning("Fluxo não encontrado para reordenar listas: {}", fluxo_id)
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
        logger.warning("Etapa não encontrada para arquivar lista: {}", etapa_id)
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
        logger.warning("Fluxo não encontrado para arquivar board: {}", fluxo_id)
    except Exception as exc:
        logger.warning("Falha ao arquivar board Trello: {}", exc)


def task_atendimento_ensure_card(atendimento_id: int) -> None:
    """Garante o card Trello para um atendimento.

    Args:
        atendimento_id: ID do ``Atendimento``.
    """
    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        TicketSyncService().ensure_card_for_atendimento(atendimento)
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
            try:
                trello_client.add_member_to_card(
                    card.external_id, member_id
                )
            except Exception as exc:
                logger.warning(
                    "Falha ao adicionar membro ao card: {}",
                    exc,
                )

        from smart_core_assistant_painel.app.ui.atendimentos.models import (
            Atendimento as AtModelo,
        )

        qs = AtModelo.objects.filter(atendente_humano=atendente).order_by(
            "-data_inicio"
        )
        nome_agente: str = getattr(atendente, "nome", "")
        email_agente: str = getattr(atendente, "email", "")
        dep_nome: str = (
            atendente.departamento.nome
            if getattr(atendente, "departamento", None)
            else ""
        )
        especialidades: list[str] = getattr(atendente, "especialidades", [])
        espec_str: str = (
            ", ".join(especialidades) if especialidades else "(não informado)"
        )
        servico_atual: str = (
            getattr(atendimento, "produto_servico", "") or "(não informado)"
        )

        lines = [
            f"Agente: {nome_agente} ({email_agente})",
            (
                f"Departamento: {dep_nome}"
                if dep_nome
                else "Departamento: (não informado)"
            ),
            f"Especialidades: {espec_str}",
            f"Serviço atual: {servico_atual}",
            "Atendimentos vinculados:",
        ]
        for a in qs[:10]:
            assunto = getattr(a, "assunto", "") or "(sem assunto)"
            lines.append(f"- #{a.pk} - {assunto}")
        desc = "\n".join(lines)

        try:
            trello_client.update_item(
                data_source_id=card.list_sync.external_id,
                item_id=card.external_id,
                payload={"desc": desc},
            )
        except Exception as exc:
            logger.warning("Falha ao atualizar descrição do card: {}", exc)
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
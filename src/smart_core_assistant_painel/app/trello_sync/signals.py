from typing import Any, cast

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.trello_sync.services import (
    FlowSyncService,
    TicketSyncService,
    MemberSyncService,
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


@receiver(post_save, sender=Atendente)
def atendente_created_invite_trello(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    """Envia convite para o board do fluxo ao cadastrar Atendente."""
    if not created:
        return
    try:
        MemberSyncService().invite_for_atendente(instance)
    except Exception as exc:
        logger.warning("Falha ao convidar atendente para Trello: {}", exc)


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
        # Resolve board pelo fluxo do atendente
        fluxo = getattr(instance, "fluxo", None)
        if fluxo is None:
            return
        from smart_core_assistant_painel.app.trello_sync.models import TrelloBoard

        board = TrelloBoard.objects.filter(fluxo=fluxo).first()
        if board is None:
            return

        ms = MemberSyncService()
        member_id = ms.resolve_member_external_id(instance)

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
                    "Falha ao remover membro do board Trello: {}", exc
                )
        else:
            logger.warning(
                "Membro Trello não resolvido para atendente ao remover; ignorado."
            )
    except Exception as exc:
        logger.warning("Remoção Trello em Atendente falhou: {}", exc)


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
        # Garante card
        service = TicketSyncService()
        try:
            card = getattr(instance, "trello_card", None)
            if card is None:
                card = service.ensure_card_for_atendimento(instance)
        except Exception:
            card = getattr(instance, "trello_card", None)

        atendente = getattr(instance, "atendente_humano", None)
        if not card or not atendente:
            return

        # Resolve member id e adiciona ao card
        ms = MemberSyncService()
        member_id = ms.resolve_member_external_id(atendente)
        # Obtem cliente Trello a partir do SERVICEHUB global
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
                trello_client.add_member_to_card(card.external_id, member_id)
            except Exception as exc:
                logger.warning("Falha ao adicionar membro ao card: {}", exc)

        # Atualiza descrição com contexto do atendente (especialidades,
        # departamento, serviço atual) e atendimentos vinculados
        from smart_core_assistant_painel.app.ui.atendimentos.models import (
            Atendimento as AtModelo,
        )

        qs = AtModelo.objects.filter(atendente_humano=atendente).order_by(
            "-data_inicio"
        )
        nome_agente: str = getattr(atendente, "nome", "")
        email_agente: str = getattr(atendente, "email", "")
        dep_nome: str = (
            atendente.departamento.nome if getattr(atendente, "departamento", None) else ""
        )
        especialidades: list[str] = getattr(atendente, "especialidades", [])
        espec_str: str = ", ".join(especialidades) if especialidades else "(não informado)"

        servico_atual: str = getattr(instance, "produto_servico", "") or "(não informado)"

        lines = [
            f"Agente: {nome_agente} ({email_agente})",
            f"Departamento: {dep_nome}" if dep_nome else "Departamento: (não informado)",
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
    except Exception as exc:
        logger.warning("Atualização Trello em Atendimento falhou: {}", exc)

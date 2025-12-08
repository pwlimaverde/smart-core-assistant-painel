from typing import Any, Optional

from loguru import logger

from smart_core_assistant_painel.app.trello_sync.models import TrelloCard


class WebhookProcessingService:
    """[TRL-MOV-001] Processa payloads de webhook do Trello e aplica mudanças.

    Sincronização Bidirecional de Movimentação.
    """

    def process(self, payload: dict[str, Any]) -> None:
        """[TRL-MOV-001] Processa o evento recebido do Trello.

        Sincronização Bidirecional de Movimentação.

        Comentário: Implementação mínima que lida com mudança de lista
        (card move) e criação de listas (list create).
        """
        action: dict[str, Any] = payload.get("action", {})
        action_type: str = action.get("type", "")

        if action_type == "createList":
            self._handle_create_list(action)
            return

        if action_type not in {"updateCard", "moveCardToList"}:
            logger.debug("Evento Trello ignorado: {}", action_type)
            return

        data: dict[str, Any] = action.get("data", {})
        card_obj: dict[str, Any] = data.get("card", {})
        list_after: dict[str, Any] = data.get("listAfter", {})

        card_id: Optional[str] = card_obj.get("id")
        dest_list_id: Optional[str] = list_after.get("id")
        if not card_id or not dest_list_id:
            logger.warning("Webhook sem card/list id válidos")
            return

        try:
            trello_card: TrelloCard = TrelloCard.objects.select_related(
                "atendimento", "list_sync", "list_sync__etapa"
            ).get(external_id=card_id)
        except TrelloCard.DoesNotExist:
            logger.warning("Card Trello não mapeado: {}", card_id)
            return

        # Se mudou de lista, tentar atualizar etapa do atendimento
        if trello_card.list_sync.external_id != dest_list_id:
            from smart_core_assistant_painel.app.trello_sync.models import (
                TrelloList,
            )

            try:
                dest_list = TrelloList.objects.select_related("etapa").get(
                    external_id=dest_list_id
                )
            except TrelloList.DoesNotExist:
                logger.warning(
                    "Lista Trello destino não mapeada: {}", dest_list_id
                )
                return

            # Atualiza o mapeamento do card
            trello_card.list_sync = dest_list
            trello_card.save(update_fields=["list_sync"])

            # Atualiza etapa atual no atendimento e registra movimento
            atendimento = trello_card.atendimento
            etapa_dest = dest_list.etapa
            etapa_origem = getattr(atendimento, "etapa_atual", None)
            atendimento.etapa_atual = etapa_dest
            atendimento.save(update_fields=["etapa_atual"])

            # Sincroniza status para etapas padrão
            try:
                from smart_core_assistant_painel.app.ui.atendimentos.models import (
                    StatusAtendimento,
                )
                from smart_core_assistant_painel.app.ui.operacional.models import (
                    TipoEtapa,
                )

                tipo_etapa = getattr(etapa_dest, "tipo_etapa", None)
                novo_status = None

                if tipo_etapa == TipoEtapa.FILA:
                    novo_status = StatusAtendimento.FILA
                elif tipo_etapa == TipoEtapa.TRABALHO:
                    novo_status = StatusAtendimento.EM_ATENDIMENTO
                elif tipo_etapa == TipoEtapa.ESPERA:
                    novo_status = StatusAtendimento.PENDENCIA
                elif tipo_etapa == TipoEtapa.FINALIZACAO:
                    # Distinguir entre resolvido e cancelado pelo nome da etapa
                    nome_lower = etapa_dest.nome.lower()
                    if "cancelado" in nome_lower or "cancel" in nome_lower:
                        novo_status = StatusAtendimento.CANCELADO
                    else:
                        novo_status = StatusAtendimento.RESOLVIDO

                if novo_status and atendimento.status != novo_status:
                    atendimento.status = novo_status
                    atendimento.save(update_fields=["status"])
                    logger.info(
                        "Status do atendimento {} atualizado para {} via Trello",
                        atendimento.id,
                        novo_status,
                    )

            except Exception as exc:
                logger.warning(
                    "Falha ao sincronizar status do atendimento via Trello: {}",
                    exc,
                )

            try:
                from smart_core_assistant_painel.app.ui.operacional.models import (
                    MovimentoFluxo,
                )

                MovimentoFluxo.criar_movimento(
                    atendimento=atendimento,
                    etapa_destino=etapa_dest,
                    atendente_destino=None,
                    motivo="Atualização via Trello webhook",
                    automatico=True,
                )
            except Exception as exc:
                logger.error("Falha ao registrar movimento: {}", exc)

    def _handle_create_list(self, action: dict[str, Any]) -> None:
        """Processa evento de criação de lista (createList)."""
        data: dict[str, Any] = action.get("data", {})
        board_data: dict[str, Any] = data.get("board", {})
        list_data: dict[str, Any] = data.get("list", {})

        board_id = board_data.get("id")
        list_id = list_data.get("id")
        list_name = list_data.get("name")
        list_pos = list_data.get("pos", 0)

        if not board_id or not list_id or not list_name:
            logger.warning("Webhook createList incompleto: {}", data)
            return

        from django.db import transaction

        from smart_core_assistant_painel.app.trello_sync.models import (
            TrelloBoard,
            TrelloList,
        )
        from smart_core_assistant_painel.app.ui.operacional.models import (
            EtapaFluxo,
        )

        try:
            trello_board = TrelloBoard.objects.select_related("fluxo").get(
                external_id=board_id
            )
        except TrelloBoard.DoesNotExist:
            logger.warning("Board Trello não mapeado: {}", board_id)
            return

        # Evitar duplicidade
        if TrelloList.objects.filter(external_id=list_id).exists():
            logger.info("Lista Trello já existe: {}", list_id)
            return

        try:
            with transaction.atomic():
                # Determina nova ordem
                last_etapa = (
                    EtapaFluxo.objects.filter(fluxo=trello_board.fluxo)
                    .order_by("-ordem")
                    .first()
                )
                new_order = (last_etapa.ordem + 1) if last_etapa else 1

                # Cria EtapaFluxo
                nova_etapa = EtapaFluxo.objects.create(
                    fluxo=trello_board.fluxo,
                    nome=list_name[:50],  # Limita tamanho conforme model
                    ordem=new_order,
                    tipo_etapa="TRABALHO",  # Default seguro
                    automatico=False,
                )

                # Tratamento seguro para posição (pode ser 'top', 'bottom' ou float)
                try:
                    trello_pos = float(list_pos)
                except (ValueError, TypeError):
                    # Se não for número, define um padrão seguro
                    trello_pos = 0.0

                # Cria TrelloList
                TrelloList.objects.create(
                    etapa=nova_etapa,
                    board=trello_board,
                    external_id=list_id,
                    name=list_name,
                    position=trello_pos,
                    metadata=list_data,
                )
                logger.info(
                    "Nova EtapaFluxo criada via Trello: {} (Board {})",
                    list_name,
                    board_id,
                )

        except Exception as exc:
            logger.error("Falha ao criar EtapaFluxo via Webhook: {}", exc)

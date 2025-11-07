from typing import Any, Optional

from loguru import logger

from smart_core_assistant_painel.app.trello_sync.models import TrelloCard


class WebhookProcessingService:
    """Processa payloads de webhook do Trello e aplica mudanças."""

    def process(self, payload: dict[str, Any]) -> None:
        """Processa o evento recebido do Trello.

        Comentário: Implementação mínima que lida com mudança de lista
        (card move). Atualiza a etapa_atual do atendimento se mapeada.
        """
        action: dict[str, Any] = payload.get("action", {})
        action_type: str = action.get("type", "")

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
                logger.warning("Lista Trello destino não mapeada: {}",
                               dest_list_id)
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
from typing import Any, Optional

from loguru import logger

from smart_core_assistant_painel.modules.services import (
    FeaturesCompose,
    SERVICEHUB,
)
from smart_core_assistant_painel.modules.services.features.\
    unifield_data_services.domain.interface.unified_data_service import (
        UnifiedDataService,
    )
from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloCard,
    TrelloList,
)


class TicketSyncService:
    """
    Serviço de sincronização de tickets (Atendimento → Card).
    """

    def __init__(self) -> None:
        # Comentário (PT-BR): Obtém o UDS do SERVICEHUB. Se necessário,
        # inicializa via FeaturesCompose para registrar a instância.
        try:
            self.client: UnifiedDataService = SERVICEHUB.unified_data_service
        except Exception:
            FeaturesCompose.unifield_data_services()
            self.client = SERVICEHUB.unified_data_service

    def ensure_card_for_atendimento(self, atendimento: Any) -> TrelloCard:
        """
        Garante criação de Card no Trello para o atendimento.
        """
        existing: Optional[TrelloCard] = getattr(
            atendimento, "trello_card", None
        )
        if existing:
            return existing

        etapa = getattr(atendimento, "etapa_atual", None)
        if not etapa:
            logger.info(
                "Atendimento %s sem etapa_atual; não cria card",
                atendimento.pk,
            )
            raise ValueError("Atendimento sem etapa_atual para Trello")

        lista: Optional[TrelloList] = getattr(etapa, "trello_list", None)
        if not lista:
            from .flow_sync_service import FlowSyncService

            lista = FlowSyncService().ensure_list_for_etapa(etapa)

        name: str = atendimento.assunto or f"Atendimento {atendimento.pk}"
        # Comentário: create_item retorna o ID do card; montar payload.
        payload: dict[str, Any] = {"name": name, "desc": ""}
        card_id: str = self.client.create_item(
            data_source_id=lista.external_id, payload=payload
        )
        # Buscar dados completos do card para metadados.
        data: Optional[dict[str, Any]] = self.client.get_item(
            data_source_id=lista.external_id, item_id=card_id
        )
        card_data: dict[str, Any] = data if isinstance(data, dict) else {}
        card: TrelloCard = TrelloCard.objects.create(
            atendimento=atendimento,
            list_sync=lista,
            external_id=card_id,
            name=card_data.get("name", name),
            url=card_data.get("shortUrl"),
            metadata=card_data,
        )
        return card
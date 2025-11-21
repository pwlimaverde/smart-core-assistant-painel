from typing import Any

from loguru import logger


class WebhookProcessingService:
    """Processa payloads de webhook vindos do ClickUp.

    Implementação mínima apenas registra o recebimento.
    """

    def process(self, payload: dict[str, Any]) -> None:
        # Comentário: lógica futura pode disparar sync de itens/estados
        event = str(payload.get("event", ""))
        logger.info("Webhook ClickUp recebido: {}", event)

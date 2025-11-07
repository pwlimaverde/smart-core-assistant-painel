from typing import Any

from django.apps import AppConfig


class TrelloSyncConfig(AppConfig):
    name: str = "smart_core_assistant_painel.app.trello_sync"
    label: str = "trello_sync"
    verbose_name: str = "Integração Trello"

    def ready(self) -> None:
        # Comentário (PT-BR): Carrega sinais ao iniciar a app
        try:
            from . import signals as _signals  # noqa: F401
        except Exception as exc:
            # Evita falha de inicialização caso models ainda não migrados
            from loguru import logger

            logger.warning(
                "Falha ao carregar sinais do trello_sync: {}", exc
            )
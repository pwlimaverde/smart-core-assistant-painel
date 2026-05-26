from django.apps import AppConfig


class ChatEvolutionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.chat_evolution"

    def ready(self) -> None:
        try:
            from . import (
                signals,  # noqa: F401 # pyright: ignore[reportUnusedImport]
            )
        except Exception as exc:
            from loguru import logger

            logger.warning("Falha ao carregar sinais chat_evolution: {}", exc)

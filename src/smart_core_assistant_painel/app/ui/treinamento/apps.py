from django.apps import AppConfig
from loguru import logger


class TreinamentoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.ui.treinamento"

    def ready(self) -> None:
        from . import signals  # noqa: F401
        # Inicialização idempotente dos serviços essenciais
        try:
            from smart_core_assistant_painel.modules.initial_loading import (
                start_initial_loading,
            )
            from smart_core_assistant_painel.modules.services import (
                start_services,
            )

            start_initial_loading()
            start_services()
        except Exception as e:  # pragma: no cover
            logger.error(
                f"Erro ao inicializar serviços para Django (treinamento): {e}",
                exc_info=True,
            )
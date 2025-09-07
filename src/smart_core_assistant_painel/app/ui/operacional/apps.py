from django.apps import AppConfig
from loguru import logger


class OperacionalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smart_core_assistant_painel.app.ui.operacional'

    def ready(self) -> None:
        """Inicializa Firebase e carrega variáveis de ambiente.

        Ordem: initial_loading depois services. Idempotente e robusto.
        """
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
                f"Erro ao inicializar serviços para Django (operacional): {e}",
                exc_info=True,
            )

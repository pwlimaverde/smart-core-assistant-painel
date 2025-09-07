from django.apps import AppConfig
from loguru import logger


class ClientesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smart_core_assistant_painel.app.ui.clientes'

    def ready(self) -> None:
        """Inicializa Firebase e carrega variáveis de ambiente.

        - Carrega .env e inicializa Firebase (initial_loading).
        - Inicializa serviços e variáveis remotas (services).
        - Idempotente e tolerante a falhas.
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
                f"Erro ao inicializar serviços para Django (clientes): {e}",
                exc_info=True,
            )

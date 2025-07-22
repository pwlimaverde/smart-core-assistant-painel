from django.apps import AppConfig
from loguru import logger


class OraculoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oraculo'

    def ready(self) -> None:
        # Importa signals para registrar os handlers
        from . import signals  # noqa: F401

        # Inicializa serviços quando a aplicação estiver pronta
        # Isso garante que o VetorStorage esteja configurado para Django-Q
        # workers
        try:
            from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import (
                start_initial_loading, )
            from smart_core_assistant_painel.modules.services.start_services import (
                start_services, )
            logger.info("Inicializando serviços para Django-Q workers...")
            # start_initial_loading()
            # start_services()
            logger.info(
                "Serviços inicializados com sucesso para Django-Q workers!")
        except Exception as e:
            logger.error(f"Erro ao inicializar serviços para Django-Q: {e}")
            # Não falha a aplicação, apenas loga o erro

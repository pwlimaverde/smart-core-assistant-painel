"""Configuração do aplicativo de usuários.

Este módulo define a configuração do aplicativo Django para o gerenciamento
de usuários.
"""

from django.apps import AppConfig
from loguru import logger


class UsuariosConfig(AppConfig):
    """Configuração para o aplicativo de usuários."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.ui.usuarios"

    def ready(self) -> None:
        """Inicializa Firebase e carrega variáveis de ambiente.

        - Garante que as variáveis do .env sejam carregadas (initial_loading).
        - Inicializa serviços (set_environ_remote, service hub, whatsapp).
        - A ordem é: initial_loading ANTES de services.
        - É idempotente e tolerante a falhas (apenas loga erros).
        """
        try:
            from smart_core_assistant_painel.modules.initial_loading import (
                start_initial_loading,
            )
            from smart_core_assistant_painel.modules.services import (
                start_services,
            )

            # Garantir ordem correta de inicialização
            start_initial_loading()
            start_services()
        except Exception as e:  # pragma: no cover - proteção de inicialização
            logger.error(
                f"Erro ao inicializar serviços para Django (usuarios): {e}",
                exc_info=True,
            )

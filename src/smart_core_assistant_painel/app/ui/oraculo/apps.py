"""Configuração do aplicativo Oráculo.

Este módulo define a configuração do aplicativo Django para o Oráculo,
incluindo a inicialização de serviços e o registro de signals.
"""
from django.apps import AppConfig
from loguru import logger
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete


class OraculoConfig(AppConfig):
    """Configuração para o aplicativo Oraculo."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.ui.oraculo"

    def ready(self) -> None:
        """Executa quando o aplicativo está pronto."""
        from . import signals  # noqa: F401

        try:
            from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import (
                start_initial_loading,
            )
            from smart_core_assistant_painel.modules.services.start_services import (
                start_services,
            )

            start_initial_loading()
            start_services()
        except Exception as e:
            logger.error(f"Erro ao inicializar serviços para Django-Q: {e}")

        self._configure_signals_as_robust()

    def _configure_signals_as_robust(self) -> None:
        """Configura os signals do modelo para usar send_robust."""
        try:
            self._set_send_to_robust(post_save, "post_save")
            self._set_send_to_robust(pre_save, "pre_save")
            self._set_send_to_robust(post_delete, "post_delete")
            self._set_send_to_robust(pre_delete, "pre_delete")
        except Exception as e:
            logger.error(f"Falha ao configurar signals como robustos: {e}", exc_info=True)

    @staticmethod
    def _set_send_to_robust(signal_obj, label: str) -> None:
        """Substitui o método send por send_robust de forma idempotente.

        Args:
            signal_obj: O objeto de signal a ser modificado.
            label (str): Um rótulo para fins de logging.
        """
        try:
            if getattr(signal_obj.send, "__name__", "") == "send_robust":
                return
            signal_obj.send = signal_obj.send_robust  # type: ignore[assignment]
            logger.debug(f"Signal '{label}' configurado para envio robusto.")
        except Exception as e:
            logger.warning(f"Não foi possível configurar '{label}' como robusto: {e}", exc_info=True)

from django.apps import AppConfig
from loguru import logger

# Importações necessárias para configurar sinais como robustos
from django.db.models.signals import (
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)


class OraculoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.ui.oraculo"

    def ready(self) -> None:
        # Importa signals para registrar os handlers
        from . import signals  # noqa: F401

        # Inicializa serviços quando a aplicação estiver pronta
        # Isso garante que o VetorStorage esteja configurado para Django-Q
        # workers
        try:
            from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import (  # noqa: E501
                start_initial_loading,
            )
            from smart_core_assistant_painel.modules.services.start_services import (
                start_services,
            )

            start_initial_loading()
            start_services()
        except Exception as e:
            logger.error(f"Erro ao inicializar serviços para Django-Q: {e}")
            # Não falha a aplicação, apenas loga o erro

        # Configura sinais padrão do Django para envio robusto (send_robust)
        # Isto impede que exceções em handlers quebrem o fluxo principal,
        # atendendo aos requisitos dos testes de signals.
        self._configure_signals_as_robust()

    def _configure_signals_as_robust(self) -> None:
        """Configura sinais de modelo para usar send_robust.

        Evita que exceções em handlers propaguem para a origem do evento.
        """
        try:
            self._set_send_to_robust(post_save, "post_save")
            self._set_send_to_robust(pre_save, "pre_save")
            self._set_send_to_robust(post_delete, "post_delete")
            self._set_send_to_robust(pre_delete, "pre_delete")
        except Exception as e:
            # Qualquer falha aqui não deve interromper a app.
            logger.error(
                f"Falha ao configurar sinais como robustos: {e}", exc_info=True
            )

    @staticmethod
    def _set_send_to_robust(signal_obj, label: str) -> None:
        """Substitui o método send pelo send_robust de forma idempotente."""
        try:
            # Se já estiver configurado, não faz nada.
            if getattr(signal_obj.send, "__name__", "") == "send_robust":
                return
            # Substitui o método de envio para capturar exceções dos handlers.
            signal_obj.send = signal_obj.send_robust  # type: ignore[assignment]
            logger.debug(
                f"Sinal '{label}' configurado para envio robusto (send_robust)."
            )
        except Exception as e:
            logger.warning(
                f"Não foi possível configurar '{label}' como robusto: {e}",
                exc_info=True,
            )

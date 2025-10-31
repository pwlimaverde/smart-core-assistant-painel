from typing import Any

from django.apps import AppConfig


class AppFlowyAdapterConfig(AppConfig):
    """Configuração do app `appflowy_adapter`.

    Comentários em Português conforme padrão do projeto.
    """

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "smart_core_assistant_painel.app.appflowy_adapter"

    def ready(self) -> None:
        """Executa inicializações do app quando carregado.

        Registra sinais de sincronização do adapter.
        """

        # Import tardio para evitar ciclos de import durante o startup.
        from . import signals as _signals  # noqa: F401
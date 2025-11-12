from django.apps import AppConfig


class ClickupSyncConfig(AppConfig):
    """Configuração do app de sincronização com ClickUp."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.clickup_sync"

    def ready(self) -> None:  # type: ignore[override]
        # Comentário: registra sinais ao iniciar o app
        from . import signals  # noqa: F401
        return None
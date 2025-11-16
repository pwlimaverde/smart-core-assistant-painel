from django.apps import AppConfig


class EvolutionSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.evolution_sync"
    verbose_name = "Evolution Sync"

    def ready(self) -> None:
        from . import signals  # noqa: F401
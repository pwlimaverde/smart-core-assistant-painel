from django.apps import AppConfig


class AtendimentosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.ui.atendimentos"

    def ready(self):
        from . import signals  # noqa: F401
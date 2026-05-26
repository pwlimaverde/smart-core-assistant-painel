from django.apps import AppConfig


class GestaoKanbanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.gestao_kanban"

    def ready(self) -> None:
        import smart_core_assistant_painel.app.gestao_kanban.signals  # noqa: F401 # pyright: ignore[reportUnusedImport]

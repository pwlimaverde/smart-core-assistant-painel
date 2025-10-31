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

        Por ora, nenhuma inicialização específica é necessária.
        """

        # Inicializações futuras (sinais, caches, etc.) podem ser feitas aqui.
        _noop: Any = None
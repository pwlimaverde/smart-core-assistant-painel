"""
Configuração do app notion_sync.

Este módulo contém a configuração Django para o app de sincronização
com plataformas externas (Notion, Airtable, etc).
"""

from django.apps import AppConfig


class NotionSyncConfig(AppConfig):
    """
    Configuração do app de sincronização com plataformas externas.

    Esta classe é responsável por:
    - Definir o nome e configurações do app
    - Registrar signals quando o app for carregado
    - Inicializar serviços necessários
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.notion_sync"
    verbose_name = "Sincronização com Plataformas Externas"

    def ready(self) -> None:
        """
        Método chamado quando o Django inicializa o app.

        Registra os signal receivers para capturar mudanças nos
        models principais e disparar sincronização.
        """
        # Import signals para registrar os receivers
        from . import signals  # noqa: F401

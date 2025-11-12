"""
Facade para datasources do UnifiedDataService.

Este pacote centraliza e expõe as implementações de datasource para o
serviço de dados unificado, permitindo selecionar o adapter adequado
(ex.: Trello, Notion) sem acoplamento no restante da aplicação.
"""

from .unifield_data_services_datasource import UnifieldDataServicesDatasource
from .trello_adapter import TrelloUnifiedDataService
from .clicup_adapter import ClicupUnifiedDataService
# Desabilitado temporariamente: import do adapter Notion.
# Isso evita carregar modelos do app `notion_sync` enquanto
# a integração está desativada.
# from .notion_adapter import NotionUnifiedDataService

__all__ = [
    # Datasource principal
    "UnifieldDataServicesDatasource",
    # Adapters
    "TrelloUnifiedDataService",
    "ClicupUnifiedDataService",
    # "NotionUnifiedDataService",
]

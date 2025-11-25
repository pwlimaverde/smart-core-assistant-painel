"""
Facade para datasources do UnifiedDataService.

Este pacote centraliza e expõe as implementações de datasource para o
serviço de dados unificado, permitindo selecionar o adapter adequado
(ex.: Trello, Notion) sem acoplamento no restante da aplicação.
"""

from .clicup_adapter import ClicupUnifiedDataService
from .trello_adapter import TrelloUnifiedDataService
from .unifield_data_services_datasource import UnifieldDataServicesDatasource

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

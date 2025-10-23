"""
Serviços de sincronização com plataformas externas.

Este módulo contém as implementações concretas dos serviços de sincronização
com diferentes plataformas (Notion, Airtable, etc).
"""

from .notion_service import NotionSyncService

__all__ = [
    "NotionSyncService",
]

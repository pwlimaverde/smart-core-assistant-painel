"""
App trello_sync: integra o fluxo de atendimento com o Trello.

Este módulo centraliza a integração bidirecional entre os modelos
do Django (Departamento, FluxoAtendimento, EtapaFluxo, Atendimento)
e os artefatos do Trello (Board, List, Card), utilizando adapters
existentes e uma camada de serviços.
"""

from importlib import import_module
from typing import Any

from .apps import TrelloSyncConfig

__all__ = [
    "TrelloSyncConfig",
    "TrelloBoard",
    "TrelloList",
    "TrelloCard",
    "TrelloMember",
]


def __getattr__(name: str) -> Any:
    """Importação tardia para evitar erros na inicialização do Django.

    Comentário: evita AppRegistryNotReady ao expor modelos via __init__.
    """
    if name in {"TrelloBoard", "TrelloList", "TrelloCard", "TrelloMember"}:
        module = import_module(
            "smart_core_assistant_painel.app.trello_sync.models"
        )
        return getattr(module, name)
    if name == "TrelloSyncConfig":
        return TrelloSyncConfig
    raise AttributeError(name)

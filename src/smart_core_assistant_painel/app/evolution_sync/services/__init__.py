"""Módulo de serviços do Evolution Sync.

Este módulo contém a camada de serviços para processamento de webhooks
e comunicação com a API Evolution.
"""

from .evolution_api import EvolutionWhatsAppService
from .webhook import WebhookProcessor

__all__ = [
    "EvolutionWhatsAppService",
    "WebhookProcessor",
]

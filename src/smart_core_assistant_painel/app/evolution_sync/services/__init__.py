"""Módulo de serviços do Evolution Sync.

Este módulo contém a camada de serviços para processamento de webhooks
e comunicação com a API Evolution (v2 e Go).
"""

from .evolution_api import (
    EvolutionAPIInterface,
    EvolutionWhatsAppService,
    get_evolution_adapter,
)
from .evolution_go_adapter import EvolutionGoAdapter
from .evolution_v2_adapter import EvolutionV2Adapter
from .message_buffer import (
    clear_buffer_contact,
    clear_scheduling_lock,
    get_and_clear_buffer_contact,
    sched_response_contact,
    set_buffer_contact,
)
from .webhook import WebhookProcessor

__all__ = [
    # Interface e factory
    "EvolutionAPIInterface",
    "get_evolution_adapter",
    # Adapters concretos
    "EvolutionGoAdapter",
    "EvolutionV2Adapter",
    # Alias retrocompat
    "EvolutionWhatsAppService",
    # Webhook
    "WebhookProcessor",
    # Buffer
    "clear_buffer_contact",
    "clear_scheduling_lock",
    "get_and_clear_buffer_contact",
    "sched_response_contact",
    "set_buffer_contact",
]

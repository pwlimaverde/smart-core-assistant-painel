"""Módulo de serviços do Evolution Sync.

Este módulo contém a camada de serviços para processamento de webhooks
e comunicação com o Evolution Go (único backend suportado).
"""

from .evolution_go_adapter import EvolutionGoAdapter
from .message_buffer import (
    clear_buffer_contact,
    clear_scheduling_lock,
    get_and_clear_buffer_contact,
    sched_response_contact,
    set_buffer_contact,
)
from .webhook import WebhookProcessor

__all__ = [
    # Adapter Evolution Go (único)
    "EvolutionGoAdapter",
    # Webhook
    "WebhookProcessor",
    # Buffer
    "clear_buffer_contact",
    "clear_scheduling_lock",
    "get_and_clear_buffer_contact",
    "sched_response_contact",
    "set_buffer_contact",
]

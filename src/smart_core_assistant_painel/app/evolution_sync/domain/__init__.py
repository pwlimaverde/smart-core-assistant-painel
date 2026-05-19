"""Módulo de domínio do Evolution Sync.

Este módulo contém as definições de dados e regras de negócio do app.
"""

from .schemas import (
    EvolutionContactData,
    EvolutionEventName,
    EvolutionMessageData,
    EvolutionProfileData,
    EvolutionWebhookEnvelope,
)

__all__ = [
    "EvolutionContactData",
    "EvolutionEventName",
    "EvolutionMessageData",
    "EvolutionProfileData",
    "EvolutionWebhookEnvelope",
]

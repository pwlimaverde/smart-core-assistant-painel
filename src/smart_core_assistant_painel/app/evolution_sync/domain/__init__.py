"""Módulo de domínio do Evolution Sync.

Este módulo contém as definições de dados e regras de negócio do app.
"""

from .schemas import (
    EvolutionContactData,
    EvolutionMessageData,
    EvolutionProfileData,
    EvolutionWebhookEnvelope,
)

__all__ = [
    "EvolutionContactData",
    "EvolutionMessageData",
    "EvolutionProfileData",
    "EvolutionWebhookEnvelope",
]

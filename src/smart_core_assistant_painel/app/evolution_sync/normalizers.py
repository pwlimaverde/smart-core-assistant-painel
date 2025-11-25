from typing import Any, Dict, List

from smart_core_assistant_painel.app.evolution_sync.domain.schemas import (
    EvolutionWebhookEnvelope,
)


def normalize_evolution_webhook(
    payload: Dict[str, Any],
) -> EvolutionWebhookEnvelope:
    """Normaliza o payload do webhook para um envelope unificado.

    Este é um wrapper para o método from_dict_single da dataclass.

    Args:
        payload: O dicionário de dados recebido do webhook.

    Returns:
        EvolutionWebhookEnvelope: O objeto envelope normalizado.
    """
    return EvolutionWebhookEnvelope.from_dict_single(payload)


def normalize_evolution_webhook_batch(
    payload: Dict[str, Any],
) -> List[EvolutionWebhookEnvelope]:
    """Normaliza um payload de lote para uma lista de envelopes.

    Este é um wrapper para o método from_dict_batch da dataclass.

    Args:
        payload: O dicionário de dados recebido do webhook.

    Returns:
        List[EvolutionWebhookEnvelope]: Lista de envelopes normalizados.
    """
    return EvolutionWebhookEnvelope.from_dict_batch(payload)

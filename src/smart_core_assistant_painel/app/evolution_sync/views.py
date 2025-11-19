import json
from typing import Any, Dict, List

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from smart_core_assistant_painel.app.evolution_sync.domain.schemas import (
    EvolutionWebhookEnvelope,
)
from smart_core_assistant_painel.app.evolution_sync.normalizers import (
    normalize_evolution_webhook,
    normalize_evolution_webhook_batch,
)
from smart_core_assistant_painel.app.evolution_sync.services.webhook import (
    WebhookProcessor,
)


@csrf_exempt
def webhook(request: HttpRequest) -> JsonResponse:
    """Endpoint para receber webhooks da Evolution API.

    Args:
        request: O objeto HttpRequest do Django.

    Returns:
        JsonResponse: Resposta com status do processamento.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "method not allowed"}, status=405)
    try:
        payload: Dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "invalid json"}, status=400)

    data_obj = payload.get("data")
    envelopes: List[EvolutionWebhookEnvelope]
    if isinstance(data_obj, list):
        envelopes = normalize_evolution_webhook_batch(payload)
    else:
        envelopes = [normalize_evolution_webhook(payload)]

    processor = WebhookProcessor()
    result = processor.process_webhook(payload, envelopes)

    status_code = 200 if result.get("status") == "ok" else 200
    # Mantendo 200 para ignored_from_me conforme original,
    # mas accepted geralmente é 202. O original retornava 200 para ignored e 202 para accepted no final.

    if result.get("status") == "accepted":
        return JsonResponse(result, status=202)

    return JsonResponse(result, status=status_code)

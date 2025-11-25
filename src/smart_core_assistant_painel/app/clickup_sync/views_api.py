from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger

from .models import ClickupWebhookEvent
from .services import WebhookProcessingService


@csrf_exempt
def webhook(request: HttpRequest) -> HttpResponse:
    """Endpoint público para receber webhooks do ClickUp.

    - HEAD: verificação de existência (retorna 200).
    - POST: processa o payload JSON e persiste o evento.
    """
    if request.method == "HEAD":
        return HttpResponse("OK", status=200)

    if request.method != "POST":
        return HttpResponse(status=405)

    import json

    try:
        payload: dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    event_type: str = str(payload.get("event", ""))
    resource_id: str = str(payload.get("id", ""))

    ClickupWebhookEvent.objects.create(
        event_type=event_type, resource_id=resource_id, payload=payload
    )

    try:
        WebhookProcessingService().process(payload)
    except Exception as exc:
        logger.error("Falha ao processar webhook ClickUp: {}", exc)

    return JsonResponse({"status": "processed"}, status=200)

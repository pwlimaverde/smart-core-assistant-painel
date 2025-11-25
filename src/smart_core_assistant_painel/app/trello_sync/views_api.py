from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger

from .models import TrelloWebhookEvent
from .services import WebhookProcessingService


@csrf_exempt
def webhook(request: HttpRequest) -> HttpResponse:
    """Endpoint público para receber webhooks do Trello.

    - HEAD: usado pelo Trello para verificação de existência (retorna 200).
    - POST: processa o payload JSON e persiste o evento.
    """
    if request.method == "HEAD":
        return HttpResponse("OK", status=200)

    if request.method == "GET":
        return HttpResponse(
            "Webhook Trello está ativo e acessível.", status=200
        )

    if request.method != "POST":
        return HttpResponse(status=405)

    # Comentário: Django não possui request.json; usar request.body
    import json

    try:
        payload: dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    logger.warning("Recebido webhook Trello: {}", payload)

    return JsonResponse({"status": "processed"}, status=200)

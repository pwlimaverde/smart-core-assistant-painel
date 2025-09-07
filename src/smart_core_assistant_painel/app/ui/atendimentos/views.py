"""Views for the Atendimentos app."""

import json
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger

from smart_core_assistant_painel.app.ui.operacional.models import Departamento
from smart_core_assistant_painel.modules.ai_engine import FeaturesCompose

from .utils import sched_message_response, set_wa_buffer


@csrf_exempt
def webhook_whatsapp(request: HttpRequest) -> JsonResponse:
    """Endpoint to receive WhatsApp message notifications."""
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)
        if not request.body:
            return JsonResponse({"error": "Empty request body"}, status=400)
        try:
            body_str = request.body.decode("utf-8")
        except UnicodeDecodeError:
            body_str = request.body.decode("utf-8", errors="ignore")
            logger.warning("Decoding with errors='ignore' applied")

        data:dict[str, Any] = json.loads(body_str)
        departamento = Departamento.validar_api_key(data)
        if not departamento:
            return JsonResponse({"error": "Invalid or inactive API key"}, status=401)

        logger.info(f"Received webhook: {data}")
        message = FeaturesCompose.load_message_data(data)
        set_wa_buffer(message)
        sched_message_response(message.numero_telefone)

        return JsonResponse({"status": "success"}, status=200)
    except Exception as e:
        logger.error(f"Critical error in WhatsApp webhook: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)
import json
from typing import Any, Dict, List

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger

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
from smart_core_assistant_painel.app.tenants.models import Tenant


@csrf_exempt
def webhook(
    request: HttpRequest, tenant_slug: str | None = None
) -> JsonResponse:
    """[EVO-MSG-003] Endpoint para receber webhooks da Evolution API.

    Recebimento de Status e Mensagens (Webhooks).

    Args:
        request: O objeto HttpRequest do Django.
        tenant_slug: Slug do tenant (opcional, mas recomendado).

    Returns:
        JsonResponse: Resposta com status do processamento.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "method not allowed"}, status=405)

    # Buscar tenant pelo middleware (request.tenant)
    tenant: Tenant | None = getattr(request, "tenant", None)

    if not tenant and tenant_slug:
        tenant = Tenant.objects.filter(slug=tenant_slug).first()
        if tenant:
            logger.debug(
                f"Webhook tenant resolvido por slug da URL: {tenant.slug}"
            )

    if tenant:
        # Sanity Check: se tenant_slug veio na URL, deve bater com o tenant do contexto
        if tenant_slug and tenant.slug != tenant_slug:
            logger.warning(
                f"Mismatch de tenant: URL={tenant_slug} vs Context={tenant.slug}"
            )
        logger.debug(
            f"Webhook recebido para tenant: {tenant.name} ({tenant.slug})"
        )
    else:
        logger.warning(
            "Webhook recebido SEM tenant identificado. "
            f"URL slug: {tenant_slug}. "
            "Verifique se o TenantMiddleware está ativo."
        )

    try:
        payload: Dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "invalid json"}, status=400)

    # 1. Filtro Global: Processar APENAS 'messages.upsert'
    event = payload.get("event")
    if event != "messages.upsert":
        # Retorna 200 para confirmar recebimento, mas ignora processamento
        return JsonResponse({"status": "ignored_event"}, status=200)

    data_obj = payload.get("data")
    envelopes: List[EvolutionWebhookEnvelope]
    if isinstance(data_obj, list):
        envelopes = normalize_evolution_webhook_batch(payload)
    else:
        envelopes = [normalize_evolution_webhook(payload)]

    # Passa tenant para o processador
    processor = WebhookProcessor(tenant=tenant)
    result = processor.process_webhook(payload, envelopes)

    status_code = 200 if result.get("status") == "ok" else 200

    if result.get("status") == "accepted":
        return JsonResponse(result, status=202)

    return JsonResponse(result, status=status_code)

from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger

from smart_core_assistant_painel.app.tenants.middleware import (
    set_current_tenant,
)
from smart_core_assistant_painel.app.tenants.models import Tenant
from smart_core_assistant_painel.app.tenants.tenant_context import (
    get_current_tenant_slug,
)
from smart_core_assistant_painel.app.trello_sync.tasks import (
    task_process_trello_card_move,
    task_process_trello_list_create,
    task_process_trello_list_update,
)


@csrf_exempt
def webhook(
    request: HttpRequest, tenant_slug: str | None = None
) -> HttpResponse:
    """[TRL-MOV-001] Endpoint público para receber webhooks do Trello.

    Sincronização Bidirecional de Movimentação.

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

    logger.info("Recebido webhook Trello: {}", payload)

    # Comentário (PT-BR): Tenta definir contexto do tenant.
    # Prioridade: 1) tenant_slug da URL, 2) Fallback via board_id do payload
    if tenant_slug:
        tenant = Tenant.objects.filter(slug=tenant_slug).first()
        if tenant:
            set_current_tenant(tenant)
            request.tenant = tenant
            logger.info(
                "Contexto de tenant definido para webhook Trello: {}",
                tenant.slug,
            )
    else:
        # Fallback: inferir tenant a partir do board_id no payload
        # Isso permite que webhooks antigos (sem tenant_slug na URL) funcionem
        try:
            model = payload.get("model", {})
            board_id = model.get("id") if isinstance(model, dict) else None
            if board_id:
                # Importar aqui para evitar import circular
                from smart_core_assistant_painel.app.trello_sync.models import (
                    TrelloBoard,
                )

                # Buscar board no banco e obter tenant do fluxo associado
                board = (
                    TrelloBoard.objects.select_related(
                        "fluxo__departamento__tenant"
                    )
                    .filter(external_id=board_id)
                    .first()
                )
                if (
                    board
                    and board.fluxo
                    and hasattr(board.fluxo, "departamento")
                    and board.fluxo.departamento
                    and hasattr(board.fluxo.departamento, "tenant")
                ):
                    inferred_tenant = board.fluxo.departamento.tenant
                    if inferred_tenant:
                        tenant_slug = inferred_tenant.slug
                        set_current_tenant(inferred_tenant)
                        request.tenant = inferred_tenant
                        logger.info(
                            "Contexto de tenant inferido do board {} para "
                            "webhook Trello: {}",
                            board_id,
                            inferred_tenant.slug,
                        )
        except Exception as exc:
            logger.warning(
                "Falha ao inferir tenant do payload do webhook: {}", exc
            )

    tenant_slug = get_current_tenant_slug() or "public"
    if tenant_slug == "public":
        logger.warning(
            "Webhook Trello processado sem contexto de tenant definido (public)."
        )

    # Processamento de eventos
    try:
        action = payload.get("action", {})
        action_type = action.get("type")
        data = action.get("data", {})

        # Detecta movimentação de card entre listas
        if action_type == "updateCard":
            list_before = data.get("listBefore")
            list_after = data.get("listAfter")
            card = data.get("card", {})

            if list_before and list_after and card:
                card_id = card.get("id")
                list_after_id = list_after.get("id")
                # Extrai ID do membro que realizou a ação
                member_creator_id = action.get("idMemberCreator")

                if card_id and list_after_id:
                    logger.info(
                        "Detectada movimentação de card Trello: {} -> {} (por {})",
                        card_id,
                        list_after_id,
                        member_creator_id,
                    )
                    task_process_trello_card_move.delay(
                        tenant_slug,
                        card_id,
                        list_after_id,
                        member_creator_id,
                    )

        # Detecta criação de lista
        elif action_type == "createList":
            list_data = data.get("list", {})
            board_data = data.get("board", {})

            list_id = list_data.get("id")
            list_name = list_data.get("name")
            board_id = board_data.get("id")

            if list_id and list_name and board_id:
                logger.info("Detectada criação de lista Trello: {}", list_name)
                task_process_trello_list_create.delay(
                    tenant_slug,
                    list_id,
                    list_name,
                    board_id,
                )

        # Detecta atualização de lista (renomear ou arquivar)
        elif action_type == "updateList":
            list_data = data.get("list", {})
            old_data = data.get("old", {})

            list_id = list_data.get("id")

            # Se houve mudança de nome ou status (closed)
            if list_id and ("name" in old_data or "closed" in old_data):
                list_name = list_data.get("name")
                closed = list_data.get("closed")

                logger.info(
                    "Detectada atualização de lista Trello: {}", list_id
                )
                task_process_trello_list_update.delay(
                    tenant_slug,
                    list_id,
                    list_name,
                    closed,
                )

    except Exception as exc:
        logger.error("Erro ao processar payload do webhook: {}", exc)

    return JsonResponse({"status": "processed"}, status=200)

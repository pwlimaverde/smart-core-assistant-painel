from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger


@csrf_exempt
def webhook(request: HttpRequest) -> HttpResponse:
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
                    from django_q.tasks import async_task

                    logger.info(
                        "Detectada movimentação de card Trello: {} -> {} (por {})",
                        card_id,
                        list_after_id,
                        member_creator_id,
                    )
                    async_task(
                        "smart_core_assistant_painel.app.trello_sync.tasks.task_process_trello_card_move",
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
                from django_q.tasks import async_task

                logger.info("Detectada criação de lista Trello: {}", list_name)
                async_task(
                    "smart_core_assistant_painel.app.trello_sync.tasks.task_process_trello_list_create",
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

                from django_q.tasks import async_task

                logger.info(
                    "Detectada atualização de lista Trello: {}", list_id
                )
                async_task(
                    "smart_core_assistant_painel.app.trello_sync.tasks.task_process_trello_list_update",
                    list_id,
                    list_name,
                    closed,
                )

    except Exception as exc:
        logger.error("Erro ao processar payload do webhook: {}", exc)

    return JsonResponse({"status": "processed"}, status=200)

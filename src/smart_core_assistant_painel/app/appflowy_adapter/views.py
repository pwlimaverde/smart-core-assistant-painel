from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from django.http import HttpRequest, JsonResponse

try:  # Uso opcional de loguru para logs estruturados
    from loguru import logger
except Exception:  # pragma: no cover - fallback simples
    class _DummyLogger:
        def info(self, msg: str) -> None:  # type: ignore[no-untyped-def]
            pass

        def warning(self, msg: str) -> None:  # type: ignore[no-untyped-def]
            pass

        def error(self, msg: str) -> None:  # type: ignore[no-untyped-def]
            pass

    logger = _DummyLogger()  # type: ignore[assignment]


def health(request: HttpRequest) -> JsonResponse:
    """Endpoint de saúde do adapter.

    Retorna um JSON simples indicando que o adapter está acessível.
    """

    logger.info("health endpoint called")
    payload: Dict[str, Any] = {
        "status": "ok",
        "adapter": "appflowy_adapter",
        "timestamp": datetime.utcnow().isoformat(),
    }
    return JsonResponse(payload, status=200)


def workspaces(request: HttpRequest) -> JsonResponse:
    """Lista de workspaces disponíveis (stub inicial).

    No MVI, retornamos dados estáticos para validar o fluxo.
    """

    logger.info("workspaces endpoint called")
    payload: Dict[str, Any] = {
        "workspaces": [
            {
                "workspace_id": "default",
                "name": "Default Workspace",
            }
        ]
    }
    return JsonResponse(payload, status=200)


def grid_schema(request: HttpRequest, grid_id: UUID) -> JsonResponse:
    """Metadados do Grid (colunas e tipos) — stub inicial.

    """

    logger.info(f"grid_schema endpoint called: {grid_id}")
    payload: Dict[str, Any] = {
        "grid_id": str(grid_id),
        "columns": [
            {"key": "ticket_id", "type": "string"},
            {"key": "name", "type": "string"},
            {"key": "status", "type": "string"},
            {"key": "priority", "type": "string"},
            {"key": "assigned_to", "type": "string"},
            {"key": "tags", "type": "list[string]"},
        ],
    }
    return JsonResponse(payload, status=200)


def rows_list_or_create(request: HttpRequest, grid_id: UUID) -> JsonResponse:
    """Lista ou cria linhas do Grid (stub).

    GET: retorna delta/dados estáticos.
    POST: simula criação e retorna identificador.
    """

    logger.info("rows_list_or_create called")
    logger.info(f"grid={grid_id} method={request.method}")
    if request.method == "GET":
        since: str = request.GET.get("since", "")
        payload: Dict[str, Any] = {
            "grid_id": str(grid_id),
            "since": since,
            "rows": [],  # MVI: lista vazia; será populado futuramente
        }
        return JsonResponse(payload, status=200)

    if request.method == "POST":
        payload: Dict[str, Any] = {
            "grid_id": str(grid_id),
            "row_id": "00000000-0000-0000-0000-000000000000",
            "status": "created",
        }
        return JsonResponse(payload, status=201)

    return JsonResponse({"detail": "Method not allowed"}, status=405)


def row_update_or_delete(request: HttpRequest, grid_id: UUID, row_id: UUID) -> JsonResponse:
    """Atualiza ou deleta uma linha do Grid (stub).

    PUT: retorna sucesso com versão fictícia.
    DELETE: retorna sucesso sem conteúdo.
    """

    logger.info("row_update_or_delete called")
    logger.info(f"grid={grid_id} row={row_id} method={request.method}")
    if request.method == "PUT":
        payload: Dict[str, Any] = {
            "grid_id": str(grid_id),
            "row_id": str(row_id),
            "status": "updated",
            "version": 1,
        }
        return JsonResponse(payload, status=200)

    if request.method == "DELETE":
        payload: Dict[str, Any] = {
            "status": "deleted",
        }
        return JsonResponse(payload, status=204)

    return JsonResponse({"detail": "Method not allowed"}, status=405)
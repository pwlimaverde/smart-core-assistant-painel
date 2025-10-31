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

# --- DRF endpoints protegidos por JWT ---
from rest_framework import status  # noqa: E402
from rest_framework.decorators import api_view, permission_classes  # noqa: E402
from rest_framework.permissions import IsAuthenticated  # noqa: E402
from rest_framework.request import Request  # noqa: E402
from rest_framework.response import Response  # noqa: E402

from .models import (  # noqa: E402
    AppFlowyColumn,
    AppFlowyGrid,
    AppFlowyRow,
    AppFlowyWorkspace,
)
from .serializers import (  # noqa: E402
    AppFlowyColumnSerializer,
    AppFlowyRowSerializer,
    AppFlowyWorkspaceSerializer,
    validate_if_match_version,
)


@api_view(["GET"])  # type: ignore[misc]
@permission_classes([IsAuthenticated])  # type: ignore[misc]
def workspaces(request: Request) -> Response:
    """Lista workspaces disponíveis."""

    qs = AppFlowyWorkspace.objects.all().order_by("name")
    data = AppFlowyWorkspaceSerializer(qs, many=True).data
    return Response({"items": data}, status=status.HTTP_200_OK)


@api_view(["GET"])  # type: ignore[misc]
@permission_classes([IsAuthenticated])  # type: ignore[misc]
def grid_schema(request: Request, grid_id: UUID) -> Response:
    """Retorna metadados das colunas de um grid."""

    try:
        grid = AppFlowyGrid.objects.get(grid_id=grid_id)
    except AppFlowyGrid.DoesNotExist:
        return Response({"detail": "grid não encontrado"}, status=404)

    cols = AppFlowyColumn.objects.filter(grid=grid).order_by("order")
    data = AppFlowyColumnSerializer(cols, many=True).data
    return Response({"grid_id": str(grid_id), "columns": data}, status=200)


@api_view(["GET", "POST"])  # type: ignore[misc]
@permission_classes([IsAuthenticated])  # type: ignore[misc]
def rows_list_or_create(request: Request, grid_id: UUID) -> Response:
    """Lista ou cria linhas de um grid."""

    try:
        grid = AppFlowyGrid.objects.get(grid_id=grid_id)
    except AppFlowyGrid.DoesNotExist:
        return Response({"detail": "grid não encontrado"}, status=404)

    if request.method == "GET":
        since_param = request.query_params.get("since")
        qs = AppFlowyRow.objects.filter(grid=grid)
        if since_param:
            try:
                since_dt = datetime.fromisoformat(str(since_param))
                qs = qs.filter(updated_at__gt=since_dt)
            except ValueError:
                return Response({"detail": "since inválido"}, status=400)
        qs = qs.order_by("-updated_at")
        data = AppFlowyRowSerializer(qs, many=True).data
        return Response({"items": data}, status=200)

    payload: Dict[str, Any] = dict(request.data)
    required = ["ticket_id", "name", "channel", "status", "priority"]
    missing = [k for k in required if k not in payload]
    if missing:
        return Response({"detail": f"campos faltando: {missing}"}, status=400)

    obj, created = AppFlowyRow.objects.get_or_create(
        grid=grid,
        ticket_id=str(payload["ticket_id"]).strip(),
        defaults={
            "name": str(payload["name"]).strip(),
            "channel": str(payload["channel"]).strip(),
            "status": str(payload["status"]).strip(),
            "priority": str(payload["priority"]).strip(),
            "assigned_to": str(payload.get("assigned_to", "")).strip(),
            "tags": payload.get("tags", []),
            "last_message": str(payload.get("last_message", "")).strip(),
        },
    )
    if not created:
        for field in [
            "name",
            "channel",
            "status",
            "priority",
            "assigned_to",
            "tags",
            "last_message",
        ]:
            if field in payload:
                setattr(obj, field, payload[field])
        obj.version = (obj.version or 1) + 1
        obj.save(update_fields=[
            "name",
            "channel",
            "status",
            "priority",
            "assigned_to",
            "tags",
            "last_message",
            "version",
            "updated_at",
        ])

    data = AppFlowyRowSerializer(obj).data
    return Response(data, status=status.HTTP_201_CREATED if created else 200)


@api_view(["PUT", "DELETE"])  # type: ignore[misc]
@permission_classes([IsAuthenticated])  # type: ignore[misc]
def row_update_or_delete(request: Request, grid_id: UUID, row_id: UUID) -> Response:
    """Atualiza (If-Match) ou remove uma linha."""

    try:
        grid = AppFlowyGrid.objects.get(grid_id=grid_id)
    except AppFlowyGrid.DoesNotExist:
        return Response({"detail": "grid não encontrado"}, status=404)

    try:
        row = AppFlowyRow.objects.get(grid=grid, row_id=row_id)
    except AppFlowyRow.DoesNotExist:
        return Response({"detail": "linha não encontrada"}, status=404)

    if request.method == "DELETE":
        row.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if_match = request.headers.get("If-Match")
    ok, msg = validate_if_match_version(if_match, int(row.version))
    if not ok:
        return Response(
            {"detail": msg, "current_version": int(row.version)},
            status=status.HTTP_412_PRECONDITION_FAILED,
        )

    payload: Dict[str, Any] = dict(request.data)
    for field in [
        "name",
        "channel",
        "status",
        "priority",
        "assigned_to",
        "tags",
        "last_message",
        "sla_due",
        "received_at",
    ]:
        if field in payload:
            setattr(row, field, payload[field])

    row.version = int(row.version) + 1
    row.save(update_fields=[
        "name",
        "channel",
        "status",
        "priority",
        "assigned_to",
        "tags",
        "last_message",
        "sla_due",
        "received_at",
        "version",
        "updated_at",
    ])

    data = AppFlowyRowSerializer(row).data
    return Response(data, status=status.HTTP_200_OK)


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
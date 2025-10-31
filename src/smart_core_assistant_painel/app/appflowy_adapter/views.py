from __future__ import annotations

from datetime import datetime
from django.utils.dateparse import parse_datetime
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
    AppFlowyGridSerializer,
    AppFlowyRowSerializer,
    AppFlowyRowWriteSerializer,
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
def grids_list(request: Request, workspace_id: UUID) -> Response:
    """Lista grids de um workspace por `workspace_id`.

    Permite resolução por nome no cliente quando IDs não estão definidos.
    """

    try:
        ws = AppFlowyWorkspace.objects.get(workspace_id=workspace_id)
    except AppFlowyWorkspace.DoesNotExist:
        return Response({"detail": "workspace não encontrado"}, status=404)

    qs = AppFlowyGrid.objects.filter(workspace=ws).order_by("name")
    data = AppFlowyGridSerializer(qs, many=True).data
    return Response({"items": data}, status=200)


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
            # Aceita ISO8601 com timezone (inclui sufixo 'Z') ou sem.
            # Usa parse do Django para ampliar compatibilidade.
            raw_since: str = str(since_param).strip()
            since_dt = parse_datetime(raw_since)
            if since_dt is None and raw_since.endswith("Z"):
                # Ajusta 'Z' → '+00:00' para parsers que exigem offset
                adjusted: str = f"{raw_since[:-1]}+00:00"
                since_dt = parse_datetime(adjusted)
            if since_dt is None and " " in raw_since:
                # Alguns parsers transformam '+' em espaço no offset.
                # Troca o ÚLTIMO espaço por '+' e tenta novamente.
                head, sep, tail = raw_since.rpartition(" ")
                if sep:
                    fixed: str = f"{head}+{tail}"
                    since_dt = parse_datetime(fixed)
            if since_dt is None:
                return Response({"detail": "since inválido"}, status=400)
            qs = qs.filter(updated_at__gt=since_dt)
        qs = qs.order_by("-updated_at")
        data = AppFlowyRowSerializer(qs, many=True).data
        return Response({"items": data}, status=200)

    # Validação de payload via serializer de escrita
    serializer = AppFlowyRowWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=400)
    payload: Dict[str, Any] = dict(serializer.validated_data)

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
            "last_message": str(
                payload.get("last_message", "")
            ).strip(),
            "received_at": payload.get("received_at"),
            "sla_due": payload.get("sla_due"),
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
            "received_at",
            "sla_due",
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

    # Validação parcial do payload via serializer
    serializer = AppFlowyRowWriteSerializer(
        data=request.data,
        partial=True,
    )
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=400)
    payload: Dict[str, Any] = dict(serializer.validated_data)
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


@api_view(["GET"])  # type: ignore[misc]
@permission_classes([IsAuthenticated])  # type: ignore[misc]
def rows_stream(request: Request, grid_id: UUID) -> Response:
    """Stub de streaming de mudanças (SSE/WebSocket) pós-MVP.

    Planejado para fornecer eventos de alterações de linhas. Por ora,
    retornamos 501 para sinalizar funcionalidade futura.
    """

    return Response(
        {"detail": "stream de rows planejado (SSE/WebSocket)"},
        status=status.HTTP_501_NOT_IMPLEMENTED,
    )


# Removido: stubs antigos sem proteção JWT. Mantemos apenas as views DRF
# acima com @api_view e IsAuthenticated, alinhadas ao plano da Fase 2.
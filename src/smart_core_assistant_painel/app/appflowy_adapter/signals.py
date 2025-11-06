"""Sinais de sincronização entre o domínio (Atendimentos) e o Grid AppFlowy.

Quando um `Atendimento` é criado/atualizado/removido, espelhamos o
registro em `AppFlowyRow` dentro do grid padrão, normalizando campos
segundo o adapter.
"""

from __future__ import annotations

from typing import Any

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento

from .models import (
    AppFlowyColumn,
    AppFlowyGrid,
    AppFlowyRow,
    AppFlowyWorkspace,
    ColumnType,
)


def _normalize_priority(value: str) -> str:
    """Normaliza valores de prioridade do domínio para o adapter.

    - baixa → low
    - normal → medium
    - alta → high
    - urgente → urgent
    """

    mapping: dict[str, str] = {
        "baixa": "low",
        "normal": "medium",
        "alta": "high",
        "urgente": "urgent",
    }
    return mapping.get(value.lower(), value)


def _ensure_default_workspace_and_grid() -> AppFlowyGrid:
    """Garante a existência de um workspace e grid padrão.

    Cria o workspace `Default Workspace` e o grid `Atendimentos` se não
    existirem, com colunas mínimas necessárias para o MVI.
    """

    workspace, _ = AppFlowyWorkspace.objects.get_or_create(
        name="Default Workspace",
        defaults={},
    )

    grid, created = AppFlowyGrid.objects.get_or_create(
        workspace=workspace,
        name="Atendimentos",
        defaults={"description": "Grid espelho de Atendimentos"},
    )

    if created:
        # Define colunas padrão
        defaults = [
            ("ticket_id", "Ticket", ColumnType.STRING, 0),
            ("name", "Nome", ColumnType.STRING, 1),
            ("status", "Status", ColumnType.STRING, 2),
            ("priority", "Prioridade", ColumnType.STRING, 3),
            ("assigned_to", "Responsável", ColumnType.STRING, 4),
            ("tags", "Tags", ColumnType.MULTI_SELECT, 5),
            ("last_message", "Última Mensagem", ColumnType.TEXT, 6),
            ("channel", "Canal", ColumnType.STRING, 7),
            ("received_at", "Recebido Em", ColumnType.DATE, 8),
            ("sla_due", "SLA", ColumnType.DATE, 9),
            ("version", "Versão", ColumnType.NUMBER, 10),
            ("updated_at", "Atualizado Em", ColumnType.DATE, 11),
        ]
        for key, name, ctype, order in defaults:
            AppFlowyColumn.objects.get_or_create(
                grid=grid,
                key=key,
                defaults={
                    "name": name,
                    "type": ctype,
                    "order": order,
                    "required": False,
                },
            )

    return grid


def _upsert_row_from_atendimento(
    grid: AppFlowyGrid, a: Atendimento
) -> AppFlowyRow:
    """Cria/atualiza a linha do Grid com base em um `Atendimento`.

    A chave idempotente é `ticket_id` derivada do ID do atendimento.
    """

    ticket_id: str = f"ATD-{a.id}"

    # Pré-calcula valores normalizados para evitar linhas longas
    name_value: str = a.assunto or str(a.contato.telefone)
    priority_value: str = _normalize_priority(a.prioridade)
    assigned_to_value: str = (
        a.atendente_humano.nome if a.atendente_humano else ""
    )

    row, created = AppFlowyRow.objects.get_or_create(
        grid=grid,
        ticket_id=ticket_id,
        defaults={
            "received_at": a.data_inicio,
            "name": name_value,
            "channel": a.canal,
            "status": a.status,
            "priority": priority_value,
            "assigned_to": assigned_to_value,
            "tags": a.tags,
            "last_message": "",
            "sla_due": None,
            "version": 1,
        },
    )

    if not created:
        # Atualiza campos e incrementa versão
        row.received_at = a.data_inicio
        row.name = name_value
        row.channel = a.canal
        row.status = a.status
        row.priority = priority_value
        row.assigned_to = assigned_to_value
        row.tags = a.tags
        row.last_message = row.last_message or ""
        row.sla_due = None
        row.version = row.version + 1
        row.updated_at = timezone.now()
        row.save(
            update_fields=[
                "received_at",
                "name",
                "channel",
                "status",
                "priority",
                "assigned_to",
                "tags",
                "last_message",
                "sla_due",
                "version",
                "updated_at",
            ]
        )

    return row


@receiver(post_save, sender=Atendimento)
def espelhar_atendimento_para_grid(
    sender: Any, instance: Atendimento, created: bool, **kwargs: Any
) -> None:
    """Espelha o `Atendimento` no Grid AppFlowy ao salvar.

    - Cria o workspace/grid padrão se necessário.
    - Cria/atualiza a linha correspondente, incrementando `version`.
    """

    grid = _ensure_default_workspace_and_grid()
    _upsert_row_from_atendimento(grid, instance)


@receiver(post_delete, sender=Atendimento)
def remover_linha_do_grid_quando_atendimento_excluido(
    sender: Any, instance: Atendimento, **kwargs: Any
) -> None:
    """Remove a linha do Grid correspondente ao `Atendimento` excluído."""

    grid = _ensure_default_workspace_and_grid()
    AppFlowyRow.objects.filter(
        grid=grid, ticket_id=f"ATD-{instance.id}"
    ).delete()

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass
class Row:
    """Representa uma linha do Grid de Atendimentos.

    Comentários em Português, tipos obrigatórios.
    """

    row_id: UUID
    ticket_id: str
    received_at: datetime
    name: str
    channel: str
    status: str
    priority: str
    assigned_to: str
    tags: List[str]
    last_message: str
    sla_due: Optional[datetime]
    version: int
    updated_at: datetime


@dataclass
class RowPatch:
    """Patch de atualização/criação para linhas.

    Usado para `push_rows` pelo cliente.
    """

    row_id: Optional[UUID]
    ticket_id: str
    name: Optional[str]
    status: Optional[str]
    priority: Optional[str]
    assigned_to: Optional[str]
    tags: Optional[List[str]]
    last_message: Optional[str]
    sla_due: Optional[datetime]
    version: Optional[int]


@dataclass
class RowDelta:
    """Delta de mudanças recebido em `pull_rows`.

    `change_type` pode ser "created", "updated" ou "deleted".
    """

    change_type: str
    row: Optional[Row]
    row_id: Optional[UUID]
    since: datetime
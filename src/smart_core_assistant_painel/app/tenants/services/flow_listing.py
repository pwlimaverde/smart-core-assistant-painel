"""Helpers para listar fluxos de atendimento de um tenant a partir do
escopo do painel administrativo (banco default).

As permissões `flow_permissions` em `TenantUser`/`TenantInvite` guardam
IDs de `operacional.FluxoAtendimento`, que vive no banco do tenant.
Estas funções ativam o contexto do tenant temporariamente para que o
`TenantDatabaseRouter` direcione a query ao banco correto.
"""

# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from ..middleware import get_current_tenant, set_current_tenant
from ..models import Tenant


@contextmanager
def _tenant_scope(tenant: Tenant) -> Iterator[None]:
    """Ativa o tenant no thread-local apenas pelo bloco com."""
    previous = get_current_tenant()
    set_current_tenant(tenant)
    try:
        yield
    finally:
        set_current_tenant(previous)


def list_tenant_fluxos(tenant: Tenant) -> list[dict[str, Any]]:
    """Retorna fluxos ativos do tenant agrupados por departamento.

    Cada item é ``{"id", "nome", "departamento_id", "departamento_nome"}``.
    Ordenação: departamento → nome do fluxo.
    """
    from smart_core_assistant_painel.app.operacional.models import (
        FluxoAtendimento,
    )

    with _tenant_scope(tenant):
        qs = (
            FluxoAtendimento.objects.filter(ativo=True)
            .select_related("departamento")
            .order_by("departamento__nome", "nome")
        )
        return [
            {
                "id": f.id,
                "nome": f.nome,
                "departamento_id": f.departamento_id,
                "departamento_nome": (
                    f.departamento.nome if f.departamento_id else ""
                ),
            }
            for f in qs
        ]


def group_fluxos_by_departamento(
    fluxos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa o resultado de :func:`list_tenant_fluxos` por departamento.

    Retorna lista ``[{"departamento_nome", "fluxos": [...]}, ...]``
    preservando a ordem original (departamentos sem nome vão para "Sem
    Departamento").
    """
    grupos: dict[str, dict[str, Any]] = {}
    ordem: list[str] = []
    for f in fluxos:
        chave = f.get("departamento_nome") or "Sem Departamento"
        if chave not in grupos:
            grupos[chave] = {"departamento_nome": chave, "fluxos": []}
            ordem.append(chave)
        grupos[chave]["fluxos"].append(f)
    return [grupos[k] for k in ordem]


def sanitize_flow_ids(
    raw_ids: list[Any], tenant: Tenant
) -> list[int]:
    """Filtra IDs recebidos do formulário, mantendo apenas fluxos do tenant.

    Garante isolamento: mesmo que o cliente envie IDs aleatórios via POST,
    apenas IDs de fluxos ativos do tenant atual são persistidos.
    """
    try:
        ids_recebidos = {int(v) for v in raw_ids}
    except (TypeError, ValueError):
        return []
    if not ids_recebidos:
        return []
    validos = {f["id"] for f in list_tenant_fluxos(tenant)}
    return sorted(ids_recebidos & validos)

"""Feature flag do Workspace de Atendimento Unificado.

A flag é controlada por configuração de ambiente para não exigir
migration em tabelas legadas (princípio de independência total
documentado no plano `atendimento-unificado-chat-kanban.md`).

- `ATENDIMENTO_UNIFICADO_ENABLED`: liga/desliga globalmente.
- `ATENDIMENTO_UNIFICADO_TENANT_SLUGS`: lista CSV de slugs com acesso.
  Quando vazia, todos os tenants são liberados (desde que ENABLED=True).
"""

from __future__ import annotations

from django.conf import settings

from smart_core_assistant_painel.app.tenants.tenant_context import (
    get_current_tenant_slug,
)


def is_workspace_globally_enabled() -> bool:
    """Retorna o valor global da flag, independente de tenant."""
    return bool(getattr(settings, "ATENDIMENTO_UNIFICADO_ENABLED", False))


def is_workspace_enabled_for_tenant(tenant_slug: str | None = None) -> bool:
    """Resolve se o Workspace está habilitado para o tenant informado.

    Args:
        tenant_slug: Slug do tenant. Se ``None``, busca do contexto atual.
    """
    if not is_workspace_globally_enabled():
        return False

    slugs: list[str] = list(
        getattr(settings, "ATENDIMENTO_UNIFICADO_TENANT_SLUGS", []) or []
    )
    if not slugs:
        # Liberado para todos quando lista de allowlist estiver vazia.
        return True

    slug = (
        tenant_slug if tenant_slug is not None else get_current_tenant_slug()
    )
    return bool(slug) and slug in slugs


def get_sse_channel(tenant_slug: str | None = None) -> str:
    """Calcula o canal Redis pub/sub para SSE do tenant atual."""
    template: str = str(
        getattr(
            settings,
            "ATENDIMENTO_UNIFICADO_SSE_CHANNEL",
            "sse:{tenant_slug}:events",
        )
    )
    slug = (
        tenant_slug if tenant_slug is not None else get_current_tenant_slug()
    )
    return template.format(tenant_slug=slug or "default")

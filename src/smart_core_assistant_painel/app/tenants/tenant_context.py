from .middleware import get_current_tenant


def get_current_tenant_slug() -> str:
    """Retorna o slug do tenant atual ou string vazia.

    Útil para passar contexto para tasks assíncronas (Celery).
    """
    tenant = get_current_tenant()
    return tenant.slug if tenant else ""

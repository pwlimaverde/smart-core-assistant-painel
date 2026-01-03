from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from loguru import logger


class TenantAdminSite(AdminSite):
    """
    Admin Site dedicado aos Tenants (Clientes).
    Valida permissões específicas e acesso ao tenant atual.
    """

    site_header = _("Painel do Cliente")
    site_title = _("Administração do Tenant")
    index_title = _("Painel de Controle")
    # namespace = "tenant_admin" # Opcional, se precisar de namespace específico

    def has_permission(self, request: HttpRequest) -> bool:
        """
        Retorna True se o usuário tiver permissão para acessar o admin deste tenant.
        Resolve o tenant diretamente pelo usuário logado se necessário.
        """
        # 1. Usuário deve estar logado e ativo
        if not request.user.is_authenticated or not request.user.is_active:
            logger.debug(
                "TenantAdmin: Acesso negado - usuário não autenticado ou inativo"
            )
            return False

        # 2. Superuser tem acesso irrestrito
        if request.user.is_superuser:
            logger.debug("TenantAdmin: Acesso permitido - superuser")
            return True

        # 3. Tentar obter tenant do middleware ou resolver diretamente
        tenant = getattr(request, "tenant", None)
        logger.debug(f"TenantAdmin: Tenant na request: {tenant}")

        if tenant is None:
            # Resolver tenant pelo owner
            from smart_core_assistant_painel.app.tenants.models import (
                Tenant,
                TenantUser,
            )

            tenant = Tenant.objects.filter(owner=request.user).first()

            if not tenant:
                # Tentar como funcionário
                t_user = (
                    TenantUser.objects.filter(
                        user=request.user, is_active=True
                    )
                    .select_related("tenant")
                    .first()
                )
                if t_user:
                    tenant = t_user.tenant
                    request.tenant_user = t_user

            logger.debug(f"TenantAdmin: Tenant resolvido: {tenant}")
            if tenant:
                # Popular na request para uso posterior
                request.tenant = tenant  # type: ignore[attr-defined]

        if tenant is None:
            logger.warning(
                f"TenantAdmin: Acesso negado - nenhum tenant para user {request.user}"
            )
            return False

        # 4. Tenant deve estar ativo
        if not tenant.active:
            logger.warning(
                f"TenantAdmin: Acesso negado - tenant {tenant.slug} inativo"
            )
            return False

        # 5. Usuário deve ser o dono OU ter permissão explícita
        if request.user == tenant.owner:
            logger.debug(
                f"TenantAdmin: Acesso permitido - user é owner do tenant {tenant.slug}"
            )
            return True

        # Checar TenantUser
        if hasattr(request, "tenant_user") and request.tenant_user:
            # Já resolvido anteriormente
            if request.tenant_user.tenant == tenant:
                return True

        # Buscar se não estiver na request
        from smart_core_assistant_painel.app.tenants.models import TenantUser

        t_user = TenantUser.objects.filter(
            user=request.user, tenant=tenant, is_active=True
        ).first()

        if t_user:
            request.tenant_user = t_user
            return True

        logger.warning(
            f"TenantAdmin: Acesso negado - user {request.user} != owner {tenant.owner}"
        )
        return False


# Instância global do AdminSite do Cliente
tenant_admin_site = TenantAdminSite(name="tenant_admin")

"""Database Router para roteamento dinâmico multi-tenant."""

from typing import Any, Optional, Type

from django.db import connections
from django.db.models import Model
from loguru import logger

from .models import Tenant

CORE_APPS = {
    "tenants",
    "settings_manager",
    "auth",
    "admin",
    "contenttypes",
    "sessions",
    "django_celery_beat",
    "django_celery_results",
}

TENANT_APPS = {
    "clientes",
    "atendimentos",
    "operacional",
    "evolution_sync",  # Precisa estar junto com clientes (FK Contato)
    "trello_sync",
    "treinamento",
    "atendimento_unificado",
}


class TenantDatabaseRouter:
    """Router que direciona queries baseado no tenant do contexto."""

    def db_for_read(self, model: Type[Model], **hints: Any) -> Optional[str]:
        return self._route(model)

    def db_for_write(self, model: Type[Model], **hints: Any) -> Optional[str]:
        return self._route(model)

    def allow_relation(
        self, obj1: Model, obj2: Model, **hints: Any
    ) -> Optional[bool]:
        """Permite relações entre modelos de diferentes bancos.

        Regras:
        - Se ambos os modelos estão no mesmo banco, permite.
        - Se um dos modelos pertence ao CORE_APPS (ex: Tenant), permite.
          Isso é necessário porque modelos de tenant precisam referenciar
          o Tenant que está sempre no banco 'default'.
        """
        app1 = obj1._meta.app_label
        app2 = obj2._meta.app_label

        # Permite relações quando um dos modelos é do CORE_APPS
        # (ex: EvolutionInstance -> Tenant)
        if app1 in CORE_APPS or app2 in CORE_APPS:
            return True

        # Para modelos de TENANT_APPS, verifica se estão no mesmo banco
        db1 = self._route(type(obj1))
        db2 = self._route(type(obj2))
        return db1 == db2

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        model_name: Optional[str] = None,
        **hints: Any,
    ) -> Optional[bool]:
        if app_label in CORE_APPS:
            return db == "default"
        if app_label in TENANT_APPS:
            return True
        return None

    def _route(self, model: Type[Model]) -> str:
        """Determina qual banco usar para o model."""
        app_label = model._meta.app_label

        if app_label in CORE_APPS:
            return "default"

        if app_label in TENANT_APPS:
            from .middleware import get_current_tenant

            tenant = get_current_tenant()
            if tenant:
                db_alias = self._get_tenant_db_alias(tenant)
                if db_alias:
                    return db_alias

        return "default"

    def _get_tenant_db_alias(self, tenant: Tenant) -> Optional[str]:
        """Obtém ou configura alias de conexão para o tenant."""
        alias = f"tenant_{tenant.slug}"

        if alias in connections.databases:
            return alias

        try:
            db_config = getattr(tenant, "database_config", None)

            if not db_config or not db_config.connection_valid:
                return None

            connections.databases[alias] = {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": db_config.database_name,
                "USER": db_config.username,
                "PASSWORD": db_config.password,
                "HOST": db_config.host,
                "PORT": db_config.port,
                "OPTIONS": {"sslmode": db_config.ssl_mode},
                "TIME_ZONE": None,  # Usa o TIME_ZONE default do Django
                "CONN_MAX_AGE": 0,
                "CONN_HEALTH_CHECKS": False,
                "AUTOCOMMIT": True,
                "ATOMIC_REQUESTS": False,
            }

            # logger.debug(f"Configurada conexão dinâmica: {alias}")
            return alias

        except Exception as e:
            logger.warning(f"Erro ao configurar DB para {tenant.slug}: {e}")
            return None

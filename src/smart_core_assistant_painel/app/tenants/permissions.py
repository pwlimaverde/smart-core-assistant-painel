from enum import Enum


class TenantModule(str, Enum):
    """Módulos disponíveis no sistema para controle de permissão user-friendly."""

    CLIENTES = "clientes"
    OPERACIONAL = "operacional"
    TREINAMENTO = "treinamento"
    ATENDIMENTOS = "atendimentos"
    CONFIGURACOES = "configuracoes"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(m.value, m.value.title()) for m in cls]

    @classmethod
    def all_values(cls) -> list[str]:
        return [m.value for m in cls]


class TenantRoleType(str, Enum):
    """Tipos de role dentro do tenant."""

    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"

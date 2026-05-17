from enum import Enum


class TenantModule(str, Enum):
    """Módulos disponíveis no sistema para controle de permissão user-friendly."""

    PAINEL_ADMIN = "painel_admin"
    CLIENTES = "clientes"
    OPERACIONAL = "operacional"
    TREINAMENTO = "treinamento"
    ATENDIMENTOS = "atendimentos"
    ATENDIMENTO = "atendimento"
    CONFIGURACOES = "configuracoes"
    USUARIOS = "usuarios"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        labels = {
            cls.PAINEL_ADMIN.value: "Painel Admin",
            cls.CLIENTES.value: "Clientes",
            cls.OPERACIONAL.value: "Operacional",
            cls.TREINAMENTO.value: "Treinamento",
            cls.ATENDIMENTOS.value: "Atendimentos",
            cls.ATENDIMENTO.value: "Workspace de Atendimento",
            cls.CONFIGURACOES.value: "Configurações",
            cls.USUARIOS.value: "Usuários",
        }
        return [(m.value, labels.get(m.value, m.value.title())) for m in cls]

    @classmethod
    def all_values(cls) -> list[str]:
        return [m.value for m in cls]


class TenantRoleType(str, Enum):
    """Tipos de role dentro do tenant."""

    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"

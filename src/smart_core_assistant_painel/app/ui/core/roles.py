from rolepermissions.roles import AbstractUserRole


class Gerente(AbstractUserRole):  # type: ignore[misc]
    available_permissions = {
        "treinar_ia": True,
    }

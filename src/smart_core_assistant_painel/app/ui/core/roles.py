from rolepermissions.roles import AbstractUserRole


class Gerente(AbstractUserRole):  # [misc]
    available_permissions = {
        "treinar_ia": True,
    }

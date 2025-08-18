"""Define as funções de usuário para o sistema de permissões.

Este módulo utiliza a biblioteca `django-role-permissions` para definir
as funções de usuário e suas permissões associadas.

Classes:
    Gerente: A função de gerente com permissões específicas.
"""

from rolepermissions.roles import AbstractUserRole


class Gerente(AbstractUserRole):
    """Define a função de Gerente e suas permissões.

    A função de Gerente tem permissão para treinar a IA.

    Attributes:
        available_permissions (dict[str, bool]): Um dicionário que mapeia
            nomes de permissões para um booleano que indica se a permissão
            está disponível.
    """

    available_permissions = {
        "treinar_ia": True,
    }

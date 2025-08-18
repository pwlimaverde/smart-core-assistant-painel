"""Define dataclasses para os parâmetros das funcionalidades de carregamento inicial.

Este módulo contém dataclasses que estruturam os parâmetros necessários para as
funcionalidades de carregamento inicial, como a inicialização do Firebase.

Classes:
    FirebaseInitParameters: Parâmetros para o processo de inicialização do Firebase.
"""
from dataclasses import dataclass

from py_return_success_or_error import ParametersReturnResult

from smart_core_assistant_painel.modules.initial_loading.utils.erros import (
    FirebaseInitError,
)


@dataclass
class FirebaseInitParameters(ParametersReturnResult):
    """Parâmetros para a inicialização da aplicação Firebase.

    Attributes:
        error (FirebaseInitError): O erro a ser levantado se a
            operação falhar.
    """

    error: FirebaseInitError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()

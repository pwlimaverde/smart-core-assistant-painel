from dataclasses import dataclass

from py_return_success_or_error import ParametersReturnResult

from .erros import FirebaseInitError


@dataclass
class FirebaseInitParameters(ParametersReturnResult):
    error: FirebaseInitError

    def __str__(self) -> str:
        return self.__repr__()

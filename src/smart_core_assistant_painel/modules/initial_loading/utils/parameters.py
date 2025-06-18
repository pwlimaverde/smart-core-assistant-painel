from dataclasses import dataclass

from py_return_success_or_error import ParametersReturnResult

from smart_core_assistant_painel.modules.initial_loading.utils.erros import (
    FirebaseInitError,
)


@dataclass
class FirebaseInitParameters(ParametersReturnResult):
    error: FirebaseInitError

    def __str__(self) -> str:
        return self.__repr__()

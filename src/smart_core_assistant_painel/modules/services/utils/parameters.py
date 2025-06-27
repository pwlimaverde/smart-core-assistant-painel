from dataclasses import dataclass

from py_return_success_or_error import ParametersReturnResult

from smart_core_assistant_painel.modules.services.utils.erros import (
    SetEnvironRemoteError,
)


@dataclass
class SetEnvironRemoteParameters(ParametersReturnResult):
    config_mapping: dict[str, str]
    error: SetEnvironRemoteError

    def __str__(self) -> str:
        return self.__repr__()

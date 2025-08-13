from dataclasses import dataclass
from typing import Dict, Any

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


@dataclass
class WSParameters(ParametersReturnResult):
    """Parâmetros para o envio de mensagens via WhatsApp."""
    instance: str
    api_key: str
    message_data: Dict[str, Any]

    def __str__(self) -> str:
        return f"WSParameters(instance={self.instance})"
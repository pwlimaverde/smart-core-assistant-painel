from dataclasses import dataclass
from typing import Any, Dict

from py_return_success_or_error import ParametersReturnResult

from smart_core_assistant_painel.modules.services.utils.erros import (
    SetEnvironRemoteError,
    WhatsAppServiceError,
)


@dataclass
class SetEnvironRemoteParameters(ParametersReturnResult):
    config_mapping: dict[str, str]
    error: SetEnvironRemoteError

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class WhatsAppMensagemParameters(ParametersReturnResult):
    """Parâmetros para o envio de mensagens via WhatsApp."""

    instance: str
    api_key: str
    message_data: Dict[str, Any]
    error: WhatsAppServiceError

    def __str__(self) -> str:
        return f"WhatsAppServiceParameters(instance={self.instance})"

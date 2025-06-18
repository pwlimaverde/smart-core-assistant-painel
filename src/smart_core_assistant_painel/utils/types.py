from typing import TypeAlias

from py_return_success_or_error import Datasource, Empty, UsecaseBaseCallData

from smart_core_assistant_painel.app.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi, )
from smart_core_assistant_painel.utils.parameters import (
    LlmParameters,
    MessageParameters,
)

WSUsecase: TypeAlias = UsecaseBaseCallData[
    Empty,
    WhatsappApi,
    MessageParameters
]
WSData: TypeAlias = Datasource[WhatsappApi, MessageParameters]

ACUsecase: TypeAlias = UsecaseBaseCallData[
    str,
    str,
    LlmParameters,
]
ACData: TypeAlias = Datasource[str, LlmParameters]

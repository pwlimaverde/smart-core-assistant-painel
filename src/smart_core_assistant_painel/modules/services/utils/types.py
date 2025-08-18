from typing import TypeAlias

from py_return_success_or_error import Datasource, Empty, NoParams, UsecaseBaseCallData

from ..features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage,
)
from ..features.whatsapp_services.domain.interface.whatsapp_service import (
    WhatsAppService,
)
from .parameters import SetEnvironRemoteParameters

SERUsecase: TypeAlias = UsecaseBaseCallData[
    Empty,
    bool,
    SetEnvironRemoteParameters,
]
SERData: TypeAlias = Datasource[bool, SetEnvironRemoteParameters]

VSUsecase: TypeAlias = UsecaseBaseCallData[
    VetorStorage,
    VetorStorage,
    NoParams,
]
VSData: TypeAlias = Datasource[VetorStorage, NoParams]

# Tipos para o serviço de WhatsApp
WSUsecase: TypeAlias = UsecaseBaseCallData[
    WhatsAppService,
    WhatsAppService,
    NoParams,
]
WSData: TypeAlias = Datasource[WhatsAppService, NoParams]

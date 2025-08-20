"""Define apelidos de tipo para os casos de uso e fontes de dados de serviços.

Este módulo centraliza as definições de tipo usadas em diferentes serviços,
melhorando a legibilidade e a manutenção do código. Ele utiliza `TypeAlias`
para criar tipos claros e descritivos para casos de uso e fontes de dados
relacionados à configuração de ambiente, armazenamento de vetores e serviços
de WhatsApp.
"""

from typing import TypeAlias

from py_return_success_or_error import (
    Datasource,
    Empty,
    NoParams,
    UsecaseBaseCallData,
)

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

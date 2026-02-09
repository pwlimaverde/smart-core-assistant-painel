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
    UsecaseBaseCallData,
)

from ..features.unifield_data_services.domain.interface import (
    UnifiedDataService,
)
from .parameters import (
    SetEnvironRemoteParameters,
    UnifieldDataServicesParameters,
)

SERUsecase: TypeAlias = UsecaseBaseCallData[
    Empty,
    bool,
    SetEnvironRemoteParameters,
]
SERData: TypeAlias = Datasource[bool, SetEnvironRemoteParameters]


# Tipos para o serviço de dados unificado (UDS)
UDSData: TypeAlias = Datasource[
    UnifiedDataService,
    UnifieldDataServicesParameters,
]
UDSUsecase: TypeAlias = UsecaseBaseCallData[
    UnifiedDataService,
    UnifiedDataService,
    UnifieldDataServicesParameters,
]

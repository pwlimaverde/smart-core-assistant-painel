from typing import TypeAlias

from py_return_success_or_error import Datasource, Empty, NoParams, UsecaseBaseCallData

from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage, )
from smart_core_assistant_painel.modules.services.utils.parameters import (
    SetEnvironRemoteParameters,
)

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

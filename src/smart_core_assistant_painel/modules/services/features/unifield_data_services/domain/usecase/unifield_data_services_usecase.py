from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)
from smart_core_assistant_painel.modules.services.utils.types import UDSUsecase


class UnifieldDataServicesUseCase(UDSUsecase):
    def __call__(
        self, parameters: UnifieldDataServicesParameters
    ) -> ReturnSuccessOrError[UnifiedDataService]:
        # Chamada segura ao datasource provida por UsecaseBaseCallData
        data = self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )

        if isinstance(data, SuccessReturn):
            return SuccessReturn(data.result)
        elif isinstance(data, ErrorReturn):
            error = parameters.error
            error.message = (
                "Erro ao executar unifield_data_services: " + str(data.result)
            )
            return ErrorReturn(error)
        else:
            error = parameters.error
            error.message = "Tipo de retorno inesperado do datasource."
            return ErrorReturn(error)

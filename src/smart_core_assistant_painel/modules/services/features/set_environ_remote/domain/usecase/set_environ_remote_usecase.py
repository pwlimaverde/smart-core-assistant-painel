from py_return_success_or_error import (
    EMPTY,
    Empty,
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.services.utils.parameters import (
    SetEnvironRemoteParameters,
)
from smart_core_assistant_painel.modules.services.utils.types import SERUsecase


class SetEnvironRemoteUseCase(SERUsecase):
    def __call__(
        self, parameters: SetEnvironRemoteParameters
    ) -> ReturnSuccessOrError[Empty]:
        try:
            result_data = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )
            if isinstance(result_data, SuccessReturn):
                return SuccessReturn(EMPTY)
            elif isinstance(result_data, ErrorReturn):
                return ErrorReturn(result_data.result)
            else:
                return ErrorReturn(parameters.error)
        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - Exception: {str(e)}"
            return ErrorReturn(error)

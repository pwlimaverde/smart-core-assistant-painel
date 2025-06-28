from py_return_success_or_error import (
    ErrorReturn,
    NoParams,
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage, )
from smart_core_assistant_painel.modules.services.utils.types import VSUsecase


class VetorStorageUseCase(VSUsecase):

    def __call__(
            self,
            parameters: NoParams) -> ReturnSuccessOrError[VetorStorage]:

        try:

            return self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )

        except Exception as e:
            error = parameters.error
            error.message = f'{error.message} - Exception: {str(e)}'
            return ErrorReturn(error)

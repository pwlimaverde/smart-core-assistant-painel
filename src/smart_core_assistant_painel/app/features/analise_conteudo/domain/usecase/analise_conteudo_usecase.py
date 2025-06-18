
from py_return_success_or_error import (
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.utils.parameters import LlmParameters
from smart_core_assistant_painel.utils.types import ACUsecase


class AnaliseConteudoUseCase(ACUsecase):

    def __call__(
            self,
            parameters: LlmParameters) -> ReturnSuccessOrError[str]:

        return self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )

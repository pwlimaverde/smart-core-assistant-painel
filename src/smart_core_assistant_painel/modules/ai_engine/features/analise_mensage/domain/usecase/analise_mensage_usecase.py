from py_return_success_or_error import (
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseMensageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    AMUsecase,
)


class AnaliseMensageUseCase(AMUsecase):
    def __call__(
        self, parameters: AnaliseMensageParameters
    ) -> ReturnSuccessOrError[str]:
        return self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )

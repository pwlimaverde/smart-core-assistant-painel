from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseMensageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    AMTuple,
    AMUsecase,
)


class AnaliseMensageUseCase(AMUsecase):
    def __call__(self, parameters: AnaliseMensageParameters) -> ReturnSuccessOrError[AMTuple]:

        data = self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )

        if isinstance(data, SuccessReturn):
            return SuccessReturn(AMTuple(data.result.resposta_bot, data.result.confiabilidade))
        elif isinstance(data, ErrorReturn):
            return ErrorReturn(data.result)
        else:
            return ErrorReturn(parameters.error)

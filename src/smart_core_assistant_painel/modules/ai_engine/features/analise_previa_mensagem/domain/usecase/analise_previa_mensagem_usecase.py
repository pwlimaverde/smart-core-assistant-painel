from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    APMTuple,
    APMUsecase,
)


class AnalisePreviaMensagemUsecase(APMUsecase):
    def __call__(
        self, parameters: AnalisePreviaMensagemParameters
    ) -> ReturnSuccessOrError[APMTuple]:
        try:
            data = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )

            if isinstance(data, SuccessReturn):
                # Verificar se o resultado é uma instância de
                # AnalisePreviaMensagem
                result = data.result

                # Converter AnalisePreviaMensagem para APMTuple
                # Os dados já estão no formato correto: lista de dicionários
                # {tipo: valor}
                tuple_result = APMTuple(
                    intent_types=result.intent, entity_types=result.entities
                )
                return SuccessReturn(success=tuple_result)
            elif isinstance(data, ErrorReturn):
                return ErrorReturn(data.result)
            else:
                return ErrorReturn(parameters.error)
        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - Exception: {str(e)}"
            return ErrorReturn(error)

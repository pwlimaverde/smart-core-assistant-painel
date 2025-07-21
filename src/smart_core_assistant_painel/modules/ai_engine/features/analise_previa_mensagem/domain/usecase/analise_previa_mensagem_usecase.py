

from loguru import logger
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
            self,
            parameters: AnalisePreviaMensagemParameters) -> ReturnSuccessOrError[APMTuple]:
        try:
            data = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )

            if isinstance(data, SuccessReturn):
                # Verificar se o resultado tem os atributos necessários
                result = data.result

                # Converter objetos Pydantic para dicionários com formato personalizado
                # De: {'type': 'cotacao', 'value': 'texto'}
                # Para: {'cotacao': 'texto'}
                intent_dicts = [{item.type: item.value}
                                for item in result.intent]
                entity_dicts = [{item.type: item.value}
                                for item in result.entities]

                tuple_result = APMTuple(
                    intent_types=intent_dicts,
                    entity_types=entity_dicts
                )

                return SuccessReturn(success=tuple_result)
            elif isinstance(data, ErrorReturn):
                logger.error(
                    f'🚨 USECASE: ErrorReturn: {
                        data.result}')
                return ErrorReturn(data.result)
            else:
                logger.error(f'🚨 USECASE: Tipo inesperado: {type(data)}')
                return ErrorReturn(parameters.error)
        except Exception as e:
            error = parameters.error
            error.message = f'{error.message} - Exception: {str(e)}'
            return ErrorReturn(error)

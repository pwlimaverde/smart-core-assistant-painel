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
    """Use case para realizar a análise prévia de uma mensagem.

    Este caso de uso orquestra a extração de intenções e entidades de um
    texto de entrada, utilizando um datasource que interage com um LLM.
    """

    def __call__(
        self, parameters: AnalisePreviaMensagemParameters
    ) -> ReturnSuccessOrError[APMTuple]:
        """Executa o caso de uso de análise prévia de mensagem.

        Args:
            parameters (AnalisePreviaMensagemParameters): Parâmetros que
                incluem o texto a ser analisado, histórico e configurações
                do LLM.

        Returns:
            ReturnSuccessOrError[APMTuple]: Um objeto de retorno contendo uma
                tupla nomeada com as intenções e entidades extraídas em caso
                de sucesso (SuccessReturn), ou um AppError em caso de falha
                (ErrorReturn).
        """
        try:
            data = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )

            if isinstance(data, SuccessReturn):
                # O resultado do datasource é um objeto AnalisePreviaMensagem
                result = data.result

                # Converte o resultado para a tupla APMTuple definida no contrato
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

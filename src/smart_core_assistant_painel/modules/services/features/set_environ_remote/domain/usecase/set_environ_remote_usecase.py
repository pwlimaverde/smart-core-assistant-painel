"""Caso de uso para definir variáveis de ambiente a partir de uma fonte remota.

Este módulo define o caso de uso responsável por orquestrar o processo
de carregamento de variáveis de ambiente a partir de uma fonte de dados remota.
Ele lida com os fluxos de sucesso e erro, retornando um objeto de resultado
apropriado.

Classes:
    SetEnvironRemoteUseCase: A classe principal do caso de uso.
"""
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
    """Caso de uso para acionar o carregamento de variáveis de ambiente remotas.

    Esta classe chama a fonte de dados configurada para buscar e definir
    variáveis de ambiente. Ela garante que o resultado da operação seja
    tratado adequadamente, retornando um objeto de sucesso `Empty` ou um
    `AppError` em caso de falha.
    """

    def __call__(
        self, parameters: SetEnvironRemoteParameters
    ) -> ReturnSuccessOrError[Empty]:
        """Executa o caso de uso para definir variáveis de ambiente remotas.

        Args:
            parameters (SetEnvironRemoteParameters): Os parâmetros necessários
                para a operação, incluindo o mapeamento de configuração e
                um possível objeto de erro.

        Returns:
            ReturnSuccessOrError[Empty]: Um objeto de resultado que indica
                sucesso (com um valor `Empty`) ou falha (com um `AppError`).
        """
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

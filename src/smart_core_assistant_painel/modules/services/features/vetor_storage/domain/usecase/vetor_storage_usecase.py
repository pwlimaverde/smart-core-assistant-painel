from py_return_success_or_error import (
    ErrorReturn,
    NoParams,
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage,
)
from smart_core_assistant_painel.modules.services.utils.types import VSUsecase


class VetorStorageUseCase(VSUsecase):
    """Use case para obter a instância do serviço de armazenamento vetorial.

    Esta classe orquestra a obtenção da instância de um VetorStorage a partir
    de um datasource e a retorna para ser usada em outras partes do sistema.
    """

    def __call__(self, parameters: NoParams) -> ReturnSuccessOrError[VetorStorage]:
        """Executa o caso de uso.

        Args:
            parameters (NoParams): Não são esperados parâmetros para este
                caso de uso.

        Returns:
            ReturnSuccessOrError[VetorStorage]: Um objeto de retorno que
                contém a instância do `VetorStorage` em caso de sucesso
                (SuccessReturn) ou um `AppError` em caso de falha
                (ErrorReturn).
        """
        try:
            return self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )

        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - Exception: {str(e)}"
            return ErrorReturn(error)

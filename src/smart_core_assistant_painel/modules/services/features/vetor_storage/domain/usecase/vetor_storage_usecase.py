from py_return_success_or_error import (
    ErrorReturn,
    NoParams,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    VetorStorageError,
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
            # Chamamos diretamente o datasource para preservar a exceção
            # original (evitando que bibliotecas intermediárias a convertam
            # em um ErrorGeneric genérico, o que perde contexto importante).
            storage: VetorStorage = self._datasource(parameters)
            return SuccessReturn(storage)
        except VetorStorageError as e:
            # Exceção já específica do domínio: apenas propaga
            return ErrorReturn(e)
        except Exception as e:  # noqa: BLE001
            # Constrói um erro específico com a mensagem original para
            # manter rastreabilidade do problema na inicialização.
            base_msg = "Erro ao inicializar VetorStorage"
            error = VetorStorageError(message=f"{base_msg} - Exception: {e}")
            return ErrorReturn(error)

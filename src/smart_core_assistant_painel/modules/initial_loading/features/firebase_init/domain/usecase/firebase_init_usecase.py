import firebase_admin
from dotenv import find_dotenv, load_dotenv
from py_return_success_or_error import (
    EMPTY,
    Empty,
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.initial_loading.utils.parameters import (
    FirebaseInitParameters,
)
from smart_core_assistant_painel.modules.initial_loading.utils.types import FIUsecase


class FirebaseInitUseCase(FIUsecase):
    """Use case para inicializar o SDK do Firebase Admin.

    Esta classe garante que o Firebase seja inicializado corretamente no início
    da aplicação, carregando as credenciais a partir das variáveis de ambiente.
    """

    def __call__(
        self, parameters: FirebaseInitParameters
    ) -> ReturnSuccessOrError[Empty]:
        """Executa o caso de uso de inicialização do Firebase.

        Args:
            parameters (FirebaseInitParameters): Parâmetros que contêm o
                objeto de erro a ser usado em caso de falha.

        Returns:
            ReturnSuccessOrError[Empty]: Retorna um `SuccessReturn` com um
                objeto `EMPTY` em caso de sucesso, ou um `ErrorReturn`
                contendo um `FirebaseInitError` em caso de falha.
        """
        try:
            load_dotenv(find_dotenv())
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app()

            return SuccessReturn(EMPTY)

        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - Exception: {str(e)}"
            return ErrorReturn(error)

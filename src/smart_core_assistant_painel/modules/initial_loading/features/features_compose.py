from py_return_success_or_error import (
    ErrorReturn,
)

from ..utils.erros import FirebaseInitError
from ..utils.parameters import FirebaseInitParameters
from ..utils.types import FIUsecase
from .firebase_init.domain.usecase.firebase_init_usecase import (
    FirebaseInitUseCase,
)


class FeaturesCompose:
    """Facade para os casos de uso do módulo de Carregamento Inicial.

    Esta classe fornece uma interface para executar as tarefas de inicialização
    necessárias quando a aplicação começa, como a inicialização do Firebase.
    """

    @staticmethod
    def init_firebase() -> None:
        """Inicializa o serviço do Firebase.

        Este método executa o caso de uso para inicializar o cliente do
        Firebase, que é essencial para outras funcionalidades que dependem
        de serviços do Google.

        Raises:
            FirebaseInitError: Se ocorrer um erro durante a inicialização
                               do Firebase.
        """
        error = FirebaseInitError("Erro ao inicializar o Firebase")
        parameters = FirebaseInitParameters(error=error)
        usecase: FIUsecase = FirebaseInitUseCase()

        data = usecase(parameters)
        if isinstance(data, ErrorReturn):
            raise data.result

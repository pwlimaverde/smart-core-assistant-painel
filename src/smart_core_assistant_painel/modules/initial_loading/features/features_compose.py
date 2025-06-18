
from loguru import logger
from py_return_success_or_error import (
    ErrorReturn,
)

from smart_core_assistant_painel.modules.initial_loading.features.firebase_init.domain.usecase.firebase_init_usecase import (
    FirebaseInitUseCase, )
from smart_core_assistant_painel.modules.initial_loading.utils.erros import (
    FirebaseInitError,
)
from smart_core_assistant_painel.modules.initial_loading.utils.parameters import (
    FirebaseInitParameters, )
from smart_core_assistant_painel.modules.initial_loading.utils.types import FIUsecase





class FeaturesCompose:

    @staticmethod
    def init_firebase() -> None:

        error = FirebaseInitError('Erro ao inicializar o Firebase')
        parameters = FirebaseInitParameters(error=error)
        usecase: FIUsecase = FirebaseInitUseCase()

        data = usecase(parameters)
        if isinstance(data, ErrorReturn):
            raise data.result
        logger.info("Firebase Admin SDK inicializado com sucesso!")
        

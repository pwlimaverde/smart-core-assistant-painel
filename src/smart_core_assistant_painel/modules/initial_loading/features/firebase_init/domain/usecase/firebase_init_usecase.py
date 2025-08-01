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
    def __call__(
        self, parameters: FirebaseInitParameters
    ) -> ReturnSuccessOrError[Empty]:
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

from typing import TypeAlias

from py_return_success_or_error import Empty, UsecaseBase

from smart_core_assistant_painel.modules.initial_loading.utils.parameters import (
    FirebaseInitParameters, )

FIUsecase: TypeAlias = UsecaseBase[
    Empty,
    FirebaseInitParameters
]

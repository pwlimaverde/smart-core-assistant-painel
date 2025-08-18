from typing import TypeAlias

from py_return_success_or_error import Empty, UsecaseBase

from .parameters import FirebaseInitParameters

FIUsecase: TypeAlias = UsecaseBase[Empty, FirebaseInitParameters]

from dataclasses import dataclass

from py_return_success_or_error import AppError


@dataclass
class FirebaseInitError(AppError):
    message: str

    def __str__(self) -> str:
        return f"LlmError - {self.message}"

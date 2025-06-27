from dataclasses import dataclass

from py_return_success_or_error import AppError

@dataclass
class SetEnvironRemoteError(AppError):
    message: str

    def __str__(self) -> str:
        return f'LlmError - {self.message}'
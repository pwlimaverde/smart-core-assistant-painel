from dataclasses import dataclass

from py_return_success_or_error import AppError


@dataclass
class WahaApiError(AppError):
    message: str

    def __str__(self) -> str:
        return f"WahaApiError - {self.message}"


@dataclass
class HtmlStrError(AppError):
    message: str

    def __str__(self) -> str:
        return f"HtmlStrError - {self.message}"


@dataclass
class LlmError(AppError):
    message: str

    def __str__(self) -> str:
        return f"LlmError - {self.message}"


@dataclass
class DocumentError(AppError):
    message: str

    def __str__(self) -> str:
        return f"DocumentError - {self.message}"

@dataclass
class DataMessageError(AppError):
    message: str

    def __str__(self) -> str:
        return f"DataMessageError - {self.message}"
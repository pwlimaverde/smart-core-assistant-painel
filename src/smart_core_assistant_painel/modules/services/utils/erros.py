from dataclasses import dataclass

from py_return_success_or_error import AppError


@dataclass
class SetEnvironRemoteError(AppError):
    message: str

    def __str__(self) -> str:
        # Ajuste do prefixo para refletir corretamente a origem do erro
        # evitando confusão com erros de LLM.
        return f"SetEnvironRemoteError - {self.message}"


@dataclass
class WhatsAppServiceError(AppError):
    message: str

    def __str__(self) -> str:
        return f"WhatsAppServiceError - {self.message}"


@dataclass
class VetorStorageError(AppError):
    """Erro específico para inicialização/uso do VetorStorage."""

    message: str

    def __str__(self) -> str:
        # Mantém padrão consistente de mensagem específica
        return f"VetorStorageError - {self.message}"

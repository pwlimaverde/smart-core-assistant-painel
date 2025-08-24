"""Define classes de erro personalizadas para os serviços.

Este módulo contém dataclasses para erros de aplicação específicos que podem
ocorrer dentro dos serviços, proporcionando um tratamento de erros claro e
consistente.
"""

from dataclasses import dataclass

from py_return_success_or_error import AppError


@dataclass
class SetEnvironRemoteError(AppError):
    """Erro levantado durante a configuração de variáveis de ambiente remotas."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"SetEnvironRemoteError - {self.message}"


@dataclass
class WhatsAppServiceError(AppError):
    """Erro relacionado às operações do serviço WhatsApp."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"WhatsAppServiceError - {self.message}"

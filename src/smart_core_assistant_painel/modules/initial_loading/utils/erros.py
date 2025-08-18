"""Define classes de erro personalizadas para o módulo de carregamento inicial.

Este módulo contém dataclasses para erros de aplicação específicos que podem
ocorrer durante o processo de carregamento inicial.
"""
from dataclasses import dataclass

from py_return_success_or_error import AppError


@dataclass
class FirebaseInitError(AppError):
    """Erro levantado durante a inicialização do Firebase."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"FirebaseInitError - {self.message}"

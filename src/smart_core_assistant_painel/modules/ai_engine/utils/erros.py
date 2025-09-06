"""Define classes de erro personalizadas para o motor de IA.

Este módulo contém dataclasses para erros de aplicação específicos que podem
ocorrer dentro do motor de IA, proporcionando um tratamento de erros claro e
consistente para diferentes funcionalidades.
"""

from dataclasses import dataclass

from py_return_success_or_error import AppError


@dataclass
class HtmlStrError(AppError):
    """Erro relacionado ao processamento de strings HTML."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"HtmlStrError - {self.message}"


@dataclass
class LlmError(AppError):
    """Erro relacionado à interação com o modelo de linguagem (LLM)."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"LlmError - {self.message}"


@dataclass
class DocumentError(AppError):
    """Erro relacionado ao processamento ou carregamento de documentos."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"DocumentError - {self.message}"


@dataclass
class DataMessageError(AppError):
    """Erro relacionado ao processamento de dados de mensagens."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"DataMessageError - {self.message}"


@dataclass
class EmbeddingError(AppError):
    """Erro relacionado à geração ou processamento de embeddings."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"EmbeddingError - {self.message}"


@dataclass
class GenerateChunksError(AppError):
    """Erro relacionado à geração ou processamento de chunks."""

    message: str

    def __str__(self) -> str:
        """Retorna uma mensagem de erro formatada."""
        return f"GenerateChunksError - {self.message}"

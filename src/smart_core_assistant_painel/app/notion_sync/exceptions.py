"""
Exceções customizadas para o módulo de sincronização.

Este módulo define as exceções específicas utilizadas durante o processo
de sincronização com plataformas externas (Notion, Airtable, etc).
"""

from typing import Any


class SyncError(Exception):
    """
    Exceção base para erros de sincronização.

    Todas as exceções relacionadas ao processo de sincronização
    devem herdar desta classe.

    Args:
        message: Mensagem descritiva do erro.
        details: Detalhes adicionais sobre o erro (opcional).
    """

    def __init__(
        self, message: str, details: dict[str, Any] | None = None
    ) -> None:
        """
        Inicializa a exceção com mensagem e detalhes opcionais.

        Args:
            message: Mensagem descritiva do erro.
            details: Informações adicionais sobre o erro.
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """
        Retorna representação em string da exceção.

        Returns:
            Mensagem de erro formatada com detalhes se disponíveis.
        """
        if self.details:
            return f"{self.message} - Detalhes: {self.details}"
        return self.message


class NotionSyncError(SyncError):
    """
    Exceção específica para erros na sincronização com Notion.

    Utilizada quando ocorrem problemas na comunicação com a API do Notion
    ou durante o processamento de dados do Notion.

    Args:
        message: Mensagem descritiva do erro.
        status_code: Código HTTP retornado pela API do Notion (opcional).
        notion_error: Código de erro específico do Notion (opcional).
        details: Detalhes adicionais sobre o erro (opcional).
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        notion_error: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Inicializa exceção específica do Notion.

        Args:
            message: Mensagem descritiva do erro.
            status_code: Código HTTP da resposta da API.
            notion_error: Código de erro específico retornado pelo Notion.
            details: Informações adicionais sobre o erro.
        """
        self.status_code = status_code
        self.notion_error = notion_error
        error_details = details or {}

        if status_code is not None:
            error_details["status_code"] = status_code
        if notion_error is not None:
            error_details["notion_error"] = notion_error

        super().__init__(message=message, details=error_details)


# SyncConfigError removido - não é mais necessário
# pois SyncConfig foi eliminado em favor de abordagem mais simples


class WebhookValidationError(SyncError):
    """
    Exceção para erros de validação de webhooks.

    Utilizada quando a validação de assinatura do webhook falha ou
    quando o payload recebido é inválido.

    Args:
        message: Mensagem descritiva do erro.
        details: Detalhes adicionais sobre o erro (opcional).
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Inicializa exceção de validação de webhook.

        Args:
            message: Mensagem descritiva do erro.
            details: Informações adicionais sobre o erro.
        """
        super().__init__(message=message, details=details)


class MappingError(SyncError):
    """
    Exceção para erros durante o mapeamento de dados.

    Utilizada quando ocorre um problema ao converter dados entre
    o formato Django e o formato da plataforma externa.

    Args:
        message: Mensagem descritiva do erro.
        field_name: Nome do campo que causou o erro (opcional).
        source_value: Valor original que não pôde ser mapeado (opcional).
        details: Detalhes adicionais sobre o erro (opcional).
    """

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        source_value: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Inicializa exceção de mapeamento.

        Args:
            message: Mensagem descritiva do erro.
            field_name: Campo problemático no mapeamento.
            source_value: Valor que causou o erro.
            details: Informações adicionais sobre o erro.
        """
        self.field_name = field_name
        self.source_value = source_value
        error_details = details or {}

        if field_name is not None:
            error_details["field_name"] = field_name
        if source_value is not None:
            error_details["source_value"] = str(source_value)

        super().__init__(message=message, details=error_details)
